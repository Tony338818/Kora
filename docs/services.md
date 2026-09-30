# Services

This document describes the main service modules and their responsibilities.

## `app/services/messaging_service.py`

Provides Twilio messaging support.

Functions:
- `normalize_phone(phone: str) -> str`
  - Normalizes phone numbers to the `+<digits>` format.
- `send_message(message: str, phone: str)`
  - Sends a WhatsApp message using Twilio.
- `send_onboarding_messages(message: str)`
  - Placeholder for onboarding messaging logic.

## `app/services/otp_service.py`

Handles OTP generation and verification.

Functions:
- `generateOTP() -> str`
- `hashOTP(OTP: str) -> str`
- `verify(otp: str, otp_hash: str) -> bool`
- `createOTP(db, data: RequestOTP)`
  - Creates a hashed OTP record and returns the one-time code.
- `verify_otp(db, data: VerifyOTP)`
  - Validates the OTP, checks expiry, and marks it as used.

## `app/services/user_service.py`

Manages user creation and lookup.

Functions:
- `createUser(db, user: UserCreate)`
  - Creates a new `Users` record in the database.
- `readUser(db, phone_number: str)`
  - Finds a user by phone number and returns existence metadata.

## `app/services/inventory_service.py`

Implements inventory CRUD and stock management.

Functions:
- `add_product(db, phone, data)`
- `increment_stock(db, phone, data)`
- `decrement_stock(db, phone, data)`
- `update_cost_price(db, phone, data)`
- `update_selling_price(db, phone, data)`
- `get_product_info(db, phone, data)`
- `delete_product(db, phone, data)`
- `view_inventory(db, phone, data)`

## `app/services/transaction_service.py`

Implements sales and purchase transaction handling.

Functions:
- `record_sale(db, phone, data)`
- `record_purchase(db, phone, data)`
- `create_transaction(db, phone, data, transaction_type)`
- `get_transaction(db, phone, data)`
- `list_transactions(db, phone, data)`
- `generate_receipt(db, phone, data)`

## `app/services/dispatch_service.py`

Routes validated intent names to service handlers.

Handler map includes:
- inventory actions such as `add_product`, `view_inventory`, `delete_product`
- sales actions such as `record_sale`, `get_transaction`, `generate_receipt`

Function:
- `dispatch(db, phone, intent, data) -> str`
