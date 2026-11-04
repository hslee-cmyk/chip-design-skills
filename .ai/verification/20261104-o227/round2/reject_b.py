"""Calls the real test functions of test_stage_b_library with mutated copies of real reports. Writes each outcome to a JSON file.
usage: reject_b.py <clone root> <out json>"""
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
import test_stage_b_library as t  # noqa: E402

assert Path(t.__file__).resolve().is_relative_to(ROOT.resolve())


class F:
    @staticmethod
    def mktemp(name):
        return Path(tempfile.mkdtemp(prefix=name[:8]))


env = t.env.__wrapped__()
real = {c: t._run(env, c, F) for c in ("cnr_ota", "erfc_ota", "r2r_opamp", "rfc_ota")}
BG, GT, AR, DG = (t.test_block_grid_products_and_budget_gate, t.test_gain_target_and_verdict,
                  t.test_area_lower_bound_from_declared_values, t.test_diagnostic_mode_keeps_stage_a_exit_code)
RES = []


def call(fn, circuit, a, b):
    env["cache"][circuit] = (a, b)
    try:
        fn(env, circuit, F)
    except pytest.xfail.Exception:
        return "XFAIL"
    except pytest.fail.Exception as e:
        return "FAILED:" + ("baseline" if "기준선" in str(e) else "notstop" if "실패하지 않는다" in str(e) else "differs" if "다르다" in str(e) else str(e)[:60])
    except AssertionError as e:
        return "ASSERT:" + str(e)[:70].replace("\n", " ")
    except Exception as e:
        return "EXC:" + type(e).__name__
    return "PASS"


def clone(circuit, **over):
    a, b = real[circuit]
    return (SimpleNamespace(status=a.status, exit_code=over.get("a_exit", a.exit_code)),
            SimpleNamespace(status=b.status, exit_code=over.get("b_exit", b.exit_code), report=copy.deepcopy(b.report), s1=over.get("s1", b.s1)))


def rec(name, want, got):
    ok = got.split(":")[0] in want if isinstance(want, tuple) else got.split(":")[0] == want
    RES.append({"case": name, "want": want, "got": got, "ok": ok})


# ------- real values, no mutation
for c in ("cnr_ota", "erfc_ota"):
    for fn in (BG, GT, AR, DG):
        a, b = clone(c)
        rec("real/%s/%s" % (c, fn.__name__), "XFAIL", call(fn, c, a, b))
a, b = clone("r2r_opamp")
rec("real/r2r/block_grid", "XFAIL", call(BG, "r2r_opamp", a, b))
for fn in (BG, DG):
    a, b = clone("rfc_ota")
    rec("real/rfc/" + fn.__name__, "PASS", call(fn, "rfc_ota", a, b))
a, b = clone("r2r_opamp")
rec("real/r2r/diagnostic", "PASS", call(DG, "r2r_opamp", a, b))


# ------- stop table mutations, every pinned test, both circuits
def stop_mut(c):
    item = json.loads(real[c][1].report["stop_reasons"][0])

    def j(**kw):
        x = copy.deepcopy(item)
        for k, v in kw.items():
            if k in ("reason", "rule_branch", "nets"):
                x["detail"][k] = v
            else:
                x[k] = v
        return json.dumps(x)
    dev = item["devices"]
    return {
        "branch_differs": ([j(rule_branch="other")], "FAILED"),
        "reason_differs": ([j(reason="other")], "FAILED"),
        "class_differs": ([j(**{"class": "OTHER"})], "FAILED"),
        "device_added": ([j(devices=dev + ["Mx"])], "FAILED"),
        "device_removed": ([j(devices=dev[:-1])], "FAILED"),
        "device_renamed": ([j(devices=["Mx"] + dev[1:])], "FAILED"),
        "devices_empty": ([j(devices=[])], "FAILED"),
        "net_added": ([j(nets=item["detail"].get("nets", []) + ["Nx"])], "FAILED"),
        "second_reason": ([j(), j(rule_branch="other")], "FAILED"),
        "duplicate": ([j(), j()], "FAILED"),
        "empty": ([], "FAILED"),
        "not_json": (["|x|"], "EXC"),
        "no_detail": ([json.dumps({"class": "X", "devices": []})], "EXC"),
        "no_devices": ([json.dumps({"class": "X", "detail": item["detail"]})], "EXC"),
        "no_branch": ([json.dumps({"class": "X", "devices": dev, "detail": {"reason": "r"}})], "EXC"),
    }


for c in ("cnr_ota", "erfc_ota"):
    for name, (reasons, want) in stop_mut(c).items():
        for fn in (BG, GT, AR, DG):
            a, b = clone(c)
            b.report["stop_reasons"] = reasons
            rec("stop/%s/%s/%s" % (c, name, fn.__name__), want, call(fn, c, a, b))
    # same content in another device order must stay pinned (set comparison)
    a, b = clone(c)
    item = json.loads(b.report["stop_reasons"][0])
    item["devices"] = list(reversed(item["devices"]))
    b.report["stop_reasons"] = [json.dumps(item)]
    rec("stop/%s/device_order_only" % c, "XFAIL", call(BG, c, a, b))
    # stops no more
    for fn in (BG, GT, AR):
        a, b = clone(c)
        b.report["achievability"] = copy.deepcopy(real["rfc_ota"][1].report["achievability"])
        rec("notstop/%s/%s" % (c, fn.__name__), "FAILED", call(fn, c, a, b))
    fake_snap = SimpleNamespace(snapshot=SimpleNamespace(record=lambda *_a: object()))
    a, b = clone(c, s1=fake_snap)
    rec("notstop/%s/diagnostic" % c, "FAILED", call(DG, c, a, b))
    a, b = clone(c, s1=None)
    rec("s1_none/%s/diagnostic" % c, "XFAIL", call(DG, c, a, b))
    # m1: exit code assertion runs before the pin
    a, b = clone(c, b_exit=3)
    rec("m1/%s/exit_code_differs" % c, "ASSERT", call(DG, c, a, b))

# ------- fake baseline: only the named circuit reacts, whatever the stop reason
tmp = Path(tempfile.mkdtemp(prefix="o227f"))
orig = pin.BASELINE_PATH
for entry_name, entry in (("empty_dict", {}), ("status_only", {"status": ["stopped", "stopped"]})):
    d = json.loads(orig.read_text(encoding="utf-8"))
    d["cnr_ota"] = entry
    (tmp / "f.json").write_text(json.dumps(d), encoding="utf-8")
    pin.BASELINE_PATH = tmp / "f.json"
    for fn in (BG, GT, AR, DG):
        a, b = clone("cnr_ota")
        rec("fake/%s/cnr/%s" % (entry_name, fn.__name__), "FAILED", call(fn, "cnr_ota", a, b))
        a, b = clone("erfc_ota")
        rec("fake/%s/erfc_untouched/%s" % (entry_name, fn.__name__), "XFAIL", call(fn, "erfc_ota", a, b))
    # baseline beats a differing reason as well
    a, b = clone("cnr_ota")
    b.report["stop_reasons"] = []
    rec("fake/%s/cnr/with_empty_reasons" % entry_name, "FAILED", call(GT, "cnr_ota", a, b))
pin.BASELINE_PATH = orig


# ------- r2r block table
def blocks(b):
    g = b.report["achievability"]["gain"]
    return g, next(x for x in g["blocks"] if x["pi"] == 0), next(x for x in g["blocks"] if x["pi"] != 0)


def r2r(mut):
    a, b = clone("r2r_opamp")
    g, bad, other = blocks(b)
    mut(g, bad, other)
    return call(BG, "r2r_opamp", a, b)


rec("block/second_bad_other_key_same_reason", "FAILED", r2r(lambda g, bad, o: g["ff"].append(dict(copy.deepcopy(bad), key=["Zz"]))))
rec("block/second_bad_other_reason", "FAILED", r2r(lambda g, bad, o: g["ff"].append(dict(copy.deepcopy(bad), key=["Zz"], reason="other"))))
rec("block/duplicate_same_key", "FAILED", r2r(lambda g, bad, o: g["blocks"].append(copy.deepcopy(bad))))
rec("block/other_block_goes_bad", "FAILED", r2r(lambda g, bad, o: o.__setitem__("pi", o["pi"] + 1)))
rec("block/key_changed", "FAILED", r2r(lambda g, bad, o: bad.__setitem__("key", ["n_gn"])))
rec("block/reason_changed", "FAILED", r2r(lambda g, bad, o: bad.__setitem__("reason", "other")))
rec("block/fixed_no_bad", "FAILED", r2r(lambda g, bad, o: bad.__setitem__("pi", 1)))
rec("m2/other_axes_size_wrong", "ASSERT", r2r(lambda g, bad, o: (o.__setitem__("axes", [["vgs", 7]]), o.__setitem__("pi", 7))))
rec("m2/other_over_budget_reason", "ASSERT", r2r(lambda g, bad, o: o.__setitem__("reason", "other")))
rec("m2/other_over_budget_status", "ASSERT", r2r(lambda g, bad, o: o.__setitem__("status", "certified")))
rec("m2/other_over_budget_amax", "ASSERT", r2r(lambda g, bad, o: o.__setitem__("a_max_db", 1.0)))
rec("m2/pinned_block_axes_size_wrong", "ASSERT", r2r(lambda g, bad, o: bad.__setitem__("axes", [["vgs", 7]])))
rec("m2/pinned_block_certified_no_amax", "ASSERT", r2r(lambda g, bad, o: bad.__setitem__("status", "certified")))


def r2r_extra_cert(g, bad, o):
    g["ff"].append({"key": ["Cc"], "axes": [["vgs", o["axes"][0][1]]], "pi": o["axes"][0][1], "status": "certified", "reason": None, "a_max_db": None, "b_db": None})


rec("m2/added_ok_block_certified_no_amax", "ASSERT", r2r(r2r_extra_cert))
a, b = clone("rfc_ota")
g = b.report["achievability"]["gain"]
g["blocks"][0]["pi"] = 0
rec("unpinned/rfc_pi_zero_not_absorbed", "ASSERT", call(BG, "rfc_ota", a, b))
rec("table/stop_circuits", ("cnr_ota,erfc_ota",), ",".join(sorted(pin.STOP)))
rec("table/block_circuits", ("r2r_opamp",), ",".join(sorted(pin.BLOCK)))
rec("table/stage_b_pinned", ("9",), str(len(t._STOP_PINNED) + len(t._BLOCK_PINNED)))
bad = [r for r in RES if not r["ok"]]
OUT.write_text(json.dumps({"cases": len(RES), "unexpected": bad, "all": RES}, ensure_ascii=False, indent=0), encoding="utf-8")
print("cases", len(RES), "unexpected", len(bad))
for r in bad:
    print(r)
print("min", {k: sum(1 for r in RES if r["got"].split(":")[0] == k) for k in {r["got"].split(":")[0] for r in RES}})
