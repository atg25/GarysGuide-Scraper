# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- Refactored scraper architecture to follow DIP and SRP with new modules: `protocols`, `models`, `filters`, `formatters`, `newsletter_parser`, and `http`
- Runner now depends on protocol abstractions instead of concrete scraper/store implementations
- Scraper extraction logic decomposed into focused helper methods for clarity and testability
- Test suite migrated from `requests-mock` to injected HTTP client doubles
- Docker runtime moved to one-shot execution; scheduling is now external (host cron or Kubernetes CronJob)

### Removed

- Removed unsafe `get_events_safe` API that previously swallowed network failures and returned empty lists
- Removed in-container cron startup flow

## [0.2.0] - 2026-02-17

### Added (0.2.0)

- SQLite persistence layer with transactional schema (`runs`, `products`, `product_snapshots`)
- One-shot runner command with retry/backoff and run status classification
- Cron schedule validation utilities and container cron startup flow
- Dockerfile + docker-compose scheduler runtime with named volume persistence
- SQL verification scripts and operations docs (runbook, traceability, checklist)
- Unit tests for persistence, scheduler validation, retry behavior, and failure/partial run handling

## [0.1.0] - 2026-02-06

### Added (0.1.0)

- Initial scraper for GarysGuide events
- Newsletter HTML fallback parser
- Polite throttling and browser-like User-Agent
- Safe-mode API for network errors
- Test suite with unit, integration, and optional E2E tests

## [0.1.1] - 2026-02-06

### Changed (0.1.1)

- Corrected package metadata (author and repository URLs)
