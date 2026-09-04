from types import SimpleNamespace

import pytest

import main as api_main
from app.config.b2_contract import B2_USER_AGENT_EXTRA
from app.config.settings import Settings
from app.repo import b2_client

B2_ENV_NAMES = (
    "B2_APPLICATION_KEY_ID",
    "B2_KEY_ID",
    "B2_APPLICATION_KEY",
    "B2_BUCKET_NAME",
    "B2_REGION",
    "B2_PUBLIC_URL_BASE",
    "B2_PUBLIC_URL",
)


def _settings_from_env(monkeypatch, **env: str) -> Settings:
    for key in B2_ENV_NAMES:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return Settings(_env_file=None)


def _startup_settings(**overrides):
    values = {
        "b2_application_key_id": "key-id",
        "b2_application_key": "application-key",
        "b2_bucket_name": "bucket-name",
        "b2_region": "us-west-004",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_b2_endpoint_url_is_derived_from_region():
    settings = Settings(b2_region="test-region-001")

    assert settings.b2_endpoint_url == "https://s3.test-region-001.backblazeb2.com"


@pytest.mark.parametrize(
    "region",
    [
        "attacker.example/#",
        "evil.com/path",
        "us-west-004?x=",
        "us.west.004",
        " us-west-004",
        "us-west-004 ",
    ],
)
def test_b2_endpoint_url_rejects_malformed_region(region):
    settings = Settings(b2_region=region)

    with pytest.raises(ValueError, match="Invalid B2_REGION"):
        _ = settings.b2_endpoint_url


def test_settings_accept_new_key_id_env(monkeypatch):
    settings = _settings_from_env(
        monkeypatch,
        B2_APPLICATION_KEY_ID="new-key-id",
    )

    assert settings.b2_application_key_id == "new-key-id"


def test_settings_accept_legacy_key_id_env(monkeypatch):
    settings = _settings_from_env(
        monkeypatch,
        B2_KEY_ID="legacy-key-id",
    )

    assert settings.b2_application_key_id == "legacy-key-id"


def test_settings_prefer_new_key_id_env(monkeypatch):
    settings = _settings_from_env(
        monkeypatch,
        B2_APPLICATION_KEY_ID="new-key-id",
        B2_KEY_ID="legacy-key-id",
    )

    assert settings.b2_application_key_id == "new-key-id"


def test_settings_accept_new_public_url_base_env(monkeypatch):
    settings = _settings_from_env(
        monkeypatch,
        B2_PUBLIC_URL_BASE="https://cdn.example.com/bucket",
    )

    assert settings.b2_public_url_base == "https://cdn.example.com/bucket"


def test_settings_accept_legacy_public_url_env(monkeypatch):
    settings = _settings_from_env(
        monkeypatch,
        B2_PUBLIC_URL="https://legacy.example.com/bucket",
    )

    assert settings.b2_public_url_base == "https://legacy.example.com/bucket"


def test_settings_prefer_new_public_url_base_env(monkeypatch):
    settings = _settings_from_env(
        monkeypatch,
        B2_PUBLIC_URL_BASE="https://cdn.example.com/bucket",
        B2_PUBLIC_URL="https://legacy.example.com/bucket",
    )

    assert settings.b2_public_url_base == "https://cdn.example.com/bucket"


@pytest.mark.asyncio
async def test_startup_validation_accepts_key_id_setting(monkeypatch):
    monkeypatch.setattr(api_main, "settings", _startup_settings())

    async with api_main.lifespan(None):
        pass


@pytest.mark.asyncio
async def test_startup_validation_rejects_malformed_region(monkeypatch):
    monkeypatch.setattr(
        api_main,
        "settings",
        _startup_settings(b2_region="evil.com/path"),
    )

    with pytest.raises(RuntimeError, match="Invalid B2_REGION"):
        async with api_main.lifespan(None):
            pass


def test_s3_client_sets_standard_user_agent(monkeypatch):
    captured = {}

    def fake_client(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return object()

    b2_client.get_s3_client.cache_clear()
    monkeypatch.setattr(b2_client.boto3, "client", fake_client)

    b2_client.get_s3_client()

    assert captured["kwargs"]["config"].user_agent_extra == B2_USER_AGENT_EXTRA
    b2_client.get_s3_client.cache_clear()
