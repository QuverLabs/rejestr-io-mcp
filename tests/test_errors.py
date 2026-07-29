"""Tests for the domain exception hierarchy."""
import pytest

from rejestr_io_mcp.errors import (
    ApiError,
    AuthError,
    NotFoundError,
    PlanRequiredError,
    RateLimitError,
    RejestrIoError,
)


@pytest.mark.parametrize(
    "exc_class", [AuthError, PlanRequiredError, NotFoundError, RateLimitError, ApiError]
)
def test_all_domain_errors_subclass_rejestr_io_error(exc_class):
    assert issubclass(exc_class, RejestrIoError)
    assert issubclass(exc_class, Exception)


def test_error_message_is_preserved():
    assert str(AuthError("invalid key")) == "invalid key"
