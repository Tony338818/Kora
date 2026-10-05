# Testing

## Test Framework

This project uses `pytest`.

## Existing Tests

- `tests/conftest.py`
  - Defines an in-memory SQLite engine fixture.
- `tests/db/test_db.py`
  - Verifies that database tables exist and primary keys are configured.

## Run Tests

```powershell
pytest
```

## Recommended Improvements

The current test coverage is minimal. Recommended next tests:
- service-level tests for `inventory_service` and `transaction_service`
- validation tests for `ai/validator.py`
- session lifecycle tests for `app/dependency/session.py`
- endpoint tests for `app/main.py` using FastAPI `TestClient`

## Notes

- The in-memory SQLite fixture does not persist data between tests.
- For API tests, create a separate test client and mock external integrations like Twilio and Gemini.
