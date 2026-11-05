"""IT-2c 판정 기록 작성(BOM 없는 UTF-8). 인자: 임시 루트, audit worktree."""
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

T, W = Path(sys.argv[1]), Path(sys.argv[2])
R = T / "res"
ID = "20261104-it2c-icm-config"
rev = lambda x: subprocess.check_output(["git", "-C", str(W), "rev-parse", x], text=True).strip()   # noqa: E731
BASE, TEST, CODE, HEAD = rev("4d39eaf5"), rev("dc8ccefe"), rev("4e985989"), rev("37a2cf5c")
P = "skills/analog-gmid-design/"


def fhash(tid, exc):
    return hashlib.sha256(("%s\n%s" % (tid, exc)).encode("utf-8")).hexdigest()


def suite(path):
    root = ET.parse(path).getroot()
    s = root if root.tag == "testsuite" else root[0]
    return int(s.get("tests")), int(s.get("failures")) + int(s.get("errors")), int(s.get("skipped") or 0)


card, structure, canon, smoke_before, impacted = (suite(R / "head" / (n + ".xml")) for n in ("card", "structure", "canon", "smoke", "impacted"))
smoke_after, structure_after = suite(R / "after" / "smoke.xml"), suite(R / "after" / "structure.xml")
assert card == (589, 0, 0) and structure == (171, 0, 0) and canon == (12, 0, 0) and smoke_before == (23, 2, 0), (card, structure, canon, smoke_before)
assert smoke_after == (23, 0, 0) and structure_after == (171, 0, 0) and impacted == (742, 0, 0), (smoke_after, structure_after, impacted)

rows = [json.loads(x) for x in (R / "red.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
failed = [r for r in rows if r["outcome"] == "failed"]
mss = [r for r in failed if "test_ss_metrics.py" in r["id"] and r["exc"] == "builtins.ImportError"]
red = [r for r in failed if r not in mss]
assert len(mss) == 55 and len(red) == 69, (len(mss), len(red))
types = {}
for r in red:
    n = r["exc"].rsplit(".", 1)[-1]
    types[n] = types.get(n, 0) + 1

mut = [json.loads(x) for x in (R / "mutations.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
mut = [m for m in mut if "mut" in m]
assert all("error" not in m for m in mut), [m for m in mut if "error" in m]
surv = [m["mut"].split()[0] for m in mut if not m["killed"]]
killed = [m["mut"].split()[0] for m in mut if m["killed"]]
assert surv == ["M7", "M8", "M11", "M14", "M18", "M19"] and len(killed) == 17, (surv, killed)

rej = [json.loads(x) for x in (R / "reject.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
rej2 = [json.loads(x) for x in (R / "reject2.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
assert all(r["ok"] for r in rej + rej2) and len(rej) == 29 and len(rej2) == 6, (len(rej), len(rej2))

phys = [json.loads(x) for x in (R / "flow2_head.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
ph = [r for r in phys if r["case"] == "phys"]
assert len(ph) == 12
worst_end = 0.0
for r in ph:
    for p, e in r["independent_ends"].items():
        worst_end = max(worst_end, abs(e[0] - r["cfg"][p][0]), abs(e[1] - r["cfg"][p][1]))
    assert r["rows_missing_nets"] == 0
worst_kcl = max(r["kcl_residual"] for r in ph)
worst_cs = max(abs(r["c_dot_s"]) for r in ph if r["config"] == "servo")
cost = {r["circuit"]: r for r in phys if r["case"] == "cost"}
ratio = {c: (r["prof"]["ss_nodal_system"][1] + r["prof"]["icm_config_window"][1]) / r["wall_s"] for c, r in cost.items()}
folded_phys = next(r for r in ph if r["circuit"] == "folded_cascode")
cg_phys = next(r for r in ph if r["circuit"] == "common_gate_amplifier")

rn = [json.loads(x) for x in (R / "rename_mut.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
rb = [json.loads(x) for x in (R / "rename_base.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
cert_n = sum("pf_moved" in r for r in rn)
cert_ok = sum(bool(r.get("pf_cert_same")) for r in rn)
moved = sum(r.get("pf_moved", 0) > 0 for r in rn)
p_same = sum(sum(r["p_port_colour_same"]) for r in rn)
p_n = sum(len(r["p_port_colour_same"]) for r in rn)
p_same_b = sum(sum(r["p_port_colour_same"]) for r in rb)
node_mm = sum(len(r["node_mismatch"]) for r in rn)
node_mm_b = sum(len(r["node_mismatch"]) for r in rb)
dev_mm = {r["circuit"]: 0 for r in rn}
for r in rn:
    dev_mm[r["circuit"]] += len(r["device_mismatch"])
assert cert_ok == cert_n == 45 and moved == 3 and p_same == p_n and node_mm == 0 and node_mm_b > 0, (cert_ok, cert_n, moved, p_same, p_n, node_mm, node_mm_b)
canon_h = {json.loads(x)["circuit"]: json.loads(x) for x in (R / "canon_head.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
canon_b = {json.loads(x)["circuit"]: json.loads(x) for x in (R / "canon_base.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
colour_diff = sum(canon_h[c]["node_colour"] != canon_b[c]["node_colour"] or canon_h[c]["device_colour"] != canon_b[c]["device_colour"] for c in canon_h)
assert colour_diff == 0 and sum(r.get("pf_called") is False for r in canon_h.values()) == 2

a8h = json.loads((R / "a8_mut.jsonl").read_text(encoding="utf-8").splitlines()[0])
a8b = json.loads((R / "a8_base.jsonl").read_text(encoding="utf-8").splitlines()[0])
assert a8h == a8b

we = [json.loads(x) for x in (R / "we.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
assert [r["sealed"] for r in we] == [False, False, False, False, True, True, True, False, False, False, False]
assert all(abs(r["slack_v"]) <= r["tol_v"] for r in we if not r["sealed"])

causes = json.loads((R / "cause_table.json").read_text(encoding="utf-8"))
assert len(causes) == 11
fixture_diff = subprocess.check_output(["git", "-C", str(T / "iso"), "diff", "--", P + "gmid_engine/tests/integration/fixtures/u17_1b_s0_baseline.json", P + "gmid_engine/tests/structure/g8_baseline.json"])
fixture_sha = hashlib.sha256(fixture_diff).hexdigest()

lows = []
for f in R.glob("jobs*.json.log"):
    for x in f.read_text(encoding="utf-8").splitlines():
        d = json.loads(x)
        if "low" in d:
            lows.append(d["low"])
        if "free" in d:
            lows.append(round(d["free"], 2))
mem_low = min(lows)

HOLD = "미완료(보류 다리: 13회로 변화표·착수 실측 (a)(b)(d)(e)·sf_pushpull 재측정·SPICE, O-225·A-5·A-7, 통과로 세지 않음, base = %s)" % BASE
RAN = ("잰 범위 = 병합본 %s(격리 복제본): card test 16 파일 %d개 실패 0, tests/structure %d개 실패 0(규칙 H 마커 1 deselected), search/test_canonical_order %d개 실패 0, 2회로 연기 stage_b·s0·g10 %d개(재측정 전 실패 %d = test_stage_reports_unchanged_from_base[folded_cascode, ngcc_3stage_ff] `tables`, fixture 재측정 뒤 %d개 실패 0), 영향 파일 21개(옛 test, 원인 규명용) %d개 실패 0"
       % (HEAD[:8], card[0], structure[0], canon[0], smoke_before[0], smoke_before[1], smoke_after[0], impacted[0]))
checks = {
    "V1": {"verdict": "N/A", "basis": "전체 test 안 돌림, 임시 규칙 O-229. " + RAN + ". 그 밖 test 는 통과로 세지 않는다."},
    "V2": {"verdict": "PASS", "basis": "red: 격리 base 복제본(엔진 %s + 동결 test 트리 %s, 엔진 diff 0, 커밋별 역할 분리 실측 13커밋: test 커밋 엔진 0 파일, code 커밋 test 0 파일). 실패 124 = _mss 픽스처 ImportError 55(interface 빈칸 답 2-9 는 56 이라 적었으나 56번째 test_block_declaration 은 READS AssertionError 라 red 로 셈, 옛 test_ss_metrics.py 가 base 에서 59 통과 실측) + red %d %s. base green 인 새 test 7 나열: zero_inputs_toy(로더 거부 기존 사실), sw_root_is_a_single_net, sw_rows_at_or_below_eps 4, sw_row_just_above_eps -- 옛·새 동작 공통 회귀 보호로 유지, 각 id 에 red 사례가 따로 있음(interface green 규칙). green: 같은 %d 이 병합본에서 전부 통과. 새 모듈 import 실패는 계약상 신규 함수 조건." % (BASE[:8], TEST[:8], len(red), json.dumps(types, ensure_ascii=False), len(red))},
    "V3": {"verdict": "PASS", "basis": "mutate_changed.py 는 대상이 assets/tests 라 안 썼다(DEC-86). 손 뮤턴트 23(복제본 임시 수정, 커밋 없음, scripts/mutate.py): killed 17 = %s, 생존 6 = %s. 생존은 test 구멍으로 minor(엔진 값 결함 아님, 복제본 직접 호출로 그 갈래가 옳게 동작함을 확인, reject2.jsonl): M7 선언 뷰가 섞인 스냅샷의 default_port 거름, M8 tol_v 최솟값, M11 view_factor 다른 고정 집합, M14 |a_e|·span <= δV_out 거부 갈래(T-L8e (b)는 _transfer_resolution 만 부름), M18 h 대신 위치 맞바꿈(cert 불변 단언 없음), M19 archive 배열." % (",".join(killed), ",".join(surv))},
    "V4": {"verdict": "PASS", "basis": "test_lint.py 안 돌림: 대상이 assets/tests 라 공허, DEC-86 merge_gate 미사용. oracle 대조: T-L8a·b servo 끝 = spec '물리 결정자'(servo 구성 + VDS = VDSAT) 손 KCL s_o = -2A1A2/(A1+A2), s_p = 1∓δ 와 일치. T-L8a′ 여유 0 끝 != +tol 끝(전제 포함). T-L8c W3 출력·T-L8d MOS 부하 Gf 손 식, T-L8e (a) gm 비트 같음 a_e 0, (b) Fraction 참값 대조, T-L8g V_cm 같은 끝 상태 평균, T-L8h Δc 대 Δlo, T-D triode 행 영 교차, T-K Δlo > Δhi·건너뛴 행 slack < 0, g_bound Higham 식 손 계산: 모두 스냅샷 원시값·LUT 식으로 계산하고 피검 kvl_sensitivity·saturation_window·icm_config_window·port_window 를 기대값에 안 씀(grep: test_icm_config 의 conductance_matrix·_transfer_resolution 는 T-L8e (b) 단위 호출만, region_rows 는 값 test 대상). 판정자 독립 재계산: 실회로 folded_cascode·common_gate_amplifier 봉인점 12점에서 G 를 numpy 로 직접 풀어 낸 끝과 cfg 끝 차 최대 %.3g V." % worst_end},
    "V5": {"verdict": "PASS", "basis": "기준 약화 없음. (1) test_window_ends_are_saturated: 허용 = '봉인이면 항목 7 pass, 봉인 7 거부면 |slack_v| <= tol_v', 다른 거부 사유는 _evaluate_point 가 실패 -- 같은 파일 O-103 test 와 같은 _evaluate_point·_tol_of_window 이고 그 test 는 oracle·V(in) 단언까지 유지하므로 더 넓지 않음. 실측 y = 0: slack_v −0.973 mV, tol_v 7.81 mV. (2) dc_window[\"in\"] 삭제분: cfg 쪽 test_it2c_servo_window_two_inputs_hand_kcl·three_inputs 등이 입력 DC 선언 toy 에서 measured·손 끝(Δlo < 0 < Δhi)을 단언 -- 실제 있음. (3) 폐기 RETIRED 20건 AST 대조: 제거된 test 20 중 19 목록 일치, test_dc_table_has_34_fields 는 33 으로 이름 변경(계약). (4) 대체: k1 -> T-K, d_triode -> test_it2c_triode_*, l12b -> single_input/servo_undeclared, pb -> servo 손 식(대칭 toy 없음 minor). (5) l12a (d) 소사례 삭제: 전제 소멸, (a)(c) 유지, WB-1 재작성 대상, 대체 단언 없음 기록. (6) metrics_ss READS 정확 집합 -> ⊇ 는 interface 'READS' 문언. (7) g8_baseline stale 8행 삭제(줄임, A3 판정자 몫), fixture tables 11행(재측정). 기준선 diff sha256 %s." % fixture_sha},
    "V6": {"verdict": "PASS", "basis": "tests/structure %d 통과, ratchet new 0, stale 8 -> 0(_Circuit.L·bulk·coord·device_colour·kinds·pins·rail_v·writers, Circuit 이동으로 줄어든 키를 판정자가 줄임, 100 -> 92행). 회로 이름 0(새 모듈 grep), 광범위 except 추가 0, 새 수치 상수 0(ε = sys.float_info). 규칙 H(기본 deselected): 새 위반 1 = metrics/ss_nodal.py 짝 test 없음(spec·interface T-L10 은 test_ss_nodal.py, 실제 단언은 test_icm_config·test_ss_evaluate) -- minor. source_lint.py 안 돌림(대상 assets/tests)." % structure[0]},
    "V7": {"verdict": "PASS", "basis": "reachability.py 안 돌림(공허). graph 정본·소비 판정: 새 필드 4(graph.ss_circuit·graph.ss_nodal·node.dc_window_cfg·graph.icm_config), 새 칸 5(default_port 2·g_ops·g_bound·pivot 2 = 칸 6). writer 각 1(WriterTable·grep, S2 표, ss_evaluate 호출 1). 소비자: ss_circuit = metrics_ss·metrics_aux·ss_nodal, ss_nodal = icm_config·metrics_aux, g_bound = _transfer_resolution, g_ops = conductance_matrix, ViewS1v.default_port = icm_config, Circuit = dc_columns·icm_config. 소비자 0 = 2: node.dc_window_cfg·graph.icm_config -- 작성자 표대로 IT-2d interface(T-M1·T-M3, metrics_aux READS)에 계약이 있으나 role/code/20261104-it2d 머리 10ca55a6 은 test 병합뿐이고 엔진 소비 코드 0(실측) -> **병합 조건: IT-2d 코드와 같은 통합 병합, 단독 master 병합 금지**. 피벗 두 칸 출력 전용 사실: 엔진 소비 0, S3 스냅샷 JSON 에 있음(common_gate 실측 pivot_a_e 8.84). 조립 사본 삭제: _ss_of 0, metrics_ss·metrics_aux 조립 0, 세 조립 자리 view_factor -> 필드, block_model·ff_gm_ratio 의 conductance_matrix 는 부분 회로라 다른 입력. 필드 수 4 / 소비자 0 2(조건부) / 정본 우회 의심 1(region_rows 와 봉인 7 VDSAT 같은 입력 = HC-S 배정, card 표지) / KVL·KCL 관계 미적용 0 / graph 밖 저장 자리 0(새 모듈 dict·cache·memo·sctx 슬롯·EvalResult 칸 0, conductance_matrix terms·index 는 호출 안 지역 값). archive: 스냅샷 전체를 쓰는 출력 경로의 직렬화 분기만, 엔진 재읽기 0, ss_nodal 칸 약 1.5 kB/947 kB(7노드), find_front 2점 -- 값 사본 아님. rule_hash(A5): 두 파일 diff = rule_hash 줄 1, 다른 키 비트 동일, e1521ae5 안, structure_rule_fp == 기록값, T-RH 통과, 되돌리면 M23 kill. fix 의 s1_symmetry·s1_values 는 rule 파일 밖 -> 재기록 불필요."},
    "V8": {"verdict": "PASS", "basis": "우회 두 자리 발동 0 실측: (1) icm_config 포트 사실 경로 default_port_seeds: 실회로 2개 전 평가 스냅샷에 graph.views 있음, 규칙 정의 하나, 값 저장 없음, S1v 없는 단위 toy 전용 -- test_icm_config toy 는 이 경로를 지나고 S1v 경로는 실회로·직접 호출로만 잰다(minor, LA-1 재점검). (2) nodal=None 경로: metrics_aux 가 늘 필드를 넘김(grep), 단위 호출만. 거부 경로 직접 1회 35건 전부 거부/계약대로(reject.jsonl 29, reject2.jsonl 6): saturation_window 쌍 root·없는 root·건너뛴 행 slack<0, _end_state 빈 창, kvl 구동 비고정·closure·특이·a_e 0, servo rail_span 0·None·특이·a_e<=δ, as_is 특이 -> unmeasured, _select 갈래 1·2·3·4·4′·5, StampSet 길이, NodalSystem 쓰기 2, Circuit 키워드. 지원 밖 원소·VDSAT 없음·결측 저항 = card test 통과."},
    "V9": {"verdict": "PASS", "basis": "물리 정합: (a) 측정 구성은 DC 양: G = gm·gmb·gds·저항, 용량 개방, W·바이어스 고정 KCL, θ 감도 호출 0(원칙 3·4). (b) 독립 풀이 대조 12점(folded_cascode servo, common_gate as_is): KCL 잔차 최대 %.3g A/V, servo c·s 최대 %.3g, 끝 차 최대 %.3g V, 행 넷 누락 0. folded: V_cm [%.4f, %.4f] V, a_e %.2f, 분해능 %.3g. common_gate: 창 [%.4f, %.4f] V. (c) 여유 0 대 봉인 7 +tol 기간: toy y 훑기 11점 -- y <= 1e-3·>= 0.999 봉인 7 거부(slack_v -0.73~-0.98 mV, 독립 oracle 일치), y = 0.01·0.5·0.99 봉인, 봉인이 창보다 엄격 = fail-closed, 창이 봉인을 넓히지 않음. (d) saturation_window: 건너뛴 행 slack<0 -> None -> 모든 포트 unmeasured(fail-closed), 건너뛰지 않은 행 slack<0 은 끝이 0 밖으로(창이 봉인점을 안 품음), M3 kill. 커널 None 은 unmeasured 순서 창 + 봉인 판정. (e) 회귀 수정: _p_port_first 이름 전단사 5 seed(측정 10회로, 나머지 3회로는 탐침 전원 구성 탓 미측정, p 포트 있는 9회로) cert 같음 %d/%d(움직인 사례 %d), p 포트 색 같음 %d/%d(base %d), node 색 불일치 0(base %d), library 원이름 13회로 색·orbits 변화 0, p 포트 없는 2회로 미호출, port_role writer = s1_structure 가 s1_symmetry 보다 앞(층 순서 유지), canonical_order 12/12, s1_symmetry 기대 갱신 1. 잔여: cnr_ota 병렬 finger device 색 이름 의존 %d/5seed(base 201) minor." % (worst_kcl, worst_cs, worst_end, folded_phys["vcm"][1], folded_phys["vcm"][2], folded_phys["pivot_a_e"], folded_phys["pivot_res"], cg_phys["cfg"]["vin"][0], cg_phys["cfg"]["vin"][1], cert_ok, cert_n, moved, p_same, p_n, p_same_b, node_mm_b, dev_mm["cnr_ota"])},
    "V10": {"verdict": "N/A", "basis": "spec '재현할 수치' 없음. " + HOLD + ". 기준선 재측정(원인 칸, 값 표 아님): 11회로 stage_a_sha.tables 만 변화, 회로마다 head tables 에서 views[].default_port 를 지우면 base tables 와 비트 동일(cause_table.json, 사슬 두 번 비트 동일). cnr·erfc O-228 고정 유지. A8: 같은 toy·같은 θ metrics_ss·metrics_aux·metrics_dc value_fp 비트 동일(block_residual 보고 포함, offset_* 는 이 toy 에서 정의 불능 code 까지 동일). 실회로는 같은 θ 라도 입력 뿌리 창 여유 0 으로 y -> V(in) 사상이 약 1.2 mV 옮겨 DC 가 달라 지문 다름(folded 24/24, common_gate 4/4, 동작 변경 칸, 13회로 표는 보류)."},
}
stale_doc = {"id": ID, "order": "순서 3 freeze", "isolation": str(T / "iso").replace("\\", "/") + " (git clone --no-hardlinks --no-local, origin 제거), base 복제본 동일",
             "freeze": {"test_end_commit_T": TEST, "base_commit": BASE, "code_commit": CODE, "head": HEAD,
                        "tests_tree_lsTree_sha256": hashlib.sha256(subprocess.check_output(["git", "-C", str(W), "ls-tree", "-r", TEST, "--", P + "gmid_engine/tests"])).hexdigest(),
                        "tests_diff_base_T_sha256": hashlib.sha256(subprocess.check_output(["git", "-C", str(W), "diff", BASE, TEST, "--", P + "gmid_engine/tests"])).hexdigest()},
             "red": {"count": len(red), "types": types, "mss_fixture_excluded": len(mss), "base_green_new": 7}, "retired_tests_file": P + "gmid_engine/tests/RETIRED_TESTS_it2c.md",
             "collect_views_private_call": "test_icm_config.py _ota_views: 비공개 collect_views·net_model 호출, A-83 지시대로(기록만)"}

record = {
    "id": ID, "spec_card": "docs/02-design/specs/%s.spec.md" % ID, "evidence_type": "red-green",
    "base_commit": BASE, "test_commit": TEST, "code_commit": CODE,
    "red": {"test_ids": [P + r["id"] for r in red], "failure_hashes": [fhash(P + r["id"], r["exc"]) for r in red]},
    "checks": checks,
    "reproduced_numbers": [
        {"name": "card test 수", "value": card[0], "command": "scripts/run_head.py iso res/head card"},
        {"name": "card test 실패 수", "value": card[1], "command": "scripts/run_head.py iso res/head card"},
        {"name": "tests/structure 수", "value": structure[0], "command": "scripts/run_head.py iso res/head structure"},
        {"name": "ratchet new 수", "value": 0, "command": "tests/structure/test_g8_baseline.py::test_rule_g8_baseline_ratchet"},
        {"name": "ratchet stale 수(줄인 뒤)", "value": 0, "command": "scripts/apply_baseline.py 뒤 같은 test"},
        {"name": "canonical_order 수", "value": canon[0], "command": "scripts/run_head.py iso res/head canon"},
        {"name": "2회로 연기 수", "value": smoke_before[0], "command": "--run-slow -k folded_cascode or ngcc_3stage_ff, stage_b·s0·g10"},
        {"name": "기준선 재측정 전 s0 실패 수", "value": smoke_before[1], "command": "같은 연기"},
        {"name": "기준선 재측정 후 연기 실패 수", "value": smoke_after[1], "command": "scripts/apply_baseline.py 뒤 같은 연기"},
        {"name": "영향 파일 옛 test 수", "value": impacted[0], "command": "jobs2 impacted"},
        {"name": "red 수", "value": len(red), "command": "scripts/run_red.py base red.jsonl plug iso"},
        {"name": "손 뮤턴트 생존 수", "value": len(surv), "command": "scripts/mutate.py mut mutations.jsonl"},
        {"name": "거부 경로 직접 수", "value": len(rej) + len(rej2), "command": "scripts/test_zz_reject.py, test_zz_reject2.py"},
        {"name": "cert 같음 사례 수", "value": cert_ok, "command": "scripts/test_zz_rename.py"},
        {"name": "독립 풀이 끝 차 최대 V", "value": worst_end, "command": "scripts/test_zz_audit_probe.py test_flow"},
        {"name": "측정 구성 두 블록 비용 비 folded", "value": ratio["folded_cascode"], "command": "scripts/test_zz_audit_probe.py test_flow cProfile"},
        {"name": "측정 구성 두 블록 비용 비 common_gate", "value": ratio["common_gate_amplifier"], "command": "scripts/test_zz_audit_probe.py test_flow cProfile"},
        {"name": "기준선 tables 변화 행 수", "value": len(causes), "command": "scripts/test_zz_remeasure.py + apply_baseline.py"},
    ],
    "approvals": [],
    "auditor_run": {
        "time": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "worktree": str(W).replace("\\", "/"),
        "commands": [
            "V1: 전체 실행 안 함(임시 규칙 O-229), 범위 실행 = python scripts/run_head.py iso res/head (card, structure, canon, smoke)",
            "git clone --no-hardlinks --no-local <worktree> la1s_it2c_audit/iso; git -C iso remote remove origin (mut·base 도 같은 방식, base 는 clone -n 뒤 detached 4d39eaf5)",
            "python scripts/driver.py jobs (test_zz_remeasure 11회로 head·base, test_zz_audit_probe, run_red, mutate; OPENBLAS_NUM_THREADS=1, 프로세스 하나씩, 2 GB 아래면 자기 자식 정지·재개)",
            "python scripts/apply_baseline.py iso res; python scripts/run_head.py iso res/after smoke,structure",
        ],
    },
}
out = W / ".ai/verification" / (ID + ".json")
out.write_bytes(json.dumps(record, ensure_ascii=False, indent=1).encode("utf-8"))
ev = W / ".ai/verification" / ID
(ev / "scripts").mkdir(parents=True, exist_ok=True)
(ev / "base_check.json").write_bytes(json.dumps(stale_doc, ensure_ascii=False, indent=1).encode("utf-8"))
for f in ("run_head.py", "driver.py", "mutate.py", "run_red.py", "apply_baseline.py", "build_record.py", "test_zz_audit_probe.py", "test_zz_remeasure.py", "test_zz_reject.py", "test_zz_reject2.py", "test_zz_rename.py", "test_zz_a8.py", "test_zz_we.py", "red_cap.py"):
    shutil.copy(T / "scripts" / f, ev / "scripts" / f)
for f in ("mutations.jsonl", "reject.jsonl", "reject2.jsonl", "we.jsonl", "cause_table.json", "a8_mut.jsonl", "a8_base.jsonl", "rename_mut.jsonl", "rename_base.jsonl", "red.jsonl"):
    shutil.copy(R / f, ev / f)
phys_keep = [x for x in (R / "flow2_head.jsonl").read_text(encoding="utf-8").splitlines() if '"case": "eval"' not in x]
(ev / "probes_head.jsonl").write_bytes(("\n".join(phys_keep) + "\n").encode("utf-8"))
print("written", out, "mem_low", mem_low, "ratio", ratio, "worst", worst_end, worst_kcl, worst_cs, "dev_mm", dev_mm["cnr_ota"], "p", p_same, p_n, p_same_b, node_mm_b, "types", types)
