import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from api.models.emotion_orm import SCHEMA, Base
from api.routes.emotion import router as emotion_router
from api.routes.health import router as health_router
from shared.database import engine, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables ready, warming up emotion model…")
    from api.routes.emotion import _analyzer

    _analyzer.warm_up()
    logger.info("Emotion model warmed up")

    yield


app = FastAPI(title="Hackathon Microservice", lifespan=lifespan)

app.include_router(health_router)
app.include_router(emotion_router, prefix="/emotion", tags=["Emotion Detection"])
