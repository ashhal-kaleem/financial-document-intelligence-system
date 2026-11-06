-- Source proposal only. Apply separately after review; no records are deleted.
-- Applies strict own-data-only reads even if 0004 was applied before this correction.
begin;
drop policy if exists documents_owner_read on public.documents;
create policy documents_owner_read on public.documents for select to authenticated
 using (owner_id = auth.uid() and not is_sample and status <> 'deleting');
drop policy if exists chunks_owner_read on public.chunks;
create policy chunks_owner_read on public.chunks for select to authenticated using (exists (
 select 1 from public.documents d where d.id = chunks.document_id
 and d.owner_id = auth.uid() and not d.is_sample and d.status <> 'deleting'
));
commit;
