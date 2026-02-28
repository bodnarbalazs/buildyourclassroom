import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from api.models.emotion_orm import SCHEMA, Base
from api.routes.agenda import router as agenda_router
from api.routes.assessment import router as assessment_router
from api.routes.emotion import router as emotion_router
from api.routes.health import router as health_router
import shared.database as db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()

    async with db.engine.begin() as conn:
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
app.include_router(agenda_router, prefix="/api/v1", tags=["Lesson Agenda"])
app.include_router(assessment_router, prefix="/api/v1", tags=["Lesson Assessment"])
