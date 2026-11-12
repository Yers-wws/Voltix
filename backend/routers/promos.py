"""Promotions and discounts router."""

from typing import Dict
from fastapi import APIRouter, status
from models.schemas import PromoValidateRequest, PromoValidateResponse
from services.promo_service import promo_service
from config import ACTIVE_PROMO_CODES

router = APIRouter(prefix="/promos", tags=["Promotions"])


@router.post(
    "/validate",
    response_model=PromoValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate promo code and calculate discount",
)
def validate_promo_code(payload: PromoValidateRequest):
    """
    Validates a promo code against active store discounts and returns potential savings.
    """
    return promo_service.validate_promo(payload.code, payload.subtotal)


@router.get(
    "",
    response_model=Dict[str, float],
    status_code=status.HTTP_200_OK,
    summary="List available store promotion codes and discount rates",
)
def get_active_promotions():
    """Returns active promotional coupon codes."""
    return ACTIVE_PROMO_CODES
