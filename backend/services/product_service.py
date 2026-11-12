"""Business logic for product catalog, stock updates, and customer reviews."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from models.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductPublic,
    ReviewCreate,
    ReviewPublic,
)
from storage.db import db


def calculate_sale_price(price: float, discount_pct: float) -> float:
    discounted = price * (1.0 - (discount_pct / 100.0))
    return round(discounted, 2)


def to_product_public(data: Dict[str, Any]) -> ProductPublic:
    reviews_data = data.get("reviews", [])
    ratings = [r["rating"] for r in reviews_data if "rating" in r]
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 5.0
    sale_price = calculate_sale_price(data["price"], data.get("discount_percentage", 0.0))

    reviews_public = [
        ReviewPublic(
            id=r["id"],
            reviewer_name=r["reviewer_name"],
            rating=r["rating"],
            comment=r["comment"],
            created_at=r["created_at"],
        )
        for r in reviews_data
    ]

    disc = data.get("discount_percentage", 0.0)

    return ProductPublic(
        id=data["id"],
        title=data["title"],
        description=data["description"],
        category=data["category"],
        price=data["price"],
        discount_percentage=disc,
        discountPercentage=disc,
        sale_price=sale_price,
        salePrice=sale_price,
        stock=data["stock"],
        brand=data["brand"],
        thumbnail=data.get("thumbnail"),
        images=data.get("images", []),
        rating=avg_rating,
        reviews_count=len(reviews_data),
        reviews=reviews_public,
    )


class ProductService:
    @staticmethod
    def list_products(
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[ProductPublic]:
        with db._lock:
            items = list(db.products.values())

        # Filtering
        if category:
            cat_norm = category.strip().lower()
            items = [p for p in items if p["category"].lower() == cat_norm]

        if brand:
            brand_norm = brand.strip().lower()
            items = [p for p in items if p["brand"].lower() == brand_norm]

        if in_stock is True:
            items = [p for p in items if p["stock"] > 0]
        elif in_stock is False:
            items = [p for p in items if p["stock"] == 0]

        if search:
            q = search.strip().lower()
            items = [
                p
                for p in items
                if q in p["title"].lower()
                or q in p["description"].lower()
                or q in p["brand"].lower()
            ]

        # Convert to public models to obtain calculated sale_price
        public_items = [to_product_public(p) for p in items]

        # Price range filter based on final sale price
        if min_price is not None:
            public_items = [p for p in public_items if p.sale_price >= min_price]
        if max_price is not None:
            public_items = [p for p in public_items if p.sale_price <= max_price]

        # Sorting
        if sort_by == "price_asc":
            public_items.sort(key=lambda p: p.sale_price)
        elif sort_by == "price_desc":
            public_items.sort(key=lambda p: p.sale_price, reverse=True)
        elif sort_by == "rating":
            public_items.sort(key=lambda p: p.rating, reverse=True)
        elif sort_by == "discount":
            public_items.sort(key=lambda p: p.discount_percentage, reverse=True)
        elif sort_by == "name":
            public_items.sort(key=lambda p: p.title.lower())

        return public_items

    @staticmethod
    def get_product(product_id: int) -> ProductPublic:
        with db._lock:
            p = db.products.get(product_id)
        if not p:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID {product_id} not found",
            )
        return to_product_public(p)

    @staticmethod
    def create_product(product_create: ProductCreate) -> ProductPublic:
        with db._lock:
            pid = db._next_product_id
            db._next_product_id += 1

            product_dict = product_create.model_dump()
            product_dict["id"] = pid
            product_dict["reviews"] = []
            db.products[pid] = product_dict

        return to_product_public(product_dict)

    @staticmethod
    def update_product(product_id: int, product_update: ProductUpdate) -> ProductPublic:
        with db._lock:
            p = db.products.get(product_id)
            if not p:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product with ID {product_id} not found",
                )

            # Apply only supplied fields (matching exclude_unset=True concept)
            update_data = product_update.model_dump(exclude_unset=True)
            for key, val in update_data.items():
                p[key] = val

            db.products[product_id] = p

        return to_product_public(p)

    @staticmethod
    def delete_product(product_id: int) -> None:
        with db._lock:
            if product_id not in db.products:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product with ID {product_id} not found",
                )
            del db.products[product_id]

    @staticmethod
    def add_review(product_id: int, review_create: ReviewCreate) -> ReviewPublic:
        with db._lock:
            p = db.products.get(product_id)
            if not p:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product with ID {product_id} not found",
                )

            rid = db._next_review_id
            db._next_review_id += 1

            new_review = {
                "id": rid,
                "reviewer_name": review_create.reviewer_name.strip(),
                "rating": review_create.rating,
                "comment": review_create.comment.strip(),
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }

            if "reviews" not in p:
                p["reviews"] = []
            p["reviews"].append(new_review)
            db.products[product_id] = p

        return ReviewPublic(**new_review)

    @staticmethod
    def list_reviews(product_id: int) -> List[ReviewPublic]:
        with db._lock:
            p = db.products.get(product_id)
        if not p:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID {product_id} not found",
            )
        return [ReviewPublic(**r) for r in p.get("reviews", [])]


product_service = ProductService()
