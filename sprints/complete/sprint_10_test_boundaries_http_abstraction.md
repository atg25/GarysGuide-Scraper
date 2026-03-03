# Sprint 10 — Test Boundaries: Rename Integration Tests and Abstract the HTTP Client

**Status:** Planned  
**Prerequisite:** Sprint 9 merged  
**Review reference:** Uncle Bob audit, Section IV — Testing Boundaries

---

## Goal

Fix the incorrect labeling of mocked-HTTP tests as "integration tests." Then decouple all tests
from the `requests` library by introducing an `HttpClient` protocol and injecting it into
`GarysGuideScraper`, so swapping the HTTP library never breaks a test.

---

## Rationale

A test that uses `requests_mock` is not an integration test. `requests_mock` intercepts calls at
the `requests` layer before any I/O occurs. The test never touches a socket. By calling it an
integration test, the team misleads itself about what coverage it actually has and what the test
pyramid looks like.

More dangerously, every mock at the `requests` layer is a coupling point. If the team replaces
`requests` with `httpx` for async support, all of these "integration" tests must be rewritten even
though the scraping logic has not changed at all. The scraping algorithm has nothing to do with
which HTTP library carries the bytes.

Uncle Bob: _"Design your systems so that you can test the most important behaviors without spin-up
costs and without being coupled to external libraries or frameworks."_

---

## Tasks

### 1. Rename and reclassify `test_scraper_integration.py`

Rename `tests/test_scraper_integration.py` → `tests/test_scraper_unit.py` (consolidating into the
existing unit test file, or a clearly named `test_scraper_http_unit.py` if size warrants it).

Update `pyproject.toml` `[tool.pytest.ini_options]` test markers if any marker distinguishes
integration from unit tests. Ensure CI still runs all tests.

Do the same audit for `test_scraper_safe_integration.py` — rename or merge into a unit test file.

---

### 2. Define `HttpClient` protocol in `protocols.py`

Add to `src/garys_nyc_events/protocols.py`:

```python
class HttpResponse(Protocol):
    @property
    def text(self) -> str: ...
    def raise_for_status(self) -> None: ...

class HttpClient(Protocol):
    def get(
        self,
        url: str,
        *,
        headers: Dict[str, str],
        timeout: int,
    ) -> HttpResponse: ...
```

No `requests` import inside `protocols.py`.

---

### 3. Create `src/garys_nyc_events/http.py` — the real implementation

```python
class RequestsHttpClient:
    def get(self, url: str, *, headers: Dict[str, str], timeout: int) -> requests.Response:
        return requests.get(url, headers=headers, timeout=timeout)
```

This is the only file in the entire package that imports `requests` (other than `exceptions.py`
wrapping, if needed). All other modules must be free of `import requests`.

---

### 4. Inject `HttpClient` into `GarysGuideScraper`

Update `GarysGuideScraper.__init__` to accept an optional `http_client: Optional[HttpClient]`
parameter.

```python
def __init__(
    self,
    delay_seconds: float = 1.5,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout_seconds: int = 10,
    http_client: Optional[HttpClient] = None,
) -> None:
    self._http = http_client or RequestsHttpClient()
```

Update `_fetch_html` to call `self._http.get(...)` instead of `requests.get(...)`.

Remove the top-level `import requests` from `scraper.py`. The scraper no longer needs to know
the HTTP library exists.

---

### 5. Create `tests/http_doubles.py` — test doubles for `HttpClient`

Create a small test-only module with reusable stubs:

```python
class StubHttpResponse:
    def __init__(self, text: str, status_code: int = 200): ...
    def raise_for_status(self) -> None: ...  # raises ScraperNetworkError on 4xx/5xx

class StubHttpClient:
    def __init__(self, responses: List[StubHttpResponse]): ...
    def get(self, url, *, headers, timeout) -> StubHttpResponse: ...

class FailingHttpClient:
    """Always raises ScraperNetworkError."""
    def get(self, url, *, headers, timeout) -> NoReturn: ...
```

---

### 6. Rewrite `requests_mock`-based tests to use `StubHttpClient`

Replace every test that uses `@requests_mock.Mocker` or the `requests_mock` fixture with an
equivalent test that constructs a `StubHttpClient` and injects it into `GarysGuideScraper`.

Example before:

```python
def test_parse_events_returns_list(requests_mock):
    requests_mock.get(URL, text=SAMPLE_HTML)
    scraper = GarysGuideScraper()
    events = scraper.get_events()
    assert len(events) > 0
```

Example after:

```python
def test_parse_events_returns_list():
    client = StubHttpClient([StubHttpResponse(text=SAMPLE_HTML)])
    scraper = GarysGuideScraper(http_client=client)
    events = scraper.get_events()
    assert len(events) > 0
```

---

### 7. Remove `requests-mock` from dev dependencies

After all tests are migrated, remove `requests-mock` from `pyproject.toml`
`[tool.poetry.dev-dependencies]` and run `poetry lock --no-update` to update the lock file.

---

### 8. Define what a true integration test looks like (documentation)

Create `docs/TESTING_STRATEGY.md` describing:

- **Unit tests:** no I/O, no network, no filesystem. Use doubles. Fast enough to run on every save.
- **Integration tests:** hit a real local server or a recorded fixture via VCR; never mock at the
  library level.
- **E2E tests:** hit the live `garysguide.com` endpoint. Run only in CI on a schedule, not on every
  push. Tagged `@pytest.mark.e2e` and excluded from the default test run.

---

## Acceptance Criteria

- [ ] No file under `tests/` is named `*_integration.py` unless it actually performs I/O against a
      real endpoint.
- [ ] `requests_mock` does not appear anywhere in `tests/`.
- [ ] `import requests` does not appear in `scraper.py`.
- [ ] `GarysGuideScraper` accepts an `http_client` constructor parameter.
- [ ] `StubHttpClient` and `FailingHttpClient` exist in `tests/http_doubles.py`.
- [ ] All tests pass without `requests-mock` installed.
- [ ] `docs/TESTING_STRATEGY.md` exists and documents all three test tiers.

---

## Tests Required

All existing `requests_mock`-based tests are rewritten in place (not added to). New tests:

| #   | Name                                                       | Type | What it asserts                                           |
| --- | ---------------------------------------------------------- | ---- | --------------------------------------------------------- |
| 1   | `test_scraper_uses_injected_http_client`                   | Unit | `StubHttpClient` call count is 1 after `get_events()`     |
| 2   | `test_scraper_raises_on_failing_http_client`               | Unit | `FailingHttpClient` → `ScraperNetworkError` is raised     |
| 3   | `test_requests_http_client_satisfies_http_client_protocol` | Unit | `isinstance(RequestsHttpClient(), HttpClient)` is `True`  |
| 4   | `test_stub_http_client_satisfies_http_client_protocol`     | Unit | `isinstance(StubHttpClient([...]), HttpClient)` is `True` |

---

## Definition of Done

- `grep -rn "requests_mock" tests/` returns zero results.
- `grep -rn "import requests" src/garys_nyc_events/scraper.py` returns zero results.
- `docs/TESTING_STRATEGY.md` exists.
- CI passes with `requests-mock` removed from dev dependencies.
