# Contributing

Thanks for considering contributing!

## Setup

```bash
poetry install
```

## Tests

```bash
poetry run pytest
```

## Linting

This project keeps dependencies minimal and does not enforce a formatter by default. If you contribute code, follow the existing style.

## E2E Tests

Live scraping tests are disabled by default. To enable:

```bash
RUN_E2E=1 poetry run pytest -m e2e
```
