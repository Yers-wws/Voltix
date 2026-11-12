"""Main entrypoint for Voltix TechStore FastAPI application."""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from config import APP_TITLE, APP_DESCRIPTION, APP_VERSION, API_PREFIX
from routers import products, orders, promos

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS to allow frontend communication from any local origin (e.g., Live Server, file://, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include resource routers under /api prefix
app.include_router(products.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)
app.include_router(promos.router, prefix=API_PREFIX)


@app.post(
    f"{API_PREFIX}/carts/add",
    status_code=status.HTTP_201_CREATED,
    tags=["Frontend Compatibility"],
    summary="Legacy carts/add compatibility endpoint",
)
def compatibility_cart_add(payload: dict):
    """Direct bridge for techstore script.js fetch('/carts/add') POST request."""
    from routers.orders import create_cart_order_compatibility
    return create_cart_order_compatibility(payload)


@app.get(
    "/health",
    tags=["System"],
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
)
def health_check():
    """Returns operational status of the API server (Week 11 pattern)."""
    return {"status": "ok", "app": APP_TITLE, "version": APP_VERSION}


@app.get(
    "/",
    tags=["System"],
    status_code=status.HTTP_200_OK,
    summary="Root landing page",
)
def root():
    """Welcome route directing users and evaluators to interactive Swagger docs."""
    return {
        "message": f"Welcome to {APP_TITLE}!",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "products": f"{API_PREFIX}/products",
            "categories": f"{API_PREFIX}/categories",
            "orders": f"{API_PREFIX}/orders",
            "promotions": f"{API_PREFIX}/promos",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
