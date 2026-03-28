from ai.intent_model import recognize_intent
from ai.validator import validator
from dependency.session import get_session, update_session, append_history
from ai.model_router import model_router
from ai.chatbot import chatbot
from ai.inventory_bot import inventorybot


# def process_message(user_id: str, message: str) -> dict:
    # """
    # Full pipeline:
    # 1. Load session
    # 2. Call LLM with session data
    # 3. Handle clarification / final / unknown
    # """

    # # Load session
    # session = get_session(user_id)
    # session_data = session.get("data", {})

    # # Call LLM
    # llm_result = recognize_intent(message, session_data)
    # response_type = llm_result.get("type")

    # # ── UNKNOWN / ERROR ─────────────────────────────
    # if response_type in ("unknown", "error"):
    #     return {
    #         "status": "unknown",
    #         "message": llm_result.get("message", "I didn't understand that.")
    #     }

    # # ── CLARIFICATION ───────────────────────────────
    # if response_type == "clarification":
    #     update_session(user_id, {
    #         "intent": llm_result.get("intent"),
    #         "class": llm_result.get("class"),
    #         "data": llm_result.get("data", {})
    #     })

    #     return {
    #         "status": "clarification",
    #         "message": llm_result.get("message"),
    #         "missing_fields": llm_result.get("missing_fields", [])
    #     }

    # # ── FINAL → VALIDATE ────────────────────────────
    # if response_type == "final":
    #     msg_class = llm_result.get("class")
    #     intent = llm_result.get("intent")
    #     data = llm_result.get("data", {})

    #     validation = validator(msg_class, intent, data)

    #     # VALID → CALL API
    #     if validation["valid"]:
    #         clear_session(user_id)

    #         return {
    #             "status": "ready",
    #             "action": "call_api",
    #             "class": msg_class,
    #             "intent": intent,
    #             "data": data
    #         }

    #     # INVALID → ASK AGAIN
    #     else:
    #         update_session(user_id, {
    #             "intent": intent,
    #             "class": msg_class,
    #             "data": data
    #         })

    #         missing_fields = [e["field"] for e in validation["errors"]]

    #         return {
    #             "status": "clarification",
    #             "message": _fields_to_question(missing_fields),
    #             "missing_fields": missing_fields
    #         }

    # return {
    #     "status": "error",
    #     "message": "Unexpected response from model."
    # }


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


def process_message(user_id: str, message: str):
    """
    1) Get user the message and Load session
    2) Classify the message and call the right model
    3) LLM extracts intent and data
    4) Call Validator
    5) Call Backend
    6) send message to user
    """

    
    # Load session
    session = get_session(user_id)
    session_intent = session.get('intent')
    session_data = session.get("data", {})
    
    # classify    
    route = model_router(message=message, session=session)

    # routing
    convo_class = route.get('conversation_class')
    if convo_class == 'casual_conversation':
        response = chatbot(message, session)
        
        update_session(
            user_id=user_id,
            updates={
                "mode": "chat",
                "last_intent": "casual_conversation",
                "last_message": message,
                # add the bots response as well
                "task": None
            }
        )

        append_history(user_id, {
            "type": "chat",
            "message": message
        })
        return response
    elif convo_class == 'inventory_query':
        response = inventorybot(message=message, session=session)
        
        # update_session(
        #     user_id=user_id,
        #     updates= {
        #         "mode": 'task'
        #     }
        # )
        return response
    # elif convo_class == 'inventory_query':
    #     extraction = inventorybot(message=message, session=session)

    #     if "intent" not in extraction or "data" not in extraction:
    #         return chatbot(message, session)

    #     intent = extraction.get("intent")
    #     data = extraction.get("data", {})

    #     # # If model fails → fallback to chat
    #     # if intent is None:
    #     #     return chatbot(message, session)

    #     # current_task = session.get("task") or {
    #     #     "intent": None,
    #     #     "data": {},
    #     #     "status": "idle"
    #     # }

    #     # # 🔥 TASK STATE MANAGEMENT

    #     # # 1. Start new task
    #     # if current_task["intent"] is None:
    #     #     current_task["intent"] = intent
    #     #     current_task["status"] = "in_progress"

    #     # # 2. User switched intent → reset task
    #     # elif current_task["intent"] != intent:
    #     #     current_task = {
    #     #         "intent": intent,
    #     #         "data": {},
    #     #         "status": "in_progress"
    #     #     }

    #     # # 3. Merge extracted data
    #     # current_task["data"].update(data)

    #     # # 4. Save session
    #     # update_session(
    #     #     user_id=user_id,
    #     #     updates={
    #     #         "mode": "task",
    #     #         "task": current_task,
    #     #         "last_intent": intent,
    #     #         "last_message": message
    #     #     }
    #     # )

    #     # append_history(user_id, {
    #     #     "type": "task",
    #     #     "message": message
    #     # })
        
    return