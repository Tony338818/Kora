from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse

from ai.orchestrator import process_message
from services.messaging_service import send_message

app = FastAPI(
    version='0.1',
    description='Business Operations Support System'
)

@app.post("/webhook")
async def webhook(
    Body: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    ProfileName: str = Form(default=None)
):
    
    print("WEBHOOK HIT")
    print(f"Message: {Body}")
    print(f"From: {From}")

    user_id = From
    message = Body
    
    # Call orchestrator 
    result = process_message(user_id, message)
    
    send_message(result, user_id)

    resp = MessagingResponse()
    
    return Response(
        content=str(resp),
        media_type="application/xml"
    )