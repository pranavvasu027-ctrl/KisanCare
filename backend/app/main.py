from fastapi import FastAPI
from app.api import endpoints

app = FastAPI(title="KisanCare Backend API", version="1.0.0")

app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}
