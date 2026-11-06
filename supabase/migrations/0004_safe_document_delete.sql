-- Reviewed source proposal only. Not applied to a hosted project by this change.
-- Deletion is two-phase because Storage and Postgres cannot share a transaction.
-- Mark deleting under a row lock to fence queue writes, hide reads and retain a retry handle.
create or replace function public.begin_document_delete(p_id uuid, p_owner uuid)
returns setof public.documents language plpgsql as $$
declare d public.documents;
begin
  select * into d from public.documents
   where id = p_id and owner_id = p_owner and not is_sample for update;
  if not found then return; end if;
  -- Do not race an inline upload or a storage write still in progress.
  if d.status in ('uploaded', 'processing') then
    raise exception 'Document is busy' using errcode = '55000';
  end if;
  update public.documents set status = 'deleting' where id = p_id;
  return query select * from public.documents where id = p_id;
end $$;
revoke execute on function public.begin_document_delete(uuid,uuid) from public, anon, authenticated;
grant execute on function public.begin_document_delete(uuid,uuid) to service_role;

-- A failed Storage delete remains retryable but is not available to retrieval or direct RLS reads.
drop policy if exists documents_owner_read on public.documents;
create policy documents_owner_read on public.documents for select to authenticated
  using (status <> 'deleting' and (owner_id = auth.uid() and not is_sample));
drop policy if exists chunks_owner_read on public.chunks;
create policy chunks_owner_read on public.chunks for select to authenticated using (exists (
  select 1 from public.documents d where d.id = chunks.document_id
    and d.status <> 'deleting' and (d.owner_id = auth.uid() and not d.is_sample)
));
