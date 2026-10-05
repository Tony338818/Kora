from ai.validator import validator
from schema.conversation_schema import ConversationState
from dependency.db import get_db
from services.dispatch_service import dispatch
from dependency.session import session_service
from ai.chatbot import chatbot
from ai.inventory_bot import inventorybot, inventory_spacy_model
from ai.sales_bot import salesbot
from sqlalchemy.orm import Session
from fastapi import Request
from utils.normalize_model_output import normalize_inventory_entities



async def process_message(
    db: Session, 
    user_id: str,
    message: str, 
    session: ConversationState,
    request: Request):
    
    conversation_model = request.app.state.conversation_classifier
    labels, scores = conversation_model.predict(message)

    convo_class = labels[0].replace("__label__", "").lower()

    intent_model = request.app.state.inventory_classifier
    labels, scores = intent_model.predict(message)
    intent_class = labels[0].replace("__label__", "").lower()
    
    # Casual Conversation Bot
    if convo_class == "casual":
            response = chatbot(message, session.model_dump())

            # Synchronous in-memory update (no await)
            session_service.add_message(session, "assistant", response)

            return {
                "success": True,
                "message": response
            }
        
    # Inventory Management
    elif convo_class == "inventory":
        # response = inventorybot(message=message, session=session.model_dump())
        response = inventory_spacy_model(message=message, request=request)

        intent = intent_class
        data = normalize_inventory_entities(response)

        # Preserve existing intent if LLM didn't return a new one
        existing_intent = session.task.intent
        if existing_intent and not intent:
            intent = existing_intent

        # Update slots in memory
        session_service.update_task(session=session, intent=intent, slots=data)
        
        print(session.task.slots)
        valid = validator(
            msg_class=convo_class,
            intent=intent,
            data=session.task.slots
        )

        if valid["valid"]:

            result = dispatch(
                db,
                user_id,
                intent,
                session.task.slots
            )

            session_service.clear_task(
                session=session
            )

            bot_msg = (
                result.get(
                    "message",
                    "Done."
                )
                if isinstance(result, dict)
                else str(result)
            )

        else:

            # If validator already has a specific error message,
            # use it.
            if valid.get("message"):
                bot_msg = valid["message"]

            else:
                bot_msg = build_missing_fields_message(
                    missing_fields=valid.get(
                        "missing_fields",
                        []
                    ),
                    intent=intent
                )

        session_service.add_message(
            session,
            "assistant",
            bot_msg
        )

        return {
            "success": valid["valid"],
            "message": bot_msg
        }
                
    elif convo_class == "sales_conversation":
        response = salesbot(message=message, session=session.model_dump())

        if isinstance(response, dict) and response.get("error"):
            return {"success": False, "message": "LLM down"}

        intent = response.get("intent")
        data = response.get("data") or {}

        # Preserve existing intent if the LLM didn't return a new one
        task = session.task
        existing_intent = task.intent

        if existing_intent and not intent:
            intent = existing_intent

        # 1. Update task slots in memory
        session_service.update_task(
            session=session,
            intent=intent,
            slots=data
        )

        # 2. Validate merged slots
        valid = validator(
            msg_class=convo_class,
            intent=intent,
            data=session.task.slots
        )

        if valid.get("valid"):
            # Task is complete! Dispatch to database/service and clear task
            result = dispatch(db, session.user_id, intent, session.task.slots)
            session_service.clear_task(session=session)

            bot_msg = result.get("message", "Task completed!") if isinstance(result, dict) else str(result)
            session_service.add_message(session, "assistant", bot_msg)
            return {"success": True, "message": bot_msg}

        else:
            # Task is incomplete — ask user for missing fields
            missing_fields = valid.get("missing_fields", [])
            bot_msg = build_missing_fields_message(missing_fields)
            session_service.add_message(session, "assistant", bot_msg)
            return {"success": False, "message": bot_msg}
            
    return response


FIELD_LABELS = {
    "name": "product name",
    "product_name": "product name",
    "quantity": "quantity",
    "cost_price": "cost price",
    "selling_price": "selling price",
    "unit_price": "price",
    "available": "availability",
    "transaction_id": "transaction ID",
    "items": "items",
}


def build_missing_fields_message(
    missing_fields: list[str],
    intent: str
) -> str:

    if not missing_fields:
        return "I need a bit more information to complete that."

    missing = set(missing_fields)

    # -----------------------------------------------------
    # Add product
    # -----------------------------------------------------

    if intent == "add_product":

        if missing == {
            "name",
            "quantity",
            "cost_price",
            "selling_price",
        }:
            return (
                "What product are you adding, how many, "
                "and what's the cost and selling price?"
            )

        if missing == {
            "quantity",
            "cost_price",
            "selling_price",
        }:
            return (
                "How many are you adding, and what's the "
                "cost and selling price?"
            )

        if missing == {
            "cost_price",
            "selling_price",
        }:
            return "What's the cost and selling price?"

        if missing == {
            "quantity",
            "cost_price",
        }:
            return (
                "How many are you adding, and what's the cost price?"
            )

        if missing == {
            "quantity",
            "selling_price",
        }:
            return (
                "How many are you adding, and what's the selling price?"
            )

    # -----------------------------------------------------
    # Stock changes
    # -----------------------------------------------------

    if intent in [
        "increment_stock_quantity",
        "decrement_stock_quantity",
    ]:
        if missing == {"name", "quantity"}:
            return "Which product, and how many units?"

        if "name" in missing:
            return "Which product?"

        if "quantity" in missing:
            return "How many units?"

    # -----------------------------------------------------
    # Prices
    # -----------------------------------------------------

    if intent == "update_cost_price":
        if missing == {"name", "cost_price"}:
            return "Which product, and what's the new cost price?"

        if "name" in missing:
            return "Which product?"

        if "cost_price" in missing:
            return "What's the new cost price?"

    if intent == "update_selling_price":
        if missing == {"name", "selling_price"}:
            return "Which product, and what's the new selling price?"

        if "name" in missing:
            return "Which product?"

        if "selling_price" in missing:
            return "What's the new selling price?"

    # -----------------------------------------------------
    # Availability
    # -----------------------------------------------------

    if intent == "change_product_availabilty":
        if missing == {"name", "available"}:
            return (
                "Which product, and should it be available "
                "or unavailable?"
            )

        if "name" in missing:
            return "Which product?"

        if "available" in missing:
            return "Should it be available or unavailable?"

    # -----------------------------------------------------
    # Sales / purchases
    # -----------------------------------------------------

    if intent in ["record_sale", "record_purchase"]:

        if "items" in missing:
            return "What did you sell?" if intent == "record_sale" else \
                   "What did you purchase?"

        if missing == {
            "product_name",
            "quantity",
            "unit_price",
        }:
            return (
                "Which product, how many, and at what price?"
            )

        if missing == {"quantity", "unit_price"}:
            return "How many, and at what price?"

        if "product_name" in missing:
            return "Which product?"

        if "quantity" in missing:
            return "How many?"

        if "unit_price" in missing:
            return "At what price?"

    # -----------------------------------------------------
    # Transaction
    # -----------------------------------------------------

    if "transaction_id" in missing:
        return "What's the transaction ID?"

    # -----------------------------------------------------
    # Generic fallback
    # -----------------------------------------------------

    fields = [
        FIELD_LABELS.get(
            field,
            field.replace("_", " ")
        )
        for field in missing_fields
    ]

    if len(fields) == 1:
        return f"What's the {fields[0]}?"

    if len(fields) == 2:
        return f"What's the {fields[0]} and {fields[1]}?"

    return (
        f"What's the {', '.join(fields[:-1])}, "
        f"and {fields[-1]}?"
    )