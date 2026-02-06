from fastapi import APIRouter

from app.api.v1 import calculations, deductions, documents, income, interview, pdf, returns, review, taxpayer

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(returns.router)
api_v1_router.include_router(taxpayer.router)
api_v1_router.include_router(income.router)
api_v1_router.include_router(deductions.router)
api_v1_router.include_router(calculations.router)
api_v1_router.include_router(review.router)
api_v1_router.include_router(pdf.router)
api_v1_router.include_router(documents.router)
api_v1_router.include_router(interview.router)
