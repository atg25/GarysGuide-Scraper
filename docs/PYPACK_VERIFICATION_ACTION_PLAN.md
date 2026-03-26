# PyPack_GarysGuide: Cross-Repo Verification Action Plan

**To:** Gary's Guide PyPack Development Team  
**From:** Project Governance (on behalf of Midterm_Ordo Integration)  
**Date (Timestamp):** 2026-03-26T14:50:00Z  
**Last Updated:** 2026-03-26T19:05:00Z (Slot 8 Re-Score PASS)  
**Status:** SPRINT 20 UNBLOCKED – PHASE 1 COMPLETE; PHASE 2 ACTIVE

---

## Executive Summary

Midterm_Ordo delivered all first-drop artifacts (2026-03-26T15:20:00Z), remediation packet (2026-03-26T15:55:00Z), and Slot 8 follow-up packet (2026-03-26T18:55:00Z). **Phase 1 is now complete.**

**Current State:**

- ✅ PyPack artifacts delivered (14:26:43Z)
- ✅ Midterm delivery acknowledgment received (14:50:00Z)
- ✅ PyPack slots: 9/9 PASS/IMPLEMENTED
- ✅ Midterm evidence packet received & re-scored (2026-03-26T15:20:00Z → 2026-03-26T16:05:00Z)
  - **Slot 1: CONDITIONAL → ✅ PASS** (Lifecycle test evidence complete)
  - **Slots 2-7: ✅ PROVISIONAL_PASS** (Targeted evidence verified)
  - **Slot 8: ✅ PASS** (full-repo gates green: test/typecheck/lint strict all pass)
- 🚀 **Phase 2:** ACTIVE (staging handoff dispatched)
- 🔒 **Final merge:** remains governed by Phase 4 approval policy

**Your task:** Execute Phase 2 staging integration and schedule Phase 3 E2E validation.

---

## What Midterm Delivered & Re-Score Status (Updated 2026-03-26T16:05:00Z)

All 8 required matrix slots implemented and tested on Midterm side. **Phase 1 re-scoring complete.**

| #   | Slot                         | Evidence                                                                        | Initial Status      | Re-Score Status (2026-03-26T16:05:00Z) |
| --- | ---------------------------- | ------------------------------------------------------------------------------- | ------------------- | -------------------------------------- |
| 1   | Subprocess startup/lifecycle | 3/3 lifecycle tests (timeout, crash+retry, graceful stop); runtime fix provided | ⚠️ CONDITIONAL      | ✅ **PASS**                            |
| 2   | Fail-open default            | Targeted test output provided                                                   | ✅ PROVISIONAL PASS | ✅ **PROVISIONAL PASS**                |
| 3   | Fail-closed toggle           | Targeted test output provided                                                   | ✅ PROVISIONAL PASS | ✅ **PROVISIONAL PASS**                |
| 4   | Dot-name compatibility       | Pre-registration pointer sequence provided                                      | ✅ PROVISIONAL PASS | ✅ **PROVISIONAL PASS**                |
| 5   | Alias deterministic mapping  | Alias mapping test snippet provided                                             | ✅ PROVISIONAL PASS | ✅ **PROVISIONAL PASS**                |
| 6   | Tool-count updates           | Assertions + targeted outputs provided                                          | ✅ PROVISIONAL PASS | ✅ **PROVISIONAL PASS**                |
| 7   | Role visibility/blocking     | Role tests + outputs provided                                                   | ✅ PROVISIONAL PASS | ✅ **PROVISIONAL PASS**                |
| 8   | Midterm quality gates        | Follow-up packet: 1632/1632 tests pass, typecheck exit 0, lint strict exit 0    | ❌ FAIL             | ✅ **PASS**                            |

**Full details:** [docs/PYPACK_PHASE1_REMEDIATION_RESPONSE.md](PYPACK_PHASE1_REMEDIATION_RESPONSE.md) (formal re-score letter)  
**Matrix:** [docs/CROSS_REPO_RELEASE_GATE_MATRIX.md](CROSS_REPO_RELEASE_GATE_MATRIX.md) (updated with verification log entries)

---

## Phase 1 Remediation Re-Score Summary (2026-03-26T15:55:00Z – 2026-03-26T16:05:00Z)

### Remediation Packet Received

Midterm_Ordo submitted targeted remediation packet at 2026-03-26T15:55:00Z addressing Slots 1 and 8.

### Slot 1: Lifecycle Test Evidence → ✅ **PASS CONFIRMED**

**Evidence Provided:**

- Test file: `src/lib/mcp/garys-events-runtime.lifecycle.test.ts`
- Test command: `npm run test -- src/lib/mcp/garys-events-runtime.lifecycle.test.ts`
- Raw output: 3/3 passing test cases
  - ✓ returns timeout runtime error when startup connect exceeds configured timeout
  - ✓ retries startup after crash and succeeds on a later attempt
  - ✓ registers shutdown hooks and closes transport on explicit shutdown

**Verification Against Strict Criteria:**
All seven required criteria met:

1. ✅ Test names explicit and specific
2. ✅ Reproducible command provided (npm run test with file path)
3. ✅ Raw output proof of timeout handling
4. ✅ Raw output proof of crash+retry recovery
5. ✅ Raw output proof of graceful shutdown
6. ✅ Supporting runtime fix referenced (retriable classification updated)
7. ✅ Evidence committed to working tree (Midterm branch)

**Verdict:** Slot 1 status changed from CONDITIONAL → PASS effective 2026-03-26T16:05:00Z.

### Slot 8: Full-Repo Quality Gates → ❌ **GATES STILL RED (Remediation In Progress)**

**Fresh Gate Outputs:**

- `npm run test`: 11 failed / 1621 passed (1632 total) → exit code 1 ❌
- `npm run typecheck`: 2 errors in src/components/GraphRenderer.tsx → exit code 2 ❌
- `npm run lint:strict`: 14 problems (4 errors, 10 warnings) → exit code 1 ❌

**Verdict:** All three required gates remain red. Slot 8 does not close on this packet. Status: REMEDIATION_IN_PROGRESS.

**Midterm Commitment:** Follow-up packet with green outputs to be submitted immediately. Merge gate locked until Slot 8 PASS received and verified.

### Gate Matrix Impact

- **Slots closed:** 7 of 8 (Slots 1, 2-7 all PASS/PROVISIONAL_PASS)
- **Merge gate:** LOCKED (awaiting Slot 8)
- **Phase 2 authorization:** Parallel prep work approved; staging deployment blocked on Slot 8 close

---

## Phase 1: Verification (Checkpoint STARTED NOW at 2026-03-26T14:51:06Z; Slot 1 Closed 2026-03-26T16:05:00Z; Slot 8 Closed 2026-03-26T18:55:00Z)

### Task 1.1: Review Midterm Artifacts

- [ ] Read [MIDTERM_FIRST_DROP_ARTIFACT_DELIVERY.md](MIDTERM_FIRST_DROP_ARTIFACT_DELIVERY.md) in full
- [ ] Cross-reference each section with your MCP implementation
- [ ] Verify architecture decisions align
- [ ] Document any questions or clarifications needed

**Estimated time:** 2-3 hours

### Task 1.2: Validate Matrix Slot Compliance

For each of the 8 matrix slots, confirm Midterm's implementation matches your expectations:

#### Slot 1: Module Entrypoint Integration

- [ ] Confirm Midterm can invoke `python -m garys_nyc_events.mcp.server`
- [ ] Verify subprocess starts successfully
- [ ] Verify stderr/stdout handling is correct (stdio transport)
- [ ] Document any issues or deviations

#### Slot 2: Tool Identity Recognition

- [ ] Verify tool appears as `garys_events.query_events` in Midterm's registry
- [ ] Confirm no aliases or alternate names are exposed
- [ ] Verify tool is properly gated (only visible when enabled)

#### Slot 3: ListTools Contract

- [ ] Request ListTools response from Midterm
- [ ] Compare response structure with [MIDTERM_RESPONSE_ARTIFACT_DELIVERY.md](MIDTERM_RESPONSE_ARTIFACT_DELIVERY.md) sample
- [ ] Verify schema matches exactly (properties, required fields, validation)
- [ ] Verify only canonical tool is listed (count should be 1)

#### Slot 4: CallTool Execution

- [ ] Request CallTool execution with sample payloads
- [ ] Verify strict schema validation (reject unknown fields, require limit, etc.)
- [ ] Verify deterministic dispatch (same input → same output)

#### Slot 5: Output Normalization

- [ ] Compare success responses with your expected shape: `{ok: true, data: {count, events}}`
- [ ] Verify no internal host details, stack traces, or secrets in output
- [ ] Verify event objects only contain safe fields (id, date, title, location, tags)

#### Slot 6: Error Handling & Retriable Classification

- [ ] Request error responses (timeout, invalid input, rate limit, etc.)
- [ ] Compare error codes with your taxonomy
- [ ] Verify retriable classification matches (transient vs. non-transient)
- [ ] Document any mismatches

#### Slot 7: Environment Variable Configuration

- [ ] Verify Midterm consumes `GARYS_EVENTS_REST_API_BASE_URL` correctly
- [ ] Verify Midterm consumes `GARYS_EVENTS_REST_API_TIMEOUT_MS` correctly
- [ ] Verify Midterm respects `GARYS_EVENTS_MCP_ENABLED` (fail-open/fail-closed modes)
- [ ] Document default values used

#### Slot 8: Quality Gates Validation

- [x] Review Midterm test/typecheck/lint packet outputs (Initial packet 2026-03-26T15:20:00Z)
- [x] Review Midterm remediation packet outputs (Fresh run 2026-03-26T15:55:00Z)
- [x] Log intermediate failure state in verification matrix
- [x] Receive follow-up packet with green outputs for `npm run test`, `npm run typecheck`, `npm run lint:strict`
- [x] Re-score follow-up packet immediately (15-minute SLA)
- [x] Verify all three quality gates show PASS before sign-off

**Status:** PASS – Slot 8 closed at 2026-03-26T18:55:00Z packet intake; Phase 1 verification blocker removed.

**Estimated time:** 2-4 hours (code review + spot checks)

### Task 1.3: Verification Sign-Off

**Deliverable:** Email to Midterm team (atg25) with:

```
Subject: PyPack Verification Sign-Off – All Slots Validated

Status: [PASS / CONDITIONAL PASS with notes / FAIL]

Slot-by-slot validation:
- [ ] Subprocess startup/lifecycle: PASS / CONDITIONAL / FAIL
- [ ] Fail-open default: PASS / CONDITIONAL / FAIL
- [ ] Fail-closed toggle: PASS / CONDITIONAL / FAIL
- [ ] Dot-name compatibility: PASS / CONDITIONAL / FAIL
- [ ] Alias deterministic mapping: PASS / CONDITIONAL / FAIL
- [ ] Tool-count updates: PASS / CONDITIONAL / FAIL
- [ ] Role visibility/blocking: PASS / CONDITIONAL / FAIL
- [ ] Midterm quality gates: PASS / CONDITIONAL / FAIL

Summary: [2-3 paragraphs on overall assessment]

Blockers: [None / description if any]

Questions for next phase: [List any clarifications needed before staging]
```

---

## Phase 2: Staging Environment Setup (Next 48 Hours – By 2026-03-28)

### Task 2.1: Deploy PyPack MCP Server to Staging

**Prerequisites:**

- Staging environment is available
- Python environment is set up (venv or similar)
- PyPack repository is cloned/available

**Steps:**

- [ ] Check out PyPack_GarysGuide from main branch
- [ ] Install dependencies: `pip install -r requirements.txt` (or via poetry)
- [ ] Verify MCP server is available: `python -m garys_nyc_events.mcp.server --help` (or just run it)
- [ ] Configure environment variables:
  ```
  export GARYS_EVENTS_REST_API_BASE_URL="https://staging-api.garys-guide.app"  # Example
  export GARYS_EVENTS_REST_API_TIMEOUT_MS=5000
  export GARYS_EVENTS_MCP_ENABLED=true
  ```
- [ ] Start server in background (using supervisor, systemd, docker, or similar)
- [ ] Verify server is listening on stdin/stdout (test with a simple ListTools call)
- [ ] Verify logs show successful startup
- [ ] Document any issues or configuration changes

**Estimated time:** 2-3 hours

### Task 2.2: Share Staging Endpoint with Midterm

**Deliverable:** Email to Midterm team with:

```
Staging Deployment Complete

Endpoint details:
- Server command: python -m garys_nyc_events.mcp.server
- Host: [staging hostname]
- Status: [running / ready for subprocess integration]
- Environment variables configured: [list]
- Logs available at: [log path]

Ready for Midterm integration testing: YES / NO
```

**Estimated time:** 0.5 hours (documentation)

### Task 2.3: Generate Test Evidence Artifacts

**Deliverable:** Create a file with sample request/response pairs (send to Midterm):

```markdown
# PyPack MCP Server – Staging Test Evidence

## Sample 1: ListTools Response

Request: (none – standalone ListTools call)
Response:
[
{
"name": "garys_events.query_events",
...schema...
}
]

## Sample 2: CallTool Success (Basic Query)

Request: {"limit": 10}
Response: {
"ok": true,
"data": {
"count": 10,
"events": [...]
}
}

## Sample 3: CallTool Success (With Tags)

Request: {"limit": 20, "tags": ["music", "tech"]}
Response: {
"ok": true,
"data": {
"count": 12,
"events": [...]
}
}

## Sample 4: Error – Validation Failure

Request: {"limit": 600} # Exceeds max of 500
Response: {
"ok": false,
"error": {
"code": "validation_error",
"message": "limit must be an integer between 0 and 500",
"retriable": false
}
}

## Sample 5: Error – Timeout

Request: {query that takes >5000ms to respond}
Response: {
"ok": false,
"error": {
"code": "api_timeout",
"message": "Request to REST API exceeded timeout threshold",
"retriable": true
}
}
```

**Estimated time:** 1-2 hours

---

## Phase 3: Cross-Repo E2E Testing (Next 3 Days – By 2026-03-29)

### Task 3.1: Enable Midterm Integration

Your role: **Monitor and support**

- Midterm will set `GARYS_EVENTS_REST_API_BASE_URL` to your staging endpoint
- Midterm will set `GARYS_EVENTS_MCP_ENABLED=true`
- Midterm will test subprocess startup
- **You:** Monitor logs, confirm requests are arriving

### Task 3.2: Test Various Query Scenarios

Midterm will execute queries like these; you monitor/validate:

**Basic Query:**

```json
{ "limit": 10 }
```

**With Tags:**

```json
{ "limit": 20, "tags": ["music", "techspeaker"] }
```

**With Date Range:**

```json
{ "limit": 30, "date_from": "2026-03-20", "date_to": "2026-03-30" }
```

**With AI-Only Filter:**

```json
{ "limit": 15, "ai_only": true }
```

**Error Scenarios (test handling):**

- Server timeout (intentionally slow response)
- Invalid input (limit > 500)
- Rate-limit response (429)
- Service error (503)

**Your task:** Verify each scenario produces correct response, logs are clean, no regressions.

### Task 3.3: Final Validation

- [ ] All E2E tests passed
- [ ] Error handling works as expected
- [ ] Performance meets expectations (no timeouts, reasonable latency)
- [ ] No regressions on PyPack side
- [ ] Logs are clean (no errors, warnings only where expected)

**Estimated time:** 3-4 hours (monitoring + troubleshooting)

---

## Phase 4: Final Approval & Merge Gate Release (By 2026-03-29T23:59:59Z)

### Task 4.1: Approval Sign-Off

**Deliverable:** Final email to Midterm + governance:

```
Subject: PyPack Integration – Final Approval for Production

Integration status: APPROVED FOR PRODUCTION

Verification phase: COMPLETE ✅
- All 8 matrix slots validated
- Architecture decisions confirmed
- Contract compliance verified

Staging deployment: COMPLETE ✅
- MCP server running in staging
- E2E tests all passing
- Error handling validated

Quality assurance: COMPLETE ✅
- No regressions detected
- Performance acceptable
- Logs clean

Production readiness: YES ✅

Approval to merge: YES ✅
Approval to deploy: YES ✅

PyPack team contact: [email]
```

**Estimated time:** 0.5 hours

---

## Timeline Summary

| Date                 | Phase                 | Deliverable                 | Status           |
| -------------------- | --------------------- | --------------------------- | ---------------- |
| 2026-03-26           | Artifacts Delivery    | PyPack + Midterm first-drop | ✅ COMPLETE      |
| 2026-03-27           | Verification          | Slot-by-slot validation     | 🔄 IN PROGRESS   |
| 2026-03-27T23:59:59Z | Verification Sign-Off | Email to Midterm            | ⏳ DUE THIS WEEK |
| 2026-03-28           | Staging Setup         | Deploy + endpoint sharing   | ⏳ NEXT WEEK     |
| 2026-03-28           | E2E Kickoff           | Midterm integration begins  | ⏳ NEXT WEEK     |
| 2026-03-29           | E2E Testing           | Cross-repo testing complete | ⏳ NEXT WEEK     |
| 2026-03-29T23:59:59Z | Final Approval        | Merge gate release          | ⏳ NEXT WEEK     |
| 2026-03-30           | Production Ready      | Deploy to production        | ⏳ FUTURE        |

---

## Key Files & Resources

**Midterm Deliverables (Read These):**

1. [MIDTERM_FIRST_DROP_ARTIFACT_DELIVERY.md](MIDTERM_FIRST_DROP_ARTIFACT_DELIVERY.md) – Full artifact details
2. [INTEGRATION_HANDOFF_SUMMARY.md](INTEGRATION_HANDOFF_SUMMARY.md) – Architecture decisions
3. [MIDTERM_STATUS_UPDATE_TO_GARYS_GUIDE.md](MIDTERM_STATUS_UPDATE_TO_GARYS_GUIDE.md) – Status overview

**PyPack References (Yours):**

- [docs/MIDTERM_RESPONSE_ARTIFACT_DELIVERY.md](docs/MIDTERM_RESPONSE_ARTIFACT_DELIVERY.md) – Your artifact delivery
- [docs/CROSS_REPO_RELEASE_GATE_MATRIX.md](docs/CROSS_REPO_RELEASE_GATE_MATRIX.md) – Gate status (updated)
- [docs/MIDTERM_DISPATCH_STATUS.md](docs/MIDTERM_DISPATCH_STATUS.md) – Governance tracker

---

## Escalation & Support

**If you encounter blockers:**

- Reach out to Midterm_Ordo (atg25) directly
- Flag in next daily standup
- We're committed to resolving any issues quickly

**Expected Success Rate:** High

- Integration layer is complete and tested
- Contracts are well-defined
- Both teams have full documentation

---

## What Success Looks Like

By end of approval phase (2026-03-29):

- ✅ All 8 matrix slots verified by both teams
- ✅ Cross-repo E2E tests passing
- ✅ Error handling validated in real scenarios
- ✅ Performance acceptable
- ✅ No-merge gate released
- ✅ Production deployment approved

---

## Next Steps

**Immediate:**

1. **Today/Tomorrow:** Review Midterm artifacts at [MIDTERM_FIRST_DROP_ARTIFACT_DELIVERY.md](MIDTERM_FIRST_DROP_ARTIFACT_DELIVERY.md)
2. **By Friday:** Complete verification checklist and send sign-off email

**Next Week:** 3. **Monday:** Deploy staging, share endpoint 4. **Wednesday:** Complete E2E testing 5. **Thursday:** Final approval email

---

**Sprint 20 Status:** UNBLOCKED – MOVING TO VERIFICATION PHASE  
**No-merge gate:** Still enforced until final verification phase complete  
**Production deployment:** Pending cross-repo verification completion

---

**Questions?** Reach out to governance or Midterm_Ordo team.

**Timestamp:** 2026-03-26T14:50:00Z  
**Document:** PyPack_GarysGuide/docs/PYPACK_VERIFICATION_ACTION_PLAN.md
