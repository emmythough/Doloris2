-- Migration 003: Add notes table for user note-taking
-- This enables Doloris to manage user notes with tagging

CREATE TABLE IF NOT EXISTS notes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id BIGINT NOT NULL,
  content TEXT NOT NULL,
  tags TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id);
CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_tags ON notes USING GIN(tags);

-- Comments
COMMENT ON TABLE notes IS 'User notes with tagging support for Doloris 2.0';
COMMENT ON COLUMN notes.tags IS 'Array of tags for categorization (e.g., ["work", "personal"])';
