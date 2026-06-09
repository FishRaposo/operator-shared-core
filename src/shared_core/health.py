from sqlalchemy import text


def check_health(db_manager, redis_manager, service_name: str) -> dict:
    """Service health indicator checking database and cache health."""
    db_healthy = False
    redis_healthy = False

    # 1. Test database connection
    try:
        with db_manager.SessionLocal() as session:
            session.execute(text("SELECT 1"))
            db_healthy = True
    except Exception:
        db_healthy = False

    # 2. Test redis connection
    try:
        redis_healthy = redis_manager.ping()
    except Exception:
        redis_healthy = False

    status = "healthy" if db_healthy and redis_healthy else "degraded"

    return {
        "status": status,
        "service": service_name,
        "dependencies": {
            "database": "online" if db_healthy else "offline",
            "redis": "online" if redis_healthy else "offline",
        },
    }
