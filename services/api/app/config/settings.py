from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings

from app.config.b2_contract import (
    LEGACY_B2_KEY_ID_ENV,
    PRIMARY_B2_KEY_ID_ENV,
    b2_endpoint_url_from_region,
)


class Settings(BaseSettings):
    b2_region: str = ""
    b2_application_key_id: str = Field(
        default="",
        validation_alias=AliasChoices(
            PRIMARY_B2_KEY_ID_ENV,
            LEGACY_B2_KEY_ID_ENV,
        ),
    )
    b2_application_key: str = ""
    b2_bucket_name: str = ""
    b2_public_url_base: str = ""

    api_port: int = 8000
    # Explicit allowlist by default — covers Next on :3000 and the
    # fallback :3001 it picks if 3000 is busy. Production deploys should
    # override with the exact frontend origin.
    api_cors_origins: str = "http://localhost:3000,http://localhost:3001"
    # Optional dev-only escape hatch: a regex that matches additional
    # allowed origins. Empty by default — set this to e.g.
    # `^http://localhost:\d+$` to accept any localhost port without
    # listing each one. NEVER ship this to production.
    api_cors_origin_regex: str = ""

    # Upload limits
    max_file_size: int = 100 * 1024 * 1024  # 100MB

    # Small durable counters (downloads, etc). Point at a persistent
    # volume in production if you care about surviving restarts.
    download_count_file: str = "data/download_count.json"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
    }

    @property
    def b2_endpoint_url(self) -> str:
        return b2_endpoint_url_from_region(self.b2_region)

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",")]


settings = Settings()
