from fastapi import APIRouter

from app.api.v1 import income, returns, taxpayer

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(returns.router)
api_v1_router.include_router(taxpayer.router)
api_v1_router.include_router(income.router)
