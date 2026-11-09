"""P10 `20260930-p10-df23-inventory` 계약 빠른 점검기 (오케스트레이터용, 읽기 전용).

regen_df23.py와 코드를 공유하지 않는다(계획 표 파싱·어휘 수집·정확 일치 스캔을 따로 구현).

사용:
    python -B check_contracts.py <inventory.json> [--repo <저장소> --base <커밋>] [--docs] [--selftest]

* JSON만 주면 계약 1(형식)·2·4와 계약 3의 형식 부분(DF 번호 모양)만 본다. 닫힌 집합은 초안 계약 2 문장 그대로.
* --repo/--base를 주면: 계약 3(계획 DF 표 Phase 열, base 계획서 blob), 계약 1(measured_at blob = base blob),
  계약 7(a)(줄 일치, measured_at blob), 7(b)(독립 정확 일치 스캔 누락 0), 7(c)(정확 일치 항목 role 재분류),
  레일 규칙(base library supply_nets)을 추가로 본다.
* --docs: 계약 5(참조 문서의 Phase 2 삭제·이동 이름 표시)를 base blob에서 본다.
* exit 0 = 전부 PASS, 1 = 위반 있음, 2 = 입력 오류.
"""
import argparse
import ast
import collections
import json
import re
import subprocess
import sys

A = "skills/analog-gmid-design/assets"
PLAN = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
CLOSED_DEFAULT = ["3", "4", "5", "6a", "6b", "6c", "7a", "7b", "7c", "해당 없음"]
NA, MSG, BEH = "해당 없음", "메시지뿐", "동작을 정함"
# 계약 5의 이름 집합 N (초안 원문 그대로)
N_NAMES = ["converge_with_parasitics", "slew_rate", "render_stick_diagram", "suggest_headroom_stack_groups",
           "_cmrr_telescopic_class_ab", "_cmrr_telescopic_class_ab_cmfb", "_psrr_telescopic_class_ab",
           "_psrr_telescopic_class_ab_cmfb", "_cmfb_amp_gain_diode_load", "_load_telescopic_topology_cached",
           "_telescopic_class_ab_open_loop_response", "_telescopic_open_loop_device_names",
           "_telescopic_class_ab_open_loop_gains", "_TELESCOPIC_FIXED_BASE", "find_interleaved_symmetric_splits",
           "run_regression_case", "_run_optimize_multistage_case", "RegressionVerdict", "_REGRESSION_ENGINES"]
N_METHODS = ["fT", "junction_cap"]          # 호출형 .name( 만
N_KEYS = ["telescopic_class_ab", "telescopic_class_ab_cmfb"]  # SR 레지스트리 선택 키


class Git:
    def __init__(self, repo):
        self.repo = repo

    def run(self, *a):
        r = subprocess.run(["git", "-C", self.repo, *a], capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.decode("utf-8", "replace"))
        return r.stdout.decode("utf-8")

    def show(self, c, p):
        return self.run("show", f"{c}:{p}")

    def ls(self, c, d):
        return [x for x in self.run("ls-tree", "--name-only", c, d + "/").splitlines() if x]

    def oid(self, c, p):
        return self.run("rev-parse", f"{c}:{p}").strip()


def cells(line):
    line = line.strip().strip("|")
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def plan_tables(plan):
    lines = plan.splitlines()
    # N6.1 Phase 열
    i = next(k for k, l in enumerate(lines) if l.startswith("### N6.1"))
    order, seen_hdr = [], False
    for l in lines[i + 1:]:
        if l.startswith("#"):
            break
        if l.startswith("|"):
            c = cells(l)
            if not seen_hdr:
                seen_hdr = True
                continue
            if re.fullmatch(r"[-: ]+", c[0]):
                continue
            order.append(c[0].replace("*", ""))
    # DF 표: '| DF-' 행 바로 위 헤더에서 'Phase'가 든 열
    rows, col = {}, None
    for k, l in enumerate(lines):
        if l.startswith("| ID ") and k + 2 < len(lines) and lines[k + 2].startswith("| DF-"):
            col = [j for j, c in enumerate(cells(l)) if "Phase" in c][0]
        elif l.startswith("| DF-") and col is not None:
            c = cells(l)
            rows[c[0]] = c[col]
    return order, rows


def phase_tokens(cell, order):
    depth, seg, segs = 0, "", []
    for ch in cell:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            segs.append(seg); seg = ""
        else:
            seg += ch
    segs.append(seg)
    toks = []
    for s in segs:
        m = re.match(r"\s*([0-9][0-9a-z.]*)", s)
        if m:
            t = m.group(1)
            while t and t not in order:
                t = t[:-1]
            if t:
                toks.append(t)
    return [t for t in toks if t != "2"]


def library_vocab(g, c):
    names, nets, circuits, rails = set(), set(), set(), set()
    for p in g.ls(c, A + "/library"):
        if not p.endswith(".topology.json"):
            continue
        circuits.add(p.rsplit("/", 1)[1].replace(".topology.json", ""))
        d = json.loads(g.show(c, p))
        for e in d.get("netlist") or []:
            if isinstance(e, dict):
                names.add(e.get("name"))
                nets.update(v for k, v in e.items() if k in ("source", "drain", "gate", "body", "bulk") and isinstance(v, str))
        for f in ("passive_elements", "ideal_sources"):
            for e in d.get(f) or []:
                if isinstance(e, dict):
                    names.add(e.get("name"))
                    nets.update(t for t in e.get("terminals") or [] if isinstance(t, str))
        rails.update(r for r in d.get("supply_nets") or [] if isinstance(r, str))
    nets |= rails
    vocab = {x for x in (names | nets | circuits) if isinstance(x, str) and len(x) >= 2}
    return vocab, rails


def check(inv, g=None, base=None, docs=False):
    V = collections.defaultdict(list)   # 계약 -> 위반 목록
    items = inv.get("items")
    # ---- 계약 1
    for k in ("measured_at", "scope", "method", "vocabulary", "totals", "items"):
        if k not in inv:
            V["1"].append(f"최상위 키 없음: {k}")
    if not isinstance(items, list):
        return V
    if not re.fullmatch(r"[0-9a-f]{40}", str(inv.get("measured_at", ""))):
        V["1"].append(f"measured_at 40자리 소문자 16진 아님: {inv.get('measured_at')!r}")
    sc = str(inv.get("scope", ""))
    if "run_harness.py" not in sc or "*.py" not in sc:
        V["1"].append(f"scope 문구: {sc!r}")
    for x in items:
        if x.get("role") == BEH and not (isinstance(x.get("function"), str) and x["function"].strip()):
            V["1"].append(f"동작 항목 function 빔: {x.get('file')}:{x.get('line')}")
    # ---- 계약 2
    order, rows = None, None
    closed = CLOSED_DEFAULT
    if g is not None:
        order, rows = plan_tables(g.show(base, PLAN))
        closed = order[order.index("2") + 1:] + [NA]
        if closed != CLOSED_DEFAULT:
            V["2"].append(f"계획 N6.1에서 읽은 닫힌 집합 {closed} != 초안 {CLOSED_DEFAULT}")
    for x in items:
        ph, pm = x.get("phase"), str(x.get("plan_mapping", ""))
        loc = f"{x.get('file')}:{x.get('line')} {x.get('literal')!r}"
        if ph not in closed:
            V["2"].append(f"phase 닫힌 집합 밖/없음 {ph!r}: {loc}")
        need_reason = ph == NA or not re.match(r"^DF-\d+", pm)
        if need_reason and not str(x.get("phase_reason", "")).strip():
            V["2"].append(f"phase_reason 없음(phase={ph}, plan_mapping={pm}): {loc}")
        if x.get("role") == MSG and ph != NA:
            V["2"].append(f"메시지뿐인데 phase={ph}: {loc}")
    # ---- 계약 3
    for x in items:
        m = re.match(r"^DF-(\d+)", str(x.get("plan_mapping", "")))
        if not m:
            continue
        df = f"DF-{int(m.group(1)):02d}"
        loc = f"{x.get('file')}:{x.get('line')} {x.get('literal')!r}"
        if rows is None:
            continue
        if df not in rows:
            V["3"].append(f"{df} 계획 DF 표에 행 없음: {loc}")
            continue
        toks = phase_tokens(rows[df], order)
        if x.get("phase") not in toks:
            V["3"].append(f"{df} Phase 열 {toks}에 phase {x.get('phase')!r} 없음: {loc}")
    # ---- 계약 4
    t = inv.get("totals", {})
    if t.get("n_items") != len(items):
        V["4"].append(f"n_items {t.get('n_items')} != {len(items)}")
    for key, fld in (("by_role", "role"), ("by_phase", "phase"), ("by_plan_mapping", "plan_mapping")):
        got = dict(collections.Counter(x.get(fld) for x in items))
        if t.get(key) != got:
            V["4"].append(f"{key} 불일치: 적힘 {t.get(key)} / 셈 {got}")
    if g is None:
        return V
    if docs:
        V.update(check_docs(g, base))
    # ---- 계약 1 blob, 레일, 7(a)(b)(c)
    m = inv.get("measured_at")
    if not re.fullmatch(r"[0-9a-f]{40}", str(m)):
        for c in ("7a", "7b", "7c"):
            V[c].append("measured_at이 없어 blob 대조 불가")
        return V
    scope = [p for p in g.ls(base, A) if p.endswith(".py") and p.count("/") == A.count("/") + 1] + ["workspaces/run_harness.py"]
    for p in scope:
        try:
            if g.oid(m, p) != g.oid(base, p):
                V["1"].append(f"measured_at blob != base blob: {p}")
        except RuntimeError:
            V["1"].append(f"measured_at에 없음: {p}")
    vocab, rails = library_vocab(g, base)
    for x in items:
        if x.get("role") == BEH and x.get("literal") in rails and x.get("context") == "운영" \
                and not re.match(r"^DF-(19|26)\b", str(x.get("plan_mapping", ""))):
            V["3"].append(f"운영 레일 넷 이름 리터럴인데 plan_mapping {x.get('plan_mapping')!r}: {x['file']}:{x['line']}")
    src = {p: g.show(m, p) for p in scope}
    for x in items:
        L = src.get(x["file"], "").splitlines()
        if not (0 < x["line"] <= len(L)) or L[x["line"] - 1].strip() != str(x.get("source_line", "")).strip():
            V["7a"].append(f"줄 불일치: {x['file']}:{x['line']}")
    have = collections.Counter((x["file"], x["line"], x["literal"]) for x in items)
    role_of = collections.defaultdict(list)
    for x in items:
        role_of[(x["file"], x["line"], x["literal"])].append(x.get("role"))
    need = collections.Counter()
    exp_role = collections.defaultdict(list)
    for p, s in src.items():
        tree = ast.parse(s)
        doc = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                doc.add(n.value)
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in vocab:
                need[(p, n.lineno, n.value)] += 1
                exp_role[(p, n.lineno, n.value)].append(MSG if n in doc else BEH)
    for k, c in (need - have).items():
        V["7b"].append(f"정확 일치 항목 누락 x{c}: {k[0]}:{k[1]} {k[2]!r}")
    for k in need:
        if k in role_of and collections.Counter(exp_role[k]) != collections.Counter(role_of[k]):
            V["7c"].append(f"role 재분류 불일치: {k[0]}:{k[1]} {k[2]!r} 기대 {exp_role[k]} 목록 {role_of[k]}")
    if docs:
        V.update(check_docs(g, base))
    return V


def check_docs(g, base):
    V = collections.defaultdict(list)
    defs_engine, defs_tools = set(), collections.defaultdict(set)
    files = [p for p in g.ls(base, A) if p.endswith(".py") and p.count("/") == A.count("/") + 1] + ["workspaces/run_harness.py"]

    def top_names(s):
        out = set()
        for n in ast.parse(s).body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(n.name)
                if isinstance(n, ast.ClassDef):
                    out |= {m.name for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
            elif isinstance(n, (ast.Assign, ast.AnnAssign)):
                for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                    if isinstance(t, ast.Name):
                        out.add(t.id)
        return out

    sr_keys = set()
    for p in files:
        s = g.show(base, p)
        defs_engine |= top_names(s)
        if p.endswith("sizing_recipe.py"):
            for n in ast.parse(s).body:
                if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in
                                                     ("_CMRR_ESTIMATOR_REGISTRY", "_PSRR_ESTIMATOR_REGISTRY") for t in n.targets) \
                        and isinstance(n.value, ast.Dict):
                    sr_keys |= {k.value for k in n.value.keys if isinstance(k, ast.Constant)}
    for p in g.ls(base, A + "/tests/tools"):
        if p.endswith(".py"):
            for nm in top_names(g.show(base, p)):
                defs_tools[nm].add(p.rsplit("/", 1)[1])
    docs = [p for p in g.run("ls-tree", "-r", "--name-only", base, "skills/analog-gmid-design/references/").splitlines()
            if p.endswith(".md")] + ["skills/analog-gmid-design/SKILL.md", "skills/analog-gmid-design/skill-validation-prompt.md"]
    pats = [(n, re.compile(r"(?<![A-Za-z0-9_])" + re.escape(n) + r"(?![A-Za-z0-9_])"), "name") for n in N_NAMES] + \
           [(n, re.compile(r"\." + re.escape(n) + r"\("), "method") for n in N_METHODS] + \
           [(n, re.compile(r"(?<![A-Za-z0-9_])" + re.escape(n) + r"(?![A-Za-z0-9_])"), "key") for n in N_KEYS]
    for d in docs:
        try:
            text = g.show(base, d)
        except RuntimeError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for n, pat, kind in pats:
                if not pat.search(line):
                    continue
                if kind == "key":
                    status = "live" if n in sr_keys else "deleted"
                elif n in defs_engine:
                    status = "live"
                elif n in defs_tools:
                    status = "moved:" + sorted(defs_tools[n])[0]
                else:
                    status = "deleted"
                if status == "live":
                    continue
                if status == "deleted" and "Phase 2에서 삭제" not in line:
                    V["5"].append(f"{d}:{i} `{n}` 삭제 표시 없음")
                if status.startswith("moved:"):
                    mod = status.split(":", 1)[1]
                    if not ("Phase 2에서" in line and f"tests/tools/{mod}" in line):
                        V["5"].append(f"{d}:{i} `{n}` 이동 표시(Phase 2에서 + tests/tools/{mod}) 없음")
    return V


def selftest():
    """합성 입력으로 거부/통과를 확인(초안 '거부해야 할 입력')."""
    base_item = {"file": "a.py", "line": 1, "literal": "x", "role": BEH, "function": "f", "phase": "4",
                 "plan_mapping": "DF-23", "source_line": "x"}

    def inv(its):
        return {"measured_at": "a" * 40, "scope": "A/*.py + workspaces/run_harness.py", "method": "", "vocabulary": {},
                "totals": {"n_items": len(its), "by_role": dict(collections.Counter(i["role"] for i in its)),
                           "by_phase": dict(collections.Counter(i.get("phase") for i in its)),
                           "by_plan_mapping": dict(collections.Counter(i.get("plan_mapping") for i in its))}, "items": its}

    bad = [dict(base_item, phase=None), dict(base_item, phase="2"), dict(base_item, phase="8"), dict(base_item, phase=""),
           dict(base_item, phase=NA), dict(base_item, role=MSG, phase="4"), dict(base_item, function=""),
           dict(base_item, plan_mapping="신규", phase="3")]
    ok = True
    for b in bad:
        v = check(inv([b]))
        if not any(v.values()):
            print("SELFTEST FAIL(거부 안 됨):", b); ok = False
    good = [dict(base_item), dict(base_item, plan_mapping="신규", phase="3", phase_reason="픽스처"),
            dict(base_item, role=MSG, phase=NA, phase_reason="메시지")]
    v = check(inv(good))
    if any(v.values()):
        print("SELFTEST FAIL(오거부):", dict(v)); ok = False
    x = inv(good); x["totals"]["n_items"] += 1
    if not check(x)["4"]:
        print("SELFTEST FAIL: n_items 틀림 미검출"); ok = False
    x = inv(good); x["measured_at"] = "abc"
    if not check(x)["1"]:
        print("SELFTEST FAIL: measured_at 미검출"); ok = False
    order = ["0", "0(문서)", "0.5", "1", "2", "3", "4", "5", "6a", "6b", "6c", "7a", "7b", "7c"]
    assert phase_tokens("4(PDK 상수 한 곳 선언 U-30으로 복사 제거), 7b(`x` v5 이관에서 교체)", order) == ["4", "7b"]
    assert phase_tokens("2(전수 목록·레지스트리 기록), 4(일반 규칙으로 교체)", order) == ["4"]
    assert phase_tokens("6b(a, b), 6c(IC4 PASS로 확인)", order) == ["6b", "6c"]
    print("selftest", "PASS" if ok else "FAIL")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory", nargs="?")
    ap.add_argument("--repo")
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--docs", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    if not a.inventory:
        ap.error("inventory 경로 필요")
    try:
        inv = json.load(open(a.inventory, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("입력 오류:", e); return 2
    g = Git(a.repo) if a.repo else None
    base = g.run("rev-parse", a.base + "^{commit}").strip() if g else None
    V = check(inv, g, base, a.docs)
    names = ["1", "2", "3", "4"] + (["7a", "7b", "7c"] if g else []) + (["5"] if a.docs else [])
    for c in names:
        v = V.get(c, [])
        print(f"계약 {c}: {'PASS' if not v else f'FAIL ({len(v)})'}")
        for s in v[:25]:
            print("   ", s)
        if len(v) > 25:
            print(f"    ... 외 {len(v) - 25}")
    return 0 if not any(V.get(c) for c in names) else 1


if __name__ == "__main__":
    sys.exit(main())
