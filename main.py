from fastapi import FastAPI, Form, Response, Depends
from twilio.twiml.messaging_response import MessagingResponse

from ai.orchestrator import process_message
from services.messaging_service import send_message
from dependency.db import get_db
from sqlalchemy.orm import Session

app = FastAPI(
    version='0.1',
    description='Business Operations Support System'
)

@app.post("/webhook")
async def webhook(
    Body: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    ProfileName: str = Form(default=None),
    db: Session = Depends(get_db)
):
    
    print("WEBHOOK HIT")
    print(f"Message: {Body}")
    print(f"From: {From}")

    user_id = From
    message = Body
    
    # Call orchestrator 
    result = await process_message(db=db,user_id=user_id, message=message)
    
    send_message(result, user_id)

    resp = MessagingResponse()
    
    return Response(
        content=str(resp),
        media_type="application/xml"
    )