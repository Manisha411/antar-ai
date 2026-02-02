-- Add period_type to reflection_summary for daily/weekly/monthly summaries.
-- Run against analytics_db: psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/migrations/analytics-add-reflection-summary-period-type.sql
ALTER TABLE reflection_summary ADD COLUMN IF NOT EXISTS period_type VARCHAR(20);
