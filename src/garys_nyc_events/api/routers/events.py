from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...filters import filter_events_upcoming_week
from ..auth import require_api_token
from ..dependencies import get_store
from ..schemas import EventListOut, EventOut


router = APIRouter(dependencies=[Depends(require_api_token)])


def _filter_by_tags(events: list[dict], tags: str) -> list[dict]:
    requested = {token.strip().lower() for token in tags.split(",") if token.strip()}
    if not requested:
        return events
    return [
        event
        for event in events
        if requested.intersection({tag.lower() for tag in event.get("tags", [])})
    ]


@router.get("", response_model=EventListOut)
def list_events(
    ai_only: bool = True,
    limit: int = 100,
    tags: str = "",
    date_from: date | None = None,
    date_to: date | None = None,
    store=Depends(get_store),
):
    events = store.fetch_events(limit=limit, ai_only=ai_only)
    events = _filter_by_tags(events, tags)

    if date_from is not None and date_to is not None:
        window = filter_events_upcoming_week(events, today=date_from)
        events = [event for event in window if event.get("date", "") <= str(date_to)]

    return EventListOut(count=len(events), events=[EventOut(**event) for event in events])


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, store=Depends(get_store)):
    events = store.fetch_events(limit=0, ai_only=False)
    for event in events:
        if int(event.get("id", -1)) == event_id:
            return EventOut(**event)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
