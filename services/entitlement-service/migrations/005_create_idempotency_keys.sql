-- Migration 005: Create idempotency_keys table
-- Description: RFC-8785 canonical JSON-based idempotency for API endpoints
-- Version: 1.0.0
-- Date: 2025-11-08

CREATE TABLE idempotency_keys (
    idempotency_key UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    endpoint VARCHAR(100) NOT NULL,         -- '/tokens/consume'|'/tokens/reward/claim'|'/tokens/refund'
    request_hash VARCHAR(64) NOT NULL,      -- RFC-8785 canonical body hash

    response_status INT,
    response_body JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,

    CONSTRAINT valid_endpoint CHECK (endpoint IN ('/tokens/consume','/tokens/reward/claim','/tokens/refund'))
);

CREATE INDEX idx_idempotency_keys_user_id ON idempotency_keys(user_id, created_at DESC);
CREATE INDEX idx_idempotency_keys_expires_at ON idempotency_keys(expires_at);

COMMENT ON TABLE idempotency_keys IS 'RFC-8785 canonical JSON-based idempotency for critical endpoints';
COMMENT ON COLUMN idempotency_keys.request_hash IS 'SHA-256 hash of RFC-8785 canonical JSON request body';
COMMENT ON COLUMN idempotency_keys.expires_at IS 'Idempotency keys expire after 24 hours';
