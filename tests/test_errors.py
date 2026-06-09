import pytest
from fastapi.responses import JSONResponse

from shared_core.errors import (
    DatabaseError,
    ValidationError,
    application_error_handler,
)


def test_exceptions_structure():
    err = ValidationError("Input was invalid")
    assert err.code == "VALIDATION_ERROR"
    assert err.status_code == 400
    assert err.message == "Input was invalid"

    db_err = DatabaseError("Query failed")
    assert db_err.code == "DATABASE_ERROR"
    assert db_err.status_code == 500


@pytest.mark.anyio
async def test_application_error_handler():
    # Simulate FastAPI request
    exc = ValidationError("Bad input payload")

    # We pass None as Request for testing as handler only reads from exc
    response = await application_error_handler(None, exc)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400

    body = response.body.decode("utf-8")
    assert "VALIDATION_ERROR" in body
    assert "Bad input payload" in body
