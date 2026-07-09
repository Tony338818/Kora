from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from schema.db_schema import OTP
from schema.user_schema import RequestOTP, VerifyOTP
import bcrypt
import secrets


class OTPService:
    def _generate_otp() -> str:
        """Generates a cryptographically secure 6-digit One-Time Password.

        Returns:
            str: A 6-digit numeric string.
        """
        return str(secrets.randbelow(900000) + 100000)

    def _hash_otp(OTP: str) -> str:
        """Hashes a plain text OTP using bcrypt.

        Args:
            otp_code (str): The plain text 6-digit OTP.

        Returns:
            str: The decoded string representation of the secure hash.
        """
        otp = OTP.encode('utf-8')
        salt = bcrypt.gensalt(12)
        hashedotp = bcrypt.hashpw(otp, salt)
        return hashedotp.decode('utf-8')

    def _check_hash_otp(otp: str, otp_hash: str) -> bool:
        """Verifies a provided plain text OTP against a stored bcrypt hash.

        Args:
            otp_code (str): The plain text OTP code provided by the user.
            otp_hash (str): The stored hashed version from the database.

        Returns:
            bool: True if the code matches the hash, False otherwise.
        """
        return bcrypt.checkpw(otp.encode('utf-8'), otp_hash.encode('utf-8'))

    def create_otp(self, db: Session, data: RequestOTP):
        """Generates, hashes, and stores a new OTP in the database after clearing old ones.

        Args:
            db (Session): The active SQLAlchemy database session.
            data (RequestOTP): The schema containing the user's phone number.

        Returns:
            dict: A response dictionary containing success status, message, and the plain OTP.
        """
        # OTP payload
        otp = self._generate_otp()
        otp_hash = self._hash_otp(otp)
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
        
    def verify_otp(self, db: Session, data: VerifyOTP):
        """Validates a user-provided OTP against the record in the database.

        Args:
            db (Session): The active SQLAlchemy database session.
            data (VerifyOTP): The schema containing the phone number and OTP code.

        Returns:
            dict: A verification result dictionary containing valid status and message.
        """
        otp_record = db.query(OTP).filter(
                OTP.phone_number == data.phone_number,
            ).first()
        
        if not otp_record:
            return {"valid": False, "message": "Invalid phone"}
        
        if not self._check_hash_otp(data.otp_code, otp_record.otp_hash):
            return {"valid": False, "message": "Invalid phone"}
            
        # Check expiry
        if datetime.utcnow() > otp_record.expires_at:
            return {"valid": False, "message": "OTP expired. Request a new one."}
        
        # Mark as used
        otp_record.is_used = True
        db.commit()
            
        return {"valid": True, "message": "OTP verified successfully"}
    