"""Order placement and inventory checkout service."""

from datetime import datetime
from typing import List, Dict, Any
from fastapi import HTTPException
from config import FREE_SHIPPING_THRESHOLD, STANDARD_SHIPPING_FEE
from models.schemas import OrderCreate, OrderPublic, OrderItemPublic
from services.product_service import calculate_sale_price
from services.promo_service import promo_service
from storage.db import db


class OrderService:
    @staticmethod
    def create_order(order_create: OrderCreate) -> OrderPublic:
        """
        Executes order checkout workflow:
        1. Validates product existence and stock availability.
        2. Applies optional promo code discounts.
        3. Computes delivery shipping fees.
        4. Atomically reserves/deducts inventory stock.
        5. Persists the created order.
        """
        if not order_create.items:
            raise HTTPException(status_code=400, detail="Order items list cannot be empty")

        with db._lock:
            # Step 1: Pre-validation of products and stock
            order_items_public: List[OrderItemPublic] = []
            subtotal = 0.0

            # Map to verify duplicate items in request
            consolidated_items: Dict[int, int] = {}
            for item in order_create.items:
                consolidated_items[item.product_id] = (
                    consolidated_items.get(item.product_id, 0) + item.quantity
                )

            for pid, qty in consolidated_items.items():
                product = db.products.get(pid)
                if not product:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Product with ID {pid} was not found in catalog"
                    )

                available_stock = product.get("stock", 0)
                if available_stock < qty:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Insufficient stock for '{product['title']}'. "
                            f"Requested quantity: {qty}, currently available: {available_stock}"
                        )
                    )

                sale_p = calculate_sale_price(product["price"], product.get("discount_percentage", 0.0))
                line_total = round(sale_p * qty, 2)
                subtotal += line_total

                order_items_public.append(
                    OrderItemPublic(
                        product_id=pid,
                        title=product["title"],
                        price=product["price"],
                        sale_price=sale_p,
                        quantity=qty,
                        subtotal=line_total,
                    )
                )

            subtotal = round(subtotal, 2)

            # Step 2: Promo code validation & discount calculation
            discount = 0.0
            applied_code = None
            if order_create.promo_code:
                promo_res = promo_service.validate_promo(order_create.promo_code, subtotal)
                if not promo_res.valid:
                    raise HTTPException(
                        status_code=400,
                        detail=promo_res.message
                    )
                discount = promo_res.discount_amount
                applied_code = promo_res.code

            after_discount = max(0.0, subtotal - discount)

            # Step 3: Shipping fee calculation
            shipping = 0.0 if after_discount >= FREE_SHIPPING_THRESHOLD else STANDARD_SHIPPING_FEE
            total = round(after_discount + shipping, 2)

            # Step 4: Atomic stock deduction
            for pid, qty in consolidated_items.items():
                db.products[pid]["stock"] -= qty

            # Step 5: Save order
            order_id = db._next_order_id
            db._next_order_id += 1

            order_record: Dict[str, Any] = {
                "id": order_id,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "customer_name": order_create.customer_name.strip(),
                "email": order_create.email.strip().lower(),
                "shipping_address": order_create.shipping_address.strip(),
                "items": [item.model_dump() for item in order_items_public],
                "subtotal": subtotal,
                "discount": discount,
                "shipping": shipping,
                "total": total,
                "promo_code": applied_code,
                "status": "confirmed",
            }
            db.orders[order_id] = order_record

        return OrderPublic(**order_record)

    @staticmethod
    def list_orders() -> List[OrderPublic]:
        with db._lock:
            return [OrderPublic(**o) for o in db.orders.values()]

    @staticmethod
    def get_order(order_id: int) -> OrderPublic:
        with db._lock:
            order = db.orders.get(order_id)
        if not order:
            raise HTTPException(
                status_code=404,
                detail=f"Order with ID {order_id} not found"
            )
        return OrderPublic(**order)

    @staticmethod
    def cancel_order(order_id: int) -> OrderPublic:
        """
        Cancels an order and automatically restores stock to inventory.
        """
        with db._lock:
            order = db.orders.get(order_id)
            if not order:
                raise HTTPException(
                    status_code=404,
                    detail=f"Order with ID {order_id} not found"
                )

            if order["status"] == "cancelled":
                raise HTTPException(
                    status_code=400,
                    detail=f"Order #{order_id} is already cancelled"
                )

            # Restore product stock
            for item in order["items"]:
                pid = item["product_id"]
                qty = item["quantity"]
                if pid in db.products:
                    db.products[pid]["stock"] += qty

            order["status"] = "cancelled"
            db.orders[order_id] = order

        return OrderPublic(**order)


order_service = OrderService()
