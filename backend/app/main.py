from fastapi import FastAPI

app = FastAPI(title="KisanCare API", description="AI-powered Farm Decision Intelligence Backend")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "KisanCare API"
    }
