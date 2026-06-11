import asyncio
import logging

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import judgments, missioncontrol, portfolio, prices, reports, trades, traders

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading App",
    version="0.1.0",
    description="Cross-Platform Trading App Backend",
)

HEALTH_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    path = request.url.path
    if path in HEALTH_PATHS or path.startswith("/static"):
        return await call_next(request)
    if settings.api_key and request.headers.get("X-API-Key") != settings.api_key:
        return Response(status_code=401, content="Unauthorized")
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(trades.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(prices.router, prefix="/api")
app.include_router(traders.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(missioncontrol.router, prefix="/api")
app.include_router(judgments.router, prefix="/api")


@app.on_event("startup")
async def startup():
    await init_db()
    asyncio.create_task(_periodic_service_history())


async def _periodic_service_history():
    """Collect service response times every 5 minutes for the history chart."""
    await asyncio.sleep(10)  # Initial delay to let everything settle
    while True:
        try:
            missioncontrol._collect_service_history()
        except Exception as e:
            logger.warning("Service history collection failed: %s", e)
        await asyncio.sleep(300)  # 5 minutes


@app.get("/api/health")
async def health():
    return {"status": "ok"}