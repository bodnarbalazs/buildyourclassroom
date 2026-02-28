from __future__ import annotations

from pydantic import BaseModel

from api.models.simulation.tick_snapshot import TickSnapshot


class SimulateResponse(BaseModel):
    rows: int
    cols: int
    cycles: int
    max_engagement: int
    ticks: list[TickSnapshot]
