from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.message_api import router as message_router
from api.otp_api import router as otp_router
from dependency.app_state import lifespan

app = FastAPI(
    version='0.2',
    description='No Name For This Version',
    lifespan=lifespan
)

app.include_router(router= message_router)
app.include_router(router= otp_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    
    