from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.learning_paths.router import router as learning_paths_router
from app.gemini.router import router as gemini_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # await init_db()

    # await bot.set_webhook(url=settings.WEBHOOK_URL, secret_token=settings.WEBHOOK_SECRET_TOKEN)
    # print(f"Webhook set: {settings.webhook_url}")
    # yield
    # await bot.delete_webhook()
    # await bot.session.close()
    # print("Webhook removed, bot session closed.")
    yield

app = FastAPI(title="Bot API", lifespan=lifespan)

app.include_router(learning_paths_router)
app.include_router(gemini_router)


@app.get("/")
async def root():
    return {"message": "FastAPI is connected to Sail PostgreSQL"}
