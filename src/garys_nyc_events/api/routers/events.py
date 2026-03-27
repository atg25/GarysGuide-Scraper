from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from dateutil import parser as date_parser

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


def _parse_event_date(value: str, anchor: date) -> date | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        parsed = date_parser.parse(
            cleaned, fuzzy=True, default=date_parser.parse(str(anchor))
        )
    except (ValueError, OverflowError):
        return None
    return parsed.date()


def _filter_by_date_range(
    events: list[dict],
    *,
    date_from: date,
    date_to: date,
) -> list[dict]:
    filtered: list[dict] = []
    for event in events:
        parsed_date = _parse_event_date(event.get("date", ""), date_from)
        if parsed_date is None:
            continue
        if date_from <= parsed_date <= date_to:
            filtered.append(event)
    return filtered


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
        if date_from > date_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="date_from cannot be later than date_to",
            )
        events = _filter_by_date_range(events, date_from=date_from, date_to=date_to)

    return EventListOut(
        count=len(events), events=[EventOut(**event) for event in events]
    )


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, store=Depends(get_store)):
    events = store.fetch_events(limit=0, ai_only=False)
    for event in events:
        if int(event.get("id", -1)) == event_id:
            return EventOut(**event)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
