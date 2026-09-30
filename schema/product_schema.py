from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ProductCreate(BaseModel):
    name: str = Field(..., max_length=100)
    quantity: int = Field(..., ge=0)
    cost_price: float = Field(..., ge=0)
    selling_price: float = Field(..., ge=0)

    supplier: Optional[str] = None
    img_url: Optional[str] = None
    description: Optional[str] = None

    buy_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    
class ProductOut(BaseModel):
    id: int
    name: str
    quantity: int
    selling_price: float
    img_url: Optional[str]
    buy_date: Optional[datetime]
    expiry_date: Optional[datetime]

    class Config:
        from_attributes = True
        
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    supplier: Optional[str] = None
    img_url: Optional[str] = None
    description: Optional[str] = None
    buy_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    
    
class ProductDisplay(BaseModel):
    success: bool
    message: Optional[str] = None
    product: Optional[List[ProductOut]] = None

    class Config:
        from_attributes = True
        
class ProductResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    product: Optional[ProductOut] = None

    class Config:
        from_attributes = True