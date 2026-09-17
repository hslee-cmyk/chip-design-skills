# -*- coding: utf-8 -*-
"""용어집 'DC 역할' 유도 절차를 library 9회로 전수로 돌려 발동·오발동을 잰다.

절차(계획 N0.4 용어집 '소자 역할(DC·AC)'):
  (1) gate == drain          -> diode 기준
  (2) gate 넷과 source 넷을 **둘 다** 공유하는 다른 소자가 있으면 -> 바이어스 전류원
      (VGS가 같아 DC 전류가 비례로 묶인다. 그룹에 diode가 있으면 그 소자만 diode 기준)
  (3) gate 넷이 모든 뷰에서 교류접지 -> 바이어스 전류원
  (4) 선언된 equal_vgs·matching_ratio·kcl_group으로 그 그룹에 닿으면 상속
  (5) 나머지 -> 신호 소자

확인할 것(과발동 점검):
  * 입력 차동쌍은 **신호 소자**여야 한다(gate가 서로 달라 (2)에 안 걸려야 한다)
  * 공통모드 되먹임이 tail 게이트를 구동하는 소자는 **바이어스 전류원**이어야 한다
    (규칙 5의 stage 시작 예외가 그 값을 쓴다)
  * 측면 주입 후보(K8)는 **바이어스 전류원**이어야 한다(J12-d 기본안이 그 값을 쓴다)

결과는 stdout이 아니라 같은 이름 `.txt`에 append한다(세션 규칙).
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LIB = os.path.join(ROOT, "skills", "analog-gmid-design", "assets", "library")
OUT = os.path.splitext(os.path.abspath(__file__))[0] + ".txt"
NAMESET = {"vdd", "vss", "gnd"}


def ac_ground_always(d, mos):
    """모든 뷰에서 교류접지인 넷: 레일 + gate에만 붙고 구동되지 않는 넷."""
    rails = set(d.get("supply_nets") or {n for m in mos for n in
                                          (m["drain"], m["gate"], m["source"]) if n in NAMESET})
    driven = set()
    for m in mos:
        driven |= {m["drain"], m["source"]}
    for e in (d.get("passive_elements") or []):
        if isinstance(e, dict):
            driven |= set(e.get("terminals") or [])
    for s in (d.get("ideal_sources") or []):
        if isinstance(s, dict):
            driven |= {t for t in (s.get("terminals") or []) if t}
    ports = set((d.get("ports") or {}).keys())
    return rails | ({m["gate"] for m in mos} - driven - ports)


def derive(d, mos):
    acg = ac_ground_always(d, mos)
    role = {}
    # (1) diode 기준
    for m in mos:
        if m["gate"] == m["drain"]:
            role[m["name"]] = "diode 기준"
    # (2) gate 넷 + source 넷 공유 그룹 -- **기준이 그룹 안에 있을 때만**
    groups = {}
    for m in mos:
        groups.setdefault((m["gate"], m["source"]), []).append(m)
    shared, undecided = {}, []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        has_diode = any(x["gate"] == x["drain"] for x in members)
        gate_is_acg = key[0] in acg
        if has_diode or gate_is_acg:
            for m in members:
                if role.get(m["name"]) != "diode 기준":
                    role[m["name"]] = "바이어스 전류원"
            shared[key] = [x["name"] for x in members]
        else:
            # 공유 VGS지만 기준이 그룹 밖(자기바이어스 사슬 등) -> 구조만으로 못 가른다
            undecided.append((key, [x["name"] for x in members]))
    # (3) gate 넷이 항상 교류접지 **이고 source가 레일**
    rails = set(d.get("supply_nets") or set())
    for m in mos:
        if m["name"] not in role and m["gate"] in acg and m["source"] in rails:
            role[m["name"]] = "바이어스 전류원"
    # (5) 나머지
    for m in mos:
        role.setdefault(m["name"], "신호 소자")
    return role, shared, undecided


def main():
    lines = ["=== DC 역할 유도 절차 -- library 9회로 전수 ===",
             "(4) 선언 상속은 현 library에 해당 선언이 없어 측정에서 빠진다(발동 0).", ""]
    for fn in sorted(os.listdir(LIB)):
        if not fn.endswith(".topology.json") or fn.startswith("_TEMPLATE"):
            continue
        d = json.load(io.open(os.path.join(LIB, fn), encoding="utf-8"))
        name = str(d.get("topology_name"))
        mos = [m for m in d["netlist"] if isinstance(m, dict)]
        role, shared, undecided = derive(d, mos)
        cnt = {}
        for v in role.values():
            cnt[v] = cnt.get(v, 0) + 1
        lines.append(f"  {name:30s} 소자 {len(mos)}  " +
                     " / ".join(f"{k} {v}" for k, v in sorted(cnt.items())))
        for key, members in sorted(shared.items()):
            lines.append(f"      공유 VGS 그룹(기준 있음) (g={key[0]}, s={key[1]}): {members}")
        for key, members in sorted(undecided):
            lines.append(f"      ** 구조로 못 가름 (g={key[0]}, s={key[1]}): {members} -> J ratify")
        sig = [n for n, v in role.items() if v == "신호 소자"]
        lines.append(f"      신호 소자: {sorted(sig)}")
    lines += ["",
              "과발동 점검 기준: 입력 차동쌍이 '신호 소자'로 남아야 하고(gate가 서로 달라 (2)에 걸리지 "
              "않는다), 공통모드 되먹임이 게이트를 구동하는 tail 소자와 측면 주입 후보는 '바이어스 "
              "전류원'이어야 한다.",
              ""]
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
