-- Seed journal entries for the last 45 days (journal_db).
-- Varied content covering prompts/nudges: work, exercise, morning walk, creative ideas, family, sleep, gratitude, deadlines, etc.
--
-- *** WHY THE API RETURNED ONLY 16 ENTRIES ***
-- The 30-day seed (seed-journal.sql) uses IDs a1000001..a1000030. This script now uses a2000001..a2000045
-- so there is no conflict: all 45 rows insert for your user. Previously we used a1000001..a1000045; the
-- first 30 IDs already existed (from the 30-day seed, possibly another user), so only 15 inserted for you.
--
-- *** WHY DATA ONLY GOES UP TO A CERTAIN DATE ***
-- CURRENT_DATE is the date when you RUN this script. Re-run today to move the range up to "yesterday".
--
-- IMPORTANT: Use the SAME user_id as your logged-in account (JWT "sub" or login response).
-- 1. Replace ea4b5be7-1d22-46f0-97cf-86025ec07056 with your actual user UUID.
-- 2. Run: psql -h localhost -p 5432 -U journal -d journal_db -f scripts/seed-journal-45.sql

SET timezone = 'UTC';

INSERT INTO journal_entry (id, user_id, content, mood_rating, mood, mood_note, created_at, updated_at) VALUES
  ('a2000001-0000-4000-8000-000000000001', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Had a great morning run. Felt strong and clear-headed. Going to keep this routine.', NULL, 'Calm', NULL, (CURRENT_DATE - 45) + time '09:00:00', (CURRENT_DATE - 45) + time '09:00:00'),
  ('a2000002-0000-4000-8000-000000000002', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Finished the project ahead of schedule. Team was supportive. Really grateful for this job.', NULL, 'Grateful', NULL, (CURRENT_DATE - 44) + time '10:30:00', (CURRENT_DATE - 44) + time '10:30:00'),
  ('a2000003-0000-4000-8000-000000000003', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Spent the afternoon with the kids at the park. No screens, just playing. Best day this week.', NULL, 'Joyful', NULL, (CURRENT_DATE - 43) + time '14:00:00', (CURRENT_DATE - 43) + time '14:00:00'),
  ('a2000004-0000-4000-8000-000000000004', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Busy day. Did not get enough sleep last night. Not sure if I am doing too much or not enough.', NULL, 'Tired', NULL, (CURRENT_DATE - 42) + time '08:00:00', (CURRENT_DATE - 42) + time '08:00:00'),
  ('a2000005-0000-4000-8000-000000000005', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Thought a lot about where I want to be in a year. Career, health, family – trying to balance it all.', NULL, 'Reflective', NULL, (CURRENT_DATE - 41) + time '20:00:00', (CURRENT_DATE - 41) + time '20:00:00'),
  ('a2000006-0000-4000-8000-000000000006', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Slept badly again. Woke up anxious about the meeting. Coffee did not help much.', NULL, 'Anxious', NULL, (CURRENT_DATE - 40) + time '07:30:00', (CURRENT_DATE - 40) + time '07:30:00'),
  ('a2000007-0000-4000-8000-000000000007', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Someone at work went out of their way to help me. Small kindness, big impact.', NULL, 'Grateful', NULL, (CURRENT_DATE - 39) + time '12:00:00', (CURRENT_DATE - 39) + time '12:00:00'),
  ('a2000008-0000-4000-8000-000000000008', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Finally started the online course I have been putting off. First lesson done. Feeling motivated.', NULL, 'Hopeful', NULL, (CURRENT_DATE - 38) + time '11:00:00', (CURRENT_DATE - 38) + time '11:00:00'),
  ('a2000009-0000-4000-8000-000000000009', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Got good feedback from my manager. Feeling seen and valued at work.', NULL, 'Good', NULL, (CURRENT_DATE - 37) + time '17:00:00', (CURRENT_DATE - 37) + time '17:00:00'),
  ('a2000010-0000-4000-8000-000000000010', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Had a hard conversation with a friend. Uncomfortable but necessary. Hoping it leads to something better.', NULL, 'Reflective', NULL, (CURRENT_DATE - 36) + time '19:00:00', (CURRENT_DATE - 36) + time '19:00:00'),
  ('a2000011-0000-4000-8000-000000000011', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Read for an hour before bed. Felt like the first time I have slowed down in days.', NULL, 'Peaceful', NULL, (CURRENT_DATE - 35) + time '21:00:00', (CURRENT_DATE - 35) + time '21:00:00'),
  ('a2000012-0000-4000-8000-000000000012', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Meditated for 10 minutes. Mind kept wandering, but I am glad I showed up.', NULL, 'Calm', NULL, (CURRENT_DATE - 34) + time '07:00:00', (CURRENT_DATE - 34) + time '07:00:00'),
  ('a2000013-0000-4000-8000-000000000013', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Missed a deadline. Felt like I let everyone down. Need to plan better.', NULL, 'Frustrated', NULL, (CURRENT_DATE - 33) + time '18:00:00', (CURRENT_DATE - 33) + time '18:00:00'),
  ('a2000014-0000-4000-8000-000000000014', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Argument with my partner over something small. We are both tired. Not sure how to fix it.', NULL, 'Low', NULL, (CURRENT_DATE - 32) + time '20:30:00', (CURRENT_DATE - 32) + time '20:30:00'),
  ('a2000015-0000-4000-8000-000000000015', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Spent too much time on news and social media. Feel drained and irritable.', NULL, 'Overwhelmed', NULL, (CURRENT_DATE - 31) + time '22:00:00', (CURRENT_DATE - 31) + time '22:00:00'),
  ('a2000016-0000-4000-8000-000000000016', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Grateful for a quiet evening at home. Cooked a simple dinner. No drama.', NULL, 'Peaceful', NULL, (CURRENT_DATE - 30) + time '19:00:00', (CURRENT_DATE - 30) + time '19:00:00'),
  ('a2000017-0000-4000-8000-000000000017', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Called my parents. They are doing okay. Reminded me to appreciate what I have.', NULL, 'Grateful', NULL, (CURRENT_DATE - 29) + time '15:00:00', (CURRENT_DATE - 29) + time '15:00:00'),
  ('a2000018-0000-4000-8000-000000000018', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Weather was perfect for a walk. Noticed the trees and birds. Felt present.', NULL, 'Calm', NULL, (CURRENT_DATE - 28) + time '10:00:00', (CURRENT_DATE - 28) + time '10:00:00'),
  ('a2000019-0000-4000-8000-000000000019', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Wrote down three things I am grateful for. Sleep, health, and people who care.', NULL, 'Grateful', NULL, (CURRENT_DATE - 27) + time '08:30:00', (CURRENT_DATE - 27) + time '08:30:00'),
  ('a2000020-0000-4000-8000-000000000020', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Health check-up did not go as hoped. Waiting on more tests. Trying not to spiral.', NULL, 'Anxious', NULL, (CURRENT_DATE - 26) + time '14:00:00', (CURRENT_DATE - 26) + time '14:00:00'),
  ('a2000021-0000-4000-8000-000000000021', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Lunch with an old friend. Laughed a lot. Need to do this more often.', NULL, 'Joyful', NULL, (CURRENT_DATE - 25) + time '13:00:00', (CURRENT_DATE - 25) + time '13:00:00'),
  ('a2000022-0000-4000-8000-000000000022', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Could not focus at all. Kept checking email. Need to set better boundaries.', NULL, 'Frustrated', NULL, (CURRENT_DATE - 24) + time '16:00:00', (CURRENT_DATE - 24) + time '16:00:00'),
  ('a2000023-0000-4000-8000-000000000023', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Took a proper lunch break outside. Came back feeling much clearer.', NULL, 'Okay', NULL, (CURRENT_DATE - 23) + time '12:30:00', (CURRENT_DATE - 23) + time '12:30:00'),
  ('a2000024-0000-4000-8000-000000000024', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Weekend project finally done. Proud of myself for finishing it.', NULL, 'Good', NULL, (CURRENT_DATE - 22) + time '17:00:00', (CURRENT_DATE - 22) + time '17:00:00'),
  ('a2000025-0000-4000-8000-000000000025', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Slept in. No alarm. Felt human again.', NULL, 'Calm', NULL, (CURRENT_DATE - 21) + time '10:00:00', (CURRENT_DATE - 21) + time '10:00:00'),
  ('a2000026-0000-4000-8000-000000000026', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Stressed about money. Made a budget. At least I have a plan now.', NULL, 'Hopeful', NULL, (CURRENT_DATE - 20) + time '20:00:00', (CURRENT_DATE - 20) + time '20:00:00'),
  ('a2000027-0000-4000-8000-000000000027', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'First workout in two weeks. Hard but worth it.', NULL, 'Good', NULL, (CURRENT_DATE - 19) + time '07:00:00', (CURRENT_DATE - 19) + time '07:00:00'),
  ('a2000028-0000-4000-8000-000000000028', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Team celebrated a launch. Felt good to be part of something.', NULL, 'Joyful', NULL, (CURRENT_DATE - 18) + time '18:00:00', (CURRENT_DATE - 18) + time '18:00:00'),
  ('a2000029-0000-4000-8000-000000000029', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Quiet day. Caught up on admin. Boring but necessary.', NULL, 'Okay', NULL, (CURRENT_DATE - 17) + time '15:00:00', (CURRENT_DATE - 17) + time '15:00:00'),
  ('a2000030-0000-4000-8000-000000000030', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'End of the month. Reflecting on what went well and what to change next month.', NULL, 'Reflective', NULL, (CURRENT_DATE - 16) + time '21:00:00', (CURRENT_DATE - 16) + time '21:00:00'),
  ('a2000031-0000-4000-8000-000000000031', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'You have mentioned work a few times this week. Today was another heavy day – deadlines piling up. Took a short walk at lunch and it helped.', NULL, 'Tired', NULL, (CURRENT_DATE - 15) + time '19:30:00', (CURRENT_DATE - 15) + time '19:30:00'),
  ('a2000032-0000-4000-8000-000000000032', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Creative ideas came up more often this week. Jotted down a few for the side project. Feeling energized when I write about this.', NULL, 'Hopeful', NULL, (CURRENT_DATE - 14) + time '09:00:00', (CURRENT_DATE - 14) + time '09:00:00'),
  ('a2000033-0000-4000-8000-000000000033', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Morning walk again. You have written about walking a few times – today the air was crisp and I felt lighter afterward.', NULL, 'Calm', NULL, (CURRENT_DATE - 13) + time '08:00:00', (CURRENT_DATE - 13) + time '08:00:00'),
  ('a2000034-0000-4000-8000-000000000034', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Family dinner. Kids were loud but it was nice. Something from this week I want to carry into next.', NULL, 'Grateful', NULL, (CURRENT_DATE - 12) + time '20:00:00', (CURRENT_DATE - 12) + time '20:00:00'),
  ('a2000035-0000-4000-8000-000000000035', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Slept better. Made an effort to put the phone away. What helped you feel more at ease on those lighter days? For me it was less screen before bed.', NULL, 'Peaceful', NULL, (CURRENT_DATE - 11) + time '07:30:00', (CURRENT_DATE - 11) + time '07:30:00'),
  ('a2000036-0000-4000-8000-000000000036', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Work stress again. On tougher days I notice I write more about deadlines. Trying to notice what helps – even a five-minute break.', NULL, 'Frustrated', NULL, (CURRENT_DATE - 10) + time '17:00:00', (CURRENT_DATE - 10) + time '17:00:00'),
  ('a2000037-0000-4000-8000-000000000037', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'What is one small step you could take from here? I signed up for that class I kept putting off.', NULL, 'Hopeful', NULL, (CURRENT_DATE - 9) + time '12:00:00', (CURRENT_DATE - 9) + time '12:00:00'),
  ('a2000038-0000-4000-8000-000000000038', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Another day where exercise showed up. Ran 3k. Entries on days I move tend to feel lighter.', NULL, 'Good', NULL, (CURRENT_DATE - 8) + time '09:30:00', (CURRENT_DATE - 8) + time '09:30:00'),
  ('a2000039-0000-4000-8000-000000000039', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Want to go deeper? Today I thought about why I get so anxious before meetings. Maybe it is the fear of being judged.', NULL, 'Reflective', NULL, (CURRENT_DATE - 7) + time '21:00:00', (CURRENT_DATE - 7) + time '21:00:00'),
  ('a2000040-0000-4000-8000-000000000040', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'How did work feel today? Honestly overwhelming. But I asked for help and one colleague stepped in. Grateful for that.', NULL, 'Grateful', NULL, (CURRENT_DATE - 6) + time '18:30:00', (CURRENT_DATE - 6) + time '18:30:00'),
  ('a2000041-0000-4000-8000-000000000041', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'You have mentioned sleep a few times. Last night was rough again. Going to try no caffeine after 2pm and see if it helps.', NULL, 'Tired', NULL, (CURRENT_DATE - 5) + time '08:00:00', (CURRENT_DATE - 5) + time '08:00:00'),
  ('a2000042-0000-4000-8000-000000000042', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Creative ideas – wrote about the trip idea again. When I write about travel and plans I feel more energized. Want to lean into that.', NULL, 'Joyful', NULL, (CURRENT_DATE - 4) + time '10:00:00', (CURRENT_DATE - 4) + time '10:00:00'),
  ('a2000043-0000-4000-8000-000000000043', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'What helped you feel more at ease? Talking to my sister on the phone. She gets it. Going to call her more often.', NULL, 'Peaceful', NULL, (CURRENT_DATE - 3) + time '19:00:00', (CURRENT_DATE - 3) + time '19:00:00'),
  ('a2000044-0000-4000-8000-000000000044', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'Is there something from this week you would like to carry into next week? The morning walk habit. And saying no to one extra meeting.', NULL, 'Reflective', NULL, (CURRENT_DATE - 2) + time '20:00:00', (CURRENT_DATE - 2) + time '20:00:00'),
  ('a2000045-0000-4000-8000-000000000045', 'ea4b5be7-1d22-46f0-97cf-86025ec07056', 'End of a long stretch. Reflecting on progress: more consistent with journaling, more aware of what helps on tough days. Gentle with myself today.', NULL, 'Calm', NULL, (CURRENT_DATE - 1) + time '21:00:00', (CURRENT_DATE - 1) + time '21:00:00')
ON CONFLICT (id) DO UPDATE SET
  content = EXCLUDED.content,
  mood_rating = EXCLUDED.mood_rating,
  mood = EXCLUDED.mood,
  mood_note = EXCLUDED.mood_note,
  created_at = EXCLUDED.created_at,
  updated_at = EXCLUDED.updated_at;
