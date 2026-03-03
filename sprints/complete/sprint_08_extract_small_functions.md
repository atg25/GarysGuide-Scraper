# Sprint 8 — Functions Do One Thing: Decompose `_extract_event_from_element`

**Status:** Planned  
**Prerequisite:** Sprint 7 merged  
**Review reference:** Uncle Bob audit, Section II — Functions Should Do One Thing

---

## Goal

The `_extract_event_from_element` method in `GarysGuideScraper` currently performs five distinct
operations inside a single function body. Break it into small, well-named private methods, each of
which does exactly one thing and can be read and understood in under 30 seconds.

---

## Rationale

As written, `_extract_event_from_element` does all of the following:

1. Searches for an anchor tag inside the element.
2. Extracts and cleans the title and URL from that anchor.
3. Normalizes the URL.
4. Extracts the full text blob from the element.
5. Branches on whether the element is a `<tr>` and if so reads cells.
6. Falls back to text-blob extraction for both date and price.
7. Constructs and returns an `Event`.

A function that contains `if element.name == "tr"` is a function that has more than one reason to
exist. The table-row path and the text-blob path are two different parsing strategies. Uncle Bob's
rule: _"The first rule of functions is that they should be small. The second rule is that they should
be smaller than that."_

---

## Tasks

### 1. Extract `_extract_anchor(element: Tag) -> Optional[Tuple[str, str]]`

Responsibility: find the first `<a href>` inside `element`, return `(clean_title, clean_href)`.
Return `None` if no anchor exists or either value is empty.

This completely replaces the first block of `_extract_event_from_element`.

---

### 2. Extract `_extract_date_from_table_row(cells: List[Tag]) -> str`

Responsibility: given the list of `<td>` elements from a `<tr>`, extract the date string from
`cells[0]`.

This replaces the `if element.name == "tr":` branch for date.

---

### 3. Extract `_extract_price_from_table_row(cells: List[Tag]) -> str`

Responsibility: given the list of `<td>` elements from a `<tr>`, extract the price string from
`cells[-1]`.

This replaces the `if element.name == "tr":` branch for price.

---

### 4. Extract `_extract_date_and_price_from_element(element: Tag) -> Tuple[str, str]`

Responsibility: orchestrate — try the table-row strategy first; fall back to text-blob extraction.
Returns `(date, price)`.

This is the only function allowed to contain the `if element.name == "tr"` branch. It delegates
immediately to `_extract_date_from_table_row` or `_extract_date` / `_extract_price`.

---

### 5. Rewrite `_extract_event_from_element` as an orchestrator

After the extractions above, the method body should read as a sequence of noun-verb statements
that could be narrated aloud:

```python
anchor = self._extract_anchor(element)
if anchor is None:
    return None
title, href = anchor
url = self._normalize_url(href)
date, price = self._extract_date_and_price_from_element(element)
return Event(title=title, date=date, price=price, url=url, source="garysguide_web")
```

No logic should live in this method — only delegation.

---

### 6. Remove the `_clean` / `_normalize_url` inline calls from `_extract_event_from_element`

These are already private methods. Their calls must now live only inside the purpose-named
extraction helpers, not scattered through the orchestrator.

---

## Acceptance Criteria

- [ ] `_extract_event_from_element` body contains only delegation calls (no `if`, no string
      manipulation, no regex).
- [ ] `_extract_anchor` exists, returns `Optional[Tuple[str, str]]`, has its own unit test.
- [ ] `_extract_date_from_table_row` exists, takes `List[Tag]`, has its own unit test.
- [ ] `_extract_price_from_table_row` exists, takes `List[Tag]`, has its own unit test.
- [ ] `_extract_date_and_price_from_element` exists, returns `Tuple[str, str]`, has its own unit
      test for both the table-row path and the text-blob fallback path.
- [ ] No method in `GarysGuideScraper` has a cyclomatic complexity > 3 (enforce with
      `flake8 --max-complexity 3` on `scraper.py`).
- [ ] All existing scraper tests continue to pass.

---

## Tests Required

All tests go in `tests/test_scraper_unit.py`.

| #   | Name                                                 | Type | What it asserts                                                              |
| --- | ---------------------------------------------------- | ---- | ---------------------------------------------------------------------------- |
| 1   | `test_extract_anchor_returns_none_when_no_link`      | Unit | Element with no `<a>` tag → `None`                                           |
| 2   | `test_extract_anchor_returns_none_when_title_empty`  | Unit | `<a href="/events/x"></a>` (empty text) → `None`                             |
| 3   | `test_extract_anchor_returns_title_and_href`         | Unit | Well-formed anchor → `("Title", "/events/x")`                                |
| 4   | `test_extract_date_from_table_row_first_cell`        | Unit | Two `<td>` tags, first contains "Mon Jan 6" → returns that string            |
| 5   | `test_extract_price_from_table_row_last_cell`        | Unit | Three `<td>` tags, last contains "$25" → `"$25"`                             |
| 6   | `test_extract_date_and_price_prefers_table_row`      | Unit | `<tr>` element with cells → uses cell extraction, not text blob              |
| 7   | `test_extract_date_and_price_falls_back_to_blob`     | Unit | `<div>` element → uses text-blob extraction                                  |
| 8   | `test_extract_event_from_element_is_pure_delegation` | Unit | Spy/stub all four helpers; assert each is called exactly once per invocation |

---

## Definition of Done

- All eight new unit tests pass.
- `flake8 --max-complexity 3 src/garys_nyc_events/scraper.py` exits 0.
- A code reviewer can read and fully understand each new private method in under 30 seconds.
