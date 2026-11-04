# -*- coding: utf-8 -*-
"""판정자 점검: 하위 실행 rc, log_errors, 로그별 판, OP-1 출력과의 차이, isolated_env 두 정의 대조, 넷리스트 include."""
import importlib.util, json, os, re, sys, glob
B, ISO = sys.argv[1:3]
SC = os.path.join(ISO, ".ai/verification/20261104-op1b/scripts")
sys.path.insert(0, SC)
import op1b_lib as L
import run_op1b as RUN
spec = importlib.util.spec_from_file_location("bin_rule_lib", os.path.join(ISO, ".ai/verification/20261104-op7a/scripts/bin_rule_lib.py"))
BR = importlib.util.module_from_spec(spec); spec.loader.exec_module(BR)
WORK = os.path.join(B, "run/work")
OP1 = os.path.join(ISO, RUN.OP1_TMP)
out = {"cases": {}}


def walk(x, ptr, keys, hits):
    if isinstance(x, dict):
        for k, v in x.items():
            p = ptr + "/" + str(k)
            if k in keys:
                hits.append((p, v))
            walk(v, p, keys, hits)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk(v, ptr + "/" + str(i), keys, hits)


for rid, rel, sha12, biases, cats in RUN.INPUTS:
    wd = os.path.join(WORK, rid, "o")
    op1d = os.path.dirname(os.path.join(OP1, rel))
    c = {"sub_rc": {}, "log_errors": {}, "logs_without_version": [], "diff_vs_op1": {}}
    for f in sorted(os.listdir(wd)):
        if f.endswith(".log"):
            t = open(os.path.join(wd, f), encoding="utf-8", errors="replace").read()
            v = set(re.findall(r"ngspice-(\d+(?:\.\d+)*)", t))
            if v != {"46"}:
                c["logs_without_version"].append([f, sorted(v)])
    for b in biases:
        fn = [f for f in os.listdir(wd) if f.endswith(f".{b}.sim.json")][0]
        sim = json.load(open(os.path.join(wd, fn), encoding="utf-8"))
        hits = []
        walk(sim, "", {"ngspice_rc"}, hits)
        c["sub_rc"][b] = {p: v for p, v in hits}
        le = []
        walk(sim, "", {"log_errors"}, le)
        c["log_errors"][b] = {p: v for p, v in le if v}
        c.setdefault("skipped", {})[b] = sim.get("skipped")
        op1p = os.path.join(op1d, fn)
        if os.path.exists(op1p):
            old = json.load(open(op1p, encoding="utf-8"))
            d = L.compare_runs(old, sim)
            c["diff_vs_op1"][b] = [p for p in d if not p.endswith("/log")]
        else:
            c["diff_vs_op1"][b] = "op1 파일 없음"
    # 넷리스트: OP-1 대 새 실행 차이 줄 수(공백·경로 제외 안 함)
    nd = {}
    for f in sorted(os.listdir(wd)):
        if f.endswith(".cir"):
            q = os.path.join(op1d, f)
            if os.path.exists(q):
                a = open(os.path.join(wd, f), encoding="utf-8", errors="replace").read().splitlines()
                o = open(q, encoding="utf-8", errors="replace").read().splitlines()
                nd[f] = [(x, y) for x, y in zip(a, o) if x != y][:3] if len(a) == len(o) else ["줄 수 다름", len(a), len(o)]
    c["netlist_diff"] = nd
    out["cases"][rid] = c
e = {"HOME": "x", "USERPROFILE": "y", "HOMEDRIVE": "C:", "HOMEPATH": "z", "SPICE_USERINIT_DIR": "u", "PATH": "p", "OTHER": "o"}
out["isolated_env_equal"] = RUN.isolated_env(e, "h") == BR.isolated_env(e, "h")
out["old_tree"] = "git archive 5fea301e, oracle_*.py 7개 blob 동일"
json.dump(out, open(os.path.join(B, "a3_scan.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
for r, c in out["cases"].items():
    bad = {b: {p: v for p, v in d.items() if v != 0} for b, d in c["sub_rc"].items()}
    print(r, "sub_rc_n", sum(len(d) for d in c["sub_rc"].values()), "nonzero", bad, "log_err", {b: list(x)[:3] for b, x in c["log_errors"].items()}, "skipped", c["skipped"],
          "nover", c["logs_without_version"][:3], "diff_op1", {b: (len(d), d[:6]) if isinstance(d, list) else d for b, d in c["diff_vs_op1"].items()}, "netdiff", {k: v for k, v in c["netlist_diff"].items() if v})
print("isolated_env_equal", out["isolated_env_equal"])
