#!/usr/bin/env python3
"""pre-push eval 게이트 — 전역 RAG 검색 품질 회귀 차단.

흐름: ① 정본 principles로 인덱스 최신화(kb_index) → ② 프로덕션 설정(rerank pool=20)으로
eval → ③ MRR/P@1 임계 미만이면 비0 종료(push BLOCK).

정책:
- 측정값이 임계 미만 → BLOCK (검색 품질 회귀).
- 인프라 문제(venv/모델/모듈 불가)로 eval 자체를 못 돌리면 → SKIP(0). 환경 문제는 품질 회귀가
  아니므로 push를 막지 않는다. KB_EVAL_STRICT=1 이면 인프라 실패에도 BLOCK.

env: KB_EVAL_MIN_MRR(기본 0.90), KB_EVAL_MIN_P1(기본 0.90), KB_EVAL_STRICT.
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try: _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

MIN_MRR = float(os.environ.get("KB_EVAL_MIN_MRR", "0.90"))
MIN_P1 = float(os.environ.get("KB_EVAL_MIN_P1", "0.90"))
STRICT = os.environ.get("KB_EVAL_STRICT") == "1"
EPS = 1e-9


def skip_or_fail(msg):
    print(f"[eval-gate] {msg}{' → BLOCK(STRICT)' if STRICT else ' → SKIP'}")
    return 1 if STRICT else 0


def main():
    try:
        import kb_index, kb_search, kb_eval
    except Exception as e:
        return skip_or_fail(f"모듈 import 실패: {e}")

    # 1) 인덱스 최신화 (정본 principles 반영; incremental — 변경분만 재임베딩)
    try:
        kb_index.main()
    except SystemExit:
        pass
    except Exception as e:
        return skip_or_fail(f"인덱스 빌드 실패: {e}")

    # 2) 프로덕션 설정으로 eval
    try:
        con = kb_search.connect()
        qpath = HERE / "eval" / "queries.json"
        queries = json.loads(qpath.read_text(encoding="utf-8"))["queries"]
        m = kb_eval.eval_config(con, queries, rerank=True, pool=20)
    except Exception as e:
        return skip_or_fail(f"eval 실행 실패: {e}")

    mrr, p1 = m["MRR"], m["P@1"]
    print(f"[eval-gate] MRR={mrr:.3f} (min {MIN_MRR})  P@1={p1:.3f} (min {MIN_P1})  "
          f"질의 {m['n']}개")
    if mrr + EPS < MIN_MRR or p1 + EPS < MIN_P1:
        print("[eval-gate] FAIL — 검색 품질 회귀(임계 미달). "
              "principles 수정 또는 골드셋 점검 필요.")
        return 1
    print("[eval-gate] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
