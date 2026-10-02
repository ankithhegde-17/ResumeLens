-- Run once in Supabase SQL Editor. No public tables or existing rows replaced.
-- Used ONLY through a server-held Postgres connection, not the browser/Data API.
begin;
create schema if not exists resumelens_private;
revoke all on schema resumelens_private from public, anon, authenticated;
create table if not exists resumelens_private.runtime_state (
  kind text not null check(kind in ('session','draft','chat')),
  key text not null,
  owner text not null,
  payload jsonb not null,
  expires double precision not null,
  primary key(kind,key)
);
create index if not exists runtime_expiry on resumelens_private.runtime_state(expires);
create table if not exists resumelens_private.rate_limits (
  bucket text primary key,
  count integer not null,
  reset double precision not null
);
alter table resumelens_private.runtime_state enable row level security;
alter table resumelens_private.rate_limits enable row level security;
revoke all on all tables in schema resumelens_private from public, anon, authenticated;
-- Optional least-privilege runtime login: use its transaction-pooler URL.
-- Provision its password privately, never in this migration or Git.
do $$ begin
  if not exists(select 1 from pg_roles where rolname='resumelens_runtime') then
    create role resumelens_runtime login;
  end if;
end $$;
grant usage on schema resumelens_private to resumelens_runtime;
grant select,insert,update,delete on all tables in schema resumelens_private to resumelens_runtime;
drop policy if exists runtime_backend on resumelens_private.runtime_state;
create policy runtime_backend on resumelens_private.runtime_state for all to resumelens_runtime using(true) with check(true);
drop policy if exists limits_backend on resumelens_private.rate_limits;
create policy limits_backend on resumelens_private.rate_limits for all to resumelens_runtime using(true) with check(true);
commit;
-- Housekeeping (run periodically through SQL Editor or your existing scheduler):
-- DELETE FROM resumelens_private.runtime_state WHERE expires < extract(epoch from now());
-- DELETE FROM resumelens_private.rate_limits WHERE reset < extract(epoch from now());
