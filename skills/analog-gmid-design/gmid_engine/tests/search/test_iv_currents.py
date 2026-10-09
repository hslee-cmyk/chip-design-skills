"""search/iv_currents.py -- `current_model(ctx, gm_id, lengths) -> CurrentModel` (설계 41 §6.5 '전류: I = gm/(gm/ID), 나머지 소자는 미러 비와 KCL 로 전파').

oracle (a) 물리 불변식·구성:
- 블록 입력 소자 d: I_d = gm_b / (gm/ID)_d (41 §6.5) -- 아핀 벡터 (gm_1 계수, ..., 상수항) 로 쓰면 그 블록 계수만 1/(gm/ID)_d.
- KCL: 같은 가지 직렬 소자(CS 입력 nmos 와 pmos 부하)는 같은 전류.
- 값 선언 이상원이 없는 회로에서 상수항은 0.
- 출발 구간 보고(start_intervals)에서도 같은 관계: i_start(MN_k) = i_start(MP_k) = gm_k / gm_id_chosen(MN_k), θ 전류 성분 = 그 가지 전류.
"""
import pytest

from gmid_engine.search.iv_context import build_start_context
from gmid_engine.search.iv_currents import current_model

from .u13_hand import cs_chain, rows_by_name, toy_case

TARGETS = (("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0))
ELS2 = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 2e-12))


def _case():
    return toy_case(cs_chain(2), cap_scale=1e-12, elements=ELS2, constraints=TARGETS)


def test_affine_currents_follow_block_gm_and_kcl():
    c = _case()
    ctx = build_start_context(c.s1v, c.ach, c.kctx, c.spec, c.pdk, c.sctx.domain)
    names = [d.name for d in ctx.devices]
    g = {n: 12.0 for n in names}                        # VGS 1.0 마디(20 − 8·1.0)
    lengths = {n: 1e-6 for n in names}
    model = current_model(ctx, g, lengths)
    assert len(model.blocks) == 2
    outs = [b.out_net for b in model.blocks]
    assert outs == ["n1", "out"]                         # stage 순서
    assert [b.inputs for b in model.blocks] == [("MN1",), ("MN2",)]
    assert model.unassigned == ()
    for k, (mn, mp) in enumerate((("MN1", "MP1"), ("MN2", "MP2"))):
        want = [0.0, 0.0, 0.0]
        want[k] = 1.0 / 12.0
        assert list(model.mos[mn]) == pytest.approx(want, abs=1e-15)
        assert list(model.mos[mp]) == pytest.approx(want, abs=1e-15)   # KCL 직렬 가지


def test_reported_currents_equal_gm_over_gm_id():
    st = _case().start
    rows = rows_by_name(st)
    gm = dict(st.macro.gm)
    theta = dict(st.theta)
    for k, net in ((1, "n1"), (2, "out")):
        mn, mp = rows["MN%d" % k], rows["MP%d" % k]
        want = gm[(net,)] / mn.gm_id_chosen
        assert mn.i_start == pytest.approx(want, rel=1e-9)
        assert mp.i_start == pytest.approx(want, rel=1e-9)
        assert theta[("current", "MP%d" % k)] == pytest.approx(want, rel=1e-9)
