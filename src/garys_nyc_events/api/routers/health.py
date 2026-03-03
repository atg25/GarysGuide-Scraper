from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_store


router = APIRouter()


@router.get("/health")
def health(store=Depends(get_store)):
    return {"status": "ok", "db_event_count": store.count_rows("all events")}
