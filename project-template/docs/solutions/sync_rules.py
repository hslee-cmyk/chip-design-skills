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
from datetime import date
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

    # ── REPORT A: Required Reading 승격 후보 (critical-patterns.md) ──────────
    crit_text = CRIT_PATH.read_text(encoding="utf-8") if CRIT_PATH.exists() else ""
    crit_candidates = []
    for r in data["rules"]:
        if r.get("syncedBy") != SYNC_TAG:
            continue
        hot = r["violationCount"] >= PROMOTE_THRESHOLD or r["severity"] == "critical"
        in_crit = r["id"] in crit_text or r["category"] in crit_text
        if hot and not in_crit:
            crit_candidates.append(r)

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

    print(f"\n[A] Required Reading 승격 후보 (violationCount>={PROMOTE_THRESHOLD} "
          f"또는 severity=critical, critical-patterns.md 미등재):")
    if crit_candidates:
        for r in crit_candidates:
            print(f"  - [{r['category']}] {r['id']}  "
                  f"(viol={r['violationCount']}, sev={r['severity']})  ← {r['source']}")
        print("  → critical-patterns.md 에 ❌WRONG/✅CORRECT 코드쌍으로 등재 권장.")
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


if __name__ == "__main__":
    sys.exit(main())
