"""
schemas.py

Pydantic models and intent definitions for the AI Natural-Language Query Layer.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class IntentNames:
    EMPLOYEE_SALARY = "EMPLOYEE_SALARY"
    EMPLOYEE_PRODUCTION = "EMPLOYEE_PRODUCTION"
    EMPLOYEE_WORK_HISTORY = "EMPLOYEE_WORK_HISTORY"
    EMPLOYEE_DEDUCTION = "EMPLOYEE_DEDUCTION"
    EMPLOYEE_BONUS = "EMPLOYEE_BONUS"
    WEEKLY_EXPENSE = "WEEKLY_EXPENSE"
    WEEKLY_OUTSOURCING = "WEEKLY_OUTSOURCING"
    WEEKLY_SECURITY = "WEEKLY_SECURITY"
    DEPARTMENT_SUMMARY = "DEPARTMENT_SUMMARY"
    PRODUCTION_SUMMARY = "PRODUCTION_SUMMARY"
    SALARY_SUMMARY = "SALARY_SUMMARY"
    WEEK_COMPARISON = "WEEK_COMPARISON"

    # Meta/guardrail intents
    UNSUPPORTED = "UNSUPPORTED"
    REJECTED_WRITE = "REJECTED_WRITE"
    REJECTED_SQL = "REJECTED_SQL"

    ALL_SUPPORTED = [
        EMPLOYEE_SALARY,
        EMPLOYEE_PRODUCTION,
        EMPLOYEE_WORK_HISTORY,
        EMPLOYEE_DEDUCTION,
        EMPLOYEE_BONUS,
        WEEKLY_EXPENSE,
        WEEKLY_OUTSOURCING,
        WEEKLY_SECURITY,
        DEPARTMENT_SUMMARY,
        PRODUCTION_SUMMARY,
        SALARY_SUMMARY,
        WEEK_COMPARISON,
    ]


class QueryRequest(BaseModel):
    """Incoming user natural-language question."""
    question: str = Field(..., min_length=1, description="Natural-language question from user.")


class StructuredInterpretation(BaseModel):
    """Structured extraction of intent and entity arguments produced by the LLM."""
    intent: str = Field(..., description="Classified intent identifier.")
    employee: Optional[str] = Field(None, description="Employee name or employee code if mentioned.")
    date: Optional[str] = Field(None, description="Specific date if mentioned (e.g. 'YYYY-MM-DD' or '07/07/2026').")
    week: Optional[str] = Field(None, description="Week identifier or reference (e.g. 'current', 'last week', '147').")
    department: Optional[str] = Field(None, description="Department name if mentioned (e.g. 'Singer', 'Finishing').")
    style: Optional[str] = Field(None, description="Style number if mentioned.")
    compare_week: Optional[str] = Field(None, description="Secondary week reference for comparative queries.")


class QueryResponse(BaseModel):
    """Standardized response format for the AI query endpoint."""
    question: str
    intent: str
    answer: str
    data: Optional[dict[str, Any]] = None
