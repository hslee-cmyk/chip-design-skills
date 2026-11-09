# 대표 동작점(sky130 적응 치수, 손계산 θ 기저 설계) 정의 + 전체 벤치 대조. 결과 append: design_out.jsonl
import json, pathlib, sys
import bench as B
import design as D
HERE = pathlib.Path(__file__).parent
BASE = dict(B.SIZES); BASE.update(M15=("p", 200, 0.36), M9a=("p", 5, 0.15))
IQ = 20e-6

def setup(IQ=IQ, I9a=0.6e-6, I9b=0.6e-6):
    S, nodes = D.hand(IQ=IQ, I9a=I9a, I9b=I9b, sizes=BASE)
    B.SIZES.clear(); B.SIZES.update(S)
    B.I8 = B.I10 = I9a + I9b; B.I12 = 2.2e-6; B.I13 = 2.5e-6
    return S, nodes

if __name__ == "__main__":
    I9a = float(sys.argv[1]) if len(sys.argv) > 1 else 0.6e-6
    I9b = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6e-6
    S, nodes = setup(I9a=I9a, I9b=I9b)
    r = B.op(f"rep_q_{I9a*1e9:.0f}n_{I9b*1e9:.0f}n")
    out = dict(case="rep_quiescent", I9a_design=I9a, I9b_design=I9b, IQ_design=IQ, hand_nodes=nodes, sizes=S,
               spice_nodes=r["nodes"], spice={k: r["dev"][k] for k in r["dev"]})
    with open(HERE / "design_out.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(out) + "\n")
    print(json.dumps(out, indent=1))
