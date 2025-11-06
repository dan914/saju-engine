"""Common utilities and infrastructure for 사주 앱 v1.4 services.

This package provides:
- RFC7807 error handling with correlation IDs
- Request logging and timing middleware
- Application factory for standardized FastAPI apps
- Domain-specific exceptions
- Policy file loading utilities
- Shared interfaces and implementations (Protocols)
- Mapping tables and utilities

Example:
    >>> from saju_common import create_service_app, ValidationError
    >>> app = create_service_app(
    ...     app_name="my-service",
    ...     version="1.0.0",
    ...     rule_id="v1"
    ... )
    >>>
    >>> # Use domain-specific utilities
    >>> from saju_common import BasicTimeResolver, BRANCH_TO_SEASON
    >>> time_resolver = BasicTimeResolver()
    >>> season = BRANCH_TO_SEASON["寅"]  # "spring"
"""

# Application factory
from .app_factory import create_service_app

# Dependency injection
from .container import Container, get_default_container, reset_default_container

# Exceptions (RFC7807)
from .exceptions import (
    SajuBaseException,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    InternalError,
    ServiceUnavailableError,
    DependencyError,
    PolicyLoadError,
    CalculationError,
    LLMGuardError,
    TokenQuotaError,
)

# Middleware
from .middleware import (
    CorrelationIDMiddleware,
    RequestLoggingMiddleware,
    configure_logging,
    add_middleware,
)

# Handlers
from .handlers import register_exception_handlers

# Settings (centralized configuration)
from .settings import SajuSettings, get_repo_root, settings

# Observability (OpenTelemetry tracing)
from .tracing import (
    setup_tracing,
    get_tracer,
    trace_span,
    trace_function,
    add_span_attribute,
    add_span_event,
    record_exception,
)

# Rate limiting
from .rate_limit import (
    RateLimitMiddleware,
    TokenBucketRateLimiter,
    RateLimitExceeded,
    setup_rate_limiting,
    DEFAULT_RATE_LIMITS,
)

# Legacy utilities (preserved for backward compatibility)
from .policy_loader import resolve_policy_path
from .trace import TraceMetadata

# Protocols
# Built-in implementations
from .builtins import (
    BasicTimeResolver,
    SimpleDeltaT,
    TableSolarTermLoader,
    get_default_delta_t_policy,
    get_default_solar_term_loader,
    get_default_time_resolver,
)

# File-based implementations
from .file_solar_term_loader import FileSolarTermLoader, SolarTermEntry
from .interfaces import DeltaTPolicy, SolarTermLoader, TimeResolver

# Mapping tables
from .seasons import (
    BRANCH_TO_ELEMENT,
    BRANCH_TO_SEASON,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATES,
    GREGORIAN_MONTH_TO_BRANCH,
    SEASON_ELEMENT_BOOST,
    STEM_TO_ELEMENT,
)

# Timezone handling
from .timezone_handler import (
    CITY_LMT_OFFSETS,
    DST_PERIODS,
    MODERN_LMT_OFFSETS,
    KoreanTimezoneHandler,
    TimezoneWarning,
    get_saju_adjusted_time,
)

__all__ = [
    # Version
    "__version__",
    # Application factory
    "create_service_app",
    # Settings
    "SajuSettings",
    "get_repo_root",
    "settings",
    # Dependency injection
    "Container",
    "get_default_container",
    "reset_default_container",
    # Exceptions (4xx)
    "ValidationError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    # Exceptions (5xx)
    "InternalError",
    "ServiceUnavailableError",
    "DependencyError",
    # Domain exceptions
    "PolicyLoadError",
    "CalculationError",
    "LLMGuardError",
    "TokenQuotaError",
    # Base exception
    "SajuBaseException",
    # Middleware
    "CorrelationIDMiddleware",
    "RequestLoggingMiddleware",
    "configure_logging",
    "add_middleware",
    # Handlers
    "register_exception_handlers",
    # Observability (OpenTelemetry)
    "setup_tracing",
    "get_tracer",
    "trace_span",
    "trace_function",
    "add_span_attribute",
    "add_span_event",
    "record_exception",
    # Rate limiting
    "RateLimitMiddleware",
    "TokenBucketRateLimiter",
    "RateLimitExceeded",
    "setup_rate_limiting",
    "DEFAULT_RATE_LIMITS",
    # Legacy
    "TraceMetadata",
    "resolve_policy_path",
    # Protocols
    "TimeResolver",
    "SolarTermLoader",
    "DeltaTPolicy",
    # Implementations
    "BasicTimeResolver",
    "TableSolarTermLoader",
    "SimpleDeltaT",
    # File-based loaders
    "FileSolarTermLoader",
    "SolarTermEntry",
    # Factories
    "get_default_time_resolver",
    "get_default_solar_term_loader",
    "get_default_delta_t_policy",
    # Tables
    "GREGORIAN_MONTH_TO_BRANCH",
    "BRANCH_TO_SEASON",
    "BRANCH_TO_ELEMENT",
    "STEM_TO_ELEMENT",
    "SEASON_ELEMENT_BOOST",
    "ELEMENT_GENERATES",
    "ELEMENT_CONTROLS",
    # Timezone handling
    "KoreanTimezoneHandler",
    "get_saju_adjusted_time",
    "DST_PERIODS",
    "CITY_LMT_OFFSETS",
    "MODERN_LMT_OFFSETS",
    "TimezoneWarning",
]

__version__ = "1.4.0"
