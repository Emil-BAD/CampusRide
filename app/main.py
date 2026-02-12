from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from app.database import get_db
from app.redis_client import redis_client
from app.bot import start_bot
import asyncio
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler: start background bot task on startup and cancel on shutdown."""
    bot_task = asyncio.create_task(start_bot())
    try:
        yield
    finally:
        # cancel the background bot task on shutdown
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)

# @app.get("/")
# async def root():
#     redis_client.set("test_key", "test_value")
#     redis_value = redis_client.get("test_key")
#     try:
#         db: Session = next(get_db())
#         db.execute(text("SELECT 1"))
#         postgres_status = "Connection OK"
#     except Exception as e:
#         postgres_status = f"Error: {str(e)}"
#     return {
#         "message": "FastAPI is running",
#         "redis_test": redis_value,
#         "postgres_test": postgres_status
#     }
