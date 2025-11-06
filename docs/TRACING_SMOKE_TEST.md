# Tracing Smoke Test Checklist

Follow this procedure when validating OTLP exporter configuration in staging.

## Pre-flight Configuration

- Ensure `SAJU_ENABLE_TRACING=true` for the service under test.
- If no explicit endpoint is supplied in code, set the appropriate environment
  variables:
  - `OTEL_EXPORTER_OTLP_ENDPOINT` (`grpc://collector:4317` or
    `https://collector:4318/v1/traces`).
  - `OTEL_EXPORTER_OTLP_HEADERS` for any required auth tokens (comma-separated
    `key=value`).
  - Optional: `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf` to force HTTP when
    using port 4318.

## Validation Steps

1. Deploy the service to staging with tracing enabled and the desired OTLP
   settings.
2. Generate traffic (smoke request) that exercises the service.
3. Confirm service logs show `OpenTelemetry OTLP GRPC exporter configured` or
   `HTTP exporter` message with the correct endpoint.
4. In the collector UI (or `otelcol` logs), verify spans arriving from the
   service name configured in `SAJU_SERVICE_NAME`.
5. Optionally, add `SAJU_LOG_LEVEL=DEBUG` temporarily to confirm console spans
   only appear when expected.

## Troubleshooting

- If no spans arrive, double-check that the endpoint/headers align with the
  collector’s listener type (4317 for gRPC, 4318 for HTTP).
- For authentication errors, re-run with the `OTEL_EXPORTER_OTLP_HEADERS`
  string logged (ensure secrets are redacted before sharing).
- If FastAPI instrumentation fails, the service log will include
  `Failed to instrument FastAPI`; investigate dependency versions.
