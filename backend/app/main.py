import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import api_router
from app.config import settings
from app.storage.case_store import case_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("text_detective")

# In-memory rate limiter (sliding window, max 300 requests per minute per IP)
_client_request_history = defaultdict(list)
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 300


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Text Detective framework storage and indexing...")
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    settings.data_path.mkdir(parents=True, exist_ok=True)
    yield
    logger.info("Text Detective framework shutting down.")


app = FastAPI(
    title="Text Detective: An Agentic Text Analytics Framework for Evidence-Based Investigation",
    description=(
        "An investigation-oriented text analytics framework that ingests heterogeneous documents, "
        "extracts entities, events and timelines, constructs a structured case graph, retrieves evidence, "
        "detects cross-document contradictions, scores and ranks competing hypotheses, and generates "
        "auditable, source-referenced investigation reports."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = _client_request_history[client_ip]

    # Clean old timestamps
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    _client_request_history[client_ip] = [t for t in timestamps if t > cutoff]

    if len(_client_request_history[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please slow down."},
        )

    _client_request_history[client_ip].append(now)
    response: Response = await call_next(request)
    return response


# Global exception handler to prevent unhandled internal stack traces from leaking
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception during request {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact the investigation administrator."},
    )


# CORS middleware configured for secure local development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix="/api")


# Mount frontend static distribution if built
frontend_dist = settings.BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {
            "title": "Text Detective: An Agentic Text Analytics Framework for Evidence-Based Investigation",
            "version": "1.0.0",
            "docs_url": "/docs",
            "api_url": "/api",
            "provider": settings.LLM_PROVIDER,
            "demo_mode": settings.DEMO_MODE,
            "citation": "Makka Lokesh, Punith Sai Nallapaneni, Vamsika Kilari",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
