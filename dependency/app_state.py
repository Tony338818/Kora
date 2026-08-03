from contextlib import asynccontextmanager
from fastapi import FastAPI
import fasttext
import spacy

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Loads the inventory bot once on startup
    app.state.inventory_bot = spacy.load('ai\inventory_model')
    app.state.conversation_classifier = fasttext.load_model(r'engine\models\conversation.bin')
    app.state.inventory_classifier = fasttext.load_model(r'engine\models\inventory.bin')
    yield
    
app = FastAPI(lifespan=lifespan)