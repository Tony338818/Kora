from fastapi import APIRouter, Depends, Form, Request, Response
from ai.orchestrator import process_message
from ai.semantic_router import SemanticRouter
from services.messaging_service import send_message
from services.user_service import read_user
from dependency.db import get_db
from sqlalchemy.orm import Session
from utils.normalize_phone import normalize_phone_numbers
from dependency.session import session_service

router = APIRouter(prefix='/conversations')


def get_semantic_router(request: Request):
    return request.app.state.semantic_router

@router.post('/')
async def recieve_user_query(
    sender: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db),
):
    phone = normalize_phone_numbers(sender)
    

    user = read_user(
            db=db,
            phone_number=phone
        )

    if not user.get("exists"):
        return Response(
            status_code=200,
            content='User does not exist in the DB!'
        )
        
    session = await session_service.get(
        phone
    )
    
    if not session:

        session = await session_service.create(
            phone
        )
        
    session_service.add_message(
        session,
        "user",
        message
    )
      
    result = await process_message(db=db, user_id=user.get('user_id'), message=message, session=session)
    print(result)
    # send_message(message=result.get('message'), phone=number)
    
    await session_service.save(session)
    

    return {"message": "All recieved!", "result": result}

