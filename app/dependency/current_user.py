from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
import os
import datetime
from dotenv import load_dotenv

load_dotenv()
SECRET = os.getenv("SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_SECONDS = 1200 
security = HTTPBearer()

def create_token(user_id: int):
    payload = {
        "sub": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=ACCESS_TOKEN_SECONDS)
    }

    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)



def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload["sub"]

    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")