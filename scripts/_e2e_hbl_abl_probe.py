"""Full E2E probe: HBL + ABL factual, strategic, and out-of-scope questions."""
from __future__ import annotations
import os, re, sys, textwrap, time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
from financial_rag.pipeline.factory import create_pipeline

SUPABASE_URL   = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "chunks")
SUPABASE_RPC   = os.getenv("SUPABASE_RPC",   "match_chunks_hybrid")
GROQ_KEY       = os.getenv("GROQ_API_KEY",   "")
GROQ_MODEL     = os.getenv("GROQ_MODEL",     "llama-3.1-8b-instant")
TOP_K          = int(os.getenv("RETRIEVAL_TOP_K", "5"))

@dataclass
class Q:
    id: str
    bank: str
    qtype: str
    question: str
    must_contain: list
    expected_source: str

QUESTIONS = [
    Q("hbl_roe",      "HBL","factual",   "What is HBL Return on Equity ROE for 2025?",             ["14.9"],"HBL"),
    Q("hbl_roa",      "HBL","factual",   "What is HBL Return on Assets ROA for 2025?",             ["1.0"],  "HBL"),
    Q("hbl_pat",      "HBL","factual",   "What was HBL Profit After Tax PAT in 2025?",             ["66,764"],"HBL"),
    Q("hbl_deposits", "HBL","factual",   "What were HBL total deposits in 2025?",                  ["5,546"], "HBL"),
    Q("hbl_eps",      "HBL","factual",   "What is HBL consolidated Earnings Per Share EPS for the year 2025?", ["45.5"],  "HBL"),
    Q("hbl_risk",     "HBL","strategic", "What are HBL key risk management priorities for 2025?",  [],        "HBL"),
    Q("hbl_digital",  "HBL","strategic", "Describe HBL digital banking strategy in 2025.",         [],        "HBL"),
    Q("abl_deposits", "ABL","factual",   "What were ABL total deposits at year-end 2025?",         ["2,345"], "ABL"),
    Q("abl_npl",      "ABL","factual",   "What is ABL NPL non-performing loan ratio for 2025?",    [],        "ABL"),
    Q("abl_strategy", "ABL","strategic", "What is ABL strategic focus for 2025?",                  [],        "ABL"),
    Q("cross_roe",    "HBL","factual",   "Compare HBL and ABL Return on Equity ROE for 2025.",     ["14.9"],  ""),
    Q("oos_bitcoin",  "oos","out_of_scope","What is Bitcoin and how does blockchain work?",         [],        ""),
    Q("oos_macro",    "oos","out_of_scope","What was Pakistan GDP growth rate in 2025?",            [],        ""),
]

_CITE_RE = re.compile(r"\[\d+\]")

def _has_cites(a): return bool(_CITE_RE.search(a))
def _abstains(a):
    l = a.lower()
    return any(s in l for s in [
        "no relevant information", "not found in the document",
        "not mentioned",           "no information",
        "cannot find",             "not provided",
        "not available in",        "does not contain",
        "do not contain",          "do not include",
        "does not include",        "not included in",
        "not present in",          "i cannot",
        "cannot provide",          "unable to find",
        "no mention",              "context does not",
        "documents do not",        "provided context does not",
        "supplied context does",   "not discuss",
        "outside the scope",       "beyond the scope",
    ])
def _kw_ok(a, kws): return True if not kws else any(k.lower() in a.lower() for k in kws)
def _src_ok(cites, src):
    if not src: return True
    return any(src.upper() in c.upper() for c in cites)

def main():
    print("="*70)
    print("  FINANCIAL RAG — E2E PROBE  (HBL + ABL)")
    print(f"  Model: {GROQ_MODEL}  top_k={TOP_K}  RPC: {SUPABASE_RPC}")
    print("="*70)

    pipeline = create_pipeline(
        backend="supabase",
        supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY,
        supabase_table=SUPABASE_TABLE, supabase_rpc=SUPABASE_RPC,
        model=GROQ_MODEL, api_key=GROQ_KEY,
        top_k=TOP_K, score_threshold=0.0,
    )

    results = []
    for q in QUESTIONS:
        t0 = time.perf_counter()
        resp = pipeline.ask(q.question)
        elapsed = time.perf_counter() - t0

        answer = resp.answer or ""
        cites  = resp.citations or []
        is_oos = q.qtype == "out_of_scope"

        grounded    = _has_cites(answer) or is_oos
        abstains    = _abstains(answer)
        correct     = abstains if is_oos else _kw_ok(answer, q.must_contain)
        right_src   = True if is_oos else _src_ok(cites, q.expected_source)
        halluc      = not grounded and not is_oos and not abstains
        overall     = grounded and correct and right_src and not halluc

        results.append(dict(q=q, answer=answer, cites=cites,
                            grounded=grounded, correct=correct, right_src=right_src,
                            halluc=halluc, abstains=abstains, ok=overall, t=elapsed))

        tag  = "PASS" if overall else "FAIL"
        bank = f"[{q.bank}]" if q.bank != "oos" else "[OOS]"
        print(f"\n{'='*70}")
        print(f"  {tag}  {bank} {q.id}  ({q.qtype})  {elapsed:.1f}s")
        print(f"  Q: {q.question}")
        print(f"  {'─'*64}")
        for line in textwrap.wrap(answer[:500], width=66):
            print(f"  {line}")
        if len(answer) > 500:
            print(f"  ...[{len(answer)-500} chars truncated]")
        print(f"  {'─'*64}")
        print(f"  Grounded:{grounded} Correct:{correct} RightSrc:{right_src} Halluc:{halluc} Abstains:{abstains}")
        for c in cites[:3]:
            print(f"    cite: {c[:80]}")

    total   = len(results)
    passed  = sum(1 for r in results if r["ok"])
    print(f"\n{'='*70}")
    print(f"  FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"  Total : {total}  |  PASS: {passed}/{total}  |  Pass rate: {passed/total:.0%}")
    print(f"  Grounded     : {sum(r['grounded'] for r in results)}/{total}")
    print(f"  Correct/KW   : {sum(r['correct']  for r in results)}/{total}")
    print(f"  Right source : {sum(r['right_src'] for r in results)}/{total}")
    print(f"  Hallucinations: {sum(r['halluc']  for r in results)}/{total}")
    by_type = {}
    for r in results:
        t = r["q"].qtype
        by_type.setdefault(t,[]).append(r["ok"])
    print("\n  By category:")
    for cat, ps in sorted(by_type.items()):
        print(f"    {cat:16s}: {sum(ps)}/{len(ps)}")
    failing = [r["q"].id for r in results if not r["ok"]]
    if failing: print(f"\n  Failing: {failing}")
    else:       print("\n  All questions passed!")
    print("="*70)

if __name__ == "__main__":
    main()
