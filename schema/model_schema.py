from enum import Enum
from pydantic import BaseModel, Field

class ConversationClass(str, Enum):
    CASUAL_CONVERSATION = "casual_conversation"
    INVENTORY_QUERY = "inventory_query"
    OTHER = "other"

class RouterOutput(BaseModel):
    conversation_class: ConversationClass = Field(..., description="Exact intent category")
    reasoning: str = Field(..., description="Short 1-sentence explanation")
    product_name: str | None = Field(None, description="Only fill if inventory_query")
    
class Conversation(BaseModel):
    message: str = Field(..., description='Response to user message')
    reasoning: str = Field(..., description="Short 1-sentence explanation")