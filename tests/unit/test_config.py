from src.config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.port == 8000
    assert settings.host == "0.0.0.0"
    assert settings.env.value == "development"
    assert "sqlite" in settings.database_url


def test_app_metadata():
    settings = Settings()
    assert settings.app_name == "LMU Telemetry API"
    assert settings.app_version == "0.1.0"
