# -*- coding: utf-8 -*-
"""Vg15/Vop1 노드의 실제 DC KCL을 sympy로 처음부터(from scratch) 재유도한다.

동기(2026-08, 세션6): 사용자가 "M10과 M8은 같은 branch 전류인데 독립적이야?"라고 물었고,
현재 topology.json은 M8(r_classab_src)과 M10(r_sink_vop1vom1)을 독립 free theta로 두고
있다. do.md(analog-topology-json-library) §7.3.1 재분류표(733행)는 원래 "M12/M10 |
유형A | M8/M9b계 KCL 직렬"이라고 명시했었다 -- 즉 원래는 독립이 아니었는데, 세션5에서
branch_symmetric 오용 버그(우연히 M12 전류를 물려받던 것)를 고치며 이 KCL 연결이
같이 사라지고 그 자리를 "논문에 공식 없음" 사유로 새 자유 theta가 메웠다.

이 스크립트는 손으로 유도하지 않는다(그 과정에서 기존 `kcl_battery_M9b` theta의 주석이
"Vg15 노드 3단자 = M11b.drain/M9a.drain/M9b.drain"이라고 적어놨는데, 실제 netlist는
M11b.drain=N11b, M9a.drain=Vop1이라 **둘 다 Vg15가 아니다** -- 이 불일치를 발견한 것 자체가
손 유도의 위험성을 보여줌, `feedback_no_paper_values_derive_rationally`/
`feedback_no_assumption_without_evidence` 원칙). 대신 `stage1_cmrr_sympy_derivation.py`와
같은 방식으로 **오직 `load_topology()`가 돌려주는 실제 connectivity만** 읽어 프로그램적으로
KCL을 조립한다(손타이핑 netlist 없음).

전류 부호 규약(DC, 소자 kind별로 명시적 -- 소신호 MNA와 다름, 여기서는 실제 DC 전류의
물리적 방향이 필요하다):
  NMOS: 전류가 drain -> source로 흐른다(관행) -- drain 노드는 I(d)를 잃고
        (전류가 노드에서 소자로 들어감), source 노드는 I(d)를 얻는다(소자에서 노드로 나옴).
  PMOS: 전류가 source -> drain으로 흐른다 -- source 노드는 I(d)를 잃고,
        drain 노드는 I(d)를 얻는다.
  (둘 다 "정상 동작(포화) 상태에서 실제로 흐르는 방향 = 양수"라는 표준 관행이며,
  이 프로젝트의 다른 곳(예: allocate_stack_headroom 대상 스택)과도 일치.)

결과가 코드 자체(KCL 방정식과 sympy solve)로 증거를 남긴다 -- 사람이 재확인 가능."""
import os
import sys

import sympy as sp

_HERE = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.abspath(os.path.join(
    _HERE, "..", "..", "..", "skills", "analog-gmid-design", "assets"))
sys.path.insert(0, _ASSETS)
from stick_diagram import load_topology  # noqa: E402

TOPO_JSON = os.path.join(_ASSETS, "library", "current_reuse_telescopic_ota.topology.json")


def load_all():
    trs, meta = load_topology(TOPO_JSON)
    return {t.name: t for t in trs}, meta


def device_current_symbol(name):
    return sp.Symbol(f"I_{name}", real=True)


def node_kcl_terms(by_name, node):
    """`node`에 실제 전류 단자(source 또는 drain)로 연결된 모든 소자를 훑어
    "node가 얻는 전류(+)/잃는 전류(-)" 항의 리스트를 돌려준다. gate 연결은 전류가
    안 흐르므로 무시(이 프로젝트 다른 소신호 코드와 동일 전제)."""
    terms = []
    for name, t in by_name.items():
        I = device_current_symbol(name)
        if t.drain == node:
            terms.append(I if t.kind == "pmos" else -I)   # pmos: drain이 얻음 / nmos: drain이 잃음
        if t.source == node:
            terms.append(-I if t.kind == "pmos" else I)   # pmos: source가 잃음 / nmos: source가 얻음
    return terms


def report_node(by_name, node):
    print(f"--- node {node!r} 실제 connectivity(load_topology() 그대로) ---")
    for name, t in by_name.items():
        if node in (t.source, t.drain):
            role = "drain" if t.drain == node else "source"
            print(f"  {name:6s} kind={t.kind:4s} {role:6s}=={node}"
                  f"  (source={t.source}, drain={t.drain}, gate={t.gate})")


def main():
    by_name, meta = load_all()

    for node in ("Vg15", "Vop1"):
        report_node(by_name, node)
        print()

    print("=" * 78)
    print("KCL 방정식(프로그램적으로 조립, 손타이핑 아님)")
    print("=" * 78)
    eqs = {}
    for node in ("Vg15", "Vop1"):
        terms = node_kcl_terms(by_name, node)
        eq = sp.Eq(sp.Add(*terms), 0)
        eqs[node] = eq
        print(f"  KCL[{node}]:  {eq}")

    print()
    print("=" * 78)
    print("Vg15 KCL로 I_M9b를 풀고, 그 결과를 Vop1 KCL에 대입해 I_M10을 I_M8/I_M9a/"
          "I_M2b/I_M3b로 표현")
    print("=" * 78)
    I = device_current_symbol
    sol_m9b = sp.solve(eqs["Vg15"], I("M9b"))
    print(f"  Vg15 KCL에서 I_M9b = {sol_m9b}")
    assert len(sol_m9b) == 1
    eq_vop1_sub = eqs["Vop1"].subs(I("M9b"), sol_m9b[0])
    sol_m10 = sp.solve(eq_vop1_sub, I("M10"))
    print(f"  Vop1 KCL(I_M9b 대입 후)에서 I_M10 = {sol_m10}")
    assert len(sol_m10) == 1
    final = sp.simplify(sol_m10[0])
    print()
    print(f"  ==> I(M10) = {final}")
    print()

    print("=" * 78)
    print("기존 kcl_battery_M9b theta(topology.json)와 대조")
    print("=" * 78)
    print("  topology.json의 주석 주장: Vg15 3단자 = M11b.drain/M9a.drain/M9b.drain")
    print(f"    실제 M11b.drain = {by_name['M11b'].drain!r}  (Vg15와 같은가: "
          f"{by_name['M11b'].drain == 'Vg15'})")
    print(f"    실제 M9a.drain  = {by_name['M9a'].drain!r}  (Vg15와 같은가: "
          f"{by_name['M9a'].drain == 'Vg15'})")
    print("  -> 이 스크립트가 프로그램적으로 찾은 Vg15의 실제 3단자는 위 리포트 참고"
          "(M8.drain/M9a.source/M9b.drain)")
    print()
    print(f"  기존 theta 공식: ID(M9b) = ID(M11a-chain) + ID(M9a)")
    print(f"  이 스크립트 결과: I_M9b = {sol_m9b[0]}  (M11a-chain 항 없음)")
    print()

    print("=" * 78)
    print("검산: I_M2b/I_M3b는 2단자 net으로 각각 I_M1b/I_M4b와 직렬 강제(참고용, 여기선 "
          "기호로 유지)")
    print("=" * 78)
    print(f"  N1b2b(M1b.drain/M2b.source) 2단자: "
          f"{by_name['M1b'].drain!r} == {by_name['M2b'].source!r} "
          f"-> {by_name['M1b'].drain == by_name['M2b'].source}")
    print(f"  N3b4b(M3b.source/M4b.drain) 2단자: "
          f"{by_name['M3b'].source!r} == {by_name['M4b'].drain!r} "
          f"-> {by_name['M3b'].source == by_name['M4b'].drain}")


if __name__ == "__main__":
    main()
