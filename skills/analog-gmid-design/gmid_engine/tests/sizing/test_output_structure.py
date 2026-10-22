"""`node.dc_output_structure` -- 출력 구조 분류 (card IT-2b, design 41 v1.12.8 4.7-1a, 계획 N3.8 '출력 구조 분류 -- 규칙 하나').

writer = 쓰기 계획 블록 `dc_writer_plan` 하나. 값 = 출력 포트 넷마다 "high_impedance" | "kvl_fixed"(출력 아닌 넷은 항목 없음).
분류 규칙(손): F' = 레일 + (입력 DC 선언이면 입력 포트), W3 목표 넷은 F' 에 넣지 않는다. G_vgs 엣지(MOS gate-source, 저항 양 끝)에서 출력 넷부터
너비 우선으로 성분을 걷어 F' 에 닿으면 kvl_fixed, 닿지 않거나 출력 넷이 G_vgs 엣지의 끝점이 아니면 high_impedance.

oracle (ID 가 아래 test 주석 `oracle 대조:` 에 적힌 것):
- (손) toy 연결에서 위 규칙을 손으로 적용한 기대값. 피검 함수(`dc_writer_plan` 의 출력)로 기대값을 만들지 않는다. toy 는 이름 없는 연결이다.
- (독립) `RunCounters` 증분·`block_version`·소스 문자열 수(`git grep` 과 같은 뜻의 텍스트 수).
이 파일의 toy 는 모두 conftest 의 손 회로 생성기(`topo`·`mos`·`two`)로 만든다.
"""
import re
from pathlib import Path

import pytest

import gmid_engine
from gmid_engine.sizing import dc_writer_plan

from .conftest import (Oracle, block_row, build_ctx, circuit_cs_pmos_load, free_currents, kschema, mos, node_voltages,
                       row_delta, run_blocks, topo, two)

HI = "high_impedance"
KVL = "kvl_fixed"


def _structure(ctx):
    return dict(ctx.base.column("node", "dc_output_structure"))


def _follower(i="in", o="out", m1="M1", m2="M2", extra_input=False):
    """source follower: m1 nmos (vdd, i, o)(출력에 MOS source writer), m2 nmos (o, vb, gnd)(풀다운, gate 는 외부 바이어스).
    G_vgs 엣지: (i, o), (vb, gnd). extra_input 이면 둘째 입력 포트 in2 -- m3 nmos (z, in2, gnd) + 저항 R3 (vdd, z): in2 의 성분은 레일에 닿는다."""
    net = [mos(m1, "nmos", "vdd", i, o), mos(m2, "nmos", o, "vb", "gnd")]
    ports = {i: ("input", "x"), o: ("output", "y")}
    passives = ()
    if extra_input:
        net.append(mos("M3", "nmos", "z", "in2", "gnd"))
        ports["in2"] = ("input", "x")
        passives = [two("R3", "resistor", "vdd", "z")]
    return topo("os_follower", net, ports, passives=passives, bias=["vb"])


# ---------------------------------------------------------------- OS (a)~(k)

def test_it2b_os_a_drain_only_output_is_high_impedance(tmp_path, toy_access):
    """oracle 대조: (손) OS (a). 출력 out 은 M1·M2 의 드레인에만 닿는다 -> G_vgs 엣지 끝점이 아니다 -> high_impedance. 항목은 출력 넷 하나뿐."""
    ctx = build_ctx(tmp_path, circuit_cs_pmos_load(), toy_access)[2]
    assert _structure(ctx) == {"out": HI}


def test_it2b_os_b_follower_output_without_fixed_end_is_high_impedance(tmp_path, toy_access):
    """oracle 대조: (손) OS (b). follower(M1 source = out): G_vgs 성분 {in, out}, 레일·선언 입력 DC 없음 -> F' 에 닿지 않음 -> high_impedance."""
    ctx = build_ctx(tmp_path, _follower(), toy_access)[2]
    assert _structure(ctx) == {"out": HI}


def test_it2b_os_c_resistor_load_to_rail_is_kvl_fixed(tmp_path, toy_access):
    """oracle 대조: (손) OS (c). 차동 입력 단일 출력: 부하 저항 R1 이 out 과 vdd 를 잇는다 -> 저항 엣지로 레일에 닿음 -> kvl_fixed.
    o2 는 출력 포트가 아니므로 항목이 없다."""
    doc = topo("os_diffres", [mos("M1", "nmos", "out", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"),
                              mos("M5", "nmos", "t", "vb", "gnd")],
               {"inp": ("input", "x"), "inn": ("input", "x"), "out": ("output", "y")},
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "vdd", "o2")], bias=["vb"])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    assert _structure(ctx) == {"out": KVL}


def test_it2b_os_d_w3_output_without_fixed_end_is_high_impedance(tmp_path, toy_access):
    """oracle 대조: (손) OS (d). 출력 out 이 W3 목표(0.9 V) -- 핀을 뺀 성분 {in, out} 에 F' 없음 -> high_impedance
    (v1.12.1 의 값 `w3_target` 이 나오면 red)."""
    ctx = build_ctx(tmp_path, _follower(), toy_access, node_targets=(("out", 0.9),))[2]
    assert _structure(ctx) == {"out": HI}
    assert "w3_target" not in _structure(ctx).values()


def _diode_load():
    """M1 diode nmos (out, out, gnd) + M2 nmos (out, in, gnd) + 이상 전류원 I1 (vdd -> out). G_vgs 엣지: (out, gnd), (in, gnd)."""
    return topo("os_diode", [mos("M1", "nmos", "out", "out", "gnd"), mos("M2", "nmos", "out", "in", "gnd")],
                {"in": ("input", "x"), "out": ("output", "y")}, sources=[two("I1", "current_source", "vdd", "out")])


def _rail_gate_source_out():
    """M1 nmos (vdd, vdd, out): gate = 레일, source = out. M2 nmos (out, in, gnd). G_vgs 엣지: (vdd, out), (in, gnd)."""
    return topo("os_railgate", [mos("M1", "nmos", "vdd", "vdd", "out"), mos("M2", "nmos", "out", "in", "gnd")],
                {"in": ("input", "x"), "out": ("output", "y")})


@pytest.mark.parametrize("make", [_diode_load, _rail_gate_source_out], ids=["diode_load", "gate_at_rail_source_out"])
def test_it2b_os_e_w3_output_on_hard_path_is_kvl_fixed(tmp_path, toy_access, make):
    """oracle 대조: (손) OS (e). W3 목표 출력이 MOS 엣지로 레일에 닿는다(diode 부하의 source = gnd, 또는 gate = vdd·source = out) ->
    G_vgs 걷기가 레일(F')에 닿음 -> kvl_fixed. W3 출력을 일괄 고임피던스로 두면 red(O-64 경우 1)."""
    ctx = build_ctx(tmp_path, make(), toy_access, node_targets=(("out", 0.9),))[2]
    assert _structure(ctx) == {"out": KVL}


def test_it2b_os_f_other_w3_node_in_component_is_not_a_fixed_end(tmp_path, toy_access):
    """oracle 대조: (손) OS (f). 출력 성분 {in, out} 에 출력 아닌 W3 목표 노드(in = 0.9 V)만 있고 레일·선언 입력 DC 없음 ->
    W3 목표 넷은 F' 가 아니다 -> high_impedance (그 W3 를 F 로 세면 kvl_fixed -- red)."""
    ctx = build_ctx(tmp_path, _follower(), toy_access, node_targets=(("in", 0.9),))[2]
    assert _structure(ctx) == {"out": HI}


def test_it2b_os_g_declared_input_dc_reaches_output_through_gate_source(tmp_path, toy_access):
    """oracle 대조: (손) OS (g). 같은 연결에서 입력 DC 선언이면 in 이 F' -> M1 gate-source 엣지로 out 에 닿음 -> kvl_fixed,
    미선언이면 high_impedance."""
    declared = build_ctx(tmp_path / "decl", _follower(), toy_access, input_dc_v=0.7)[2]
    assert _structure(declared) == {"out": KVL}
    undeclared = build_ctx(tmp_path / "undecl", _follower(), toy_access)[2]
    assert _structure(undeclared) == {"out": HI}


@pytest.mark.parametrize("input_dc, expected", [(None, HI), (0.7, KVL)], ids=["undeclared", "declared"])
def test_it2b_os_h_swapped_names_give_same_values(tmp_path, toy_access, input_dc, expected):
    """oracle 대조: (손) OS (h). 넷 in <-> out 과 소자 M1 <-> M2 이름을 맞바꾼 toy(입력 포트 이름이 "out", 출력 포트 이름이 "in") 도
    연결이 같으므로 같은 값. 출력 포트는 이제 "in" 이다."""
    kw = {} if input_dc is None else {"input_dc_v": input_dc}
    ctx = build_ctx(tmp_path, _follower(i="out", o="in", m1="M2", m2="M1"), toy_access, **kw)[2]
    assert _structure(ctx) == {"in": expected}


def _follower_theta(ctx, vgs2):
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.9, 0.5),
          ("ln_idu", "M2"): Oracle.ln_idu("nmos", vgs2, 0.6, 0.0)}
    th.update({(k, key): 0.7 for k, key in kschema(ctx).components if k == "y"})
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    return th


def test_it2b_os_i_value_is_theta_independent_and_not_recomputed(tmp_path, toy_access):
    """oracle 대조: (독립) OS (i), G-10. 서로 다른 θ 둘(M2 의 vgs 0.55 / 0.65)로 커널 평가한 스냅샷의 이 필드 값과 쓰기 계획 블록의 block_version 이
    base 와 같고(같음·다름만 본다), 평가 때문에 `dc_writer_plan` computes 가 늘지 않는다(RunCounters 증분 0)."""
    ctx = build_ctx(tmp_path, _follower(), toy_access)[2]
    before_structure = _structure(ctx)
    assert before_structure == {"out": HI}
    version = ctx.base.block_version("dc_writer_plan")
    computes0 = block_row(ctx.counters, dc_writer_plan.name)
    for vgs2 in (0.55, 0.65):
        snap = run_blocks(ctx, _follower_theta(ctx, vgs2), upto="columns")
        assert dict(snap.column("node", "dc_output_structure")) == before_structure
        assert snap.block_version("dc_writer_plan") == version
    assert row_delta(block_row(ctx.counters, dc_writer_plan.name), computes0)[4] == 0


def test_it2b_os_k_no_same_dc_edge_between_input_ports(tmp_path, toy_access):
    """oracle 대조: (손) OS (k). 입력 DC 미선언 두 입력 포트 가운데 in 만 출력 성분 {in, out} 에 있고 in2 의 성분 {in2, gnd} 는 레일에 닿는다.
    '같은 DC' 엣지(옛 `_TIE`)가 두 성분을 이으면 out 이 레일에 닿아 kvl_fixed 가 되지만, 그 엣지는 없다 -> high_impedance."""
    ctx = build_ctx(tmp_path, _follower(extra_input=True), toy_access)[2]
    assert _structure(ctx) == {"out": HI}


# ---------------------------------------------------------------- OS (j) 둘째 생산자 부재 (텍스트 수 -- git grep 과 같은 뜻)

ENGINE = Path(gmid_engine.__file__).resolve().parent


def _count(rel, pattern):
    path = ENGINE / rel
    return len(re.findall(pattern, path.read_text(encoding="utf-8"))) if path.exists() else 0


def test_it2b_os_j_single_writer_site_and_no_second_producer():
    """oracle 대조: (독립) OS (j). 권한표 행은 `sizing/s2_values.py` 의 DC_WRITES 하나(필드 이름 문자열 1회), 쓰기 자리는 `sizing/writer_plan.py`
    (WRITES 에 1회 이상 -- 블록 안 대입은 같은 파일), G_vgs 성분 걷기(`_edges` 호출)는 측정 구성·다듬은 창·front 블록 파일에 0,
    `IcmConfig` 에 `output_structure` 칸 없음."""
    assert _count("sizing/s2_values.py", r'"dc_output_structure"') == 1
    assert _count("sizing/writer_plan.py", r'"dc_output_structure"') >= 1
    for rel in ("metrics/icm_config.py", "sizing/window_refine.py", "metrics/icm_front.py"):
        assert _count(rel, r"\b_edges\b") == 0, rel
    assert _count("metrics/aux_types.py", r"\boutput_structure\b") == 0
