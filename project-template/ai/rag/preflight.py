#!/usr/bin/env python3
"""지식 프리플라이트 (2-tier, 우선순위·차이설명) — RTL/버그 착수 전 조회.

  1. 일반 원칙 [GENERAL] — 전역 RAG (fpga/.tools/kb-global). 전 프로젝트 적용·정본 git·**우선**.
  2. 프로젝트 고유 [PROJECT] — 이 프로젝트 graphify (관계·instance). 더 깊은 탐색은 graphify MCP.

원칙: 일반 원칙이 *우선*(정본). 프로젝트 내용은 그 원칙의 구체 적용/instance.
충돌하면 일반 원칙을 따른다. 자세히: chip-design-skills/docs/05.

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


def hdr(t): print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


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

    # 1) 일반 원칙 (전역 RAG) — 우선·정본 ───────────────────────────────
    hdr(f'1. 일반 원칙 [GENERAL · 전 프로젝트 적용 · 정본 git · 우선] — "{query}"')
    try:
        out, err, rc = run([PY, str(KB_GLOBAL / "kb_search.py"), query, "-k", "5", *extra])
        print(out or "(결과 없음)")
        if rc != 0 and err:
            print("[kb_search stderr]", err[:300])
    except Exception as e:
        print(f"(전역 RAG 조회 실패: {e})")
    print("   ※ 이게 정본·우선. 프로젝트 내용과 충돌하면 일반 원칙을 따른다.")

    # 2) 프로젝트 고유 (graphify) — instance/관계 ──────────────────────
    hdr(f'2. 프로젝트 고유 [PROJECT · 이 repo · 관계/instance] — "{query}"')
    try:
        out, _e, _rc = run([PY, "-m", "graphify", "query", query, "--budget", "350"],
                           cwd=str(PROJ))
        print(out or "(graph 결과 없음 — graphify-out 미생성이면 `/graphify .` 1회)")
    except Exception as e:
        print(f"(graphify 조회 실패: {e})")
    print("   ※ 위 일반 원칙의 구체 적용/instance. 더 깊은 탐색: graphify MCP "
          "(graphify_query/shortest_path/explain/neighbors) 또는 graphify-out/graph.html.")

    # 3) 일반 원칙 vs 프로젝트 내용 — 차이 설명 ────────────────────────
    print("\n" + "-" * 72)
    print("일반 원칙(GENERAL) vs 프로젝트 내용(PROJECT) — 어떻게 다른가")
    print("-" * 72)
    print("- GENERAL: 전 프로젝트에 적용되는 *규칙*(무엇을 해야/하지 말아야). "
          "정본=chip-design-skills/kb-global(git). **충돌 시 우선.**")
    print("- PROJECT: 이 repo의 모듈분석·설계·버그 *instance*(여기선 어떻게 구현/발생). "
          "정본=<proj>/{.ai, docs}. graphify가 관계 항법.")
    print("- 프로젝트에서 일반화되는 패턴은 kb-global/principles로 격상되면 GENERAL이 된다.")
    print("\n착수: GENERAL 원칙을 우선 적용 + PROJECT 관계로 이 설계의 구체 맥락 보강 → "
          "PLAN-BEFORE-CODE. 해결 후 /solution-capture 로 자산화.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
