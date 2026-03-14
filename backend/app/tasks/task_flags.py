from typing import Callable

from app.tasks.redis_client import redis_client


def stop_key(job_id: str) -> str:
    return f"stop:job:{job_id}"


def request_stop(job_id: str, ttl_seconds: int = 24 * 3600) -> None:
    redis_client.set(stop_key(job_id), "1", ex=ttl_seconds)


def clear_stop(job_id: str) -> None:
    redis_client.delete(stop_key(job_id))


def is_stop_requested(job_id: str) -> Callable[[], bool]:
    def should_stop():
        return redis_client.get(stop_key(job_id)) == "1"
    return should_stop