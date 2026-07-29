"""Domain exceptions for rejestr.io API responses, mapped from HTTP status codes in client.py."""


class RejestrIoError(Exception):
    """Base class for all rejestr.io domain errors."""


class AuthError(RejestrIoError):
    """Raised for 401/403 responses: invalid or missing API key."""


class PlanRequiredError(RejestrIoError):
    """Raised when an endpoint requires a higher rejestr.io plan (402)."""


class NotFoundError(RejestrIoError):
    """Raised for 404 responses."""


class RateLimitError(RejestrIoError):
    """Raised for 429 responses: rate limit exceeded."""


class ApiError(RejestrIoError):
    """Raised for unexpected (5xx or other) API errors."""
