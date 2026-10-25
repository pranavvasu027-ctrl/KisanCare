import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    _repo_root = Path(__file__).resolve().parent.parent.parent
    _env_file = _repo_root / ".env"
    if _env_file.exists():
        load_dotenv(dotenv_path=_env_file)
    else:
        load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI
from .api.endpoints import router as api_router
from .api.rentals import router as rentals_router
from .copilot.router import router as copilot_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

storage_uri = os.environ.get("RATELIMIT_STORAGE_URL", "memory://")
limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri, application_limits=[os.environ.get("APPLICATION_RATE_LIMIT", "300/minute")])

app = FastAPI(title="KisanCare API", description="AI-powered Farm Decision Intelligence Backend")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
from collections import defaultdict

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int = 5_000_000, max_requests: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.max_upload_size = max_upload_size
        self.max_requests = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "500" if os.environ.get("TESTING") else str(max_requests)))
        self.window_seconds = window_seconds
        self.ip_records = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # 1. Payload size limit
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > self.max_upload_size:
            return JSONResponse(status_code=413, content={"detail": "Payload too large"})
            
        # 2. Simple IP-based Rate Limiting (in-memory for MVP, shared cache (Redis) recommended for multi-instance)
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        
        # Clean up old records for this IP
        self.ip_records[client_ip] = [t for t in self.ip_records[client_ip] if now - t < self.window_seconds]
        
        if len(self.ip_records[client_ip]) >= self.max_requests:
            return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})
            
        self.ip_records[client_ip].append(now)
        
        return await call_next(request)

app.add_middleware(SecurityMiddleware)

from .api.soil import soil_router

# Routes mounted under /api/v1 (primary) and /api (convenience aliases)
app.include_router(api_router, prefix="/api/v1")
app.include_router(soil_router, prefix="/api/v1")
app.include_router(copilot_router, prefix="/api")
app.include_router(rentals_router, prefix="/api/v1")
app.include_router(rentals_router, prefix="/api")

@app.get("/health")
def health_check():
    from .copilot.service import get_copilot_provider
    provider = get_copilot_provider()
    configured = provider.is_configured()
    model = getattr(provider, "model_name", os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"))
    return {
        "status": "ok",
        "service": "KisanCare API",
        "copilot": {
            "status": "ready" if configured else "unconfigured",
            "model": model,
            "configured": configured
        }
    }
