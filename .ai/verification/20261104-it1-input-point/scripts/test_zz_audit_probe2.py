"""IT-1 재판정 탐침(복제본, 커밋 안 함). PROBE_OUT 에 케이스마다 append."""
import cProfile
import json
import os
import pstats
import time

from gmid_engine.sizing import size_and_seal

from .conftest import build_ctx, mos, r4_ln_idu, topo, two

OUT = os.environ["PROBE_OUT"]
P = ("input", "differential_input_p")
N = ("input", "differential_input_n")
O = ("output", "b")


def rec(case, **kw):
    with open(OUT, "ab") as f:
        f.write((json.dumps({"case": case, **kw}, ensure_ascii=False, default=str) + "\n").encode("utf-8"))


def schema(ctx):
    from gmid_engine.sizing import KERNEL_KEY
    return ctx.base.value("graph", KERNEL_KEY, "theta_schema")


def fill(ctx):
    kinds = dict(ctx.base.column("device", "kind"))
    th = {}
    for k, key in schema(ctx).components:
        th[(k, key)] = {"L": 1e-6, "y": 0.5, "current": 1e-5, "resistance": 2e4}.get(k)
        if k == "ln_idu":
            th[(k, key)] = r4_ln_idu(kinds[key], 0.6, 0.6, 0.0 if kinds[key] == "pmos" else 0.1)
    return th


def diff_mos(pn=("inp", "inn"), ports=None):
    p, n = pn
    return topo("p_diff", [mos("M1", "nmos", "o1", p, "t"), mos("M2", "nmos", "o2", n, "t"), mos("M5", "nmos", "t", "vb", "gnd"),
                           mos("M3", "pmos", "o1", "pb3", "vdd"), mos("M4", "pmos", "o2", "pb4", "vdd")],
                ports or {p: P, n: N, "o1": O, "o2": O}, bias=["vb", "pb3", "pb4"])


def attempt(case, fn):
    try:
        rec(case, result=fn())
    except BaseException as exc:
        rec(case, exc=type(exc).__name__, detail=str(getattr(getattr(exc, "record", None), "detail", exc))[:400])


def test_old_dv_toy_now_stops(tmp_path, r4_access):
    """앞 판정 p3: 한 포트만 W3 -> ΔV θ 함수였던 toy."""
    for tg in (("inn",), ("inp",)):
        (tmp_path / tg[0]).mkdir()
        attempt("q1:" + tg[0], lambda: str(dict(build_ctx(tmp_path / tg[0], diff_mos(), r4_access, node_targets=((tg[0], 0.9),))[2].base.column("node", "dc_writer"))))


def test_both_and_declared(tmp_path, r4_access):
    (tmp_path / "b").mkdir()
    (tmp_path / "d").mkdir()
    (tmp_path / "bd").mkdir()
    attempt("q2:both_diff_values", lambda: {k: str(v) for k, v in dict(build_ctx(tmp_path / "b", diff_mos(), r4_access, node_targets=(("inn", 0.9), ("inp", 0.8)))[2].base.column("node", "dc_writer")).items() if k in ("inp", "inn")})
    attempt("q2:declared_plus_one_target", lambda: {k: str(v) for k, v in dict(build_ctx(tmp_path / "d", diff_mos(), r4_access, input_dc_v=0.9, node_targets=(("inn", 0.9),))[2].base.column("node", "dc_writer")).items() if k in ("inp", "inn")})


def test_port_on_rail(tmp_path, r4_access):
    """n 포트 넷이 레일이면 free_inputs 하나 -- 입력 점이 안 묶이는가."""
    doc = diff_mos(("inp", "gnd"), {"inp": P, "gnd": N, "o1": O, "o2": O})
    attempt("q3:n_port_on_rail", lambda: {k: str(v) for k, v in dict(build_ctx(tmp_path, doc, r4_access)[2].base.column("node", "dc_writer")).items() if k in ("inp", "gnd")})


def test_terms_cost(tmp_path, r4_access):
    """terms() 쓰기 계획 scan 비용 -- 평가당 호출 수·시간. 재사용 없이 매번 같은 입력을 도는지 잰다."""
    doc = topo("p_res", [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"), mos("M5", "nmos", "t", "vb", "gnd")],
               {"inp": P, "inn": N, "o1": O, "o2": O}, passives=[two("R1", "resistor", "vdd", "o1"), two("R2", "resistor", "vdd", "o2")], bias=["vb"])
    ctx = build_ctx(tmp_path, doc, r4_access)[2]
    th = fill(ctx)
    pr = cProfile.Profile()
    t = time.perf_counter()
    pr.enable()
    ev = size_and_seal(ctx, th)
    pr.disable()
    wall = time.perf_counter() - t
    st = pstats.Stats(pr)
    rows = {k[2]: (v[0], v[3]) for k, v in st.stats.items() if k[2] in ("terms", "kvl_window", "dc_columns")}
    rec("q4:terms", wall_s=wall, rows=rows, nodes=len(dict(ctx.base.column("node", "dc_writer"))), ev=type(ev).__name__)
