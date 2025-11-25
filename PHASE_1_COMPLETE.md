# Phase 1 Complete - Migration Instructions

## ✅ What Was Completed

**Phase 1.1 - Database Migrations:**
- ✅ Created 3 SQL migration files
- ✅ Updated models.py with new types (ErrorLog, RepairTicket, RepairAttempt, Note)

**Phase 1.2 - Error Logger Integration:**
- ✅ Created error_logger middleware
- ✅ Integrated into webhook error handler
- ✅ Integrated into brain error handlers (2 locations)
- ✅ Errors now tracked with deduplication

**Code Deployed:** All changes pushed to GitHub + auto-deploying to Render

---

## 🔴 ACTION REQUIRED: Run Database Migrations

The error tracking won't work until you create the new tables!

### Quick Steps:

1. **Go to Supabase Dashboard**
   - https://supabase.com/dashboard
   - Select your Doloris project

2. **Open SQL Editor**
   - Click "SQL Editor" in sidebar

3. **Run Each Migration** (in order):

**Migration 1 - Errors Table:**
```sql
-- Copy from: migrations/001_add_errors_table.sql
CREATE TABLE IF NOT EXISTS errors (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  error_signature TEXT NOT NULL UNIQUE,
  stack_trace TEXT,
  service TEXT DEFAULT 'doloris',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  count INT DEFAULT 1,
  last_seen_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_errors_signature ON errors(error_signature);
CREATE INDEX IF NOT EXISTS idx_errors_last_seen ON errors(last_seen_at DESC);
```

**Migration 2 - Repair Tables:**
```sql
-- Copy from: migrations/002_add_repair_tickets.sql
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

CREATE INDEX IF NOT EXISTS idx_repair_tickets_status ON repair_tickets(status);
CREATE INDEX IF NOT EXISTS idx_repair_tickets_created ON repair_tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_repair_attempts_ticket ON repair_attempts(ticket_id);
```

**Migration 3 - Notes Table:**
```sql
-- Copy from: migrations/003_add_notes_table.sql
CREATE TABLE IF NOT EXISTS notes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id BIGINT NOT NULL,
  content TEXT NOT NULL,
  tags TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id);
CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_tags ON notes USING GIN(tags);
```

4. **Verify Tables Created:**
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('errors', 'repair_tickets', 'repair_attempts', 'notes');
```

Should return 4 rows ✅

---

## 🧪 Test Error Tracking

After migrations are done and Render deployment completes:

1. Trigger an error (intentionally send bad input to bot)
2. Check Supabase `errors` table - should see entry
3. Trigger same error again - `count` should increment

Or run the test script:
```bash
python test_error_logging.py
```

---

## 📊 What This Enables

- **Error Deduplication:** Same error tracked once with counter
- **R.D Foundation:** Error signatures ready for R.D to diagnose
- **Production Visibility:** All errors logged to database
- **Repair Workflow:** Infrastructure for ticket-based repairs

---

## ⏭️ Next: Phase 1.3

After migrations:
- Add GitHub token to config
- Update requirements.txt
- Ready for Phase 2 (Intent Classifier)
