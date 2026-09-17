# -*- coding: utf-8 -*-
"""'전압 구동 CG stage 시작' 규칙 분기의 **발동 회로**가 생겼는지 library 전수로 잰다.

계획서는 이 분기를 "검증 발동 0"으로 적어 두었다(DEC-59 -> 해당 회로는 탐색 전 정지).
`common_gate_amplifier` 추가가 그 분기를 실제로 발동시키는지, 그리고 기존 회로의 CG 셀은
여전히 **전류 구동**뿐인지를 함께 확인한다(= 추가가 기존 판독을 바꾸지 않는다).

적용 규칙(계획 v5.18):
  * CG = gate가 그 뷰의 신호 경로 밖이고, 신호가 source로 들어와 drain으로 나가는 셀.
    **CG/pass 판별은 거리 비교가 아니라 '그 소자를 지나지 않고도 drain에 닿는가'로 한다**
    -- 그 소자의 채널 엣지를 뺀 그래프에서 drain이 여기로부터 도달하지 못하면 CG.
  * source 노드의 구동 종류: 입력 포트(이상원)로 들어오면 **전압 구동**,
    신호 셀의 drain으로 들어오면 **전류 구동**(용어집 '입력 노드 구동 종류').

결과는 stdout이 아니라 같은 이름 `.txt`에 append한다(세션 규칙).
"""
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LIB = os.path.join(ROOT, "skills", "analog-gmid-design", "assets", "library")
OUT = os.path.splitext(os.path.abspath(__file__))[0] + ".txt"

spec = importlib.util.spec_from_file_location(
    "scan", os.path.join(HERE, "review9_bias_dependent_net_scan.py"))
SCAN = importlib.util.module_from_spec(spec)
sys.modules["scan"] = SCAN
spec.loader.exec_module(SCAN)


def drive_of(net, mos, sig, ports):
    """그 노드로 신호가 들어오는 단자의 종류."""
    kinds = []
    if net in ports and ports[net].get("direction") == "input":
        kinds.append("전압(입력 포트)")
    for m in mos:
        if m["drain"] == net and (m["gate"] in sig or m["source"] in sig):
            kinds.append("전류(신호 셀 drain)")
        if m["source"] == net and m["gate"] in sig:
            kinds.append("전압(CD 출력)")
    return "+".join(sorted(set(kinds))) or "미판정"


def main():
    lines = ["=== '전압 구동 CG' 분기 발동 측정 (library 전수) ===",
             "CG 판별: 그 소자의 채널 엣지를 뺀 그래프에서 drain이 여기로부터 도달하지 못하면 CG.", ""]
    voltage_driven, current_driven = [], []
    for fn in sorted(os.listdir(LIB)):
        if not fn.endswith(".topology.json") or fn.startswith("_TEMPLATE"):
            continue
        d = json.load(io.open(os.path.join(LIB, fn), encoding="utf-8"))
        name = str(d.get("topology_name"))
        mos = [m for m in d["netlist"] if isinstance(m, dict)]
        pas = [e for e in (d.get("passive_elements") or []) if isinstance(e, dict)]
        ports = {k: v for k, v in (d.get("ports") or {}).items() if isinstance(v, dict)}
        ex = SCAN.excitation(d)
        if not ex:
            lines.append(f"  {name:30s} 측정 불가(입력 포트 미선언)")
            continue
        rails = SCAN.rails_of(d, mos, pas)
        acg = SCAN.ac_ground(d, mos, pas, rails, set())
        sig = SCAN.signal_nets(mos, pas, ex, acg)
        found = []
        for m in mos:
            if m["gate"] in sig or m["source"] not in sig or m["drain"] not in sig:
                continue
            # 이 소자의 채널을 뺀 그래프에서 drain이 도달 가능한가
            others = [x for x in mos if x["name"] != m["name"]]
            sig_wo = SCAN.signal_nets(others, pas, ex, acg)
            if m["drain"] in sig_wo:
                continue                     # 우회로가 있다 -> pass 후보
            drv = drive_of(m["source"], mos, sig, ports)
            found.append((m["name"], m["source"], m["drain"], drv))
        if not found:
            lines.append(f"  {name:30s} CG 0개")
            continue
        lines.append(f"  {name:30s} CG {len(found)}개")
        for nm, s_, d_, drv in found:
            lines.append(f"      {nm:6s} source={s_:10s} drain={d_:10s} 구동={drv}")
            (voltage_driven if drv.startswith("전압") else current_driven).append(f"{name}.{nm}")
    lines += ["",
              f"전압 구동 CG: {voltage_driven or '없음'}",
              f"전류 구동 CG: {current_driven or '없음'}",
              "판정: 전압 구동 CG가 하나라도 있으면 '전압 구동 CG stage 시작' 분기의 발동 회로가 "
              "생긴 것이고, DEC-59의 '검증 발동 0 -> 탐색 전 정지'가 그 분기에서 풀린다.",
              ""]
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
