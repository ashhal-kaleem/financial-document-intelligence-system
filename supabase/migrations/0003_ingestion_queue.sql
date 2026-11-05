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

-- Fencing. claim_next_document bumps `attempts`; that number is the worker's fencing token.
-- Every worker write below checks "I still hold attempt N" under a row lock, so a worker that
-- lost its lease (crash recovery, or a stall longer than the lease) can no longer change anything.
-- Heartbeats keep a live worker's lease fresh, so a lease only expires if the worker is really gone.

create or replace function public.heartbeat_document(p_id uuid, p_attempt int)
returns boolean language plpgsql as $$
begin
  update public.documents set claimed_at = now()
   where id = p_id and attempts = p_attempt and status = 'processing';
  return found;
end $$;

create or replace function public.clear_chunks_fenced(p_id uuid, p_attempt int)
returns boolean language plpgsql as $$
begin
  perform 1 from public.documents
   where id = p_id and attempts = p_attempt and status = 'processing' for update;
  if not found then return false; end if;
  delete from public.chunks where document_id = p_id;
  return true;
end $$;

-- p_rows: JSON array of chunk objects; "embedding" is the vector as text, e.g. "[0.1,0.2,...]".
create or replace function public.insert_chunks_fenced(p_id uuid, p_attempt int, p_rows jsonb)
returns boolean language plpgsql as $$
begin
  perform 1 from public.documents
   where id = p_id and attempts = p_attempt and status = 'processing' for update;
  if not found then return false; end if;
  insert into public.chunks (document_id, content, source, page, chunk_index, total_chunks, metadata, embedding)
  select p_id, r.content, r.source, r.page, r.chunk_index, r.total_chunks,
         coalesce(r.metadata, '{}'::jsonb), r.embedding::vector
    from jsonb_to_recordset(p_rows) as r(
      content text, source text, page int, chunk_index int, total_chunks int, metadata jsonb, embedding text);
  return true;
end $$;

create or replace function public.finish_document(
  p_id uuid, p_attempt int, p_status text, p_error text, p_pages int, p_chunks int
)
returns boolean language plpgsql as $$
begin
  update public.documents
     set status = p_status, error_message = p_error,
         page_count = coalesce(p_pages, page_count), chunk_count = coalesce(p_chunks, chunk_count)
   where id = p_id and attempts = p_attempt and status = 'processing';
  return found;
end $$;

-- Queue functions are for the backend (service role) only, never the public API keys.
revoke execute on function public.claim_next_document(int, int) from public, anon, authenticated;
revoke execute on function public.heartbeat_document(uuid, int) from public, anon, authenticated;
revoke execute on function public.clear_chunks_fenced(uuid, int) from public, anon, authenticated;
revoke execute on function public.insert_chunks_fenced(uuid, int, jsonb) from public, anon, authenticated;
revoke execute on function public.finish_document(uuid, int, text, text, int, int) from public, anon, authenticated;
revoke execute on function public.fail_stale_documents(int, int) from public, anon, authenticated;
grant execute on function public.claim_next_document(int, int) to service_role;
grant execute on function public.heartbeat_document(uuid, int) to service_role;
grant execute on function public.clear_chunks_fenced(uuid, int) to service_role;
grant execute on function public.insert_chunks_fenced(uuid, int, jsonb) to service_role;
grant execute on function public.finish_document(uuid, int, text, text, int, int) to service_role;
grant execute on function public.fail_stale_documents(int, int) to service_role;
