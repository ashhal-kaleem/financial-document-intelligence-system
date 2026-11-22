-- Refund one daily question unit (per-guest and global) after an answer fails
-- server-side. Mirrors take_question_quota's two increments exactly, floored
-- at zero so a refund can never drive a counter negative. One refund per
-- failed request is enforced by the caller structure; the decrements
-- themselves are single atomic UPDATEs, race-safe under concurrency.
create or replace function public.refund_question_quota(p_owner uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_global uuid := 'ffffffff-ffff-ffff-ffff-ffffffffffff';
begin
  update public.ask_usage
     set question_count = greatest(question_count - 1, 0)
   where owner_id = v_global and day = current_date;

  update public.ask_usage
     set question_count = greatest(question_count - 1, 0)
   where owner_id = p_owner and day = current_date;
end;
$$;

revoke all on function public.refund_question_quota(uuid) from public, anon, authenticated;
grant execute on function public.refund_question_quota(uuid) to service_role;
