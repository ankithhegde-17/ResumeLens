-- Run this whole script once in your Supabase SQL Editor. It can be rerun.
-- Use a new project or review conflicts with existing tables of the same names.
begin;
create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null check (char_length(display_name) between 2 and 60),
  headline text not null default '' check (char_length(headline) <= 120),
  location text not null default '' check (char_length(location) <= 80),
  goal_role text not null default ''
);
create table if not exists public.analyses (
  id uuid primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  series_id uuid not null,
  title text not null check (char_length(title) between 2 and 80),
  version integer not null check (version > 0),
  created_at timestamptz not null default now(),
  source_name text not null,
  source_type text not null check (source_type in ('PDF','Image')),
  result jsonb not null check (jsonb_typeof(result) = 'object'),
  unique(user_id, series_id, version)
);
create index if not exists analyses_owner_history on public.analyses(user_id, created_at desc);
alter table public.profiles enable row level security;
alter table public.analyses enable row level security;
revoke all on public.profiles, public.analyses from anon, authenticated;
grant usage on schema public to authenticated;
grant select, insert, update on public.profiles to authenticated;
grant select, insert, delete on public.analyses to authenticated;
-- Analyses have no UPDATE grant or policy, so saved versions are immutable.
drop policy if exists profiles_read_own on public.profiles;
drop policy if exists profiles_insert_own on public.profiles;
drop policy if exists profiles_update_own on public.profiles;
create policy profiles_read_own on public.profiles for select to authenticated using ((select auth.uid()) = user_id);
create policy profiles_insert_own on public.profiles for insert to authenticated with check ((select auth.uid()) = user_id);
create policy profiles_update_own on public.profiles for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists analyses_read_own on public.analyses;
drop policy if exists analyses_insert_own on public.analyses;
drop policy if exists analyses_delete_own on public.analyses;
create policy analyses_read_own on public.analyses for select to authenticated using ((select auth.uid()) = user_id);
create policy analyses_insert_own on public.analyses for insert to authenticated with check ((select auth.uid()) = user_id);
create policy analyses_delete_own on public.analyses for delete to authenticated using ((select auth.uid()) = user_id);

-- A transaction assigns the version and makes duplicate form submission safe.
-- SECURITY INVOKER means this function respects the same owner-only RLS.
create or replace function public.save_resume_analysis(
  p_id uuid, p_series_id uuid, p_title text, p_source_name text, p_source_type text, p_result jsonb
) returns jsonb language plpgsql security invoker set search_path = public as $$
declare
  owner_id uuid := auth.uid();
  next_version integer;
  canonical_title text;
  saved public.analyses;
begin
  if owner_id is null then raise exception 'Authentication required'; end if;
  perform pg_advisory_xact_lock(hashtextextended(owner_id::text || p_series_id::text, 0));
  select * into saved from public.analyses where id = p_id and user_id = owner_id;
  if found then return to_jsonb(saved); end if;
  select coalesce(max(version), 0) + 1 into next_version from public.analyses
    where user_id = owner_id and series_id = p_series_id;
  select title into canonical_title from public.analyses
    where user_id = owner_id and series_id = p_series_id order by version limit 1;
  insert into public.analyses (id, user_id, series_id, title, version, source_name, source_type, result)
    values (p_id, owner_id, p_series_id, coalesce(canonical_title, p_title), next_version, p_source_name, p_source_type, p_result)
    returning * into saved;
  return to_jsonb(saved);
end;
$$;
revoke all on function public.save_resume_analysis(uuid,uuid,text,text,text,jsonb) from public, anon;
grant execute on function public.save_resume_analysis(uuid,uuid,text,text,text,jsonb) to authenticated;
commit;

