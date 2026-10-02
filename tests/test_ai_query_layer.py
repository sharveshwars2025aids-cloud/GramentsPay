"""
test_ai_query_layer.py

Comprehensive tests for Step 4: AI Natural-Language Query Layer.
Covers all 18 required test scenarios plus integration and endpoint tests:

1. Employee salary query
2. Employee production query
3. Employee work history query
4. Employee deduction query
5. Employee bonus query
6. Weekly expense query
7. Weekly outsourcing query
8. Weekly security query
9. Department summary query
10. Production summary query
11. Salary summary query
12. Week comparison query
13. Unknown employee handling
14. Ambiguous employee handling
15. Invalid / non-existent week handling
16. Unsupported question handling
17. Attempted database modification rejection
18. Arbitrary SQL injection / execution prevention
19. Full end-to-end integration test
20. FastAPI POST /ai/query endpoint test
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import database
from api.main import app
from ai.schemas import IntentNames, QueryRequest
from ai.safety import validate_query_safety, REJECTION_REASONS
from ai.extractor import extract_intent_and_entities
from ai.resolver import (
    resolve_employee,
    resolve_week,
    resolve_department,
    EmployeeNotFoundError,
    AmbiguousEmployeeError,
    WeekResolutionError,
)
from ai.service import process_ai_query
from ai.config import set_groq_client
from tests.test_phase7_weekly_closing import setup_comprehensive_test_week

client = TestClient(app)


def make_mock_groq_client(mock_json_content: str):
    """Creates a mock Groq client returning predetermined JSON content."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = mock_json_content
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture(scope="module")
def sample_week():
    """Sets up a fully populated test week with verified production, shifts, expenses, etc."""
    return setup_comprehensive_test_week()


@pytest.fixture(autouse=True)
def reset_client():
    """Ensure mock client is cleaned up after each test."""
    yield
    set_groq_client(None)


# ==============================================================================
# 1. EMPLOYEE SALARY QUERY
# ==============================================================================
def test_01_employee_salary_query(sample_week):
    mock = make_mock_groq_client('{"intent": "EMPLOYEE_SALARY", "employee": "RAMESH", "week": "current"}')
    res = process_ai_query("What is Ramesh's salary this week?", client=mock)

    assert res.intent == IntentNames.EMPLOYEE_SALARY
    assert res.data is not None
    assert res.data["employee_name"] == "RAMESH"
    assert "piece_salary" in res.data
    assert "net_salary" in res.data
    assert "₹" in res.answer or "Ramesh" in res.answer


# ==============================================================================
# 2. EMPLOYEE PRODUCTION QUERY
# ==============================================================================
def test_02_employee_production_query(sample_week):
    mock = make_mock_groq_client('{"intent": "EMPLOYEE_PRODUCTION", "employee": "RAMESH", "date": null, "week": "current"}')
    res = process_ai_query("What did Ramesh produce this week?", client=mock)

    assert res.intent == IntentNames.EMPLOYEE_PRODUCTION
    assert res.data is not None
    assert res.data["employee_name"] == "RAMESH"
    assert "total_qty" in res.data
    assert "total_amount" in res.data


# ==============================================================================
# 3. EMPLOYEE WORK HISTORY QUERY
# ==============================================================================
def test_03_employee_work_history_query(sample_week):
    mock = make_mock_groq_client('{"intent": "EMPLOYEE_WORK_HISTORY", "employee": "RAMESH"}')
    res = process_ai_query("Show me Ramesh's work history.", client=mock)

    assert res.intent == IntentNames.EMPLOYEE_WORK_HISTORY
    assert res.data is not None
    assert res.data["employee_name"] == "RAMESH"
    assert "total_pieces_produced" in res.data
    assert "recent_production" in res.data


# ==============================================================================
# 4. EMPLOYEE DEDUCTION QUERY
# ==============================================================================
def test_04_employee_deduction_query(sample_week):
    mock = make_mock_groq_client('{"intent": "EMPLOYEE_DEDUCTION", "employee": "RAMESH", "week": "current"}')
    res = process_ai_query("What deductions does Ramesh have this week?", client=mock)

    assert res.intent == IntentNames.EMPLOYEE_DEDUCTION
    assert res.data is not None
    assert res.data["employee_name"] == "RAMESH"
    assert "total_deduction" in res.data
    assert "deductions" in res.data


# ==============================================================================
# 5. EMPLOYEE BONUS QUERY
# ==============================================================================
def test_05_employee_bonus_query(sample_week):
    mock = make_mock_groq_client('{"intent": "EMPLOYEE_BONUS", "employee": "RAMESH", "week": "current"}')
    res = process_ai_query("Did Ramesh receive a bonus this week?", client=mock)

    assert res.intent == IntentNames.EMPLOYEE_BONUS
    assert res.data is not None
    assert res.data["employee_name"] == "RAMESH"
    assert "total_bonus" in res.data
    assert "bonuses" in res.data


# ==============================================================================
# 6. WEEKLY EXPENSE QUERY
# ==============================================================================
def test_06_weekly_expense_query(sample_week):
    mock = make_mock_groq_client('{"intent": "WEEKLY_EXPENSE", "week": "current"}')
    res = process_ai_query("How much did we spend this week?", client=mock)

    assert res.intent == IntentNames.WEEKLY_EXPENSE
    assert res.data is not None
    assert "factory_expenses_total" in res.data
    assert "by_category" in res.data


# ==============================================================================
# 7. WEEKLY OUTSOURCING QUERY
# ==============================================================================
def test_07_weekly_outsourcing_query(sample_week):
    mock = make_mock_groq_client('{"intent": "WEEKLY_OUTSOURCING", "week": "current"}')
    res = process_ai_query("Show this week's outsourced work.", client=mock)

    assert res.intent == IntentNames.WEEKLY_OUTSOURCING
    assert res.data is not None
    assert "total_amount" in res.data
    assert "items" in res.data


# ==============================================================================
# 8. WEEKLY SECURITY QUERY
# ==============================================================================
def test_08_weekly_security_query(sample_week):
    mock = make_mock_groq_client('{"intent": "WEEKLY_SECURITY", "week": "current"}')
    res = process_ai_query("How much was paid for security this week?", client=mock)

    assert res.intent == IntentNames.WEEKLY_SECURITY
    assert res.data is not None
    assert "total_amount" in res.data
    assert "items" in res.data


# ==============================================================================
# 9. DEPARTMENT SUMMARY QUERY
# ==============================================================================
def test_09_department_summary_query(sample_week):
    mock = make_mock_groq_client('{"intent": "DEPARTMENT_SUMMARY", "department": "POWERTABLE", "week": "current"}')
    res = process_ai_query("Show me the POWERTABLE department summary.", client=mock)

    assert res.intent == IntentNames.DEPARTMENT_SUMMARY
    assert res.data is not None
    assert res.data.get("department") == "POWERTABLE" or "departments" in res.data


# ==============================================================================
# 10. PRODUCTION SUMMARY QUERY
# ==============================================================================
def test_10_production_summary_query(sample_week):
    mock = make_mock_groq_client('{"intent": "PRODUCTION_SUMMARY", "week": "current"}')
    res = process_ai_query("How much production was completed this week?", client=mock)

    assert res.intent == IntentNames.PRODUCTION_SUMMARY
    assert res.data is not None
    assert "total_quantity" in res.data
    assert "total_amount" in res.data


# ==============================================================================
# 11. SALARY SUMMARY QUERY
# ==============================================================================
def test_11_salary_summary_query(sample_week):
    mock = make_mock_groq_client('{"intent": "SALARY_SUMMARY", "week": "current"}')
    res = process_ai_query("Show me the salary summary for this week.", client=mock)

    assert res.intent == IntentNames.SALARY_SUMMARY
    assert res.data is not None
    assert "net_salary" in res.data
    assert "gross_salary" in res.data


# ==============================================================================
# 12. WEEK COMPARISON QUERY
# ==============================================================================
def test_12_week_comparison_query(sample_week):
    mock = make_mock_groq_client('{"intent": "WEEK_COMPARISON", "week": "current", "compare_week": "last week"}')
    res = process_ai_query("Compare this week with last week.", client=mock)

    assert res.intent == IntentNames.WEEK_COMPARISON
    assert res.data is not None
    assert "week_1" in res.data
    assert "week_2" in res.data
    assert "comparison" in res.data


# ==============================================================================
# 13. UNKNOWN EMPLOYEE HANDLING
# ==============================================================================
def test_13_unknown_employee_handling(sample_week):
    mock = make_mock_groq_client('{"intent": "EMPLOYEE_SALARY", "employee": "NonExistentGhostWorker", "week": "current"}')
    res = process_ai_query("What is NonExistentGhostWorker's salary?", client=mock)

    assert "I couldn't find an employee matching" in res.answer
    assert res.data == {"error": "employee_not_found"}


# ==============================================================================
# 14. AMBIGUOUS EMPLOYEE HANDLING
# ==============================================================================
def test_14_ambiguous_employee_handling(sample_week):
    # Ensure two employees share prefix 'TEST_AMBIG_'
    conn = database.connect_database()
    cur = conn.cursor()
    cur.execute("SELECT id FROM employees WHERE employee_code = 'E901'")
    if not cur.fetchone():
        cur.execute("INSERT INTO employees (employee_code, name, pay_type) VALUES ('E901', 'TEST_AMBIG_ALICE', 'PIECE')")
        cur.execute("INSERT INTO employees (employee_code, name, pay_type) VALUES ('E902', 'TEST_AMBIG_BOB', 'PIECE')")
        conn.commit()
    conn.close()

    mock = make_mock_groq_client('{"intent": "EMPLOYEE_SALARY", "employee": "TEST_AMBIG", "week": "current"}')
    res = process_ai_query("What is TEST_AMBIG's salary?", client=mock)

    assert "multiple employees matching" in res.answer
    assert res.data is not None
    assert res.data["error"] == "ambiguous_employee"


# ==============================================================================
# 15. INVALID / NON-EXISTENT WEEK HANDLING
# ==============================================================================
def test_15_invalid_week_handling():
    mock = make_mock_groq_client('{"intent": "SALARY_SUMMARY", "week": "week 9999999"}')
    res = process_ai_query("Show me salary summary for week 9999999", client=mock)

    assert "I couldn't find a week matching" in res.answer
    assert res.data == {"error": "week_not_found"}


# ==============================================================================
# 16. UNSUPPORTED QUESTION HANDLING
# ==============================================================================
def test_16_unsupported_question_handling():
    mock = make_mock_groq_client('{"intent": "UNSUPPORTED"}')
    res = process_ai_query("How many rings does Saturn have?", client=mock)

    assert res.intent == IntentNames.UNSUPPORTED
    assert "I can currently answer questions about salaries" in res.answer
    assert res.data is None


# ==============================================================================
# 17. ATTEMPTED DATABASE MODIFICATION REJECTION
# ==============================================================================
def test_17_attempted_database_modification():
    mutation_questions = [
        "Delete Ravi.",
        "Change Ravi's salary to 5000.",
        "Update his rate to 25.",
        "Drop table employees",
        "Set Ravi bonus to 1000",
        "Remove employee E012",
    ]
    for q in mutation_questions:
        res = process_ai_query(q)
        assert res.intent == IntentNames.REJECTED_WRITE
        assert "Database modification requests are rejected" in res.answer
        assert res.data is None


# ==============================================================================
# 18. ARBITRARY SQL INJECTION / ARBITRARY EXECUTION PREVENTION
# ==============================================================================
def test_18_sql_injection_prevention():
    sql_attacks = [
        "SELECT * FROM employees WHERE 1=1",
        "Ravi' OR '1'='1",
        "UNION SELECT password FROM users --",
        "'; DROP TABLE weeks; --",
        "INSERT INTO employees (name) VALUES ('Hacker')",
    ]
    for q in sql_attacks:
        res = process_ai_query(q)
        assert res.intent in (IntentNames.REJECTED_SQL, IntentNames.REJECTED_WRITE)
        assert "not permitted" in res.answer or "rejected" in res.answer
        assert res.data is None


# ==============================================================================
# 19. INTEGRATION-STYLE TEST: NL -> STRUCTURED INTENT -> RESOLUTION -> ROUTING -> RESPONSE
# ==============================================================================
def test_19_controlled_integration_pipeline(sample_week):
    question = "What is Suresh's salary this week?"
    mock = make_mock_groq_client('{"intent": "EMPLOYEE_SALARY", "employee": "SURESH", "week": "current"}')

    # Step 1: Safety
    safe, _, _ = validate_query_safety(question)
    assert safe is True

    # Step 2: Extraction
    interp = extract_intent_and_entities(question, client=mock)
    assert interp.intent == IntentNames.EMPLOYEE_SALARY
    assert interp.employee == "SURESH"

    # Step 3: End-to-end service
    res = process_ai_query(question, client=mock)
    assert res.intent == IntentNames.EMPLOYEE_SALARY
    assert res.data["employee_name"] == "SURESH"
    assert res.data["shift_salary"] > 0
    assert "₹" in res.answer


# ==============================================================================
# 20. FASTAPI POST /ai/query ENDPOINT TEST
# ==============================================================================
def test_20_fastapi_ai_endpoint(sample_week):
    mock = make_mock_groq_client('{"intent": "WEEKLY_EXPENSE", "week": "current"}')
    set_groq_client(mock)

    payload = {"question": "How much did we spend this week?"}
    response = client.post("/ai/query", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == payload["question"]
    assert data["intent"] == IntentNames.WEEKLY_EXPENSE
    assert "factory_expenses_total" in data["data"]
    assert len(data["answer"]) > 10
