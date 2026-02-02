-- Add emotions column to sentiment_result (Phase 2: emotion tags).
-- Run against the analytics DB.
ALTER TABLE sentiment_result
ADD COLUMN IF NOT EXISTS emotions JSONB;
