"""'actually rejects' probe. Runs in a throwaway clone. usage: python -I reject_probe.py <clone root> <out jsonl> <out summary>
Per kind: one violating line appended to a real engine file -> ratchet.new has that key. One violation removed -> stale.
Lines only shifted -> both empty. Baseline file deleted -> test_rule_g8_baseline_ratchet fails.
Every engine file is restored byte for byte after each case; git status is checked at the end."""
import json, os, subprocess, sys
from pathlib import Path

root = Path(sys.argv[1])
outp, summ = Path(sys.argv[2]), Path(sys.argv[3])
E = root / "skills/analog-gmid-design/gmid_engine"
S = E / "tests/structure"
sys.dont_write_bytecode = True
sys.path.insert(0, str(S))
import structure_checks as c

base = c.load_baseline(S / "g8_baseline.json")


def now():
    _, a = c.check_g8(E)
    _, b = c.check_value_types(E)
    return c.ratchet(list(a) + list(b), base)


TARGET = "metrics/_gl1_probe_host.py"     # new file so that keys never collide with existing rows
CASES = [
    ("g8_attr_container", "class P1:\n    def m(self):\n        self.probe = {}\n", ("g8_attr_container", TARGET, "P1.probe", 1)),
    ("g8_class_container", "class P2:\n    probe = []\n", ("g8_class_container", TARGET, "P2.probe", 1)),
    ("g8_default_factory", "from dataclasses import dataclass, field\n@dataclass\nclass P3:\n    probe: dict = field(default_factory=dict)\n",
     ("g8_default_factory", TARGET, "P3.probe", 1)),
    ("g8_cached_property", "from functools import cached_property\nclass P4:\n    @cached_property\n    def probe(self):\n        return 1\n",
     ("g8_cached_property", TARGET, "P4.probe", 1)),
    ("g8_cache_call", "from functools import lru_cache\ndef f(x):\n    return x\ng = lru_cache(maxsize=1)(f)\n", ("g8_cache_call", TARGET, "<module>", 1)),
    ("g8_module_cache", "from collections import OrderedDict\nPROBE = OrderedDict()\n", ("g8_module_cache", TARGET, "PROBE", 1)),
    ("g8_id_call", "def probe(x):\n    return id(x)\n", ("g8_id_call", TARGET, "probe", 1)),
    ("g8_memo_call_form", "def probe(memo):\n    return memo.call(lambda: 1, 2)\n", ("g8_memo_call_form", TARGET, "probe", 1)),
    ("g8_memo_lookup_form", "def probe(memo):\n    return memo.lookup('a', 'b', (), None)\n", ("g8_memo_lookup_form", TARGET, "probe", 1)),
    ("vt_annotation", "from .records import X\nfrom dataclasses import dataclass\n@dataclass(frozen=True)\nclass PV:\n    a: int = 0\nPROBE: PV = None\n", ("vt_annotation", TARGET, "PROBE:PV", 1)),
    ("vt_assign", "from dataclasses import dataclass\n@dataclass(frozen=True)\nclass PV:\n    a: int = 0\nPROBE = PV()\n", ("vt_assign", TARGET, "PROBE:PV", 1)),
]
results = []


def log(rec):
    results.append(rec)
    with open(outp, "ab") as f:
        f.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))


host = E / TARGET
for kind, src, key in CASES:
    host.write_text(src, encoding="utf-8", newline="\n")
    r = now()
    log({"case": "add:" + kind, "new": [list(x) for x in r.new], "stale": [list(x) for x in r.stale], "ok": r.new == (key,) and r.stale == ()})
    host.unlink()

# (same key count + 1 on an existing row): add one more id() to an existing function body
p = E / "metrics/resolution.py"
orig = p.read_bytes()
txt = orig.decode("utf-8")
needle = "key = (id(system), float(omega))"
assert needle in txt
p.write_bytes(txt.replace(needle, needle + "\n    _ = id(omega)", 1).encode("utf-8"))
r = now()
log({"case": "count+1:g8_id_call", "new": [list(x) for x in r.new], "stale": [list(x) for x in r.stale],
     "ok": r.new == (("g8_id_call", "metrics/resolution.py", "_sens", 1),) and r.stale == ()})
p.write_bytes(orig)

# (one violation removed -> stale)
p.write_bytes(txt.replace(needle, "key = (0, float(omega))", 1).encode("utf-8"))
r = now()
log({"case": "remove:g8_id_call", "new": [list(x) for x in r.new], "stale": [list(x) for x in r.stale],
     "ok": r.new == () and r.stale == (("g8_id_call", "metrics/resolution.py", "_sens", 1),)})
p.write_bytes(orig)

# (shift lines only, one file for each kind present in the tree)
files = ["layout/diffusion.py", "layout/_helpers_alias.py", "layout/euler_graph.py", "metrics/resolution.py", "lut/cap_query.py", "lut/lut_set.py"]
saved = {f: (E / f).read_bytes() for f in files}
for f in files:
    (E / f).write_bytes(b"# gl1 probe\n# gl1 probe\n# gl1 probe\n" + saved[f])
r = now()
_, a = c.check_g8(E)
log({"case": "shift_lines", "new": [list(x) for x in r.new], "stale": [list(x) for x in r.stale], "ok": r.new == () and r.stale == ()})
for f in files:
    (E / f).write_bytes(saved[f])

# (delete the baseline -> the real tree test fails, not skipped)
b = S / "g8_baseline.json"
keep = b.read_bytes()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", OPENBLAS_NUM_THREADS="1")


def rt():
    x = subprocess.run([sys.executable, "-P", "-m", "pytest", str(S / "test_g8_baseline.py") + "::test_rule_g8_baseline_ratchet", "-q", "-p", "no:cacheprovider", "--tb=line"],
                       cwd=str(root), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return x.returncode, x.stdout[-400:]


b.unlink()
rc, tail = rt()
log({"case": "delete_baseline", "rc": rc, "tail": tail, "ok": rc == 1 and "FoundError: [Errno 2]" in tail and "g8_baseline.json" in tail})
b.write_bytes(b'{"id": "x"}\n')
rc, tail = rt()
log({"case": "malformed_baseline", "rc": rc, "tail": tail, "ok": rc == 1 and "g8_baseline_malformed" in tail})
b.write_bytes(keep)
host.write_text(CASES[6][1], encoding="utf-8", newline="\n")
rc, tail = rt()
log({"case": "real_test_red_on_new", "rc": rc, "tail": tail, "ok": rc == 1})
host.unlink()
rc, tail = rt()
log({"case": "real_test_green_restored", "rc": rc, "tail": tail, "ok": rc == 0})
st = subprocess.run(["git", "-C", str(root), "status", "--short"], capture_output=True, text=True).stdout
summ.write_text(json.dumps({"n": len(results), "all_ok": all(x["ok"] for x in results), "failed": [x for x in results if not x["ok"]], "git_status_after": st},
                           ensure_ascii=False, indent=1), encoding="utf-8")
print(summ.read_text(encoding="utf-8"))
