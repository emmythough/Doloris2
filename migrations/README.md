# Database Migrations

This directory contains SQL migration files for Doloris 2.0 + R.D 2.1.

## Running Migrations

### On Supabase (Recommended)

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Go to **SQL Editor**
4. Copy and paste each migration file in order:
   - `001_add_errors_table.sql`
   - `002_add_repair_tickets.sql`
   - `003_add_notes_table.sql`
5. Execute each migration

### Using psql (Alternative)

```bash
psql $DATABASE_URL -f migrations/001_add_errors_table.sql
psql $DATABASE_URL -f migrations/002_add_repair_tickets.sql
psql $DATABASE_URL -f migrations/003_add_notes_table.sql
```

## Migration Files

| File | Description |
|------|-------------|
| `001_add_errors_table.sql` | Error tracking with deduplication |
| `002_add_repair_tickets.sql` | R.D 2.1 repair workflow tables |
| `003_add_notes_table.sql` | User notes with tagging |

## Verification

After running migrations, verify tables exist:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('errors', 'repair_tickets', 'repair_attempts', 'notes');
```

Should return 4 rows.
