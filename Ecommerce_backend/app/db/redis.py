from redis import Redis

from app.core.config import settings


redis_client = Redis.from_url(
    str(settings.REDIS_URL),
    decode_responses=True,
    max_connections=settings.REDIS_MAX_CONNECTIONS,
    socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
    health_check_interval=30,
)


def get_redis_client() -> Redis:
    return redis_client