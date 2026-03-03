from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Event:
    title: str
    date: str
    price: str
    url: str
    source: str
    time: str = ""
    location: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
