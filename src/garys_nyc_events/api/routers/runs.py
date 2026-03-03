from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ...config import PipelineConfig
from ...runner_once import run_once
from ..auth import require_api_token, require_api_token_for_mutation
from ..dependencies import get_config, get_store
from ..schemas import RunOut, TriggerRunOut


router = APIRouter()


@router.get("", dependencies=[Depends(require_api_token)])
def list_runs(store=Depends(get_store)):
    latest = store.fetch_latest_run()
    if latest is None:
        return []
    return [
        {
            "run_id": latest["id"],
            "status": latest["status"],
            "source": latest["source"],
            "attempts": latest["attempts"],
            "fetched_count": latest["fetched_count"],
            "error": latest["error"],
        }
    ]


@router.post("/trigger", response_model=TriggerRunOut, dependencies=[Depends(require_api_token_for_mutation)])
def trigger_run(config: PipelineConfig = Depends(get_config), store=Depends(get_store)):
    summary = run_once(
        config=PipelineConfig(
            **{
                **config.__dict__,
                "db_path": config.db_path,
            }
        ),
        store=store,
    )
    return TriggerRunOut(
        message="Run triggered",
        run=RunOut(
            run_id=summary.run_id,
            status=summary.status,
            source=summary.source,
            attempts=summary.attempts,
            fetched_count=summary.fetched_count,
            error=summary.error,
        ),
    )
