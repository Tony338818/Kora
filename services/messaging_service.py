from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN_SID = os.getenv('TWILIO_ACCOUNT_SID')
TOKEN_AUTH = os.getenv('TWILIO_AUTH_TOKEN')

twilio_client = Client(TOKEN_SID, TOKEN_AUTH)

def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to format: +1234567890
    Removes spaces, dashes, and ensures + prefix
    """
    # Remove all non-digit characters except +
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Remove leading zeros after country code 
        return cleaned
    else:
        # Add + if missing
        return '+' + cleaned

def send_message(message: str, phone: str):
    print('preparing to send message')
    sender = 'whatsapp:+14155238886'
    
    normalized = normalize_phone(phone)
    receiver = f'whatsapp:{normalized}'
    
    message = twilio_client.messages.create(
        from_=sender,
        body=message,
        to=receiver
    )
    
    print(message.sid)
    print(message.status)
    
    return message
    
async def send_onboarding_messages(message: str):
    """
    Get basic info like
    1. Name 
    2. Business name
    3. Business location
    4. Type of business/what they sell
    """
    pass
