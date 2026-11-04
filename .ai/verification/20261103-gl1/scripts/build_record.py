"""Builds .ai/verification/20261103-gl1.json and copies evidence. usage: python -I build_record.py <temp root> <audit worktree>"""
import datetime, hashlib, json, shutil, sys
from pathlib import Path

T, W = Path(sys.argv[1]), Path(sys.argv[2])
O = T / "out6"
EV = W / ".ai/verification/20261103-gl1"
BASE = "f50bc916e3f76290363d113d7e3a14f9fdfd319f"
TEST = "0a33d0b649ee09494cf6900f0516ba310a311715"
CODE = "d798a8745a4ded13e6fef18b120de901a4131497"
red = json.loads((O / "red6.json").read_text(encoding="utf-8"))
summ = json.loads((O / "summary_1.json").read_text(encoding="utf-8"))
mut = [json.loads(x) for x in (O / "mutants.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
surv = [m["id"] for m in mut if m["status"] != "killed"]
killed = sum(m["status"] == "killed" for m in mut)
assert len(mut) == 69 and killed == 54 and len(surv) == 15
rej = json.loads((O / "reject_summary.json").read_text(encoding="utf-8"))
assert rej["all_ok"] and rej["n"] == 18
smoke = [json.loads(x) for x in (O / "smoke/results.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
assert all(s["rc"] == 0 and not s["failed"] and not s["aborted_memory"] for s in smoke) and len(smoke) == 3
assert summ["new"] == 0 and summ["stale"] == 0
tool = json.loads((O / "tool_vs_audit.json").read_text(encoding="utf-8"))
sha = {n: hashlib.sha256((O / "tool_1" / n).read_bytes()).hexdigest() for n in ("calls.json", "shared.tsv", "b_candidates.tsv", "limits.json")}
for n in sha:
    assert (O / "tool_4242" / n).read_bytes() == (O / "tool_1" / n).read_bytes()
limits = json.loads((O / "tool_1/limits.json").read_text(encoding="utf-8"))

SMOKE_CMD = "cd iso6 && python -P -m pytest tests/integration/<file> --run-slow -k \"folded_cascode or ngcc_3stage_ff\" (scripts/smoke_2c.py)"
STRUCT_CMD = "cd iso6 && python -P -m pytest skills/analog-gmid-design/gmid_engine/tests/structure -q -p no:cacheprovider --junitxml=H_structure.xml"
REJ_CMD = "python -I scripts/reject_probe.py iso6p reject.jsonl reject_summary.json"
GEN_CMD = "python -I scripts/gen_baseline.py iso6 " + BASE + " baseline_N.json summary_N.json (2회)"
TOOL_CMD = "PYTHONHASHSEED=1|4242 python iso6/tools/audit/scan_shared_calls.py --engine iso6/skills/analog-gmid-design/gmid_engine --out out6/tool_<seed>"
MINORS = ("minor(판정 막지 않음, LA-1 재점검): m1 lint가 안 잡는 꼴(interface 표 밖) -- field(default_factory=lambda: ...) 진짜 트리 1자리 layout/euler_graph.py:20 adjacency 가 기준선에 없고, "
          "self.a, self.b = {}, [] 와 self.c = {} if x else None 은 진짜 트리 0자리; m2 함수 안 import 이름을 뿌리로 쓴 memo.call 은 거짓 거부(진짜 트리 memo.call 0자리); "
          "m3 method_calls_unresolved 5617 은 모듈 함수 호출·.column·.value 까지 세어 메서드 수보다 크다(모호점 A-40); m4 --touching 이 저장소 기준 경로도 받는다(A-40 은 엔진 기준); "
          "m5 도구 TEXT_MAX = 300 은 선언 없는 text 절단 상수; m6 Literal 안 문자열도 주석 타입으로 읽힐 수 있다(코드 읽기, 미실측); m7 vt_assign 10행 중 WriterTable·ModuleEntry 정적 표가 interface 글자로는 위반이나 design ② '필드 값 형식' 취지와 맞는지 재검토 대상")

checks = {
 "V1": {"verdict": "N/A", "basis": "전체 test 안 돌림: 사용자 지시, card별 회귀 + 2회로 연기, 전체는 LA-1 측정 시점(A-73). 그래서 PASS로 적지 않는다(지시 전달 = 오케스트레이터, A-73 = wt/_drafts/la1_auto_decisions.md:79). 잰 범위: 기준선 포함 트리 a916d5c3(= a20c75d5 + g8_baseline.json, 격리 복제본) tests/structure 170 passed, failed 0, 1 deselected(새 99 + 기존 71, 기존 결과 변화 0); 2회로 연기 --run-slow -k folded_cascode or ngcc_3stage_ff: test_stage_b_library 10 passed, test_s0_layer_9circuits 11 passed, test_g10_no_recompute_9circuits 2 passed, failed 0. 미측정: 나머지 약 438 파일, xfail 수, master f50bc916 전체 결과와의 비교. 엔진 소스 diff 0이라 base 대비 엔진 동작은 바뀌지 않는다는 것은 diff로만 판정했다"},
 "V2": {"verdict": "PASS", "basis": "red: base + T = ccbb0dc2(f50bc916 과 " + TEST[:8] + " 병합, 격리 복제본)에서 새 test 99 전부 red, AttributeError 70(새 심볼 check_g8·check_value_types·G8_ALLOWED_MODULES·dump_baseline·load_baseline·ratchet), AssertionError 29(도구 없음), 다른 원인 0, 기존 71 전부 passed. green: 기준선 포함 트리에서 99 전부 passed. test 불변: 새 test 파일 4개 blob 이 " + TEST[:8] + " 과 a20c75d5 에서 같다(README·structure_checks 만 code 커밋 변경). 예외 타입은 junit 메시지에서 읽었다(merge_gate 플러그인 아님, DEC-86). 순서 3 base_check.json 은 옛 base 0d99a813 기준이고 이 판정 red 는 새 base 로 다시 쟀다. 다리: 정의 toy, 봉인·SPICE·변화표 = 대상 없음(엔진 소스 diff 0, 엔진 안 새 이름 소비 0). 연기 시험 = toy로 대신, 사유 = 지나는 엔진 경로 없음. 오케스트레이터 지시로 2회로 연기 회귀는 따로 돌렸다(V1)"},
 "V3": {"verdict": "PASS", "basis": "mutate_changed.py 는 대상이 assets/tests 라 쓰지 않았다. 손 뮤턴트 69(격리 복제본, scripts/mutants.py): killed 54, 생존 15. 거부·래칫·기준선 형식 뮤턴트 C01~C20·V01~V05·V07·V11~V15·R01~R10 은 전부 killed. 생존: " + ", ".join(surv) + ". 그중 V08·V09·V10·T01·T03·T04·T08·T20·T21 쪽 동작은 판정자 toy(scripts/interface_probe.py)로 계약대로임을 확인했다(A-40의 .value 잎 판단 입력: 도구는 맞게 동작, test 공백만 남음). V06·T10·T11·T14·T16·T19 는 코드 읽기만, 실행 미확인. 생존은 test 공백이고 toy 추가는 LA-1 재점검 minor"},
 "V4": {"verdict": "PASS", "basis": "oracle 대조: EXPECTED_G8_BAD 56행·EXPECTED_VT_BAD 31행 = 픽스처 줄과 대조 불일치 0(순서 3 expected_vs_fixture.tsv, T 불변이라 재사용, 스크립트 재실행 동일 집계); test_g8_baseline HAND_ROWS·줄 이동 [1,2,3,7,10]->[3,4,5,9,12] = edges.py·idcall.py 손 계산 일치; test_scan_shared_calls_tool 기대 class = interface §4 표, 줄·arg_keys = 픽스처 손 대조; 진짜 트리 수치를 기대값으로 쓴 test 0; test_lint.py(대상 밖 경로라 --module-dir·--subject 로 실행) 결과 FAIL 7줄을 손 판정: (1) test_dump_baseline_same_doc_same_bytes 는 같은 doc 두 번 호출의 바이트 동일 계약이라 복사 아님(값은 test_dump_baseline_format·roundtrip 이 따로 단언), (4) test_exit2_* 6개는 assert 가 헬퍼 _expect_input_error 안에 있어 거짓 경보(C·T 뮤턴트 T13·T22·T23·T24 killed 로 확인); UNJUDGED 43줄은 위 기대 목록 대조에 포함"},
 "V5": {"verdict": "PASS", "basis": "weakening_diff.py --base " + BASE[:8] + " --head a20c75d5 = PASS 이지만 diff_paths 0이라 공허(대상 assets/tests 뿐). 손 판정: master 대비 A 81·M 2, M = structure_checks.py(삭제 줄 0) 와 README.md(표 행 1줄 확장 + 추가). 기존 test·규칙·픽스처 변경 0, skip·xfail 추가 0, 기준선은 첫 생성이라 약화 대상 없음, criteria_weakened 없음. 진짜 트리 위반 전체가 기준선에 들어간 것은 O-182 (가1) 설계 그대로다"},
 "V6": {"verdict": "PASS", "basis": "source_lint.py = PASS 이지만 targets 0이라 공허. 손 판정: 엔진 소스 diff 0. 새 코드 except 는 InputError·SyntaxError·ValueError 좁은 형태만, 광범위 except 0, 회로 이름 0(library 13 이름 grep), 물리·설계 상수 0. " + MINORS},
 "V7": {"verdict": "PASS", "basis": "reachability.py = PASS 이지만 new_defs 0이라 공허. 손 판정 소비자: check_g8·check_value_types·load_baseline·ratchet = test_rule_g8_baseline_ratchet(tests/structure 진짜 트리 test), baseline_doc·dump_baseline = 판정자 기준선 생성(scripts/gen_baseline.py) + 40 §10.4 행, 도구 = 첫 소비는 다음 엔진 card 판정(이번 진짜 트리 1회 실행). graph 단일 정본: 필드 수 0 / 소비자 0 필드 0 / 정본 우회 의심 0 / KVL·KCL 관계 미적용 해당 없음(엔진 계산 변경 0) / graph 밖 저장 자리 0(엔진 diff 0, g8_baseline.json 은 검사 기록이고 엔진 소비 0, git grep). 새 cache·memo·sctx 슬롯·값 사본 0. interface §1~§4 대 구현 대조 불일치 없음(모호점은 A-40 후속). 나머지 design gap 상세는 오케스트레이터 지시로 생략(LA-1 재점검)"},
 "V8": {"verdict": "N/A", "basis": "도입 해당 없음: 폴백 코드 없음(검사 도구 card, 엔진 diff 0, DEC-86 merge_gate 미사용)"},
 "V9": {"verdict": "N/A", "basis": "도입 해당 없음: 물리 불변식 대상 없음(엔진 동작 변경 0, 회로 값 변화 0)"},
 "V10": {"verdict": "PASS", "basis": "기준선 2회 바이트 동일 sha256 " + summ["sha256"] + ", kind별 행 " + json.dumps(summ["rows_by_kind"]) + " 총 " + str(summ["n_rows"]) + "행·위반 101, new 0, stale 0(판정 커밋 트리). kind 0행 = g8_class_container·g8_cache_call·g8_module_cache·g8_memo_call_form·vt_annotation(독립 AST·grep 도 0). 독립 재계수(scripts/indep_count.py): attr 59, default_factory 4, cached_property 3, id 2, memo.lookup 23, frozen 타입 335, 대상 420 파일 일치. kind마다 소스 손 확인 행: layout/diffusion.py:28, layout/euler_graph.py:18, layout/_helpers_alias.py:28, metrics/resolution.py:38, lut/cap_query.py:52, _module_map.py:194, 위반 아닌 행 0. 실제 거부 18/18(kind 11 new, 수 +1 new, 제거 stale, 줄 이동 둘 다 빔, 기준선 삭제·형식 오류 실패, 진짜 test red·복원 green), 복제본 git status 0. 도구 2회(PYTHONHASHSEED 1·4242) 네 산출물 바이트 동일. 진짜 트리 1회: 호출 자리 2194, 공유 callee 201(D 199, B 2, not_B 0), limits " + json.dumps(limits) + ". 감사 B 함수 21 중 도구 B 0, D 21(합격 조건 아님, LA-1 완료 13 입력). 도구 B 2 = sorted_items·check_theta 는 감사 B 목록 밖(거짓 B 후보, 손 분류 대상)"},
}
cmd = lambda n: n
nums = [
 ("판정 커밋 기준 stale 수", 0, GEN_CMD), ("병합본 new 수", 0, GEN_CMD), ("기준선 행 수", summ["n_rows"], GEN_CMD), ("기준선 위반 수", 101, GEN_CMD),
] + [("기준선 행 " + k, v, GEN_CMD) for k, v in summ["rows_by_kind"].items()] + [
 ("tests/structure passed", 170, STRUCT_CMD), ("tests/structure failed", 0, STRUCT_CMD),
 ("2회로 stage_b passed", 10, SMOKE_CMD), ("2회로 s0_layer passed", 11, SMOKE_CMD), ("2회로 g10 passed", 2, SMOKE_CMD), ("2회로 failed", 0, SMOKE_CMD),
 ("새 test red 수", red["n_red"], "base + T ccbb0dc2, tests/structure junit, scripts/red_hash.py"),
 ("실제 거부 통과 사례", 18, REJ_CMD), ("손 뮤턴트 killed", killed, "python -I scripts/mutants.py"), ("손 뮤턴트 생존", len(surv), "python -I scripts/mutants.py"),
 ("도구 호출 자리", 2194, TOOL_CMD), ("도구 공유 callee", 201, TOOL_CMD), ("도구 method_calls_unresolved", limits["method_calls_unresolved"], TOOL_CMD),
 ("도구 sites_with_param_leaf", limits["sites_with_param_leaf"], TOOL_CMD), ("감사 B 함수 중 도구 B", 0, "python -I scripts/tool_vs_audit.py"),
 ("새 graph 필드", 0, "git diff master HEAD -- gmid_engine (tests 제외) = 0"), ("엔진 소스 diff 파일", 0, "git diff --name-only master HEAD"),
]
rec = {
 "id": "20261103-gl1", "spec_card": "docs/02-design/specs/20261103-gl1.spec.md", "evidence_type": "red-green",
 "base_commit": BASE, "test_commit": TEST, "code_commit": CODE,
 "red": {"test_ids": red["test_ids"], "failure_hashes": red["failure_hashes"]},
 "checks": checks,
 "reproduced_numbers": [{"name": a, "value": b, "command": c} for a, b, c in nums],
 "approvals": [],
 "auditor_run": {"time": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).replace(microsecond=0).isoformat(),
                 "worktree": W.as_posix(),
                 "commands": ["V1: 전체 실행 안 함(A-73). 대신 " + STRUCT_CMD + " ; " + SMOKE_CMD,
                              "격리: git clone --no-hardlinks --no-local <audit worktree> la1s_gl1_audit/{iso6,iso6r,iso6p} ; git -C <각각> remote remove origin ; iso6r = checkout --detach ccbb0dc2 ; iso6 = HEAD + g8_baseline.json 커밋 a916d5c3",
                              GEN_CMD, REJ_CMD, TOOL_CMD, "python -I scripts/mutants.py iso6p mutants.jsonl", "python -I scripts/interface_probe.py iso6 probe_toy interface_probe.json",
                              "python tools/gates/{weakening_diff,source_lint,reachability}.py --root iso6 --base " + BASE + " --head a20c75d5b8fbbf71defd447bc2fe1df6960f8d2c"]},
}
(W / ".ai/verification/20261103-gl1.json").write_bytes(json.dumps(rec, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
(EV / "scripts").mkdir(exist_ok=True)
for s in ("gen_baseline", "indep_count", "reject_probe", "red_hash", "mutants", "interface_probe", "tool_vs_audit", "smoke_2c", "build_record"):
    shutil.copyfile(T / "scripts" / (s + ".py"), EV / "scripts" / (s + ".py"))
for f in ("summary_1.json", "summary_1.json.viol.tsv", "red6.json", "reject.jsonl", "reject_summary.json", "mutants.jsonl", "interface_probe.json", "tool_vs_audit.json", "gate_weakening_diff.txt", "gate_source_lint.txt", "gate_reachability.txt"):
    shutil.copyfile(O / f, EV / f)
shutil.copyfile(O / "smoke/results.jsonl", EV / "smoke_results.jsonl")
(EV / "tool_sha256.json").write_text(json.dumps(sha, indent=1) + "\n", encoding="utf-8", newline="\n")
(EV / "verdict.txt").write_text("PASS Major 0, minor 7 + 뮤턴트 생존 15 (LA-1 재점검), 전체 test 미실행(A-73)\n", encoding="utf-8", newline="\n")
print("ok", len(rec["red"]["test_ids"]))
