-- Run the entire script in Supabase SQL Editor. Existing application/private
-- runtime tables and data are retained. No table is dropped or truncated.
begin;
create table if not exists public.server_runtime_state (
  kind text not null check(kind in ('session','draft','chat')),
  key text not null check(key ~ '^[a-f0-9]{64}$'),
  owner text not null check(char_length(owner) between 1 and 254),
  payload jsonb not null,
  expires double precision not null,
  primary key(kind,key,owner)
);
create index if not exists server_runtime_expiry on public.server_runtime_state(expires);
create table if not exists public.server_rate_limits (
  bucket text primary key check(bucket ~ '^[a-f0-9]{64}$'),
  count integer not null check(count>=1),
  reset double precision not null
);
alter table public.server_runtime_state enable row level security;
alter table public.server_rate_limits enable row level security;
-- No anon/authenticated policies. Only backend service_role can access.
revoke all on public.server_runtime_state,public.server_rate_limits from public,anon,authenticated;
grant usage on schema public to service_role;
grant select,insert,update,delete on public.server_runtime_state to service_role;
grant select,insert,update on public.server_rate_limits to service_role;

-- INVOKER: service_role already has the needed grants and bypasses RLS.
-- One UPSERT holds the row lock: no read-then-write race between instances.
create or replace function public.runtime_rate_allow(p_bucket text,p_maximum integer,p_window integer)
returns boolean language plpgsql security invoker set search_path='' as $$
declare
  stamp double precision := extract(epoch from pg_catalog.clock_timestamp());
  allowed_count integer;
begin
  if p_bucket is null or p_bucket !~ '^[a-f0-9]{64}$'
     or p_maximum is null or p_maximum<1 or p_maximum>100000
     or p_window is null or p_window<1 or p_window>604800 then
    raise exception 'Invalid runtime limit arguments';
  end if;
  insert into public.server_rate_limits as limits(bucket,count,reset)
  values(p_bucket,1,stamp+p_window)
  on conflict(bucket) do update set
    count=case when limits.reset<=stamp then 1 else limits.count+1 end,
    reset=case when limits.reset<=stamp then excluded.reset else limits.reset end
  where limits.reset<=stamp or limits.count<p_maximum
  returning count into allowed_count;
  return allowed_count is not null;
end;
$$;
revoke all on function public.runtime_rate_allow(text,integer,integer) from public,anon,authenticated;
grant execute on function public.runtime_rate_allow(text,integer,integer) to service_role;
notify pgrst,'reload schema';
commit;
-- New runtime tables start empty. Existing private-schema state is preserved,
-- but not automatically copied: active cloud users must sign in again and old
-- unfinished review drafts/chats are not read by the new adapter.
-- Periodic cleanup through SQL Editor or your existing scheduler:
-- DELETE FROM public.server_runtime_state WHERE expires<extract(epoch from now());
-- DELETE FROM public.server_rate_limits WHERE reset<extract(epoch from now());
