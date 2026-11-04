# -*- coding: utf-8 -*-
import datetime, glob, json, os, shutil, subprocess
T = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7b_audit"
P = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op23_audit"
W = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-op7b-audit"
ID = "20261104-op7b"
R = f"{W}/.ai/verification/{ID}"
for s in ("measure", "tools"):
    os.makedirs(f"{R}/{s}", exist_ok=True)
open(f"{R}/.gitattributes", "w", newline="\n").write("* -text\n")
for n in ("a7_1.txt", "a7_3.txt", "a7_4.json", "a7_4b.json", "a7_6.txt", "a7_mut.json", "red.jsonl", "m/a7.json"):
    shutil.copyfile(f"{T}/out/{n}", f"{R}/measure/{os.path.basename(n)}")
for p in glob.glob(f"{T}/tools/*.py"):
    shutil.copyfile(p, f"{R}/tools/{os.path.basename(p)}")
shutil.copyfile(f"{P}/tools/redcap.py", f"{R}/tools/redcap.py")
# 7 bias 를 (회로 이름이 겹치는 R1·R2 도) 따로 대조
eq = {}
for rid in ("R1", "R2", "R3", "R4", "R5"):
    for p in glob.glob(f"{T}/out/run1/{rid}/o/*.sim.json"):
        b = os.path.basename(p)
        eq[f"{rid}/{b}"] = json.load(open(p, encoding="utf-8")) == json.load(open(f"{P}/out/run1/{rid}/o/{b}", encoding="utf-8"))
print(eq)
n_eq = sum(eq.values())
git = lambda *a: subprocess.run(["git", "-C", W, *a], capture_output=True, text=True, check=True).stdout.strip()
BASE, TEST, CODE = git("rev-parse", "377e2c58"), git("rev-parse", "73699801"), git("rev-parse", "29505b7a")
red = [json.loads(x) for x in open(f"{T}/out/red.jsonl", encoding="utf-8")]
ok = [x for x in red if x["exc"] in ("builtins.ImportError", "builtins.ModuleNotFoundError", "builtins.AssertionError")]
json.dump({"id": ID, "order": "순서 3 freeze", "isolation": f"{T}/iso (clone --no-hardlinks --no-local, origin 제거), 뮤턴트 {T}/iso_m, test 사본 {T}/iso_t",
           "freeze": {"test_end_commit_T": TEST, "test_commits": ["32362b67", "73699801"], "code_commits": ["29505b7a"], "note": "T 는 code 뒤다: dispute 2건(compat_sha256 기대값 전환 = spec 소비자 표대로, T7-10e 입력 교체 = 기대 코드 유지). 기준 약화 아님"},
           "base_commit": BASE, "red": {"collected": len(red), "counted": len(ok), "note": "base 코드 + T 판 새 test 세 파일. OracleError 1건은 허용 타입 밖이라 세지 않음. merge_gate 플러그인은 interface 에 '## 신규 시그니처' 절이 없어 판정자 플러그인 사용"}, "equivalence": "해당 없음"},
          open(f"{R}/base_check.json", "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
sections = {
 "verdict": "FAIL (Major 1)",
 "major": [{"id": "M-1", "what": "card test test_spiceinit_isolation.py 2/3 실패(T7-9a, T7-9b). 코드의 격리 동작 자체는 판정자 측정으로 맞다",
            "cause": ["(1) test log_of 가 status.log_path='bench.log' 를 cwd 기준으로 연다. FileNotFoundError. log_path 는 실행 폴더 기준 상대 경로이고(oracle_run.py:314-315, 출력 폴더 경로를 결과에 넣지 않음, D §6.1 출력 전용) test 쪽 결함이다(test 해석 H-15)",
                      "(2) log_of 만 고친 사본에서 T7-9b·9c 통과, T7-9a 는 assert status.error is None 에서 실패: sim_failed_other. 어댑터 __init__.py 의 present 가 MOS id 만 보므로 MOS 없는 저항 넷리스트는 V(a)=1 이 있어도 결과 없음으로 분류한다. interface T7-9a '결과 있음'과 어긋남. oracle_run 경로는 devices minItems 1 이고 R1~R5 status.error None 이라 닿지 않는다. test bench 에 MOS 를 넣거나 present 정의를 고치는 결정이 필요"],
            "repro": "pytest tests/adapters/ngspice/test_spiceinit_isolation.py; 사본 tools/patch_iso_test.py"}],
 "measures": {
  "A7-1": ["PASS", "T7 + OP-3 회귀 219 passed. base 코드 + 새 test red 10건"],
  "A7-2": ["PASS", "R1~R10 10/10 판정자 파일 LF ⊆ 선언 7개, 기록값 직접 일치 0(정의가 달라 비교 안 함이 맞음). 선언 compat default, 글 빈 값 sha e3b0c442 자기 일치"],
  "A7-3": ["FAIL(test) / 물리 PASS", "test 2 failed 1 passed(M-1). 판정자 변형: 독 HOME(hsa + echo 표지)에서 실행 폴더 파일이 있으면 표지 안 찍힘·default, SPICE_USERINIT_DIR 도 막음, None 도 빈 파일·default. 대조: 실행 폴더 파일 없으면 표지 찍힘·hs a"],
  "A7-4": ["PASS", f"R1~R5 7 bias 1회: rc 7/7, verdict 7/7, blockers 같음, pm_deg_raw 같음. sim 칸 차 6칸(끝자리, OP-3 때와 같은 칸), 데이터 파일 30개 기준선과 바이트 동일, 로그 8/8 default 문장, .spiceinit 8/8 빈 파일, compat_sha256 전부 e3b0c442. OP-3 판정 실행과 sim {n_eq}/{len(eq)} 동일, bench.cir 8/8 동일. 제외 칸 추가 0"],
  "A7-5": ["PASS", "bin_rule import 어댑터·subprocess·엔진 0, 키 리터럴 빈 값 0, compat_sha256 None 0, 엔진·assets diff 0"],
  "A7-6": ["PASS", "tests/structure 171 passed 1 deselected, g8 ratchet stale 0. X-13·test_verified_by 48 passed"],
  "A7-7": ["미측정", "2회로 연기 생략(엔진 diff 0, 브리핑 허용). 이름 불변성 test_canonical_order 도 생략. 통과로 세지 않음"],
  "A7-8": ["기록", "엔진 .py 시뮬레이터 이름: _helpers_bins 1, junction_cap 6, lut_parameters 1, noise_devices 1, verified_by 1(test 제외, B-5)"],
  "넘김": "13회로 비트 동일(B-4), test_independent(이번 미측정), 시스템 초기화 스크립트로 모드 바꾸기 직접 측정. 통과로 세지 않음"},
 "reject_paths_real_oracle_run": {"mode_unknown": "bin_rule_compat_mismatch 8b", "mode_default_text_hsa": "bin_rule_compat_mismatch 8b", "sha_self": "bin_rule_compat_mismatch 8b", "simulator_45": "bin_rule_undeclared why simulator", "model_set": "bin_rule_undeclared why model_set", "model_empty": "decl_invalid", "decl_file_{}": "decl_invalid", "decl_not_json": "decl_invalid", "no_field": "no_decl_ref", "field_{}": "descriptor_schema_invalid stage 2", "field_sha": "pdk_descriptor_stale ref bin_rule_decl stage 2", "control": "rc 0", "hsa_consistent": "rc 0 (선언대로 hsa)", "all_rejects_rc": 2, "sim_runs_in_rejects": 0},
 "physics": {"isolation": "막는다(A7-3 변형). 뮤턴트(.spiceinit 쓰기 삭제) + 독 HOME 으로 실제 oracle_run R1 -> bin_rule_compat_mismatch declared default actual hsa: 실행 뒤 대조가 실제 경로에서 닿는다",
             "mode_table": "측정값이다: 어댑터 run 으로 빈 글 -> 'Note: No compatibility mode selected!', 'set ngbehavior=hsa' -> 'Note: Compatibility modes selected: hs a'. 표와 같다",
             "cache_hit": "대조한다: 미스·적중 통과, 슬롯 로그를 hs a 로 바꾸면 적중에서 bin_rule_compat_mismatch. 모드만 다른 실행은 슬롯 2개(키 다름)",
             "values": "OP-3 와 같다(A7-4)", "definitions": "모드·묶음 LF·판 정의 D §16·§8.1 과 코드 일치"},
 "dispute": "2건 처리 맞음: test_result_contract:83 = spec 소비자 표대로, T7-10e 는 기대 코드 유지하고 입력을 8단계 규칙 (i)까지 가게 고침. 기준 약화 아님",
 "graph_single_source": {"new_graph_fields": 0, "engine_consumer_zero": 0, "canonical_bypass_suspects": 0, "kvl_kcl_relation_skipped": 0, "out_of_graph_storage": 0, "note": "엔진 diff 0. 선언 정본 파일 하나, 기술자는 경로·sha 만. compat_modes 는 대조 상대이고 어긋나면 거부. Descriptor.bin_rule_doc 은 읽은 내용이고 값 판정 사본 아님"},
 "doc_v0631_v049": "OP-7b 쪽: 계획 bin 선언 참조 칸, N3.4 (i), D §7.2 8b, §8.1 끝, §10.2, §16 B-1·B-2·B-3 이 코드와 일치. OP-5 쪽 문언은 그 card 판정 때. 어긋남: minor m1",
 "minor": ["m1 순서: D §7.2 = 8 -> 8b -> 9 인데 oracle_run 은 ir_name_collision(9)을 8b 앞에서 낸다. 두 결함 동시 입력에서 코드가 다르다",
           "m2 실행 뒤 거부는 reject 외에 벤치 폴더(bench.cir, bench.log, bench.ac.txt)가 남아 D §11.7 'reject 하나만'과 다르다. 결과 sim·compare 는 없다",
           "m3 bin_rule._sha_text 가 hashlib 직접(raw_sha256 있음), 해시 정의 한 곳 어긋남",
           "m4 calibration.json compat_modes 출처가 저장소 밖 wt/_drafts/evidence 파일을 가리킨다. 이번 판정 a7.json 이 같은 문장을 다시 쟀다",
           "m5 interface 에 '## 신규 시그니처' 절이 없음(op23 m10 과 같음)",
           "m6 T7-9c 는 선언 글·모드 어긋남을 CompatDecl 직접 생성으로 만든다(H-16, interface '어댑터 표 조작'과 방법 다름, 뜻 같음)"]}
json.dump(sections, open(f"{R}/sections.json", "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).replace(microsecond=0).isoformat()
rec = {"id": ID, "spec_card": f"docs/02-design/specs/{ID}.spec.md", "evidence_type": "red-green", "base_commit": BASE, "test_commit": TEST, "code_commit": CODE,
 "red": {"test_ids": [x["test_id"] for x in ok], "failure_hashes": [x["failure_hash"] for x in ok]},
 "checks": {
  "V1": {"verdict": "N/A", "basis": "임시 규칙 O-229·O-232: 전체 test 안 돌림, 통과로 세지 않음. 잰 범위 = card toy 219 passed, test_spiceinit_isolation 2 failed 1 passed, X-13·test_verified_by 48 passed, tests/structure 171 passed 1 deselected, R1~R5 7 bias 1회. 미측정(LA-1 재점검) = 2회로 연기(엔진 diff 0), test_canonical_order, test_independent, 13회로(B-4)."},
  "V2": {"verdict": "FAIL", "basis": f"A7-1 219 passed, red {len(ok)}건. A7-2 10/10. A7-3 FAIL: test_spiceinit_isolation T7-9a·9b 실패(log_path 상대 경로, 고쳐도 T7-9a status.error sim_failed_other). A7-4 PASS. 표 = .ai/verification/{ID}/sections.json."},
  "V3": {"verdict": "N/A", "basis": "뮤테이션 도구 안 돌림(O-229, 엔진 diff 0). 손 뮤턴트 1회: .spiceinit 쓰기 삭제 + 독 HOME -> 실제 oracle_run 거부. 통과로 세지 않는다."},
  "V4": {"verdict": "PASS", "basis": "oracle 대조: test_lint 미실행. 표본: T7-1a hashlib 구성값, T7-5 missing L3, T7-7 toy sha, T3-8d compat_sha256 = sha(T) 손 유도, T7-9 V(a)=1 KVL. 피검 함수 출력을 옮긴 기대값 표본 0, 전 행 대조 아님."},
  "V5": {"verdict": "PASS", "basis": "약화 없음: test_result_contract:83 전환은 spec 소비자 표(J-5 기간 끝), T7-10e 는 기대 코드 유지, A7-4 제외 칸 추가 0. 13회로 미측정은 B-4(A-84) 표지, 통과로 세지 않음. weakening_diff 미실행(O-229)."},
  "V6": {"verdict": "N/A", "basis": "source_lint 대상 없음: gmid_engine diff 0줄, assets diff 0. §5 잠금 grep 0건."},
  "V7": {"verdict": "PASS", "basis": "배선: oracle_run -> recorded_lf_set·find_decl·check_compat -> Adapter.run(compat) -> .spiceinit·compat_mode_of, 실제 실행과 거부 11종으로 확인. compat_sha256 소비 칸 채움. graph 점검 수치: 필드 수 0 / 소비자 0 결함 0 / 정본 우회 의심 0 / KVL·KCL 관계 미적용 0 / graph 밖 저장 자리 0(엔진 diff 0)."},
  "V8": {"verdict": "PASS", "basis": "폴백 0: 선언 없으면 기본 모드로 돌지 않음(no_decl_ref), 로그 모드 못 읽으면 거부, 캐시 적중도 대조, 거부 11종 시뮬레이션 0."},
  "V9": {"verdict": "PASS", "basis": "격리: 독 HOME·SPICE_USERINIT_DIR 막음, 표지 echo 안 찍힘, 파일 없으면 찍힘. 모드 표 default·hsa 실행 로그와 같음. 값: 데이터 30파일 기준선 바이트 동일, OP-3 sim 동일. 시스템 초기화 스크립트 직접 측정은 없음(로그 대조로 막는 경로만 뮤턴트로 확인)."},
  "V10": {"verdict": "PASS", "basis": "재현: 저자 예비 모드 표를 어댑터 경로로 다시 잼, R1~R5 verdict 7/7. reproduced_numbers 참조."}},
 "reproduced_numbers": [
  {"name": "card toy 통과", "value": 219, "command": "pytest tests/core tests/test_bin_rule_run.py tests/test_input_contract.py tests/test_result_contract.py test_dialect test_errors test_legacy_adapter"},
  {"name": "격리 test 실패", "value": 2, "command": "pytest tests/adapters/ngspice/test_spiceinit_isolation.py"},
  {"name": "tests/structure 통과", "value": 171, "command": "pytest gmid_engine/tests/structure"},
  {"name": "R1~R10 선언 찾음", "value": 10, "command": "tools/a7.py A7-2"},
  {"name": "R1~R5 bias rc·verdict 같음", "value": 7, "command": "tools/a3_run.py, a3_cmp.py"},
  {"name": "기준선과 바이트 동일 데이터 파일", "value": 30, "command": "tools/a7_4b.py"},
  {"name": "로그 default 문장", "value": 8, "command": "tools/a7_4b.py"},
  {"name": "OP-3 와 같은 sim", "value": n_eq, "command": "tools/finalize.py"},
  {"name": "최저 메모리 여유 MB(표본, 시작 전 포함)", "value": 3451, "command": "FreePhysicalMemory 표본"}],
 "approvals": [],
 "auditor_run": {"time": now, "worktree": W, "commands": [f"git clone --no-hardlinks --no-local {W} {T}/iso; git -C {T}/iso remote remove origin", "V1: 전체 test 미실행(O-229). 잰 범위 = card toy, test_spiceinit_isolation, X-13, tests/structure", "tools/a7.py, a3_run.py, a3_cmp.py, a7_4b.py, a7_mut.py, patch_iso_test.py (.ai/verification/20261104-op7b/tools)"]}}
p = f"{W}/.ai/verification/{ID}.json"
json.dump(rec, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
import jsonschema
print("schema", [e.message[:100] for e in jsonschema.Draft202012Validator(json.load(open(f"{W}/.ai/verification/_schema.json", encoding="utf-8"))).iter_errors(rec)], len(ok), n_eq, len(eq))
