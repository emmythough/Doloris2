-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- USERS TABLE
create table users (
  id uuid default gen_random_uuid() primary key,
  telegram_id bigint unique not null,
  name text,
  timezone text default 'UTC',
  settings jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- MESSAGES TABLE
create table messages (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references users(id) on delete cascade not null,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null,
  meta jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- TASKS TABLE
create table tasks (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references users(id) on delete cascade not null,
  title text not null,
  status text default 'todo' check (status in ('todo', 'in_progress', 'done', 'deleted')),
  due_at timestamp with time zone,
  priority int default 1,
  source text default 'user',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- LOGS TABLE (Life Log)
create table logs (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references users(id) on delete cascade not null,
  type text not null, -- e.g., 'sleep', 'mood', 'work'
  summary text,
  details jsonb default '{}'::jsonb,
  occurred_at timestamp with time zone default timezone('utc'::text, now()) not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- INSTRUCTIONS TABLE (The Code Sheet)
create table instructions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references users(id) on delete cascade not null,
  scope text default 'global',
  content text not null,
  is_active boolean default true,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- NUDGES TABLE (Outbound Log)
create table nudges (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references users(id) on delete cascade not null,
  reason text,
  message text not null,
  sent_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- EMBEDDINGS TABLE (Semantic Memory)
create table embeddings (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references users(id) on delete cascade not null,
  source_type text not null, -- 'message', 'log', 'task', 'instruction'
  source_id uuid not null,
  embedding vector(1536), -- OpenAI text-embedding-3-small dimension
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create indexes for better performance
create index idx_users_telegram_id on users(telegram_id);
create index idx_messages_user_id on messages(user_id);
create index idx_tasks_user_id on tasks(user_id);
create index idx_tasks_status on tasks(status);
create index idx_logs_user_id on logs(user_id);
create index idx_instructions_user_id on instructions(user_id);
