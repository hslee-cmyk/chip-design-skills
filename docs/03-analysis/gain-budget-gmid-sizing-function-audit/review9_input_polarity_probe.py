# -*- coding: utf-8 -*-
"""`ports` 기입 전에 입력 극성을 독립 소신호 해석으로 확인한다(넷 이름을 믿지 않는다).

배경: 이 프로젝트에서 `two_stage_ota`의 `vin_p`/`vin_n` 라벨이 실제 극성과 어긋나 있던 적이 있다.
그래서 `differential_input_p`/`_n`을 붙이기 전에 **어느 입력이 출력과 동상인지**를 직접 푼다.

방법: 모든 소자에 같은 단위 소신호 파라미터(gm, gds)를 주고 노달 해석만 한다. 절대값은 의미가
없고 **부호만** 본다. 소신호 모델은 nmos/pmos가 같다(극성 차이는 DC 동작점이 흡수한다):
    i(d->s) = gm*(vg - vs) + gds*(vd - vs)
교류접지 = 레일 + gate에만 붙고 구동되지 않는 넷(바이어스). 한 입력만 여기하고 나머지는 접지한다.

결과는 stdout이 아니라 같은 이름 `.txt`에 append한다(세션 규칙).
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LIB = os.path.join(ROOT, "skills", "analog-gmid-design", "assets", "library")
OUT = os.path.splitext(os.path.abspath(__file__))[0] + ".txt"
NAMESET = {"vdd", "vss", "gnd", "vdd!", "gnd!"}
GM, GDS = 1e-3, 1e-5

CASES = [
    # (파일, 입력 넷 둘, 출력 넷)
    ("folded_cascode", ("vin_p", "vin_n"), "out"),
    ("nmcnr_amplifier", ("Vin_n", "Vin_p"), "Vout"),
    ("two_stage_ota", ("vin_p", "vin_n"), "OUT"),          # 이미 정정된 회로 -- 대조군
]


def solve(mos, acg, nodes, excite_net):
    """단순 노달 해석. excite_net을 1 V로 고정하고 나머지 자유 노드를 푼다."""
    idx = {n: i for i, n in enumerate(nodes)}
    k = len(nodes)
    A = [[0.0] * k for _ in range(k)]
    b = [0.0] * k

    def volt(net):
        """고정 넷이면 (계수 없음, 값), 자유 넷이면 (인덱스, 0)."""
        if net == excite_net:
            return None, 1.0
        if net in acg:
            return None, 0.0
        return idx[net], 0.0

    for m in mos:
        for term, sgn in ((m["drain"], +1.0), (m["source"], -1.0)):
            ti, _ = volt(term)
            if ti is None:
                continue                      # 고정 노드의 KCL 행은 세우지 않는다
            for src, coef in ((m["gate"], GM), (m["drain"], GDS), (m["source"], -(GM + GDS))):
                si, sv = volt(src)
                if si is None:
                    b[ti] -= sgn * coef * sv
                else:
                    A[ti][si] += sgn * coef

    # 가우스 소거
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(A[r][c]))
        if abs(A[p][c]) < 1e-18:
            return None
        A[c], A[p] = A[p], A[c]
        b[c], b[p] = b[p], b[c]
        for r in range(k):
            if r == c:
                continue
            f = A[r][c] / A[c][c]
            if f:
                for cc in range(c, k):
                    A[r][cc] -= f * A[c][cc]
                b[r] -= f * b[c]
    return {n: b[i] / A[i][i] for n, i in idx.items()}


def main():
    lines = ["=== ports 기입 전 입력 극성 독립 확인(부호만) ===",
             "단위 소신호 파라미터로 노달 해석. 한 입력만 1 V 여기, 나머지 입력·바이어스는 교류접지.", ""]
    for fn, ins, out in CASES:
        d = json.load(io.open(os.path.join(LIB, fn + ".topology.json"), encoding="utf-8"))
        mos = [m for m in d["netlist"] if isinstance(m, dict)]
        drains = {m["drain"] for m in mos}
        sources = {m["source"] for m in mos}
        gates = {m["gate"] for m in mos}
        rails = set(d.get("supply_nets") or {n for n in (drains | sources | gates) if n in NAMESET})
        bias_only = gates - drains - sources - set(ins)
        acg = rails | bias_only
        nodes = sorted((drains | sources | gates) - acg - set(ins))
        lines.append(f"--- {fn}  (교류접지: 레일 {sorted(rails)} + 바이어스 {sorted(bias_only)})")
        for net in ins:
            sol = solve(mos, acg | (set(ins) - {net}), nodes, net)
            if sol is None or out not in sol:
                lines.append(f"    {net:8s} -> 풀 수 없음(특이행렬 또는 출력 노드 고정)")
                continue
            g = sol[out]
            sign = "동상(+, non-inverting)" if g > 0 else "역상(-, inverting)"
            lines.append(f"    {net:8s} -> v({out}) = {g:+.4g}   {sign}")
        lines.append("")
    lines += ["판정 규칙: 출력과 **동상**인 입력이 `differential_input_p`, 역상인 입력이 `_n`이다",
              "(단일 출력 회로 기준. 넷 이름과 어긋나면 이름이 아니라 이 결과가 정본이다).", ""]
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
