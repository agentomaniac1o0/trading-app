from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import portfolio, prices, reports, trades, traders

app = FastAPI(
    title="Trading App",
    version="0.1.0",
    description="Cross-Platform Trading App Backend",
)

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


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/api/health")
async def health():
    return {"status": "ok"}