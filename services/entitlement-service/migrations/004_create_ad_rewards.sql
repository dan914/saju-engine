-- Migration 004: Create ad_rewards table
-- Description: Google AdMob Server-Side Verification (SSV) tracking
-- Version: 1.0.0
-- Date: 2025-11-08

CREATE TABLE ad_rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Ad network details
    ad_network VARCHAR(50) NOT NULL,          -- 'admob' (can extend to 'unity', 'applovin')
    ad_unit_id VARCHAR(100) NOT NULL,
    reward_amount INT NOT NULL DEFAULT 2,

    -- Google AdMob SSV signature verification
    ssv_signature TEXT NOT NULL,
    ssv_key_id BIGINT NOT NULL,
    ssv_verified BOOLEAN NOT NULL DEFAULT FALSE,
    ssv_verified_at TIMESTAMPTZ,

    -- User context (for fraud detection)
    user_ip INET NOT NULL,
    user_agent TEXT NOT NULL,
    device_id VARCHAR(255),

    -- Status workflow
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending'|'verified'|'rejected'|'expired'
    rejection_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,

    -- SSV deduplication (prevents duplicate AdMob callbacks)
    ssv_request_hash VARCHAR(64) UNIQUE,      -- SHA-256 of canonical SSV query

    CONSTRAINT valid_status CHECK (status IN ('pending','verified','rejected','expired')),
    CONSTRAINT valid_reward_amount CHECK (reward_amount > 0 AND reward_amount <= 10)
);

CREATE INDEX idx_ad_rewards_user_id ON ad_rewards(user_id, created_at DESC);
CREATE INDEX idx_ad_rewards_status ON ad_rewards(status, created_at);
CREATE INDEX idx_ad_rewards_expires_at ON ad_rewards(expires_at) WHERE status = 'pending';

COMMENT ON TABLE ad_rewards IS 'Google AdMob Server-Side Verification (SSV) tracking with fraud detection';
COMMENT ON COLUMN ad_rewards.ssv_signature IS 'ECDSA signature from Google AdMob (base64-encoded)';
COMMENT ON COLUMN ad_rewards.ssv_request_hash IS 'SHA-256 hash of canonical SSV query (prevents duplicate callbacks)';
COMMENT ON COLUMN ad_rewards.expires_at IS 'Pending rewards expire after 5 minutes';
