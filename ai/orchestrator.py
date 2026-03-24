
# FIELD_QUESTIONS = {
#     "name": "What product are you referring to?",
#     "quantity": "How many units?",
#     "selling_price": "What is the selling price?",
#     "cost_price": "What is the cost price?",
# }

# def process_message(message: str, session: dict) -> dict:
#     """
#     Pipeline:
#     1. Feed message + session to LLM (LLM handles merging with prior session data)
#     2. If clarification → save partial data to session, return follow-up to user
#     3. If final → validate
#        - Valid   → return ready payload for API call
#        - Invalid → save partial data to session, return clarification to user
#     4. If unknown/error → return as-is
#     """
 
#     session_data = session.get("data", {})
#     llm_result = recognize_intent(message, session_data)
#     response_type = llm_result.get("type")
 
#     # ── LLM couldn't understand ──────────────────────────────────────────────
#     if response_type in ("unknown", "error"):
#         return {
#             "status": "unknown",
#             "message": llm_result.get("message", "I didn't understand that.")
#         }
 
#     # ── LLM needs more info from the user ────────────────────────────────────
#     if response_type == "clarification":
#         # Persist whatever partial data the LLM extracted so far
#         create_session(message, {
#             "intent": llm_result.get("intent"),
#             "class":  llm_result.get("class"),
#             "data":   llm_result.get("data", {}),
#         })
 
#         return {
#             "status":         "clarification",
#             "message":        llm_result.get("message"),
#             "missing_fields": llm_result.get("missing_fields", []),
#         }
 
#     # ── LLM thinks it has everything — validate ───────────────────────────────
#     if response_type == "final":
#         msg_class = llm_result.get("class")
#         intent    = llm_result.get("intent")
#         data      = llm_result.get("data", {})
 
#         validation = validator(msg_class, intent, data)
 
#         if validation["valid"]:
#             # Clear session — conversation is complete
#             create_session(message, None)
 
#             return {
#                 "status": "ready",
#                 "action": "call_api",
#                 "class":  msg_class,
#                 "intent": intent,
#                 "data":   data,
#             }
 
#         else:
#             # LLM thought it was done but validation caught gaps — save partial
#             # data to session so the next user message still has context, and
#             # surface the missing fields for the caller to prompt the user.
#             create_session(message, {
#                 "intent": intent,
#                 "class":  msg_class,
#                 "data":   data,
#             })
 
#             missing_fields = [e["field"] for e in validation["errors"]]
 
#             return {
#                 "status":         "clarification",
#                 "message":        _fields_to_question(intent, missing_fields),
#                 "missing_fields": missing_fields,
#             }
 
#     return {"status": "unknown", "message": "Unexpected response from model."}
 
 
# # ── HELPERS ───────────────────────────────────────────────────────────────────
 
# def _fields_to_question(intent: str, missing_fields: list[str]) -> str:
#     """
#     Produce a simple fallback question when the validator rejects a
#     'final' LLM response. This avoids a second LLM call just to rephrase
#     a missing-field error.
#     """
#     readable = {
#         "name":          "the product name",
#         "quantity":      "the quantity",
#         "cost_price":    "the cost price",
#         "selling_price": "the selling price",
#         "available":     "whether the product is available (yes/no)",
#         "transaction_id":"the transaction ID",
#         "items":         "the items (name + quantity) for the sale",
#     }
 
#     labels = [readable.get(f, f) for f in missing_fields]
 
#     if len(labels) == 1:
#         return f"Could you provide {labels[0]}?"
#     last = labels[-1]
#     rest = ", ".join(labels[:-1])
#     return f"Could you provide {rest} and {last}?"


# def _build_error_feedback(intent: str, errors: list) -> str:
#     """
#     Formats validator errors into a prompt the LLM uses
#     to ask the user for the missing/invalid fields.
#     """
#     lines = [
#         f"The user is trying to: {intent}.",
#         "The following fields are missing or invalid:"
#     ]
#     for err in errors:
#         field   = err.get("field", "unknown")
#         message = err.get("message", "invalid value")
#         lines.append(f"  - {field}: {message}")

#     lines.append(
#         "Ask the user a single, natural question to collect this information."
#     )
#     return "\n".join(lines)

from ai.intent_model import recognize_intent
from ai.validator import validator
from dependency.session import get_session, update_session, clear_session


def process_message(user_id: str, message: str) -> dict:
    """
    Full pipeline:
    1. Load session
    2. Call LLM with session data
    3. Handle clarification / final / unknown
    """

    # ✅ Load session
    session = get_session(user_id)
    session_data = session.get("data", {})

    # ✅ Call LLM
    llm_result = recognize_intent(message, session_data)
    response_type = llm_result.get("type")

    # ── UNKNOWN / ERROR ─────────────────────────────
    if response_type in ("unknown", "error"):
        return {
            "status": "unknown",
            "message": llm_result.get("message", "I didn't understand that.")
        }

    # ── CLARIFICATION ───────────────────────────────
    if response_type == "clarification":
        update_session(user_id, {
            "intent": llm_result.get("intent"),
            "class": llm_result.get("class"),
            "data": llm_result.get("data", {})
        })

        return {
            "status": "clarification",
            "message": llm_result.get("message"),
            "missing_fields": llm_result.get("missing_fields", [])
        }

    # ── FINAL → VALIDATE ────────────────────────────
    if response_type == "final":
        msg_class = llm_result.get("class")
        intent = llm_result.get("intent")
        data = llm_result.get("data", {})

        validation = validator(msg_class, intent, data)

        # VALID → CALL API
        if validation["valid"]:
            clear_session(user_id)

            return {
                "status": "ready",
                "action": "call_api",
                "class": msg_class,
                "intent": intent,
                "data": data
            }

        # INVALID → ASK AGAIN
        else:
            update_session(user_id, {
                "intent": intent,
                "class": msg_class,
                "data": data
            })

            missing_fields = [e["field"] for e in validation["errors"]]

            return {
                "status": "clarification",
                "message": _fields_to_question(missing_fields),
                "missing_fields": missing_fields
            }

    return {
        "status": "error",
        "message": "Unexpected response from model."
    }


# ── HELPER ───────────────────────────────────────

def _fields_to_question(missing_fields: list[str]) -> str:
    readable = {
        "name": "the product name",
        "quantity": "the quantity",
        "cost_price": "the cost price",
        "selling_price": "the selling price",
        "available": "whether the product is available (yes/no)",
        "transaction_id": "the transaction ID",
        "items": "the items (name + quantity) for the sale",
    }

    labels = [readable.get(f, f) for f in missing_fields]

    if len(labels) == 1:
        return f"Could you provide {labels[0]}?"

    return f"Could you provide {', '.join(labels[:-1])} and {labels[-1]}?"
