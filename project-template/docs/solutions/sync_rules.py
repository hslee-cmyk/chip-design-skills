#!/usr/bin/env python3
"""capture↔curate 브리지 (P1): docs/solutions ↔ .bkit/state/regression-rules.json.

방향:
  - PUSH: docs/solutions 각 자산(frontmatter) → bkit regression-rules.json 의 rule.
    (카테고리 = problem_type, severity 매핑, violationCount 보존, source 추적)
  - REPORT A: violationCount >= 임계 또는 severity=critical 인데 아직 critical-patterns.md
    에 없는 rule → "Required Reading 승격 후보"로 출력.
  - REPORT B: problem_type=toolflow 또는 module=System 인 rule → "kb-global 격상 후보"로 출력.
    (툴/환경 버그는 프로젝트 무관 — violationCount 기다리지 않고 생성 즉시 후보)
  - PRUNE: 과거 이 스크립트가 만든 rule 중 원본 자산이 사라진 것 → stale 제거.

bkit regression-rules 스키마(v2.0):
  { version, rules:[{ id, category, description, pattern, severity(critical|major|minor),
                      addedAt, violationCount, source?, syncedBy? }] }

Usage:
    python docs/solutions/sync_rules.py            # 동기 + 리포트
    python docs/solutions/sync_rules.py --dry-run  # 변경 없이 리포트만
"""
from __future__ import annotations
import json
import re
import sys
import uuid as _uuid
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent          # docs/solutions
PROJ = HERE.parent.parent                        # <project-root>
RULES_PATH = PROJ / ".bkit" / "state" / "regression-rules.json"
CRIT_PATH = HERE / "patterns" / "critical-patterns.md"
# kb-global: <workspace>/chip-design-skills/kb-global/principles/
KB_GLOBAL_PATH = PROJ.parent / "chip-design-skills" / "kb-global" / "principles"

PROMOTE_THRESHOLD = 2                            # violationCount >= 2 → Required Reading 후보

# problem_type이 이것이면 툴/환경 레벨 → kb-global 즉시 후보
_KB_GLOBAL_TYPES = {"toolflow"}
# module이 이것이면 특정 RTL 모듈 아님 → kb-global 즉시 후보
_KB_GLOBAL_MODULES = {"system", "System", ""}

EXCLUDE_NAMES = {"README.md"}
EXCLUDE_DIRS = {"patterns"}
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
SYNC_TAG = "docs-solutions"
SEV_MAP = {"critical": "critical", "high": "major",
           "medium": "minor", "low": "minor"}


def parse_fm(text: str):
    m = FM_RE.match(text)
    body = text[m.end():] if m else text
    if not m:
        return {}, body
    try:
        import yaml
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        fm = {}
    return (fm if isinstance(fm, dict) else {}), body


def iter_assets():
    for p in sorted(HERE.rglob("*.md")):
        if p.name in EXCLUDE_NAMES:
            continue
        if any(part in EXCLUDE_DIRS for part in p.relative_to(HERE).parts[:-1]):
            continue
        yield p


def load_rules() -> dict:
    if RULES_PATH.exists():
        try:
            d = json.loads(RULES_PATH.read_text(encoding="utf-8"))
            d.setdefault("version", "2.0")
            d.setdefault("rules", [])
            return d
        except Exception:
            pass
    return {"version": "2.0", "rules": []}


def _critical_contributed_ids() -> set:
    """critical-patterns.md의 contributed_from 목록을 반환."""
    if not CRIT_PATH.exists():
        return set()
    try:
        fm, _ = parse_fm(CRIT_PATH.read_text(encoding="utf-8", errors="replace"))
        contributed = fm.get("contributed_from") or []
        if isinstance(contributed, list):
            return {str(x) for x in contributed}
    except Exception:
        pass
    return set()


def _kb_global_texts() -> str:
    """kb-global/principles/ 전체 텍스트를 이어붙여 반환 (미존재 시 빈 문자열)."""
    if not KB_GLOBAL_PATH.exists():
        return ""
    parts = []
    for p in KB_GLOBAL_PATH.rglob("*.md"):
        try:
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            pass
    return "\n".join(parts)


def _kb_global_promoted_ids() -> set:
    """kb-global/principles/ 파일들의 promoted_from 목록을 모아 반환."""
    if not KB_GLOBAL_PATH.exists():
        return set()
    ids: set[str] = set()
    for p in KB_GLOBAL_PATH.rglob("*.md"):
        try:
            fm, _ = parse_fm(p.read_text(encoding="utf-8", errors="replace"))
            promoted = fm.get("promoted_from") or []
            if isinstance(promoted, list):
                ids.update(str(x) for x in promoted)
        except Exception:
            pass
    return ids


def _is_kb_global_candidate(fm: dict) -> bool:
    """툴/환경 레벨 솔루션 여부 — 생성 즉시 kb-global 후보."""
    pt = str(fm.get("problem_type", "") or "").lower().replace("-", "_")
    mod = str(fm.get("module", "") or "")
    if pt in _KB_GLOBAL_TYPES:
        return True
    # module이 System/빈값이고 RTL 타입이 아닌 경우
    rtl_types = {"fsm_corner", "protocol_spec", "pointer_handshake", "timing_cycle",
                 "fpga_ram", "width_truncation", "port_integration", "structure_style",
                 "clock_reset_cdc"}
    if mod in _KB_GLOBAL_MODULES and pt not in rtl_types:
        return True
    return False


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = load_rules()
    by_id = {r["id"]: r for r in data["rules"]}

    # asset별 frontmatter 보존 (kb-global 판정에 필요)
    asset_fm: dict[str, dict] = {}

    assets = list(iter_assets())
    seen_ids: set[str] = set()
    added, updated = 0, 0

    for p in assets:
        text = p.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_fm(text)
        pt = str(fm.get("problem_type", "") or "")
        if not pt:
            continue
        category = pt.replace("_", "-")
        rid = p.stem
        seen_ids.add(rid)
        asset_fm[rid] = fm

        h1 = H1_RE.search(body)
        desc = (h1.group(1).strip() if h1 else p.stem)
        sev = SEV_MAP.get(str(fm.get("severity", "")).lower(), "minor")
        rel = p.relative_to(PROJ).as_posix()
        tags = fm.get("tags", [])
        pattern = ", ".join(tags) if isinstance(tags, list) and tags else None
        added_at = str(fm.get("date", "")) or date.today().isoformat()

        if rid in by_id:
            r = by_id[rid]
            changed = (r.get("category") != category or r.get("description") != desc
                       or r.get("severity") != sev or r.get("source") != rel)
            r.update({"category": category, "description": desc, "severity": sev,
                      "pattern": pattern, "source": rel, "syncedBy": SYNC_TAG})
            r.setdefault("violationCount", 1)
            r.setdefault("addedAt", added_at)
            if changed:
                updated += 1
        else:
            by_id[rid] = {
                "id": rid, "category": category, "description": desc,
                "pattern": pattern, "severity": sev, "addedAt": added_at,
                "violationCount": 1, "source": rel, "syncedBy": SYNC_TAG}
            added += 1

    # PRUNE: 이 스크립트가 만든 rule 중 원본 사라진 것
    pruned = [rid for rid, r in list(by_id.items())
              if r.get("syncedBy") == SYNC_TAG and rid not in seen_ids]
    for rid in pruned:
        del by_id[rid]

    data["rules"] = sorted(by_id.values(), key=lambda r: (r["category"], r["id"]))

    if not dry:
        RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
        RULES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                              encoding="utf-8")

    # ── REPORT A: Required Reading 패턴 추출 권장 (critical-patterns.md) ──────
    contributed_ids = _critical_contributed_ids()  # 이미 기여된 솔루션 ID 집합
    # 카테고리별 rule 집계 (기여 안 된 것만 fresh로 카운트)
    cat_rules: dict[str, list] = defaultdict(list)
    for r in data["rules"]:
        if r.get("syncedBy") != SYNC_TAG:
            continue
        cat_rules[r["category"]].append(r)
    kb_promoted_ids = _kb_global_promoted_ids()  # [B] 격상된 ID → [A]에서도 제외
    crit_candidates: list[dict] = []
    # 1) 카테고리 내 미기여·미격상 솔루션 >= PROMOTE_THRESHOLD → 공통 패턴 추출 권장
    for cat, rules in cat_rules.items():
        fresh = [r for r in rules
                 if r["id"] not in contributed_ids      # [A] 미기여
                 and r["id"] not in kb_promoted_ids]    # [B] 미격상
        if len(fresh) >= PROMOTE_THRESHOLD:
            crit_candidates.append({"category": cat, "rules": fresh, "reason": "recurrence"})
    # 2) severity=critical → 단독으로도 즉시 후보 (미기여·미격상분만)
    for r in data["rules"]:
        if r.get("syncedBy") != SYNC_TAG:
            continue
        if (r["severity"] == "critical"
                and r["id"] not in contributed_ids
                and r["id"] not in kb_promoted_ids):
            cat = r["category"]
            if not any(c["category"] == cat for c in crit_candidates):
                crit_candidates.append({"category": cat, "rules": [r], "reason": "critical"})

    # ── REPORT B: kb-global 격상 후보 ──────────────────────────────────────
    kb_text = _kb_global_texts()
    promoted_ids = _kb_global_promoted_ids()   # promoted_from 명시 목록
    kb_candidates = []
    for r in data["rules"]:
        if r.get("syncedBy") != SYNC_TAG:
            continue
        fm = asset_fm.get(r["id"], {})
        if not _is_kb_global_candidate(fm):
            continue
        # 이미 kb-global에 등재된 경우 제외:
        #   1순위: promoted_from 명시 목록 (정확)
        #   2순위: id가 kb-global 본문에 직접 등장 (fallback)
        already = r["id"] in promoted_ids or r["id"] in kb_text
        if not already:
            kb_candidates.append(r)

    # ── 출력 ───────────────────────────────────────────────────────────────
    print(f"{'[dry-run] ' if dry else ''}regression-rules 동기: "
          f"+{added} 추가, ~{updated} 갱신, -{len(pruned)} 정리. "
          f"총 {len(data['rules'])} rules. ({RULES_PATH})")
    if pruned:
        print("  정리됨:", ", ".join(pruned))

    print(f"\n[A] Required Reading 패턴 추출 권장 "
          f"(카테고리 솔루션 >={PROMOTE_THRESHOLD}개 또는 severity=critical, "
          f"critical-patterns.md 미등재):")
    if crit_candidates:
        for c in crit_candidates:
            label = "severity=critical" if c["reason"] == "critical" else f"{len(c['rules'])}개 솔루션"
            print(f"  - [{c['category']}] {label}")
            for r in c["rules"]:
                print(f"      ← {r['source']}")
        print("  → /kb-promote 로 공통 패턴 합성 후 critical-patterns.md 등재 권장.")
    else:
        print("  없음.")

    kb_label = str(KB_GLOBAL_PATH) if KB_GLOBAL_PATH.exists() else "(경로 없음 — chip-design-skills 미발견)"
    print(f"\n[B] kb-global 격상 후보 (toolflow/System-level, kb-global 미등재):")
    print(f"    대상: {kb_label}")
    if kb_candidates:
        for r in kb_candidates:
            fm = asset_fm.get(r["id"], {})
            mod = fm.get("module", "?")
            print(f"  - [{r['category']}] {r['id']}  "
                  f"(module={mod}, sev={r['severity']})  ← {r['source']}")
        print("  → chip-design-skills/kb-global/principles/ 에 일반화 원칙으로 격상 권장.")
        print("    격상 후: git commit + push → KB_PY .tools/kb-global/kb_index.py 재색인.")
    else:
        print("  없음.")

    return 0


def record_promo_main() -> int:
    """--record-promo 모드: [A]/[B] 격상 이벤트를 bkit audit/decisions에 기록."""
    import argparse
    args_list = [a for a in sys.argv[1:] if a != "--record-promo"]
    p = argparse.ArgumentParser(prog="sync_rules.py --record-promo")
    p.add_argument("--type", choices=["A", "B"], required=True, dest="promo_type",
                   help="격상 유형: A=critical-patterns, B=kb-global")
    p.add_argument("--category", default="", help="솔루션 카테고리명")
    p.add_argument("--ids", default="", help="쉼표 구분 솔루션 ID 목록")
    p.add_argument("--target", default="", help="격상 대상 파일 상대 경로")
    p.add_argument("--reason", default="", help="recurrence|critical|toolflow")
    args = p.parse_args(args_list)

    source_ids = [s.strip() for s in args.ids.split(",") if s.strip()]
    now = datetime.now(timezone.utc).isoformat()
    today = now[:10]

    # Audit entry (.bkit/audit/YYYY-MM-DD.jsonl)
    audit_entry = {
        "id": str(_uuid.uuid4()),
        "timestamp": now,
        "sessionId": "",
        "actor": "agent",
        "actorId": "kb-promote",
        "action": "file_modified",
        "category": "quality",
        "target": "kb-global",
        "targetType": "feature",
        "details": {
            "promotionType": args.promo_type,
            "category": args.category,
            "sourceIds": source_ids,
            "targetFile": args.target,
            "reason": args.reason,
        },
        "result": "success",
        "reason": None,
        "destructiveOperation": False,
        "blastRadius": "low",
        "bkitVersion": "",
    }

    # Decision trace (.bkit/decisions/YYYY-MM-DD.jsonl)
    n = len(source_ids)
    if args.promo_type == "A":
        question = (f"[A] category '{args.category}': {n}개 fresh 솔루션 → "
                    f"critical-patterns.md 격상 여부")
        rationale = f"카테고리 내 미기여 솔루션 {n}개 누적, /kb-promote 승인 후 패턴 등재"
    else:
        first_id = source_ids[0] if source_ids else ""
        question = (f"[B] '{first_id}': kb-global 격상 여부 ({args.reason})")
        rationale = "toolflow/System-level 솔루션, /kb-promote 승인 후 일반 원칙 등재"

    decision_entry = {
        "id": str(_uuid.uuid4()),
        "timestamp": now,
        "sessionId": "",
        "feature": "kb-global",
        "phase": "check",
        "automationLevel": 1,
        "decisionType": "quality_gate_result",
        "question": question,
        "chosenOption": "promote",
        "alternatives": [{"option": "skip", "reason": "defer",
                          "rejectedBecause": "user approved"}],
        "rationale": rationale,
        "confidence": 0.9,
        "impact": "medium",
        "affectedFiles": [args.target] if args.target else [],
        "reversible": True,
        "outcome": "positive",
    }

    # 쓰기
    audit_dir = PROJ / ".bkit" / "audit"
    try:
        audit_dir.mkdir(parents=True, exist_ok=True)
        with (audit_dir / f"{today}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(audit_entry, ensure_ascii=False) + "\n")
        print(f"[record-promo] audit 기록 → .bkit/audit/{today}.jsonl")
    except Exception as e:
        print(f"[record-promo] audit 쓰기 실패(무시): {e}", file=sys.stderr)

    dec_dir = PROJ / ".bkit" / "decisions"
    try:
        dec_dir.mkdir(parents=True, exist_ok=True)
        with (dec_dir / f"{today}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(decision_entry, ensure_ascii=False) + "\n")
        print(f"[record-promo] decision 기록 → .bkit/decisions/{today}.jsonl")
    except Exception as e:
        print(f"[record-promo] decision 쓰기 실패(무시): {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    if "--record-promo" in sys.argv:
        sys.exit(record_promo_main())
    sys.exit(main())
