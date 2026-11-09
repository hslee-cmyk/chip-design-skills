"""plan v6.38.4 P2 재계수(검증 1 C-1·m-6) -- 결정자 정의: R의 커패시터 쪽 노드 n(단일 가지 = R의 능동 끝 A, T 망 = 공통 노드 CM)에서
B(출력)를 AC 접지한 전체 용량망의 s → ∞ 전압비. 'S 정확형'(R_null = 1/Σ_S gm) 구조 조건 = 단일 직렬 가지 ∧ S 셀 source = 교류 접지 ∧
n과 S 밖 출력 소자(drain = B)의 gate·source 사이 용량 경로 없음(선언 C·MOS 단자 쌍). 회로 이름 조건 없음. 출력 cond3.out.jsonl"""
import json, os, glob
LIB = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6384/skills/analog-gmid-design/assets/library"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cond3.out.jsonl")
rows = []
for f in sorted(glob.glob(os.path.join(LIB, "*.topology.json"))):
    if os.path.basename(f).startswith("_"): continue
    t = json.load(open(f, encoding="utf-8")); name = os.path.basename(f)[:-len(".topology.json")]
    acg = set(t.get("supply_nets") or []) | set(t.get("bias_inputs") or []) | {k for k, v in (t.get("ports") or {}).items() if not k.startswith("_") and v.get("direction") == "input"}
    pes = t.get("passive_elements", []); mos = t["netlist"]
    touch = {}
    for p in pes:
        for n in p["terminals"]: touch.setdefault(n, []).append(("P", p))
    for d in mos:
        for k in ("gate", "drain", "source"): touch.setdefault(d[k], []).append(("M", d))
    nets = []
    for r in (p for p in pes if p["kind"] == "resistor"):
        for i, mid in enumerate(r["terminals"]):
            other = r["terminals"][1 - i]; at = touch.get(mid, [])
            caps = [p for kind, p in at if kind == "P" and p is not r and p["kind"] == "capacitor"]
            if not caps or len(caps) + 1 != len(at): continue
            ends = [[n for n in c["terminals"] if n != mid][0] for c in caps]
            # 경로마다 (구동 끝, 출력 끝) = (gate 끝, drain 끝)인 S 셀
            paths = []
            for e in ends:
                for a, b in ((other, e), (e, other)):
                    S = [d["name"] for d in mos if d["gate"] == a and d["drain"] == b]
                    if S: paths.append({"A": a, "B": b, "S": S, "S_source_acgnd": all(d["source"] in acg for d in mos if d["name"] in S)})
            single = len(caps) == 1
            n = (paths[0]["A"] if paths else other) if single else mid
            coup = []
            for pth in paths:
                for d in mos:
                    if d["drain"] != pth["B"] or d["name"] in pth["S"]: continue
                    for term in ("gate", "source"):
                        g = d[term]
                        if g in acg: continue
                        if any(set(c["terminals"]) == {n, g} for c in (p for p in pes if p["kind"] == "capacitor")) or \
                           any(n in (m["gate"], m["drain"], m["source"]) and g in (m["gate"], m["drain"], m["source"]) and m["name"] != d["name"] for m in mos):
                            coup.append([d["name"], term, g])
            exact = single and bool(paths) and all(p["S_source_acgnd"] for p in paths) and not coup
            nets.append({"R": r["name"], "C": [c["name"] for c in caps], "single_branch": single, "n": n, "paths": paths, "coupling_to_other_output_devices": coup, "S_exact_form": exact})
    rows.append({"circuit": name, "zero_cancel": nets})
with open(OUT, "w", encoding="utf-8") as fh:
    for r in rows: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
withR = [r for r in rows if r["zero_cancel"]]
print("영점 상쇄 R 있는 회로", len(withR), "/ 9; 경로", sum(len(r["zero_cancel"]) for r in withR), "; S 정확형", sum(z["S_exact_form"] for r in withR for z in r["zero_cancel"]))
for r in withR:
    for z in r["zero_cancel"]: print(r["circuit"], z["R"], z["C"], "single" if z["single_branch"] else "T", "n=", z["n"], [(p["A"], p["B"], p["S"]) for p in z["paths"]], "coup", z["coupling_to_other_output_devices"], "exact", z["S_exact_form"])
