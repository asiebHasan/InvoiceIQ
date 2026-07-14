from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "InvoiceIQ"}


@router.get("/health/services")
async def service_health():
    from app.config import settings
    import httpx

    services = {"api": "ok", "redis": "unknown", "ollama": "unknown"}

    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        services["redis"] = "ok"
    except Exception:
        services["redis"] = "unavailable"

    # Check Ollama
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                services["ollama"] = "ok"
            else:
                services["ollama"] = "unavailable"
    except Exception:
        services["ollama"] = "unavailable"

    return services
