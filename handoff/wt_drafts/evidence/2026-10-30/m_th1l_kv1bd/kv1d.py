# M-KV1d: B = ∅ follower 고리 2개에서 DEC-95 (3) ② 술어가 종속 멤버를 유일하게 정하는지 + 소스 사슬 하류·정준 라벨 적용.
# 연결만(topology.json netlist, 태그 미사용). 엔진 import 없음.
# ② 술어(계획 DEC-64 263행 ② 문언 "GB5가 gm을 요구하는 소자·뒤 stage 소자는 독립으로 남긴다")를 연결로 읽는 두 방법:
#   (R-a) 'GB5 gm 요구' = 신호 경로 셀(gate 가 신호 넷 = 입력 포트에서 MOS gate->source/drain 로 닿는 넷)인 멤버 전부
#   (R-b) '뒤 stage' = 고리 안에서 출력 포트 넷을 source/drain 으로 가진 멤버(출력 쪽 stage)
# 소스 사슬 하류: 고리가 레일을 지나지 않으면, 고리 안 '고정 넷'(입력 포트 -- DEC-64 v1 '외부 원이 DC를 고정하는 넷')을 기준으로 P(Y) 를 만든다. 없으면 정의 불가.
# 정준 라벨: 1-WL 색 정제(kind, 단자 역할) -- DEC-97 의 완전 정준 라벨이 아니라 그 첫 단계(구조 동치 판정용). 동치류가 다르면 '결정적으로 갈림'.
import json, pathlib, collections
LIB = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library")
OUT = pathlib.Path(__file__).with_name("kv1d.jsonl")
CASES = {"pushpull_follower_buffer": ["M1", "M2", "M3", "M4"], "sf_pushpull_output_opamp": ["M18", "M19", "M21", "M22"]}


def signal_nets(t, mos):
    ins = {k for k, v in t["ports"].items() if isinstance(v, dict) and v.get("direction") == "input"}
    rails = set(t["supply_nets"])
    sig, frontier = set(ins), list(ins)
    while frontier:
        n = frontier.pop()
        for d in mos:
            if d["gate"] == n:
                for x in (d["drain"], d["source"]):
                    if x not in rails and x not in sig:
                        sig.add(x); frontier.append(x)
    return sig


def wl_colors(mos, rails, rounds=4):
    col = {d["name"]: d["kind"] for d in mos}
    nets = {}
    for _ in range(rounds):
        ncol = collections.defaultdict(list)
        for d in mos:
            for role in ("drain", "gate", "source"):
                n = d[role]
                ncol["RAIL" if n in rails else n].append((role, col[d["name"]]))
        nets = {n: tuple(sorted(v)) for n, v in ncol.items()}
        col = {d["name"]: (d["kind"], tuple(("RAIL" if d[r] in rails else nets[d[r]]) for r in ("drain", "gate", "source"))) for d in mos}
        col = {k: str(hash(v)) for k, v in col.items()}
    return col


def main():
    if OUT.exists():
        OUT.unlink()
    for c, members in CASES.items():
        t = json.loads((LIB / f"{c}.topology.json").read_text(encoding="utf-8"))
        rails = set(t["supply_nets"])
        mos = [d for d in t["netlist"] if d.get("kind") in ("nmos", "pmos")]
        M = {d["name"]: d for d in mos}
        ins = {k for k, v in t["ports"].items() if isinstance(v, dict) and v.get("direction") == "input"}
        outs = {k for k, v in t["ports"].items() if isinstance(v, dict) and v.get("direction") == "output"}
        sig = signal_nets(t, mos)
        Ra = [m for m in members if M[m]["gate"] in sig]
        Rb = [m for m in members if M[m]["source"] in outs or M[m]["drain"] in outs]
        left_a = [m for m in members if m not in Ra]
        left_b = [m for m in members if m not in Rb]
        # 고리 노드 순서(gate-source 엣지)
        adj = collections.defaultdict(list)
        for m in members:
            adj[M[m]["gate"]].append((m, M[m]["source"])); adj[M[m]["source"]].append((m, M[m]["gate"]))
        start = M[members[0]]["gate"]; order = [start]; used = []; cur = start
        while True:
            nxt = [(m, n) for m, n in adj[cur] if m not in used]
            if not nxt:
                break
            m, n = nxt[0]; used.append(m)
            if n == start:
                break
            order.append(n); cur = n
        fixed = [n for n in order if n in rails or n in ins]
        P = {}
        if fixed:
            F = fixed[0]
            k = len(order)
            edges = []
            for i in range(k):
                a, b = order[i], order[(i + 1) % k]
                m = [x for x in members if {M[x]["gate"], M[x]["source"]} == {a, b}][0]
                edges.append(m)
            for i, m in enumerate(edges):
                s = M[m]["source"]
                if s == F:
                    P[m] = []; continue
                path_nodes = [order[(i + 1 + j) % k] for j in range(k)]
                path_edges = [edges[(i + 1 + j) % k] for j in range(k - 1)]
                a, b = path_nodes.index(F), path_nodes.index(s)
                lo, hi = min(a, b), max(a, b)
                P[m] = path_edges[lo:hi]
        down_b = [m for m in left_b if fixed and all(m not in P[y] for y in members if y != m)]
        col = wl_colors(mos, rails)
        rec = dict(circuit=c, loop_nodes=order, fixed_nodes=fixed, signal_nets_in_loop=[n for n in order if n in sig],
                   Ra_independent=Ra, Ra_left=left_a, Rb_independent=Rb, Rb_left=left_b,
                   P=P, downstream_among_Rb_left=down_b,
                   wl_colour_classes={m: col[m] for m in left_b}, left_b_struct_equiv=len({col[m] for m in left_b}) == 1 if left_b else None,
                   bulk=[M[m].get("bulk") for m in members])
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(json.dumps(rec, ensure_ascii=False))


if __name__ == "__main__":
    main()
