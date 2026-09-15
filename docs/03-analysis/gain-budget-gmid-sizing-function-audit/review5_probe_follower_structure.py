# -*- coding: utf-8 -*-
"""검토용 측정(저장소 수정 없음): library 회로 7개에서
(1) 순수 follower 셀(drain이 레일, gate가 신호 후보 넷) 목록
(2) gate-source(VGS) 엣지만으로 닫힌 DC KVL 사이클(레일은 한 고정 노드로 병합, 포트는 병합 안 함)
    - 같은 (gate넷, source넷) 쌍의 평행 엣지는 equal_vgs(자명)로 분리
(3) 출력 포트 노드별 방향(공급/흡수) 전류 경로 셀 분류: bias(gate가 gate 전용 넷) / signal
결과는 파일에 케이스마다 append.
"""
import json, glob, os, sys

LIB = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe_follower_structure.result.md")
RAILS = {"vdd", "VDD", "gnd", "GND", "vss", "VSS"}  # 넷 이름 집합(DEC-60 전환기 해석과 같음) -- 측정용

open(OUT, "w", encoding="utf-8").write("# probe_follower_structure 결과\n\n")

def w(s):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

class UF:
    def __init__(self): self.p = {}
    def f(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def u(self, a, b):
        ra, rb = self.f(a), self.f(b)
        if ra == rb: return False
        self.p[ra] = rb; return True

for path in sorted(glob.glob(os.path.join(LIB, "*.topology.json"))):
    name = os.path.basename(path).replace(".topology.json", "")
    if name.startswith("_"):
        continue
    t = json.load(open(path, encoding="utf-8"))
    net = [d for d in t.get("netlist", []) if d.get("kind") in ("nmos", "pmos")]
    ports = set((t.get("ports") or {}).keys())
    pas_nets = set()
    for p in t.get("passive_elements") or []:
        pas_nets.update(p.get("terminals") or [])
    for s in t.get("ideal_sources") or []:
        pas_nets.update(s.get("terminals") or [])
    # 넷별 단자
    term = {}
    for d in net:
        for k in ("drain", "gate", "source"):
            term.setdefault(d[k], []).append((d["name"], k))
    gate_only = {n for n, ts in term.items()
                 if all(k == "gate" for _, k in ts) and n not in ports and n not in pas_nets and n not in RAILS}
    w(f"## {name}\n")
    w(f"- 소자 {len(net)}, gate 전용 넷(교류접지 후보 SP1-1(2)): {sorted(gate_only)}")
    # (1) follower 셀
    fol = [d for d in net if d["drain"] in RAILS and d["source"] not in RAILS
           and d["gate"] not in gate_only and d["gate"] not in RAILS and d["gate"] != d["drain"]]
    w("- drain=레일·source≠레일·gate=신호 후보(순수 follower 후보): " +
      (", ".join(f"{d['name']}({d['kind']} g={d['gate']} s={d['source']} d={d['drain']})" for d in fol) or "없음"))
    # source가 레일이 아니고 drain도 레일이 아닌데 source 노드가 다른 소자 gate로 이어지는 소자(비순수 CD 후보)
    src_to_gate = [d for d in net if d["source"] not in RAILS and d["drain"] not in RAILS
                   and any(k == "gate" for _, k in term.get(d["source"], []))
                   and d["gate"] not in gate_only]
    w("- source 노드가 다른 소자 gate로 이어지고 drain·source 모두 비레일(비순수 CD/pass 후보): " +
      (", ".join(f"{d['name']}(g={d['gate']} s={d['source']} d={d['drain']})" for d in src_to_gate) or "없음"))
    # (2) VGS 사이클
    uf = UF(); seen_pairs = {}; trivial = []; nontriv = []
    norm = lambda n: "RAIL" if n in RAILS else n
    for d in net:
        g, s = norm(d["gate"]), norm(d["source"])
        if g == s:
            continue
        key = frozenset((g, s))
        if key in seen_pairs:
            trivial.append((d["name"], seen_pairs[key]))
            continue
        seen_pairs[key] = d["name"]
        if not uf.u(g, s):
            nontriv.append(d)
    w(f"- equal_vgs 자명 평행 엣지 {len(trivial)}건: " + ", ".join(f"{a}~{b}" for a, b in trivial))
    if nontriv:
        # 사이클 멤버 복원: 트리 경로 탐색
        adj = {}
        tree_edges = [d for d in net if frozenset((norm(d['gate']), norm(d['source']))) in seen_pairs
                      and seen_pairs[frozenset((norm(d['gate']), norm(d['source'])))] == d['name'] and d not in nontriv
                      and norm(d['gate']) != norm(d['source'])]
        for d in tree_edges:
            a, b = norm(d["gate"]), norm(d["source"])
            adj.setdefault(a, []).append((b, d["name"])); adj.setdefault(b, []).append((a, d["name"]))
        def path(a, b):
            st = [(a, [])]; vis = {a}
            while st:
                x, pth = st.pop()
                if x == b: return pth
                for y, dn in adj.get(x, []):
                    if y not in vis:
                        vis.add(y); st.append((y, pth + [(dn, x, y)]))
            return None
        for d in nontriv:
            a, b = norm(d["gate"]), norm(d["source"])
            p = path(b, a)
            members = [d["name"]] + [x[0] for x in (p or [])]
            nodes = [a, b] + [x[2] for x in (p or [])]
            w(f"- **비자명 VGS 사이클**: 소자 {members}, 노드 {sorted(set(nodes))}, 레일 경유={'RAIL' in nodes}")
    else:
        w("- 비자명 VGS 사이클: 없음")
    # (3) 출력 포트 노드 방향 분류
    for p, meta in (t.get("ports") or {}).items():
        if not isinstance(meta, dict):
            w(f"- (ports `{p}` 값이 dict가 아님: {meta!r} -- 옛 스키마, 방향 분류 생략)")
            continue
        if meta.get("direction") != "output":
            continue
        cells = [(dn, k) for dn, k in term.get(p, []) if k in ("drain", "source")]
        rows = []
        for dn, k in cells:
            d = next(x for x in net if x["name"] == dn)
            other = d["source"] if k == "drain" else d["drain"]
            gk = "bias(gate 전용 넷)" if d["gate"] in gate_only else ("rail-gate" if d["gate"] in RAILS else "signal")
            rows.append(f"{dn}[{d['kind']}, 단자={k}, 반대단자={other}, gate={d['gate']}:{gk}]")
        w(f"- 출력 포트 `{p}` drain/source 소자: " + "; ".join(rows))
    w("")

# LUT 축 확인(가능하면)
try:
    import numpy as np
    root = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
    cands = [f for f in glob.glob(os.path.join(root, "**", "*.npz"), recursive=True)
             if "ac_sweep_checkpoints" not in f]
    w("## LUT npz(ac_sweep_checkpoints 제외)\n")
    for f in cands[:12]:
        try:
            z = np.load(f, allow_pickle=True)
            keys = list(z.keys())
            info = []
            for k in keys:
                a = z[k]
                if a.ndim == 1 and a.size < 200 and a.dtype.kind == "f":
                    info.append(f"{k}[{a.min():.3g}..{a.max():.3g}, n={a.size}]")
                else:
                    info.append(f"{k}{tuple(a.shape)}")
            w(f"- `{os.path.relpath(f, root)}`: " + ", ".join(info))
        except Exception as e:
            w(f"- `{f}`: 로드 실패 {e!r}")
except Exception as e:
    w(f"## LUT 확인 생략: {e!r}")
print("done ->", OUT)
