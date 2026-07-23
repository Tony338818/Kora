from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from schema.db_schema import OTP
from schema.user_schema import RequestOTP, VerifyOTP
import bcrypt
import secrets
from dependency.redis import redis_client


class OTPService:
    PREFIX = "otp"
    EXPIRY_SECONDS = 600
    
    @classmethod
    def _key(cls, phone_number: str) -> str:
        return f"{cls.PREFIX}:{phone_number}"
    
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
    async def create_otp(cls, phone_number: str) -> dict:
        """Generates, hashes, and stores an OTP in Redis with automatic 10-minute expiry."""
        otp = cls._generate_otp()
        otp_hash = cls._hash_otp(otp)
        key = cls._key(phone_number)

        # Store in Redis with TTL (ex = 600 seconds)
        await redis_client.set(key, otp_hash, ex=cls.EXPIRY_SECONDS)

        return {
            "success": True,
            "message": f"OTP generated successfully. Expires in {cls.EXPIRY_SECONDS // 60} minutes.",
            "otp": otp, 
        } 
        
    @classmethod
    async def verify_otp(cls, phone_number: str, otp_code: str) -> dict:
        """Verifies a user-provided OTP against the stored Redis hash."""
        key = cls._key(phone_number)
        stored_hash = await redis_client.get(key)

        if not stored_hash:
            return {"valid": False, "message": "OTP expired or does not exist."}

        # Convert bytes to str if redis_client returns bytes
        if isinstance(stored_hash, bytes):
            stored_hash = stored_hash.decode("utf-8")

        if not cls._check_hash_otp(otp_code, stored_hash):
            return {"valid": False, "message": "Invalid OTP."}

        # Delete the key immediately upon successful verification to prevent reuse
        await redis_client.delete(key)

        return {"valid": True, "message": "OTP verified successfully."}