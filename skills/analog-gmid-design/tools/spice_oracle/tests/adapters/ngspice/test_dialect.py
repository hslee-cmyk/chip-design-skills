"""ngspice 어댑터 방언 -- 소자 줄 작성기 `device_line`, 전체 `render`, 능력·보정 선언 -- interface §6 T3-1a·b, T3-2, §5 `Adapter`.

oracle (a): 구성으로 정해진 손 계산 -- 기하 칸은 단위 u 의 거듭제곱으로 나눈 숫자(길이 u^1, 면적 u^2, 손으로 나눗셈),
`.option scale` 줄을 직접 쓰고, 배수는 `to` 대상 전부에 같은 값, R·C·전원 값은 그대로(D §10.6, spec C-3.4). 다른 방법의 계산이므로
작성기 식을 test 에 다시 쓰지 않고 숫자를 손으로 대입한다.
해석(interface 모호): `device_line(mos, name_str, unit_u, to)` 의 name_str = 호출하는 subckt 이름(expected 의 `sub`), `unit_u` = "si" 이면
1.0, `to` = `[{"target": "instance_multiplier"}, {"target": "model_param", "name": "mult"}]`(이름 해석을 마친 꼴),
소자 줄 이름 = 'X' + mos.name. `render` 의 descriptor 는 `doc`·`quantity(키)`·`source_path(키)`·`fp` 만 쓰는 대역을 준다.
"""
import re
from types import SimpleNamespace

import pytest

from adapters.ngspice.dialect import device_line, render
from core.ir import Capacitor, Circuit, Diffusion, Mos, Resistor, VSource
from core.requests import Condition, Op, OpOutputs

from op23_support import build_toy

TO_BOTH = [{"target": "instance_multiplier"}, {"target": "model_param", "name": "mult"}]
TO_INST = [{"target": "instance_multiplier"}]


def mos(diffusion=True):
    return Mos(name="M1", kind="nk", d="o", g="i", s="s", b="b", L=5e-7, finger_w=1e-6, n_fingers=2,
               diffusion=Diffusion(ad=5e-13, as_=5e-13, pd=3e-6, ps=3e-6) if diffusion else None, lod=None)


def parse(line):
    t = line.split()
    kv = {k.lower(): v for k, v in (x.split("=", 1) for x in t if "=" in x)}
    return t, kv


def nums(kv):
    return {k: float(v) for k, v in kv.items()}


def test_t3_1a_scaled_geometry_and_multiplier_both_targets():
    # u = 1e-6: l = 5e-7/1e-6 = 0.5, w = 1e-6/1e-6 = 1, ad = as = 5e-13/(1e-6)^2 = 0.5, pd = ps = 3e-6/1e-6 = 3, m = mult = 2
    t, kv = parse(device_line(mos(), "sub", 1e-6, TO_BOTH))
    assert t[0] == "XM1" and t[1:6] == ["o", "i", "s", "b", "sub"]
    exp = {"l": 0.5, "w": 1.0, "m": 2.0, "mult": 2.0, "ad": 0.5, "as": 0.5, "pd": 3.0, "ps": 3.0}
    assert set(kv) == set(exp)
    for k, v in nums(kv).items():
        assert v == pytest.approx(exp[k], rel=1e-9), k


def test_t3_1b_si_numbers_ten_significant_digits_and_multiplier_instance_only():
    t, kv = parse(device_line(mos(), "sub", 1.0, TO_INST))
    assert t[0] == "XM1" and t[1:6] == ["o", "i", "s", "b", "sub"]
    # 표기: format(x, ".10g") -- 5e-07, 1e-06, 5e-13, 3e-06 (손으로 쓴 문자열)
    assert kv == {"l": "5e-07", "w": "1e-06", "m": "2", "ad": "5e-13", "as": "5e-13", "pd": "3e-06", "ps": "3e-06"}


def test_geometry_scales_with_u_not_hard_coded():
    # u = 2e-6 (손 대입): l = 0.25, w = 0.5, ad = as = 5e-13/(2e-6)^2 = 0.125, pd = ps = 1.5
    t, kv = parse(device_line(mos(), "sub", 2e-6, TO_INST))
    exp = {"l": 0.25, "w": 0.5, "m": 2.0, "ad": 0.125, "as": 0.125, "pd": 1.5, "ps": 1.5}
    for k, v in nums(kv).items():
        assert v == pytest.approx(exp[k], rel=1e-9), k


def test_multiplier_targets_exactly_as_declared():
    # 대상을 빼거나 더하지 않는다(D §10.6): 모델 파라미터만 선언하면 인스턴스 m 은 없다
    t, kv = parse(device_line(mos(), "sub", 1.0, [{"target": "model_param", "name": "mult"}]))
    assert "m" not in kv and kv["mult"] == "2"


def test_no_diffusion_means_no_diffusion_tokens():
    t, kv = parse(device_line(mos(diffusion=False), "sub", 1.0, TO_INST))
    assert not ({"ad", "as", "pd", "ps"} & set(kv))


# ------------------------------------------------------------------ T3-2 render
def descriptor_stub(tmp_path, u):
    toy = build_toy(tmp_path, kind="nk", geometry_unit={"source": "scale_q"})
    return SimpleNamespace(doc=toy.doc, fp="d" * 64, quantity=lambda key: u,
                           source_path=lambda key: str(toy.pdk / f"{key}.lib"), path=str(toy.d))


def circuit():
    els = (mos(), Resistor(name="RL", a="vdd", b="o", value=2e4), Capacitor(name="CL", a="o", b="s", value=1e-12),
           VSource(name="Vd", p="vdd", n="s", dc=1.8))
    return Circuit(elements=els, role={"M1": "circuit", "RL": "circuit", "CL": "circuit", "Vd": "testbench"}, meta={})


def test_t3_2_render_values_directive_and_options(tmp_path):
    cond = Condition(temp_c=27.0, corner="tt")
    reqs = (Op(id="op", cond=cond, exc=(), outputs=OpOutputs(devices="all", nodes=(), currents=())),)
    opts = {"reltol": "1e-4", "vntol": "1e-7", "abstol": "1e-13"}
    text, name_map = render(circuit(), reqs, descriptor_stub(tmp_path, 1e-6), cond, opts)
    assert text.endswith("\n") and "\r" not in text
    lines = text.splitlines()

    def line_of(ir_name):
        hits = [ln for ln in lines if ln.split() and ln.split()[0] == name_map[ir_name]]
        assert len(hits) == 1, (ir_name, hits)
        return hits[0].split()

    # R·C·전원 값은 단위 u 로 나뉘지 않고 그대로 (R 2e4 -> 20000, C 1e-12, V 1.8)
    assert float(line_of("RL")[-1]) == 20000.0
    assert float(line_of("CL")[-1]) == 1e-12
    v = line_of("Vd")
    assert float(v[[x.lower() for x in v].index("dc") + 1]) == 1.8
    # 소자 줄은 u^power 로 나눈 숫자(.option scale 가 배율을 되돌린다)
    kv = nums(parse(" ".join(line_of("M1")))[1])
    assert kv["l"] == pytest.approx(0.5, rel=1e-9) and kv["w"] == pytest.approx(1.0, rel=1e-9)
    assert kv["ad"] == pytest.approx(0.5, rel=1e-9) and kv["pd"] == pytest.approx(3.0, rel=1e-9)
    # .option 줄: scale 값은 한 줄에 정확히 하나, simulator.options 키는 전부
    opt_lines = [ln for ln in lines if ln.lower().startswith(".option")]
    scale = [m.group(1) for ln in opt_lines for m in re.finditer(r"\bscale\s*=\s*(\S+)", ln, re.I)]
    assert len(scale) == 1 and float(scale[0]) == 1e-6
    joined = " ".join(opt_lines)
    for k, val in opts.items():
        assert re.search(rf"\b{k}\s*=\s*{re.escape(val)}", joined, re.I), k
    # .temp 와 include
    assert any(ln.lower().startswith(".temp") and float(ln.split()[1]) == 27.0 for ln in lines)
    inc = " ".join(ln for ln in lines if ln.lower().startswith((".include", ".inc", ".lib")))
    assert "a.lib" in inc and "x.lib" in inc                         # 기술자 includes 순서대로 둘 다 (toy kind nk = [a, x])
    assert inc.index("a.lib") < inc.index("x.lib")


def test_t3_2_name_map_is_total_and_injective(tmp_path):
    cond = Condition(temp_c=27.0, corner="tt")
    reqs = (Op(id="op", cond=cond, exc=(), outputs=OpOutputs(devices="all", nodes=(), currents=())),)
    c = circuit()
    _, name_map = render(c, reqs, descriptor_stub(tmp_path, 1e-6), cond, {"reltol": "1e-4"})
    ir_names = {e.name for e in c.elements}
    assert ir_names <= set(name_map)                                  # 전체를 덮음
    vals = [name_map[n] for n in ir_names]
    assert len({v.lower() for v in vals}) == len(vals)                # 단사(방언은 대소문자 구분 없음)


# ------------------------------------------------------------------ 능력·보정 선언 (interface §5 Adapter, D-1)
def make_adapter():
    import sys
    from adapters import ngspice
    return ngspice.Adapter(exe=sys.executable)         # 해석: 생성자는 실행 파일 경로를 받는다(능력·보정 조회는 실행하지 않음)


def test_capabilities_first_period_declaration():
    caps = make_adapter().capabilities()
    for k in ("op", "ac", "temperature", "instance_geometry_readback", "case_insensitive_names"):
        assert caps[k] is True, k
    for k in ("tran", "pz", "noise", "op_sweep", "tf", "mc_native", "mc_keep_identity", "mc_diagnostic"):
        assert caps[k] is False, k                                    # [D-1] OP-3 기간에 선언하지 않는다
    assert caps["geometry_unit_application"] == ["global_directive"]
    assert caps["model_families"] and all(isinstance(x, str) and x for x in caps["model_families"])


def test_calibration_every_value_has_a_source_and_directive_is_complete():
    cal = make_adapter().calibration()
    assert {"default_tolerances", "data_digits", "simulator_version_probe", "global_geometry_directive"} <= set(cal)
    for k in ("reltol", "vntol", "abstol"):
        assert cal["default_tolerances"][k]["source"], k              # 출처 칸 필수(숨은 상수 금지)
    assert cal["data_digits"]["source"] and cal["simulator_version_probe"]["source"]
    g = cal["global_geometry_directive"]
    assert g["source"] and g["affects"] and set(g["affects"]) <= set(g["power"])
    assert all(p in (1, 2) for p in g["power"].values())             # 길이 u^1, 면적 u^2
