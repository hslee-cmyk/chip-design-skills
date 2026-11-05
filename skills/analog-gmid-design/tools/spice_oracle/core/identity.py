# -*- coding: utf-8 -*-
"""core/identity.py -- C15 topology 연결 동일성 (design §4.1, card 20261104-op23).

옛 코드는 오라클이 쓴 넷리스트 텍스트를 다시 파싱해 원소 표를 만들었다(`parse_netlist_elements`). 이제 IR 의 역할 표로 가른다:
`role == "circuit"` 원소만 topology JSON(netlist + passive_elements + ideal_sources)과 비교하고 테스트벤치 원소는 대조에서 뺀다.
파일 읽기·sha256 기록은 진입점 몫이다(코어가 여는 파일은 입력·기술자·출력뿐, design §3.2).
"""
from __future__ import annotations

from core.ir import Capacitor, ISource, Mos, Resistor, VSource

TOPOLOGY_SOURCE_KINDS = {"current_source": "current", "voltage_source": "voltage", "current": "current", "voltage": "voltage"}


def topology_elements(topo):
    """topology JSON -> {이름: (종류, 단자 넷 tuple, 바디 선언 여부)}, 이름 중복 목록. `_` 로 시작하는 키·dict 가 아닌 원소는 무시."""
    out, dup = {}, []

    def put(name, val):
        if name in out:
            dup.append(name)
        out[name] = val
    for e in topo.get("netlist") or []:
        if not isinstance(e, dict):
            continue
        t = (e.get("drain"), e.get("gate"), e.get("source")) + ((e["bulk"],) if "bulk" in e else ())
        put(e.get("name"), (e.get("kind"), t, "bulk" in e))
    for e in topo.get("passive_elements") or []:
        if isinstance(e, dict):
            put(e.get("name"), (e.get("kind"), tuple(e.get("terminals") or ()), False))
    for e in topo.get("ideal_sources") or []:
        if isinstance(e, dict):
            put(e.get("name"), (TOPOLOGY_SOURCE_KINDS.get(e.get("kind"), f"topology:{e.get('kind')}"),
                                tuple(e.get("terminals") or ()), False))
    return out, dup


def circuit_elements(circuit):
    """IR 의 본 회로 원소 표 {이름: (종류, 단자 넷 tuple)}와 테스트벤치 원소 이름 목록. 노드 '0' 은 기준 레일 넷 이름으로 되돌린다."""
    ground = circuit.meta.get("ground", "0")
    back = lambda n: ground if n == "0" else n    # noqa: E731
    elems, tbe = {}, []
    for e in circuit.elements:
        if circuit.role.get(e.name) != "circuit":
            tbe.append(e.name)
            continue
        if isinstance(e, Mos):
            elems[e.name] = (e.kind, tuple(back(n) for n in (e.d, e.g, e.s, e.b)))
        elif isinstance(e, Resistor):
            elems[e.name] = ("resistor", (back(e.a), back(e.b)))
        elif isinstance(e, Capacitor):
            elems[e.name] = ("capacitor", (back(e.a), back(e.b)))
        elif isinstance(e, ISource):
            elems[e.name] = ("current", (back(e.p), back(e.n)))
        elif isinstance(e, VSource):
            elems[e.name] = ("voltage", (back(e.p), back(e.n)))
        else:
            raise TypeError(f"본 회로 IR 원소 종류 밖: {type(e).__name__}")
    return elems, tbe


def topology_identity(circuit, topo):
    """C15: IR 본 회로 원소 집합과 topology JSON 의 집합 비교. 반환 {status: verified|mismatch, diffs, compared, excluded_testbench,
    declared_not_in_topology, bulk_compared, bias_inputs}. 비교 규칙: 원소 이름 집합·종류·단자 넷이 같다. MOS 는 (d, g, s) 순서 그대로
    (+ topology 가 bulk 를 선언했으면 bulk), 저항·커패시터는 순서 무관, 이상원은 순서 그대로(방향). 입력 passives/sources 중
    not_in_topology_reason 이 있는 원소는 비교에서 빼고 이유와 함께 기록한다. 입력 bias_voltages 넷 집합 == topology bias_inputs."""
    res = {"status": "unverified", "diffs": [], "compared": 0, "excluded_testbench": [], "declared_not_in_topology": {},
           "bulk_compared": []}
    want, dup = topology_elements(topo)
    got, tbe = circuit_elements(circuit)
    res["excluded_testbench"] = tbe
    diffs = [f"topology 원소 이름 중복: {n}" for n in sorted(set(dup))]
    extra = dict(circuit.meta.get("not_in_topology") or {})
    res["declared_not_in_topology"] = extra
    for n in sorted(extra):
        got.pop(n, None)
    for n in sorted(set(want) - set(got)):
        diffs.append(f"{n}: topology 에 있고 넷리스트에 없다")
    for n in sorted(set(got) - set(want)):
        diffs.append(f"{n}: 넷리스트에 있고 topology 에 없다")
    for n in sorted(set(want) & set(got)):
        wk, wt, has_bulk = want[n]
        gk, gt = got[n]
        res["compared"] += 1
        if gk != wk:
            diffs.append(f"{n}: 종류 topology {wk} != 넷리스트 {gk}")
        if wk in ("resistor", "capacitor"):
            same = sorted(wt) == sorted(gt)
        elif len(gt) == 4 and not has_bulk:
            same = tuple(gt[:3]) == tuple(wt)
        else:
            same = tuple(gt) == tuple(wt)
        if has_bulk:
            res["bulk_compared"].append(n)
        if not same:
            diffs.append(f"{n}: 단자 넷 topology {list(wt)} != 넷리스트 {list(gt[:len(wt)]) if len(gt) == 4 else list(gt)}")
    bi = topo.get("bias_inputs", [])
    if not isinstance(bi, list) or not all(isinstance(x, str) for x in bi):
        diffs.append(f"topology bias_inputs 가 문자열 list 가 아니다: {bi!r}")
    else:
        want_b, got_b = set(bi), set(circuit.meta.get("bias_nets") or [])
        res["bias_inputs"] = sorted(want_b)
        if want_b != got_b:
            diffs.append(f"bias_voltages 넷 {sorted(got_b)} != topology bias_inputs {sorted(want_b)} "
                         f"(topology 에만 {sorted(want_b - got_b)}, 입력에만 {sorted(got_b - want_b)})")
    res["diffs"] = diffs
    res["status"] = "mismatch" if diffs else "verified"
    return res
