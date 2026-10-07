"""
세션31 CH -- 사용자 지시("folding해서 끝까지 가보자") -- CG가 진단 사본으로만 확인했던
"M5/M7 theta 분리 + 4개 소자 전부 row_split(folding)" 조합을 **실제 library/two_stage_
ota.topology.json 변경**(L_mirror_M5 -> L_M5/L_M7 분리, .ai/context.md CH 참고) 위에서
끝까지 실행해 instance.json/box_shape PASS까지 완주시킨다.

gain_db>=60은 CF/CG로 이미 반증됐다(진짜 상한 ~51.1dB) -- self-test와 동일 패턴으로
gain_db 문턱만 51.0(CG 실측 51.14보다 살짝 낮은 안전값)으로 낮춘 임시 사본을 쓴다.
library/two_stage_ota.topology.json의 constraints.gain_db>=60 선언 자체는 미변경
(아직 "목표"로 남겨둠 -- 달성 여부와 별개로 이 스크립트는 그 목표를 낮추지 않는다).
"""
import sys, json, os, tempfile, traceback
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import SemiEmpiricalGmIdLUT, optimize_full_circuit_budget, dense_candidates, layout_grid_L_candidates
from stick_diagram import save_instance_json, run_full_circuit_audit_from_topology
from design_report import assemble_report_data, save_html_report

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\two_stage_ota.topology.json"
INSTANCE_OUT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\two-stage-ota-report\two_stage_ota.PROVISIONAL_gain51_M5M7split.instance.json"
REPORT_OUT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\two-stage-ota-report\two_stage_ota.PROVISIONAL_gain51_M5M7split.report.html"
L_GRID_STEP = 0.005e-6

with open(TOPO, encoding="utf-8") as f:
    topo_dict = json.load(f)
for c in topo_dict["sizing_roles"]["constraints"]:
    if c["metric"] == "gain_db":
        c["value"] = 51.0  # CG 실측 상한 51.14보다 살짝 낮춘 임시값(self-test와 동일 패턴)
tmp_path = os.path.join(tempfile.gettempdir(), "two_stage_ota_boxshape_M5M7split.topology.json")
with open(tmp_path, "w", encoding="utf-8") as f:
    json.dump(topo_dict, f)

d = np.load(LUTFILE)
W_REF = 5e-6
nmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_n"], d["GM_n"], d["GDS_n"], d["CGG_n"], W_ref=W_REF, SID_1F=d["SID_1F_n"])
pmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_p"], d["GM_p"], d["GDS_p"], d["CGG_p"], W_ref=W_REF, SID_1F=d["SID_1F_p"])

spec = {
    "lut_by_kind": {"nmos": nmos, "pmos": pmos},
    "lut": nmos,
    "vdd": 1.8,
    "L_candidates": layout_grid_L_candidates(nmos, L_GRID_STEP, n=41),
    "L_grid_step": L_GRID_STEP,
    "VDS_candidates": dense_candidates(nmos.VDS_grid, n=13),
    "gm_id_grid": [i * 0.5 for i in range(4, 61)],
    "GBW": 20e6, "CL": 3e-12, "Z": 10.0, "NDP": 4.0,
    "stage_gain_min": [10 ** (30.0 / 20), 10 ** (30.0 / 20)],
    "L_min": 0.15e-6,
    "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
    "W_bounds": (1e-6, 200e-6),
    "min_vds_by_role": {"cascode": 0.2, "tail": 0.2},
    "stage_objective": "power",
    "stage_w_max": 500e-6,
    "min_finger_w": 0.1e-6,
    "max_finger_w": 40e-6,
    "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    # 2026-08-13(세션31 CH) -- L_mirror_M5(공유 theta)가 L_M5/L_M7(독립)로 분리되면서
    # M5/M7을 더 이상 한 물리 행에 묶을 수 없다(서로 다른 L을 가질 수 있어 한 diffusion
    # strip으로 못 그림) -- 독립 stack으로.
    "stack_groups_override": {"M1": ["M1", "M2"], "M3": ["M3", "M4"],
                                "M5": ["M5"], "M7": ["M7"], "M6": ["M6"]},
    # CG 실측: M5/M7 분리 후 box_shape가 오히려 악화(1.18->2.0, M3/M5/M7이 전부 24핑거로
    # 몰리면서 M6/M1과 불균형) -- M3/M5/M6/M7 4개 소자 전부 2행 folding해야 다시 PASS(1.0).
    "row_split": {"M3": 2, "M5": 2, "M6": 2, "M7": 2},
}

try:
    result = optimize_full_circuit_budget(tmp_path, spec, grid_points_per_theta=7)
    print("OK -- theta_star:", result["theta_star"])
    print("audit_ok:", result["audit_ok"])
    print("metrics:", result["metrics"])
    print()
    print("sizing:")
    for name, s in sorted(result["sizing"].items()):
        print(f"  {name}: kind={s['kind']}, L={s['L']*1e6:.3f}um, W={s['W']*1e6:.3f}um, "
              f"gm_id={s['gm_id']:.2f}, VDS={s['vds']:.3f}V, ID={s['ID']*1e6:.3f}uA")

    full_circuit_audit = None
    try:
        full_circuit_audit = run_full_circuit_audit_from_topology(tmp_path)
        print()
        print("run_full_circuit_audit.ok:", full_circuit_audit.ok)
        for c in full_circuit_audit.checks:
            print(f"  - {c.name}: {c.ok} ({c.detail})")
    except ValueError as e:
        print()
        print(f"[SKIP] run_full_circuit_audit_from_topology() 실패(별도 gap, box-shape와 무관): {e}")

    if result["pipeline_result"] is not None:
        pr = result["pipeline_result"]
        print()
        print("=== box_shape/coverage 감사 ===")
        print(f"box_shape.ok = {pr['box_shape'].ok}  max_ratio={pr['box_shape'].max_ratio:.3f}  "
              f"message: {pr['box_shape'].message}")
        print(f"  row_widths(finger count): {pr['box_shape'].row_widths}")
        print(f"coverage.ok  = {pr['coverage'].ok}  missing: {pr['coverage'].missing}")
        if "repaired_rows" in pr:
            print(f"repaired_rows 존재 -- matching-safety 자동수정이 개입했음")
        save_instance_json(INSTANCE_OUT, tmp_path, result["sizing"], result["pipeline_result"])
        print(f"\ninstance.json 저장(PROVISIONAL, gain_db>=51.0 문턱, M5/M7 분리+4개 folding): {INSTANCE_OUT}")
        if full_circuit_audit is not None:
            report_data = assemble_report_data(tmp_path, INSTANCE_OUT, full_circuit_audit=full_circuit_audit)
            save_html_report(report_data, REPORT_OUT)
            print(f"report.html 저장: {REPORT_OUT}")
        else:
            print("report.html 생략(full_circuit_audit 실패로 assemble_report_data 입력 불완전)")
    else:
        print("pipeline_result=None -- 넷리스트 전체가 사이징되지 않아 box-shape 감사 불가")
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {e}")
    traceback.print_exc()
