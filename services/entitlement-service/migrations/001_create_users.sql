-- Migration 001: Create users table
-- Description: User accounts with plan tier management
-- Version: 1.0.0
-- Date: 2025-11-08

CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100),

    plan_tier VARCHAR(20) NOT NULL DEFAULT 'free',  -- 'free'|'plus'|'pro'
    plan_start_date TIMESTAMPTZ,
    plan_end_date TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_plan CHECK (plan_tier IN ('free', 'plus', 'pro'))
);

CREATE INDEX idx_users_plan_tier ON users(plan_tier);
CREATE INDEX idx_users_plan_end_date ON users(plan_end_date) WHERE plan_end_date IS NOT NULL;

COMMENT ON TABLE users IS 'User accounts with subscription plan management';
COMMENT ON COLUMN users.plan_tier IS 'Subscription tier: free (3 light/day, 0 deep), plus (10 light/day, 20 deep), pro (unlimited light, 100 deep)';
COMMENT ON COLUMN users.plan_start_date IS 'Start of current subscription period (KST)';
COMMENT ON COLUMN users.plan_end_date IS 'End of current subscription period (KST), NULL for active subscriptions';
