-- Doloris 3.0 Schema Migration

-- Enable pgvector if not already enabled (requires superuser, might fail on some managed instances if not available)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Repair Tickets Table (for Dev Brain)
CREATE TABLE IF NOT EXISTS repair_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    description TEXT NOT NULL,
    error_ids TEXT[], -- Array of error IDs from the errors table
    trace_ids TEXT[], -- Array of trace IDs related to this issue
    status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, pr_created, resolved, closed
    pr_url TEXT,
    pr_number INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- 2. Enhanced System Events (for Traceability)
-- We might already have a system_events table, so we'll alter it or create a v3 version.
-- Let's assume we want a clean break or upgrade.
CREATE TABLE IF NOT EXISTS system_events_v3 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id TEXT NOT NULL,
    type TEXT NOT NULL, -- telegram_in, intent_classified, tool_call, error, etc.
    data JSONB, -- Structured data for the event
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast trace lookups
CREATE INDEX IF NOT EXISTS idx_system_events_v3_trace_id ON system_events_v3(trace_id);

-- 3. Job Queue (Backup/Persistence if Redis fails, or for long term history)
CREATE TABLE IF NOT EXISTS job_queue_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id TEXT NOT NULL,
    trace_id TEXT,
    status TEXT NOT NULL, -- queued, processing, completed, failed
    payload JSONB,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- 4. Update Tasks for Vector Search (Optional, if we want semantic search on tasks)
-- ALTER TABLE tasks ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- 5. Update Logs for Vector Search
-- ALTER TABLE logs ADD COLUMN IF NOT EXISTS embedding vector(1536);
