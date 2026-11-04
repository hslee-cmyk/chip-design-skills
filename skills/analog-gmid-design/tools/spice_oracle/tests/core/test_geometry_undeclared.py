"""OP-3 기하 선언 검사(실행 전 거부) -- interface §6 T3-1c~T3-1f, design §10.6·§7.2 3·4·5·6단계.

oracle (d): 회로 해석 결론(불일치 면적 의존은 기하 단위와 병렬 배수를 모르면 소자 줄을 정할 수 없다 -> 기본값 SI·배수 1 로 대체하지
않고 거부) + 구성: 선언을 지우는 한 곳만 바꾼 toy. 거부는 시뮬레이터 호출 0(stub.calls == [])이고 양성 대조(같은 요청, 완전 선언)는
stub 결과가 있다. 해석: 진입점 `oracle_run.main(argv, adapters=...)`; 거부 기록 `<circuit>.reject.json` 의 code·detail·stage.
"""
import json

import pytest

from op23_support import World, read_json_glob, read_reject
from stub_adapter import StubAdapter

DEV = {"M1": {"gm": 6e-4, "gds": 1.0 / 60000.0}}


def rejected(out):
    return (out / "cs_toy.reject.json").exists()


def test_t3_1c_positive_control_full_declaration_runs(tmp_path):
    w = World(tmp_path)
    stub = StubAdapter(DEV)
    rc, out = w.run(stub)
    assert not rejected(out) and len(stub.calls) >= 1                    # 완전 선언 + 공칭 op·ac = stub 결과 있음
    assert read_json_glob(out, "*.sim.json")["ac"]


@pytest.mark.parametrize("kw,missing", [
    ({"geometry_unit": None}, {"geometry_unit"}),
    ({"multiplier": False}, {"parallel_multiplier"}),
    ({"geometry_unit": None, "multiplier": False}, {"geometry_unit", "parallel_multiplier"}),
], ids=["no_unit", "no_multiplier", "neither"])
def test_t3_1c_undeclared_rejected_before_any_simulation(tmp_path, kw, missing):
    w = World(tmp_path, **kw)
    stub = StubAdapter(DEV)
    rc, out = w.run(stub)
    rec = read_reject(out)
    assert rc == 2
    assert rec["code"] == "descriptor_geometry_undeclared" and rec["stage"] == "3"
    assert rec["detail"]["kind"] == "nmos" and set(rec["detail"]["missing"]) == missing
    assert stub.calls == []                                              # 시뮬레이터 호출 0


def test_t3_1d_non_si_unit_without_application_method(tmp_path):
    w = World(tmp_path, geometry_unit={"source": "scale_q"})
    stub = StubAdapter(DEV)                                              # geometry_unit_application = [] (적용 방법 없음)
    rc, out = w.run(stub)
    rec = read_reject(out)
    assert rec["code"] == "adapter_capability_missing" and rec["detail"] == "geometry_unit_application"
    assert rec["stage"] == "5" and stub.calls == []


def test_t3_1d_global_directive_without_affects_declaration(tmp_path):
    w = World(tmp_path, geometry_unit={"source": "scale_q"})
    stub = StubAdapter(DEV, geometry_application=["global_directive"])   # 보정값에 global_geometry_directive 없음
    rc, out = w.run(stub)
    rec = read_reject(out)
    assert rec["code"] == "adapter_calibration_missing" and rec["stage"] == "6" and stub.calls == []


def with_offset_mc(w):
    inp = json.loads(json.dumps(w.inp))
    inp["offset_mc"] = {"rel_resolution": 0.1}
    return inp


def test_t3_1e_offset_mc_block_refused_when_descriptor_has_no_mc(tmp_path):
    w = World(tmp_path)                                                   # 기하 완전, 기술자에 mc 칸 없음
    stub = StubAdapter(DEV)
    rc, out = w.run(stub, inp=with_offset_mc(w))
    rec = read_reject(out)
    assert rec["code"] == "mc_method_unsupported" and rec["detail"]["side"] == "descriptor" and rec["stage"] == "4"
    assert stub.calls == []


def test_t3_1f_geometry_check_precedes_mc_check(tmp_path):
    w = World(tmp_path, multiplier=False)                                 # 기하 미선언 + offset_mc 블록
    stub = StubAdapter(DEV)
    rc, out = w.run(stub, inp=with_offset_mc(w))
    rec = read_reject(out)
    assert rec["code"] == "descriptor_geometry_undeclared"                # 3번이 4번보다 먼저
    assert stub.calls == []
