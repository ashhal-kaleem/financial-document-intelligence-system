"""Applies supabase/migrations to a throwaway local Postgres (with pgvector) and checks behavior.
Run:  uv run --with pgserver --with psycopg2-binary python scripts/test_migrations.py
It stubs the Supabase pieces (auth schema, auth.uid(), anon/authenticated/service_role roles).
It never connects to any hosted database."""
import glob, os, random, shutil, sys, tempfile, uuid
import pgserver, psycopg2

ROOT = os.path.join(os.path.dirname(__file__), "..")
STUB = """
create schema if not exists auth;
create table if not exists auth.users (id uuid primary key);
create or replace function auth.uid() returns uuid language sql stable as
  $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
do $$ begin
  create role anon nologin; exception when duplicate_object then null; end $$;
do $$ begin
  create role authenticated nologin; exception when duplicate_object then null; end $$;
do $$ begin
  create role service_role nologin bypassrls; exception when duplicate_object then null; end $$;
grant usage on schema public, auth to anon, authenticated, service_role;
"""
fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

tmp = tempfile.mkdtemp()
srv = pgserver.get_server(tmp, cleanup_mode="delete")
def conn():
    c = psycopg2.connect(srv.get_uri()); c.autocommit = True; return c
db = conn(); cur = db.cursor()
cur.execute(STUB)
files = sorted(glob.glob(os.path.join(ROOT, "supabase/migrations/*.sql")))
for round_ in (1, 2):  # second round proves idempotency
    for f in files:
        cur.execute(open(f).read())
check(f"applied {len(files)} migrations twice (idempotent)", True)
cur.execute("grant all on all tables in schema public to service_role; grant select on all tables in schema public to authenticated")

A, B = str(uuid.uuid4()), str(uuid.uuid4())
for u in (A, B): cur.execute("insert into auth.users values (%s)", (u,))
vec = lambda seed: "[" + ",".join(str(round(random.Random(seed + i).random(), 4)) for i in range(384)) + "]"
docs = {}
for name, owner, sample in (("a", A, False), ("b", B, False), ("s", None, True)):
    d = str(uuid.uuid4()); docs[name] = d
    cur.execute("insert into documents (id, filename, owner_id, is_sample, status) values (%s,%s,%s,%s,'ready')", (d, name + ".pdf", owner, sample))
    cur.execute("insert into chunks (document_id, content, source, page, chunk_index, total_chunks, embedding) values (%s,'x',%s,1,0,1,%s::vector)", (d, name + ".pdf", vec(ord(name))))

cur.execute("select count(*) from match_chunks(%s::vector, 0.0, 10, null)", (vec(ord('a')),))
check("match_chunks returns all docs when unscoped", cur.fetchone()[0] == 3)
cur.execute("select document_id::text from match_chunks(%s::vector, 0.0, 10, %s::uuid[])", (vec(ord('a')), [docs["a"]]))
check("match_chunks scoped to p_document_ids", [r[0] for r in cur.fetchall()] == [docs["a"]])
cur.execute("select count(*) from match_chunks(%s::vector, 0.99999, 10, null)", (vec(1),))
check("match_chunks honors threshold", cur.fetchone()[0] == 0)

def as_role(role, uid=None):
    c = conn(); k = c.cursor()
    k.execute(f"set role {role}")
    if uid: k.execute("select set_config('request.jwt.claim.sub', %s, false)", (uid,))
    return k
k = as_role("authenticated", A); k.execute("select filename from documents order by filename")
check("RLS: user A sees own + sample, not B", [r[0] for r in k.fetchall()] == ["a.pdf", "s.pdf"])
k.execute("select count(*) from chunks"); check("RLS: user A sees only own+sample chunks", k.fetchone()[0] == 2)
k = as_role("anon"); 
try:
    k.execute("select count(*) from documents"); denied = False
except psycopg2.errors.InsufficientPrivilege: denied = True
check("anon cannot read documents", denied)

# queue
q = str(uuid.uuid4())
cur.execute("insert into documents (id, filename, owner_id, status) values (%s,'q.pdf',%s,'queued')", (q, A))
cur.execute("select id::text, status, attempts from claim_next_document(600, 3)")
row = cur.fetchone()
check("claim returns the queued job as processing, attempts=1", row == (q, "processing", 1))
cur.execute("select count(*) from claim_next_document(600, 3)"); check("same job is not claimed twice", cur.fetchone()[0] == 0)
cur.execute("update documents set claimed_at = now() - interval '20 minutes' where id=%s", (q,))
cur.execute("select attempts from claim_next_document(600, 3)"); check("stale job is re-claimed, attempts=2", cur.fetchone()[0] == 2)
cur.execute("update documents set claimed_at = now() - interval '20 minutes', attempts = 3 where id=%s", (q,))
cur.execute("select count(*) from claim_next_document(600, 3)"); check("job at max attempts is not re-claimed", cur.fetchone()[0] == 0)
cur.execute("select fail_stale_documents(600, 3)"); check("fail_stale marks exactly 1 job", cur.fetchone()[0] == 1)
cur.execute("select status, error_message from documents where id=%s", (q,))
check("exhausted job is error with generic message", cur.fetchone() == ("error", "Ingestion failed after repeated attempts."))

# two workers racing for two jobs never share one
j = [str(uuid.uuid4()) for _ in range(2)]
for x in j: cur.execute("insert into documents (id, filename, owner_id, status) values (%s,'r.pdf',%s,'queued')", (x, A))
c1, c2 = conn(), conn()
for c in (c1, c2): c.autocommit = False
k1, k2 = c1.cursor(), c2.cursor()
k1.execute("select id::text from claim_next_document(600,3)"); k2.execute("select id::text from claim_next_document(600,3)")
g1, g2 = k1.fetchall(), k2.fetchall(); c1.commit(); c2.commit()
check("concurrent claims get different jobs (skip locked)", len(g1) == 1 and len(g2) == 1 and g1 != g2)

# fencing: a worker that lost its lease cannot write
f = str(uuid.uuid4())
cur.execute("insert into documents (id, filename, owner_id, status) values (%s,'f.pdf',%s,'queued')", (f, A))
cur.execute("select attempts from claim_next_document(600,3) where id = %s", (f,))
# the queue may hand out an older job first; drain until ours is claimed
got = cur.fetchone()
while got is None:
    cur.execute("select attempts from claim_next_document(600,3) where id = %s", (f,)); got = cur.fetchone()
    if got is None:
        cur.execute("select count(*) from documents where status='queued'")
        if cur.fetchone()[0] == 0: break
cur.execute("select attempts, status from documents where id=%s", (f,)); att, st = cur.fetchone()
rows = '[{"content":"c","source":"f.pdf","page":1,"chunk_index":0,"total_chunks":1,"metadata":{},"embedding":"%s"}]' % vec(7)
cur.execute("select heartbeat_document(%s,%s)", (f, att)); check("heartbeat succeeds for the lease holder", cur.fetchone()[0])
cur.execute("select clear_chunks_fenced(%s,%s)", (f, att)); check("clear_chunks_fenced ok for holder", cur.fetchone()[0])
cur.execute("select insert_chunks_fenced(%s,%s,%s::jsonb)", (f, att, rows)); check("insert_chunks_fenced ok for holder", cur.fetchone()[0])
cur.execute("select count(*) from chunks where document_id=%s", (f,)); check("fenced insert stored the chunk (vector parsed)", cur.fetchone()[0] == 1)
# lease expires and a second worker re-claims
cur.execute("update documents set claimed_at = now() - interval '20 minutes' where id=%s", (f,))
cur.execute("select attempts from claim_next_document(600,3) where id = %s", (f,)); new_att = cur.fetchone()[0]
check("re-claim bumps the fencing token", new_att == att + 1)
cur.execute("select heartbeat_document(%s,%s)", (f, att)); check("old worker heartbeat rejected", cur.fetchone()[0] is False)
cur.execute("select clear_chunks_fenced(%s,%s)", (f, att)); check("old worker cannot clear chunks", cur.fetchone()[0] is False)
cur.execute("select insert_chunks_fenced(%s,%s,%s::jsonb)", (f, att, rows)); check("old worker cannot insert chunks", cur.fetchone()[0] is False)
cur.execute("select finish_document(%s,%s,'ready',null,1,1)", (f, att)); check("old worker cannot finish the job", cur.fetchone()[0] is False)
cur.execute("select count(*) from chunks where document_id=%s", (f,)); check("old worker left chunks untouched", cur.fetchone()[0] == 1)
cur.execute("select finish_document(%s,%s,'ready',null,1,1)", (f, new_att)); check("new worker can finish", cur.fetchone()[0])
cur.execute("select status, page_count, chunk_count from documents where id=%s", (f,)); check("job is ready with counts", cur.fetchone() == ("ready", 1, 1))
cur.execute("select finish_document(%s,%s,'error','x',null,null)", (f, new_att)); check("finished job cannot be overwritten", cur.fetchone()[0] is False)

k = as_role("anon")
try:
    k.execute("select * from claim_next_document()"); blocked = False
except psycopg2.errors.InsufficientPrivilege: blocked = True
check("anon cannot call claim_next_document", blocked)
k = as_role("authenticated", A)
try:
    k.execute("select * from claim_next_document()"); blocked = False
except psycopg2.errors.InsufficientPrivilege: blocked = True
check("authenticated cannot call claim_next_document", blocked)
k = as_role("authenticated", A)
try:
    k.execute("select finish_document(%s,1,'ready',null,1,1)", (f,)); blocked = False
except psycopg2.errors.InsufficientPrivilege: blocked = True
check("authenticated cannot call fenced functions", blocked)
k = as_role("service_role"); k.execute("select count(*) from claim_next_document()"); check("service_role can call claim_next_document", True)

# Two-phase deletion hides rows, fences queue claims and retains the row until Storage succeeds.
t = str(uuid.uuid4())
cur.execute("insert into documents (id,filename,owner_id,status) values (%s,'delete.pdf',%s,'queued')", (t,A))
cur.execute("select count(*) from begin_document_delete(%s,%s)",(t,B)); check("delete cannot claim another owner's document",cur.fetchone()[0]==0)
cur.execute("select status from begin_document_delete(%s,%s)",(t,A)); check("delete atomically marks queued row",cur.fetchone()[0]=='deleting')
k=as_role("authenticated",A);k.execute("select count(*) from documents where id=%s",(t,));check("deleting row hidden by RLS",k.fetchone()[0]==0)
cur.execute("select heartbeat_document(%s,0)",(t,));check("deleting row cannot be heartbeated",cur.fetchone()[0] is False)
cur.execute("select count(*) from begin_document_delete(%s,%s)",(t,A));check("delete can be retried",cur.fetchone()[0]==1)
cur.execute("delete from documents where id=%s",(t,))
k=as_role("authenticated",A)
try:
    k.execute("select * from begin_document_delete(%s,%s)",(f,A));blocked=False
except psycopg2.errors.InsufficientPrivilege:blocked=True
check("authenticated cannot call service delete function",blocked)

shutil.rmtree(tmp, ignore_errors=True)
print(f"\n{len(fails)} failed"); sys.exit(1 if fails else 0)
