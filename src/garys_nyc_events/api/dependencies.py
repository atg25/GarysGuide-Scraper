from __future__ import annotations

from functools import lru_cache

from ..config import PipelineConfig, load_config_from_env
from ..storage import SQLiteEventStore


@lru_cache(maxsize=1)
def get_config() -> PipelineConfig:
    return load_config_from_env()


def get_store() -> SQLiteEventStore:
    cfg = get_config()
    store = SQLiteEventStore(cfg.db_path)
    store.init_schema()
    return store
