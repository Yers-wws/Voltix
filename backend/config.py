"""Application configuration and constants."""

from typing import Dict

API_PREFIX = "/api"
APP_TITLE = "Voltix TechStore API"
APP_DESCRIPTION = (
    "RESTful API for Voltix TechStore electronics shop. "
    "Features catalog management, order processing with stock validation, "
    "promotions, and customer reviews."
)
APP_VERSION = "1.0.0"

# Business logic constants
FREE_SHIPPING_THRESHOLD = 500.0  # Free shipping for orders >= $500
STANDARD_SHIPPING_FEE = 15.0     # Shipping cost if below threshold

# Active promo codes and discount rates (e.g., 0.10 = 10% off)
ACTIVE_PROMO_CODES: Dict[str, float] = {
    "TECH10": 0.10,
    "VOLTIX20": 0.20,
    "WELCOME5": 0.05,
}

CATEGORIES = {
    "smartphones": "Smartphones",
    "laptops": "Laptops",
    "tablets": "Tablets",
    "mobile-accessories": "Accessories"
}
