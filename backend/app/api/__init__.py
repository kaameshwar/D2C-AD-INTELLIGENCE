from fastapi import APIRouter
from app.api import endpoints, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(endpoints.router)
