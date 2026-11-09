"""e_inst_p3.py(_drafts/p3_scripts/e_inst_p3_proposed, 수정 없음)를 같은 프로세스에서 runpy로 돌린 뒤
sizing_recipe._RV_CALLS(있으면 -- #21 시제품의 RailVoltages 읽기 계수)를 <out>.rv_calls.json에 적는다.
사용: python -B -P e_inst_c21.py <root> <회로> <out.json>"""
import json, os, runpy, sys
E = r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\p3_scripts\e_inst_p3_proposed\e_inst_p3.py"
root, circuit, out = sys.argv[1:4]
sys.argv = [E, root, circuit, out]
rc = 0
try:
    runpy.run_path(E, run_name="__main__")
except SystemExit as e:
    rc = e.code if isinstance(e.code, int) else 1
sr = sys.modules.get("sizing_recipe")
calls = getattr(sr, "_RV_CALLS", None) if sr else None
json.dump({"rc": rc, "sizing_recipe_file": getattr(sr, "__file__", None), "rv_calls": calls},
          open(out + ".rv_calls.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
sys.exit(rc)
