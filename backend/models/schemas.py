from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import re

EMAIL_REGEX = r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$"


# ---------------------------------------------------------
# Review Schemas
# ---------------------------------------------------------
class ReviewBase(BaseModel):
    reviewer_name: str = Field(..., min_length=2, max_length=60, description="Full name of reviewer")
    rating: int = Field(..., ge=1, le=5, description="Star rating between 1 and 5")
    comment: str = Field(..., min_length=3, max_length=500, description="Review text")


class ReviewCreate(ReviewBase):
    pass


class ReviewPublic(ReviewBase):
    id: int
    created_at: str


# ---------------------------------------------------------
# Product Schemas
# ---------------------------------------------------------
class ProductBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=150, description="Product title")
    description: str = Field(..., min_length=5, max_length=1000, description="Product description")
    category: str = Field(..., min_length=2, max_length=50, description="Category identifier")
    price: float = Field(..., gt=0, description="Base product price in USD")
    discount_percentage: float = Field(default=0.0, ge=0.0, le=90.0, description="Discount percentage")
    stock: int = Field(..., ge=0, description="Available stock quantity")
    brand: str = Field(..., min_length=1, max_length=50, description="Brand name")
    thumbnail: Optional[str] = Field(default="https://via.placeholder.com/300", description="Product thumbnail URL")
    images: List[str] = Field(default_factory=list, description="Product photo gallery")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, min_length=5, max_length=1000)
    category: Optional[str] = Field(default=None, min_length=2, max_length=50)
    price: Optional[float] = Field(default=None, gt=0)
    discount_percentage: Optional[float] = Field(default=None, ge=0.0, le=90.0)
    stock: Optional[int] = Field(default=None, ge=0)
    brand: Optional[str] = Field(default=None, min_length=1, max_length=50)
    thumbnail: Optional[str] = None
    images: Optional[List[str]] = None


class ProductPublic(ProductBase):
    id: int
    sale_price: float = Field(..., description="Calculated final price after discount")
    salePrice: Optional[float] = Field(default=None, description="Frontend camelCase alias for sale_price")
    discountPercentage: Optional[float] = Field(default=None, description="Frontend camelCase alias for discount_percentage")
    rating: float = Field(default=5.0, ge=0.0, le=5.0, description="Average customer rating")
    reviews_count: int = Field(default=0, ge=0, description="Total number of reviews")
    reviews: List[ReviewPublic] = Field(default_factory=list, description="List of customer reviews")


# ---------------------------------------------------------
# Order Schemas
# ---------------------------------------------------------
class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0, description="ID of product to buy")
    quantity: int = Field(..., gt=0, le=50, description="Number of items to purchase")


class OrderItemPublic(BaseModel):
    product_id: int
    title: str
    price: float
    sale_price: float
    quantity: int
    subtotal: float


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100, description="Customer full name")
    email: str = Field(..., description="Customer email address")
    shipping_address: str = Field(..., min_length=6, max_length=250, description="Delivery physical address")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="List of items in the cart")
    promo_code: Optional[str] = Field(default=None, max_length=20, description="Optional promotional discount code")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, clean):
            raise ValueError("Invalid email format. Example: user@example.com")
        return clean


class OrderPublic(BaseModel):
    id: int
    created_at: str
    customer_name: str
    email: str
    shipping_address: str
    items: List[OrderItemPublic]
    subtotal: float
    discount: float
    shipping: float
    total: float
    promo_code: Optional[str] = None
    status: str = Field(..., description="Order status: confirmed or cancelled")


# ---------------------------------------------------------
# Promotion Schemas
# ---------------------------------------------------------
class PromoValidateRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=20, description="Promo code")
    subtotal: float = Field(default=0.0, ge=0.0, description="Current subtotal to calculate discount for")


class PromoValidateResponse(BaseModel):
    valid: bool
    code: str
    discount_percentage: float
    discount_amount: float
    message: str
