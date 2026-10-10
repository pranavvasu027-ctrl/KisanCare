from fastapi import FastAPI
from app.api.endpoints import router as api_router

app = FastAPI(title="KisanCare API", description="AI-powered Farm Decision Intelligence Backend")

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "KisanCare API"
    }
