"""
세션20 스모크 테스트 -- run_harness.py에 새로 추가한 두 배선(run_full_circuit_audit_
from_topology() -- save_instance_json() 이전 / design_report.py 리포트 생성 -- 저장 이후)이
실제로 동작하는지, 세션11/18의 grid-축소 스모크 테스트 패턴(자유 theta 일부만 남기고 나머지
고정)을 재사용해 빠르게 확인한다. 프로덕션 topology.json은 읽기만 하고(신설된
_netlist_sections_structured 필드가 실제로 포함된 상태로 복사됨) 쓰지 않는다 -- 임시
복사본만 수정.

⚠️ 세션20 실행 결과(정직하게 기록) -- KEEP_FREE=2/5(4/32 조합) 둘 다 psrr_estimate_db/
classab_centering_dev_v 위반으로 "모든 theta 격자점이 infeasible"에서 멈춤(ValueError,
optimize_full_circuit_budget() 자체의 동작, 세션20 신규 코드와 무관). 원인: 이 두 metric을
실제로 좌우하는 theta(r_classab_battery/r_classab_diode_src류, CMFB 관련)가 KEEP_FREE가
고정한 "netlist 순서상 앞쪽 N개"에 안 들어가 항상 중간값에 고정됐다 -- 이건 세션11부터
이월된 그리드 축소 전략 미결(item 7, `.ai/context.md`)과 정확히 같은 문제이지 이번 세션
배선의 결함이 아니다. 그래서 이번 세션은 이 스크립트로 "pipeline_result가 실제로 나오는"
end-to-end까지는 못 갔고, 대신 `run_full_circuit_audit_from_topology()`(stick_diagram.py
Test 31, 실제 프로덕션 topology.json)와 `assemble_report_data()`/`render_html_report()`
(design_report.py self-test Test 3, 실제 topology.json+실제 옛 instance.json+실제 audit
결과)를 각각 독립적으로 실제 데이터로 검증했다 -- `save_instance_json()`은 이번 세션에
손대지 않은 기존 코드다. 세 함수 모두 개별적으로 실측 검증됐으므로 이 스크립트가 여기서
멈추는 것은 배선 검증 실패가 아니라 이미 알려진 별개 문제(item 7)의 재확인이다. item 7이
풀리면(그리드 축소 전략 확정) 이 스크립트를 그대로 다시 돌려 진짜 end-to-end를 완성할 것.
"""
import sys, json, time, tempfile, os, traceback
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import SemiEmpiricalGmIdLUT, optimize_full_circuit_budget
from stick_diagram import save_instance_json, run_full_circuit_audit_from_topology
from design_report import assemble_report_data, save_html_report

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json"
OUT_JSON = os.path.join(tempfile.gettempdir(), "smoke_session20_instance.json")
OUT_HTML = os.path.join(tempfile.gettempdir(), "smoke_session20_report.html")

with open(TOPO, encoding="utf-8") as f:
    topo = json.load(f)

assert "_netlist_sections_structured" in topo, \
    "프로덕션 topology.json에 세션20 구조화 필드가 없음(예상과 다름)"

thetas = topo["sizing_roles"]["theta"]
free = [t for t in thetas if t["bounds"][0] != t["bounds"][1]]
KEEP_FREE = 5
for t in free[KEEP_FREE:]:
    mid = (t["bounds"][0] + t["bounds"][1]) / 2
    t["bounds"] = [mid, mid]

tmp_path = os.path.join(tempfile.gettempdir(), "smoke_current_reuse_telescopic_ota_s20.json")
with open(tmp_path, "w", encoding="utf-8") as f:
    json.dump(topo, f)
print(f"임시 topology: {tmp_path}")

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
    "t_lln": 30e-9,
    "PM_target_deg": 70.0,
    "Cc": 500e-15,
    "Cf": 500e-15,
    "Cs": 500e-15,
    "C_Ltot": 1e-12,
    "t_settle_total": 6.9 * 30e-9,
    "omega_c": 6.9 / 30e-9,
}

t0 = time.time()
try:
    result = optimize_full_circuit_budget(tmp_path, spec, grid_points_per_theta=2)
    elapsed = time.time() - t0
    print(f"OK -- 소요시간: {elapsed:.1f}s")
    print("theta_star:", result["theta_star"])
    print("audit_ok:", result["audit_ok"])

    # 세션20 배선 1 -- save_instance_json() 이전 run_full_circuit_audit_from_topology()
    full_circuit_audit = run_full_circuit_audit_from_topology(tmp_path)
    print("run_full_circuit_audit.ok:", full_circuit_audit.ok)
    for c in full_circuit_audit.checks:
        print(f"  - {c.name}: {c.ok} ({str(c.detail)[:150]})")
    assert full_circuit_audit.ok, "실제 프로덕션 topology.json(자유 theta만 줄인 스모크)에서 audit FAIL -- 예상과 다름"

    pr = result["pipeline_result"]
    if pr is not None:
        save_instance_json(OUT_JSON, tmp_path, result["sizing"], pr)
        print(f"instance.json 저장 완료: {OUT_JSON}")

        # 세션20 배선 2 -- design_report.py로 리포트 생성
        report_data = assemble_report_data(tmp_path, OUT_JSON, full_circuit_audit=full_circuit_audit)
        save_html_report(report_data, OUT_HTML)
        print(f"report.html 저장 완료: {OUT_HTML} ({os.path.getsize(OUT_HTML)} bytes)")

        with open(OUT_HTML, encoding="utf-8") as f:
            html_text = f.read()
        assert "run_full_circuit_audit" in html_text, "리포트에 run_full_circuit_audit 섹션이 없음"
        assert "Topology" in html_text, "리포트에 topology 섹션이 없음"
        print("리포트 내용 확인: run_full_circuit_audit/Topology 섹션 존재 -- PASS")
    else:
        print("pipeline_result=None -- instance.json/report 저장 생략(이번 스모크 grid에서는 발생 안 함이 기대값)")
except Exception as e:
    elapsed = time.time() - t0
    print(f"[FAIL] {elapsed:.1f}s 후 {type(e).__name__}: {e}")
    traceback.print_exc()
