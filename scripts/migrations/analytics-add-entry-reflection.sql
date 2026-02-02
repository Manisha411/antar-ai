-- Add entry_reflection table (Phase 2: one-line reflection per entry).
-- Run against the analytics DB.
CREATE TABLE IF NOT EXISTS entry_reflection (
    entry_id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    reflection TEXT,
    computed_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_entry_reflection_user_id ON entry_reflection (user_id);
