"""auditor 독립 재계산(spec card 20260930-df23-registry-record 계약 5 (c)) -- reg_check·code-author 산출을 쓰지 않는다.

사용: python -P df23_recount.py <저장소 루트> <out.json> [<레지스트리 상대 경로> [<목록 상대 경로>]]
  * 목록 JSON의 items만으로 계약 1 문장의 §8.1·§8.2 값을 만든다(totals는 대조용으로만 읽는다).
  * 레지스트리에서 `## 8.`로 시작하고 `DF-23`을 담은 제목 줄의 절(다음 `## ` 줄 전까지)을 읽어 표 행을 뽑는다.
  * 둘을 행 집합(중복 행 포함)으로 비교해 out.json에 쓴다. exit 0 = 같음, 1 = 다름 또는 §8 없음, 2 = 입력 오류.
"""
import collections
import json
import os
import re
import sys

REG_REL = "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md"
INV_REL = "docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json"
BEHAVIOR = "동작을 정함"
HDR81 = ["축", "값", "항목 수"]
HDR82 = ["함수", "파일", "항목 수", "DF", "담당 Phase"]


def expected(inv):
    items = inv["items"]
    errs = []
    for k in ("measured_at", "items"):
        if k not in inv:
            errs.append("top key missing: " + k)
    role = collections.Counter()
    phase = collections.Counter()
    base_of = collections.defaultdict(set)
    groups = collections.defaultdict(list)
    bad_map = []
    empty_fn = 0
    for i, it in enumerate(items):
        for k in ("file", "function", "role", "phase", "plan_mapping"):
            if k not in it:
                errs.append("item %d missing %s" % (i, k))
        role[it["role"]] += 1
        phase[it["phase"]] += 1
        base = it["file"].rsplit("/", 1)[-1]
        base_of[base].add(it["file"])
        if it["function"] == "":
            empty_fn += 1
        if it["role"] == BEHAVIOR:
            pm = it["plan_mapping"]
            if not (re.match(r"^DF-\d+", pm) or pm.startswith("신규")):
                bad_map.append(pm)
            groups[(it["function"], base)].append(it)
    rows81 = [("role", v, str(n)) for v, n in role.items() if n] + [("phase", v, str(n)) for v, n in phase.items() if n]
    rows82 = []
    for (fn, base), its in groups.items():
        nums = sorted({int(m.group(1)) for m in (re.match(r"^DF-(\d+)", x["plan_mapping"]) for x in its) if m})
        df = ["DF-%d" % n for n in nums]
        if any(x["plan_mapping"].startswith("신규") for x in its):
            df.append("신규")
        ph = sorted({x["phase"] for x in its})
        rows82.append(("`%s`" % fn, base, str(len(its)), ", ".join(df), ", ".join(ph)))
    facts = {
        "n_items": len(items),
        "role_counts": dict(sorted(role.items())),
        "phase_counts": dict(sorted(phase.items())),
        "n_groups_82": len(rows82),
        "empty_function": empty_fn,
        "file_names": sorted(base_of),
        "ambiguous_file_names": sorted(b for b, s in base_of.items() if len(s) > 1),
        "behavior_mapping_not_df_or_new": bad_map,
        "behavior_mapping_new_prefix": sum(1 for its in groups.values() for x in its
                                           if not re.match(r"^DF-\d+", x["plan_mapping"])),
        "input_errors": errs,
        "totals_field_matches_items": {
            "by_role": inv.get("totals", {}).get("by_role") == dict(role),
            "by_phase": inv.get("totals", {}).get("by_phase") == dict(phase),
        },
    }
    return sorted(rows81), sorted(rows82), facts


def _cells(line):
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")):
        return None
    return [c.strip() for c in s[1:-1].split("|")]


def _table_under(lines, sub_prefix, header):
    """`### <sub_prefix>`로 시작하는 줄 뒤(다음 `### `/`## ` 전) 첫 표 중 머리가 header인 것의 데이터 행."""
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("### " + sub_prefix):
            start = i + 1
            break
    if start is None:
        return None, "subsection missing"
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("### ") or lines[j].startswith("## "):
            end = j
            break
    for j in range(start, end):
        c = _cells(lines[j])
        if c == header:
            rows = []
            for k in range(j + 2, end):
                r = _cells(lines[k])
                if r is None:
                    break
                rows.append(tuple(r))
            sep = _cells(lines[j + 1]) if j + 1 < end else None
            ok_sep = sep is not None and all(re.fullmatch(r":?-+:?", x) for x in sep)
            return rows, None if ok_sep else "separator row malformed"
    return None, "header not found"


def registry_section(text):
    lines = text.splitlines()
    t = None
    for i, ln in enumerate(lines):
        if ln.startswith("## 8.") and "DF-23" in ln:
            t = i
            break
    if t is None:
        return None
    end = len(lines)
    for j in range(t + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    sec = lines[t:end]
    out = {"title": sec[0], "line_range": [t + 1, end], "list_path": None, "measured_at": None}
    for ln in sec:
        m = re.match(r"^목록:\s*`([^`]*)`", ln)
        if m and out["list_path"] is None:
            out["list_path"] = m.group(1)
        m = re.match(r"^measured_at:\s*`([^`]*)`", ln)
        if m and out["measured_at"] is None:
            out["measured_at"] = m.group(1)
    out["usage_rule_present"] = any("목록을 다시 재면 이 절을 같은 Phase 안에서 갱신한다" in ln and "reg_check.py --df23-inventory" in ln
                                    for ln in sec)
    out["rows81"], out["err81"] = _table_under(sec, "8.1", HDR81)
    out["rows82"], out["err82"] = _table_under(sec, "8.2", HDR82)
    return out


def multiset_diff(exp, got):
    ce, cg = collections.Counter(exp), collections.Counter(got)
    return {"missing": sorted((ce - cg).elements()), "extra": sorted((cg - ce).elements())}


def main(argv):
    root, out = argv[1], argv[2]
    reg_rel = argv[3] if len(argv) > 3 else REG_REL
    inv_rel = argv[4] if len(argv) > 4 else INV_REL
    try:
        inv = json.load(open(os.path.join(root, inv_rel), encoding="utf-8"))
        reg_bytes = open(os.path.join(root, reg_rel), "rb").read()
    except (OSError, ValueError) as e:
        print("input error:", e)
        return 2
    exp81, exp82, facts = expected(inv)
    reg = registry_section(reg_bytes.decode("utf-8"))
    res = {"root": root, "registry": reg_rel, "inventory": inv_rel, "inventory_measured_at": inv.get("measured_at"),
           "facts": facts, "expected_rows81": exp81, "expected_rows82": exp82,
           "registry_eol": {"crlf": reg_bytes.count(b"\r\n"), "lf_only": reg_bytes.count(b"\n") - reg_bytes.count(b"\r\n")}}
    if reg is None:
        res["section8"] = None
        res["verdict"] = "section8 missing"
        rc = 1
    else:
        res["section8"] = {k: reg[k] for k in ("title", "line_range", "list_path", "measured_at", "usage_rule_present", "err81", "err82")}
        d81 = multiset_diff(exp81, reg["rows81"] or [])
        d82 = multiset_diff(exp82, reg["rows82"] or [])
        res["diff81"], res["diff82"] = d81, d82
        res["registry_rows81_n"] = len(reg["rows81"] or [])
        res["registry_rows82_n"] = len(reg["rows82"] or [])
        same = (reg["list_path"] == inv_rel and reg["measured_at"] == inv.get("measured_at") and reg["usage_rule_present"]
                and reg["err81"] is None and reg["err82"] is None
                and not any(d81.values()) and not any(d82.values()))
        res["verdict"] = "same" if same else "differs"
        rc = 0 if same else 1
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": res["verdict"], "n_items": facts["n_items"], "rows81": len(exp81), "rows82": len(exp82)},
                     ensure_ascii=False))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
