"""o227c: calls the real g10 test function and real stage_b test functions with injected changes. Writes every outcome to a JSON file.
usage: reject_c.py <clone root> <out json>"""
import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
SKILL = ROOT / "skills" / "analog-gmid-design"
sys.path[:0] = [str(SKILL), str(SKILL / "gmid_engine" / "tests" / "integration")]
os.environ["OPENBLAS_NUM_THREADS"] = "1"
import pytest  # noqa: E402
import o227_stop_pin as pin  # noqa: E402
import test_g10_no_recompute_9circuits as g  # noqa: E402
import test_stage_b_library as sb  # noqa: E402

assert Path(g.__file__).resolve().is_relative_to(ROOT.resolve())
env = g.env.__wrapped__()
RUN_B, CHECK, WRITERS, NS, STOP, BLOCK, PATH = g.run_stage_b, g._check_rows, g._s0_writers, set(g.NOT_SEARCHED), copy.deepcopy(pin.STOP), copy.deepcopy(pin.BLOCK), pin.BASELINE_PATH
RES = []


def restore():
    g.run_stage_b, g._check_rows, g._s0_writers = RUN_B, CHECK, WRITERS
    g.NOT_SEARCHED.clear()
    g.NOT_SEARCHED.update(NS)
    pin.STOP.clear()
    pin.STOP.update(copy.deepcopy(STOP))
    pin.BLOCK.clear()
    pin.BLOCK.update(copy.deepcopy(BLOCK))
    pin.BASELINE_PATH = PATH


def outcome(fn, *args):
    try:
        fn(*args)
    except pytest.xfail.Exception:
        return "XFAIL"
    except pytest.fail.Exception as e:
        m = str(e)
        return "FAILED:" + ("baseline" if "기준선" in m else "notstop" if "실패하지 않는다" in m else "differs" if "다르다" in m else m[:50])
    except AssertionError as e:
        return "ASSERT:" + str(e)[:80].replace("\n", " ")
    except Exception as e:
        return "EXC:" + type(e).__name__
    return "PASS"


def g10(c):
    return outcome(g.test_no_same_input_recompute_in_one_run, env, c, Path(tempfile.mkdtemp(prefix="o227g")))


def rec(name, want, got):
    RES.append({"case": name, "want": want, "got": got, "ok": got.split(":")[0] == want})
    restore()


class Proxy:
    def __init__(self, b, **over):
        self.__dict__["_b"], self.__dict__["_o"] = b, over

    def __getattr__(self, k):
        return self._o[k] if k in self._o else getattr(self._b, k)


def patch_b(fn=None, **over):
    def wrapped(*a, **k):
        b = RUN_B(*a, **k)
        rep = copy.deepcopy(b.report)
        if fn:
            fn(rep)
        return Proxy(b, report=rep, **over)
    g.run_stage_b = wrapped


def reasons(mut):
    def f(rep):
        items = [json.loads(x) for x in rep["stop_reasons"]]
        rep["stop_reasons"] = mut(items)
    return f


def dumps(items):
    return [json.dumps(i) for i in items]


def bad_rows(field):
    def f(rows, writers):
        rows = [dict(r) for r in rows]
        rows[0][field] = rows[0][field] + 1
        return CHECK(rows, writers)
    g._check_rows = f


def fake_baseline(c):
    d = json.loads(PATH.read_text(encoding="utf-8"))
    d[c] = {"status": ["stopped", "stopped"]}
    p = Path(tempfile.mkdtemp(prefix="o227f")) / "f.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    pin.BASELINE_PATH = p


for c in ("cnr_ota", "erfc_ota"):
    rec(c + "/real", "XFAIL", g10(c))
    g.NOT_SEARCHED.discard(c)
    rec(c + "/ns_removed", "ASSERT", g10(c))
    bad_rows("recomputes_same_input")
    rec(c + "/count_recompute_injected", "ASSERT", g10(c))
    bad_rows("calls")
    rec(c + "/count_identity_injected", "ASSERT", g10(c))
    g._check_rows = lambda rows, writers: CHECK(rows, list(writers) + ["no_such_block"])
    rec(c + "/s0_writer_missing_injected", "ASSERT", g10(c))
    g._s0_writers = lambda snap: []
    rec(c + "/writers_empty", "ASSERT", g10(c))
    patch_b(s1=None)
    rec(c + "/s1_none", "ASSERT", g10(c))
    patch_b(status="ok")
    # a.status stays stopped in the real run, so this stays not searched: pin still decides
    rec(c + "/b_status_ok_only", "XFAIL", g10(c))
    patch_b(reasons(lambda it: dumps([dict(it[0], **{"class": "OTHER"})])))
    rec(c + "/class_differs", "FAILED", g10(c))
    patch_b(reasons(lambda it: dumps([dict(it[0], detail=dict(it[0]["detail"], rule_branch="other"))])))
    rec(c + "/branch_differs", "FAILED", g10(c))
    patch_b(reasons(lambda it: dumps([dict(it[0], devices=it[0]["devices"] + ["Mx"])])))
    rec(c + "/device_added", "FAILED", g10(c))
    patch_b(reasons(lambda it: dumps([dict(it[0], devices=it[0]["devices"][:-1])])))
    rec(c + "/device_removed", "FAILED", g10(c))
    patch_b(reasons(lambda it: dumps(it + it)))
    rec(c + "/duplicate", "FAILED", g10(c))
    patch_b(reasons(lambda it: []))
    rec(c + "/empty", "FAILED", g10(c))
    patch_b(lambda rep: rep.__setitem__("stop_reasons", ["|x|"]))
    rec(c + "/not_json", "EXC", g10(c))
    patch_b(lambda rep: rep.__setitem__("achievability", {"verdict": "ok"}))
    rec(c + "/achievability_present", "FAILED", g10(c))
    fake_baseline(c)
    rec(c + "/baseline_appears", "FAILED", g10(c))
    fake_baseline(c)
    patch_b(reasons(lambda it: []))
    rec(c + "/baseline_and_empty_reasons", "FAILED", g10(c))
    fake_baseline(c)
    bad_rows("recomputes_same_input")
    rec(c + "/baseline_and_count_violation", "ASSERT", g10(c))

for c in ("r2r_opamp", "rfc_ota", "ngcc_3stage_ff"):
    rec(c + "/real", "PASS", g10(c))
    g.NOT_SEARCHED.discard(c)
    rec(c + "/ns_removed", "ASSERT", g10(c))
    bad_rows("recomputes_same_input")
    rec(c + "/count_recompute_injected", "ASSERT", g10(c))

# new gap candidate: a pinned circuit that is searched never reaches the pin in g10
c = "common_gate_amplifier"
rec(c + "/real_unpinned", "PASS", g10(c))
pin.STOP[c] = (("x", "y", "z", (), ()),)
rec(c + "/GAP_pinned_and_searched_baseline_present", "PASS", g10(c))
d = json.loads(PATH.read_text(encoding="utf-8"))
d.pop(c)
p = Path(tempfile.mkdtemp(prefix="o227f")) / "f.json"
p.write_text(json.dumps(d), encoding="utf-8")
pin.STOP[c] = (("x", "y", "z", (), ()),)
pin.BASELINE_PATH = p
rec(c + "/GAP_pinned_and_searched_baseline_absent", "PASS", g10(c))
# pinned, engine reaches ok/ok but NOT_SEARCHED entry kept: premise rejects
pin.STOP[c] = (("x", "y", "z", (), ()),)
g.NOT_SEARCHED.add(c)
rec(c + "/pinned_searched_still_registered", "ASSERT", g10(c))


# m7 docstring: the two mismatch directions, real stage_b tests
class F:
    @staticmethod
    def mktemp(name):
        return Path(tempfile.mkdtemp(prefix=name[:8]))


senv = sb.env.__wrapped__()
FNS = {"block_grid": sb.test_block_grid_products_and_budget_gate, "gain": sb.test_gain_target_and_verdict,
       "area": sb.test_area_lower_bound_from_declared_values, "diag": sb.test_diagnostic_mode_keeps_stage_a_exit_code}
SP, BP = set(sb._STOP_PINNED), set(sb._BLOCK_PINNED)
doc = {}
for name, fn in FNS.items():
    pin.STOP.pop("cnr_ota")
    doc["list_only_stop/" + name] = outcome(fn, senv, "cnr_ota", F)
    restore()
    sb._STOP_PINNED.discard((fn.__name__, "cnr_ota"))
    doc["table_only_stop/" + name] = outcome(fn, senv, "cnr_ota", F)
    sb._STOP_PINNED.clear()
    sb._STOP_PINNED.update(SP)
pin.BLOCK.pop("r2r_opamp")
doc["list_only_block/block_grid"] = outcome(FNS["block_grid"], senv, "r2r_opamp", F)
restore()
sb._BLOCK_PINNED.clear()
doc["table_only_block/block_grid"] = outcome(FNS["block_grid"], senv, "r2r_opamp", F)
sb._BLOCK_PINNED.update(BP)
pin.STOP.pop("cnr_ota")
doc["list_only_stop/g10"] = g10("cnr_ota")
restore()
bad = [r for r in RES if not r["ok"]]
OUT.write_text(json.dumps({"cases": len(RES), "unexpected": bad, "all": RES, "docstring": doc}, ensure_ascii=False, indent=0), encoding="utf-8")
print("cases", len(RES), "unexpected", len(bad))
for r in bad:
    print(r)
for r in RES:
    if "GAP" in r["case"] or "pinned_searched" in r["case"] or "b_status" in r["case"]:
        print(r["case"], "->", r["got"][:90])
for k, v in doc.items():
    print(k, "->", v[:100])
