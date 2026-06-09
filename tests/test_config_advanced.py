from shared_core.config import BaseAppConfig


def test_secretstr_fields_not_in_model_dump():
    config = BaseAppConfig(
        OPENAI_API_KEY="sk-test-key-123",
        ANTHROPIC_API_KEY="ant-test-key-456",
        GITHUB_TOKEN="ghp-test-token-789",
    )
    dump = config.model_dump()

    assert "sk-test-key-123" not in str(dump)
    assert "ant-test-key-456" not in str(dump)
    assert "ghp-test-token-789" not in str(dump)


def test_secretstr_get_secret_value():
    config = BaseAppConfig(OPENAI_API_KEY="sk-test-key-123")
    assert config.OPENAI_API_KEY is not None
    assert config.OPENAI_API_KEY.get_secret_value() == "sk-test-key-123"


def test_secretstr_defaults_to_none():
    config = BaseAppConfig()
    assert config.OPENAI_API_KEY is None
    assert config.ANTHROPIC_API_KEY is None
    assert config.GITHUB_TOKEN is None


def test_validate_config_all_valid():
    issues = BaseAppConfig.validate_config()
    assert issues == []


def test_validate_config_missing_db_url():
    issues = BaseAppConfig.validate_config({"DATABASE_URL": ""})
    assert len(issues) == 1
    assert issues[0]["field"] == "DATABASE_URL"
    assert issues[0]["severity"] == "error"


def test_validate_config_bad_log_level():
    issues = BaseAppConfig.validate_config(
        {
            "DATABASE_URL": "postgresql://localhost/db",
            "LOG_LEVEL": "VERBOSE",
        }
    )
    assert any(issue["field"] == "LOG_LEVEL" for issue in issues)


def test_validate_config_temperature_range():
    issues = BaseAppConfig.validate_config(
        {
            "DATABASE_URL": "postgresql://localhost/db",
            "LLM_TEMPERATURE": 3.0,
        }
    )
    assert any(issue["field"] == "LLM_TEMPERATURE" for issue in issues)


def test_pool_params_defaults():
    config = BaseAppConfig()
    assert config.DB_POOL_SIZE == 5
    assert config.DB_MAX_OVERFLOW == 10
    assert config.DB_POOL_TIMEOUT == 30
