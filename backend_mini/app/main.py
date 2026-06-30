import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import REPORTS_DIR
from app.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs(REPORTS_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("DB initialized")
    yield

app = FastAPI(title="Trading App Backend", version="2.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import judgments, reports, settings, traders, health, crypto_arb

app.include_router(judgments.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(traders.router, prefix="/api")
app.include_router(crypto_arb.router, prefix="/api")
app.include_router(health.router)
