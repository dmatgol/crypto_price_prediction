from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.predictor import Predictor
from tools.settings import SupportedCoins, settings

app = FastAPI(
    title="Crypto Price Prediction API",
    description="API for predicting cryptocurrency prices",
    version="1.0.0",
)

predictors: dict[str, Predictor] = {}


class PredictionRequest(BaseModel):
    """Request model for price prediction."""

    product_id: str
    prediction_horizon: int
    # TODO: for future add functionality to predict n steps into the future


class PredictionResponse(BaseModel):
    """Response model for price prediction."""

    predicted_price: float
    predicted_timestamp: str


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint to verify the API is running."""
    health_status = await health_check()
    return {
        "name": app.title,
        "version": app.version,
        "description": app.description,
        "endpoints": {
            "root": "/",
            "health": "/health",
            "predict": "/predict",
        },
        "documentation": {
            "openapi": "/docs",
            "redoc": "/redoc",
        },
        "status": health_status["status"],
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest) -> PredictionResponse:
    """Predict cryptocurrency price based on input features.

    Args:
    ----
    request (PredictionRequest): Request containing timestamp and features

    Returns:
    -------
    PredictionResponse: Predicted price, confidence score, and timestamp

    """
    product_id = request.product_id
    prediction_horizon = request.prediction_horizon
    try:
        if product_id not in SupportedCoins.get_supported_coins():
            raise HTTPException(
                status_code=400, detail=f"Product ID {product_id} not supported"
            )
        if product_id not in predictors:
            predictors[product_id] = Predictor.load_from_model_registry(
                product_id=product_id,
                status=settings.comet_ml.general_config.status,
            )
        predicted_price = predictors[product_id].predict()
        predicted_price = predicted_price[f"forecast_{prediction_horizon}"]

        return PredictionResponse(
            predicted_price=float(predicted_price),
            predicted_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Prediction failed: {str(e)}"
        ) from e
