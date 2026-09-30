# API Reference

## `POST /webhook`

Receives incoming WhatsApp messages from Twilio.

Request form fields:
- `Body` — message text
- `From` — sender phone number

Behavior:
- Normalizes phone number and loads session.
- Checks whether the user exists.
- Routes the message through `ai.orchestrator.process_message`.
- Sends the AI response back over WhatsApp.

Response:
- Returns an empty TwiML XML response with HTTP 200.

## `POST /request-otp`

Request an OTP for authentication.

Request body:
```json
{
  "phone_number": "<phone>"
}
```

Behavior:
- Normalizes the phone number.
- Saves OTP in the database.
- Sends OTP via Twilio.

Response:
- JSON with `success`, `message`, and `otp` (for debugging or delivery).

## `POST /verify-otp`

Verify an OTP and create a user account.

Request body:
```json
{
  "phone_number": "<phone>",
  "otp_code": "<code>"
}
```

Behavior:
- Verifies the OTP record and expiry.
- Creates a new user record if verification succeeds.
- Sends a welcome message.

Response:
- JSON with `valid` and `message`.

## Notes

- All endpoints depend on the SQLAlchemy database session from `app/dependency/db.py`.
- The WhatsApp webhook expects form data, not JSON.
- User sessions are stored in memory and are keyed by normalized phone number.
