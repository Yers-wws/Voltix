"""Product catalog and reviews router."""

from typing import List, Optional, Dict
from fastapi import APIRouter, Query, status
from models.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductPublic,
    ReviewCreate,
    ReviewPublic,
)
from services.product_service import product_service
from config import CATEGORIES

router = APIRouter(tags=["Products & Reviews"])


@router.get(
    "/products",
    response_model=List[ProductPublic],
    summary="List and filter catalog products",
    status_code=status.HTTP_200_OK,
)
def get_products(
    category: Optional[str] = Query(None, description="Filter by category slug"),
    brand: Optional[str] = Query(None, description="Filter by brand name"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum sale price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum sale price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter only in-stock items"),
    search: Optional[str] = Query(None, description="Search query for title, brand, or description"),
    sort_by: Optional[str] = Query(
        None,
        description="Sorting option: price_asc, price_desc, rating, discount, name",
    ),
):
    """Retrieve catalog products with optional filtering, search, and sorting."""
    return product_service.list_products(
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        search=search,
        sort_by=sort_by,
    )


@router.get(
    "/products/category/{category_slug}",
    summary="Category products compatibility endpoint",
    status_code=status.HTTP_200_OK,
)
def get_products_by_category(category_slug: str):
    """Compatibility route returning {'products': [...]}, matching techstore frontend expectations."""
    items = product_service.list_products(category=category_slug)
    return {"products": items, "total": len(items)}


@router.get(
    "/products/{product_id}",
    response_model=ProductPublic,
    summary="Get single product by ID",
    status_code=status.HTTP_200_OK,
)
def get_product(product_id: int):
    """Retrieve detailed product specifications, calculated pricing, and reviews."""
    return product_service.get_product(product_id)


@router.post(
    "/products",
    response_model=ProductPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new catalog product",
)
def create_product(product: ProductCreate):
    """Add a new product to the catalog."""
    return product_service.create_product(product)


@router.patch(
    "/products/{product_id}",
    response_model=ProductPublic,
    status_code=status.HTTP_200_OK,
    summary="Update product details or inventory stock",
)
def update_product(product_id: int, product_update: ProductUpdate):
    """Update selected product properties (partial update)."""
    return product_service.update_product(product_id, product_update)


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product from the catalog",
)
def delete_product(product_id: int):
    """Remove a product by ID."""
    product_service.delete_product(product_id)
    return None


@router.post(
    "/products/{product_id}/reviews",
    response_model=ReviewPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Add a customer review and rating to a product",
)
def add_product_review(product_id: int, review: ReviewCreate):
    """
    Submits a review for a product and automatically updates the average rating.
    """
    return product_service.add_review(product_id, review)


@router.get(
    "/products/{product_id}/reviews",
    response_model=List[ReviewPublic],
    status_code=status.HTTP_200_OK,
    summary="List all reviews for a product",
)
def get_product_reviews(product_id: int):
    """Returns all reviews submitted for a given product."""
    return product_service.list_reviews(product_id)


@router.get(
    "/categories",
    response_model=Dict[str, str],
    summary="List all store categories",
    status_code=status.HTTP_200_OK,
)
def get_categories():
    """Returns the dictionary of supported product categories."""
    return CATEGORIES
