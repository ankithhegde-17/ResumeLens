-- Additive migration. Run in the existing project's Supabase SQL Editor.
-- Does not alter profiles, analyses, auth, saved scores or existing policies.
begin;
create table if not exists public.learning_progress (
 user_id uuid not null references auth.users(id) on delete cascade,
 skill_slug text not null check (char_length(skill_slug) between 1 and 80),
 status text not null check (status in ('not_started','learning','completed')),
 updated_at timestamptz not null default now(), primary key(user_id,skill_slug)
);
create table if not exists public.learning_settings (
 user_id uuid primary key references auth.users(id) on delete cascade,
 hours integer not null default 10 check (hours in (5,10,20))
);
alter table public.learning_progress enable row level security;
alter table public.learning_settings enable row level security;
revoke all on public.learning_progress,public.learning_settings from anon,authenticated;
grant select,insert,update on public.learning_progress,public.learning_settings to authenticated;
drop policy if exists learning_progress_owner on public.learning_progress;
create policy learning_progress_owner on public.learning_progress for all to authenticated
 using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
drop policy if exists learning_settings_owner on public.learning_settings;
create policy learning_settings_owner on public.learning_settings for all to authenticated
 using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
commit;
