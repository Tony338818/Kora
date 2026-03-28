import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json
from schema.model_schema import RouterOutput


load_dotenv()
GEMINI_API_KEY =os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)


def model_router(message: str, session: dict):
    try:
        prompt = f"""Classify this WhatsApp message into ONE intent.if there is an existing intent in the session, make use of it
        Message: "{message}"
        Session: "{session.get('class') if session else None}"
        
        Examples:
        - "hey how are you" → casual_conversation
        - "how many red shirts do we have" → inventory_query + product_name="red shirts"
        - "what's the price" → inventory_query
        - "order 3 apples" → other (we'll handle later)
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
                # system_instruction=prompt,
                response_schema=RouterOutput
            )
        )
        
        print(f'Model response is {json.loads(response.text)}')
        return json.loads(response.text)
    
    except Exception as e:
        return {
            'error': str(e) 
        }


def deterministic_method(message: str, session: dict):
    msg = message.lower().strip()
    
    