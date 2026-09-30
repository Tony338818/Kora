from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TransactionItemCreate(BaseModel):
    product_id: int | None = None
    product_name: str
    quantity: int
    unit_price: float
    
class TransactionItemOut(BaseModel):
    id: int
    product_id: int | None
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True
        
class TransactionCreate(BaseModel):
    transaction_type: str
    payment_method: str
    payment_status: str
    items: list[TransactionItemCreate]
    

class TransactionOut(BaseModel):
    id: int
    user_id: int
    amount: float
    transaction_type: str
    payment_method: str
    payment_status: str
    created_at: datetime

    items: list[TransactionItemOut]

    class Config:
        from_attributes = True