"""measure only (W-2): ACF re-export line position. On a scratch copy of assets dir from clone <root> (working tree),
add a stand-in MOD module `topology_authoring.py` defining `_as_set` (the M2 move) and put the re-export line
`from topology_authoring import _as_set` either (gen) right after the first contiguous import block (before sys.path.insert --
the M2 simulation generator) or (design) after the last import of the head group (after `from stick_diagram import load_topology`).
Remove the original `_as_set` def (byte move). Then load ACF in a fresh process (a) as script from another cwd,
(b) via importlib spec_from_file_location from another cwd without assets on sys.path (other-tool import),
(c) `import audit_current_forced` with cwd = assets (IMPORT-ANY condition). Writes JSON lines to <out>.
    python -B w2_acf_position.py <clone root> <scratch dir> <out.jsonl>"""
import ast
import json
import os
import shutil
import subprocess
import sys

ROOT, SCR, OUT = sys.argv[1:4]
PY = sys.executable
A = os.path.join(ROOT, "skills", "analog-gmid-design", "assets")
res = []
for variant in ("gen", "design"):
    d = os.path.join(SCR, "w2_" + variant)
    if os.path.exists(d):
        shutil.rmtree(d)
    shutil.copytree(A, d, ignore=shutil.ignore_patterns("tests", "library", "__pycache__", "*.npz", "lut*"))
    p = os.path.join(d, "audit_current_forced.py")
    raw = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    L = raw.split(nl)
    t = ast.parse(raw)
    fn = [n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == "_as_set"][0]
    a = (fn.decorator_list[0].lineno if fn.decorator_list else fn.lineno)
    body = L[a - 1:fn.end_lineno]
    # stand-in MOD2 holding the moved def (same future line as ACF after FU)
    open(os.path.join(d, "topology_authoring.py"), "w", encoding="utf-8").write(
        "from __future__ import annotations\n\n" + "\n".join(body) + "\n")
    # first contiguous import block end (after docstring/future) vs last import of the head group
    first_block_end = None
    last_head_import = None
    for i, n in enumerate(t.body):
        if i == 0 and isinstance(n, ast.Expr):
            continue
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            if first_block_end is None or first_block_end == "open":
                first_block_end = "open"
            last_head_import = n.end_lineno
            continue
        if first_block_end == "open":
            first_block_end = t.body[i - 1].end_lineno
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and "sys.path" in ast.unparse(n.value.func):
            continue                     # path setup belongs to the head group
        break
    at = first_block_end if variant == "gen" else last_head_import
    line = "from topology_authoring import _as_set"
    newL = []
    for i, l in enumerate(L, 1):
        if a <= i <= fn.end_lineno:
            continue
        newL.append(l)
        if i == at:
            newL.append(line)
    open(p, "w", encoding="utf-8", newline="").write(nl.join(newL))
    other = os.path.join(SCR, "tmp")
    os.makedirs(other, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("PYTHONPATH", None)
    cases = {
        "script_other_cwd": ([PY, "-B", "-c", "import runpy,sys; sys.argv=['x','--help']; "
                              "import importlib.util as u; s=u.spec_from_file_location('acf_main', r'%s'); m=u.module_from_spec(s); "
                              "sys.path.insert(0, r'%s'); s.loader.exec_module(m); print('ok')" % (p, d)], other),
        "spec_import_other_cwd": ([PY, "-B", "-c", "import importlib.util as u; s=u.spec_from_file_location('acf', r'%s'); "
                                   "m=u.module_from_spec(s); s.loader.exec_module(m); print('ok', m._as_set is not None)" % p], other),
        "import_any_cwd_assets": ([PY, "-B", "-c", "import audit_current_forced as m; print('ok', m._as_set is not None)"], d),
    }
    for name, (cmd, cwd) in cases.items():
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env)
        res.append({"variant": variant, "reexport_after_line": at, "case": name, "rc": r.returncode,
                    "tail": (r.stdout + r.stderr).strip().splitlines()[-1:] })
with open(OUT, "a", encoding="utf-8") as fh:
    for x in res:
        fh.write(json.dumps(x, ensure_ascii=False) + "\n")
        print(json.dumps(x, ensure_ascii=False))
