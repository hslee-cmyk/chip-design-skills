"""usage: count_calls.py <skill root> <out json> <pytest args...>
pytest 를 한 프로세스에서 돌리며 capacitance_matrix·view_factor·nodal_of·block_local_gain 호출을 호출 자리·같은 입력(회로 내용) 별로 세고 cProfile 로 시간 몫을 잰다."""
import collections
import cProfile
import json
import pathlib
import pstats
import sys

skill = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(skill))
out_path = pathlib.Path(sys.argv[2])
args = sys.argv[3:]

import pytest
import importlib
_m = lambda n: importlib.import_module('gmid_engine.metrics.' + n)
HN, HV, SN, BM, BR, OA = _m('_helpers_nodal'), _m('_helpers_view'), _m('ss_nodal'), _m('block_model'), _m('block_residual'), _m('offset_analysis')

counts = collections.Counter()
per_input = collections.Counter()
orig_cap = HN.capacitance_matrix


def cap_counted(circuit, size):
    site = sys._getframe(1).f_code.co_name
    counts["capacitance_matrix@" + site] += 1
    per_input[(site, hash(circuit) if circuit.__hash__ else id(circuit))] += 1
    per_input[("any", hash(circuit) if circuit.__hash__ else id(circuit))] += 1
    return orig_cap(circuit, size)


for mod in (HV, SN, BM):
    mod.capacitance_matrix = cap_counted

orig_vf = HV.view_factor


def vf_counted(ss, nodal, fixed):
    base = None if nodal is None else nodal.fixed
    fx = frozenset(int(i) for i in fixed)
    counts["view_factor:nodal_none" if nodal is None else ("view_factor:base_hit" if base == fx else "view_factor:other_fixed")] += 1
    counts["view_factor@" + sys._getframe(1).f_code.co_name] += 1
    return orig_vf(ss, nodal, fixed)


for mod in (HV, BR, OA):
    mod.view_factor = vf_counted
_m('offset_systematic').view_factor = vf_counted

orig_blg = BR.block_local_gain


def blg_counted(*a, **k):
    counts["block_local_gain"] += 1
    return orig_blg(*a, **k)


BR.block_local_gain = blg_counted

prof = cProfile.Profile()
prof.enable()
rc = pytest.main(args + ["-p", "no:cacheprovider", "-q", "--tb=short"])
prof.disable()
st = pstats.Stats(prof)
times = {}
for (fn, line, name), (cc, nc, tt, ct, callers) in st.stats.items():
    if name in ("capacitance_matrix", "cap_counted", "nodal_of", "nodal_factor", "conductance_matrix", "block_local_gain", "block_stamp_matrix", "mos_stamps", "_structure", "block_residual", "ss_nodal_system", "kernel_eval", "evaluate"):
        key = pathlib.Path(fn).name + ":" + name
        times[key] = {"calls": nc, "tottime": round(tt, 4), "cumtime": round(ct, 4)}
dup = collections.Counter()
for (site, key), n in per_input.items():
    if n > 1:
        dup[site] += n - 1
out_path.write_text(json.dumps({"rc": int(rc), "counts": counts, "same_input_extra_calls": dup, "distinct_inputs": sum(1 for k in per_input if k[0] == "any"),
                                "times": times, "total_tt": round(st.total_tt, 2)}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(out_path.read_text(encoding="utf-8"))
