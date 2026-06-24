#!/usr/bin/env python3
"""pre-push eval 게이트 — 전역 RAG 검색 품질 회귀 차단.

흐름: ① 캐시 유효성 확인(콘텐츠 해시 일치 + TTL 이내) → CACHE HIT이면 즉시 0 반환.
      ② 정본 principles로 인덱스 최신화(kb_index) → ③ 프로덕션 설정(rerank pool=20)으로
      eval → ④ MRR/P@1 임계 미만이면 비0 종료(push BLOCK) → ⑤ PASS 시 캐시 기록.

캐시 정책:
- 캐시 키: kb-global/principles/**/*.md 전체 내용의 SHA-256 (파일명 포함).
  내용이 바뀌지 않으면 eval 재실행 불필요 — embedding 모델 로드(~3분) 생략.
- 캐시 파일: <workspace>/.tools/kb-global/eval_gate_cache.json (비버전관리).
- TTL: 기본 8시간 (KB_EVAL_CACHE_TTL_H=0 이면 캐시 비활성화).
- PASS 결과만 캐시. FAIL은 캐시하지 않아 재push 시 항상 재평가.

기타 정책:
- 측정값이 임계 미만 → BLOCK (검색 품질 회귀).
- 인프라 문제(venv/모델/모듈 불가)로 eval 자체를 못 돌리면 → SKIP(0).
  KB_EVAL_STRICT=1 이면 인프라 실패에도 BLOCK.

env: KB_EVAL_MIN_MRR(기본 0.90), KB_EVAL_MIN_P1(기본 0.90),
     KB_EVAL_STRICT, KB_EVAL_CACHE_TTL_H(기본 8, 0=비활성화).
"""
from __future__ import annotations
import hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try: _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass

HERE = Path(__file__).resolve().parent          # kb-global/
PROJ = HERE.parent                               # chip-design-skills/
RUNTIME_DIR = PROJ.parent / ".tools" / "kb-global"
CACHE_PATH = RUNTIME_DIR / "eval_gate_cache.json"
PRINCIPLES_DIR = HERE / "principles"

MIN_MRR = float(os.environ.get("KB_EVAL_MIN_MRR", "0.90"))
MIN_P1  = float(os.environ.get("KB_EVAL_MIN_P1",  "0.90"))
STRICT  = os.environ.get("KB_EVAL_STRICT") == "1"
CACHE_TTL_H = int(os.environ.get("KB_EVAL_CACHE_TTL_H", "8"))
EPS = 1e-9

sys.path.insert(0, str(HERE))


# ── 캐시 헬퍼 ──────────────────────────────────────────────────────────────

def _principles_hash() -> str:
    """principles/**/*.md 전체 내용의 SHA-256 (16자 prefix)."""
    h = hashlib.sha256()
    for p in sorted(PRINCIPLES_DIR.rglob("*.md")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def _load_cache() -> dict:
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(kb_hash: str, mrr: float, p1: float) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps({
            "kb_hash":   kb_hash,
            "mrr":       mrr,
            "p1":        p1,
            "passed":    True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass  # 캐시 쓰기 실패는 무시


def _check_cache(kb_hash: str) -> bool:
    """캐시가 유효하면 True (PASS 결과를 재사용 가능)."""
    if CACHE_TTL_H <= 0:
        return False
    c = _load_cache()
    if not c.get("passed") or c.get("kb_hash") != kb_hash:
        return False
    try:
        ts = datetime.fromisoformat(c["timestamp"])
        age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
        return age_h < CACHE_TTL_H
    except Exception:
        return False


# ── 메인 ───────────────────────────────────────────────────────────────────

def skip_or_fail(msg: str) -> int:
    print(f"[eval-gate] {msg}{' → BLOCK(STRICT)' if STRICT else ' → SKIP'}")
    return 1 if STRICT else 0


def main() -> int:
    # ① 캐시 확인
    kb_hash = _principles_hash()
    if _check_cache(kb_hash):
        c = _load_cache()
        print(f"[eval-gate] CACHED PASS — MRR={c['mrr']:.3f}  P@1={c['p1']:.3f}  "
              f"(hash={kb_hash}, TTL={CACHE_TTL_H}h)")
        return 0

    try:
        import kb_index, kb_search, kb_eval
    except Exception as e:
        return skip_or_fail(f"모듈 import 실패: {e}")

    # ② 인덱스 최신화
    try:
        kb_index.main()
    except SystemExit:
        pass
    except Exception as e:
        return skip_or_fail(f"인덱스 빌드 실패: {e}")

    # ③ 프로덕션 설정으로 eval
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

    # ④ 품질 회귀 차단
    if mrr + EPS < MIN_MRR or p1 + EPS < MIN_P1:
        print("[eval-gate] FAIL — 검색 품질 회귀(임계 미달). "
              "principles 수정 또는 골드셋 점검 필요.")
        return 1

    # ⑤ PASS → 캐시 기록
    print("[eval-gate] PASS")
    _save_cache(kb_hash, mrr, p1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
