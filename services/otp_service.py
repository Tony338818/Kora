from sqlalchemy.orm import Session
import random
from datetime import datetime, timedelta
from schema.db_schema import OTP
from schema.user_schema import RequestOTP, VerifyOTP
import bcrypt


def generateOTP() -> str:
    return str(random.randint(100000, 999999))

def hashOTP(OTP: str) -> str:
    otp = OTP.encode('utf-8')
    salt = bcrypt.gensalt(12)
    hashedotp = bcrypt.hashpw(otp, salt)
    return hashedotp.decode('utf-8')

def verify(otp: str, otp_hash: str) -> bool:
    otp = otp.encode('utf-8')
    otp_hash = otp_hash.encode('utf-8')
    return bcrypt.checkpw(otp, otp_hash)

def createOTP(db: Session, data: RequestOTP):
    
    # OTP payload
    otp = generateOTP()
    otp_hash = hashOTP(otp)
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    # delete old OTP
    old_otp = db.query(OTP)\
        .filter_by(phone_number = data.phone_number)\
        .first()
        
    if old_otp:
        db.delete(old_otp)
        db.commit()
    
    new_otp = OTP(
        phone_number = data.phone_number,
        otp_hash = otp_hash,
        expires_at = expires_at,
    )
    
    db.add(new_otp)
    db.commit()
    
    return {
        'success': True,
        'message': f'OTP expires in {expires_at}',
        'otp': otp
    }
    
def verify_otp(db: Session, data: VerifyOTP):
    
    otp_record = db.query(OTP).filter(
            OTP.phone_number == data.phone_number,
        ).first()
    
    if not otp_record:
        return {"valid": False, "message": "Invalid phone"}
      
    if not verify(data.otp_code, otp_record.otp_hash):
        return {"valid": False, "message": "Invalid phone"}
        
    # Check expiry
    if datetime.utcnow() > otp_record.expires_at:
        return {"valid": False, "message": "OTP expired. Request a new one."}
    
    # Mark as used
    otp_record.is_used = True
    db.commit()
        
    return {"valid": True, "message": "OTP verified successfully"}
    