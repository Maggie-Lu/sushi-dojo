from pydantic import BaseModel
from typing import List, Optional

class OrderItem(BaseModel):
    id: int
    name: str
    price: float
    quantity: int
    emoji: str

class OrderCreate(BaseModel):
    customer_name: str
    order_type: str
    address: Optional[str] = None
    phone: str
    items: List[OrderItem]
    total: float
    notes: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: str
    eta_minutes: Optional[int] = None

class OrderETAUpdate(BaseModel):
    eta_minutes: int
