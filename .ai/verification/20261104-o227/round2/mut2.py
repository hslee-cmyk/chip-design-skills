"""Throwaway clone mutations for o227b, always from committed bytes. usage: mut2.py <clone> <mutation> [<measure jsonl>]"""
import json
import subprocess
import sys
from pathlib import Path

clone, name = sys.argv[1], sys.argv[2]
I = "skills/analog-gmid-design/gmid_engine/tests/integration/"
PIN, G10, FX = I + "o227_stop_pin.py", I + "test_g10_no_recompute_9circuits.py", I + "fixtures/u17_1b_s0_baseline.json"


def head(rel):
    return subprocess.run(["git", "-C", clone, "show", "HEAD:" + rel], capture_output=True, check=True).stdout


for rel in (PIN, G10, FX):        # restore
    Path(clone, rel).write_bytes(head(rel))


def sub(rel, old, new):
    b = Path(clone, rel).read_bytes()
    assert b.count(old) >= 1, old
    Path(clone, rel).write_bytes(b.replace(old, new))


if name == "fake_real_entry":
    # the real measured entry for cnr_ota only: option (다) must be refused by the pin
    entry = next(json.loads(x)["entry"] for x in open(sys.argv[3], encoding="utf-8") if json.loads(x)["circuit"] == "cnr_ota")
    d = json.loads(Path(clone, FX).read_text(encoding="utf-8"))
    d["cnr_ota"] = entry
    Path(clone, FX).write_text(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False), encoding="utf-8")
elif name == "reason":
    sub(PIN, b'"dc_resistor_cycle"', b'"MUT_a"')
    sub(PIN, b'"mos_zero_current_structural"', b'"MUT_b"')
elif name == "devices":
    sub(PIN, b'("M19", "M20", "M21")', b'("M19", "M20")')
    sub(PIN, b'("x40",)', b'("x41",)')
elif name == "ns_drop_cnr_erfc":
    sub(G10, b'NOT_SEARCHED = {"ngcc_3stage_ff", "cnr_ota", "erfc_ota", "r2r_opamp", "rfc_ota"}', b'NOT_SEARCHED = {"ngcc_3stage_ff", "r2r_opamp", "rfc_ota"}')
elif name == "ns_drop_r2r_rfc":
    sub(G10, b'NOT_SEARCHED = {"ngcc_3stage_ff", "cnr_ota", "erfc_ota", "r2r_opamp", "rfc_ota"}', b'NOT_SEARCHED = {"ngcc_3stage_ff", "cnr_ota", "erfc_ota"}')
elif name == "g10_pin_off":
    # moves nothing else: only makes the g10 pin inactive to see whether the stage A/B count assertions hold on cnr/erfc
    sub(G10, b'    if pinned:                               # ', b'    if False:                               # ')
elif name == "g10_counts_bad":
    # the stage A/B branch must still reject a count violation on r2r/rfc
    b = Path(clone, G10).read_bytes()
    old = b"bad = _check_rows(rows, writers)"
    assert b.count(old) == 2
    Path(clone, G10).write_bytes(b.replace(old, b'bad = [("mut",)]', 1))
elif name == "head":
    pass
else:
    raise SystemExit(name)
print("mut", name)
