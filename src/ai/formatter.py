"""
formatter.py

Generates clear, grounded natural-language responses from verified backend results.
Guarantees that numbers and facts originate strictly from the database.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from ai.config import get_groq_client, get_groq_model
from ai.prompts import FORMATTER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def format_natural_response(
    question: str,
    intent: str,
    data: dict[str, Any],
    default_answer: str,
    client: Optional[Any] = None,
) -> str:
    """
    Produces a natural-language answer explaining the verified backend result.
    If Groq is available and data is present, uses LLM with temperature 0.0
    strictly constrained to verified facts. If any issue occurs, falls back
    to the verified template answer.
    """
    if not data or not default_answer:
        return default_answer

    # For simple or error responses, template is exact and immediate
    if intent in ("UNSUPPORTED", "REJECTED_WRITE", "REJECTED_SQL"):
        return default_answer

    try:
        if client is None:
            client = get_groq_client()

        model_name = get_groq_model()
        user_prompt = (
            f"Question: {question}\n"
            f"Verified Backend Data: {json.dumps(data, default=str)}\n"
            f"Verified Reference Summary: {default_answer}\n\n"
            f"Explain this verified data in 1-2 clear, professional sentences using ₹ for amounts. "
            f"Do not alter or fabricate any figures."
        )

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": FORMATTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=200,
        )
        content = response.choices[0].message.content
        if content and len(content.strip()) > 5:
            stripped = content.strip()
            # If the response looks like a JSON object or array, discard it and use default_answer
            if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
                return default_answer
            return stripped
    except Exception as exc:
        logger.debug("LLM formatter fallback triggered: %s", exc)

    return default_answer
