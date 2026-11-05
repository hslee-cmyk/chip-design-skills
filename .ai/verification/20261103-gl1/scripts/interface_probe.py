"""Auditor's own toy: interface behaviours the frozen tests do not pin (step 3 'coverage gaps').
usage: python -I interface_probe.py <clone root> <work dir> <out json>"""
import json, shutil, subprocess, sys
from pathlib import Path

root, work, outp = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
S = root / "skills/analog-gmid-design/gmid_engine/tests/structure"
TOOL = root / "tools/audit/scan_shared_calls.py"
sys.dont_write_bytecode = True
sys.path.insert(0, str(S))
import structure_checks as c

if work.exists():
    shutil.rmtree(work)
res = {}


def tree(name, files):
    e = work / name / "gmid_engine"
    for rel, src in files.items():
        p = e / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(src, encoding="utf-8", newline="\n")
    return e


def tool(e, *touching):
    out = e.parent / "out"
    if out.exists():
        shutil.rmtree(out)
    cmd = [sys.executable, str(TOOL), "--engine", str(e), "--out", str(out)]
    if touching:
        cmd += ["--touching", *touching]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        return {"rc": r.returncode}
    calls = json.loads((out / "calls.json").read_text(encoding="utf-8"))
    cand = (out / "b_candidates.tsv").read_text(encoding="utf-8").splitlines()[1:]
    shared = (out / "shared.tsv").read_text(encoding="utf-8").splitlines()[1:]
    return {"rc": 0, "keys": sorted((c_["caller_mod"].split(".")[-1], c_["line"], tuple(c_["arg_keys"]), tuple(c_["leaves"])) for c_ in calls),
            "cand": [x.split("\t")[1:] for x in cand], "shared": len(shared), "n_calls": len(calls),
            "limits": json.loads((out / "limits.json").read_text(encoding="utf-8"))}


DEFS = "def f(x):\n    return x\n"
# (leaf: .value)
e = tree("value", {"defs.py": DEFS, "a.py": 'from .defs import f\ndef ra(p):\n    return f(p.value("device", 3, "dc_op"))\n',
                   "b.py": 'from .defs import f\ndef rb(p):\n    return f(p.value("device", 4, "dc_op"))\n'})
res["value_leaf"] = tool(e)
# (import .. as and module alias)
e = tree("alias", {"defs.py": DEFS, "a.py": 'from . import defs as dd\ndef ra(p):\n    return dd.f(p.column("device", "dc_op"))\n',
                   "b.py": 'import gmid_engine.defs as qq\ndef rb(p):\n    return qq.f(p.column("device", "dc_op"))\n'})
res["import_as"] = tool(e)
# (for and comprehension local trace)
e = tree("forc", {"defs.py": DEFS, "a.py": 'from .defs import f\ndef ra(p):\n    for v in p.column("device", "dc_op"):\n        f(v)\n',
                  "b.py": 'from .defs import f\ndef rb(p):\n    return [f(v) for v in p.column("device", "dc_op")]\n'})
res["for_comp"] = tool(e)
# (literal and global leaf: not field -> D)
e = tree("litg", {"defs.py": DEFS, "a.py": 'from .defs import f\nK = 1\ndef ra():\n    return f(K)\n', "b.py": 'from .defs import f\ndef rb():\n    return f(3)\n'})
res["literal_global"] = tool(e)
# (two same-module callers with different inputs: must stay a parameter leaf, not guess one)
e = tree("twocallers", {"defs.py": DEFS, "a.py": 'from .defs import f\ndef g(x):\n    return f(x)\ndef r1(p):\n    return g(p.column("device", "dc_op"))\ndef r2(p):\n    return g(p.column("device", "ss_dev"))\n',
                        "b.py": 'from .defs import f\ndef rb(p):\n    return f(p.column("device", "dc_op"))\n'})
res["two_same_module_callers"] = tool(e)
# (--touching leaves calls/shared unchanged)
e = tree("tch", {"defs.py": DEFS + "def h(x):\n    return x\n", "a.py": 'from .defs import f\ndef ra(p):\n    return f(p.column("device", "dc_op"))\n',
                 "b.py": 'from .defs import f, h\ndef rb(p):\n    h(p.column("device", "x"))\n    return f(p.column("device", "dc_op"))\n',
                 "c.py": 'from .defs import h\ndef rc(p):\n    return h(p.column("device", "y"))\n'})
ta, tb = tool(e), tool(e, "c.py")
res["touching_invariance"] = {"same_calls": ta["keys"] == tb["keys"], "same_shared": ta["shared"] == tb["shared"], "cand_all": ta["cand"], "cand_c": tb["cand"]}
# (repo-style touching path, A-40 says the engine-relative form is the rule)
res["touching_repo_style_rc"] = tool(e, "skills/x/gmid_engine/c.py")["rc"]
# (value type wrappers not in fixtures)
vt = tree("vt", {"t.py": "from dataclasses import dataclass\n@dataclass(frozen=True)\nclass T:\n    a: int = 0\n",
                 "u.py": "from types import MappingProxyType\nfrom .t import T\nA = set([T()])\nB = dict(k=T())\nC = MappingProxyType({'k': T()})\nD = frozenset((T(),))\nE = list(T() for _ in ())\n"
                         "class K:\n    x: 'tuple[T, ...]' = ()\n    def m(self):\n        self.y = T()\n        self.z: T = None\n        q = T()\n        return q\n"
                         "def fn(p: T) -> T:\n    w = T()\n    return w\n"})
res["vt_wrappers"] = sorted((v.kind, v.path, v.line, v.detail) for v in c.check_value_types(vt)[1])
# (lint behaviours)
g = tree("g", {"o.py": "from collections import OrderedDict\nimport functools\nclass X:\n    def m(self):\n        self.a, self.b = {}, []\n        self.c = {} if self else None\n        import os\n        return memo.call(os.path, 1)\n"
                       "    y = z = {}\nclass Y:\n    def __init__(self):\n        object.__setattr__(self, 'a', {})\ndef f(x, memo):\n    x.id(1)\n    return memo.call(g2, 1)\nfrom dataclasses import field\nW = field(default_factory=lambda: {})\n"})
res["g8_edges"] = sorted((v.kind, v.line, v.detail) for v in c.check_g8(g)[1])
outp.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
print(outp.read_text(encoding="utf-8"))
