# Seed test data (30 days)

Add 30 days of sample journal entries plus sentiment/themes so **Dashboard**, **Summary**, and **Insights** show varied data. Use weekly or monthly summary in the app.

## 1. Get your user ID

- **Option A:** Sign up or log in in the app, open DevTools → Network, find the login/signup response and copy `userId`.
- **Option B:** After logging in, decode your JWT at [jwt.io](https://jwt.io) and copy the `sub` value.

## 2. Replace the user UUID

In both SQL files, replace the placeholder user ID `ec84d9bc-045b-4adc-b193-8e4f199c6a61` with your UUID (same value in both files).

- `scripts/seed-journal.sql`
- `scripts/seed-analytics.sql`

## 3. Run the scripts

From the repo root, with Postgres and Postgres Analytics running (e.g. `docker-compose up -d postgres postgres_analytics`):

**Journal DB (port 5432):**

```bash
psql -h localhost -p 5432 -U journal -d journal_db -f scripts/seed-journal.sql
# Password: journal_secret
```

**Analytics DB (port 5433):**

```bash
psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/seed-analytics.sql
# Password: analytics_secret
```

## 4. Check the app

- **History:** 30 entries spread over the last 30 days (relative to today).
- **Dashboard:** Sentiment over time and theme tags (varied over the month).
- **Summary:** “Generate weekly summary” or date ranges for weekly/monthly reflection.

---

The seed scripts use **relative dates** (`CURRENT_DATE - N`), so data always falls in the last 30 days and Dashboard/Summary show it without extra steps.

## 45-day seed (varied prompts and nudges)

For a richer dataset (e.g. 7/30/90-day Dashboard filters and reflection summaries), use the 45-day scripts. They add **45 days** of varied content: work stress, morning walks, creative ideas, family, sleep, gratitude, exercise, deadlines, and sample nudges/follow-up style entries.

**Important:** Use the **same user UUID as your logged-in account** (JWT `sub` or login response). If you use a different UUID, History and Streak will show only your account’s data, not the seeded 45 entries.

**Steps:**

1. Get your user ID (same as above — must match the account you use in the app).
2. In both 45-day SQL files, replace the placeholder UUID (e.g. `ea4b5be7-1d22-46f0-97cf-86025ec07056`) with your UUID:
   - `scripts/seed-journal-45.sql`
   - `scripts/seed-analytics-45.sql`
3. Run analytics migrations first if needed: `analytics-add-emotions.sql`, `analytics-add-entry-created-at.sql`.
4. Run the scripts:

**Journal DB:**
```bash
psql -h localhost -p 5432 -U journal -d journal_db -f scripts/seed-journal-45.sql
```

**Analytics DB:**
```bash
psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/seed-analytics-45.sql
```

After seeding, **History** will show 45 entries, **Dashboard** (7/30/90 days) and **Summary** (daily/weekly/monthly) will have varied sentiment, themes, emotions, and moods to explore.

**Why does History only show up to a certain date (e.g. 17 Jan)?**  
The script uses PostgreSQL’s `CURRENT_DATE`, which is the date **on the day you run the script**, not “today” when you open the app. If you ran the seed on 18 Jan, the last entry is 17 Jan. To move the range up to “yesterday” again, re-run both 45-day scripts (journal then analytics). The `ON CONFLICT DO UPDATE` logic will overwrite the same 45 rows with new dates. Then refresh the app.

## If you used older seed scripts (fixed January dates)

Dashboard and weekly summary only look at **the last 30 days** and **the last 7 days** from **today**. The seed data uses fixed dates (e.g. January 2025), so if “today” is later, run the date-fix scripts above to move rows into the last 30 days.

Run the date-fix scripts to move existing rows into the last 30 days:

**Journal DB:** `psql -h localhost -p 5432 -U journal -d journal_db -f scripts/fix-seed-dates-journal.sql`  
**Analytics DB:** `psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/fix-seed-dates-analytics.sql`

## Re-seed from scratch (delete then seed)

To remove all seed data for the seed user and re-run the seed scripts, use the same user UUID in the delete scripts as in your seed files, then run:

**Journal DB (delete then seed):**
```bash
psql -h localhost -p 5432 -U journal -d journal_db -f scripts/delete-seed-user-journal.sql
psql -h localhost -p 5432 -U journal -d journal_db -f scripts/seed-journal.sql
```

**Analytics DB (delete then seed):**
```bash
psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/delete-seed-user-analytics.sql
psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/seed-analytics.sql
```

## Analytics DB migrations (Phase 2)

If you add or upgrade the AI/analytics stack (emotion tags, one-line reflection, time-of-day), run the migration scripts against the analytics DB:

```bash
psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/migrations/analytics-add-emotions.sql
psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/migrations/analytics-add-entry-reflection.sql
psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/migrations/analytics-add-entry-created-at.sql
```
