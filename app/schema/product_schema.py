from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


class ProductCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    quantity: int = Field(
        default=0,
        ge=0
    )

    cost_price: Optional[float] = Field(
        default=None,
        ge=0
    )

    selling_price: Optional[float] = Field(
        default=None,
        ge=0
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255
    )

    img_url: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    quantity: Optional[int] = Field(
        default=None,
        ge=0
    )

    cost_price: Optional[float] = Field(
        default=None,
        ge=0
    )

    selling_price: Optional[float] = Field(
        default=None,
        ge=0
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255
    )

    img_url: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    quantity: int

    cost_price: Optional[float] = None
    selling_price: Optional[float] = None

    description: Optional[str] = None
    img_url: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ProductResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    product: Optional[ProductOut] = None


class ProductDisplay(BaseModel):
    success: bool
    message: Optional[str] = None
    products: list[ProductOut] = Field(
        default_factory=list
    )