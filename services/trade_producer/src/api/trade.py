from pydantic import BaseModel, field_validator


class Trade(BaseModel):
    """A class representing a trade using Pydantic."""

    product_id: str
    side: str
    price: float
    volume: float
    timestamp: str
    exchange: str

    @field_validator("side")
    def validate_side(cls, v):
        """Validate that the trade side is either "buy" or "sell"."""
        if v not in ["buy", "sell"]:
            raise ValueError("Trade side must be either 'buy' or 'sell'.")
        return v
