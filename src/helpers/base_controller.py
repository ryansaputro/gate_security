"""
BaseController - Validation helper (mirrors basecode-golang helpers/base-controller).
"""

from fastapi import HTTPException, Request


class BaseController:
    @staticmethod
    def validate_payload(payload, required_fields: list):
        """Validate required fields in payload."""
        missing = [f for f in required_fields if not getattr(payload, f, None)]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing)}"
            )
