from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ...mcp.server import _handle_request
from ...mcp.tools import query_events
from ..auth import require_api_token


router = APIRouter(dependencies=[Depends(require_api_token)])


@router.post("")
def mcp_request(request: dict[str, Any]):
    return _handle_request(request, handler=query_events, enabled=None)
