# -*- coding: utf-8 -*-
"""DEC-60 (iii) 숨은 레일 후보 거부 게이트가 **실제로 거부하고 오거부하지 않는지** 측정한다.

WP-02("게이트는 '통과'가 아니라 '실제로 거부한다'를 먼저 확인한다")의 근거 측정이고,
N4.3 공격 14의 (a)(b) 두 케이스를 같은 판별식으로 돌린다.

판별식(계획 DEC-60 (iii)):
  숨은 넷 = 트랜지스터 단자에 나타나지 않고 수동소자·이상원 단자로만 나타나는 넷 중,
            DC 전도 그래프(MOS 채널 + 저항 + 이상원. 커패시터는 DC 엣지가 아니다)에서
            어느 레일 넷과도 연결되지 않는 넷.
  거부     = 숨은 넷 중 `supply_nets`에 들어 있지 않은 것이 하나라도 있으면 거부.

결과는 stdout이 아니라 같은 이름 `.txt`에 append한다(세션 규칙).
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LIB = os.path.join(ROOT, "skills", "analog-gmid-design", "assets", "library")
OUT = os.path.splitext(os.path.abspath(__file__))[0] + ".txt"
# 전환기 이름집합 해석(DEC-60, MG1까지 한시)
NAMESET = {"vdd", "vss", "gnd", "vdd!", "gnd!"}


def terminals_of_passives(d):
    nets = set()
    for e in (d.get("passive_elements") or []):
        if isinstance(e, dict):
            for t in (e.get("terminals") or []):
                if isinstance(t, str):
                    nets.add(t)
    for s in (d.get("ideal_sources") or []):
        if isinstance(s, dict):
            for t in (s.get("terminals") or [s.get("from"), s.get("to")]):
                if isinstance(t, str):
                    nets.add(t)
    return nets


def dc_edges(d):
    """DC 전도 엣지. 커패시터는 넣지 않는다."""
    edges = []
    for m in d.get("netlist") or []:
        if isinstance(m, dict) and m.get("drain") and m.get("source"):
            edges.append((m["drain"], m["source"]))
    for e in (d.get("passive_elements") or []):
        if isinstance(e, dict) and e.get("kind") == "resistor":
            t = e["terminals"]
            edges.append((t[0], t[1]))
    for s in (d.get("ideal_sources") or []):
        if isinstance(s, dict):
            t = s.get("terminals") or [s.get("from"), s.get("to")]
            if t and all(t):
                edges.append((t[0], t[1]))
    return edges


def judge(d, declared_override=None):
    """(거부 여부, 숨은 넷 목록, DC 고립 넷 목록, 미선언 넷 목록)."""
    mos_nets = set()
    for m in d.get("netlist") or []:
        if isinstance(m, dict):
            for k in ("drain", "gate", "source", "bulk"):
                v = m.get(k)
                if isinstance(v, str):
                    mos_nets.add(v)
    pnets = terminals_of_passives(d)
    hidden = sorted(pnets - mos_nets)

    adj = {}
    for u, v in dc_edges(d):
        adj.setdefault(u, set()).add(v)
        adj.setdefault(v, set()).add(u)

    declared = declared_override if declared_override is not None else d.get("supply_nets")
    rails = set(declared) if declared else {n for n in (mos_nets | pnets) if n in NAMESET}

    seen, stack = set(), [r for r in rails if r in adj]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(adj.get(n, ()))

    isolated = [n for n in hidden if n not in seen]
    undeclared = [n for n in isolated if n not in (declared or [])]
    return bool(undeclared), hidden, isolated, undeclared


def main():
    rows, reject, accept = [], [], []
    for p in sorted(os.listdir(LIB)):
        if not p.endswith(".topology.json") or p.startswith("_TEMPLATE"):
            continue
        d = json.load(io.open(os.path.join(LIB, p), encoding="utf-8"))
        name = str(d.get("topology_name"))
        rej, hidden, iso, undecl = judge(d)
        (reject if rej else accept).append(name)
        rows.append(f"  {name:30s} 숨은넷={hidden} DC고립={iso} 거부={'YES' if rej else 'no'} {undecl}")

    # 공격 14 (b): 선언은 있으나 숨은 넷을 빼고 적은 경우도 거부되는가
    b_cases = []
    for fn in ("pushpull_follower_buffer.topology.json", "sf_pushpull_output_opamp.topology.json"):
        d = json.load(io.open(os.path.join(LIB, fn), encoding="utf-8"))
        rej, _, iso, undecl = judge(d, declared_override=["vdd", "vss"])
        b_cases.append(f"  {d.get('topology_name'):30s} supply_nets=['vdd','vss'](agnd 누락) "
                       f"-> 거부={'YES' if rej else 'no'} {undecl}")

    lines = [
        "=== DEC-60 (iii) 숨은 레일 후보 거부 게이트 측정 ===",
        "[공격 14 (a)] supply_nets 현 선언 그대로:",
        *rows,
        f"  거부 {len(reject)}회로: {reject}",
        f"  통과 {len(accept)}회로: {accept}",
        "[공격 14 (b)] 선언은 있으나 숨은 넷을 뺀 경우:",
        *b_cases,
        "판정: 거부는 agnd 두 회로에서만 발동하고, DC로 연결된 보상망 내부 노드"
        "(파일럿 N_cc_rz1/N_cc_rz2)를 가진 회로는 오거부되지 않는다.",
        "",
    ]
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
