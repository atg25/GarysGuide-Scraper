from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    title: str
    date: str
    price: str
    url: str
    source: str
