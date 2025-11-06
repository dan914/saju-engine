# Proxy-Aware Client Identity

## Configuration

- `SAJU_FORWARDED_FOR_HEADERS` (list): ordered headers inspected to derive the
  real client IP. Default is `X-Forwarded-For`.
- `SAJU_TRUSTED_PROXY_CIDRS` (list): CIDR ranges considered trusted; any IP in
  these ranges is treated as a proxy hop and skipped when choosing the client
  address.

Example `.env` snippet:

```
SAJU_FORWARDED_FOR_HEADERS=X-Forwarded-For,X-Real-IP
SAJU_TRUSTED_PROXY_CIDRS=10.0.0.0/8,192.168.0.0/16,172.16.0.0/12
```

## Middleware Behaviour

- `RequestLoggingMiddleware` now resolves the client IP using the configuration
  above before logging `client_host`.
- If every IP in the header chain is trusted, the middleware falls back to the
  socket-level `request.client.host`.
- Headers are evaluated left-to-right, returning the first untrusted entry.

## Coordination Notes

1. Confirm with the gateway/ingress team which headers are injected and in what
   order.
2. Populate the trusted CIDR list with known proxy ranges (AWS ALB, Cloudflare,
   etc.).
3. Validate in staging by sending requests with controlled `X-Forwarded-For`
   sequences and confirming log output (see `services/common/tests/test_middleware_logging.py`).
4. Document any additional proprietary headers in this file to keep the contract
   aligned.
