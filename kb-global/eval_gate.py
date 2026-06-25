#!/usr/bin/env python3
"""pre-push eval 게이트 — 전역 RAG 검색 품질 회귀 차단.

모드:
  기본 (AI 사전 작업용):
    흐름: ① 캐시 유효성 확인 → HIT이면 즉시 0 반환.
          ② 인덱스 최신화(kb_index) → ③ eval(rerank pool=20) → ④ MRR/P@1 임계
          미만이면 1 반환 → ⑤ PASS 시 캐시 기록.
    사용: "$KB_PY" eval_gate.py
          (~3분 cold start. kb-global 변경 후 push 전에 AI가 먼저 실행.)

  --gate (pre-push hook 전용):
    캐시 HIT이면 즉시 0. MISS이면 full eval 없이 즉시 1(BLOCK) + 재구성 안내.
    사용: "$KB_PY" eval_gate.py --gate
    → push hook은 절대 3분 대기하지 않음. 캐시 없으면 AI에게 위임.

캐시 정책:
- 캐시 키: kb-global/principles/**/*.md 전체 내용의 SHA-256 (파일명 포함).
- 캐시 파일: <workspace>/.tools/kb-global/eval_gate_cache.json (비버전관리).
- TTL: 기본 8시간 (KB_EVAL_CACHE_TTL_H=0 이면 캐시 비활성화).
- PASS 결과만 캐시. FAIL은 캐시하지 않아 재실행 시 항상 재평가.

기타 정책:
- 측정값이 임계 미만 → BLOCK.
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
GATE_MODE = "--gate" in sys.argv   # pre-push hook 전용: 캐시 없으면 eval 없이 즉시 BLOCK
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


def _write_bkit_metrics(mrr: float, p1: float, n_queries: int) -> None:
    """PASS 결과를 워크스페이스 내 모든 프로젝트 .bkit/state/quality-metrics.json에 기록."""
    workspace = PROJ.parent
    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "feature": "kb-global",
        "phase": "check",
        "projectLevel": "global",
        "timestamp": now,
        "metrics": {
            "kb_search_mrr":     {"value": mrr,       "collector": "eval_gate", "collectedAt": now},
            "kb_search_p1":      {"value": p1,        "collector": "eval_gate", "collectedAt": now},
            "kb_eval_n_queries": {"value": n_queries, "collector": "eval_gate", "collectedAt": now},
        },
    }
    # 프로젝트별 .bkit/state + 워크스페이스 루트 .bkit/state
    candidates = list(workspace.glob("*/.bkit/state")) + [workspace / ".bkit" / "state"]
    for bkit_state in candidates:
        if not bkit_state.is_dir():
            continue
        metrics_path = bkit_state / "quality-metrics.json"
        try:
            data = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
            data["kb-global"] = entry
            metrics_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass  # 기록 실패는 무시


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

    # --gate 모드: 캐시 없으면 full eval 없이 즉시 BLOCK
    if GATE_MODE:
        print(f"[eval-gate] 캐시 없음/만료 (hash={kb_hash})")
        print("[eval-gate] BLOCK — kb-global 변경 후 캐시 재구성이 필요합니다.")
        print(f"  다음 명령으로 eval 실행 후 재push:")
        print(f"    KB_PY=/c/Users/HSLEE/Documents/Todoc/fpga/.tools/kb-venv/Scripts/python.exe")
        print(f"    \"$KB_PY\" {Path(__file__).resolve()}")
        return 1

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

    # ⑤ PASS → 캐시 기록 + bkit quality-metrics 갱신
    print("[eval-gate] PASS")
    _save_cache(kb_hash, mrr, p1)
    _write_bkit_metrics(mrr, p1, m["n"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
