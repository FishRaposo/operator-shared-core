import sys
from unittest.mock import MagicMock


def test_create_celery_app_bootstrap():
    # Mock celery module dependencies
    mock_celery = MagicMock()
    mock_celery_class = MagicMock()
    mock_celery.Celery = mock_celery_class

    # Inject into sys.modules to test loading safely
    sys.modules["celery"] = mock_celery
    sys.modules["celery.signals"] = MagicMock()

    from shared_core.tasks import create_celery_app

    app = create_celery_app("test-service")
    assert app is not None
    assert mock_celery_class.called
    mock_celery_class.assert_called_with(
        "test-service",
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0",
    )

    # Clean up mocked sys.modules
    del sys.modules["celery"]
    del sys.modules["celery.signals"]
