"""b26pre -- review2_b26_1 E6·E7 생존 변이 재현.
v4 모의 head(b26v4_head mode v4: 사이트 10·14는 B35로 넘김)의 N2d 대상 중 E6·E7 def만 골라
b26v4_kill(b1 = HEAD + B34)로 기존 test 인벤토리에 실행한다.
출력: C:/g87/out/e67/kill_v4_N2d.jsonl (변이마다 append)
사용: python -B b26pre_kill.py <NW> [extra test node ...]
"""
import json, os, sys

sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26pre_scripts")
import b26v4_kill as K   # noqa: E402

DEFS = {"optimize_full_circuit_budget", "optimize_full_circuit_budget._evaluate_row_split",
        "_fixup_euler_blocked_rows", "run_matching_safety_with_finger_growth", "run_full_circuit_audit",
        "resolve_stack_layout", "propose_vertical_stack_id_gap_fill", "propose_device_roles_gap_fill",
        "_propose_gm_id_roles", "_propose_L_roles"}
SUB = os.environ.get("E67_OUT", "C:/g87/out/e67/")

if __name__ == "__main__":
    os.makedirs(SUB, exist_ok=True)
    tg = json.load(open("C:/g87/out/targets_v4.json", encoding="utf-8"))
    sel = [t for t in tg if t["def_"] in DEFS]
    json.dump(sel, open(SUB + "targets_v4.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("selected", len(sel), flush=True)
    K.OUT = SUB
    K.main("v4", int(sys.argv[1]), "N2d", sys.argv[2:])
