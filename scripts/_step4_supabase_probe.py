"""Step 4 -- Supabase real connectivity probe.

6 checks: connect, table, RPC, insert, retrieve, delete.
Never prints URL or key.  Exit 0 = all passed.
"""
from __future__ import annotations
import os, sys, textwrap, traceback
import numpy as np
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
TABLE        = os.getenv("SUPABASE_TABLE", "chunks")
RPC_FN       = os.getenv("SUPABASE_RPC",   "match_chunks")

_results: list[tuple[str, bool, str]] = []

def step(name, ok, detail=""):
    _results.append((name, ok, detail))
    tag = "  PASS" if ok else "  FAIL"
    msg = f"{tag}  {name}"
    if detail:
        msg += "\n         " + textwrap.shorten(str(detail), 120)
    print(msg)

def abort(name, exc):
    step(name, False, type(exc).__name__ + ": " + str(exc))
    _summary(); sys.exit(1)

def _summary():
    passed = sum(1 for _, ok, _ in _results if ok)
    total  = len(_results)
    print("\n" + "="*52)
    print(f"  {passed}/{total} checks passed")
    if passed < total:
        print("  Failed:", [n for n, ok, _ in _results if not ok])
    print("="*52)

# --- check 0: env vars ---
print("\n-- Prerequisites --")
if not SUPABASE_URL or "PLACEHOLDER" in SUPABASE_URL:
    print("  FAIL  SUPABASE_URL missing"); sys.exit(1)
if not SUPABASE_KEY or "PLACEHOLDER" in SUPABASE_KEY:
    print("  FAIL  SUPABASE_KEY missing"); sys.exit(1)
step("env vars present", True,
     f"url_len={len(SUPABASE_URL)} key_len={len(SUPABASE_KEY)} vs=supabase")

# --- check 1: client construction ---
print("\n-- Check 1: client construction --")
try:
    from supabase import create_client, Client
    client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    step("supabase client created", True)
except Exception as exc:
    abort("supabase client created", exc)

# --- check 2: chunks table reachable ---
print("\n-- Check 2: chunks table --")
try:
    resp = client.table(TABLE).select("id", count="exact").limit(1).execute()
    cnt = resp.count if resp.count is not None else len(resp.data or [])
    step("chunks table reachable", True, f"existing row count approx {cnt}")
except Exception as exc:
    msg = str(exc)
    if "PGRST125" in msg or "Invalid path" in msg:
        step("chunks table reachable", False,
             "Table 'chunks' does not exist -- run scripts/supabase_schema.sql in the SQL Editor")
    else:
        step("chunks table reachable", False, type(exc).__name__ + ": " + msg[:120])
    _summary(); sys.exit(1)

# --- check 3: match_chunks RPC ---
print("\n-- Check 3: match_chunks RPC --")
try:
    dummy = [0.0] * 384; dummy[0] = 1.0
    resp = client.rpc(RPC_FN, {
        "query_embedding": dummy,
        "match_threshold": 0.99,
        "match_count": 1,
    }).execute()
    step("match_chunks RPC callable", True,
         f"returned {len(resp.data or [])} rows at threshold 0.99")
except Exception as exc:
    abort("match_chunks RPC callable", exc)

# --- check 4: insert test chunk ---
print("\n-- Check 4: insert test chunk --")
TEST_SOURCE = "__step4_probe__"
tv = np.zeros(384, dtype=np.float32); tv[7] = 0.6; tv[42] = 0.8
row = {
    "content":      "PROBE: temp test chunk for Step 4 connectivity check.",
    "source":       TEST_SOURCE,
    "page":         0,
    "chunk_index":  0,
    "total_chunks": 1,
    "metadata":     {"probe": True},
    "embedding":    tv.tolist(),
}
inserted_id = None
try:
    resp = client.table(TABLE).insert(row).execute()
    data = resp.data or []
    if not data:
        raise RuntimeError("Insert returned empty data -- check table permissions / RLS.")
    inserted_id = data[0]["id"]
    step("test chunk inserted", True, f"id={inserted_id}")
except Exception as exc:
    abort("test chunk inserted", exc)

# --- check 5: retrieve via SupabaseVectorStore ---
print("\n-- Check 5: retrieve via SupabaseVectorStore --")
try:
    sys.path.insert(0, "src")
    from financial_rag.retrieval.supabase_vector_store import SupabaseVectorStore
    from financial_rag.embeddings.mock import MockEmbedder

    store = SupabaseVectorStore(SUPABASE_URL, SUPABASE_KEY, table=TABLE, rpc_fn=RPC_FN)
    embedder = MockEmbedder(dim=384)
    results = store.search("probe chunk test", embedder, top_k=10, score_threshold=0.0)
    found = any(r.chunk.source == TEST_SOURCE for r in results)
    step("SupabaseVectorStore.search works", True,
         f"RPC returned {len(results)} result(s); probe row in set: {found}")
except Exception as exc:
    step("SupabaseVectorStore.search works", False, traceback.format_exc(limit=3))

# --- check 6: delete test chunk ---
print("\n-- Check 6: delete test chunk --")
try:
    if inserted_id is not None:
        del_resp = client.table(TABLE).delete().eq("id", inserted_id).execute()
        deleted  = del_resp.data or []
        if deleted:
            step("test chunk deleted", True, f"id={inserted_id} removed")
        else:
            verify = client.table(TABLE).select("id").eq("id", inserted_id).execute()
            gone   = len(verify.data or []) == 0
            step("test chunk deleted", gone,
                 "row gone (DELETE returned empty -- ok)" if gone
                 else "row still present -- check RLS delete policy")
    else:
        step("test chunk deleted", False, "nothing to delete (insert failed earlier)")
except Exception as exc:
    step("test chunk deleted", False, str(exc))

# safety-net cleanup by source tag
try:
    leftover = client.table(TABLE).select("id").eq("source", TEST_SOURCE).execute()
    if leftover.data:
        client.table(TABLE).delete().eq("source", TEST_SOURCE).execute()
        print(f"  NOTE  safety-net removed {len(leftover.data)} leftover probe row(s)")
except Exception:
    pass

# --- summary ---
_summary()
sys.exit(0 if all(ok for _, ok, _ in _results) else 1)
