# -*- coding: utf-8 -*-
"""규칙 1 (4) '바이어스 종속 넷' 술어를 library 8회로 전수로 돌려 발동·무동작을 잰다.

계획 N3.2-1 (4)의 술어를 그대로 옮긴다(고유명사 없이 구조만 본다):
  (0)   b가 그 뷰에서 신호 넷으로 잡힌다(이미 신호 경로 밖이면 적용하지 않는다)
  (i)   b에서 신호가 나가는 단자가 gate뿐이다(b를 source로 쓰는 소자도, b에 붙은 2단자 수동소자도 없다)
  (ii)  b를 구동하는 채널 단자(= drain == b인 소자)가 모두
        - b를 gate로 읽는 소자이거나
        - gate가 그 뷰의 신호 경로 밖인 소자(바이어스 전류원)
        이고, 앞 부류가 하나 이상 있다
  (iii) 앞 부류 소자 중 하나가 **채널 단자만 거쳐** 그 뷰의 신호 노드에서 출발하는 사슬에 속하고,
        그 출발 노드는 **b를 뺀 그래프에서도 신호 넷**이다(b가 만든 신호를 근거로 b를 바이어스라고
        판정하는 순환을 막는다 -- 전류 미러 부하의 diode 노드가 이 조건에서 걸러진다)

일반성은 주장이 아니라 측정이다 -- 고르는 회로와 **고르지 않는 회로(무동작)** 를 함께 낸다.
결과는 stdout이 아니라 같은 이름 `.txt`에 append한다(세션 규칙).
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LIB = os.path.join(ROOT, "skills", "analog-gmid-design", "assets", "library")
OUT = os.path.splitext(os.path.abspath(__file__))[0] + ".txt"
NAMESET = {"vdd", "vss", "gnd", "vdd!", "gnd!"}


def rails_of(d, mos, pas):
    if d.get("supply_nets"):
        return set(d["supply_nets"])
    nets = {m[k] for m in mos for k in ("drain", "gate", "source")}
    for e in pas:
        nets |= set(e.get("terminals") or [])
    return {n for n in nets if n in NAMESET}


def ac_ground(d, mos, pas, rails, extra):
    driven = set()
    for m in mos:
        driven |= {m["drain"], m["source"]}
    for e in pas:
        driven |= set(e.get("terminals") or [])
    ports = set((d.get("ports") or {}).keys())
    gate_only = {m["gate"] for m in mos} - driven - ports
    return rails | gate_only | set(extra)


def excitation(d):
    """기본 전달 뷰: input 역할 포트 전부."""
    return [n for n, p in (d.get("ports") or {}).items()
            if isinstance(p, dict) and p.get("direction") == "input"]


def signal_nets(mos, pas, excite, acg):
    sig = {n for n in excite if n not in acg}
    changed = True
    while changed:
        changed = False
        for m in mos:
            add = set()
            if m["gate"] in sig:
                add |= {m["drain"], m["source"]}
            if m["source"] in sig:
                add.add(m["drain"])
            for n in add:
                if n not in acg and n not in sig:
                    sig.add(n)
                    changed = True
        for e in pas:
            t = e.get("terminals") or []
            if len(t) == 2:
                for a, b in ((t[0], t[1]), (t[1], t[0])):
                    if a in sig and b not in acg and b not in sig:
                        sig.add(b)
                        changed = True
    return sig


def chain_reaches_signal(mos, dev, sig, acg):
    """(iii): dev에서 채널 단자만 거슬러 올라가 신호 노드에 닿는가."""
    seen, stack = set(), [dev["source"]]
    while stack:
        n = stack.pop()
        if n in seen or n in acg:
            continue
        seen.add(n)
        if n in sig:
            return True, n
        for m in mos:                     # n을 drain으로 갖는 소자의 source로 거슬러 간다
            if m["drain"] == n:
                stack.append(m["source"])
    return False, None


def candidates(d, mos, pas, acg, sig, excite):
    out = []
    passive_nets = set()
    for e in pas:
        passive_nets |= set(e.get("terminals") or [])
    for b in sorted({m["gate"] for m in mos}):
        if b in acg:
            continue
        # (0) 그 뷰에서 신호 넷으로 잡히는 넷만 대상이다(이미 신호 경로 밖이면 규칙이 바꿀 것이 없다)
        if b not in sig:
            continue
        # (i) 나가는 단자가 gate뿐
        if any(m["source"] == b for m in mos) or b in passive_nets:
            continue
        drivers = [m for m in mos if m["drain"] == b]
        if not drivers:
            continue
        self_gated = [m for m in drivers if m["gate"] == b]
        if not self_gated:
            continue
        # (ii) 나머지 구동 소자는 gate가 신호 경로 밖이어야 한다
        ok = all((m["gate"] == b) or (m["gate"] not in sig) for m in drivers)
        if not ok:
            continue
        # (iii) 자기게이트 소자 중 하나가 채널만 거쳐 신호 노드에서 출발하되,
        #       그 출발 노드는 b를 뺀 그래프에서도 신호 넷이어야 한다(순환 차단)
        sig_wo_b = signal_nets(mos, pas, excite, acg | {b})
        for m in self_gated + [x for x in mos if x["gate"] == b and x["drain"] != b]:
            hit, start = chain_reaches_signal(mos, m, sig, acg)
            if hit and start in sig_wo_b:
                out.append((b, m["name"], start, sorted(x["name"] for x in drivers)))
                break
    return out


def main():
    lines = ["=== 규칙 1 (4) 바이어스 종속 넷 술어 -- library 8회로 전수 측정 ===",
             "기본 전달 뷰(입력 포트 여기) 기준. ports 미선언 회로는 여기를 만들 수 없어 '측정 불가'.",
             ""]
    fired = nofire = skipped = 0
    for fn in sorted(os.listdir(LIB)):
        if not fn.endswith(".topology.json") or fn.startswith("_TEMPLATE"):
            continue
        d = json.load(io.open(os.path.join(LIB, fn), encoding="utf-8"))
        name = str(d.get("topology_name"))
        mos = [m for m in d["netlist"] if isinstance(m, dict)]
        pas = [e for e in (d.get("passive_elements") or []) if isinstance(e, dict)]
        ex = excitation(d)
        if not ex:
            lines.append(f"  {name:30s} 측정 불가(입력 포트 미선언, U-08)")
            skipped += 1
            continue
        rails = rails_of(d, mos, pas)
        acg = ac_ground(d, mos, pas, rails, set())
        sig = signal_nets(mos, pas, ex, acg)
        cands = candidates(d, mos, pas, acg, sig, ex)
        if cands:
            fired += 1
            lines.append(f"  {name:30s} **발동 {len(cands)}건**")
            for b, dev, start, drivers in cands:
                lines.append(f"      넷 {b}: 자기게이트 구동 {dev}, 사슬 출발 신호 노드 {start}, "
                             f"구동 소자 {drivers}")
        else:
            nofire += 1
            lines.append(f"  {name:30s} 무동작 0건")
    lines += ["",
              f"요약: 발동 {fired}회로 / 무동작 {nofire}회로 / 측정 불가 {skipped}회로",
              "무동작이 다수인 것이 일반성의 증거다 -- 술어가 필요 없는 회로에서는 아무 것도 바꾸지 않는다.",
              ""]
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
