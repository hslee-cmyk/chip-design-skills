"""scratch: rejection self-test of the simulated M1 judges (check sim, G1 proto moved_defs, IMPORT-ANY) -- measure only.
For each variant: start from H2, apply an edit, commit (detached), run move_plan check (sim) + G1 moved_defs static V3 count,
IMPORT-ANY (single first import of gmid_lut and sizing_recipe). Appends one JSON line per variant to C:/g200/out/neg_M1.jsonl."""
import json
import os
import re
import subprocess
import sys
import time

R = "C:/g200/r"
A = "skills/analog-gmid-design/assets/"
B = "4b2ab859f02cb51ab4073672321fdb1063129d75"
H2 = "a206346f559fbd588fd842644c4bb650208ad086"
PY = "C:/Python314/python.exe"
OUT = "C:/g200/out/neg_M1.jsonl"
MP = ["--plan", "docs/01-plan/features/gain-budget-gmid-sizing.plan.md", "--registry",
      "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md", "--split", "sizing_recipe.py", "stick_diagram.py",
      "topology_library.py", "design_report.py", "audit_current_forced.py", "--keep", "audit_current_forced.py",
      "--aliases", '{"optimizer": "theta_search.py"}']
ENV = dict(os.environ, TMP="C:/g200/tmp", TEMP="C:/g200/tmp", PYTHONIOENCODING="utf-8",
           APPDATA="C:/Users/HSLEE/AppData/Roaming", HOME="C:/Users/HSLEE")


def git(*a):
    r = subprocess.run(["git", "-C", R, "-c", "core.hooksPath=C:/g200/nohooks"] + list(a), capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr))
    return r.stdout.strip()


def rd(rel):
    return open(os.path.join(R, rel), encoding="utf-8", newline="").read().replace("\r\n", "\n")


def wr(rel, t):
    open(os.path.join(R, rel), "w", encoding="utf-8", newline="").write(t)


def v_edit_body():          # one constant token changed inside a moved def body
    t = rd(A + "gmid_lut.py")
    m = re.search(r"def _invq_newton\(.*?\n(.*?)\n\n\n", t, flags=re.S)
    body = m.group(0)
    new = re.sub(r"(?<![\w.])(\d+)(?![\w.])", lambda x: str(int(x.group(1)) + 1), body, count=1)
    assert new != body
    wr(A + "gmid_lut.py", t.replace(body, new, 1))


def v_drop_reexport():      # one moved name missing from the shim's re-export line
    t = rd(A + "sizing_recipe.py")
    t2 = t.replace("from gmid_lut import GmIdLUT, ", "from gmid_lut import ", 1)
    assert t2 != t
    wr(A + "sizing_recipe.py", t2)


def v_import_shim():        # MOD1 imports the residual shim (ORDER)
    t = rd(A + "gmid_lut.py")
    wr(A + "gmid_lut.py", t.replace("import numpy as np\n", "import numpy as np\nimport sizing_recipe\n", 1))


def v_dup_import():         # same name bound twice by imports (import-dup, M-4 cascade)
    t = rd(A + "gmid_lut.py")
    wr(A + "gmid_lut.py", t.replace("import numpy as np\n", "import numpy as np\nimport numpy as np\n", 1))


def v_no_future():          # MOD file without the source file's __future__ line
    t = rd(A + "gmid_lut.py")
    t2 = t.replace("from __future__ import annotations\n", "", 1)
    assert t2 != t
    wr(A + "gmid_lut.py", t2)


def v_extra_unit():         # a unit assigned to another MOD moved in the same card (move-set)
    t = rd(A + "sizing_recipe.py")
    m = re.search(r"\ndef estimate_mismatch_sigma\(.*?(?=\n\S)", t, flags=re.S)
    assert m
    seg = m.group(0)
    t = t.replace(seg, "\n", 1)
    t = t.replace("from gmid_lut import ", "from gmid_lut import estimate_mismatch_sigma, ", 1)
    wr(A + "sizing_recipe.py", t)
    g = rd(A + "gmid_lut.py")
    wr(A + "gmid_lut.py", g + "\n" + seg.lstrip("\n") + "\n")


VARIANTS = [("edit-body", v_edit_body), ("drop-reexport", v_drop_reexport), ("import-shim", v_import_shim),
            ("dup-import", v_dup_import), ("no-future", v_no_future), ("extra-unit", v_extra_unit)]
sys.path.insert(0, R + "/tools/gates")
for name, fn in VARIANTS:
    git("checkout", "-q", "--detach", H2)
    git("checkout", "-q", "--", ".")
    fn()
    git("add", "-A", "skills")
    git("commit", "-q", "-m", "neg %s (measure only)" % name)
    h = git("rev-parse", "HEAD")
    t0 = time.time()
    r = subprocess.run([PY, "-B", R + "/tools/migrate/move_plan.py", "check", "--root", R, "--base", B, "--head", h,
                        "--card", "gmid_lut.py"] + MP, capture_output=True, text=True, encoding="utf-8", env=ENV)
    try:
        ck = json.loads(r.stdout.splitlines()[0])
        fsum = {k: len(v) for k, v in ck["findings"].items() if v}
        sample = {k: v[:2] for k, v in ck["findings"].items() if v}
    except Exception as e:
        fsum, sample = {"ERROR": str(e) + r.stderr[-300:]}, {}
    # G1 proto static V3 (moved_defs + changed_defs -- the V3 target selection)
    st = subprocess.run([PY, "-B", "-c", (
        "import sys,json;sys.path.insert(0,%r);import reachability as rch, mutate_changed as mc;"
        "b={k:v for k,v in rch.read_tree(%r,%r,rch.GRAPH_PREFIXES).items() if rch._is_source(k)};"
        "h={k:v for k,v in rch.read_tree(%r,%r,rch.GRAPH_PREFIXES).items() if rch._is_source(k)};"
        "mv=rch.moved_defs(b,h);d=[];m=0\n"
        "for p,s in h.items():\n"
        " if b.get(p)==s: continue\n"
        " for q,f in mc.changed_defs(b.get(p),s):\n"
        "  if rch.g1_excluded(mv,p,q,f): continue\n"
        "  d.append(p.split('/')[-1]+'::'+q); m+=sum(1 for _ in mc.mutants(f,s))\n"
        "print(json.dumps({'defs':d[:5],'n_defs':len(d),'mutants':m,'rejected':{k.split('/')[-1]:v['rule'] for k,v in mv['rejected'].items()}}))"
    ) % ("C:/g200/cache/tools/gates", R, B, R, h)], capture_output=True, text=True, encoding="utf-8", env=ENV)
    try:
        v3 = json.loads(st.stdout.splitlines()[-1])
    except Exception:
        v3 = {"ERROR": st.stderr[-300:]}
    imp = {}
    for mod in ("gmid_lut", "sizing_recipe"):
        p = subprocess.run([PY, "-B", "-c", "import %s" % mod], cwd=R + "/" + A, capture_output=True, text=True, encoding="utf-8", env=ENV)
        imp[mod] = "ok" if p.returncode == 0 else (p.stderr.strip().splitlines() or ["?"])[-1][:160]
    rec = {"variant": name, "head": h, "check_exit": r.returncode, "check_findings": fsum, "sample": sample, "v3_static_g1": v3,
           "import_first": imp, "sec": round(time.time() - t0, 1)}
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("variant", "check_exit", "check_findings", "import_first")}, ensure_ascii=False), flush=True)
git("checkout", "-q", "--detach", H2)
git("checkout", "-q", "--", ".")
