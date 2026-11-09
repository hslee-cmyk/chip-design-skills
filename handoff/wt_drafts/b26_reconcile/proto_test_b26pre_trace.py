"""b26pre 보강 시제품(scratch, 커밋하지 않음) -- find_differential_pair_candidates trace 루프 범위(range(i + 1, …)).
입력: 공통 tail(ntail)을 공유하는 nmos 입력 소자 n개 + 각 branch pmos 부하(source vdd) + tail 소자(source gnd).
기대값은 구성으로 정해진다(oracle (a)): branch 서명이 모두 같으므로 같은 서명 그룹의 모든 branch 쌍 (i<j)을 i, j 오름차순으로 비교하고,
위치 1(입력 소자)에서 같은 non-rail source(ntail)·다른 gate라 후보가 된다. 위치 0(부하)은 source가 레일, 위치 2(tail)는 같은 소자.
n=2이면 층위1 폴백도 같은 쌍을 낸다(그룹 크기 2). n=3이면 층위1 그룹 크기 3이라 폴백 없음.
"""
import importlib
import pathlib
import sys

_ASSETS_DIR = pathlib.Path(__file__).resolve().parents[2]


def _b26pre_sd():
    if str(_ASSETS_DIR) not in sys.path:
        sys.path.insert(0, str(_ASSETS_DIR))
    return importlib.import_module("stick_diagram")


def _b26pre_branches(sd, n):
    T = sd.Transistor
    ts = [T("Mt", "nmos", source="gnd", drain="ntail", gate="nb")]
    for k in range(1, n + 1):
        ts.append(T("Mi%d" % k, "nmos", source="ntail", drain="no%d" % k, gate="ni%d" % k))
        ts.append(T("Ml%d" % k, "pmos", source="vdd", drain="no%d" % k, gate="nbp"))
    return ts


def _b26pre_cands(sd, ts):
    r = sd.find_differential_pair_candidates(ts)
    return [(c["direction"], c["position"], tuple(c["devices"]), c["shared_source"]) for c in r["candidates"]]


def test_b26pre_trace_two_branches():
    sd = _b26pre_sd()
    assert _b26pre_cands(sd, _b26pre_branches(sd, 2)) == [
        ("vdd_to_gnd", 1, ("Mi1", "Mi2"), "ntail"),
        ("gnd_to_vdd", 1, ("Mi1", "Mi2"), "ntail"),
        ("layer1_fallback", None, ("Mi1", "Mi2"), "ntail"),
    ]


def test_b26pre_trace_three_branches_order():
    sd = _b26pre_sd()
    exp = []
    for d in ("vdd_to_gnd", "gnd_to_vdd"):
        exp += [(d, 1, ("Mi1", "Mi2"), "ntail"), (d, 1, ("Mi1", "Mi3"), "ntail"), (d, 1, ("Mi2", "Mi3"), "ntail")]
    assert _b26pre_cands(sd, _b26pre_branches(sd, 3)) == exp
