from ai.validator import validator
from dependency.db import get_db
from services.dispatch_service import dispatch
from dependency.session import get_session, update_session, append_history, clear_task
from ai.chatbot import chatbot
from ai.inventory_bot import inventorybot
from ai.sales_bot import salesbot
from ai.semantic_router import SemanticRouter
from sqlalchemy.orm import Session


router = SemanticRouter()
def process_message(db: Session, user_id: str, message: str):
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
    route = router.route(user_query=message, session=session)

    # routing
    convo_class = route.get('best_route')
    if convo_class == 'casual_conversation':
        response = chatbot(message, session)

        update_session(
            user_id=user_id,
            updates={
                "mode": "chat",
                "last_intent": convo_class,
                "last_message": message,
                "task": None
            }
        )

        append_history(user_id, {
            "type": convo_class,
            "message": message,
            "bot_response": response,
        })
        return response    
    elif convo_class == 'inventory_conversation':

        response = inventorybot(message=message, session=session)
        
        if response.get('error'):
            response = 'LLM down'
            return response

        intent = response.get('intent')
        data = response.get('data') or {}

        task = session.get("task") or {}

        existing_data = task.get("collected_data", {})
        existing_intent = task.get("intent")

        # preserve intent
        if existing_intent and intent is None:
            intent = existing_intent

        # merge data
        merged_data = {**existing_data, **data}

        # validate merged data
        valid = validator(
            msg_class=convo_class,
            intent=intent,
            data=merged_data
        )

        # update session
        update_session(
            user_id=user_id,
            updates={
                "mode": "task",
                "last_intent": convo_class,
                "last_message": message,
                "task": {
                    "intent": intent,
                    "collected_data": merged_data,
                    "status": "in_progress"
                }
            }
        )

        append_history(user_id, {
            "type": convo_class,
            "message": message,
            "bot_response": response
        })

        # handle result
        if valid["valid"]:
            print(f'user_id {user_id}')
            print(f'intent: {intent}')
            print(f'data: {merged_data}')
            result = dispatch(db, user_id, intent, merged_data)
            clear_task(user_id)
            return result

        return {
            "status": "incomplete",
            "missing_fields": [e["field"] for e in valid["errors"]],
            "message": "Provide missing fields"
        }
        
    elif convo_class == 'sales_conversation':
        response = salesbot(message, session)

        if response.get('error'):
            return 'LLM down'

        intent = response.get('intent')
        data = response.get('data') or {}

        task = session.get("task") or {}

        existing_data = task.get("collected_data", {})
        existing_intent = task.get("intent")

        # preserve intent ONLY if LLM didn't return one
        if existing_intent and intent is None:
            intent = existing_intent

        # merge data
        merged_data = {**existing_data, **data}

        # # enrich with DB (your rule)
        # if intent in ["record_sale", "record_purchase"]:
        #     if "items" in merged_data:
        #         merged_data["items"] = enrich_items_with_price(merged_data["items"])

        # validate
        valid = validator(
            msg_class=convo_class,
            intent=intent,
            data=merged_data
        )

        # update session
        update_session(
            user_id=user_id,
            updates={
                "mode": "task",
                "last_intent": convo_class,
                "last_message": message,
                "task": {
                    "intent": intent,
                    "collected_data": merged_data,
                    "status": "in_progress"
                }
            }
        )

        append_history(user_id, {
            "type": convo_class,
            "message": message,
            "bot_response": response
        })

        if valid["valid"]:
            print(f'user_id {user_id}')
            print(f'intent: {intent}')
            print(f'data: {merged_data}')
            result = dispatch(db, user_id, intent, merged_data)
            clear_task(user_id)
            return result

        return {
            "status": "incomplete",
            "missing_fields": [e["field"] for e in valid["errors"]],
            "message": "Provide missing fields"
        }
    return


if __name__ == "__main__":
    db = next(get_db())
    
    while True:
        
        message = input('You: ')
        if message == 'quit' or message == 'exit':
            break
        
        response = process_message(db=db, user_id='whatsapp:+2349133881829', message=message)
        print(f'Bot: {response}')
        
    