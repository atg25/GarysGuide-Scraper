# Sprint 14 — Gemini AI Tagging: Automated Event Tags via Google Gemini API

**Status:** Planned
**Addresses:** Goal 3 — AI-generated tags for each event using Google Gemini API

---

## Goal

After each event is scraped and deduplicated, call the **Google Gemini API** to generate a concise
list of semantic tags (e.g. `["LLM", "Networking", "Workshop", "Free"]`) for each event based on
its `title`, `description`, and `location`. Store the tags in the database and expose them in
query results.

**Note on .env key name:** The `.env` file currently spells the variable `GEMNINI_API_KEY` (typo).
This sprint standardises on `GEMINI_API_KEY` in code and documentation. For backward compatibility,
the config loader will also check `GEMNINI_API_KEY` and emit a deprecation warning. Rename the
variable in `.env` to `GEMINI_API_KEY` when deploying.

---

## Rationale

Free-text titles alone are poor search and grouping signals. A normalised tag vocabulary (e.g.
`"workshop"`, `"panel"`, `"hackathon"`, `"networking"`, `"free"`) enables API consumers to filter
by event type without implementing their own NLP. Gemini Flash is fast and low-cost for short
event metadata payloads. The tagger is designed as an **optional enrichment step** — if the API
key is absent or the call fails, the pipeline continues with `tags = []`.

---

## Tasks

### 1. Add `tags` field to `Event` model (`src/garys_nyc_events/models.py`)

```python
@dataclass(frozen=True)
class Event:
    ...
    tags: List[str] = field(default_factory=list)  # ← NEW
```

`Event` is `frozen=True`; use `dataclasses.field(default_factory=list)`.

---

### 2. Create `src/garys_nyc_events/tagger.py`

```python
from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger("garys_nyc_events.tagger")

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

TAG_PROMPT_TEMPLATE = """
You are a concise event tagger. Given the event metadata below, respond with ONLY a
JSON array of 3-7 lowercase short tags that best classify this event.
Do NOT include any explanation, markdown, or extra text.

Title: {title}
Description: {description}
Location: {location}

Example output: ["ai", "workshop", "free", "networking", "llm"]
"""

class GeminiTagger:
    def __init__(
        self,
        api_key: Optional[str] = None,
        http_client=None,       # HttpClient protocol — injected for tests
        max_tags: int = 7,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GEMNINI_API_KEY")
        self._http = http_client
        self.max_tags = max_tags

    def is_available(self) -> bool:
        return bool(self.api_key)

    def tag_event(self, event: Dict[str, str]) -> List[str]:
        """Return a list of tags for the event. Returns [] on any failure."""
        if not self.is_available():
            return []
        prompt = TAG_PROMPT_TEMPLATE.format(
            title=event.get("title", ""),
            description=event.get("description", "")[:500],
            location=event.get("location", ""),
        )
        try:
            return self._call_gemini(prompt)
        except Exception as exc:
            logger.warning("Gemini tagging failed for %r: %s", event.get("title"), exc)
            return []

    def tag_events(self, events: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return [{**e, "tags": self.tag_event(e)} for e in events]

    def _call_gemini(self, prompt: str) -> List[str]:
        ...  # implemented in task 3
```

---

### 3. Implement `_call_gemini` using the `HttpClient` protocol

- POST to `GEMINI_ENDPOINT?key={api_key}` with JSON body:
  ```json
  {"contents": [{"parts": [{"text": "<prompt>"}]}]}
  ```
- Parse `response.json()["candidates"][0]["content"]["parts"][0]["text"]`.
- `json.loads(...)` the text → expect a list of strings.
- Truncate to `self.max_tags`.
- Raise `ValueError` if the parsed result is not a `list[str]`.

Add `_call_gemini` to the `HttpClient` implementors; `RequestsHttpClient` must accept JSON bodies.

---

### 4. Add `GEMINI_API_KEY` to config (`src/garys_nyc_events/config.py`)

```python
@dataclass(frozen=True)
class PipelineConfig:
    ...
    gemini_api_key: Optional[str] = None   # ← NEW
    tagging_enabled: bool = True           # ← NEW; set False to skip Gemini calls

def load_config_from_env() -> PipelineConfig:
    ...
    gemini_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GEMNINI_API_KEY"),
    tagging_enabled=os.getenv("TAGGING_ENABLED", "true").lower() != "false",
```

---

### 5. Wire tagger into `runner_once._run_scrape`

After filtering, if `config.tagging_enabled` and a Gemini key is present:
```python
tagger = GeminiTagger(api_key=config.gemini_api_key)
events = tagger.tag_events(events)
```

---

### 6. Persist tags to DB (`src/garys_nyc_events/storage.py`)

- Add `tags TEXT` column to `product_snapshots` (JSON-serialised list: `'["ai","workshop"]'`).
- `fetch_events()` deserialises the column back to `List[str]` in the returned dict.

---

## Acceptance Criteria

- [ ] `Event.tags` defaults to `[]` and serialises via `dataclasses.asdict`.
- [ ] `GeminiTagger.tag_event` returns `[]` when `GEMINI_API_KEY` is absent — **no exception**.
- [ ] `GeminiTagger.tag_event` returns `[]` when the API call fails — **no exception**.
- [ ] With a valid API key, `tag_event` returns a non-empty list of lowercase strings.
- [ ] Tags column is persisted as JSON text; `fetch_events()` returns them as `List[str]`.
- [ ] `TAGGING_ENABLED=false` env var bypasses all Gemini calls.
- [ ] All prior tests pass unmodified.

---

## Tests Required

### Unit tests — `tests/test_tagger_unit.py` (new file)

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| U1 | `test_tagger_returns_empty_list_when_no_api_key` | Negative | `GeminiTagger(api_key=None).tag_event({...}) == []` |
| U2 | `test_tagger_returns_empty_list_on_network_failure` | Negative | Stub HTTP client raises `ScraperNetworkError` → `tag_event` returns `[]`, does not raise |
| U3 | `test_tagger_returns_empty_list_on_malformed_json` | Negative | Gemini returns `"not json"` → `tag_event` returns `[]` |
| U4 | `test_tagger_returns_empty_list_on_non_list_json` | Negative | Gemini returns `'{"key": "val"}'` → `tag_event` returns `[]` |
| U5 | `test_tagger_parses_valid_response` | Positive | Stub returns `'["ai","workshop","free"]'` → `tag_event` returns `["ai","workshop","free"]` |
| U6 | `test_tagger_truncates_to_max_tags` | Positive | Gemini returns 10 tags, `max_tags=5` → `len(result) == 5` |
| U7 | `test_tagger_uses_fallback_env_var_name` | Positive | `GEMNINI_API_KEY` set → `GeminiTagger().is_available() == True` |
| U8 | `test_tag_events_adds_tags_key_to_all_events` | Positive | `tag_events([e1, e2])` → both dicts have `"tags"` key |
| U9 | `test_tagging_disabled_via_config_flag` | Negative | `tagging_enabled=False` in config → tagger never called (assert call count = 0) |

### Integration tests — `tests/test_tagger_unit.py`

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| I1 | `test_tags_persisted_and_retrieved_from_db` | Positive | Persist event with `tags=["ai","free"]` → `fetch_events()[0]["tags"] == ["ai","free"]` |
| I2 | `test_tags_empty_list_stored_as_empty_json_array` | Positive | Persist event with `tags=[]` → `fetch_events()[0]["tags"] == []` |
| I3 | `test_tags_column_survives_schema_migration` | Positive | Init schema twice → no error, `tags` column still present |

### E2E test — `tests/test_e2e_live.py` (marked `@pytest.mark.e2e`)

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| E1 | `test_live_tagging_returns_nonempty_tags` | Positive | Live run with valid `GEMINI_API_KEY` → every event has `len(tags) >= 1` |
| E2 | `test_live_tagging_tags_are_lowercase_strings` | Positive | All tags are `str` and `== tag.lower()` |
| E3 | `test_live_pipeline_runs_without_api_key` | Negative | Unset `GEMINI_API_KEY` in subprocess env → pipeline completes with `status="success"` and all `tags == []` |

---

## Definition of Done

- All 15 tests pass (E2E with `pytest -m e2e`).
- `google-generativeai` **or** plain `requests` POST is the HTTP mechanism — prefer the existing
  `HttpClient` protocol over the Google SDK to avoid a heavy dependency. Add
  `google-generativeai` as an **optional** dep group in `pyproject.toml`.
- `.env` note: rename `GEMNINI_API_KEY` → `GEMINI_API_KEY` and update `.env.example`.
- No regressions in Sprints 1–13 tests.
