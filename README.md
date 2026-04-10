# Flagship Project

## Overview

This project is an AI-powered retail operations assistant built with FastAPI. It connects a WhatsApp webhook to a smart message router, uses embedded semantic classification to route conversations, and executes inventory or sales tasks through a SQLAlchemy-backed persistence layer.

Key capabilities:
- WhatsApp webhook handling through Twilio
- User authentication via OTP
- Session-aware conversational AI routing
- Inventory management and sales transaction recording
- In-memory session state for task persistence
- AI prompt orchestration using Google Gemini and sentence embeddings

## Architecture

The application is organized into these main subsystems:
- `app/main.py` — FastAPI app, webhook, OTP endpoints, session and router initialization
- `app/ai/` — AI routing and generation logic
- `app/services/` — backend business logic and database operations
- `app/dependency/` — database and session dependency helpers
- `app/schema/` — SQLAlchemy models and Pydantic schemas

## Quick Start

1. Install dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r .\app\requirements.txt
   ```

2. Create a `.env` file with the required variables (see `docs/setup.md`).

3. Run the app:
   ```powershell
   uvicorn app.main:app --reload
   ```

4. Use Twilio to point a WhatsApp webhook to `POST /webhook`.

## Endpoints

- `POST /webhook` — receive incoming WhatsApp message payloads
- `POST /request-otp` — request SMS/WhatsApp OTP for user authentication
- `POST /verify-otp` — verify OTP and create a new user record

## Documentation

The full project documentation is available in the `docs/` folder:
- `docs/architecture.md`
- `docs/services.md`
- `docs/api.md`
- `docs/dependencies.md`
- `docs/setup.md`
- `docs/testing.md`

## Notes

- Database configuration is controlled by `DATABASE_URL`.
- AI services require `GEMINI_API_KEY`.
- Twilio messaging requires `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`.
- The project loads a local embeddings file at `app/route_embeddings.pt` for routing.
