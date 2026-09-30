"""
dashboard.py

FastAPI router exposing structured, chart-ready analytics for the GarmentsPay dashboard.

Endpoints:
- GET /weeks/{week_id}/dashboard : Full consolidated dashboard for a given week
- GET /weeks/{week_id}/dashboard/production : Production analytics and breakdown
- GET /weeks/{week_id}/dashboard/salary : Salary analytics, department breakdown, and distribution
- GET /weeks/{week_id}/dashboard/expenses : Factory expenses, outsourcing, security, and categories
- GET /weeks/{week_id}/dashboard/financials : High-level weekly financial overview and cost breakdown
- GET /dashboard/trends : Multi-week comparative trajectories for charts
"""

from typing import Any
from fastapi import APIRouter, HTTPException, Query

from api.services.dashboard_service import (
    DashboardNotFoundError,
    get_week_dashboard,
    get_multi_week_trends,
)
from database import connect_database
from api.services.dashboard_service import (
    _verify_week_exists,
    get_production_analytics,
    get_salary_analytics,
    get_expense_analytics,
    get_weekly_financial_overview,
)

router = APIRouter(tags=["dashboard"])


@router.get(
    "/weeks/{week_id}/dashboard",
    response_model=dict[str, Any],
    summary="Comprehensive chart-ready dashboard analytics for a given week",
)
def get_dashboard(week_id: int):
    try:
        return get_week_dashboard(week_id)
    except DashboardNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/weeks/{week_id}/dashboard/production",
    response_model=dict[str, Any],
    summary="Production analytics (departments, operations, styles, and trend)",
)
def get_dashboard_production(week_id: int):
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        return get_production_analytics(conn, week_id)
    except DashboardNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        conn.close()


@router.get(
    "/weeks/{week_id}/dashboard/salary",
    response_model=dict[str, Any],
    summary="Salary analytics (gross, net, piece, shift, bonus, deduction, department)",
)
def get_dashboard_salary(week_id: int):
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        return get_salary_analytics(conn, week_id)
    except DashboardNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        conn.close()


@router.get(
    "/weeks/{week_id}/dashboard/expenses",
    response_model=dict[str, Any],
    summary="Expenses analytics (factory categories, outsourcing, security, and trend)",
)
def get_dashboard_expenses(week_id: int):
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        return get_expense_analytics(conn, week_id)
    except DashboardNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        conn.close()


@router.get(
    "/weeks/{week_id}/dashboard/financials",
    response_model=dict[str, Any],
    summary="Weekly financial overview and cost distribution chart data",
)
def get_dashboard_financials(week_id: int):
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        sal = get_salary_analytics(conn, week_id)
        exp = get_expense_analytics(conn, week_id)
        return get_weekly_financial_overview(conn, week_id, sal, exp)
    except DashboardNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        conn.close()


@router.get(
    "/dashboard/trends",
    response_model=dict[str, Any],
    summary="Multi-week comparative historical trajectories across production, payroll, and expenses",
)
def get_dashboard_trends(limit: int = Query(default=10, ge=1, le=52)):
    return get_multi_week_trends(limit=limit)
