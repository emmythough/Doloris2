-- Migration 001: Add errors table for error tracking and deduplication
-- This enables R.D 2.1 to diagnose and fix recurring issues

CREATE TABLE IF NOT EXISTS errors (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  error_signature TEXT NOT NULL UNIQUE,
  stack_trace TEXT,
  service TEXT DEFAULT 'doloris',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  count INT DEFAULT 1,
  last_seen_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast signature lookup
CREATE INDEX IF NOT EXISTS idx_errors_signature ON errors(error_signature);

-- Index for querying recent errors
CREATE INDEX IF NOT EXISTS idx_errors_last_seen ON errors(last_seen_at DESC);

-- Comments for documentation
COMMENT ON TABLE errors IS 'Tracks application errors with deduplication by signature';
COMMENT ON COLUMN errors.error_signature IS 'MD5 hash of exception type + file + line';
COMMENT ON COLUMN errors.count IS 'Number of times this error has occurred';
