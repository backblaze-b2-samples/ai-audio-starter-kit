import json
import logging
import sys
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

# Single source of truth: repo-root .env. Anchored to this file's path so it
# resolves correctly regardless of where uvicorn is invoked from (local
# `cd services/api && uvicorn`, Docker WORKDIR, etc.).
REPO_ROOT_ENV = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(REPO_ROOT_ENV)

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402

from app.config import settings  # noqa: E402
from app.config.b2_contract import (  # noqa: E402
    B2_PLACEHOLDER_VALUES,
    LEGACY_B2_KEY_ID_ENV,
    PRIMARY_B2_KEY_ID_ENV,
    REQUIRED_B2_ENV_NAMES,
    validate_b2_region,
)
from app.runtime import files, health, library, metrics, upload  # noqa: E402

# --- Startup validation ---
# Required B2 settings are declared with empty-string defaults so that
# `Settings()` instantiation (and therefore `from main import app`) never
# raises during test collection. We instead fail fast at server startup
# with a human-readable message — uvicorn surfaces this as the first log
# line, so misconfiguration is obvious within seconds rather than turning
# into mysterious 500s on the first request.
_ENV_TO_SETTINGS_ATTR = {
    "B2_APPLICATION_KEY_ID": "b2_application_key_id",
    "B2_APPLICATION_KEY": "b2_application_key",
    "B2_BUCKET_NAME": "b2_bucket_name",
    "B2_REGION": "b2_region",
}


def _key_id_env_label() -> str:
    return f"{PRIMARY_B2_KEY_ID_ENV} (or legacy {LEGACY_B2_KEY_ID_ENV})"


def _required_b2_settings() -> tuple[tuple[str, str], ...]:
    return tuple(
        (env_name, _ENV_TO_SETTINGS_ATTR[env_name])
        for env_name in REQUIRED_B2_ENV_NAMES
        if env_name != PRIMARY_B2_KEY_ID_ENV
    )


@asynccontextmanager
async def lifespan(_app: "FastAPI"):
    missing = [
        env_name
        for env_name, attr in _required_b2_settings()
        if not getattr(settings, attr)
    ]
    if not settings.b2_application_key_id:
        missing.insert(0, _key_id_env_label())
    if missing:
        raise RuntimeError(
            "Missing required B2 configuration: "
            + ", ".join(missing)
            + f". Add them to {REPO_ROOT_ENV} (see .env.example) and restart."
        )

    placeholders = [
        env_name
        for env_name, attr in _required_b2_settings()
        if getattr(settings, attr) in B2_PLACEHOLDER_VALUES
    ]
    if settings.b2_application_key_id in B2_PLACEHOLDER_VALUES:
        placeholders.insert(0, _key_id_env_label())
    if placeholders:
        raise RuntimeError(
            "B2 configuration still has placeholder values: "
            + ", ".join(placeholders)
            + f". Edit {REPO_ROOT_ENV} with your real B2 credentials and restart."
        )
    try:
        validate_b2_region(settings.b2_region)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    yield

# --- Structured JSON logging ---

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])
        return json.dumps(log_entry)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO)
# Quiet noisy libraries
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("api")


# --- App setup ---

app = FastAPI(
    title="AI Audio Starter Kit API",
    description="Audio upload, library, and metadata API backed by Backblaze B2",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Optional regex (empty by default). When set, any origin matching
    # the pattern is allowed in addition to the explicit allowlist.
    allow_origin_regex=settings.api_cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Request ID + timing middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=metrics.timing_middleware)

app.include_router(health.router, tags=["health"])
app.include_router(upload.router, tags=["upload"])
app.include_router(library.router, tags=["library"])
app.include_router(files.router, tags=["files"])
app.include_router(metrics.router, tags=["metrics"])
