from __future__ import annotations

import structlog
from fastapi import APIRouter

from api.models.simulation import SimulateRequest, SimulateResponse
from services.classroom_simulation import ClassroomSimulation

router = APIRouter()
logger = structlog.get_logger()


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(body: SimulateRequest) -> SimulateResponse:
    log = logger.bind(rows=body.rows, cols=body.cols, cycles=body.cycles)
    log.info("simulation_started", schedule_len=len(body.ca_schedule))

    sim = ClassroomSimulation(
        rows=body.rows,
        cols=body.cols,
        cycles=body.cycles,
        max_engagement=body.max_engagement,
        seed=body.seed,
    )

    schedule = [e.model_dump() for e in body.ca_schedule]
    ticks = sim.run(schedule)

    log.info("simulation_completed", total_ticks=len(ticks))

    return SimulateResponse(
        rows=body.rows,
        cols=body.cols,
        cycles=body.cycles,
        max_engagement=body.max_engagement,
        ticks=ticks,
    )
