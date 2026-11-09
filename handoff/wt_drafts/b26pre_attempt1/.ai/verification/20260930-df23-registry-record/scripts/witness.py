"""V3 생존 변이 판정(auditor): 생존 변이마다 원본·변이 reg_check를 메모리에서 만들어(exec, 파일 쓰기 없음)
같은 입력에 결과가 다른 증인 입력이 있는지(비등가) / 승인 9개는 무작위·경계 입력 다수에서 결과가 같은지(등가 재판정) 잰다.
사용: PYTHONPATH=<게이트 캐시> python -P witness.py <병합본 복제본> <base 커밋> <out.json>"""
import copy
import io
import json
import os
import random
import sys
import contextlib
import tempfile

root, base_rev, out = sys.argv[1:4]
cache = os.environ["PYTHONPATH"].split(os.pathsep)[0]
sys.path.insert(0, cache)
import mutate_changed as mc  # noqa: E402
import subprocess  # noqa: E402

REL = "skills/analog-gmid-design/assets/tests/tools/reg_check.py"
head_src = open(os.path.join(root, *REL.split("/")), encoding="utf-8").read().replace("\r\n", "\n")
base_src = subprocess.run(["git", "-C", root, "show", "%s:%s" % (base_rev, REL)], capture_output=True).stdout.decode("utf-8").replace("\r\n", "\n")
defs = mc.changed_defs(base_src, head_src)
plan = {}
for q, fn in defs:
    for op, path, mfn in mc.mutants(fn, head_src):
        plan["reg_check:%s:%s:%s" % (q, op, path)] = (fn, mfn)


def load(src):
    ns = {"__name__": "reg_check_w"}
    exec(compile(src, "reg_check_w.py", "exec"), ns)
    return ns


ORIG = load(head_src)


def mutant_ns(mid):
    fn, mfn = plan[mid]
    return load(mc._replace_def(head_src, fn, mfn))


# ---- 합성 입력(지어낸 이름) ----
BEH, MSG = "동작을 정함", "메시지뿐"
REL_INV = "docs/an/inv.json"
MEAS = "0" * 40


def item(file, function, role, phase, pm):
    return {"file": file, "function": function, "role": role, "phase": phase, "plan_mapping": pm}


ITEMS = [item("p/mod_a.py", "alpha_fn", BEH, "4", "DF-19"), item("p/mod_a.py", "alpha_fn", BEH, "3", "신규"),
         item("q/mod_b.py", "beta_fn", MSG, "해당 없음", "DF-2")]
INV = {"measured_at": MEAS, "items": ITEMS}
R81 = [("role", BEH, "2"), ("role", MSG, "1"), ("phase", "3", "1"), ("phase", "4", "1"), ("phase", "해당 없음", "1")]
R82 = [("`alpha_fn`", "mod_a.py", "2", "DF-19, 신규", "3, 4")]


def tbl(h, rows):
    return ["| " + " | ".join(h) + " |", "|" + "---|" * len(h)] + ["| " + " | ".join(r) + " |" for r in rows]


H81, H82 = ("축", "값", "항목 수"), ("함수", "파일", "항목 수", "DF", "담당 Phase")
TITLE = "## 8. DF-23 -- 기록"


def sec8(blank=True, r81=R81, r82=R82, extra81=(), extra82=(), pre=()):
    b = [""] if blank else []
    L = [TITLE] + b + [f"목록: `{REL_INV}`", f"measured_at: `{MEAS}`"] + b
    L += ["### 8.1 총계"] + b + tbl(H81, r81) + b + list(extra81)
    L += ["### 8.2 함수별"] + b + tbl(H82, r82) + b + list(extra82)
    return list(pre) + L


def run(ns, lines, inv=INV):
    try:
        return sorted((f["rule"], f["name"], f["detail"]) for f in ns["check_df23"]("\n".join(lines), copy.deepcopy(inv), REL_INV))
    except Exception as e:  # noqa: BLE001  (판정 비교용: 예외 타입도 결과로 본다)
        return ("EXC", type(e).__name__)


WRONG81 = tbl(H81, [("role", "가짜", "9")])
WRONG82 = tbl(H82, [("`ghost_fn`", "mod_z.py", "1", "DF-1", "3")])
WITNESS = {
    # break 삭제: 첫 `### 8.1` 대신 마지막 `### 8.1`
    "reg_check:_df23_rows_under:stmt_delete:body[2].body[0].body[1]":
        sec8(extra82=["### 8.1 (사본)", ""] + WRONG81),
    # 끝 탐색을 start+2부터: 소절 제목 바로 다음 줄이 `### `
    "reg_check:_df23_rows_under:const+:body[5].iter.args[0].right":
        sec8(blank=False, extra81=[]) [:0] + [TITLE, "", f"목록: `{REL_INV}`", f"measured_at: `{MEAS}`", "",
                                               "### 8.1 총계", "### 참고"] + WRONG81 + ["", "### 8.2 함수별", ""] + tbl(H82, R82),
    # 표 탐색 시작 start-1: `### 8.1`이 절 첫 줄(제목 바로 다음)일 때 sec[-1:end]
    "reg_check:_df23_rows_under:arith:body[8].iter.args[0].slice.lower":
        [TITLE, "### 8.1 총계"] + tbl(H81, R81) + ["", f"목록: `{REL_INV}`", f"measured_at: `{MEAS}`", "", "### 8.2 함수별"] + tbl(H82, R82),
    # 표 탐색 시작 start+2: 표 머리가 소절 제목 바로 다음 줄
    "reg_check:_df23_rows_under:const+:body[8].iter.args[0].slice.lower.right":
        sec8(blank=False),
    # §8 끝 탐색 start+2: 제목 바로 다음 줄이 `## `
    "reg_check:check_df23:const+:body[7].iter.args[0].right":
        [TITLE, "## 9. 다른 절", f"목록: `{REL_INV}`", f"measured_at: `{MEAS}`", "### 8.1 총계"] + tbl(H81, R81) + ["### 8.2 함수별"] + tbl(H82, R82),
    # break 삭제: §8 끝이 첫 `## `가 아니라 마지막 `## `
    "reg_check:check_df23:stmt_delete:body[7].body[0].body[1]":
        [TITLE, "", f"목록: `{REL_INV}`", f"measured_at: `{MEAS}`", "", "## 9. 다른 절", "", "### 8.1 총계", ""] + tbl(H81, R81)
        + ["", "### 8.2 함수별", ""] + tbl(H82, R82) + ["", "## 10. 또 다른 절"],
    # sec 시작 start-1: 제목 앞 줄이 `목록:` 줄
    "reg_check:check_df23:arith:body[8].value.slice.lower":
        [f"목록: `{REL_INV}`"] + [TITLE, f"measured_at: `{MEAS}`", "", "### 8.1 총계"] + tbl(H81, R81) + ["### 8.2 함수별"] + tbl(H82, R82),
    # sec 시작 start+2: `목록:` 줄이 제목 바로 다음 줄
    "reg_check:check_df23:const+:body[8].value.slice.lower.right":
        sec8(blank=False),
    # detail의 r[2:5] -> r[2:6]: 칸이 머리보다 많은 행의 값이 다를 때 detail
    "reg_check:check_df23:const+:body[17].orelse[1].body[3].orelse[0].orelse[0].body[0].value.args[0].args[3].values[1].value.args[0].slice.upper":
        sec8(r82=[("`alpha_fn`", "mod_a.py", "9", "DF-19, 신규", "3, 4", "덧칸")]),
}

res = {"nonequiv": {}, "equiv_recheck": {}}
for mid, lines in WITNESS.items():
    a, b = run(ORIG, lines), run(mutant_ns(mid), lines)
    res["nonequiv"][mid] = {"in_plan": True, "orig": a, "mutant": b, "differs": a != b}

# 승인 9개 등가 재판정: 무작위·경계 입력에서 원본과 같은지 + main 두 개는 CLI exit
APPROVED = ["reg_check:_df23_expected:const+:body[7].body[4].value.value.args[1]",
            "reg_check:check_df23:arith:body[15].orelse[1].body[0].value.right.right",
            "reg_check:check_df23:const+:body[15].orelse[1].body[0].value.right.right.left",
            "reg_check:check_df23:arith:body[17].orelse[1].body[0].value.right.right",
            "reg_check:check_df23:const+:body[17].orelse[1].body[0].value.right.right.left",
            "reg_check:_df23_rows_under:const-:body[8].iter.args[0].slice.lower.right",
            "reg_check:check_df23:const-:body[8].value.slice.lower.right",
            "reg_check:main:stmt_delete:body[8].body[3].body[5]",
            "reg_check:main:stmt_delete:body[8].body[3].body[5].body[0]"]
rnd = random.Random(20261001)
corpus = list(WITNESS.values()) + [sec8(), sec8(blank=False), [TITLE], ["## 7. x"] + sec8()]
for _ in range(400):
    L = sec8(blank=rnd.random() < 0.5)
    k = rnd.randrange(6)
    if k == 0:
        L = [ln for ln in L if rnd.random() > 0.15]
    elif k == 1:
        i = rnd.randrange(len(L))
        L[i] = L[i] + " | 덧칸" if L[i].startswith("|") else L[i]
    elif k == 2:
        i = rnd.randrange(len(L))
        if L[i].startswith("| ") and "---" not in L[i]:
            L[i] = "|".join(L[i].split("|")[:-2]) + "|"
    elif k == 3:
        L = L + ["## 9. 꼬리"] + sec8()
    elif k == 4:
        rnd.shuffle(L)
    corpus.append(L)
invs = [INV, {"measured_at": MEAS, "items": ITEMS + [item("r/mod_a.py", "x_fn", MSG, "3", "신규")]},
        {"measured_at": MEAS, "items": ITEMS + [item("a/b\\c/mod_c.py", "y_fn", BEH, "7a", "DF-3")]}]
for mid in APPROVED:
    if not mid.startswith("reg_check:main"):
        ns = mutant_ns(mid)
        diffs = sum(1 for L in corpus for inv in invs if run(ORIG, L, inv) != run(ns, L, inv))
        res["equiv_recheck"][mid] = {"in_plan": mid in plan, "inputs": len(corpus) * len(invs), "diffs": diffs}
# main 두 개: 최상위가 dict 아닌 목록 파일들 + 정상 목록으로 exit·stdout 비교
tmp = tempfile.mkdtemp(prefix="wit_", dir="C:/g88")
os.makedirs(os.path.join(tmp, "skills/analog-gmid-design/assets"), exist_ok=True)
open(os.path.join(tmp, "skills/analog-gmid-design/assets/e_mod.py"), "w", encoding="utf-8").write("def kept_fn():\n    return 1\n")
reg = os.path.join(tmp, "reg.md")
open(reg, "w", encoding="utf-8").write("\n".join(["# r", "## 7. D", "", "### e_mod.py (1)", ""]
                                                 + tbl(("함수", "책임", "이관 목적지", "처리", "비고"), [("`kept_fn`", "a", "b", "보류(Phase 3)", "c")])
                                                 + [""] + sec8()) + "\n")
payloads = ["[1, 2]", "\"s\"", "null", "3", "true", json.dumps(INV, ensure_ascii=False), "{\"items\": []}", "{not json"]


def cli(ns, payload):
    p = os.path.join(tmp, "docs", "an", "inv.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(payload)
    o, e = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e):
        rc = ns["main"](["--registry", reg, "--root", tmp, "--df23-inventory", p])
    return rc, o.getvalue()


for mid in [m for m in APPROVED if m.startswith("reg_check:main")]:
    ns = mutant_ns(mid)
    rows = [(pl, cli(ORIG, pl), cli(ns, pl)) for pl in payloads]
    res["equiv_recheck"][mid] = {"in_plan": mid in plan, "inputs": len(rows),
                                 "diffs": sum(1 for _, a, b in rows if a != b),
                                 "exits": [[pl, a[0], b[0]] for pl, a, b in rows]}
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"nonequiv_differs": {k.split(":", 2)[2]: v["differs"] for k, v in res["nonequiv"].items()},
                  "equiv": {k.split(":", 2)[2]: (v["in_plan"], v["diffs"], v["inputs"]) for k, v in res["equiv_recheck"].items()}},
                 ensure_ascii=False, indent=1))
