from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from .service import MarketPriceService
import traceback

router = APIRouter(prefix="/api/market-price", tags=["market-price"])
service = MarketPriceService()

class MarketPriceRequest(BaseModel):
    crop: str = Field(..., example="onion")
    market: str = Field(..., example="Pune")
    date: str = Field(..., example="2026-10-06")
    horizon_days: int = Field(7, example=7, description="Forecast horizon in days (7 or 14)")

@router.get("/health")
def health_check():
    health = service.health_check()
    if health["status"] == "up":
        return health
    else:
        raise HTTPException(status_code=503, detail=health)

@router.post("/")
def get_market_price_forecast(request: MarketPriceRequest):
    try:
        result = service.predict(
            crop=request.crop,
            market=request.market,
            target_date=request.date,
            horizon_days=request.horizon_days
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
