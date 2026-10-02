"""
ai.py

FastAPI router exposing the controlled natural-language AI query layer.
Endpoint: POST /ai/query
"""

from fastapi import APIRouter
from ai.schemas import QueryRequest, QueryResponse
from ai.service import process_ai_query

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Natural-language read-only factory query endpoint",
)
def handle_ai_query(request: QueryRequest) -> QueryResponse:
    """
    Accepts a natural-language question from an owner or accountant,
    classifies the intent, resolves master data, routes to existing verified backend logic,
    and returns a structured response with a verified natural-language answer.
    """
    return process_ai_query(request.question)
