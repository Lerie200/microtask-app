-- Run this once against your existing database to add support for
-- text-based answers (choices, ratings, counts) alongside file uploads.
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS answer_text VARCHAR(255);