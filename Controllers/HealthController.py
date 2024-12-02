from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/")
async def index():
    return "please use /docs for API Documentation"

@health_router.get("/health")
async def health():
    return "OK"