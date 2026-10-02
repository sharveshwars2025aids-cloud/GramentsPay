"""
extractor.py

Handles intent classification and entity extraction using Groq LLM with JSON mode,
preceded by safety checks and followed by validation.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from ai.config import get_groq_client, get_groq_model
from ai.prompts import EXTRACTION_SYSTEM_PROMPT
from ai.safety import validate_query_safety
from ai.schemas import IntentNames, StructuredInterpretation

logger = logging.getLogger(__name__)


def extract_intent_and_entities(
    question: str,
    client: Optional[Any] = None,
) -> StructuredInterpretation:
    """
    Executes the first phase of the query layer:
    1. Safety & Read-Only validation
    2. Groq LLM Intent Classification & Entity Extraction
    3. JSON validation against StructuredInterpretation schema
    """
    # Step 1: Read-only & SQL safety check
    is_safe, intent_type, _ = validate_query_safety(question)
    if not is_safe:
        return StructuredInterpretation(
            intent=intent_type or IntentNames.REJECTED_WRITE,
        )

    # Step 2: Invoke Groq LLM
    if client is None:
        client = get_groq_client()

    model_name = get_groq_model()

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        raw_content = response.choices[0].message.content or "{}"
        parsed = json.loads(raw_content)

        intent = str(parsed.get("intent", IntentNames.UNSUPPORTED)).strip().upper()
        if intent not in IntentNames.ALL_SUPPORTED:
            intent = IntentNames.UNSUPPORTED

        return StructuredInterpretation(
            intent=intent,
            employee=parsed.get("employee"),
            date=parsed.get("date"),
            week=parsed.get("week"),
            department=parsed.get("department"),
            style=parsed.get("style"),
            compare_week=parsed.get("compare_week"),
        )
    except Exception as exc:
        logger.warning("Groq API extraction failed or timed out: %s. Using heuristic fallback.", exc)
        return _heuristic_extraction_fallback(question)


def _heuristic_extraction_fallback(question: str) -> StructuredInterpretation:
    """
    Deterministic rule-based backup in case of network unavailability during testing.
    Follows identical classification semantics.
    """
    q = question.lower()

    # Compare week
    if "compare" in q or "versus" in q or " vs " in q:
        return StructuredInterpretation(
            intent=IntentNames.WEEK_COMPARISON,
            week="current",
            compare_week="last week",
        )

    # Outsourcing
    if "outsource" in q or "outsourced" in q:
        return StructuredInterpretation(
            intent=IntentNames.WEEKLY_OUTSOURCING,
            week="current",
        )

    # Security
    if "security" in q:
        return StructuredInterpretation(
            intent=IntentNames.WEEKLY_SECURITY,
            week="current",
        )

    # Expense
    if "expense" in q or "spend" in q or "spending" in q or "spent" in q:
        return StructuredInterpretation(
            intent=IntentNames.WEEKLY_EXPENSE,
            week="current",
        )

    # Department summary
    if "department" in q:
        import re
        dept_match = re.search(r"(\w+)\s+department", q)
        dept = dept_match.group(1).title() if dept_match else None
        return StructuredInterpretation(
            intent=IntentNames.DEPARTMENT_SUMMARY,
            department=dept,
            week="current",
        )

    # Production summary vs employee production
    if "production" in q or "produce" in q or "produced" in q:
        if "summary" in q or "total production" in q or "completed" in q:
            return StructuredInterpretation(
                intent=IntentNames.PRODUCTION_SUMMARY,
                week="current",
            )
        # Check if an employee or date is mentioned
        import re
        date_match = re.search(r"\b(\d{2}[\/\-]\d{2}[\/\-]\d{4}|\d{4}[\/\-]\d{2}[\/\-]\d{2})\b", q)
        # Check potential employee name
        emp_match = re.search(r"(?:what did|did|how much did)\s+([a-zA-Z]+)", q)
        emp_name = emp_match.group(1).title() if emp_match else None
        return StructuredInterpretation(
            intent=IntentNames.EMPLOYEE_PRODUCTION,
            employee=emp_name,
            date=date_match.group(1) if date_match else None,
            week="current" if not date_match else None,
        )

    # Work history
    if "work history" in q or "history" in q:
        import re
        emp_match = re.search(r"([a-zA-Z]+)(?:'s|\s+work\s+history|\s+history)", q)
        emp_name = emp_match.group(1).title() if emp_match else None
        return StructuredInterpretation(
            intent=IntentNames.EMPLOYEE_WORK_HISTORY,
            employee=emp_name,
        )

    # Deductions
    if "deduction" in q or "deductions" in q or "advance" in q:
        import re
        emp_match = re.search(r"([a-zA-Z]+)(?:'s|\s+have|\s+has)", q)
        emp_name = emp_match.group(1).title() if emp_match else None
        return StructuredInterpretation(
            intent=IntentNames.EMPLOYEE_DEDUCTION,
            employee=emp_name,
            week="current",
        )

    # Bonus
    if "bonus" in q or "bonuses" in q or "incentive" in q:
        import re
        emp_match = re.search(r"([a-zA-Z]+)(?:'s|\s+receive|\s+get|\s+have)", q)
        emp_name = emp_match.group(1).title() if emp_match else None
        return StructuredInterpretation(
            intent=IntentNames.EMPLOYEE_BONUS,
            employee=emp_name,
            week="current",
        )

    # Salary summary vs employee salary
    if "salary" in q or "wages" in q or "earnings" in q or "payroll" in q:
        if "summary" in q or "total" in q or "all" in q:
            return StructuredInterpretation(
                intent=IntentNames.SALARY_SUMMARY,
                week="current",
            )
        import re
        emp_match = re.search(r"([a-zA-Z]+)(?:'s|\s+salary|\s+wages)", q)
        emp_name = emp_match.group(1).title() if emp_match else None
        return StructuredInterpretation(
            intent=IntentNames.EMPLOYEE_SALARY,
            employee=emp_name,
            week="current",
        )

    return StructuredInterpretation(intent=IntentNames.UNSUPPORTED)
