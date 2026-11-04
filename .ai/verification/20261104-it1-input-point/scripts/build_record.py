"""IT-1 판정 기록 작성. 인자: 임시 루트, audit worktree."""
import datetime
import glob
import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

T, W = Path(sys.argv[1]), Path(sys.argv[2])
R = T / "res"
ID = "20261104-it1-input-point"
BASE = subprocess.check_output(["git", "-C", str(W), "rev-parse", "d3590e7b"], text=True).strip()
TEST = subprocess.check_output(["git", "-C", str(W), "rev-parse", "4562d53e"], text=True).strip()
CODE = subprocess.check_output(["git", "-C", str(W), "rev-parse", "888d28a8"], text=True).strip()
HEAD = subprocess.check_output(["git", "-C", str(W), "rev-parse", "HEAD"], text=True).strip()
assert HEAD.startswith("f2278b9a")


def fhash(tid, exc):
    return hashlib.sha256(("%s\n%s" % (tid, exc)).encode("utf-8")).hexdigest()


P = "skills/analog-gmid-design/"
rows = [json.loads(x) for x in (R / "red.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
failed = [r for r in rows if r["outcome"] == "failed" and "test_stage_a_library" not in r["id"]]
excluded = [r["id"] for r in rows if r["outcome"] == "failed" and "test_stage_a_library" in r["id"]]
assert len(failed) == 52 and len(excluded) == 3

# head 결과(junit)
green, fails_head = set(), []
tot = {"card": [0, 0], "structure": [0, 0], "smoke_before": [0, 0]}
for p in glob.glob(str(R / "head" / "*.xml")):
    name = Path(p).stem
    root = ET.parse(p).getroot()
    suite = root if root.tag == "testsuite" else root[0]
    grp = "structure" if name == "structure" else ("smoke_before" if name in ("integration_test_stage_b_library", "integration_test_s0_layer_9circuits", "integration_test_g10_no_recompute_9circuits") else "card")
    for tc in suite.iter("testcase"):
        tot[grp][0] += 1
        bad = tc.find("failure") is not None or tc.find("error") is not None
        tid = tc.get("classname").replace(".", "/") + ".py::" + tc.get("name")
        if bad:
            tot[grp][1] += 1
            fails_head.append(tid)
        else:
            green.add(tid)
not_green = [r["id"] for r in failed if r["id"] not in green]
assert not not_green, not_green
assert tot == {"card": [841, 1], "structure": [171, 1], "smoke_before": [23, 3]}, tot
s0_after = ET.parse(R / "s0_after.xml").getroot()
s0_suite = s0_after if s0_after.tag == "testsuite" else s0_after[0]
assert (s0_suite.get("tests"), s0_suite.get("failures"), s0_suite.get("errors")) == ("11", "0", "0")

types = {}
for r in failed:
    n = r["exc"].rsplit(".", 1)[-1]
    types[n] = types.get(n, 0) + 1

mut = {}
for f in ("mutations.jsonl", "mutations2.jsonl"):
    for x in (R / f).read_text(encoding="utf-8").splitlines():
        d = json.loads(x)
        if "error" not in d:
            mut[d["mut"].split()[0]] = d
del mut["M10"]                     # M10 은 내 뮤턴트가 AST 검사 이름을 우회한 꼴이라 무효, M10b 로 다시 쟀다
surv = sorted(k for k, d in mut.items() if not d["killed"])
killed = sorted(k for k, d in mut.items() if d["killed"])
assert len(mut) == 17 and surv == ["M12", "M13", "M14", "M17"], (len(mut), surv)
assert mut["R1"]["killed"] and mut["R1"]["res"][0]["n_fail"] == 4

# node_voltage_targets_v 발동 수
lib = W / "skills/analog-gmid-design/assets/library"
target_on_port = []
n_spec = 0
for sp in sorted(lib.glob("*.sizing_spec.json")):
    n_spec += 1
    spec = json.loads(sp.read_text(encoding="utf-8"))
    tg = {k for k in (spec.get("human", {}).get("node_voltage_targets_v") or {}) if not k.startswith("_") and k != "pending"}
    topo = json.loads((lib / (sp.name.replace(".sizing_spec.json", ".topology.json"))).read_text(encoding="utf-8"))
    ports = {k for k, v in topo.get("ports", {}).items() if isinstance(v, dict) and v.get("direction") == "input"}
    if tg & ports:
        target_on_port.append(sp.name)
assert n_spec == 13

fixture_diff = subprocess.run(["git", "-C", str(T / "iso"), "diff", "--", P + "gmid_engine/tests/integration/fixtures/u17_1b_s0_baseline.json", P + "gmid_engine/tests/structure/g8_baseline.json"], capture_output=True).stdout.replace(b"\r\n", b"\n")
fixture_sha = hashlib.sha256(fixture_diff).hexdigest()

HOLD = "미완료(보류 다리: 13회로 변화표·IT-0b·SPICE, 채울 card = EO-1·OP-5·CL-1, base = %s)" % BASE
MAJOR1 = "Major-1 ratchet new = 1: ('g8_attr_container', 'sizing/block_columns.py', '_Circuit.mates', 1). 코드 2b7c7c71 이 _Circuit 에 새 dict 칸을 넣었다(interface A3 'new 0', spec '새 dict·context 슬롯 0'). 행 추가는 criteria_weakened 라 안 했다. 재현: pytest tests/structure/test_g8_baseline.py::test_rule_g8_baseline_ratchet"
MAJOR2 = "Major-2 test_writer_plan.py::test_it2b_os_k_no_same_dc_edge_between_input_ports FAILED(StructureUnresolvedError input_cm_undefined). A-42·커밋 4562d53e 제목이 'os_k 폐기'인데 test 가 그대로 남았다. 엔진 동작이 맞고(역할 x 입력 둘 = T-1e 정지) test 가 낡았다. test 주체가 지워야 한다"
MAJOR3 = "Major-3 새 S1v 필드 넷(diode_nodes·composite_mos·composite_bundles·composite_internal) 실제 소비자 0. coupling_vars 는 READS 에 적고 model 에 채우지만 _k3·_k7·_k8·_cd_reach 가 쓰는 칸은 mos·rails·by_source·mos_by_name 뿐이고 column_block_map 은 s1 을 받는다. 뮤턴트 M17(model = net_index(s1), READS 유지)이 test_coupling_vars 80·test_stage_a_library 15 전부 통과로 생존. 쓰는 곳 blocks·cells·drive_kind·stage_bfs·view_analysis 는 s1v_fields 안 model 을 읽어 필드를 안 읽는다. 계획 N3.3 B4·design 40 S1v 행이 정한 소비자 전제가 틀렸다(값 영향 0, writer 하나는 지킴, 재작성 범위는 계획부터)"

checks = {
    "V1": {"verdict": "N/A", "basis": "전체 test 안 돌림, 임시 규칙 O-229, 잰 범위 = card test 24 파일 841개(실패 1), tests/structure 171개(실패 1, deselected 1), 2회로 연기 stage_b 10·s0 11·g10 2(기준선 재측정 전 s0 실패 3, 후 0). 그 밖 test 는 통과로 세지 않는다. 파일마다 프로세스 하나, OPENBLAS_NUM_THREADS=1, 격리 복제본 f2278b9a."},
    "V2": {"verdict": "FAIL", "basis": "red: base %s 엔진 + 동결 test %s(엔진 diff 0) 25 파일에서 red 52 = %s. test_stage_a_library 실패 3(cnr·erfc·r2r)은 입력 점·g = s 와 무관한 단계 A 정지(exit 7) 실패라 red 에서 뺐다(병합본 통과, 원인은 master 병합분으로 추정, 미분석). green: 병합본에서 red 52 전부 통과. FAIL 사유: %s" % (BASE[:8], TEST[:8], json.dumps(types, ensure_ascii=False), MAJOR2)},
    "V3": {"verdict": "PASS", "basis": "mutate_changed.py 는 대상이 assets/tests 라 안 썼다. 손 뮤턴트 17(복제본 임시 수정, 커밋 없음, scripts/mutate.py): killed 13 = %s, 생존 4 = %s. 새 거부 경로 input_cm_undefined: R1 정지 제거 -> T-1e 4사례 전부 실패, R2 role 무시 -> 6 실패. KVL: M5 짝 포트 +0.05 V -> T-1h 2 실패. rule_hash: R16 재기록 되돌림 -> T-RH 실패. 생존 M12(SCC 뿌리 짝 의존)·M13(창 짝 제약)·M14(fd y 스텝) = test 빈틈 minor, M13 은 탐침 p5 로 head 동작 정상(constraints 2). M17 = Major-3." % (",".join(killed), ",".join(surv))},
    "V4": {"verdict": "PASS", "basis": "test_lint.py 안 돌림: 대상이 assets/tests 라 공허, DEC-86 merge_gate 미사용(UNJUDGED 아님, 대조는 손으로). oracle 대조: T-1a G = P-t 둘·vb-F·pb3-F·pb4-F, V6 E5 C2 -> 순환 1 일치. T-1b V7 E6 C2 -> 1 일치. T-1c V4 E4 C1 -> 1, y = {o1,o2} 일치. T-1i V8 E8 C2 -> 2, cycle_vgs 하나 + parallel 하나 일치. T-1f θ 15 = L5 C2 I2 ln3 y3, DOF 17·5·5·12 일치(판정자 재유도, 변수 V:inn 하나 제거, 등식 수 불변). T-5a 넷 동등 판정, 평행 단순 그래프 순환수 불변 일치. T-5b 자기 고리 1 = fixed_vgs, ln_idu 성분 없음 일치. T-1h 두 포트 같은 전압, y=0.5 창 중점, F toy V=0.6 일치. T-6a 손 정의 일치. A8: 작성자의 gvgs_cycles 본문 1회 열람(자기 보고)은 기대값에 복사 흔적 없음: 칸 판정이 넷 동등이라 노드 비교와 다르고 계약 문장에서 재유도된다. 기대값을 피검 함수로 만든 자리 0."},
    "V5": {"verdict": "PASS", "basis": "약화 없음, 기록할 항목: (1) T-1h 허용오차 1e-5 -> tol_V(약 781배) = 사용자 O-227 (3) 유지 결정. (2) 폐기 test 확인: k1·k2·pa·ring·dependent_count_ring·ds_flip_m1 정지·옛 stop 2건 = 전제가 DEC-106·O-210 RR-6 과 충돌, 대체 test 있음(T-1a/b/c/e/g/h/i, T-5a/b). 그 밖 삭제 test 0 중 os_k 는 폐기 미이행(Major-2). (3) 판정자 기준선 변경 diff sha256 = %s: u17_1b_s0_baseline.json 행 재측정(아래 V10)과 g8_baseline.json stale 1행(_Circuit.members, 옛 IT-1 이 지운 칸) 제거. new 행 추가 0(criteria_weakened 0)." % fixture_sha},
    "V6": {"verdict": "FAIL", "basis": "source_lint.py 안 돌림(대상 assets/tests, 공허). 구조 규칙 A~I·K·M·값 타입 위반 0, 회로 이름 0, 광범위 except 추가 0, 숫자 상수 추가 0(role 상수는 authoring 어휘 참조), 범위 밖 엔진 변경 0(card 커밋 16 파일 = spec 재작성 범위·소비자 표 안). FAIL 사유: " + MAJOR1},
    "V7": {"verdict": "FAIL", "basis": "reachability.py 안 돌림(공허). 손 판정 소비자: REL_INPUT_POINT = writer_plan·block_columns·scc_order·theta_schema·achievability·fd_jacobian, BRANCH_INPUT_CM_UNDEFINED = dc_writer_plan 정지, gate_source_same = dc_writer_plan READS(g = s 재판정 0). graph 수치: 새 필드 4 + 새 칸 1, 소비자 0 = 필드 4(칸 1 은 소비자 있음), 정본 우회 의심 0, KVL·KCL 관계 미적용 0, graph 밖 저장 자리 1(_Circuit.mates, 블록 수명 구조 색인, 값 사본 아님; scc_order 지역 변수 mates 는 세지 않음). 둘째 생산자 0: net_model( 호출 = s1v_fields 하나(M10b killed), 필드 writer = s1v_fields 하나. FAIL 사유: " + MAJOR3},
    "V8": {"verdict": "N/A", "basis": "도입 해당 없음: card diff 에 폴백·우회 경로 추가 0(diff 코드 읽기), 옛 정지 2개 삭제는 계약(DEC-106·O-210 RR-6), 새 정지 1개"},
    "V9": {"verdict": "PASS", "basis": "탐침(복제본, scripts/test_zz_audit_probe.py, probes.jsonl). p1 저항 부하 차동 toy: V(inp) = V(inn) = 1.3466953592937765(잔차 0), VGS(M1) = VGS(M2) = 0.6593376497806217, KCL t: 1e-5 + 1e-5 = 2e-5, 봉인 전 항목 통과. p2 비레일 g = s toy: fixed_vgs, ln_idu 성분 없음, VGS = 0.0, 봉인 9 거부(Mgs, 봉인 1~8 통과) = fail-closed, 판정 EO-1 까지 유지(interface 표지). p4 꼬리 W3: 뿌리 없이 inp vgs_gate·inn input_point known = inp(F 닿으면 KVL 종속). p5 n 포트에 채널: 창 constraints 2 = 짝 포트 제약 포함, n 포트 항목 없음. DC·AC 분리 위반 0. 물리 결정자 일치(DEC-106: 한 차동쌍 공통모드 변수 하나, DC 차는 설계 자유도 아님). 경계 minor: p3 아래 V10 끝. SPICE 다리 " + HOLD + ", 통과로 세지 않음."},
    "V10": {"verdict": "N/A", "basis": "spec '재현할 수치' 없음. 13회로 변화표·IT-0b·SPICE = " + HOLD + ". 기준선 재측정(O-225 보류 표지, 값 표 아님, 원인 칸 DEC-106, 격리 복제본, 사슬 두 번 비트 동일 7/7): current_reuse dof·schema·domain; folded dof·rungs·schema·domain; ngcc dof; nmcnr dof·rungs·schema·domain; r2r dof; two_stage dof·rungs·schema·domain; two_stage_sf dof·rungs·schema·domain. 무변화 4 = common_gate·pushpull·rfc·sf_pushpull. cnr·erfc 는 O-228 xfail 고정이라 안 쟀다. 행 근거(cause_table.json, master 8d77b801 엔진과 같은 키 대조): dof n_variables·n_equations 각 -1(옛 tie 등식 + V:n 변수 삭제), θ y:input_common_mode -> y:<p 포트>, 입력쌍 종속 cycle_vgs -> parallel_vgs, rungs = master 값 복귀. _IT1_DELTA = {} 도 master 원값 복귀와 맞음. minor 입력(LA-1 재점검): p3 차동 한 포트만 node_voltage_targets_v 선언이면 입력 점이 안 묶이고 둘째 포트가 vgs_gate 로 쓰여 ΔV 가 θ 함수(-8.1e-5 V 실측), 정지도 없음. library 발동 %d/13." % len(target_on_port)},
}

record = {
    "id": ID, "spec_card": "docs/02-design/specs/%s.spec.md" % ID, "evidence_type": "red-green",
    "base_commit": BASE, "test_commit": TEST, "code_commit": CODE,
    "red": {"test_ids": [P + r["id"] for r in failed], "failure_hashes": [fhash(P + r["id"], r["exc"]) for r in failed]},
    "checks": checks,
    "reproduced_numbers": [
        {"name": "card test 수", "value": tot["card"][0], "command": "scripts/run_tests.py iso res/head card"},
        {"name": "card test 실패 수", "value": tot["card"][1], "command": "scripts/run_tests.py iso res/head card"},
        {"name": "tests/structure 수", "value": tot["structure"][0], "command": "scripts/run_tests.py iso res/head structure"},
        {"name": "ratchet new 수", "value": 1, "command": "pytest tests/structure/test_g8_baseline.py::test_rule_g8_baseline_ratchet"},
        {"name": "ratchet stale 수(줄인 뒤)", "value": 0, "command": "scripts/apply_baseline.py 뒤 같은 test"},
        {"name": "2회로 연기 수", "value": tot["smoke_before"][0], "command": "--run-slow -k folded_cascode or ngcc_3stage_ff, stage_b·s0·g10"},
        {"name": "기준선 재측정 전 s0 실패 수", "value": tot["smoke_before"][1], "command": "같은 연기"},
        {"name": "기준선 재측정 후 s0 실패 수", "value": 0, "command": "scripts/apply_baseline.py 뒤 test_s0_layer_9circuits"},
        {"name": "red 수", "value": len(failed), "command": "scripts/run_red.py red_tree res/red.jsonl plug"},
        {"name": "손 뮤턴트 생존 수", "value": len(surv), "command": "scripts/mutate.py"},
        {"name": "입력 점 포트 전압 잔차 V", "value": 0.0, "command": "scripts/test_zz_audit_probe.py p1"},
    ],
    "approvals": [],
    "auditor_run": {
        "time": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "worktree": str(W).replace("\\", "/"),
        "commands": [
            "V1: 전체 실행 안 함(임시 규칙 O-229), 범위 실행 = python scripts/run_tests.py iso res/head all",
            "git clone --no-hardlinks --no-local <worktree> la1s_it1_audit6/iso; git -C iso remote remove origin (뮤턴트는 같은 방식 복제본 mut)",
            "python -m pytest gmid_engine/tests/<file> -q -p no:cacheprovider --junitxml (파일마다 프로세스 하나, cwd = iso/skills/analog-gmid-design, OPENBLAS_NUM_THREADS=1)",
            "python scripts/run_remeasure.py iso res/rm_head <11회로>; python scripts/run_remeasure.py base_master res/rm_base <7회로>",
            "python scripts/mutate.py mut res/mutations.jsonl; python scripts/run_red.py red_tree res/red.jsonl plug",
        ],
    },
}
out = W / ".ai/verification" / (ID + ".json")
out.write_bytes(json.dumps(record, ensure_ascii=False, indent=1).encode("utf-8"))

ev = W / ".ai/verification" / ID
(ev / "scripts").mkdir(parents=True, exist_ok=True)
for f in ("run_tests.py", "run_remeasure.py", "test_zz_remeasure.py", "mutate.py", "run_red.py", "apply_baseline.py", "build_record.py"):
    shutil.copy(T / f, ev / "scripts" / f)
shutil.copy(T / "plug" / "red_cap.py", ev / "scripts" / "red_cap.py")
shutil.copy(T / "mut/skills/analog-gmid-design/gmid_engine/tests/sizing/test_zz_audit_probe.py" if (T / "mut/skills/analog-gmid-design/gmid_engine/tests/sizing/test_zz_audit_probe.py").exists() else T / "test_zz_audit_probe.py", ev / "scripts" / "test_zz_audit_probe.py")
for f in ("red.jsonl", "mutations.jsonl", "mutations2.jsonl", "probes.jsonl", "cause_table.json"):
    shutil.copy(R / f, ev / f)
shutil.copy(R / "head" / "summary.jsonl", ev / "test_summary.jsonl")
print("written", out, "target_on_port", target_on_port, "fails_head", fails_head, "types", types, "killed", killed)
