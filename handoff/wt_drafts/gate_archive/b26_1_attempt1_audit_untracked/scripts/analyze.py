# pytest -rA 출력과 red 수집 파일을 읽어 base 기준값·판정 변화·새 test 네 칸 표를 만든다.
import json, re, sys, collections
O = sys.argv[1]
NEWF = "skills/analog-gmid-design/assets/tests/contracts/test_b26_rail_accessor.py"
# card '판정 유형 근거' 네 칸 -- test 이름(계약 번호)과 진입점(시그니처 불변 공개 진입점 / rails= 직접 호출)으로 배정
COL = {}
def col_of(name):
    n = name.split("[")[0]
    if n.startswith("test_b26_c1_") or n.startswith("test_b26_c3_"):
        return "신규 심볼 red"
    if n == "test_b26_c4_existing_defaults_unchanged":
        return "green 회귀 고정"
    if n in ("test_b26_c4_rails_keyword_only_without_default", "test_b26_c7a_direct_calls_rail_shared_pair_not_candidate",
             "test_b26_c7a_positive_undeclared_shared_source_is_candidate", "test_b26_c7b_direct_kcl_edges_skip_declared_rails",
             "test_b26_c7e_gap_fill_rail_sites", "test_b26_c7_reverse_direct_calls_treat_undeclared_names_as_internal",
             "test_b26_c14_no_gate_input_returns") or n.startswith("test_b26_c13_"):
        return "base TypeError 집계 밖"
    return "단언 red"

LINE = re.compile(r"^(PASSED|FAILED|ERROR|XFAIL|XPASS|SKIPPED) (.+?)(?: - (.*))?$")
def norm(tid):
    path, sep, rest = tid.partition("::")
    path = path.replace("\\", "/")
    i = path.find("/skills/analog-gmid-design/")
    return (path[i + 1:] if i >= 0 else path) + sep + rest

def parse(tag):
    res = {}
    tail = ""
    with open("%s/pytest_%s.out.txt" % (O, tag), encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            m = LINE.match(line)
            if m:
                st, tid, msg = m.groups()
                tid = norm(tid)
                if st == "SKIPPED":
                    continue
                prev = res.get(tid)
                if prev and prev[0] in ("FAILED", "ERROR"):
                    continue
                res[tid] = (st, msg or "")
            if re.match(r"^\d+ (passed|failed)", line):
                tail = line
    return res, tail

def exc_of(msg):
    m = re.match(r"^([A-Za-z_][\w\.]*)(?::|$)", msg or "")
    return m.group(1) if m else (msg or "")[:40]

def strip_root(tid):
    return tid

b1, b1tail = parse("b1_s0")
t0, t0tail = parse("t1red_s0")
t1, t1tail = parse("t1red_s1")
def red(tag):
    out = []
    with open("%s/red_%s.jsonl" % (O, tag), encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out
r0, r1 = red("t1red_s0"), red("t1red_s1")
rk0 = sorted((x["test_id"], x["exc_type"], x["failure_hash"]) for x in r0)
rk1 = sorted((x["test_id"], x["exc_type"], x["failure_hash"]) for x in r1)
red_by = {x["test_id"]: x["exc_type"] for x in r0}

summary = {"b1_tail": b1tail, "t1_s0_tail": t0tail, "t1_s1_tail": t1tail,
           "b1_counts": dict(collections.Counter(v[0] for v in b1.values())),
           "t1_s0_counts": dict(collections.Counter(v[0] for v in t0.values())),
           "t1_s1_counts": dict(collections.Counter(v[0] for v in t1.values())),
           "t1_seed_outcomes_identical": {k: v[0] for k, v in t0.items()} == {k: v[0] for k, v in t1.items()},
           "red_s0_n": len(rk0), "red_s1_n": len(rk1), "red_seed_identical": rk0 == rk1}
# 새 test 표
new_rows = []
for tid, (st, msg) in sorted(t0.items()):
    if tid.startswith(NEWF + "::"):
        name = tid.split("::", 1)[1]
        new_rows.append({"test_id": tid, "column": col_of(name), "t1_outcome": st, "exc": exc_of(msg),
                         "msg": msg[:200], "red_capture": red_by.get(tid)})
summary["new_tests"] = new_rows
summary["new_by_column"] = {}
for r in new_rows:
    c = summary["new_by_column"].setdefault(r["column"], collections.Counter())
    c["%s/%s/red=%s" % (r["t1_outcome"], r["exc"], r["red_capture"])] += 1
summary["new_by_column"] = {k: dict(v) for k, v in summary["new_by_column"].items()}
# 기존 test 판정 변화(B1 -> T1, 엔진 = B1)
changed = []
for tid in sorted(set(b1) | set(t0)):
    if tid.startswith(NEWF + "::"):
        continue
    a = b1.get(tid, ("ABSENT", ""))
    b = t0.get(tid, ("ABSENT", ""))
    if a[0] != b[0]:
        changed.append({"test_id": tid, "b1": a[0], "t1": b[0], "t1_exc": exc_of(b[1]), "t1_msg": b[1][:200],
                        "red_capture": red_by.get(tid)})
summary["existing_changed"] = changed
summary["existing_changed_by_exc"] = dict(collections.Counter(c["t1_exc"] for c in changed))
summary["b1_failed_ids"] = sorted(k for k, v in b1.items() if v[0] in ("FAILED", "ERROR"))
summary["red_capture_s0"] = [{"test_id": a, "exc_type": b, "failure_hash": c} for a, b, c in rk0]
red_set_hash = __import__("hashlib").sha256("".join("%s\t%s\n" % (a, b) for a, b, c in rk0).encode()).hexdigest()
summary["red_set_sha256_testid_exctype"] = red_set_hash
json.dump(summary, open("%s/order3_red_analysis.json" % O, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({k: v[0] for k, v in sorted(b1.items())}, open("%s/order3_base_ids_B1.json" % O, "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)
print(json.dumps({k: summary[k] for k in summary if k not in ("new_tests", "existing_changed", "red_capture_s0", "b1_failed_ids")},
                 ensure_ascii=False, indent=1))
print("b1 failed:", summary["b1_failed_ids"])
for r in new_rows:
    print(r["column"], "|", r["test_id"].split("::")[1], "|", r["t1_outcome"], r["exc"], "| red:", r["red_capture"], "|", r["msg"][:90])
print("--- existing changed", len(changed))
for c in changed:
    print(c["test_id"], c["b1"], "->", c["t1"], c["t1_exc"], "| red:", c["red_capture"], "|", c["t1_msg"][:100])
