-- Migration 003: Create token_ledger table
-- Description: Immutable audit trail for all token transactions
-- Version: 1.0.0
-- Date: 2025-11-08

CREATE TABLE token_ledger (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    transaction_type VARCHAR(50) NOT NULL,  -- 'consume'|'reward'|'refund'|'grant'|'reset'
    token_delta INT NOT NULL,               -- + for add, - for consume
    tokens_before INT NOT NULL,
    tokens_after INT NOT NULL,

    reason VARCHAR(255) NOT NULL,
    related_entity_type VARCHAR(50),        -- 'chat'|'report'|'ad'|'tx'
    related_entity_id VARCHAR(100),         -- business entity ID (chat msg, report, etc.)

    idempotency_key UUID,                   -- optional UUID for idempotent operations
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,

    CONSTRAINT valid_transaction_type CHECK (transaction_type IN ('consume','reward','refund','grant','reset')),
    CONSTRAINT valid_tokens_delta CHECK (
        (transaction_type = 'consume' AND token_delta < 0) OR
        (transaction_type IN ('reward','refund','grant','reset') AND token_delta > 0)
    )
);

-- Idempotency: Prevent duplicate transactions via Idempotency-Key header
CREATE UNIQUE INDEX uq_token_ledger_idem ON token_ledger(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Business-entity uniqueness: Prevent double-deduction of same entity (chat message, report, etc.)
-- This is CRITICAL: even if client uses different Idempotency-Key, same entity can only be charged once
CREATE UNIQUE INDEX uq_consume_once
  ON token_ledger (user_id, related_entity_type, related_entity_id)
  WHERE transaction_type='consume' AND related_entity_id IS NOT NULL;

CREATE INDEX idx_token_ledger_user_id ON token_ledger(user_id, created_at DESC);
CREATE INDEX idx_token_ledger_created_at ON token_ledger(created_at DESC);
CREATE INDEX idx_token_ledger_type ON token_ledger(transaction_type, created_at DESC);

COMMENT ON TABLE token_ledger IS 'Immutable audit trail for all token transactions';
COMMENT ON COLUMN token_ledger.token_delta IS 'Positive for additions (reward/refund/grant), negative for consumption';
COMMENT ON COLUMN token_ledger.related_entity_id IS 'Business entity ID that triggered transaction (e.g., chat_message_id, report_id)';
COMMENT ON INDEX uq_consume_once IS 'CRITICAL: Prevents double-deduction even with different Idempotency-Key headers';
