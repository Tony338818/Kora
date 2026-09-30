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
    confidence = scores[0]

    intent_model = request.app.state.inventory_classifier
    labels, scores = intent_model.predict(message)
    intent_class = labels[0].replace("__label__", "").lower()
    confidence = scores[0]
    
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

        # Validate merged slots
        valid = validator(
            msg_class=convo_class,
            intent=intent,
            data=session.task.slots
        )
        
        if valid.get("valid"):
            # Execute database action & clear task
            result = dispatch(db, user_id, intent, session.task.slots)
            session_service.clear_task(session=session)

            bot_msg = result.get("message", "Inventory task completed!") if isinstance(result, dict) else str(result)
            session_service.add_message(session, "assistant", bot_msg)
            return {"success": True, "message": bot_msg}

        else:
            # Task incomplete - ask for missing fields
            missing_fields = valid.get("missing_fields", [])
            bot_msg = build_missing_fields_message(missing_fields)
            session_service.add_message(session, "assistant", bot_msg)
            return {"success": False, "message": bot_msg}
                
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


def build_missing_fields_message(missing_fields: list[str] | None) -> str:
    """
    Build a user-friendly message from a list of missing fields.

    Designed to safely handle malformed or empty AI output.
    """

    # Defensive check
    if not missing_fields:
        return "Please provide the required information to proceed."

    # Only keep valid string field names
    valid_fields = [
        field.replace("_", " ").strip()
        for field in missing_fields
        if isinstance(field, str) and field.strip()
    ]

    # If nothing usable was provided
    if not valid_fields:
        return "Please provide the required information to proceed."

    if len(valid_fields) == 1:
        fields_str = valid_fields[0]

    elif len(valid_fields) == 2:
        fields_str = f"{valid_fields[0]} and {valid_fields[1]}"

    else:
        fields_str = f"{', '.join(valid_fields[:-1])}, and {valid_fields[-1]}"

    return f"Please provide the missing {fields_str} to proceed."
