from contextlib import asynccontextmanager
from fastapi import FastAPI
from .model1.router import router as model1_router
from .model1.service import model1_service
from .digital_twin.router import router as digital_twin_router
from .market_price.router import router as market_price_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        model1_service.load_artifacts()
        print("Model 1 artifacts loaded successfully.")
    except Exception as e:
        print("Warning: Failed to load Model 1 artifacts on startup.")
    yield
    # Shutdown
    pass

app = FastAPI(
    title="KisanCare Model 1 API",
    description="Baseline crop recommendation model inference API.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(model1_router)
app.include_router(digital_twin_router)
app.include_router(market_price_router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model": "crop_recommendation",
        "model_loaded": model1_service.is_loaded
    }
