import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import analysis, news
from .dependencies import get_settings

# Configure structured logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLMAnalyze API",
    description="Stock Market Analysis API powered by LLMs and Technical Indicators",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(news.router, prefix="/api/v1/news", tags=["News"])


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "timestamp": time.time(),
        "version": "0.1.0",
        "environment": settings.env,
    }


@app.on_event("startup")
async def startup_event():
    logger.info(f"LLMAnalyze API starting up (env={settings.env})")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("LLMAnalyze API shutting down")
