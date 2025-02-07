import json
from fastapi import Request
from typing import Dict, Any
import logging
from utilities.logging_utils import configure_logger

logger = configure_logger('fastapi_utils_logger', logging.INFO)

async def log_request(request: Request) -> None:
    """
    Logs FastAPI request details in JSON format

    Args:
        request (Request): FastAPI request object to log

    Returns:
        None: Prints formatted JSON to console
    """
    request_data: Dict[str, Any] = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "client": {
            "host": request.client.host if request.client else None,
            "port": request.client.port if request.client else None
        },
        "body": (await request.body()).decode("utf-8", "replace")
    }

    logger.info("%s", json.dumps(request_data, indent=2, default=str))
