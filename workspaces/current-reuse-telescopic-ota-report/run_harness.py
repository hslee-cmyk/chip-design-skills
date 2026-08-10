"""
batch 7-5 -- current_reuse_telescopic_ota를 optimize_full_circuit_budget() 하나만으로
spec -> instance.json까지 완주시키는 harness-only 실행 스크립트.
"""
import sys, json, traceback
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import SemiEmpiricalGmIdLUT, optimize_full_circuit_budget
from stick_diagram import save_instance_json, run_full_circuit_audit_from_topology
from design_report import assemble_report_data, save_html_report

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json"
INSTANCE_OUT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\current-reuse-telescopic-ota-report\current_reuse_telescopic_ota.instance.json"
REPORT_OUT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\current-reuse-telescopic-ota-report\current_reuse_telescopic_ota.report.html"

d = np.load(LUTFILE)
W_REF = 5e-6
nmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_n"], d["GM_n"], d["GDS_n"], d["CGG_n"], W_ref=W_REF, SID_1F=d["SID_1F_n"])
pmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_p"], d["GM_p"], d["GDS_p"], d["CGG_p"], W_ref=W_REF, SID_1F=d["SID_1F_p"])

spec = {
    "lut_by_kind": {"nmos": nmos, "pmos": pmos},
    "lut": nmos,
    "vdd": 1.8,
    "L_candidates": [float(v) for v in nmos.L_grid],
    "VDS_candidates": [float(v) for v in nmos.VDS_grid[::24]],
    "gm_id_grid": [4.0, 8.0, 12.0, 16.0, 20.0, 24.0],
    "L_min": 0.15e-6,
    "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
    "W_bounds": (1e-6, 200e-6),
    "min_vds_by_role": {"cascode": 0.2, "tail": 0.3, "mirror": 0.3},
    "stage_objective": "power",
    "stage_w_max": 200e-6,
    "min_finger_w": 1e-6,
    "max_finger_w": 40e-6,
    "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    # compensation.parameters
    "t_lln": 30e-9,
    "PM_target_deg": 70.0,
    "Cc": 500e-15,
    "Cf": 500e-15,
    "Cs": 500e-15,
    "C_Ltot": 1e-12,
    # 2026-08-10(세션27) 정정 -- t_settle_total은 do.md §7.3.1 Level1 "t_s=t_slew+t_lln
    # 배분"의 총합(논문 III.A "t_slew=10ns/t_lln=30ns"=40ns)이어야 하는데, 이전 값
    # (6.9*30e-9≈207ns)은 t_lln*omega_c=6.9 정의를 엉뚱하게 총정착시간에 갖다 쓴 것이었다
    # -- f_slew->t_lln 배선이 미완결이던 동안엔 t_settle_total이 실제로 아무 데도 안 읽혀서
    # (derived[t_slew]를 아무도 안 읽음) 드러나지 않았을 뿐이다. 이제 t_lln=t_settle_total*
    # (1-f_slew)로 실제 유도되므로 물리적으로 맞는 값(40ns)으로 정정 -- f_slew=0.25일 때
    # t_slew=10ns/t_lln=30ns로 논문 수치와 정확히 재현됨(sizing_recipe.py self-test의
    # _feed_settling_split 데모와 동일 값).
    "t_settle_total": 40e-9,
    # omega_c는 더 이상 여기서 손으로 줄 필요가 없다(compensation이 t_lln에서
    # 자동 유도해 ctx.derived로 노출 -- _feed_gm_target_convention()이 우선 사용).
    # 다만 compensation이 없는 회로/구형 spec과의 하위호환을 위해 폴백값으로 남겨둔다.
    "omega_c": 6.9 / 30e-9,
}

try:
    result = optimize_full_circuit_budget(TOPO, spec, grid_points_per_theta=2)
    print("OK -- theta_star:", result["theta_star"])
    print("audit_ok:", result["audit_ok"])
    print("metrics:", result["metrics"])
    # 세션20 -- optimize_full_circuit_budget()의 audit_ok(=audit_row_split, 물리 행 단위
    # euler/box-shape/matching 품질)와는 별개로, topology.json 전체(소자 수 vs 선언된
    # 매니페스트/net 이름 대소문자/matching·hub-merge 후보 전수 disposition)를 감사하는
    # run_full_circuit_audit()도 save_instance_json() 이전에 반드시 돌린다(사용자 지시,
    # §1.6 게이트가 지금까지 이 harness 경로에 전혀 배선돼 있지 않았다 -- .ai/context.md
    # 세션20 참고). connectivity/dispositions는 사이징 성패와 무관하므로 pipeline_result
    # 유무와 관계없이 항상 실행한다.
    full_circuit_audit = run_full_circuit_audit_from_topology(TOPO)
    print("run_full_circuit_audit.ok:", full_circuit_audit.ok)
    for c in full_circuit_audit.checks:
        print(f"  - {c.name}: {c.ok} ({c.detail})")

    # 세션18 -- optimize_full_circuit_budget()은 계산까지만 하고 저장은 안 한다(순수
    # 함수 유지, .ai/context.md 세션18 참고). instance.json 저장은 "진짜 최상위"인 이
    # 스크립트(run_harness.py)의 몫 -- audit_ok=False여도 감사 실패 항목이 있는 상태
    # 그대로 정직하게 저장한다(조용히 성공으로 둔갑시키지 않는다, §1.5 원칙과 동일).
    # run_full_circuit_audit도 같은 원칙 -- ok=False라도 저장을 막지 않고 정직하게 기록한다.
    if result["pipeline_result"] is not None:
        save_instance_json(INSTANCE_OUT, TOPO, result["sizing"], result["pipeline_result"])
        note_parts = []
        if not result["audit_ok"]:
            note_parts.append("audit_ok=False -- audit_row_split에 남은 FAIL 항목 그대로 저장됨")
        if not full_circuit_audit.ok:
            note_parts.append("run_full_circuit_audit.ok=False -- 위 체크 결과 참고")
        note = f" ({'; '.join(note_parts)})" if note_parts else ""
        print(f"instance.json 저장: {INSTANCE_OUT}{note}")

        # 세션20 -- 리포트 생성도 이 harness 스크립트에서 같이 호출한다(사용자 지시).
        # design_report.py는 topology.json/instance.json/run_full_circuit_audit 결과에서
        # 기계적으로 조립 가능한 부분만 자동으로 채운다 -- 논문 spec 표/레이아웃 가이드
        # 서술(narrative)은 지어내지 않고 생략한다(§0 원칙, design_report.py 모듈 docstring
        # 참고). 더 풍부한 리포트가 필요하면 narrative dict를 채워 넘길 것.
        report_data = assemble_report_data(TOPO, INSTANCE_OUT, full_circuit_audit=full_circuit_audit)
        save_html_report(report_data, REPORT_OUT)
        print(f"report.html 저장: {REPORT_OUT}")
    else:
        print("pipeline_result=None -- 넷리스트 전체가 사이징되지 않아 instance.json/report 저장 생략")
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {e}")
    traceback.print_exc()
