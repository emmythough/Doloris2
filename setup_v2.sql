-- Doloris 2.0 Database Schema Migration

-- 1. Preferences Table
-- Stores user-specific settings for interaction style
CREATE TABLE IF NOT EXISTS preferences (
  user_id BIGINT PRIMARY KEY, -- Changed to BIGINT to match Telegram ID type
  tone TEXT DEFAULT 'friendly',
  preferred_name TEXT,
  reply_length TEXT DEFAULT 'balanced', -- concise, balanced, detailed
  thinking_mode TEXT DEFAULT 'balanced', -- fast (Tier 1), balanced (Tier 2), deep (Tier 3)
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Connections Table
-- Stores OAuth tokens for external services (Calendar, etc.)
CREATE TABLE IF NOT EXISTS connections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id BIGINT NOT NULL,
  provider TEXT NOT NULL, -- google, microsoft, etc.
  access_token TEXT,
  refresh_token TEXT,
  scopes TEXT[],
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Files Table
-- Metadata for files uploaded by users
CREATE TABLE IF NOT EXISTS files (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id BIGINT NOT NULL,
  bucket_id TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_url TEXT NOT NULL,
  file_type TEXT, -- pdf, image, etc.
  file_size BIGINT,
  summary TEXT, -- AI-generated summary
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. System State Table
-- Stores Doloris's personality and global configuration
CREATE TABLE IF NOT EXISTS system_state (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  personality TEXT NOT NULL,
  goals TEXT NOT NULL,
  version TEXT DEFAULT '2.0',
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Storage Spaces Table
-- Tracks which users have their own storage buckets
CREATE TABLE IF NOT EXISTS storage_spaces (
  user_id BIGINT PRIMARY KEY,
  bucket_id TEXT NOT NULL,
  is_public BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed initial system state
INSERT INTO system_state (personality, goals, version)
VALUES (
  'You are Doloris, a highly capable personal AI assistant. Core Traits: Warm, friendly, proactive, respectful. Style: Natural, concise, adaptable.',
  'Primary Mission: Help the user organize their life, protect their time, and achieve their goals. Rules: Privacy first, proactive tool usage, cost-effective model selection.',
  '2.0'
) ON CONFLICT DO NOTHING;

-- Enable RLS (Row Level Security) - Optional but recommended
ALTER TABLE preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE storage_spaces ENABLE ROW LEVEL SECURITY;
