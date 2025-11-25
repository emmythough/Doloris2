-- Migration 002: Add repair_tickets and repair_attempts tables
-- This enables R.D 2.1 to track repair workflows and human approval

CREATE TABLE IF NOT EXISTS repair_tickets (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'awaiting_approval', 'approved', 'rejected', 'done', 'failed')),
  instruction TEXT NOT NULL,
  error_signature TEXT,
  pr_id TEXT,
  branch_name TEXT,
  summary TEXT
);

CREATE TABLE IF NOT EXISTS repair_attempts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticket_id UUID REFERENCES repair_tickets(id) ON DELETE CASCADE,
  status TEXT CHECK (status IN ('diagnosing', 'reproducing', 'patching', 'validating', 'failed', 'success')),
  attempt_no INT NOT NULL,
  logs TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_repair_tickets_status ON repair_tickets(status);
CREATE INDEX IF NOT EXISTS idx_repair_tickets_created ON repair_tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_repair_attempts_ticket ON repair_attempts(ticket_id);

-- Comments
COMMENT ON TABLE repair_tickets IS 'Tracks R.D repair requests from creation to deployment';
COMMENT ON TABLE repair_attempts IS 'Logs each step of R.D repair process';
COMMENT ON COLUMN repair_tickets.status IS 'Workflow status: pending → in_progress → awaiting_approval → approved/rejected → done/failed';
