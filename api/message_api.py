from fastapi import APIRouter, Depends, Form, Request, Response
from ai.orchestrator import process_message
from ai.semantic_router import SemanticRouter
from services.messaging_service import send_message
from services.user_service import read_user
from dependency.db import get_db
from sqlalchemy.orm import Session
from utils.normalize_phone import normalize_phone_numbers
from dependency.session import get_session, update_session

router = APIRouter(prefix='/conversations')


def get_semantic_router(request: Request):
    return request.app.state.semantic_router

@router.post('/')
async def recieve_user_query(
    sender: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db),
    router: SemanticRouter = Depends(get_semantic_router)
):
    number = normalize_phone_numbers(sender)
    
    session = get_session(number)

    if "user_id" not in session:
        user = read_user(db=db, phone_number=number)

        if not user.get("exists"):
            send_message(
                message="No account found. Please create one on our site.",
                phone=number
            )
            return Response(status_code=200)

        update_session(number, {
            "user_id": user.get("user_id")
        })
        
    result = await process_message(db=db,user_id=number, message=message, router=router)
    print(result)
    # send_message(message=result.get('message'), phone=number)

    return {"message": "All recieved!"}

