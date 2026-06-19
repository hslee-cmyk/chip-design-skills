#!/usr/bin/env python3
"""capture↔curate 브리지 (P1): docs/solutions ↔ .bkit/state/regression-rules.json.

방향:
  - PUSH: docs/solutions 각 자산(frontmatter) → bkit regression-rules.json 의 rule.
    (카테고리 = problem_type, severity 매핑, violationCount 보존, source 추적)
  - REPORT: violationCount >= 임계 또는 severity=critical 인데 아직 critical-patterns.md
    에 없는 rule → "Required Reading 승격 후보"로 출력.
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
from datetime import date
from pathlib import Path

import os
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent          # docs/solutions
PROJ = HERE.parent.parent                        # venezia-fpga
RULES_PATH = PROJ / ".bkit" / "state" / "regression-rules.json"
CRIT_PATH = HERE / "patterns" / "critical-patterns.md"
PROMOTE_THRESHOLD = 2                            # violationCount >= 2 → 승격 후보

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
    root = HERE
    for p in sorted(root.rglob("*.md")):
        if p.name in EXCLUDE_NAMES:
            continue
        if any(part in EXCLUDE_DIRS for part in p.relative_to(root).parts[:-1]):
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


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = load_rules()
    by_id = {r["id"]: r for r in data["rules"]}

    assets = list(iter_assets())
    seen_ids = set()
    added, updated = 0, 0

    for p in assets:
        fm, body = parse_fm(p.read_text(encoding="utf-8", errors="replace"))
        pt = str(fm.get("problem_type", "") or "")
        if not pt:
            continue
        category = pt.replace("_", "-")          # width_truncation → width-truncation
        rid = p.stem                              # 날짜 suffix로 고유
        seen_ids.add(rid)
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

    # REPORT: 승격 후보
    crit_text = CRIT_PATH.read_text(encoding="utf-8") if CRIT_PATH.exists() else ""
    candidates = []
    for r in data["rules"]:
        if r.get("syncedBy") != SYNC_TAG:
            continue
        hot = r["violationCount"] >= PROMOTE_THRESHOLD or r["severity"] == "critical"
        in_crit = r["id"] in crit_text or r["category"] in crit_text
        if hot and not in_crit:
            candidates.append(r)

    print(f"{'[dry-run] ' if dry else ''}regression-rules 동기: "
          f"+{added} 추가, ~{updated} 갱신, -{len(pruned)} 정리. "
          f"총 {len(data['rules'])} rules. ({RULES_PATH})")
    if pruned:
        print("  정리됨:", ", ".join(pruned))
    print(f"\nRequired Reading 승격 후보 (violationCount>={PROMOTE_THRESHOLD} "
          f"또는 severity=critical, critical-patterns.md 미등재):")
    if candidates:
        for r in candidates:
            print(f"  - [{r['category']}] {r['id']}  "
                  f"(viol={r['violationCount']}, sev={r['severity']})  ← {r['source']}")
        print("  → 검토 후 critical-patterns.md 에 ❌WRONG/✅CORRECT 코드쌍으로 등재 권장.")
    else:
        print("  없음.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
