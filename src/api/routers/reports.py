"""
reports.py

API router providing read-only endpoints for weekly factory reports:
- Salary report
- Expense report
- Outsourcing report
- Security payment report
- Department-wise summary & operations report
- Bank-transfer report
- Weekly summary report
"""

from typing import Any
from fastapi import APIRouter, HTTPException

from api.services.report_service import (
    ReportNotFoundError,
    get_salary_report,
    get_expenses_report,
    get_outsource_report,
    get_security_report,
    get_department_summary_report,
    get_operations_report,
    get_bank_transfer_report,
    get_weekly_summary_report,
)

router = APIRouter(prefix="/weeks/{week_id}/reports", tags=["reports"])


@router.get(
    "/salary",
    response_model=list[dict[str, Any]],
    summary="Employee salary report for the week",
)
def salary_report(week_id: int):
    try:
        return get_salary_report(week_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/expenses",
    response_model=list[dict[str, Any]],
    summary="Factory expenses report for the week",
)
def expenses_report(week_id: int):
    try:
        return get_expenses_report(week_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/outsource",
    response_model=list[dict[str, Any]],
    summary="Outsource work payments report for the week",
)
def outsource_report(week_id: int):
    try:
        return get_outsource_report(week_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/security",
    response_model=list[dict[str, Any]],
    summary="Security payments report for the week",
)
def security_report(week_id: int):
    try:
        return get_security_report(week_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/department-summary",
    response_model=list[dict[str, Any]],
    summary="Department-wise salary summary report",
)
def department_summary_report(week_id: int):
    try:
        return get_department_summary_report(week_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/operations",
    response_model=list[dict[str, Any]],
    summary="Production details by style and type report",
)
def operations_report(week_id: int):
    try:
        return get_operations_report(week_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/bank-transfer",
    response_model=list[dict[str, Any]],
    summary="Consolidated bank transfer transactions report",
)
def bank_transfer_report(week_id: int):
    try:
        return get_bank_transfer_report(week_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/summary",
    response_model=list[dict[str, Any]],
    summary="Weekly closing executive summary report",
)
def summary_report(week_id: int):
    try:
        return get_weekly_summary_report(week_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
