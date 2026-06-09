from shared_core.errors import (
    ConflictError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)


def test_errors_extensions():
    # Test NotFoundError
    not_found = NotFoundError("Resource not found")
    assert not_found.status_code == 404
    assert not_found.code == "NOT_FOUND"
    assert not_found.message == "Resource not found"

    # Test ConflictError
    conflict = ConflictError("State conflict")
    assert conflict.status_code == 409
    assert conflict.code == "CONFLICT"

    # Test UnauthorizedError
    unauthorized = UnauthorizedError("Missing auth")
    assert unauthorized.status_code == 401
    assert unauthorized.code == "UNAUTHORIZED"

    # Test ForbiddenError
    forbidden = ForbiddenError("Access forbidden")
    assert forbidden.status_code == 403
    assert forbidden.code == "FORBIDDEN"

    # Test ExternalServiceError
    external = ExternalServiceError("Integration timeout")
    assert external.status_code == 502
    assert external.code == "EXTERNAL_SERVICE_ERROR"
