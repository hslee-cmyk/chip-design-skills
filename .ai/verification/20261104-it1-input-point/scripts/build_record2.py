"""IT-1 재판정: 기존 판정 기록을 갱신. 인자: 임시 루트, audit worktree."""
import datetime
import glob
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

T, W = Path(sys.argv[1]), Path(sys.argv[2])
R = T / "res"
ID = "20261104-it1-input-point"
P = "skills/analog-gmid-design/"
rev = lambda c: subprocess.check_output(["git", "-C", str(W), "rev-parse", c], text=True).strip()
HEAD = rev("HEAD")
assert HEAD.startswith("f62d4ed1")
rec_path = W / ".ai/verification" / (ID + ".json")
rec = json.loads(rec_path.read_text(encoding="utf-8"))

green, bad = set(), []
tot = {"card": 0, "structure": 0, "smoke": 0}
for p in glob.glob(str(R / "head2" / "*.xml")):
    name = Path(p).stem
    root = ET.parse(p).getroot()
    suite = root if root.tag == "testsuite" else root[0]
    grp = "structure" if name == "structure" else ("smoke" if name in ("integration_test_stage_b_library", "integration_test_s0_layer_9circuits", "integration_test_g10_no_recompute_9circuits") else "card")
    for tc in suite.iter("testcase"):
        tot[grp] += 1
        tid = tc.get("classname").replace(".", "/") + ".py::" + tc.get("name")
        if tc.find("failure") is not None or tc.find("error") is not None:
            bad.append(tid)
        else:
            green.add(tid)
assert not bad, bad
print(tot)

ids, hs = [], []
dropped = []
for i, h in zip(rec["red"]["test_ids"], rec["red"]["failure_hashes"]):
    if i[len(P):] in green:
        ids.append(i)
        hs.append(h)
    else:
        dropped.append(i)
rec["red"] = {"test_ids": ids, "failure_hashes": hs}
print(len(ids), [d.split("::")[1] for d in dropped])

mut = [json.loads(x) for x in (R / "mutations3.jsonl").read_text(encoding="utf-8").splitlines()]
st = {m["mut"].split()[0]: m["killed"] for m in mut}
assert st == {"X1": True, "X2": True, "X3": True, "X4": False, "X5": False, "X6": True}, st

HOLD = "미완료(보류 다리: 13회로 변화표·IT-0b·SPICE, 채울 card = EO-1·OP-5·CL-1, base = %s)" % rec["base_commit"]
MAJOR4 = ("Major-4 기준 약화: 커밋 e5885726 이 test_it1_net_model_has_single_call_site_in_s1v_fields(T-6b AST)를 지웠다. 필드 삭제와 무관하게 유효한 기준이고 계획 P:1766 완료 7 (i)·design 41 '`net_model(` 호출 = `s1v_fields` 하나'가 그대로 있다. "
          "대체 test 없음: 뮤턴트 X4(coupling_vars 가 net_model(s1) 재호출)가 test_coupling_vars 79·test_net_model 40·tests/structure 171 전부 통과로 생존, 앞 판정 M10b 는 그 test 로 killed. A-76 폐기 목록에 없다. 현재 코드 호출 자리는 s1v_fields 하나로 위반은 없다. test 주체가 그 test 하나를 되살리면 된다")
c = rec["checks"]
c["V1"] = {"verdict": "N/A", "basis": "전체 test 안 돌림, 임시 규칙 O-229, 잰 범위 = 재판정 병합본 f62d4ed1(rule_hash 줄 재기록, 격리 복제본) card test 24 파일 %d개, tests/structure %d개(deselected 1), 2회로 연기 stage_b 10·s0 11·g10 2, 실패 0. 그 밖 test 는 통과로 세지 않는다." % (tot["card"], tot["structure"])}
c["V2"] = {"verdict": "PASS", "basis": "red: 앞 측정 재사용(base + 동결 test), 이번에 지운 test %d개 뺀 %d개가 병합본 전부 통과. 새 test test_it1_input_target_one_port_stops 2사례는 X1(정지 코드 제거)로 실패 확인, base red 는 재측정 안 함. M-2 해소: os_k 삭제, 필수 test 실패 0." % (len(dropped), len(ids))}
c["V3"] = {"verdict": "PASS", "basis": "재판정 손 뮤턴트 6(scripts/mutate2.py, 커밋 없음): X1 input_target_one_port 정지 제거 -> only_p·only_n 실패, X2 입력 DC 선언 가드 제거 -> test_fixed_values_w3_and_input_dc 실패, X3 두 포트 다 정지 -> 대조 test 실패, X6 rule_hash 되돌림 -> T-RH 실패. 생존 X4 = Major-4(V5), X5 terms 짝 제약 = 앞 M13 과 같은 test 빈틈 minor(동작은 탐침 p5·s0 연기로 확인). 앞 판정 뮤턴트 17 은 재사용, 그중 M17 은 필드 삭제로 대상 소멸."}
c["V5"] = {"verdict": "FAIL", "basis": MAJOR4 + ". 그 밖 약화 0: 래칫 new 0을 기준선 수정 없이 달성(g8_baseline.json diff 0, 재판정 범위), T-6a 네 값 test·READS test 삭제는 필드 삭제의 귀결(A-76, 계획 P:586·P:1756(b)·design 40 행 개정과 일치, 부재 단언으로 대체), os_k 폐기 = A-42, T-1h 는 O-227 (3) 유지."}
c["V6"] = {"verdict": "PASS", "basis": "tests/structure 171 통과, 래칫 new 0·stale 0(M-1 해소, _Circuit.mates 삭제). 구조 규칙·값 타입 위반 0, 회로 이름 0, 광범위 except 추가 0, 숫자 상수 추가 0, 범위 밖 엔진 변경 0(ff61b525 = coupling_vars·net_model·s1_values·s1v_fields·block_columns·s2_values·writer_plan·CONTRACT, 레지스트리). minor: coupling_vars.py:22 import dataclasses 미사용."}
c["V7"] = {"verdict": "PASS", "basis": "M-3 해소: 필드 넷 삭제(S1V_WRITES 다섯 행, s1v 기록에 네 이름 0), coupling_vars READS 에 없음, 코드 net_index(s1), 계획 P:586·P:1756(b)·design 40 S1v 행과 일치. 새 사유 BRANCH_INPUT_TARGET_ONE_PORT 소비자 = dc_writer_plan 정지. graph 수치: 새 필드 0 + 새 칸 1(gate_source_same, 소비자 있음), 소비자 0 = 0, 정본 우회 의심 0, KVL·KCL 관계 미적용 0, graph 밖 저장 자리 0. terms(): node.dc_writer 의 known 을 읽는 조회라 둘째 생산자 아님, 평가 1회 호출 8회 누적 6.6e-5 s(size_and_seal 0.136 s의 0.05 %, 노드 8 toy) = 블록 안 scan 으로 값 저장 없음."}
c["V9"] = {"verdict": "PASS", "basis": "m1 재측정(probes2.jsonl): 앞 판정 ΔV θ 함수 toy 는 only_inn·only_inp 모두 StructureUnresolvedError input_target_one_port 정지(ports·declared 기록). 두 포트 다 선언 = W3 둘, 둘 다 아님 = input_point. 포트가 레일이면 topology_load port_on_rail 거부. 입력 점 KVL·KCL(p1)·g = s fail-closed(p2)는 앞 측정 재사용, 물리 코드 변경 없음(terms 동일 항, s0 연기 값 변화 0). SPICE 다리 " + HOLD + ", 통과로 세지 않음."}
c["V10"] = {"verdict": "N/A", "basis": "spec '재현할 수치' 없음. 13회로 변화표·IT-0b·SPICE = " + HOLD + ". 기준선 값 변화 0: fixture 수정 없이 s0 연기 11 통과(2회로, 그 밖 회로는 재측정 안 함, 앞 기준선 행과 근거는 03e4eab9 cause_table.json). rule_hash: net_model.py·s1v_fields.py 가 rule 파일이라 stale, 코드 커밋이 빠뜨려 판정자가 두 structure.json 의 그 줄만 재기록(A-34): 5c0b84c5... -> ca0fde40c5599facc08b18d3fd94036b7fd8b242580edf5db1fd0eb54ad04347 = structure_rule_fp(), 사실·topology_hash 변경 0, T-RH 통과, 되돌리면 실패(X6)."}
rec["test_commit"] = rev("e5885726")
rec["code_commit"] = rev("ff61b525")
rec["reproduced_numbers"] = [
    {"name": "card test 수", "value": tot["card"], "command": "scripts/run_tests.py iso2 res/head2 all"},
    {"name": "tests/structure 수", "value": tot["structure"], "command": "scripts/run_tests.py iso2 res/head2 all"},
    {"name": "2회로 연기 수", "value": tot["smoke"], "command": "--run-slow -k folded_cascode or ngcc_3stage_ff"},
    {"name": "필수 test 실패 수", "value": len(bad), "command": "scripts/run_tests.py iso2 res/head2 all"},
    {"name": "ratchet new 수", "value": 0, "command": "tests/structure/test_g8_baseline.py::test_rule_g8_baseline_ratchet"},
    {"name": "재판정 뮤턴트 생존 수", "value": 2, "command": "scripts/mutate2.py mut2 res/mutations3.jsonl"},
    {"name": "red 수", "value": len(ids), "command": "scripts/run_red.py red_tree res/red.jsonl plug (앞 측정 재사용)"},
]
rec["auditor_run"] = {
    "time": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "worktree": str(W).replace("\\", "/"),
    "commands": [
        "V1: 전체 실행 안 함(임시 규칙 O-229), 범위 실행 = python scripts/run_tests.py iso2 res/head2 all",
        "git clone --no-hardlinks --no-local <worktree> la1s_it1_audit6/iso2; git -C iso2 remote remove origin (뮤턴트는 같은 방식 복제본 mut2)",
        "python scripts/rehash.py <복제본> 5c0b84c5... ca0fde40...; python scripts/mutate2.py mut2 res/mutations3.jsonl; PROBE_OUT=res/probes2.jsonl pytest scripts/test_zz_audit_probe2.py",
    ],
}
rec_path.write_bytes(json.dumps(rec, ensure_ascii=False, indent=1).encode("utf-8"))

ev = W / ".ai/verification" / ID
for f in ("mutate2.py", "test_zz_audit_probe2.py", "rehash.py", "build_record2.py"):
    shutil.copy(T / f, ev / "scripts" / f)
for f in ("mutations3.jsonl", "probes2.jsonl", "p5_rerun.jsonl"):
    shutil.copy(R / f, ev / f)
shutil.copy(R / "head2" / "summary.jsonl", ev / "test_summary_rejudge.jsonl")
print({k: v["verdict"] for k, v in c.items()})
