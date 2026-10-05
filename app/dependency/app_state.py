from contextlib import asynccontextmanager
from pathlib import Path

import fasttext
import spacy
from fastapi import FastAPI
from sqlalchemy import text

from dependency.redis import redis_client
from schema.db_schema import Session


# ---------------------------------------------------------
# Model paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INVENTORY_SPACY_MODEL = BASE_DIR / "ai" / "inventory_model"
CONVERSATION_MODEL = BASE_DIR / "engine" / "models" / "conversation.bin"
INVENTORY_MODEL = BASE_DIR / "engine" / "models" / "inventory.bin"


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("\n========== APPLICATION STARTUP ==========\n")

    # -----------------------------------------------------
    # Load ML models
    # -----------------------------------------------------

    try:
        print("Loading spaCy inventory model...")

        app.state.inventory_bot = spacy.load(
            str(INVENTORY_SPACY_MODEL)
        )

        print("✓ Inventory spaCy model loaded")

    except Exception as e:
        print(f"✗ Failed to load inventory spaCy model: {e}")
        raise


    try:
        print("Loading conversation classifier...")

        app.state.conversation_classifier = fasttext.load_model(
            str(CONVERSATION_MODEL)
        )

        print("✓ Conversation classifier loaded")

    except Exception as e:
        print(f"✗ Failed to load conversation classifier: {e}")
        raise


    try:
        print("Loading inventory classifier...")

        app.state.inventory_classifier = fasttext.load_model(
            str(INVENTORY_MODEL)
        )

        print("✓ Inventory classifier loaded")

    except Exception as e:
        print(f"✗ Failed to load inventory classifier: {e}")
        raise


    # -----------------------------------------------------
    # Database
    # -----------------------------------------------------

    db = Session()

    try:
        db.execute(text("SELECT 1"))
        print("✓ Database connected successfully")

    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        raise

    finally:
        db.close()


    # -----------------------------------------------------
    # Redis
    # -----------------------------------------------------

    try:
        await redis_client.ping()
        print("✓ Redis connected successfully")

    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        raise


    print("\n========== APPLICATION READY ==========\n")

    # Application starts accepting requests here
    yield


    # -----------------------------------------------------
    # Shutdown
    # -----------------------------------------------------

    print("\n========== APPLICATION SHUTDOWN ==========\n")

    await redis_client.aclose()

    # Remove references to large models
    app.state.inventory_bot = None
    app.state.conversation_classifier = None
    app.state.inventory_classifier = None

    print("✓ Application resources released")