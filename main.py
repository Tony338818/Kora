from fastapi import FastAPI, Form, Response, Depends, Request
from twilio.twiml.messaging_response import MessagingResponse
from ai.orchestrator import process_message
from dependency.current_user import create_token
from services.messaging_service import send_message
from dependency.db import get_db
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from services.otp_service import createOTP, verify_otp
from schema.user_schema import RequestOTP, VerifyOTP

app = FastAPI(
    version='0.1',
    description='Business Operations Support System'
)

template = Jinja2Templates(directory='template')

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

@app.get('/')
def home(request: Request):
    return template.TemplateResponse('index.html', {'request': request})
    
@app.post('/request-otp')
def get_otp(
    data: RequestOTP,
    db: Session = Depends(get_db)):
    
    otp = createOTP(db=db, data=data)
    
    if not otp:
        return {
            'something went wrong1'
        }
        
    return otp

@app.post('/verify-otp')
def check_otp(
    data: VerifyOTP,
    db: Session = Depends(get_db)):
    
    result = verify_otp(db=db, data=data)
    
    if not result:
        return {
            'something went wrong1'
        }
    
    return result
    
    
    