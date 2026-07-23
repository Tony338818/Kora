from fastapi import APIRouter, Depends
from dependency.db import get_db
from sqlalchemy.orm import Session
from schema.user_schema import RequestOTP, UserCreate, VerifyOTP
from services.messaging_service import send_message
from services.otp_service import OTPService as otps
from services.user_service import create_user
from utils import normalize_phone as np

router = APIRouter(prefix='/otp')

@router.post('/send')
def get_otp(
    data: RequestOTP,
    db: Session = Depends(get_db)):
    
    normalized_phone = np.normalize_phone_numbers(data.phone_number)
    otp = otps.create_otp(db=db, data=data)
    
    if not otp.get('success'):
        return {
            'success': otp.get('success'),
        }
    message = f'{otp.get('message')}, this is your OTP: {otp.get('otp')}'
    send_message(message=message, phone=normalized_phone)
    return otp

@router.post('/verify')
async def handle_otp(
    data: VerifyOTP,
    db: Session = Depends(get_db)):
    result = otps.verify_otp(db=db, data=data)
    
    if not result.get('valid'):
        return {
            'message': result.get('message')
        }
    
    # create new user
    normalized_phone = np.normalize_phone_numbers(data.phone_number)
    payload = UserCreate(phone_number=normalized_phone)
    
    user = await create_user(db=db, user=payload)
    print(user)
    
    if not user.get('success'):
        return user
        # send_message(message='Unable to create user account please try again!', phone=normalized_phone)
    
    # send message to user for onboarding
    send_message(message='Welcome i\'m Reece your smart ai assistant, whats your name', phone=normalized_phone)
    return result
    
    