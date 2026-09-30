# Dependencies

This app depends on a combination of web, AI, and database libraries.

## Core runtime dependencies

- `fastapi` — API framework
- `SQLAlchemy` — ORM and database access
- `uvicorn` (recommended) — ASGI server
- `python-dotenv` — environment variable loading
- `bcrypt` — OTP hashing and verification
- `twilio` — WhatsApp message delivery

## AI and NLP

- `sentence-transformers` — semantic embedding model for routing
- `torch` — tensor backend for embeddings
- `google-ai-generativelanguage` / `google-generativeai` — Gemini model client
- `transformers` — NLP tooling dependency
- `spacy` and related packages — language model support

## Database / schema

- `alembic` — database migration support
- `pydantic` — request validation and schema models
- `python-jose`, `jwcrypto` / `jwt` — authentication-related packages are present in the environment

## Testing

- `pytest` — test execution

## Notes

- The project uses `app/requirements.txt` for dependency management.
- Some packages may be installed as transitive dependencies of AI frameworks.
- `route_embeddings.pt` stores precomputed sentence embeddings for router performance.
