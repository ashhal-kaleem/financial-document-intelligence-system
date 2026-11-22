-- Orphaned anonymous identities: a guest who closes the tab abandons their
-- anonymous auth user. Expired uploads are swept separately; once a guest owns
-- no documents and is older than the retention window, the identity itself is
-- safe to delete. Runs from the scheduled sweep only (service role).
create or replace function public.sweep_orphaned_guest_users(max_rows int default 100)
returns int
language plpgsql
security definer
set search_path = public
as $$
declare
  deleted_count int;
begin
  with victims as (
    select u.id
    from auth.users u
    where u.is_anonymous
      and u.created_at < now() - interval '25 hours'
      and not exists (select 1 from public.documents d where d.owner_id = u.id)
    limit max_rows
  ), del as (
    delete from auth.users u using victims v where u.id = v.id returning u.id
  )
  select count(*) into deleted_count from del;
  return deleted_count;
end;
$$;

revoke all on function public.sweep_orphaned_guest_users(int) from public, anon, authenticated;
grant execute on function public.sweep_orphaned_guest_users(int) to service_role;
