-- Migration 002: Create entitlements table
-- Description: User quotas and entitlements with three-bucket token system
-- Version: 1.0.0
-- Date: 2025-11-08

CREATE TABLE entitlements (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,

    -- Light chat quotas (daily reset at 00:00 KST)
    light_daily_limit INT NOT NULL,
    light_daily_used INT NOT NULL DEFAULT 0,
    light_last_reset_date DATE NOT NULL,

    -- Deep tokens with three-bucket system
    deep_tokens_limit INT NOT NULL,                 -- plan monthly limit (0/20/100)
    plan_tokens_available INT NOT NULL,             -- plan bucket (resets monthly)
    earned_tokens_available INT NOT NULL DEFAULT 0, -- ad rewards bucket (never resets)
    bonus_tokens_available  INT NOT NULL DEFAULT 0, -- admin grants bucket (optional)
    deep_tokens_last_reset TIMESTAMPTZ,             -- last plan bucket reset

    -- Storage quotas (bytes for precision)
    storage_limit_mb INT NOT NULL,
    storage_used_bytes BIGINT NOT NULL DEFAULT 0,

    -- Saved reports quotas
    saved_reports_limit INT NOT NULL,
    saved_reports_count INT NOT NULL DEFAULT 0,

    -- Ad rewards tracking
    ad_rewards_today INT NOT NULL DEFAULT 0,        -- watched today (KST day)
    ad_rewards_this_month INT NOT NULL DEFAULT 0,   -- watched in subscription month
    last_ad_reward_at TIMESTAMPTZ,

    -- Subscription renewal management
    plan_renewal_anchor TIMESTAMPTZ,                -- KST midnight of original plan start (supports mid-month upgrades)

    -- Metadata
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version INT NOT NULL DEFAULT 1,                 -- optimistic locking version

    -- Constraints
    CONSTRAINT chk_light_usage CHECK (light_daily_used >= 0 AND light_daily_used <= light_daily_limit),
    CONSTRAINT chk_plan_tokens CHECK (plan_tokens_available   >= 0 AND plan_tokens_available   <= deep_tokens_limit),
    CONSTRAINT chk_earned_tokens CHECK (earned_tokens_available >= 0),
    CONSTRAINT chk_bonus_tokens  CHECK (bonus_tokens_available  >= 0),
    CONSTRAINT chk_storage CHECK (storage_used_bytes >= 0),
    CONSTRAINT chk_saved_reports CHECK (saved_reports_count >= 0 AND saved_reports_count <= saved_reports_limit),
    CONSTRAINT chk_ad_rewards_daily CHECK (ad_rewards_today >= 0 AND ad_rewards_today <= 2),
    CONSTRAINT chk_ad_rewards_monthly CHECK (ad_rewards_this_month >= 0 AND ad_rewards_this_month <= 60)
);

CREATE INDEX idx_entitlements_light_reset ON entitlements(light_last_reset_date);
CREATE INDEX idx_entitlements_deep_reset ON entitlements(deep_tokens_last_reset);

COMMENT ON TABLE entitlements IS 'User quotas and entitlements with optimistic locking';
COMMENT ON COLUMN entitlements.plan_tokens_available IS 'Plan bucket: resets monthly to deep_tokens_limit';
COMMENT ON COLUMN entitlements.earned_tokens_available IS 'Earned bucket: ad rewards, never resets (persists across months)';
COMMENT ON COLUMN entitlements.bonus_tokens_available IS 'Bonus bucket: admin grants, never resets';
COMMENT ON COLUMN entitlements.version IS 'Optimistic locking version - incremented on every update';
COMMENT ON COLUMN entitlements.plan_renewal_anchor IS 'Original subscription start date for calculating monthly resets (handles mid-month upgrades)';
