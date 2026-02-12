"""
Уведомления: очередь в Redis, лог (опционально) в БД.

Redis — очередь задач на отправку (LPUSH/RPOP).
Бот или воркер забирает из очереди и отправляет.
"""
import json
from typing import Literal
from app.core.redis import redis_client

NOTIFY_QUEUE = "notifications:queue"


async def push_notification(
    tg_id: int,
    text: str,
    notification_type: Literal["trip_join", "trip_reminder", "trip_cancelled", "rating", "other"] = "other",
    trip_id: int | None = None,
    metadata: dict | None = None,
) -> None:
    """Добавить уведомление в очередь Redis."""
    payload = {
        "tg_id": tg_id,
        "text": text,
        "type": notification_type,
        "trip_id": trip_id,
        "metadata": metadata or {},
    }
    await redis_client.rpush(NOTIFY_QUEUE, json.dumps(payload))


async def pop_notification() -> dict | None:
    """Забрать следующее уведомление из очереди (блокирующий BLPOP на 1 сек)."""
    result = await redis_client.blpop(NOTIFY_QUEUE, timeout=1)
    if result:
        _, data = result
        return json.loads(data)
    return None
