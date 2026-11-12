"""Service for promotional codes and discounts."""

from fastapi import HTTPException
from config import ACTIVE_PROMO_CODES
from models.schemas import PromoValidateResponse


class PromoService:
    @staticmethod
    def validate_promo(code: str, subtotal: float = 0.0) -> PromoValidateResponse:
        normalized = (code or "").strip().upper()
        if not normalized:
            raise HTTPException(status_code=400, detail="Promo code cannot be empty")

        if normalized not in ACTIVE_PROMO_CODES:
            return PromoValidateResponse(
                valid=False,
                code=normalized,
                discount_percentage=0.0,
                discount_amount=0.0,
                message=f"Promo code '{normalized}' is invalid or expired."
            )

        rate = ACTIVE_PROMO_CODES[normalized]
        discount_amount = round(subtotal * rate, 2)
        pct = round(rate * 100, 1)

        return PromoValidateResponse(
            valid=True,
            code=normalized,
            discount_percentage=pct,
            discount_amount=discount_amount,
            message=f"Promo code applied: {pct}% off."
        )


promo_service = PromoService()
