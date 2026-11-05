"""WB-1 search 층 공용 helper -- 합성 bin LUT(`sizing/wb1_toy.write_r4_bins_lut`) + `LutAccess(memo)` 새 서명으로 case 를 만든다.
기존 search conftest `build_case` 는 옛 `pre_layout_lut_access` 를 쓰므로(fixture 이행은 이 card 범위 밖) 같은 순서를 새 접근으로 다시 쓴다.

R-2 회로(interface §6, 회로 이름 0): M1 nmos (x, inp, t, bulk t), M2 nmos (out, inn, t, bulk t), M3 pmos (x, x, vdd), M4 pmos (out, x, vdd),
이상 전류원 t -> gnd. 입력 DC 미선언: 차동쌍 두 포트는 한 점이고 ln_idu 는 M1(전류 M3·M4 는 별도 θ 성분)만 θ 성분이다(탐색 단계 실측 스키마).
oracle (a/d): 손 계산 가정은 각 test 의 전제 단언(W_M1 = W_M2 = 2e-6 등)으로 확인하고, 깨지면 회로·기대값을 고치지 않고 멈춘다.
"""
from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace

from gmid_engine.graph import build_s1
from gmid_engine.search import SearchSettings, build_search_context
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, size_and_seal

from sizing.wb1_toy import access_of, write_r4_bins_lut

from .conftest import CODE_FP, SRC, load_spec, mos, r4_ln_idu, topo, two, write_decls
from metrics.conftest import fresh_run

CONS = (("gain_ss_db", ">=", 10.0, None),)


def bins_case(tmp, doc, constraints=CONS, elements=(), eval_budget=40, widths=(1e-6, 2e-6), archive_root=None, budget_s=600.0):
    tmp = Path(tmp)
    lut, _, _ = write_r4_bins_lut(tmp / "lut", widths=widths)
    acc = access_of(lut)
    td, spec = load_spec(tmp / "case", doc, elements=elements, constraints=constraints)
    inputs = dc_inputs_from_spec(spec)
    run = fresh_run()
    dc = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs, acc, **run)
    pdk, rule = write_decls(tmp / "pdk")
    settings = SearchSettings(budget_s, eval_budget, None, tuple(SRC), None)
    sctx = build_search_context(dc, spec, settings, archive_root, pdk, rule, code_fp=CODE_FP)
    return SimpleNamespace(td=td, spec=spec, dc=dc, acc=acc, lut=lut, sctx=sctx)


def circuit_r2():
    return topo("wb1_r2", [mos("M1", "nmos", "x", "inp", "t", "t"), mos("M2", "nmos", "out", "inn", "t", "t"),
                           mos("M3", "pmos", "x", "x", "vdd", "vdd"), mos("M4", "pmos", "out", "x", "vdd", "vdd")],
                {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"),
                 "out": ("output", "single_ended_output")},
                sources=[two("I0", "current_source", "t", "gnd")])


R2_ELEMENTS = (("I0", "current_source", None),)
R2_CELLS = (0, 0, 0, 0)
VGS0 = 0.6
VX = 1.1                                    # V(x) = vdd - VSG3, VSG3 = 0.7 (M3 diode)


def r2_theta(dc, l=1e-6, scale=1.0, y_inp=0.8, rounds=30):
    """W_M1 = W_M2 = 2e-6·scale 가 되는 θ. 전류 = W·IDu/L (r4 닫힌 식), y_out 은 V(out) = V(x) 가 되게 고정점 반복으로 정한다
    (out 창 하한 = V(t) 라 V(out) = V(t) + y·(1.8 - V(t)); θ 는 입력이고 반복은 sizing 공개 경로로 한다)."""
    idu = math.exp(r4_ln_idu("nmos", VGS0, VX - 0.3, 0.0))
    ib = 2e-6 * scale * idu / l                         # W = I·L/IDu 의 역
    th = {("L", m): l for m in ("M1", "M2", "M3", "M4")}
    th.update({("current", "M3"): ib, ("current", "M4"): ib, ("ln_idu", "M1"): r4_ln_idu("nmos", VGS0, VX - 0.3, 0.0),
               ("ln_idu", "M3"): r4_ln_idu("pmos", 0.7, 0.7, 0.0), ("y", "inp"): y_inp, ("y", "out"): VX / 1.8})
    for _ in range(rounds):
        ev = size_and_seal(dc, th)
        t = dict(ev.snapshot.column("node", "dc_v"))["t"]
        th[("y", "out")] = (VX - t) / (1.8 - t)
    return th


def sorted_theta(th):
    return tuple(sorted(th.items()))
