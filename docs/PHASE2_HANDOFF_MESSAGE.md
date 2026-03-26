# Phase 1 Closed → Phase 2 Staging Deployment

**From:** Gary's Guide PyPack Development Team  
**To:** Midterm_Ordo Development Team  
**Date:** 2026-03-26 (Triggered on Slot 8 Closure)  
**Timestamp:** 2026-03-26T19:05:00Z  
**Subject:** Phase 2 Staging Deployment – Contract Frozen, MCP Server Ready

---

## Checkpoint Status

✅ **Phase 1 Complete** – All 8 matrix slots closed (Slots 1-8 PASS/PROVISIONAL_PASS)  
🚀 **Phase 2 Initiated** – Staging deployment begins now  
🎯 **Phase 3 Target** – 2026-03-28 (E2E cross-repo validation)  
💫 **Phase 4 Target** – 2026-03-29 (Final approval + merge)

---

## What's New (Phase 2)

### 1. PyPack MCP Server Staging Deployment

**Deployment Package:**

- Docker image: `garys-events-mcp:staging` (built and ready)
- Deployment script: `scripts/deploy_staging.sh`
- Compose file: `docker-compose.staging.yml`
- Configuration template: `.env.staging.template`

**Deploy now with:**

```bash
bash scripts/deploy_staging.sh full
```

This command will:

1. Build MCP server Docker image
2. Deploy to staging environment
3. Validate MCP contract (ListTools, CallTool)
4. Show deployment status

**Staging endpoint:** Will be provided after deployment (e.g., `mcp://localhost:9000`)

### 2. Contract Frozen – No Changes Pending

**Canonical Tool Identity:**

- Tool name: `garys_events.query_events` (locked, no aliases)
- No pending changes to tool registration

**Request/Response Envelope:**

- Success: `{ok: true, data: {count: number, events: [...]}}`
- Error: `{ok: false, error: {code: string, message: string, retriable: boolean}}`
- Schema validated (additionalProperties: false; all fields required)

**Retriable Error Classification:**
| Code | Retriable | Examples |
|---|---|---|
| timeout | ✅ TRUE | Request exceeds TIMEOUT_MS |
| network_error | ✅ TRUE | Connection refused, DNS failure |
| rate_limit_exceeded | ✅ TRUE | HTTP 429 |
| service_unavailable | ✅ TRUE | HTTP 503, 504 |
| validation_error | ❌ FALSE | Invalid schema, unknown fields, type mismatch |
| unknown_tool | ❌ FALSE | Tool name does not match canonical ID |
| tool_disabled | ❌ FALSE | GARYS_EVENTS_MCP_ENABLED=false |

**No runtime changes to this taxonomy are pending.**

### 3. Environment Variables (Staging Config)

**Required for Midterm integration:**

```
GARYS_EVENTS_REST_API_BASE_URL=<staging-endpoint-url>
GARYS_EVENTS_REST_API_TIMEOUT_MS=5000
GARYS_EVENTS_MCP_ENABLED=true
GARYS_EVENTS_MCP_FAIL_OPEN=true
GARYS_EVENTS_MCP_REPO_PATH=<path-to-pypack-repo>
```

All pre-configured in `.env.staging.template`.

### 4. E2E Test Scenarios (Phase 3)

**Available scenarios in `tests/e2e_scenarios.py`:**

1. **Startup timeout** – MCP respects timeout, returns retriable error
2. **Crash recovery** – Server handles unrecoverable errors, remains operational
3. **Rate limit (429)** – 429 response mapped to retriable error
4. **Service unavailable (503/504)** – 503/504 mapped to retriable error
5. **Graceful shutdown** – SIGTERM exits cleanly
6. **Contract validation** – Unknown tools and schema violations rejected

**Run scenarios:**

```bash
python -m tests.e2e_scenarios
```

---

## What You Need To Do Now (Midterm)

### 1. Integrate Staging MCP Server

**Setup:**

```bash
git clone https://github.com/atg25/Midterm_Ordo.git
cd Midterm_Ordo
bash scripts/deploy_staging.sh full  # Deploy PyPack MCP to staging
```

**Test ListTools:**

```bash
# Should return single tool: garys_events.query_events
curl -X GET http://localhost:9000/tools
```

**Test CallTool:**

```bash
# Should return events or validate error
curl -X POST http://localhost:9000/call \
  -d '{"tool":"garys_events.query_events","args":{"limit":10}}'
```

### 2. Validate Contract Points

- [ ] Tool identity is `garys_events.query_events` (no aliases)
- [ ] Response envelope matches `{ok: bool, data/error}` format
- [ ] Timeout behavior: request >5000ms returns `{ok: false, error: {code: "timeout", retriable: true}}`
- [ ] Unknown tool: request to unknown tool returns `{ok: false, error: {code: "unknown_tool", retriable: false}}`
- [ ] Invalid schema: extra fields rejected with validation error (retriable: false)

### 3. Run E2E Failure-Injection Scenarios

```bash
python -m tests.e2e_scenarios
```

This will validate:

- Timeout handling ✓
- Error classifications ✓
- Retriable semantics ✓
- Response envelope shape ✓

### 4. Document Integration Results

Provide feedback:

- ✅ All contract points validated
- ✅ All error codes mapped correctly
- ✅ All retriable classifications correct
- ⚠️ Any deviations or clarifications needed

---

## Phase 2 Timeline

| Milestone               | Owner        | Target         | Status         |
| ----------------------- | ------------ | -------------- | -------------- |
| **MCP server built**    | Gary's Guide | 2026-03-27 NOW | ✅ DONE        |
| **Staging deployed**    | Midterm      | 2026-03-27     | 🟡 IN PROGRESS |
| **Contract validation** | Midterm      | 2026-03-27     | ⏳ DUE         |
| **E2E scenarios run**   | Midterm      | 2026-03-27 EOD | ⏳ DUE         |
| **Phase 2 sign-off**    | Both         | 2026-03-27 EOD | ⏳ PENDING     |

---

## If You Hit Issues

**Problem:** Staging deploy fails  
**Solution:** Check `.env.staging` configuration; reach out if blocked

**Problem:** MCP contract mismatch  
**Solution:** Verify request/response envelope; cross-check with `src/garys_nyc_events/mcp/server.py`

**Problem:** E2E scenario failures  
**Solution:** Review scenario expectation vs. actual response; debug specific failure case

**Support:** Ask now – we will respond within 1 hour

---

## Phase 3 Preview (2026-03-28)

Once Phase 2 sign-off is complete:

- Full cross-repo E2E validation
- Failure injection tests (timeout, crash, rate limit, service unavailable)
- Load/performance baseline
- No-merge gate status

---

## Closing Notes

Slot 1 is locked in. Slot 8 just closed. **Phase 2 is live.** Your task: integrate the staging MCP server, validate contract points, and run E2E scenarios. Full team support available if you hit blockers.

**Let's move fast.** Next checkpoint: Phase 2 sign-off by 2026-03-27 EOD.

---

**Signed,**  
Gary's Guide PyPack Development Team

**Timestamp:** 2026-03-26T19:05:00Z  
**Authority:** Phase 2 coordination  
**Next checkpoint:** Phase 2 sign-off (all contract validations complete)
