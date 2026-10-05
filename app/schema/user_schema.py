from pydantic import Field, BaseModel
from typing import Optional

class UserCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: str
    business_name: Optional[str] = None
    business_address: Optional[str] = None
    
class RequestOTP(BaseModel):
    phone_number: str
    
class VerifyOTP(BaseModel):
    phone_number: str
    otp_code: str
    