from __future__ import annotations

from typing import List

from pydantic import BaseModel


class EventOut(BaseModel):
    id: int
    title: str
    date: str
    time: str
    location: str
    description: str
    date_found: str
    price: str
    url: str
    tags: List[str]


class EventListOut(BaseModel):
    count: int
    events: List[EventOut]


class RunOut(BaseModel):
    run_id: int
    status: str
    source: str
    attempts: int
    fetched_count: int
    error: str


class TriggerRunOut(BaseModel):
    message: str
    run: RunOut
