from shared_core.config import BaseAppConfig


def test_config_defaults():
    config = BaseAppConfig()
    assert config.ENV == "development"
    assert config.DEBUG is True
    assert "postgresql" in config.DATABASE_URL
    assert "redis" in config.REDIS_URL


def test_config_env_overrides(monkeypatch):
    monkeypatch.setenv("APP_NAME", "override-test")
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    config = BaseAppConfig()
    assert config.APP_NAME == "override-test"
    assert config.ENV == "production"
    assert config.DEBUG is False
    assert config.DATABASE_URL == "sqlite:///:memory:"
