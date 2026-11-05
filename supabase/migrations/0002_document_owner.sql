-- Per-user ownership. The API filters on owner_id for every read, delete and search.
-- Existing rows keep owner_id NULL: they stay hidden from users unless is_sample = true.
-- To hand old documents to a user, run:  update public.documents set owner_id = '<auth user uuid>' where owner_id is null;

alter table public.documents
  add column if not exists owner_id uuid references auth.users(id) on delete cascade;

create index if not exists documents_owner_id_idx on public.documents (owner_id);

-- Defense in depth: the API uses the service-role key (bypasses RLS), but turning RLS on
-- means the public anon key can never read these tables directly.
alter table public.documents enable row level security;
alter table public.chunks enable row level security;

drop policy if exists documents_owner_read on public.documents;
create policy documents_owner_read on public.documents
  for select to authenticated
  using (owner_id = auth.uid() or is_sample);

drop policy if exists chunks_owner_read on public.chunks;
create policy chunks_owner_read on public.chunks
  for select to authenticated
  using (exists (
    select 1 from public.documents d
    where d.id = chunks.document_id and (d.owner_id = auth.uid() or d.is_sample)
  ));
