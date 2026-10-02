"""
safety.py

Enforces strict READ-ONLY security and SQL injection prevention.
The AI natural-language query layer must never permit database mutations or raw SQL execution.
"""

from __future__ import annotations

import re
from typing import Tuple

# Mutation keywords and patterns that signal write or modification attempts
WRITE_PATTERNS = [
    r"\b(delete|remove|erase|purge)\b",
    r"\b(update|change|modify|alter|edit|set|adjust)\b",
    r"\b(insert|add|create|new)\b.*\b(employee|rate|salary|bonus|deduction|expense|week|record)\b",
    r"\b(drop|truncate)\b.*\b(table|database|schema)\b",
    r"\bchange\s+.+\s+(salary|rate|amount|bonus|deduction)\b",
    r"\bupdate\s+.+\s+(rate|salary|status)\b",
    r"\bdelete\s+[a-zA-Z0-9_]+\b",
    r"\bremove\s+[a-zA-Z0-9_]+\b",
    r"\bset\s+.+\s+to\s+\d+",
]

# SQL injection or arbitrary SQL execution patterns
SQL_INJECTION_PATTERNS = [
    r"\bselect\b.*\bfrom\b",
    r"\bunion\b.*\bselect\b",
    r"\binsert\s+into\b",
    r"\bupdate\s+[a-zA-Z0-9_]+\s+set\b",
    r"\bdelete\s+from\b",
    r"\bdrop\s+table\b",
    r"\balter\s+table\b",
    r"\btruncate\s+table\b",
    r"(--|;|\/\*|\*\/)",
    r"['\"]\s*or\b",
    r"\bor\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",
    r"['\"]\s*or\s*['\"]\w+['\"]\s*=\s*['\"]\w+",
]

REJECTION_REASONS = {
    "WRITE": "Database modification requests are rejected. The AI query layer is strictly read-only and cannot insert, update, delete, or alter any factory records.",
    "SQL": "Arbitrary SQL execution is not permitted. The AI query layer operates strictly through controlled read-only query routing.",
}


def check_for_mutations(text: str) -> bool:
    """Returns True if the text attempts to mutate or modify factory data."""
    text_clean = text.strip().lower()
    for pattern in WRITE_PATTERNS:
        if re.search(pattern, text_clean):
            return True
    return False


def check_for_sql_injection(text: str) -> bool:
    """Returns True if the text looks like raw SQL or an injection attempt."""
    text_clean = text.strip().lower()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text_clean):
            return True
    return False


def validate_query_safety(question: str) -> Tuple[bool, str | None, str | None]:
    """
    Validates that a user query is strictly read-only and free of SQL injection.
    Returns:
        (is_safe, intent_type, message)
        If safe: (True, None, None)
        If write attempt: (False, "REJECTED_WRITE", REJECTION_REASONS["WRITE"])
        If SQL injection: (False, "REJECTED_SQL", REJECTION_REASONS["SQL"])
    """
    if check_for_mutations(question):
        return False, "REJECTED_WRITE", REJECTION_REASONS["WRITE"]

    if check_for_sql_injection(question):
        return False, "REJECTED_SQL", REJECTION_REASONS["SQL"]

    return True, None, None
