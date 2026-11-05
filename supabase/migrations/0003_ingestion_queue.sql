-- Durable ingestion queue on the documents table. Upload stores the PDF and inserts a row with
-- status = 'queued'; a worker claims rows with claim_next_document(). State lives in Postgres, so a
-- restart loses nothing: rows stuck in 'processing' past the lease are claimed again, up to a cap.
-- Assumes 0001 and 0002 are applied. Not applied anywhere yet.

alter table public.documents
  add column if not exists claimed_at timestamptz,
  add column if not exists attempts integer not null default 0;

create index if not exists documents_queue_idx
  on public.documents (created_at) where status in ('queued', 'processing');

-- Claims one job. skip locked lets several workers run without taking the same row.
create or replace function public.claim_next_document(
  p_stale_seconds int default 600,
  p_max_attempts int default 3
)
returns setof public.documents
language sql
as $$
  with next as (
    select id from public.documents
    where status = 'queued'
       or (status = 'processing'
           and claimed_at < now() - make_interval(secs => p_stale_seconds)
           and attempts < p_max_attempts)
    order by created_at
    for update skip locked
    limit 1
  )
  update public.documents d
     set status = 'processing', claimed_at = now(), attempts = d.attempts + 1
    from next
   where d.id = next.id
  returning d.*;
$$;

-- Jobs whose lease expired after the last allowed attempt become errors instead of looping.
create or replace function public.fail_stale_documents(
  p_stale_seconds int default 600,
  p_max_attempts int default 3
)
returns integer
language sql
as $$
  with failed as (
    update public.documents
       set status = 'error',
           error_message = 'Ingestion failed after repeated attempts.'
     where status = 'processing'
       and claimed_at < now() - make_interval(secs => p_stale_seconds)
       and attempts >= p_max_attempts
    returning 1
  )
  select count(*)::int from failed;
$$;

-- Queue functions are for the backend (service role) only, never the public API keys.
revoke execute on function public.claim_next_document(int, int) from public, anon, authenticated;
revoke execute on function public.fail_stale_documents(int, int) from public, anon, authenticated;
grant execute on function public.claim_next_document(int, int) to service_role;
grant execute on function public.fail_stale_documents(int, int) to service_role;
