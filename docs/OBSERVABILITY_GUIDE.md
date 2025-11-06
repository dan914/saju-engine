# Observability & Tracing Guide

**Created:** 2025-11-06
**Version:** 1.0
**Related:** Week 4 Task 7 - Integrate OpenTelemetry/structured logging

## Overview

The saju-engine project includes comprehensive observability infrastructure through:

1. **Structured Logging** - JSON-formatted logs with correlation IDs
2. **OpenTelemetry Tracing** - Distributed tracing across microservices
3. **Request Timing** - Automatic HTTP request/response timing
4. **Correlation IDs** - Request tracking across service boundaries

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Correlation  │→ │   Request    │→ │ OpenTelemetry│ │
│  │      ID      │  │   Logging    │  │   Tracing    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         ↓
         ┌───────────────┴───────────────┐
         ↓                               ↓
┌─────────────────┐           ┌─────────────────┐
│ analysis-service│           │ pillars-service │
│  + middleware   │           │  + middleware   │
│  + tracing      │           │  + tracing      │
└─────────────────┘           └─────────────────┘
         ↓                               ↓
    ┌────────────────────────────────────┐
    │   OpenTelemetry Collector          │
    │   ┌──────┐  ┌────────┐  ┌────────┐│
    │   │Jaeger│  │ Zipkin │  │Grafana ││
    │   └──────┘  └────────┘  └────────┘│
    └────────────────────────────────────┘
```

## Quick Start

### 1. Enable Tracing

**Via Environment Variables:**
```bash
export SAJU_ENABLE_TRACING=true
export SAJU_SERVICE_NAME=analysis-service
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

**Via Settings:**
```python
from saju_common import settings

settings.enable_tracing = True
settings.service_name = "analysis-service"
```

### 2. Initialize in Application Startup

```python
from fastapi import FastAPI
from saju_common import create_service_app, setup_tracing

# Create FastAPI app with middleware
app = create_service_app(
    app_name="analysis-service",
    version="1.0.0",
    rule_id="v1"
)

# Initialize OpenTelemetry tracing
@app.on_event("startup")
async def startup_event():
    setup_tracing(
        service_name="analysis-service",
        endpoint="http://localhost:4317"  # Optional: OTLP collector
    )
```

### 3. Use in Your Code

**Automatic Function Tracing:**
```python
from saju_common import trace_function

@trace_function("calculate_strength")
def evaluate_strength(pillars: dict) -> dict:
    """Evaluate pillar strength."""
    # Your code here
    return {"score": 75, "level": "신약"}
```

**Manual Span Creation:**
```python
from saju_common import trace_span, add_span_attribute

def analyze_pillars(pillars: dict) -> dict:
    with trace_span("pillar_analysis") as span:
        # Add custom attributes
        add_span_attribute("pillars.count", 4)
        add_span_attribute("user.timezone", "Asia/Seoul")

        # Your analysis code
        result = perform_analysis(pillars)

        # Add result attributes
        add_span_attribute("result.score", result["score"])

        return result
```

## Structured Logging

### Configuration

**Development (Human-readable):**
```python
from saju_common import configure_logging

configure_logging(json_format=False)
```

**Production (JSON for aggregation):**
```python
from saju_common import configure_logging

configure_logging(json_format=True)
```

### Log Format

**Development Output:**
```
2025-11-06 10:30:45,123 - saju_common.middleware - INFO - POST /analysis/evaluate
2025-11-06 10:30:45,456 - saju_common.middleware - INFO - POST /analysis/evaluate - 200 (333.12ms)
```

**Production Output (JSON):**
```json
{
  "timestamp": "2025-11-06 10:30:45,123",
  "level": "INFO",
  "logger": "saju_common.middleware",
  "message": "POST /analysis/evaluate",
  "event": "request_start",
  "method": "POST",
  "path": "/analysis/evaluate",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "client_host": "192.168.1.100"
}
```

## OpenTelemetry Tracing

### Setup OpenTelemetry Collector

**Docker Compose (Jaeger):**
```yaml
version: '3'
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true
```

**Start Collector:**
```bash
docker-compose up -d jaeger
```

**Access UI:**
```
http://localhost:16686
```

### Trace Decorators

**Basic Usage:**
```python
from saju_common import trace_function

@trace_function()  # Uses function name as span name
def calculate_pillars(birth_dt: datetime) -> dict:
    return {"year": "庚辰", "month": "乙酉"}
```

**Custom Span Name:**
```python
@trace_function("pillar_calculation")
def calculate_pillars(birth_dt: datetime) -> dict:
    return {"year": "庚辰", "month": "乙酉"}
```

**With Attribute Extraction:**
```python
def extract_user_info(args, kwargs):
    return {
        "user.id": kwargs.get("user_id"),
        "user.timezone": kwargs.get("timezone", "UTC")
    }

@trace_function("user_analysis", attributes=extract_user_info)
def analyze_user_chart(birth_dt: datetime, user_id: str, timezone: str = "UTC"):
    # Span automatically includes user.id and user.timezone attributes
    pass
```

**Async Functions:**
```python
@trace_function("async_analysis")
async def async_analyze(data: dict) -> dict:
    # Works with async functions automatically
    result = await process_data(data)
    return result
```

### Manual Instrumentation

**Context Manager:**
```python
from saju_common import trace_span, add_span_attribute, add_span_event

def complex_operation(data: dict) -> dict:
    with trace_span("complex_op", attributes={"data.size": len(data)}):
        # Phase 1
        add_span_event("validation_start")
        validated = validate(data)
        add_span_event("validation_complete", {"valid": validated})

        # Phase 2
        with trace_span("processing"):
            processed = process(validated)
            add_span_attribute("process.duration_ms", 123)

        return processed
```

**Exception Recording:**
```python
from saju_common import trace_span, record_exception

def risky_operation():
    with trace_span("risky_op"):
        try:
            result = dangerous_function()
        except ValueError as e:
            record_exception(e)  # Recorded in span
            raise  # Re-raise for normal error handling
```

## Correlation IDs

### Automatic Injection

Correlation IDs are automatically injected by `CorrelationIDMiddleware`:

**Request Headers (Optional):**
```http
POST /analysis/evaluate HTTP/1.1
X-Correlation-ID: custom-id-12345
```

**Response Headers (Always):**
```http
HTTP/1.1 200 OK
X-Correlation-ID: custom-id-12345
X-Response-Time: 245.67ms
```

### Access in Handlers

```python
from fastapi import Request

@app.post("/analyze")
async def analyze(request: Request, data: dict):
    # Access correlation ID from request state
    correlation_id = request.state.correlation_id

    # Use in logging
    logger.info(f"Processing analysis", extra={"correlation_id": correlation_id})

    return result
```

## Best Practices

### 1. Span Naming

**Good:**
- `calculate_pillars` - Action-based, concise
- `evaluate_strength` - Clear operation name
- `load_policy_file` - Specific function

**Bad:**
- `function_123` - Non-descriptive
- `do_something` - Too vague
- `calculate_pillars_for_user_with_timezone_adjustment` - Too verbose

### 2. Attribute Selection

**Essential Attributes:**
```python
add_span_attribute("user.id", user_id)
add_span_attribute("operation.type", "analysis")
add_span_attribute("result.success", True)
```

**Avoid:**
```python
# Don't log sensitive data
add_span_attribute("user.password", password)  # ❌

# Don't log large objects
add_span_attribute("full.response", huge_dict)  # ❌
```

### 3. Span Hierarchy

**Good Structure:**
```
POST /analysis/evaluate                  (HTTP span - auto)
  ├─ calculate_pillars                   (business logic)
  │   ├─ load_sixty_jiazi                (helper)
  │   └─ compute_daymaster               (helper)
  ├─ evaluate_strength                   (business logic)
  │   ├─ load_strength_policy            (I/O)
  │   └─ calculate_month_state           (compute)
  └─ format_response                     (serialization)
```

### 4. Performance Considerations

**Trace Selectively:**
```python
# ✅ Trace high-level operations
@trace_function()
def analyze_full_chart(pillars: dict) -> dict:
    pass

# ❌ Don't trace tiny helpers
def add(a: int, b: int) -> int:  # No @trace_function
    return a + b
```

**Sampling:**
```bash
# Trace 10% of requests (production)
export OTEL_TRACES_SAMPLER=parentbased_traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.1
```

## Monitoring & Dashboards

### Key Metrics to Track

1. **Request Rate:** Requests per second by endpoint
2. **Latency:** P50, P95, P99 response times
3. **Error Rate:** % of requests returning 5xx
4. **Span Duration:** Time spent in each operation
5. **Dependency Calls:** Calls to external services

### Jaeger Queries

**Find Slow Requests:**
```
service=analysis-service
AND operation=POST /analysis/evaluate
AND duration>1s
```

**Find Errors:**
```
service=analysis-service
AND error=true
```

**Trace Specific User:**
```
service=analysis-service
AND tags:user.id=user123
```

## Troubleshooting

### Tracing Not Working

**Check Settings:**
```python
from saju_common import settings

print(f"Tracing enabled: {settings.enable_tracing}")
print(f"Service name: {settings.service_name}")
```

**Check OpenTelemetry Installation:**
```bash
pip install opentelemetry-api opentelemetry-sdk \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-exporter-otlp
```

**Check Collector Connection:**
```bash
# Test OTLP endpoint
curl http://localhost:4317
```

### Missing Spans

**Verify Decorator:**
```python
# ✅ Correct
@trace_function()
def my_function():
    pass

# ❌ Missing parentheses
@trace_function
def my_function():
    pass
```

**Check Async Handling:**
```python
# ✅ Works automatically
@trace_function()
async def async_func():
    pass

# Call with await
result = await async_func()
```

### High Cardinality Attributes

**Problem:**
```python
# ❌ Creates millions of unique values
add_span_attribute("user.email", user_email)
add_span_attribute("timestamp.exact", datetime.now().isoformat())
```

**Solution:**
```python
# ✅ Use bounded values
add_span_attribute("user.id_hash", hash(user_id) % 1000)
add_span_attribute("hour_of_day", datetime.now().hour)
```

## Testing

### Unit Tests

```python
from saju_common import trace_function, trace_span

def test_tracing_disabled():
    """Test that code works when tracing is disabled."""

    @trace_function()
    def my_func():
        return 42

    # Should work normally even without tracing
    assert my_func() == 42

def test_tracing_with_exception():
    """Test exception propagation with tracing."""

    @trace_function()
    def failing_func():
        raise ValueError("error")

    with pytest.raises(ValueError):
        failing_func()
```

### Integration Tests

```python
def test_full_request_tracing():
    """Test end-to-end request with tracing."""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/analyze", json={"pillars": {...}})

    # Verify correlation ID in response
    assert "X-Correlation-ID" in response.headers
    assert response.status_code == 200
```

## Environment Variables

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SAJU_ENABLE_TRACING` | `false` | Enable OpenTelemetry tracing |
| `SAJU_SERVICE_NAME` | `None` | Service name for traces |
| `SAJU_LOG_LEVEL` | `INFO` | Logging level |
| `SAJU_LOG_FORMAT` | (standard) | Log message format |

### OpenTelemetry Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP collector endpoint |
| `OTEL_TRACES_SAMPLER` | `always_on` | Trace sampling strategy |
| `OTEL_TRACES_SAMPLER_ARG` | - | Sampler argument (e.g., 0.1 for 10%) |
| `OTEL_RESOURCE_ATTRIBUTES` | - | Additional resource attributes |

## Production Deployment

### Recommended Configuration

```bash
# Production environment
export SAJU_ENABLE_TRACING=true
export SAJU_SERVICE_NAME=analysis-service
export SAJU_LOG_LEVEL=INFO

# OpenTelemetry collector
export OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

# Sampling (10% of traces)
export OTEL_TRACES_SAMPLER=parentbased_traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.1

# JSON logging for aggregation
export SAJU_JSON_LOGGING=true
```

### Docker Compose Example

```yaml
version: '3'
services:
  analysis-service:
    image: saju-analysis:latest
    environment:
      - SAJU_ENABLE_TRACING=true
      - SAJU_SERVICE_NAME=analysis-service
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
    depends_on:
      - otel-collector

  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
```

## Further Reading

- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Distributed Tracing Best Practices](https://opentelemetry.io/docs/concepts/signals/traces/)
- [FastAPI Middleware Guide](https://fastapi.tiangolo.com/advanced/middleware/)

---

**Version:** 1.0
**Last Updated:** 2025-11-06
**Maintainer:** Backend Infrastructure Team
