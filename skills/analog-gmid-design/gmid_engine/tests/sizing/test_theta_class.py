"""`device.theta_class` -- θ 분류 필드와 블록 `theta_class` (card 20261104-tb1-theta-class, interface §1·§4 T-T1·T-T2).

oracle: (손) 합성 toy 의 연결에서 손으로 유도한 S/B/F 기대값, (식) interface §1 분류 규칙·READS 규칙. 기대값을 피검 함수로 만들지 않는다.
분류 규칙(interface §1 표): S = 매크로 활성 회로의 입력 쌍(gain 제약 전달 뷰 주경로 이득 블록의 AC 역할 input) · rout 선언 버퍼 출력노드에 source 가 닿는 follower,
F = cascode·pass·follower 와 매크로 비활성 회로의 input, B = load·mirror·diode_load·tail_source · 어느 블록에도 안 드는 MOS.
매크로 활성 = has_gbw_target, 또는 has_settling 이고 GBW 미선언. PM 선언은 입력이 아니다.
S1v(`build_s1v`)가 없는 S1(블록 없음)은 전부 B.

[해석, 오케스트레이터에 보고] 값 칸 이름은 `ThetaClass.kind`(interface: `ThetaClass(kind)`, kind ∈ S·B·F). 열 읽기는 `base.column("device", "theta_class")`.
"""
import pytest

from gmid_engine.graph import build_s1, build_s1v
from gmid_engine.search import open_run
from gmid_engine.sizing import DcInputs, build_kernel_context, dc_writer_plan, theta_class

from .conftest import SUPPLIES, block_row, load_doc, mos, row_delta, run_of, topo, two


def _kind(v):
    return getattr(v, "kind", v)


def _classes(ctx):
    return {m: _kind(v) for m, v in ctx.base.column("device", "theta_class")}


def _ctx(tmp_path, access, doc, gbw=False, rout=False, settle=False, with_s1v=True):
    """S1 -> (S1v) -> 커널 컨텍스트. 실행 하나 = 이 호출 하나. bool 셋은 DcInputs 칸."""
    donors, counters = open_run()
    run = dict(donors=donors, counters=counters)
    s1 = build_s1(load_doc(tmp_path, doc), dict(SUPPLIES), **run)
    graph = build_s1v(s1, None, count_budget=10 ** 6, stop_on_unsupported=False, **run) if with_s1v else s1
    inputs = DcInputs(tuple(sorted(SUPPLIES.items())), has_gbw_target=gbw, has_rout_limit=rout, has_settling=settle)
    return build_kernel_context(graph, inputs, access, **run)


def _ota5(name="tc_ota5"):
    """5T OTA: 차동쌍 M1(x, inp, t)·M2(out, inn, t), 꼬리 M5(t, nb, gnd), 꼬리 바이어스 diode M6(nb, nb, gnd)(이상 전류원 I1: vdd -> nb),
    능동 부하 M3 diode(x, x, vdd)·M4 거울(out, x, vdd). 손 분류: 입력쌍 M1·M2, 부하 M3·M4(diode_load·mirror), 꼬리 M5, M6 은 이득 블록 밖."""
    return topo(name,
                [mos("M1", "nmos", "x", "inp", "t"), mos("M2", "nmos", "out", "inn", "t"), mos("M5", "nmos", "t", "nb", "gnd"),
                 mos("M6", "nmos", "nb", "nb", "gnd"), mos("M3", "pmos", "x", "x", "vdd"), mos("M4", "pmos", "out", "x", "vdd")],
                {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"),
                 "out": ("output", "single_ended_output")},
                sources=[two("I1", "current_source", "vdd", "nb")])


def _follower(name="tc_follower"):
    """source follower: M1(vdd, in, out) 출력 노드 out 에 source, 전류 싱크 M2(out, nb, gnd), 바이어스 diode M3(nb, nb, gnd)(I1: vdd -> nb)."""
    return topo(name,
                [mos("M1", "nmos", "vdd", "in", "out"), mos("M2", "nmos", "out", "nb", "gnd"), mos("M3", "nmos", "nb", "nb", "gnd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                sources=[two("I1", "current_source", "vdd", "nb")])


OTA_REST = {"M3": "B", "M4": "B", "M5": "B", "M6": "B"}           # 부하·꼬리·바이어스 diode = 어느 매크로 조합에서도 B


@pytest.mark.parametrize("gbw,settle,active", [
    (True, False, True),        # GBW 선언 -> 활성
    (True, True, True),         # 둘 다 -> 활성
    (False, True, True),        # 정착만 선언하고 GBW 미선언 -> 활성
    (False, False, False),      # 둘 다 없음 -> 비활성
], ids=["gbw", "gbw_settling", "settling_only", "none"])
def test_theta_class_macro_activation_four_combinations(tmp_path, toy_access, gbw, settle, active):
    """oracle (손): interface §1 매크로 활성 정의 네 조합. 활성이면 입력쌍 M1·M2 = S, 비활성이면 F. 부하·꼬리·바이어스 diode 는 항상 B."""
    got = _classes(_ctx(tmp_path, toy_access, _ota5(), gbw=gbw, settle=settle))
    assert got == {"M1": "S" if active else "F", "M2": "S" if active else "F", **OTA_REST}


def test_theta_class_without_s1v_everything_is_b(tmp_path, toy_access):
    """oracle (식): S1v 가 없는 S1(블록 없음) -> 전부 B (interface §1). 매크로 활성 입력이어도 마찬가지."""
    got = _classes(_ctx(tmp_path, toy_access, _ota5("tc_nos1v"), gbw=True, with_s1v=False))
    assert got == {m: "B" for m in ("M1", "M2", "M3", "M4", "M5", "M6")}


def test_theta_class_rout_declared_follower_is_s(tmp_path, toy_access):
    """oracle (손): rout 선언 버퍼의 출력노드(out)에 source 가 닿는 follower M1 = S. 매크로 비활성(GBW·정착 없음)에서 rout 선언만 있어도 S,
    rout 선언이 없으면 follower 는 F. 싱크 M2·diode M3 은 B."""
    (tmp_path / "rout").mkdir()
    (tmp_path / "norout").mkdir()
    with_rout = _classes(_ctx(tmp_path / "rout", toy_access, _follower(), rout=True))
    no_rout = _classes(_ctx(tmp_path / "norout", toy_access, _follower(), rout=False))
    assert with_rout == {"M1": "S", "M2": "B", "M3": "B"}
    assert no_rout == {"M1": "F", "M2": "B", "M3": "B"}


def test_theta_class_value_is_a_thetaclass_kind_in_closed_set(tmp_path, toy_access):
    """oracle (식): 값 어휘 {S, B, F} 밖이 없고 모든 MOS 에 항목이 있다(열 키 = MOS 이름 전수)."""
    ctx = _ctx(tmp_path, toy_access, _ota5("tc_closed"), gbw=True)
    got = _classes(ctx)
    assert set(got) == {"M1", "M2", "M3", "M4", "M5", "M6"} and set(got.values()) <= {"S", "B", "F"}


def test_theta_class_reads_have_no_dc_coord_and_no_second_writer():
    """oracle (식): interface §1 -- 블록 READS 에 ("device","dc_coord") 없음, WRITES 는 이 필드 하나, 쓰기 계획 블록이 이 필드를 쓰지 않고 읽는다(writer 하나)."""
    assert ("device", "dc_coord") not in set(theta_class.reads)
    assert set(theta_class.writes) == {("device", "theta_class")}
    assert ("device", "theta_class") not in set(dc_writer_plan.writes)
    assert ("device", "theta_class") in set(dc_writer_plan.reads)


def test_theta_class_runs_before_writer_plan_and_same_input_is_reused(tmp_path, toy_access):
    """oracle (식): 쓰기 계획 앞 호출 -- ctx.base 에 theta_class 블록 버전이 있고 필드가 이미 있다. 같은 입력 재호출 = 재사용(계수 증분 calls 1, reuses 1)."""
    ctx = _ctx(tmp_path, toy_access, _ota5("tc_order"), gbw=True)
    base = ctx.base
    assert base.block_version(theta_class.name) is not None
    assert _classes(ctx)
    before = block_row(ctx.counters, theta_class.name)
    assert theta_class(base, True, False, False, **run_of(ctx)) is base
    assert row_delta(block_row(ctx.counters, theta_class.name), before) == (1, 1, 0, 0, 0, 0)
