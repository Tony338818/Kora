from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from schema.db_schema import OTP
from schema.user_schema import RequestOTP, VerifyOTP
import bcrypt
import secrets


class OTPService:
    
    @staticmethod
    def _generate_otp() -> str:
        """Generates a cryptographically secure 6-digit One-Time Password."""
        return str(secrets.randbelow(900000) + 100000)

    @staticmethod
    def _hash_otp(otp_code: str) -> str:
        """Hashes a plain text OTP using bcrypt."""
        otp = otp_code.encode('utf-8')
        salt = bcrypt.gensalt(12)
        hashedotp = bcrypt.hashpw(otp, salt)
        return hashedotp.decode('utf-8')

    @staticmethod
    def _check_hash_otp(otp: str, otp_hash: str) -> bool:
        """Verifies a provided plain text OTP against a stored bcrypt hash."""
        return bcrypt.checkpw(otp.encode('utf-8'), otp_hash.encode('utf-8'))

    @classmethod
    def create_otp(cls, db: Session, data: RequestOTP):
        """Generates, hashes, and stores a new OTP in the database after clearing old ones."""
        # Use cls instead of self to call static methods
        otp = cls._generate_otp()
        otp_hash = cls._hash_otp(otp)
        # Note: consider using datetime.now(timezone.utc) as utcnow is deprecated in newer Python versions
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
        
    @classmethod
    def verify_otp(cls, db: Session, data: VerifyOTP):
        """Validates a user-provided OTP against the record in the database."""
        otp_record = db.query(OTP).filter(
                OTP.phone_number == data.phone_number,
            ).first()
        
        if otp_record is None:
            return {"valid": False, "message": "Invalid phone"}
        
        # Use cls instead of self
        if not cls._check_hash_otp(data.otp_code, otp_record.otp_hash):
            return {"valid": False, "message": "Invalid phone"}
            
        # Check expiry
        if datetime.utcnow() > otp_record.expires_at:
            return {"valid": False, "message": "OTP expired. Request a new one."}
        
        # Mark as used
        otp_record.is_used = True
        db.commit()
            
        return {"valid": True, "message": "OTP verified successfully"}