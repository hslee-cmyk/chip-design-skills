"""
세션31 BZ① 계속 -- 사용자 지시("현재 최적화된 값으로 stick layout까지 진행, box shape로
만들 수 있는지 확인") -- LUT L 확장 스윕(백그라운드 실행 중)이 끝나기 전, **지금까지
실제 sky130 LUT로 확인된 최선의 achievable 사이징**(diagnose_gain_sweep2.py 결과:
stage_w_max=500um, stage_gain_min=38dB/stage, L_mirror_M3/M5=1e-6 고정 -> gain_db=51.12,
.ai/context.md 세션31 CA 참고)으로 실제 stick diagram/box-shape 감사까지 완주시킨다.

gain_db>=60 constraint는 아직 미달성 상태이므로(51.12<60) optimize_full_circuit_budget()이
그대로면 ValueError로 죽는다 -- self-test(_tso_spec)와 동일 패턴으로 gain_db 문턱만 임시로
낮춘 topology 사본을 써서(library/two_stage_ota.topology.json 원본은 미변경) 사이징을
끝까지 통과시키고, 그 결과의 pipeline_result(box_shape/coverage 감사)를 그대로 보고한다 --
gain_db 미달성이라는 사실 자체를 숨기지 않는다(§1.5 정직한 보고 원칙).
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
INSTANCE_OUT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\two-stage-ota-report\two_stage_ota.PROVISIONAL_gain51.instance.json"
REPORT_OUT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\two-stage-ota-report\two_stage_ota.PROVISIONAL_gain51.report.html"
L_GRID_STEP = 0.005e-6
ACHIEVED_GAIN_DB = 51.12  # diagnose_gain_sweep2.py 실측 상한(stage_gain_min=38dB/stage)

with open(TOPO, encoding="utf-8") as f:
    topo_dict = json.load(f)
for c in topo_dict["sizing_roles"]["constraints"]:
    if c["metric"] == "gain_db":
        c["value"] = 50.0  # 원본 60 -> 실측 achievable(51.12)보다 살짝 낮춘 임시값(self-test와 동일 패턴)
tmp_path = os.path.join(tempfile.gettempdir(), "two_stage_ota_boxshape_check.topology.json")
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
    "stage_gain_min": [10 ** (38.0 / 20), 10 ** (38.0 / 20)],
    "L_min": 0.15e-6,
    "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
    "W_bounds": (1e-6, 200e-6),
    "min_vds_by_role": {"cascode": 0.2, "tail": 0.2},
    "stage_objective": "power",
    "stage_w_max": 500e-6,
    "min_finger_w": 0.1e-6,
    "max_finger_w": 40e-6,
    "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    "stack_groups_override": {"M1": ["M1", "M2"], "M3": ["M3", "M4"],
                                "M5": ["M5", "M7"], "M6": ["M6"]},
    # 2026-08-13(세션31 이어, CD절 -- 사용자 승인) -- M6은 매칭 파트너가 없는 단독 소자라
    # box-shape 비율(M6 26f vs M3/M5 11~12f)을 common_centroid_layout()으로는 못 줄인다
    # (매칭쌍 전용 API, N>=2 요구) -- 명시적 소자 folding(row_split)으로 2개 물리 행에
    # 나눠 접는다(추가 contact/via 비용 수반, apply_explicit_row_split() docstring 참고).
    "row_split": {"M6": 2},
}

try:
    result = optimize_full_circuit_budget(tmp_path, spec, grid_points_per_theta=5)
    print("OK -- theta_star:", result["theta_star"])
    print("audit_ok:", result["audit_ok"])
    print("metrics:", result["metrics"])
    print()
    print("sizing:")
    for name, s in sorted(result["sizing"].items()):
        print(f"  {name}: kind={s['kind']}, L={s['L']*1e6:.3f}um, W={s['W']*1e6:.3f}um, "
              f"gm_id={s['gm_id']:.2f}, VDS={s['vds']:.3f}V, ID={s['ID']*1e6:.3f}uA")

    # 2026-08-13(세션31 이어) 실측 발견 -- library/two_stage_ota.topology.json은
    # `_netlist_sections_structured`가 없다(current_reuse_telescopic_ota.topology.json엔
    # 있음, `run_full_circuit_audit_from_topology()`가 요구하는 필드) -- 이 gap은 gain_db
    # constraint와 무관하게 존재하던 것인데, 지금까지 optimize_full_circuit_budget() 자체가
    # gain_db>=60 infeasible로 먼저 죽어서 이 단계까지 온 적이 없어 안 드러났었다. box-shape
    # 확인이라는 이번 요청 덕분에 처음 발견됨 -- 정직하게 건너뛰고 별도로 보고한다(gain_db
    # 미달성과는 별개의, 이 회로가 진짜 instance-ready가 되기 전에 추가로 채워야 할 gap).
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
        print(f"\ninstance.json 저장(PROVISIONAL, gain_db=51.12<60 미달성 상태 그대로 저장): {INSTANCE_OUT}")
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
