from contextlib import asynccontextmanager
from fastapi import FastAPI
import fasttext
import spacy
from dependency.redis import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Loads the inventory bot once on startup
    app.state.inventory_bot = spacy.load(r'ai\inventory_model')
    app.state.conversation_classifier = fasttext.load_model(r'engine\models\conversation.bin')
    app.state.inventory_classifier = fasttext.load_model(r'engine\models\inventory.bin')
    
    
    try:
        await redis_client.ping()
        print("Redis connected successfully")
    except Exception as e:
        print(f"Redis connection failed: {e}")
        raise

    yield

    # Close Redis connection when FastAPI shuts down
    await redis_client.aclose()
    
app = FastAPI(lifespan=lifespan)