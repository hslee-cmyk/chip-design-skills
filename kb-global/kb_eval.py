#!/usr/bin/env python3
"""전역 RAG 검색 품질 eval 하니스 (precision@k / MRR).

골드셋(eval/queries.json)으로 검색 설정을 객관 비교한다:
  - bi-encoder only (rerank off)  vs  rerank (cross-encoder)  [+ pool 변형]
"느낌"이 아니라 숫자로 reranker·다국어 교체의 이득을 판단하기 위함.

kb_search 파이프라인을 그대로 import해 프로덕션과 동일 경로로 측정한다.
런타임 인덱스(fpga/.tools/kb-global/kb.sqlite)를 질의한다.

Usage:
    "$KB_PY" .tools/kb-global/kb_eval.py            # 비교 표
    "$KB_PY" .tools/kb-global/kb_eval.py --verbose  # 질의별 1st-rel rank
    "$KB_PY" .tools/kb-global/kb_eval.py --json
    "$KB_PY" .tools/kb-global/kb_eval.py --queries <path>
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try: _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kb_search as ks   # 동일 디렉터리의 검색 파이프라인 (DB/모델 경로는 parents[1]로 자동 해석)

K = 5   # 운영 top-k (에이전트가 보는 범위)
# 비교 설정: (이름, rerank?, pool)
CONFIGS = [
    ("bi-encoder only", False, None),
    ("rerank pool=10", True, 10),
    ("rerank pool=20", True, 20),
]


def is_rel(result, relevant):
    hay = (f"{result.get('heading','')} {result.get('rel','')} "
           f"{result.get('title','')}").lower()
    return any(tok.lower() in hay for tok in relevant)


def first_rel_rank(results, relevant):
    for i, r in enumerate(results, 1):
        if is_rel(r, relevant):
            return i
    return None


def eval_config(con, queries, rerank, pool):
    rr_sum = p1 = hit3 = hit5 = 0
    per = []
    for q in queries:
        qvec = ks.embed_query(q["query"])
        res = ks.search(con, qvec, K, {}, query=q["query"], rerank=rerank, pool=pool)
        rank = first_rel_rank(res, q["relevant"])
        rr_sum += (1.0 / rank) if rank else 0.0
        p1 += 1 if (res and is_rel(res[0], q["relevant"])) else 0
        hit3 += 1 if (rank and rank <= 3) else 0
        hit5 += 1 if (rank and rank <= 5) else 0
        per.append({"query": q["query"][:42], "rank": rank})
    n = len(queries)
    return {"MRR": rr_sum / n, "P@1": p1 / n, "hit@3": hit3 / n, "hit@5": hit5 / n,
            "n": n, "per": per}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", default=str(HERE / "eval" / "queries.json"))
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if not ks.DB_PATH.exists():
        print(f"인덱스 없음: {ks.DB_PATH}\n먼저 kb_index.py 실행.", file=sys.stderr); return 2
    qdata = json.loads(Path(a.queries).read_text(encoding="utf-8"))
    queries = qdata["queries"]
    con = ks.connect()

    print(f"embed: {ks.MODEL_NAME}\nrerank: {ks.RERANK_MODEL}\n"
          f"질의 {len(queries)}개, top-k={K}\n", file=sys.stderr)
    results = {}
    for name, rerank, pool in CONFIGS:
        results[name] = eval_config(con, queries, rerank, pool)

    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2)); return 0

    # 비교 표
    print(f"{'config':18} {'MRR':>7} {'P@1':>7} {'hit@3':>7} {'hit@5':>7}")
    print("-" * 50)
    for name in results:
        m = results[name]
        print(f"{name:18} {m['MRR']:7.3f} {m['P@1']:7.3f} {m['hit@3']:7.3f} {m['hit@5']:7.3f}")

    if a.verbose:
        print("\n질의별 1st-relevant rank (None=top-k 밖):")
        names = list(results)
        print(f"{'query':44} " + " ".join(f"{n[:14]:>14}" for n in names))
        for i in range(len(queries)):
            row = f"{results[names[0]]['per'][i]['query']:44} "
            row += " ".join(f"{str(results[n]['per'][i]['rank']):>14}" for n in names)
            print(row)
    print("\n해석: MRR/P@1↑ = 순위 품질↑. 설정 간 차이가 reranker·pool의 실제 이득.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
