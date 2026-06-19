#!/usr/bin/env python3
"""지식 프리플라이트 (P4, 2-tier) — RTL/버그 착수 전 장기+단기 지식을 한 번에 조회.

  1. 장기 일반원칙 (전역 RAG, L4-global)  : fpga/.tools/kb-global (증류 원칙·taxonomy)
  2. 단기 프로젝트 항법 (graphify, L3)      : 이 프로젝트 graph.json (모듈·설계·프로젝트 버그)

설계: 같은 정보를 두 곳에 넣지 않는다.
  - 일반화된 원칙 = 전역 RAG (전 프로젝트 공유, 의미검색)
  - 프로젝트 고유 관계·instance = 프로젝트 graphify (항법)
  자세히: .ai/KNOWLEDGE_MAP.md

Usage:
    "$KB_PY" .ai/rag/preflight.py "<증상/주제>" [--kind pattern ...]
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try: _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass

HERE = Path(__file__).resolve().parent           # <proj>/.ai/rag
PROJ = HERE.parent.parent                         # <proj>
FPGA = HERE.parents[2]                             # fpga 워크스페이스
KB_GLOBAL = FPGA / ".tools" / "kb-global"
PY = sys.executable
FILT = ("warning", "symlink", "huggingface", "fetching", "developer mode",
        "docs.microsoft", "hf_token")


def hdr(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def run(cmd, cwd=None, timeout=120):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, cwd=cwd)
    out = "\n".join(l for l in (r.stdout or "").splitlines()
                    if not any(s in l.lower() for s in FILT))
    return out.strip(), (r.stderr or "").strip(), r.returncode


def main():
    if len(sys.argv) < 2:
        print('usage: preflight.py "<증상/주제>" [--kind pattern --tag fifo ...]'); return 2
    query = sys.argv[1]; extra = sys.argv[2:]

    # 1) 장기 일반원칙 (전역 RAG)
    hdr(f'1. 장기 일반원칙 (전역 RAG) — "{query}"')
    try:
        out, err, rc = run([PY, str(KB_GLOBAL / "kb_search.py"), query, "-k", "5", *extra])
        print(out or "(결과 없음)")
        if rc != 0 and err: print("[kb_search stderr]", err[:300])
    except Exception as e:
        print(f"(전역 RAG 조회 실패: {e})")

    # 2) 단기 프로젝트 항법 (graphify)
    hdr(f'2. 단기 프로젝트 항법 (graphify) — "{query}"')
    try:
        out, _e, _rc = run([PY, "-m", "graphify", "query", query, "--budget", "350"], cwd=str(PROJ))
        print(out or "(graph 결과 없음)")
    except Exception as e:
        print(f"(graphify 조회 실패: {e})")

    print("\n" + "-" * 70)
    print("프리플라이트 완료. 장기 원칙(전역) + 단기 관계(프로젝트)를 반영해 PLAN-BEFORE-CODE.")
    print("해결 확인 후: docs/solutions 자산화 → 일반화되면 .tools/kb-global/principles 로 격상.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
