from fastapi import FastAPI, Form, Response, Depends, Request
from twilio.twiml.messaging_response import MessagingResponse
from ai.orchestrator import process_message
from dependency.session import get_session, update_session
from services.messaging_service import send_message, normalize_phone
from dependency.db import get_db
from sqlalchemy.orm import Session
from services.otp_service import createOTP, verify_otp
from schema.user_schema import RequestOTP, UserCreate, VerifyOTP
from fastapi.middleware.cors import CORSMiddleware
from services.user_service import createUser, readUser
from ai.semantic_router import SemanticRouter

app = FastAPI(
    version='0.1',
    description='Business Operations Support System'
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event('startup')
async def startup_event():
    global semantic_router
    print("Loading semantic router...")
    semantic_router = SemanticRouter()
    print("Semantic router loaded!")
    
def get_semantic_router() -> SemanticRouter:
    return semantic_router


@app.post("/webhook")
async def webhook(
    Body: str = Form(...),
    From: str = Form(...),
    db: Session = Depends(get_db),
    router: SemanticRouter = Depends(get_semantic_router)
):
    print('Webhook')

    normalized_phone = normalize_phone(From)
    message = Body
    
    session = get_session(normalized_phone)

    if "user_id" not in session:
        user = readUser(db=db, phone_number=normalized_phone)

        if not user.get("exists"):
            send_message(
                message="No account found. Please create one on our site.",
                phone=normalized_phone
            )
            return Response(status_code=200)

        update_session(normalized_phone, {
            "user_id": user.get("user_id")
        })

    # Call orchestrator 
    result = await process_message(db=db,user_id=normalized_phone, message=message, router=router)
    print(result)
    send_message(message=result.get('message'), phone=normalized_phone)

    resp = MessagingResponse()
    
    return Response(
        content=str(resp),
        media_type="application/xml"
    )
    
@app.post('/request-otp')
def get_otp(
    data: RequestOTP,
    db: Session = Depends(get_db)):
    
    normalized_phone = normalize_phone(data.phone_number)
    
    otp = createOTP(db=db, data=data)
    
    if not otp.get('success'):
        return {
            'success': otp.get('success'),
        }
    message = f'{otp.get('message')}, this is your OTP: {otp.get('otp')}'
    send_message(message=message, phone=normalized_phone)
    return otp

@app.post('/verify-otp')
async def check_otp(
    data: VerifyOTP,
    db: Session = Depends(get_db)):
    
    result = verify_otp(db=db, data=data)
    
    if not result.get('valid'):
        return {
            'message': result.get('message')
        }
    
    # create new user
    normalized_phone = normalize_phone(data.phone_number)
    payload = UserCreate(phone_number=normalized_phone)
    
    user = await createUser(db=db, user=payload)
    print(user)
    
    if not user.get('success'):
        send_message(message='Unable to create user account please try again!', phone=normalized_phone)
    
    # send message to user for onboarding
    send_message(message='Welcome i\'m Reece your smart ai assistant, whats your name', phone=normalized_phone)
    return result
    
    