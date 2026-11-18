from fastapi import APIRouter, Depends, Form, Request, Response
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from ai.orchestrator import process_message
from dependency.db import get_db
from services.messaging_service import send_message
from services.user_service import read_user
from utils.normalize_phone import normalize_phone_numbers


router = APIRouter(prefix="/conversations")


@router.post("/")
async def recieve_user_query(
    request: Request,
    sender: str = Form(..., alias="From"),
    message: str = Form(..., alias="Body"),
    message_id: str | None = Form(None, alias="MessageSid"),
    db: Session = Depends(get_db),
):
    phone = normalize_phone_numbers(sender)
    user = read_user(db=db, phone_number=phone)
    if not user.get("exists"):
        return Response(status_code=200, content="User does not exist in the DB!")

    result = await process_message(
        db=db,
        user_id=user["user_id"],
        message=message,
        session_id=phone,
        request=request,
        message_id=message_id,
    )
    if result.get("message"):
        await run_in_threadpool(send_message, message=result["message"], phone=phone)

    return {"message": "All recieved!", "result": result}
