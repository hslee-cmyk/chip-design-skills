# 13회로 kvl_branch 고리에서 권고 (가) '소스 사슬 하류' 규칙이 종속 소자를 유일하게 정하는지 -- 연결만(엔진 import 없음).
# G_vgs: MOS 마다 gate 넷 -- source 넷 무향 엣지, supply_nets 를 고정 노드 F 하나로 병합(계획 92행 정의).
#   평행 엣지(같은 {gate, source}) = equal_vgs 묶음 -> 한 엣지 부류로 접는다.
#   고리 = 접은 단순 그래프의 단순 사이클 전수(networkx simple_cycles). 입력 포트 넷을 지나는 고리 = port_diff 로 제외.
# B(θ 층 근사, 계획 91행 DC 역할 절차를 연결로): (1) gate==drain -> diode (2) {gate, source} 를 diode 와 공유하거나
#   gate 가 bias_inputs/레일이면 바이어스 전류원 (3) gate 가 bias_inputs/레일이고 source 가 레일이면 바이어스 전류원.
#   (AC 접지 판정은 bias_inputs + supply 로 근사 -- 엔진 S1v 셀 분류와 다를 수 있음, 표지.)
# 규칙 (가): 고리에서 부류 Y 의 source 가 비레일이고 결합(몸체≠source 이거나 diode 아님 -> VSB 또는 VDS 가 source 전압을 읽음)이면
#   P(Y) = 고리에서 Y 엣지를 뺀 경로 위 F -> source_Y 사이 부류들. 후보 D 는 어느 Y 의 P(Y) 에도 없을 때 '하류'(닫힌 꼴 풀이 가능).
# 순위: diode 후보(있으면) -> [궤도 대표: 자기동형 미계산, 아래 '구조 동치' 로 근사] -> 규칙 (가) -> 남으면 tie.
import json, pathlib, itertools
import networkx as nx

SK = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library")
OUT = pathlib.Path(__file__).with_name("loops13_v2.jsonl")   # v1 판 loops13.jsonl 보존
F = "<F>"


def run():
    if OUT.exists():
        OUT.unlink()
    for p in sorted(SK.glob("*.topology.json")):
        if p.name.startswith("_"):
            continue
        t = json.loads(p.read_text(encoding="utf-8"))
        rails = set(t.get("supply_nets") or [])
        ports = t.get("ports") or {}
        inputs = {k for k, v in ports.items() if isinstance(v, dict) and v.get("direction") == "input"}
        bias = set()
        bi = t.get("bias_inputs") or {}
        if isinstance(bi, dict):
            bias = {k for k in bi if not k.startswith("_")}
        elif isinstance(bi, list):
            bias = {x if isinstance(x, str) else x.get("net") for x in bi}
        mos = [d for d in t["netlist"] if d.get("kind") in ("nmos", "pmos")]
        nd = lambda n: F if n in rails else n
        diode = {d["name"] for d in mos if d["gate"] == d["drain"]}
        fixed = rails | bias
        role = {}
        for d in mos:
            if d["name"] in diode:
                role[d["name"]] = "diode"
        for d in mos:
            if d["name"] in role:
                continue
            share = any(e["name"] in diode and e["gate"] == d["gate"] and nd(e["source"]) == nd(d["source"]) for e in mos)
            if share or (d["gate"] in fixed):
                role[d["name"]] = "bias"
            else:
                role[d["name"]] = "signal"
        cls = {}
        for d in mos:
            u, v = nd(d["gate"]), nd(d["source"])
            if u == v:
                continue
            cls.setdefault(frozenset((u, v)), []).append(d)
        G = nx.Graph()
        for k in cls:
            u, v = tuple(k)
            G.add_edge(u, v)
        recs = []
        for cyc in nx.simple_cycles(G):
            if len(cyc) < 3:
                continue
            nodes = list(cyc)
            if sum(n in inputs for n in nodes) >= 2:      # DEC-64 (v1): 입력 포트 넷을 둘 이상 지나는 사이클(2026-10-30 3차 정정: 옛 '하나라도')
                kind = "port_diff"
            else:
                kind = "kvl_branch"
            edges = [frozenset((nodes[i], nodes[(i + 1) % len(nodes)])) for i in range(len(nodes))]
            members = [sorted(x["name"] for x in cls[e]) for e in edges]
            rec = dict(circuit=p.name.replace(".topology.json", ""), kind=kind, nodes=nodes, members=members,
                       through_F=F in nodes)
            if kind == "kvl_branch":
                rec.update(analyse(nodes, edges, cls, role, rails, nd))
            recs.append(rec)
        with open(OUT, "a", encoding="utf-8") as fh:
            for r in recs:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.write(json.dumps(dict(circuit=p.name.replace(".topology.json", ""), summary=True, n_mos=len(mos),
                                     n_kvl=sum(r["kind"] == "kvl_branch" for r in recs),
                                     n_port=sum(r["kind"] == "port_diff" for r in recs)), ensure_ascii=False) + "\n")


def analyse(nodes, edges, cls, role, rails, nd):
    n = len(nodes)
    # 부류 대표 정보
    info = []
    for i, e in enumerate(edges):
        devs = cls[e]
        r = sorted({role[d["name"]] for d in devs})
        src = {nd(d["source"]) for d in devs}
        assert len(src) == 1
        s = src.pop()
        isdiode = all(d["gate"] == d["drain"] for d in devs)
        bulk_eq_src = all((d.get("bulk") or d.get("body")) == d["source"] for d in devs)
        coupled = s != F and not (isdiode and bulk_eq_src)
        info.append(dict(idx=i, devs=sorted(d["name"] for d in devs), roles=r, src=s, diode=isdiode, coupled=coupled,
                         bulk_decl=sorted({str(d.get("bulk") or d.get("body")) for d in devs})))
    # P(Y): 고리에서 엣지 i 를 빼면 경로 nodes[i+1] ... nodes[i] (엣지 i 는 nodes[i]-nodes[i+1]).
    def upstream(i):
        s = info[i]["src"]
        if s == F or F not in nodes:
            # F 를 안 지나는 고리: 기준 전압이 고리 밖 -> 경로 정의 불가, 빈 집합(표지)
            return set()
        path_nodes = [nodes[(i + 1 + k) % n] for k in range(n)]          # nodes[i+1] ... nodes[i]
        path_edges = [(i + 1 + k) % n for k in range(n - 1)]             # 엣지 i+1 ... i-1
        a, b = path_nodes.index(F), path_nodes.index(s)
        lo, hi = min(a, b), max(a, b)
        return {path_edges[k] for k in range(lo, hi)}
    P = {i: (upstream(i) if info[i]["coupled"] else set()) for i in range(n)}
    B = [i for i in range(n) if any(x in ("diode", "bias") for x in info[i]["roles"])]
    cand = [i for i in B if info[i]["diode"]] or B
    down = [i for i in cand if all(i not in P[j] for j in range(n) if j != i)]
    name_pick = min(cand, key=lambda i: info[i]["devs"][0]) if cand else None
    # 남은 tie 의 구조 동치(같은 kind·diode·coupled·소스 레일 여부·P 크기) -- 궤도 근사
    sig = lambda i: (info[i]["diode"], info[i]["coupled"], info[i]["src"] == F, len(P[i]), tuple(info[i]["roles"]))
    return dict(info=info, P={str(k): sorted(v) for k, v in P.items()}, B=B, cand=cand, rule_ga=down,
                unique=len(down) == 1, empty=len(down) == 0,
                tie_struct_equiv=(len(down) > 1 and len({sig(i) for i in down}) == 1),
                name_pick=None if name_pick is None else info[name_pick]["devs"],
                ga_pick=[info[i]["devs"] for i in down])


if __name__ == "__main__":
    run()
