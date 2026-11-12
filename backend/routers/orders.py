"""Order management and checkout router."""

from typing import List
from fastapi import APIRouter, status
from models.schemas import OrderCreate, OrderPublic
from services.order_service import order_service

router = APIRouter(prefix="/orders", tags=["Orders & Checkout"])


@router.post(
    "/carts/add",
    status_code=status.HTTP_201_CREATED,
    summary="Frontend compatibility checkout endpoint",
    include_in_schema=True,
)
def create_cart_order_compatibility(payload: dict):
    """
    Direct compatibility endpoint for existing techstore frontend script.js.
    Accepts {'userId': 1, 'products': [{'id': 1, 'quantity': 2}]} and maps to order workflow.
    """
    products_raw = payload.get("products", [])
    items = [
        {"product_id": p.get("id"), "quantity": p.get("quantity", 1)}
        for p in products_raw
    ]
    order_create = OrderCreate(
        customer_name="Online Customer",
        email="customer@voltix.store",
        shipping_address="Store Delivery Address",
        items=items,
        promo_code=None,
    )
    return order_service.create_order(order_create)


@router.post(
    "",
    response_model=OrderPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Place and checkout a new order",
)
def create_order(order: OrderCreate):
    """
    Substantial checkout workflow:
    - Validates customer contact & delivery address.
    - Verifies product existence and inventory stock availability.
    - Applies promo code discount if provided.
    - Calculates shipping fee (free over $500 threshold).
    - Atomically deducts purchased quantities from stock.
    - Creates order with status 'confirmed'.
    """
    return order_service.create_order(order)


@router.get(
    "",
    response_model=List[OrderPublic],
    status_code=status.HTTP_200_OK,
    summary="List all placed orders",
)
def list_orders():
    """Retrieve full history of store orders."""
    return order_service.list_orders()


@router.get(
    "/{order_id}",
    response_model=OrderPublic,
    status_code=status.HTTP_200_OK,
    summary="Get order details by ID",
)
def get_order(order_id: int):
    """Retrieve an order by ID."""
    return order_service.get_order(order_id)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderPublic,
    status_code=status.HTTP_200_OK,
    summary="Cancel an existing order and restore product stock",
)
def cancel_order(order_id: int):
    """
    Cancels an order and automatically restores reserved quantities back to stock.
    """
    return order_service.cancel_order(order_id)
