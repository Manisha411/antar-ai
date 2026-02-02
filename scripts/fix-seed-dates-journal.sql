-- Fix seed entry dates so they fall in the "last 30 days" (Dashboard/Summary query from "now").
-- Run after seed-journal.sql if History shows entries but Dashboard/Summary are empty.
-- Run: psql -h localhost -p 5432 -U journal -d journal_db -f scripts/fix-seed-dates-journal.sql

UPDATE journal_entry SET created_at = (CURRENT_DATE - 30) + time '09:00:00', updated_at = (CURRENT_DATE - 30) + time '09:00:00' WHERE id = 'a1000001-0000-4000-8000-000000000001';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 29) + time '10:30:00', updated_at = (CURRENT_DATE - 29) + time '10:30:00' WHERE id = 'a1000002-0000-4000-8000-000000000002';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 28) + time '14:00:00', updated_at = (CURRENT_DATE - 28) + time '14:00:00' WHERE id = 'a1000003-0000-4000-8000-000000000003';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 27) + time '08:00:00', updated_at = (CURRENT_DATE - 27) + time '08:00:00' WHERE id = 'a1000004-0000-4000-8000-000000000004';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 26) + time '20:00:00', updated_at = (CURRENT_DATE - 26) + time '20:00:00' WHERE id = 'a1000005-0000-4000-8000-000000000005';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 25) + time '07:30:00', updated_at = (CURRENT_DATE - 25) + time '07:30:00' WHERE id = 'a1000006-0000-4000-8000-000000000006';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 24) + time '12:00:00', updated_at = (CURRENT_DATE - 24) + time '12:00:00' WHERE id = 'a1000007-0000-4000-8000-000000000007';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 23) + time '11:00:00', updated_at = (CURRENT_DATE - 23) + time '11:00:00' WHERE id = 'a1000008-0000-4000-8000-000000000008';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 22) + time '17:00:00', updated_at = (CURRENT_DATE - 22) + time '17:00:00' WHERE id = 'a1000009-0000-4000-8000-000000000009';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 21) + time '19:00:00', updated_at = (CURRENT_DATE - 21) + time '19:00:00' WHERE id = 'a1000010-0000-4000-8000-000000000010';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 20) + time '21:00:00', updated_at = (CURRENT_DATE - 20) + time '21:00:00' WHERE id = 'a1000011-0000-4000-8000-000000000011';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 19) + time '07:00:00', updated_at = (CURRENT_DATE - 19) + time '07:00:00' WHERE id = 'a1000012-0000-4000-8000-000000000012';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 18) + time '18:00:00', updated_at = (CURRENT_DATE - 18) + time '18:00:00' WHERE id = 'a1000013-0000-4000-8000-000000000013';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 17) + time '20:30:00', updated_at = (CURRENT_DATE - 17) + time '20:30:00' WHERE id = 'a1000014-0000-4000-8000-000000000014';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 16) + time '22:00:00', updated_at = (CURRENT_DATE - 16) + time '22:00:00' WHERE id = 'a1000015-0000-4000-8000-000000000015';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 15) + time '19:00:00', updated_at = (CURRENT_DATE - 15) + time '19:00:00' WHERE id = 'a1000016-0000-4000-8000-000000000016';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 14) + time '15:00:00', updated_at = (CURRENT_DATE - 14) + time '15:00:00' WHERE id = 'a1000017-0000-4000-8000-000000000017';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 13) + time '10:00:00', updated_at = (CURRENT_DATE - 13) + time '10:00:00' WHERE id = 'a1000018-0000-4000-8000-000000000018';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 12) + time '08:30:00', updated_at = (CURRENT_DATE - 12) + time '08:30:00' WHERE id = 'a1000019-0000-4000-8000-000000000019';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 11) + time '14:00:00', updated_at = (CURRENT_DATE - 11) + time '14:00:00' WHERE id = 'a1000020-0000-4000-8000-000000000020';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 10) + time '13:00:00', updated_at = (CURRENT_DATE - 10) + time '13:00:00' WHERE id = 'a1000021-0000-4000-8000-000000000021';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 9) + time '16:00:00', updated_at = (CURRENT_DATE - 9) + time '16:00:00' WHERE id = 'a1000022-0000-4000-8000-000000000022';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 8) + time '12:30:00', updated_at = (CURRENT_DATE - 8) + time '12:30:00' WHERE id = 'a1000023-0000-4000-8000-000000000023';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 7) + time '17:00:00', updated_at = (CURRENT_DATE - 7) + time '17:00:00' WHERE id = 'a1000024-0000-4000-8000-000000000024';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 6) + time '10:00:00', updated_at = (CURRENT_DATE - 6) + time '10:00:00' WHERE id = 'a1000025-0000-4000-8000-000000000025';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 5) + time '20:00:00', updated_at = (CURRENT_DATE - 5) + time '20:00:00' WHERE id = 'a1000026-0000-4000-8000-000000000026';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 4) + time '07:00:00', updated_at = (CURRENT_DATE - 4) + time '07:00:00' WHERE id = 'a1000027-0000-4000-8000-000000000027';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 3) + time '18:00:00', updated_at = (CURRENT_DATE - 3) + time '18:00:00' WHERE id = 'a1000028-0000-4000-8000-000000000028';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 2) + time '15:00:00', updated_at = (CURRENT_DATE - 2) + time '15:00:00' WHERE id = 'a1000029-0000-4000-8000-000000000029';
UPDATE journal_entry SET created_at = (CURRENT_DATE - 1) + time '21:00:00', updated_at = (CURRENT_DATE - 1) + time '21:00:00' WHERE id = 'a1000030-0000-4000-8000-000000000030';
