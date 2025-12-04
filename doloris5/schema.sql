-- Doloris 5.3 Database Schema
-- "Ghost in the Machine" Architecture

-- ======================
-- CORE TABLES
-- ======================

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE, -- Nullable for web users
    email TEXT UNIQUE,
    name TEXT,
    timezone TEXT DEFAULT 'UTC',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversation Events (Raw messages)
CREATE TABLE IF NOT EXISTS conversation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    turn_id TEXT NOT NULL, -- Not unique (shared by inbound/outbound)
    direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversation_user ON conversation_events(user_id, created_at DESC);
CREATE INDEX idx_conversation_turn ON conversation_events(turn_id);

-- ======================
-- COGNITIVE LAYER (THE GHOST)
-- ======================

-- Thought Traces (Internal deliberation logs)
CREATE TABLE IF NOT EXISTS thought_traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    turn_id TEXT NOT NULL, -- Loose coupling to allow flexibility
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Tri-Cameral Council outputs
    empath_summary TEXT,
    empath_tokens INTEGER,
    
    auditor_flags JSONB DEFAULT '[]'::jsonb,
    auditor_tokens INTEGER,
    
    executive_decision TEXT NOT NULL,
    executive_reasoning TEXT,
    executive_tokens INTEGER,
    
    final_intent TEXT, -- e.g., "send_email", "draft_booking"
    final_args JSONB,
    confidence FLOAT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_thought_traces_user ON thought_traces(user_id, created_at DESC);
CREATE INDEX idx_thought_traces_turn ON thought_traces(turn_id);

-- Semantic Memory (Extracted facts from session naps)
CREATE TABLE IF NOT EXISTS semantic_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    fact_type TEXT NOT NULL, -- 'preference', 'habit', 'context', 'relationship'
    fact_key TEXT NOT NULL, -- e.g., 'favorite_restaurant', 'wake_time'
    fact_value TEXT NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    
    source_turn_id TEXT, -- Which conversation led to this
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, fact_key)
);

CREATE INDEX idx_semantic_memory_user ON semantic_memory(user_id);
CREATE INDEX idx_semantic_memory_type ON semantic_memory(fact_type);

-- ======================
-- VECTOR MEMORY (RAG)
-- ======================

-- Enable Vector Extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Memories (Vector Store)
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    content TEXT NOT NULL, -- The actual memory text
    embedding vector(1536), -- OpenAI text-embedding-3-small
    
    metadata JSONB DEFAULT '{}'::jsonb, -- Extra info (source turn, date, etc.)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memories_user ON memories(user_id);
-- IVFFlat index for faster approximate search (optional, good for large datasets)
-- CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops);

-- ======================
-- EXECUTION LAYER (THE HANDS)
-- ======================

-- Signed Action Tickets
CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    action TEXT NOT NULL, -- e.g., 'send_email', 'book_calendar'
    args JSONB NOT NULL,
    args_hash TEXT NOT NULL, -- For integrity checking
    
    status TEXT NOT NULL DEFAULT 'pending_approval' CHECK (
        status IN ('pending_approval', 'approved', 'executing', 'completed', 'failed', 'expired', 'rejected')
    ),
    
    nonce TEXT UNIQUE NOT NULL, -- Prevents replay
    signature TEXT, -- HMAC signature for validation
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    approved_at TIMESTAMPTZ,
    executed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_tickets_user ON tickets(user_id, created_at DESC);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_nonce ON tickets(nonce);

-- MCP Audit Log
CREATE TABLE IF NOT EXISTS mcp_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id TEXT REFERENCES tickets(ticket_id),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    mcp_server TEXT NOT NULL, -- e.g., 'gmail', 'calendar'
    tool_name TEXT NOT NULL, -- e.g., 'send_message', 'create_event'
    args JSONB NOT NULL,
    
    status TEXT NOT NULL CHECK (status IN ('success', 'failed')),
    response JSONB,
    error TEXT,
    
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_mcp_audit_user ON mcp_audit(user_id, created_at DESC);
CREATE INDEX idx_mcp_audit_server ON mcp_audit(mcp_server, created_at DESC);

-- MCP Approvals (User consent records)
CREATE TABLE IF NOT EXISTS mcp_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    mcp_server TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    
    scope TEXT[], -- What permissions were granted
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    
    UNIQUE(user_id, mcp_server, tool_name)
);

-- ======================
-- SESSION & LEARNING
-- ======================

-- Session Metadata (For session naps)
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ DEFAULT NOW(),
    consolidated_at TIMESTAMPTZ,
    
    turn_count INTEGER DEFAULT 0,
    facts_extracted INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_sessions_user ON sessions(user_id, started_at DESC);
CREATE INDEX idx_sessions_active ON sessions(is_active, last_activity_at);

-- ======================
-- REDIS STREAM TRACKING
-- ======================

-- Stream Offsets (For Redis consumer groups)
CREATE TABLE IF NOT EXISTS stream_offsets (
    consumer_group TEXT NOT NULL,
    stream_name TEXT NOT NULL,
    last_id TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (consumer_group, stream_name)
);

-- ======================
-- INDEXES & CONSTRAINTS
-- ======================

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_events_created ON conversation_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_expires ON tickets(expires_at) WHERE status = 'pending_approval';
CREATE INDEX IF NOT EXISTS idx_sessions_consolidate ON sessions(last_activity_at) WHERE is_active = TRUE AND consolidated_at IS NULL;

-- ======================
-- ROW LEVEL SECURITY (RLS)
-- ======================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE thought_traces ENABLE ROW LEVEL SECURITY;
ALTER TABLE semantic_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own data
CREATE POLICY user_isolation_policy ON users FOR ALL USING (auth.uid()::uuid = id);
CREATE POLICY user_events_policy ON conversation_events FOR ALL USING (auth.uid()::uuid = user_id);
CREATE POLICY user_thoughts_policy ON thought_traces FOR ALL USING (auth.uid()::uuid = user_id);
CREATE POLICY user_memory_policy ON semantic_memory FOR ALL USING (auth.uid()::uuid = user_id);
CREATE POLICY user_tickets_policy ON tickets FOR ALL USING (auth.uid()::uuid = user_id);
CREATE POLICY user_audit_policy ON mcp_audit FOR ALL USING (auth.uid()::uuid = user_id);
CREATE POLICY user_sessions_policy ON sessions FOR ALL USING (auth.uid()::uuid = user_id);
CREATE POLICY user_memories_policy ON memories FOR ALL USING (auth.uid()::uuid = user_id);

-- Service role can access everything (for backend workers)
CREATE POLICY service_role_all ON users FOR ALL TO service_role USING (true);
CREATE POLICY service_role_events ON conversation_events FOR ALL TO service_role USING (true);
CREATE POLICY service_role_thoughts ON thought_traces FOR ALL TO service_role USING (true);
CREATE POLICY service_role_memory ON semantic_memory FOR ALL TO service_role USING (true);
CREATE POLICY service_role_tickets ON tickets FOR ALL TO service_role USING (true);
CREATE POLICY service_role_audit ON mcp_audit FOR ALL TO service_role USING (true);
CREATE POLICY service_role_sessions ON sessions FOR ALL TO service_role USING (true);
CREATE POLICY service_role_memories ON memories FOR ALL TO service_role USING (true);

-- ======================
-- FUNCTIONS & TRIGGERS
-- ======================

-- Update last_activity for users
CREATE OR REPLACE FUNCTION update_user_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users SET last_active_at = NOW() WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_activity_trigger
    AFTER INSERT ON conversation_events
    FOR EACH ROW
    EXECUTE FUNCTION update_user_activity();

-- Auto-expire old tickets
CREATE OR REPLACE FUNCTION expire_old_tickets()
RETURNS void AS $$
BEGIN
    UPDATE tickets
    SET status = 'expired'
    WHERE status = 'pending_approval'
    AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Schedule: Run every minute (set up in Supabase dashboard or pg_cron)
-- SELECT cron.schedule('expire-tickets', '* * * * *', 'SELECT expire_old_tickets()');
