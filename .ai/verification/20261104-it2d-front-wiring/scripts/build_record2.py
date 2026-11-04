"""IT-2d·IT-2e 판정 기록 작성(BOM 없는 UTF-8). 인자: 임시 루트, audit worktree."""
import datetime, glob, hashlib, json, shutil, subprocess, sys
import xml.etree.ElementTree as ET
from pathlib import Path

T, W = Path(sys.argv[1]), Path(sys.argv[2])
R = T / "res" / "i2"
rev = lambda x: subprocess.check_output(["git", "-C", str(W), "rev-parse", x], text=True).strip()   # noqa: E731
HEAD = rev("d5f5b8e6")
P = "skills/analog-gmid-design/"
assert rev("HEAD") == HEAD


def suite(n):
    root = ET.parse(R / (n + ".xml")).getroot()
    s = root if root.tag == "testsuite" else root[0]
    return int(s.get("tests")), int(s.get("failures")) + int(s.get("errors"))


card, structure, canon, smoke = suite("card"), suite("structure"), suite("canon"), suite("smoke")
assert card == (453, 2) and structure == (171, 0) and canon == (12, 0) and smoke == (23, 0), (card, structure, canon, smoke)


def fhash(tid, exc):
    return hashlib.sha256(("%s\n%s" % (tid, exc)).encode("utf-8")).hexdigest()


def red(name):
    rows = [json.loads(x) for x in (R / name).read_text(encoding="utf-8").splitlines() if x.strip()]
    out = [(r["id"], r["exc"]) for r in rows if r["outcome"] == "failed"]
    out += [(r["id"], "builtins.ImportError") for r in rows if r["outcome"] == "collect_error"]
    types = {}
    for _i, e in out:
        k = e.rsplit(".", 1)[-1]
        types[k] = types.get(k, 0) + 1
    return out, types, sum(r["outcome"] == "passed" for r in rows)


red_d, types_d, _ = red("red_d.jsonl")
red_e, types_e, _ = red("red_e.jsonl")
assert len(red_d) == 69 and len(red_e) == 31, (len(red_d), len(red_e))
mut = [json.loads(x) for x in (R / "mutations.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
mut = [m for m in mut if "mut" in m]
assert all("error" not in m for m in mut) and len(mut) == 22
surv = [m["mut"].split()[0] for m in mut if not m["killed"]]
assert surv == ["D4", "D15", "E7"], surv
rej = [json.loads(x) for x in (R / "reject3.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
assert all(r["ok"] for r in rej) and len(rej) == 13
rm = [json.load(open(p, encoding="utf-8")) for p in glob.glob(str(R / "rm" / "*.json"))]
assert len(rm) == 11 and all(d["diff"] == [] and d["bit_same_a"] and d["bit_same_b"] for d in rm)
flow = {}
for x in (R / "flow.jsonl").read_text(encoding="utf-8").splitlines():
    d = json.loads(x)
    flow[d["circuit"]] = d
n = flow["nmcnr_amplifier"]
assert n["calls"]["icm"] == 36 == n["calls"]["eval"] and n["calls"]["bad"] == 0 and flow["folded_cascode"]["calls"]["icm"] == 0
e3 = [json.loads(x) for x in (R / "e3same.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
assert all(r["fp_same"] and r["line_same"] for r in e3)
diag = [json.loads(x) for x in (R / "e3diag.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
assert all(len(r["diff"]) == 2 and not r["only_a"] and not r["only_b"] for r in diag)
assert {r["diff"][0][0].split(",")[-1].strip(" ')") for r in diag} == {"junction_source"}

HOLD_D = "미완료(보류 다리: 13회로 값 변화표·용량만 결측 봉인점 수·ff_gm_ratio 표기·SPICE, O-225·A-5·A-7, 통과로 세지 않음)"
HOLD_E = "미완료(보류 다리: 13회로 바뀐 실패 줄 수, O-225·A-7, 통과로 세지 않음)"
RAN = "잰 범위 = 통합 병합본 %s(격리 복제본): 두 card test·영향 test 15파일 %d개 실패 %d, tests/structure %d 실패 0(래칫 new 0·stale 0, 규칙 H 1 deselected), canonical_order %d 실패 0, 2회로 연기 stage_b·s0·g10 %d 실패 0, 기준선 11회로 재측정 차이 0" % (HEAD[:8], card[0], card[1], structure[0], canon[0], smoke[0])
MAJOR = ("Major-1(필수 test 실패, 엔진 결함 아님): search/test_it2e_partial_snapshot.py::test_it2e_s3_failure_line_fp_parent_independent[dc_seal_kcl, dc_seal_report] 2건 FAILED, ra.partial.fp != rb.partial.fp. "
         "원인 실측(e3diag.jsonl): 두 부분 스냅샷의 필드 차이는 graph/kernel junction_source·mismatch_source 두 칸의 pdk_decl sha256 뿐이고 writer·block_versions·나머지 필드는 같다. test 가 `_failed(tmp_path/\"a\")`·`_failed(tmp_path/\"b\")`로 PDK 선언을 자리마다 새로 써서(`write_decls(tmp/\"pdk\")`) 선언 sha 가 달라진다. "
         "같은 자리(tmp_path/a 를 지우고 다시)로 만들면 단언 그대로 fp·S3 줄 지문 모두 같다(e3same.jsonl 2/2). 처리: test 주체가 두 case 에 같은 pdk·rule 을 넘긴다(build_case 인자 있음). 판정자는 고치지 않았다. 엔진 코드 수정 불필요. 이 test 는 코드 머리 8b9e861d(엔진 동일)에서도 같은 이유로 깨지는 값이고 dispute 없이 넘어왔다.")
COMMON = "기준선: 11회로 재측정 차이 0(사슬 두 번 비트 동일, IT-2c 값 그대로), fixture 변경 0. 메모리 2 GB 아래 1회 자기 프로세스 정지·재개."
checks_d = {
    "V1": {"verdict": "N/A", "basis": "전체 test 안 돌림, 임시 규칙 O-229. " + RAN + ". 실패 2 는 IT-2e 몫(그 기록 V2). 그 밖 test 는 통과로 세지 않는다."},
    "V2": {"verdict": "PASS", "basis": "red: 엔진 0e6449f7(IT-2c 판정 머리) + 머리 test 트리 d5f5b8e6 에서 %d %s(test_icm_window 수집 ImportError 1 = 신규 함수, TypeError 16 = ls_swing 새 서명). base green 새 test 5 나열: g2_no_old_front_names, g2_saturation_window 자리, b77b 저항 결측, b77d 새 code 0, registry ff_gm_ratio -- 회귀 보호(interface green 규칙), 같은 id 에 red 사례 있음. green: IT-2d test 병합본 전부 통과. 역할 분리: 70325cd6 test 0 파일, e12f5f60·9798e5c1 엔진 0 파일." % (len(red_d), json.dumps(types_d))},
    "V3": {"verdict": "PASS", "basis": "손 뮤턴트 15(scripts/mutate2.py): D1~D3·D5~D14 kill, 생존 D4·D15. D4 어휘 밖 영역 ValueError, D15 V_cm None 불일치 ValueError 는 test 없음(minor), 직접 호출로 거부 확인(reject3.jsonl)."},
    "V4": {"verdict": "PASS", "basis": "oracle 대조: T-IW 예시 0.90/0.34/1.19 -> margin 0.29, icmr 0.85 손 값. T-M1 cfg V_cm 손 식과 보고 window·v_icm 비교. T-B77a 커패시터 값만 다른 대조 비트 동일(용량이 DC 망에 안 든다는 불변식). T-O215 영역 행 창 값. 판정자 독립 재계산: nmcnr_amplifier 실회로 36평가 모두 icmr = hi-lo, margin = min(...) 비트 일치(flow.jsonl bad 0). 피검 함수를 기대값에 쓰지 않음."},
    "V5": {"verdict": "PASS", "basis": "A-85 약화 아님. D1 `node_v=()`로 node_v_missing 재현, 옛 전제(입력 인자)만 소멸. D2 input_dc_v=0.6: 구성 None 갈래 2 icm_inputs_unsupported 로 파이프라인이 실제로 닿고 code·definitional·포트 셋 단언 유지, 미선언은 DEC-106 test_writer_plan 이 그대로 지킴, 뜻 유지(M: D8·D11 kill). D3 보고 키 추가 거부(값 사본 금지), 같은 칸 비교는 T-M1(보고 window·v_icm == cfg)과 T-F(판정 값·front 행 == 손 margin)로 유지. 폐기: test_two_polarity_input_empty_window_negative(입력 창 삭제), test_undefined_codes_shared_by_three_metrics -> swing_only(재명명) -- RETIRED 목록에 없음(minor), 빈 창은 음수 폭 대신 unmeasured + unmeasured_front 분리로 fail-closed 유지."},
    "V6": {"verdict": "PASS", "basis": "tests/structure %d 통과, 래칫 new 0·stale 0. 회로 이름 0, 광범위 except 0, 엔진 추가에 cache·memo·dict 슬롯 0(diff grep). `RESOLUTION_ENDS = 1 + 1`, DOMAIN_DC·SS 문자열 지역 상수는 minor(`core.units.DOMAINS` 어휘 재선언). 규칙 H 새 위반 0(test_icm_window 짝). rule 파일 변경 0, structure.json diff 0." % structure[0]},
    "V7": {"verdict": "PASS", "basis": "IT-2c 조건부 항목 닫음: `node.dc_window_cfg`(_icm_ports: input_status·tol_v 읽음)·`graph.icm_config`(_swing)가 metrics_aux READS 에 있고 실회로 nmcnr_amplifier 36평가 36회 실제 호출, 값 소비 확인. folded_cascode 는 ICMR·스윙 요청이 없어 0회(요청 구동). 필드 수 신규 0 / 소비자 0 필드 0 / 정본 우회 의심 0(세 metric 산술 = V_cm 칸뿐, T-M3·D9 kill) / KVL·KCL 미적용 0 / graph 밖 저장 0. 칸 수준 minor: IcmPort.v·lo·hi 와 cfg lo·hi 는 엔진 소비 0, 보고 키 불변이라 '보고 열'에도 안 나감(interface 문언과 다름, S3 스냅샷 JSON 출력만). swing_icmr 보고 window·v_icm·required_input_cm_v 는 graph.metrics_aux 안 V_cm 칸 사본(기존 키, interface 불변 조항, LA-1 재점검). IcmWindow 는 _swing 안 반환 전용, 필드 아님. MetricSignature.domain 소비자 = metrics_aux 하나 + catalog 검증, search 는 domain 안 읽음(relabel 파급 0, grep)."},
    "V8": {"verdict": "PASS", "basis": "폴백 0. 거부 13건 직접 계약대로(reject3.jsonl): 어휘 밖 영역 ls·geom ValueError, input_dc 어휘, 구성 None + undefined 빈 값, 포트 0, 측정됐는데 V_cm None, 미측정 numeric. 구성 불일치 ValueError 는 CANDIDATE_FAILURE 밖이라 실행 중단 = fail-closed, 불변식 깨짐 표시로 합당. IcmPort.missing \"window\" 는 사유 문자열뿐, code 는 input_window_unmeasured, 소비 없음(detail 기록)."},
    "V9": {"verdict": "PASS", "basis": "물리 정합: 세 metric = graph.icm_config V_cm(DC 풀이 양)만 입력, lo·hi 산술 0(AST·D9). ls_swing 입력 제거로 잃은 정의: no_input_port -> 구성 갈래 view_required(입력 0 은 로더 거부), 입력 node_v_missing -> 대상 없음, sat_unavailable -> cfg unmeasured numeric, 음수 폭 빈 창 -> unmeasured(front 에서 분리, kernel unmeasured_front), 봉인점이 창 밖이면 margin 음수 유지(직접 -0.1), 경로 합 창은 O-205 로 영역 행 창 대체 -- 잃은 정의 0, swing 값 불변(기준선·toy). relabel: offset·mirror·스윙·ICMR = dc 는 용량 값만 바꾼 대조 비트 동일(T-B77a), ff_gm_ratio = ss(O-112, 표기 재검토는 보류 A5). B77 _unavailable: dc = ss_nodal Undefined(저항 결측) 만, ss = 결측 하나라도, 어휘 밖 ValueError, 전달 뷰 보고 결측 시 없음 -- fail-closed(D1·D2·D3·D5 kill). 실회로 nmcnr: servo, V_cm [0.0487, 1.4413] V."},
    "V10": {"verdict": "N/A", "basis": "spec '재현할 수치' 없음. " + HOLD_D + ". " + COMMON},
}
checks_e = {
    "V1": {"verdict": "N/A", "basis": "전체 test 안 돌림, 임시 규칙 O-229. " + RAN + "."},
    "V2": {"verdict": "FAIL", "basis": MAJOR + " red: 엔진 9798e5c1(IT-2d 머리) + 머리 test 트리에서 %d %s, 해당 2건 포함. base green 21 = attach_adds_no_block_calls·parentless_unchanged·coverage_violation·dc_seal_report 사례(마지막 블록이라 keep 과 범위가 같음)·violation_keeps_report -- 회귀 보호. 나머지 card test 통과, 역할 분리 8b9e861d test 0 파일, 5b00180b 엔진 0 파일." % (len(red_e), json.dumps(types_e))},
    "V3": {"verdict": "PASS", "basis": "손 뮤턴트 7: E1~E6 kill, E7(보고서 블록 실패 부착 옛 꼴) 생존 = 그 자리에서는 keep 이 이미 같은 범위라 값이 같은 동치 뮤턴트."},
    "V4": {"verdict": "PASS", "basis": "oracle 변성: parent 없는 대조 fp == parent 경로 fp(test_size_and_seal 13+ 사례 통과, 같은 ctx 선언), writers_in_scope 손 집합, base None TypeError. 유효 조건 (가)(나) test 안 단언. S3 줄 사례만 Major-1 하네스 문제."},
    "V5": {"verdict": "PASS", "basis": "기준 약화 없음, 이 card 는 기존 test 변경 0(추가만). 실패 test 를 판정자가 고치거나 빼지 않음."},
    "V6": {"verdict": "PASS", "basis": "tests/structure %d 통과, 래칫 new 0. T-E6 정의 자리 1·호출 자리 AST 통과. 규칙 H 새 위반 1 = tests/search/test_it2e_partial_snapshot.py 원본 없음 orphan(minor, 기본 deselected). rule 파일 변경 0." % structure[0]},
    "V7": {"verdict": "PASS", "basis": "writers_in_scope 소비자 = kernel_run keep·부착, seal 부착 3, seal_versions coverage. 규칙 5 파생과 같음: keep 집합 = base writer ∪ steps ∪ later ∪ SEAL_ITEM_BLOCKS 로 옛 식과 동일(diff), 봉인 4 foreign = used - 같은 함수, overlap 은 그대로 base·called 교집합(서로소 단언 유지, coverage 위반 픽스처 FAIL 유지). 새 필드·cache·값 사본·블록 호출 0(attach_adds_no_block_calls 통과). 부분 스냅샷 소비자 = kernel._record snapshot_fp 뿐, 판정·재사용 입력 0(grep, N6.3 (ii)). 필드 수 0 / 소비자 0 0 / 정본 우회 0 / KVL·KCL 해당 없음 / graph 밖 저장 0."},
    "V8": {"verdict": "PASS", "basis": "폴백 0. writers_in_scope(None) TypeError 직접 확인. seal_dc 앞 블록 = calls 생성식(커널 steps·later + 이미 돈 봉인 항목), 실패 블록 제외 맞음. dc_seal_report 범위: 블록 자체 실패는 제외, 위반 예외는 보고서 포함 -- interface '봉인 위반 경로: dc_seal_report 필드까지 남음'과 일치(E3 kill)."},
    "V9": {"verdict": "N/A", "basis": "도입 해당 없음: 물리 값 변경 0, 부분 스냅샷 집합 규칙뿐. G-10 계수 변화 0(T-E8, 연기 g10 통과)."},
    "V10": {"verdict": "N/A", "basis": "spec '재현할 수치' 없음. " + HOLD_E + ". " + COMMON},
}


def record(id_, base, test, code, reds, checks, numbers):
    return {"id": id_, "spec_card": "docs/02-design/specs/%s.spec.md" % id_, "evidence_type": "red-green", "base_commit": rev(base), "test_commit": rev(test), "code_commit": rev(code),
            "red": {"test_ids": [P + i for i, _e in reds], "failure_hashes": [fhash(P + i, e) for i, e in reds]},
            "checks": checks, "reproduced_numbers": numbers, "approvals": [],
            "auditor_run": {"time": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "worktree": str(W).replace("\\", "/"),
                            "commands": ["V1: 전체 실행 안 함(임시 규칙 O-229), 범위 실행 = python scripts/driver.py res/i2/jobs.json",
                                         "git clone --no-hardlinks --no-local <worktree> la1s_it2c_audit/i2; git -C i2 remote remove origin (m2·r2 도 같은 방식)",
                                         "python scripts/driver.py res/i2/jobs2.json (structure 재실행, test_zz_remeasure 11회로, test_zz_i2flow, run_red2 2회, mutate2)",
                                         "PROBE_OUT=... pytest test_zz_e3diag.py, test_zz_e3same.py, test_zz_reject3.py"]}}


common_numbers = [
    {"name": "test 수(두 card + 영향)", "value": card[0], "command": "res/i2/jobs.json i2_card"},
    {"name": "test 실패 수", "value": card[1], "command": "res/i2/jobs.json i2_card"},
    {"name": "tests/structure 수", "value": structure[0], "command": "res/i2/jobs2.json i2_structure2"},
    {"name": "ratchet new 수", "value": 0, "command": "test_rule_g8_baseline_ratchet"},
    {"name": "canonical_order 수", "value": canon[0], "command": "res/i2/jobs.json i2_canon"},
    {"name": "2회로 연기 수", "value": smoke[0], "command": "res/i2/jobs.json i2_smoke"},
    {"name": "기준선 차이 회로 수", "value": 0, "command": "test_zz_remeasure 11회로"},
]
EV = W / ".ai/verification/20261104-it2d-front-wiring"
(EV / "scripts").mkdir(parents=True, exist_ok=True)
rd = record("20261104-it2d-front-wiring", "0e6449f7", "9798e5c1", "70325cd6", red_d, checks_d, common_numbers + [{"name": "red 수", "value": len(red_d), "command": "scripts/run_red2.py r2 0e6449f7"}, {"name": "실회로 icm 호출 수 nmcnr", "value": 36, "command": "scripts/test_zz_i2flow.py"}])
re_ = record("20261104-it2e-partial-snapshot", "9798e5c1", "5b00180b", "8b9e861d", red_e, checks_e, common_numbers + [{"name": "red 수", "value": len(red_e), "command": "scripts/run_red2.py r2 9798e5c1"}, {"name": "같은 선언 자리 지문 같음 사례 수", "value": 2, "command": "scripts/test_zz_e3same.py"}])
(W / ".ai/verification/20261104-it2d-front-wiring.json").write_bytes(json.dumps(rd, ensure_ascii=False, indent=1).encode("utf-8"))
(W / ".ai/verification/20261104-it2e-partial-snapshot.json").write_bytes(json.dumps(re_, ensure_ascii=False, indent=1).encode("utf-8"))
for f in ("driver.py", "mutate2.py", "run_red2.py", "build_record2.py", "prep_i2.py", "prep_i2b.py", "test_zz_i2flow.py", "test_zz_e3diag.py", "test_zz_e3same.py", "test_zz_reject3.py", "test_zz_remeasure.py"):
    shutil.copy(T / "scripts" / f, EV / "scripts" / f)
for f in ("mutations.jsonl", "reject3.jsonl", "flow.jsonl", "e3diag.jsonl", "e3same.jsonl", "red_d.jsonl", "red_e.jsonl"):
    shutil.copy(R / f, EV / f)
print("ok", len(red_d), len(red_e), surv)
