"""
service.py

High-level orchestration service for the GarmentsPay AI Natural-Language Query Layer.
Coordinates safety validation, LLM intent extraction, entity resolution,
backend routing, and natural-language formatting.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from database import connect_database
from ai.safety import validate_query_safety, REJECTION_REASONS
from ai.schemas import IntentNames, QueryResponse
from ai.extractor import extract_intent_and_entities
from ai.resolver import (
    EmployeeNotFoundError,
    AmbiguousEmployeeError,
    WeekResolutionError,
)
from ai.router import route_query
from ai.formatter import format_natural_response

logger = logging.getLogger(__name__)

UNSUPPORTED_EXPLANATION = (
    "I can currently answer questions about salaries, production, work history, "
    "deductions, bonuses, expenses, outsourcing, security payments, department summaries, "
    "production summaries, salary summaries, and week comparisons."
)


def process_ai_query(
    question: str,
    client: Optional[Any] = None,
) -> QueryResponse:
    """
    End-to-end processing of a user natural-language question.
    Strictly read-only, non-hallucinatory, and routed through verified backend logic.
    """
    clean_question = question.strip() if question else ""
    if not clean_question:
        return QueryResponse(
            question=question,
            intent=IntentNames.UNSUPPORTED,
            answer="Please ask a question about factory operations, salaries, or production.",
            data=None,
        )

    # 1. Safety validation (write prevention & SQL injection prevention)
    is_safe, intent_type, message = validate_query_safety(clean_question)
    if not is_safe:
        return QueryResponse(
            question=clean_question,
            intent=intent_type or IntentNames.REJECTED_WRITE,
            answer=message or REJECTION_REASONS["WRITE"],
            data=None,
        )

    # 2. Intent Classification & Entity Extraction
    interpretation = extract_intent_and_entities(clean_question, client=client)

    if interpretation.intent == IntentNames.REJECTED_WRITE:
        return QueryResponse(
            question=clean_question,
            intent=IntentNames.REJECTED_WRITE,
            answer=REJECTION_REASONS["WRITE"],
            data=None,
        )

    if interpretation.intent == IntentNames.REJECTED_SQL:
        return QueryResponse(
            question=clean_question,
            intent=IntentNames.REJECTED_SQL,
            answer=REJECTION_REASONS["SQL"],
            data=None,
        )

    if interpretation.intent == IntentNames.UNSUPPORTED:
        return QueryResponse(
            question=clean_question,
            intent=IntentNames.UNSUPPORTED,
            answer=UNSUPPORTED_EXPLANATION,
            data=None,
        )

    # 3. Entity Resolution & Backend Routing
    connection = connect_database()
    try:
        data, base_answer = route_query(connection, interpretation)
        final_answer = format_natural_response(
            question=clean_question,
            intent=interpretation.intent,
            data=data,
            default_answer=base_answer,
            client=client,
        )
        return QueryResponse(
            question=clean_question,
            intent=interpretation.intent,
            answer=final_answer,
            data=data,
        )
    except EmployeeNotFoundError as exc:
        return QueryResponse(
            question=clean_question,
            intent=interpretation.intent,
            answer=str(exc),
            data={"error": "employee_not_found"},
        )
    except AmbiguousEmployeeError as exc:
        return QueryResponse(
            question=clean_question,
            intent=interpretation.intent,
            answer=str(exc),
            data={
                "error": "ambiguous_employee",
                "matching_candidates": [
                    {"code": m["employee_code"], "name": m["name"]}
                    for m in exc.matches
                ],
            },
        )
    except WeekResolutionError as exc:
        return QueryResponse(
            question=clean_question,
            intent=interpretation.intent,
            answer=str(exc),
            data={"error": "week_not_found"},
        )
    except Exception as exc:
        logger.exception("Error executing AI query routing: %s", exc)
        return QueryResponse(
            question=clean_question,
            intent=interpretation.intent,
            answer=f"Could not complete query due to backend error: {exc}",
            data=None,
        )
    finally:
        connection.close()
