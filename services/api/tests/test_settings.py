from app.config.settings import Settings


def test_b2_endpoint_url_is_derived_from_region():
    settings = Settings(b2_region="test-region-001")

    assert settings.b2_endpoint_url == "https://s3.test-region-001.backblazeb2.com"

