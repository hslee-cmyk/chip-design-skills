"""새 ngspice 어댑터 대 손 넷리스트 독립 기준 (oracle (c)/(b): 옛 오라클·새 어댑터 어느 쪽의 코드도 거치지 않는 손으로 쓴 ngspice 넷리스트)
-- 판정 A3-11. 시뮬레이터를 실행하는 test 다(판정자가 돌린다). 수치 일치가 아니라 **같은 회로 정의** 대조다:

  독립 기준 = finger 마다 인스턴스 하나(w = finger_w, m 없음, 확산 기하 없음), 전역 scale 없음, 전부 SI 숫자.
  새 어댑터 = IR(`Mos.n_fingers`)을 배수 m 으로, 기하는 기술자 선언 단위 u 로 나눈 숫자 + `.option scale`.
  두 방법이 같은 회로를 뜻하면 동작점·AC 가 시뮬레이터 수렴 허용 안에서 같다. 허용 = 요청 reltol 1e-4(독립 쪽 .option 과 같은 값)의
  10 배인 1e-3 (서로 다른 넷리스트가 각자 Newton 수렴 허용 안에서 멈추는 차 + AC 가 그 동작점에서 한 번 더 누적).
  부호는 비교하지 않는다(ID 부호 규칙의 정의 동일성은 별도 정의 문장), 크기만 비교한다.
해석: `adapters.ngspice.Adapter(exe=...)`, `adapter.run(circuit, requests, descriptor, work_dir, timeout_s, cache_dir, compat)`,
`by_request[id]` = OpTable / FreqSeries. 기술자 = 실제 sky130 기술자 `O/descriptors/sky130.oracle_descriptor.json`(OP-2 산출).
"""
import os

import numpy as np
import pytest

from adapters.ngspice import Adapter
from core.descriptor import load_descriptor
from core.ir import Capacitor, Circuit, Mos, Resistor, VSource
from core.requests import Ac, Condition, NodeV, Op, OpOutputs

from conftest import CS, FB, NGSPICE, ORACLE_DIR
from independent_ref import independent_cs, independent_fb

RTOL = 1e-3
COND = Condition(temp_c=27.0, corner="tt")


@pytest.fixture(scope="module")
def descriptor():
    return load_descriptor(ORACLE_DIR / "descriptors" / "sky130.oracle_descriptor.json", env=os.environ)


def ir(elements):
    return Circuit(elements=tuple(elements), role={e.name: "circuit" for e in elements}, meta={})


def run(descriptor, circuit, requests, tmp_path):
    return Adapter(exe=str(NGSPICE)).run(circuit, tuple(requests), descriptor, str(tmp_path / "work"), None, None, None)


def op_req(nodes):
    return Op(id="op", cond=COND, exc=(), outputs=OpOutputs(devices="all", nodes=tuple(nodes), currents=()))


def ac_req(node, f0, f1, ppd):
    return Ac(id="ac", cond=COND, exc=(), f_start=f0, f_stop=f1, points_per_decade=ppd, f_list=None, outputs=(NodeV(node),))


def cs_circuit():
    c = CS
    return ir([
        VSource("Vdd", "vdd", "0", c["vdd"]), VSource("Vsp", "vsp", "0", c["vsp"]),
        VSource("Vin", "nin", "0", c["vin"], ac_mag=1.0), VSource("Vpb", "pb", "0", c["pb"]),
        Mos("M1", "nmos", "nout", "nin", "0", "0", c["L"], c["finger_w"], c["n"], None, None),
        Mos("MP1", "pmos", "pout", "pb", "vsp", "vdd", c["pL"], c["pfinger_w"], c["pn"], None, None),
        Resistor("RL", "vdd", "nout", c["rload"]), Capacitor("CL", "nout", "0", c["cl"]),
        Resistor("RP", "pout", "0", c["rp"])])


def test_cs_operating_point_matches_independent_netlist(ref_root, descriptor, tmp_path):
    ind = independent_cs(ref_root)
    res = run(descriptor, cs_circuit(), [op_req(("nout", "pout"))], tmp_path)
    assert res.status.error is None
    op = res.by_request["op"]
    for net in ("nout", "pout"):
        assert op.nodes[net] == pytest.approx(ind["V"][net], rel=RTOL, abs=1e-6), net
    for name, key in (("M1", "M1"), ("MP1", "MP1")):
        d = op.devices[name]
        assert abs(d["id"]) == pytest.approx(abs(ind[key]["id"]), rel=RTOL), name
        assert d["gm"] == pytest.approx(ind[key]["gm"], rel=RTOL), name
        assert d["gds"] == pytest.approx(ind[key]["gds"], rel=RTOL), name


def test_cs_ac_response_matches_independent_netlist(ref_root, descriptor, tmp_path):
    ind = independent_cs(ref_root)
    res = run(descriptor, cs_circuit(), [ac_req("nout", 0.01, 1e10, 40)], tmp_path)
    assert res.status.error is None
    fs = res.by_request["ac"]
    (h,) = fs.values.values()
    assert np.asarray(fs.f).shape == np.asarray(ind["f"]).shape
    assert np.allclose(np.asarray(fs.f), ind["f"], rtol=1e-9)           # 같은 로그 격자
    scale = float(np.max(np.abs(ind["H"])))
    assert np.allclose(h, ind["H"], rtol=RTOL, atol=1e-9 * scale)


def test_feedback_circuit_operating_point_matches_independent_netlist(ref_root, descriptor, tmp_path):
    c = FB
    ind = independent_fb(ref_root)
    circuit = ir([
        VSource("Vdd", "vdd", "0", c["vdd"]), VSource("Vin", "nin", "0", c["vin"]),
        Mos("M1", "nmos", "nout", "nin", "0", "0", c["L"], c["finger_w"], c["n"], None, None),
        Resistor("RL", "vdd", "nout", c["rload"]), Resistor("Rf", "nout", "nin", c["rf"])])
    res = run(descriptor, circuit, [op_req(("nout",))], tmp_path)
    assert res.status.error is None
    op = res.by_request["op"]
    assert op.nodes["nout"] == pytest.approx(ind["vout"], rel=RTOL, abs=1e-6)
    d = op.devices["M1"]
    assert d["gm"] == pytest.approx(ind["gm"], rel=RTOL) and d["gds"] == pytest.approx(ind["gds"], rel=RTOL)
