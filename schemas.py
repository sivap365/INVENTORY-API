from pydantic import BaseModel
from typing import List
import datetime


class OrderItemIn(BaseModel):
    sku: str
    quantity: int


class OrderCreate(BaseModel):
    idempotency_key: str
    items: List[OrderItemIn]


class ProductCreate(BaseModel):
    sku: str
    name: str
    stock: int


class ProductOut(BaseModel):
    sku: str
    name: str
    stock: int

    class Config:
        from_attributes = True


class OrderItemOut(BaseModel):
    sku: str
    quantity: int

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    idempotency_key: str
    status: str
    created_at: datetime.datetime
    items: List[OrderItemOut]

    class Config:
        from_attributes = True
