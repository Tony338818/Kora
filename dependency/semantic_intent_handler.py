from contextlib import asynccontextmanager
from fastapi import FastAPI
from ai.semantic_router import SemanticRouter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Loads the semantic router once on startup
    app.state.semantic_router = SemanticRouter()
    print('Router Loaded!')
    yield
    
app = FastAPI(lifespan=lifespan)