-- Migration 006: Additional performance indexes
-- Description: Supporting indexes for common query patterns
-- Version: 1.0.0
-- Date: 2025-11-08

-- Token ledger query optimization for admin audit queries
CREATE INDEX idx_token_ledger_user_type ON token_ledger(user_id, transaction_type, created_at DESC);

-- Ad rewards fraud detection queries (IP-based analysis)
CREATE INDEX idx_ad_rewards_user_ip ON ad_rewards(user_id, user_ip, created_at DESC);

-- Entitlements queries for dashboard/analytics
CREATE INDEX idx_entitlements_plan_tier ON entitlements(user_id)
  INCLUDE (plan_tokens_available, earned_tokens_available, bonus_tokens_available);

COMMENT ON INDEX idx_token_ledger_user_type IS 'Optimizes admin audit queries filtered by transaction type';
COMMENT ON INDEX idx_ad_rewards_user_ip IS 'Supports fraud detection IP hopping analysis';
COMMENT ON INDEX idx_entitlements_plan_tier IS 'Covering index for dashboard queries (reduces table lookups)';
