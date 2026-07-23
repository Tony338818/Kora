from ai.validator import validator
from schema.conversation_schema import ConversationState
from dependency.db import get_db
from services.dispatch_service import dispatch
from dependency.session import session_service
from ai.chatbot import chatbot
from ai.inventory_bot import inventorybot
from ai.sales_bot import salesbot
from ai.semantic_router import SemanticRouter
from sqlalchemy.orm import Session



async def process_message(
    db: Session, 
    message: str, 
    router: SemanticRouter, 
    session: ConversationState):


    # 1. Route intent
    route = router.route(
        user_query=message,
        session=session.model_dump()
    )

    convo_class = route.get(
        "best_route"
    )
    
    # Casual Conversation Bot

    if convo_class == "casual_conversation":
            response = chatbot(message, session.model_dump())

            # Synchronous in-memory update (no await)
            session_service.add_message(session, "assistant", response)

            return {
                "success": True,
                "message": response
            }
        
        
    # Inventory Management
    elif convo_class == "inventory_conversation":

        response = inventorybot(message=message, session=session.model_dump())

        if isinstance(response, dict) and response.get("error"):
            return {"success": False, "message": "LLM down"}

        intent = response.get("intent")
        data = response.get("data") or {}

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
            result = dispatch(db, session.user_id, intent, session.task.slots)
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


def build_missing_fields_message(missing_fields: list[str]) -> str:
    # 1. Convert 'product_name' -> 'product name'
    readable = [field.replace("_", " ") for field in missing_fields]
    
    # 2. Join fields into a natural phrase
    if len(readable) == 1:
        fields_str = readable[0]
    elif len(readable) == 2:
        fields_str = f"{readable[0]} and {readable[1]}"
    else:
        fields_str = f"{', '.join(readable[:-1])}, and {readable[-1]}"
        
    # 3. Return single direct prompt
    return f"Please provide the missing {fields_str} to proceed."