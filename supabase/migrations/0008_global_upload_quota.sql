-- Global daily upload admission budget: anonymous sign-in is scriptable, so
-- per-guest limits alone cannot protect shared free-tier storage, database
-- rows and ingestion CPU. One atomic row per UTC day, service role only.
create table if not exists public.upload_usage (
  day date primary key,
  doc_count int not null default 0,
  byte_count bigint not null default 0
);
alter table public.upload_usage enable row level security;

create or replace function public.take_upload_quota(p_bytes bigint, p_max_docs int, p_max_bytes bigint)
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  row_docs int;
  row_bytes bigint;
begin
  insert into public.upload_usage (day, doc_count, byte_count)
  values (current_date, 0, 0)
  on conflict (day) do nothing;
  select doc_count, byte_count into row_docs, row_bytes
  from public.upload_usage where day = current_date for update;
  if row_docs >= p_max_docs then
    return 'docs_exhausted';
  end if;
  if row_bytes + p_bytes > p_max_bytes then
    return 'bytes_exhausted';
  end if;
  update public.upload_usage
  set doc_count = doc_count + 1, byte_count = byte_count + p_bytes
  where day = current_date;
  return 'ok';
end;
$$;

revoke all on function public.take_upload_quota(bigint, int, bigint) from public, anon, authenticated;
grant execute on function public.take_upload_quota(bigint, int, bigint) to service_role;
