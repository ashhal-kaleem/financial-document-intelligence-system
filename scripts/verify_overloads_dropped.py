"""Verify obsolete RPC overloads have been dropped."""
import os, re
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
client = create_client(url, key)

dummy_vec = [0.0] * 384

print("=== OVERLOAD CHECK ===")

# Attempt 4-arg call — after cleanup this should either:
#   a) work (only 1 function left, 4-arg call resolves to 5-arg with default NULL)
#   b) fail with PGRST202 (function not found) — old 4-arg is gone AND 5-arg needs explicit param
# Either way, PGRST203 "Could not choose" must NOT appear.

for fn, base_params in [
    ("match_chunks_hybrid", {
        "query_embedding": dummy_vec,
        "query_text": "test",
        "match_threshold": 0.99,
        "match_count": 1,
    }),
    ("match_chunks", {
        "query_embedding": dummy_vec,
        "match_threshold": 0.99,
        "match_count": 1,
    }),
]:
    try:
        r = client.rpc(fn, base_params).execute()
        print(f"  {fn} (4-arg call): resolved OK — only 1 overload remains. PASS")
    except Exception as e:
        msg = str(e)
        if "PGRST203" in msg or "Could not choose" in msg:
            # Extract overloads from error
            sigs = re.findall(rf"public\.{fn}\([^)]+\)", msg)
            print(f"  {fn} (4-arg call): STILL AMBIGUOUS — {len(sigs)} overloads. FAIL")
            for s in sigs:
                print(f"    {s}")
        elif "PGRST202" in msg or "not found" in msg.lower():
            print(f"  {fn} (4-arg call): function requires explicit params (old 4-arg dropped). Checking 5-arg...")
        else:
            print(f"  {fn} (4-arg call): unexpected error — {msg[:120]}")

    # Always verify 5-arg still works
    try:
        r5 = client.rpc(fn, {**base_params, "p_document_ids": None}).execute()
        print(f"  {fn} (5-arg, p_doc_ids=NULL): OK ({len(r5.data or [])} rows). PASS")
    except Exception as e:
        print(f"  {fn} (5-arg, p_doc_ids=NULL): FAIL — {str(e)[:120]}")
