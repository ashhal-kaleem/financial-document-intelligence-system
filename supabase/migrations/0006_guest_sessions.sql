-- Guest sessions for the public no-login deployment.
-- 1. Anonymous-guest upload expiry marker (NULL = never expires; named accounts keep their documents).
-- 2. Atomic daily answer quotas: per guest and one global row, keeping all guests
--    combined under the Groq free plan's daily token budget. Counting happens only
--    when an answer is actually attempted (after retrieval found context).

alter table public.documents
  add column if not exists session_expires_at timestamptz;

create index if not exists documents_session_expires_at_idx
  on public.documents (session_expires_at)
  where session_expires_at is not null;

create table if not exists public.ask_usage (
  owner_id       uuid not null,
  day            date not null,
  question_count integer not null default 0,
  primary key (owner_id, day)
);

-- Service role only: no read or write policies for anon/authenticated.
alter table public.ask_usage enable row level security;

-- Counts one answer attempt atomically. The global row uses a fixed uuid that can
-- never be a real auth user. If the per-guest limit is full, the global increment
-- is rolled back so one heavy guest cannot burn the shared budget.
create or replace function public.take_question_quota(p_owner uuid, p_user_limit int, p_global_limit int)
returns text
language plpgsql
as $$
declare
  v_global uuid := 'ffffffff-ffff-ffff-ffff-ffffffffffff';
  v_count int;
begin
  insert into public.ask_usage (owner_id, day, question_count)
  values (v_global, current_date, 0)
  on conflict (owner_id, day) do nothing;

  update public.ask_usage
     set question_count = question_count + 1
   where owner_id = v_global and day = current_date and question_count < p_global_limit
   returning question_count into v_count;
  if not found then
    return 'global_exhausted';
  end if;

  insert into public.ask_usage (owner_id, day, question_count)
  values (p_owner, current_date, 0)
  on conflict (owner_id, day) do nothing;

  update public.ask_usage
     set question_count = question_count + 1
   where owner_id = p_owner and day = current_date and question_count < p_user_limit
   returning question_count into v_count;
  if not found then
    update public.ask_usage
       set question_count = question_count - 1
     where owner_id = v_global and day = current_date;
    return 'user_exhausted';
  end if;

  return 'ok';
end $$;

revoke execute on function public.take_question_quota(uuid, int, int) from public, anon, authenticated;
grant execute on function public.take_question_quota(uuid, int, int) to service_role;
