-- Add entry_created_at to sentiment_result and theme_result (Phase 2: time-of-day filter).
-- Run against the analytics DB.
ALTER TABLE sentiment_result
ADD COLUMN IF NOT EXISTS entry_created_at TIMESTAMP;

ALTER TABLE theme_result
ADD COLUMN IF NOT EXISTS entry_created_at TIMESTAMP;
