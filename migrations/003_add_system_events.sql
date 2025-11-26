-- Migration: Add system_events table for centralized logging
-- Description: Tracks message flow from webhook to response for debugging

CREATE TABLE IF NOT EXISTS system_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL,
    user_id TEXT, -- Can be UUID string or Telegram ID if user not yet resolved
    component TEXT NOT NULL, -- 'webhook', 'brain', 'tools', etc.
    event_type TEXT NOT NULL, -- 'received', 'processing', 'error', etc.
    status TEXT NOT NULL, -- 'info', 'warning', 'error', 'success'
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookup by trace_id
CREATE INDEX IF NOT EXISTS idx_system_events_trace_id ON system_events(trace_id);

-- Index for lookup by user_id
CREATE INDEX IF NOT EXISTS idx_system_events_user_id ON system_events(user_id);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_system_events_created_at ON system_events(created_at DESC);
