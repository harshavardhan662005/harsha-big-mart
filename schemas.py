from pydantic import BaseModel
from typing import Optional

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "User"

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


# --- PRODUCT SCHEMAS ---
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int
    image_url: Optional[str] = "https://images.unsplash.com/photo-1593642632823-8f785ba67e45" # Default placeholder

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int
    image_url: Optional[str]

    class Config:
        from_attributes = True
# --- CART & ORDER SCHEMAS ---

# What a user sends to add an item to their cart
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int

# Details returned when viewing items inside an order or cart
class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_purchase: float

    class Config:
        from_attributes = True

# Complete order structure returned upon successful checkout
class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    items: list[OrderItemResponse] = []

    class Config:
        from_attributes = True