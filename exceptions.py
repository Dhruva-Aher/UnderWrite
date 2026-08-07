"""Domain-specific exception hierarchy for Underwrite."""


class UnderwriteError(Exception):
    """Base exception for all Underwrite operations."""


class DataHubError(UnderwriteError):
    """Base exception for metadata graph interactions."""


class NetworkError(DataHubError):
    """Network connection refusal or REST API timeout."""


class AuthenticationError(DataHubError):
    """GMS permission or HTTP 403 Forbidden error."""


class ValidationError(UnderwriteError):
    """Policy definition or governance assertion failure."""


class SchemaError(UnderwriteError):
    """Metadata aspect format or serialization error."""


class PolicyConfigurationError(UnderwriteError):
    """Raised when an explicit policy configuration file is malformed."""
