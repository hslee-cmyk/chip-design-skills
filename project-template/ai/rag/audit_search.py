#!/usr/bin/env python3
"""bkit audit full-text search — details 딕셔너리 포함 검색.

bkit MCP bkit_audit_search는 top-level 필드만 색인하고 details 내부는 검색 안 됨.
이 스크립트는 .bkit/audit/*.jsonl을 직접 파싱해 모든 필드(details 중첩 포함)를
flat 문자열로 만들어 풀텍스트 검색한다.

Usage:
    "$KB_PY" .ai/rag/audit_search.py "<query>"
    "$KB_PY" .ai/rag/audit_search.py "<query>" --action loop_verified
    "$KB_PY" .ai/rag/audit_search.py "<query>" --category knowledge --date-from 2026-06-01
    "$KB_PY" .ai/rag/audit_search.py "" --action gate_passed --limit 20
    "$KB_PY" .ai/rag/audit_search.py "<query>" --decisions   # decisions 로그 검색
    "$KB_PY" .ai/rag/audit_search.py "<query>" --json        # JSON 출력

Filters (AND 조건):
    --action ACTION       action 필드 exact match
    --category CATEGORY   category 필드 exact match
    --actor ACTOR         actor 또는 actorId 포함 검색
    --date-from YYYY-MM-DD
    --date-to   YYYY-MM-DD
    --decisions           audit 대신 .bkit/decisions/ 검색
    --limit N             최대 출력 수 (기본 20)
    --json                JSON 배열로 출력 (파이프 용)
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from datetime import date

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try: _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass

HERE = Path(__file__).resolve().parent   # <proj>/.ai/rag
PROJ = HERE.parent.parent                # <proj>


def _flatten(obj, prefix="") -> str:
    """중첩 dict/list를 재귀적으로 flat 문자열로 변환."""
    if isinstance(obj, dict):
        return " ".join(_flatten(v, k) for k, v in obj.items())
    if isinstance(obj, list):
        return " ".join(_flatten(v) for v in obj)
    return str(obj) if obj is not None else ""


def _load_entries(subdir: str, date_from: str | None, date_to: str | None) -> list[dict]:
    log_dir = PROJ / ".bkit" / subdir
    if not log_dir.is_dir():
        return []
    entries = []
    for f in sorted(log_dir.glob("*.jsonl")):
        stem = f.stem  # YYYY-MM-DD
        if date_from and stem < date_from:
            continue
        if date_to and stem > date_to:
            continue
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def _matches(entry: dict, query: str, action: str | None,
             category: str | None, actor: str | None) -> bool:
    if action and entry.get("action") != action:
        return False
    if category and entry.get("category") != category:
        return False
    if actor:
        al = actor.lower()
        if al not in entry.get("actor", "").lower() and al not in entry.get("actorId", "").lower():
            return False
    if not query:
        return True
    flat = _flatten(entry).lower()
    return all(tok.lower() in flat for tok in query.split())


def main() -> int:
    ap = argparse.ArgumentParser(
        description="bkit audit/decisions full-text search (details 포함)")
    ap.add_argument("query", nargs="?", default="",
                    help="검색어 (공백으로 AND, 빈 문자열이면 전체)")
    ap.add_argument("--action",    help="action 필드 exact match")
    ap.add_argument("--category",  help="category 필드 exact match")
    ap.add_argument("--actor",     help="actor/actorId 포함 검색")
    ap.add_argument("--date-from", metavar="YYYY-MM-DD", help="시작 날짜")
    ap.add_argument("--date-to",   metavar="YYYY-MM-DD",
                    default=date.today().isoformat(), help="종료 날짜 (기본: 오늘)")
    ap.add_argument("--decisions", action="store_true",
                    help="audit 대신 .bkit/decisions/ 검색")
    ap.add_argument("--limit", type=int, default=20, help="최대 결과 수 (기본 20)")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="JSON 배열 출력")
    a = ap.parse_args()

    subdir = "decisions" if a.decisions else "audit"
    entries = _load_entries(subdir, a.date_from, a.date_to)

    if not entries:
        print(f"(no {subdir} logs found in {PROJ / '.bkit' / subdir})", file=sys.stderr)
        return 0

    hits = [e for e in entries
            if _matches(e, a.query, a.action, a.category, a.actor)]

    # 최신순 정렬, limit 적용
    hits.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    hits = hits[:a.limit]

    if a.as_json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return 0

    q_label = f'"{a.query}"' if a.query else "(전체)"
    filters = []
    if a.action:    filters.append(f"action={a.action}")
    if a.category:  filters.append(f"category={a.category}")
    if a.actor:     filters.append(f"actor~{a.actor}")
    if a.date_from: filters.append(f"from={a.date_from}")
    fstr = "  [" + ", ".join(filters) + "]" if filters else ""
    print(f"\n{'='*72}")
    print(f"audit_search {q_label}{fstr}  →  {len(hits)} hit(s) / {len(entries)} total ({subdir})")
    print(f"{'='*72}\n")

    for i, e in enumerate(hits, 1):
        ts  = e.get("timestamp", "")[:19].replace("T", " ")
        eid = e.get("id", "")[:8]

        # decisions 스키마 (feature/phase/decisionType/chosenOption)
        # vs audit 스키마 (action/category/target/actor/result)
        if a.decisions or "decisionType" in e:
            feat   = e.get("feature", "")
            phase  = e.get("phase", "")
            dtype  = e.get("decisionType", "")
            chosen = e.get("chosenOption", "")
            q      = e.get("question") or ""
            rat    = e.get("rationale") or ""
            print(f"#{i:02d}  [{ts}]  {dtype}  (phase={phase})  →  feature={feat}")
            print(f"     chosen={chosen}  id={eid}...")
            if q:
                print(f"     question: {q[:120]}")
            if rat:
                print(f"     rationale: {rat[:120]}")
        else:
            act  = e.get("action", "")
            cat  = e.get("category", "")
            tgt  = e.get("target", "")
            res  = e.get("result", "")
            rsn  = e.get("reason") or ""
            aid  = e.get("actorId", e.get("actor", ""))
            print(f"#{i:02d}  [{ts}]  {act}  ({cat})  →  {tgt}")
            print(f"     actor={aid}  result={res}  id={eid}...")
            if rsn:
                print(f"     reason: {rsn}")

        det = e.get("details") or {}
        if det:
            det_str = "  ".join(
                f"{k}={json.dumps(v, ensure_ascii=False)[:80]}"
                for k, v in (det.items() if isinstance(det, dict) else [])
            )
            if det_str:
                print(f"     details: {det_str[:200]}")
        print()

    if not hits:
        print(f"  (no matches for {q_label})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
