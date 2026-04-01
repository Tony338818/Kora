from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN_SID = os.getenv('TWILIO_ACCOUNT_SID')
TOKEN_AUTH = os.getenv('TWILIO_AUTH_TOKEN')

twilio_client = Client(TOKEN_SID, TOKEN_AUTH)

def send_message(message: str, phone: str):
    sender = 'whatsapp:+14155238886'
    
    message = twilio_client.messages.create(
        from_=sender,
        body=message,
        to=phone
    )