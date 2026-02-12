from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db, AsyncSessionLocal
from app.bot import start_bot
from app.db import seed_locations
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler: init DB, seed locations, start bot."""
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_locations(session)

    bot_task = asyncio.create_task(start_bot())
    try:
        yield
    finally:
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
