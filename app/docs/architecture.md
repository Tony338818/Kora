# Architecture

## System Overview

This project is designed as a modular AI-driven retail assistant. Incoming messages are received through a FastAPI webhook and passed to a semantic router, which classifies user intent and selects the correct conversation or task handler.

## Core Flow

1. `POST /webhook` receives Twilio form data from WhatsApp.
2. Phone numbers are normalized and user sessions are loaded from `app/dependency/session.py`.
3. The request is routed to the AI orchestrator in `app/ai/orchestrator.py`.
4. The `SemanticRouter` in `app/ai/semantic_router.py` chooses one of:
   - `casual_conversation`
   - `inventory_conversation`
   - `sales_conversation`
5. The selected AI bot interprets the message and returns structured output.
6. The `ai.validator` validates collected data before a backend operation.
7. The `services.dispatch_service.py` dispatches valid intents to the appropriate service handler.
8. The service returns a response string or structured result, which is sent back via Twilio.

## AI and Routing

- `SemanticRouter` uses `sentence-transformers` and an embeddings file (`route_embeddings.pt`) to classify the user query.
- `ai/chatbot.py` handles general conversation.
- `ai/inventory_bot.py` extracts inventory intents and data.
- `ai/sales_bot.py` extracts sales transaction intents and data.
- Prompts are designed for strict JSON-style extraction of intent and payload.

## Session Management

- `app/dependency/session.py` provides an in-memory session store keyed by normalized phone number.
- Sessions expire after 600 seconds.
- Session state includes:
  - `mode`
  - `last_intent`
  - `history`
  - `task`
  - `last_completed_task`

## Data Persistence

- `app/schema/db_schema.py` defines SQLAlchemy models for:
  - `Users`
  - `Products`
  - `Transactions`
  - `TransactionItem`
  - `OTP`
- `app/dependency/db.py` provides a session-scoped database dependency.

## Service Separation

- `app/services/` implements business operations separated by domain.
- `dispatch_service.py` maps intent names to handler functions.
- Inventory and transaction logic are decoupled from request handling.
