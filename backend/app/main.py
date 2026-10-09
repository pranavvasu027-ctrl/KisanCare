from fastapi import FastAPI
from app.api.market_price import router as market_price_router

app = FastAPI(title="KisanCare API", description="AI-powered Farm Decision Intelligence Backend")

app.include_router(market_price_router, prefix="/api/market-price", tags=["market-price"])

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "KisanCare API"
    }
