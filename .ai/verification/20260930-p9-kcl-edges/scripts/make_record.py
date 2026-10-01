"""P9 순서 7 판정 기록 조립(auditor). record_draft.json의 자리표시를 채워 <out>에 BOM 없는 UTF-8로 쓴다.
V3 basis는 C:/g47/out/tool_V3.txt·v3_mut.jsonl·v3_baseline_m_*.json에서 읽는다."""
import collections, json, sys
O = "C:/g47/out/"
out = sys.argv[1]
rec = json.load(open(O + "record_draft.json", encoding="utf-8"))
v3 = json.loads(open(O + "tool_V3.txt", encoding="utf-8").read().strip().splitlines()[-1])
muts = [json.loads(l) for l in open(O + "v3_mut.jsonl", encoding="utf-8")]
res = collections.Counter(m["result"] for m in muts)
tos = [m["id"] for m in muts if m.get("exit") == "timeout"]
bf = json.load(open(O + "v3_baseline_m_kcl_series_union.find.json", encoding="utf-8"))
bk = json.load(open(O + "v3_baseline_m_kcl_series_union.json", encoding="utf-8"))
C = "C:/g47/gmid-gate-cache/7535799302a9ff7cfbfcadb2281d16bf136fadcf"
M = "b7765b047ac510b7150a3b99b102891e4083e970"
V1CMD = ("PYTHONPYCACHEPREFIX=C:/g47/pyc_v1_m PYTHONPATH=%s C:/Python314/python.exe -P -m pytest -c %s/pytest_gate.ini "
         "--rootdir=C:/g47/m --confcutdir=C:/g47/m --gmid-phase=2 --gmid-strict= C:/g47/m/skills/analog-gmid-design/assets/tests") % (C, C)

B = {}
B["V1"] = ("병합본 M b7765b047ac510b7150a3b99b102891e4083e970(부모 [T c8d55db, K 16a71fa], 트리 09cfe77f = K 트리, Role: doc·Change-Id 같음)을 "
           "git clone -c core.longpaths=true --no-hardlinks --no-local --no-checkout 한 격리 복제본 C:/g47/m(origin 제거, checkout --detach, remote 0·status 0줄, "
           "실행 뒤에도 0줄)에서 base 판 캐시 7535799의 pytest_gate.ini로 slow 포함 전체 실행(-k·--deselect·-x·-m 없음, --gmid-phase=2 --gmid-strict=): "
           "822 passed, 15 xfailed, 실패·오류·skip·xpass 0, exit 0, 263.74s, 출력 sha256 1b64881e7e3a07ed63fe6a8df707c0bde9ea35eb1322e85990ee77f2212098b2. "
           "수집 837 = T 수집 837(id 집합 동일), base 813 id 전부 포함, 늘어난 24가 전부 contracts/test_dup_kcl_edges.py. 같은 명령의 base 7535799 복제본 실행은 "
           "798 passed·15 xfailed(순서 3). 엄격 집합은 base 판 merge_gate.strict_set = 공집합, v1_command_check 실패 0건(순서 3 strict_check.txt). "
           "게이트 코드는 git cat-file blob 7535799:tools/gates/<파일>로 redteam 밖 22개를 직접 뽑았고(파일 집합 sha256 705036ea1039e7abb0e449918a8209b229f4a685ab2da9d0e03907bf571d82c4) "
           "오케스트레이터 캐시와 diff -r 차이 0. code-author 보고(822 passed·15 xfailed)는 증거로 쓰지 않았고 실측과 같다")
B["V2"] = ("equivalence. FAIL 사유 = 계약 8(c) 한 곳: 병합본 레지스트리(docs/03-analysis/gain-budget-gmid-sizing.function-registry.md) 428행 "
           "trace_vdd_to_gnd_branches 비고에 낡은 줄 번호 'SD:1216-1224'가 남아 있다. 계약 8(c) 원문은 '428의 SD:1216-1224·SD:3580·SR:4469-4472'를 이름 참조로 "
           "바꾸라고 적는다(SD:3580·SR:4469-4472는 바뀌었고 SD:1216-1224만 남음; 병합본 SD에서 trace_vdd_to_gnd_branches는 1187행에서 시작해 이 번호가 함수 안 "
           "규약 줄을 가리키지 않는다). 재현: grep -n 'SD:1216-1224' <병합본>/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md -> 428행. "
           "참고(같은 수정 때 함께): 계약 8(c)는 세 행에 '겹침이 부호 규약·레일 이름 집합임을 적는다'인데 308행은 레일 이름 집합만, 428행은 부호 규약만 적는다. "
           "나머지는 모두 충족한다. [커밋 모양] base 7535799(gate master) -> T c8d55db(Role: test, 부모 base, 새 파일 test_dup_kcl_edges.py 하나, tests 밖 diff 0) -> "
           "K 16a71fa(Role: code, 부모 T, stick_diagram.py +3/-14·레지스트리 +6/-6) -> M b7765b0(Role: doc, 부모 [T, K], 트리 = K 트리). test 커밋 불변: "
           "git diff T M = 위 2경로뿐, test 경로 없음. [base·병합본 PASS] 새 test 24개가 base 엔진에서 24/24 PASS(순서 3, T 전체 822 passed·15 xfailed, base 판 red 수집 "
           "12줄 전부 IC xfail builtins.Failed, AssertionError 0) 그리고 병합본에서 24/24 PASS(-p merge_gate -rA, red 캡처 파일 생성 없음). 기존 test는 base 798 passed·15 "
           "xfailed, 병합본에서 같은 id 실패 0. [동등 증명 -- 계약 4] DIFF-DUP 9회로 x 2입력 = 18 kcl_series_union 비교 + 18 정본 엣지 목록 비교 36/36 같음, 합성 2입력 같음, "
           "출력 JSON이 base와 바이트 동일; 그룹 수 (i)/(ii) common_gate_amplifier 1/1, current_reuse_telescopic_ota 17/29, folded_cascode 5/9, ngcc_3stage_ff 11/12, "
           "nmcnr_amplifier 7/10, pushpull_follower_buffer 3/3, sf_pushpull_output_opamp 11/12, two_stage_ota 3/4, two_stage_ota_sf 4/5(spec card 수치와 같음), 합성 3/6; "
           "레일 이름 넷 정확히 2회 사용은 two_stage_ota gnd 하나; 정본 엣지의 연결 성분(auditor 독립 구현) = kcl_series_union 그룹 18/18. analog-grammar는 복제본 안 "
           "netclass.py·idioms.py로 import됨(B34 조용한 실패 없음). E-LIB 9회로 base = 병합본(출력 JSON 바이트 동일, 순서 3 값과도 같음). E-INST 파일럿·folded_cascode가 "
           "같은 경로·같은 시각대 base 2회·병합본 2회 모두 instance.json 바이트 동일(topology_ref 계약값 상대 경로). 성능 관찰(계약 9, 임계값 없음): folded_cascode base "
           "48.65·48.49s / 병합본 38.44·49.21s, 파일럿 base 286.77·363.74s / 병합본 346.32·384.83s(기계 부하 편차가 커서 차이를 결론 내지 않는다). "
           "[구조 AST -- auditor, scripts/ast_struct.py, 판정기 자기 점검: 거부 3·통과 1, 5(a)·5(b) 합성 확인] 계약 1: base kcl_series_union 본문(docstring 제외)은 정본 호출 0·"
           "_RAIL_NETS 참조 1·.source/.drain 2·find 루프 경로 압축 대입 1(루프 본문 2문장) -> (a)(b)(c)(d) 모두 어긋남; 병합본은 정본 호출 1·_RAIL_NETS 0·.source/.drain 0·"
           "경로 압축 0, find while 본문 = x = parent[x] 한 문장 -> (a)(b)(c)(d) 충족. 3(a): _kcl_and_matching_edges args·returns dump와 docstring 포함 ast.dump가 base와 같음. "
           "5(a): 병합본 A/*.py 7개 + run_harness.py의 docstring 제외 문자열 상수 다중집합 - base = 빈 집합(합계 5774 양쪽 같음). 5(b): SD _RAIL_NETS AST Name 참조 base 19 -> "
           "병합본 18(줄 grep 18 -> 17, 판정에 쓰지 않음). 5(c): 새 test의 레일 이름 넷은 gnd 3회 사용 한 입력뿐. 5(d)·8(a): §2 KCL 엣지 행 정본 칸에 '정본 후보'·'B26' 유지, "
           "'(stick_diagram 3148행)'은 이름 참조로 바뀜, 중복 칸에서 _metric_kcl_residual이 빠지고 사유 기재, kcl_series_union '엣지 생성부를 정본 호출로 통합 완료(20260930-p9-kcl-edges)', "
           "상태 칸 '엣지 정의 통합 완료, 정본 확정은 B26 뒤'. 6: 새 최상위 def 0(SD 최상위 정의 177개 키 집합 같음); kcl_series_union 호출 위치 SR _build_theta_evaluator·SD _kcl_branch_map "
           "(base와 같음); _kcl_and_matching_edges 호출 위치 base 2곳(audit_vertical_stack_id_vs_kcl, propose_vertical_stack_id_gap_fill) + kcl_series_union 1곳. 7: base와 다른 엔진 파일은 "
           "stick_diagram.py 하나, 그 안에서 ast.dump가 바뀐 최상위 정의는 kcl_series_union 하나(docstring 불변); sizing_recipe.py·run_harness.py·library 17파일 바이트 동일. "
           "8(b): §6 472·473행이 병합 뒤 사실(낡은 SD:3298·SD:3188-3212·'독자 구현' 문장 없음). 8(c): 308행 4456·3882-3883·4448과 474행 SR:4469-4472는 이름 참조로 바뀌었으나 "
           "428행 SD:1216-1224가 남음(위 FAIL 사유). 8(d): 병합본 reg_check.py --registry ... --root C:/g47/m -> '발견 0', exit 0")
B["V3"] = None
B["V4"] = ("oracle 대조: 기대값마다 spec card oracle (a)(구성 입력, KCL 2단자 내부 넷 + 매칭 이웃 쌍, 대표·구성원·키 = netlist 순서)과 손으로 대조했다 -- 11케이스 x 그룹 리터럴·엣지 집합 리터럴 "
           "22개 모두 넷리스트에서 직접 유도한 값과 같다(chain_interleaved nx_1·nx_2 -> {qb2,qa1,qc3} 대표 qb2; three_use nx_3 3회 -> 엣지 0; source=drain nx_5 같은 소자 -> 0; "
           "매칭 쌍·역순 쌍·세 소자 사슬·역순 사슬 대표 = netlist 첫 소자; gnd 3회 -> 0; mixed nx_t·nx_o1·nx_o2 -> {qn2,qp1,qn1}·{qp2,qn3}, 매칭이 고립 쌍·두 가지를 잇는 두 변형). "
           "두 피검 함수를 서로의 기대값으로 쓰지 않는다(test 본문 확인). 도구: base 판 캐시 test_lint.py --root C:/g47/m --base 7535799 --head b7765b0 --subject stick_diagram:kcl_series_union "
           "--subject stick_diagram:_kcl_and_matching_edges -> verdict PASS, exit 0, 대상 파일 1(test_dup_kcl_edges.py), findings 13 = (2) UNJUDGED 5(266·267·275·277·278행, 기대값이 "
           "파라미터 case에서 온 리터럴 -- 위 oracle 대조로 판정) + (2) NO-SUBJECT 8(시그니처 test 284-298행, 기대값 = interface card 시그니처 문자열), FAIL 0. PASS는 독립의 증거가 아니다 -- "
           "독립성은 위 손 대조와 test-author가 소스 없이 spec·interface card만 받았다는 역할 분리에 기댄다")
B["V5"] = ("base 판 캐시 weakening_diff.py --root C:/g47/m --base 7535799 --head b7765b0 -> verdict PASS, findings 없음, diff_paths 없음, diff_hash null, approved false, exit 0. "
           "순서 3 base -> T 출력과 같다(K는 test를 건드리지 않았다). 새 test 파일 추가는 약화 대상이 아니다. 기록할 diff 해시 없음")
B["V6"] = ("base 판 캐시 source_lint.py --root C:/g47/m --base 7535799 --head b7765b0 -> verdict PASS, targets [skills/analog-gmid-design/assets/stick_diagram.py], findings 0, exit 0")
B["V7"] = ("base 판 캐시 reachability.py --root C:/g47/m --base 7535799 --head b7765b0 -> verdict PASS, new_defs 없음, unreached 없음, unreached_without_approval 없음, exit 0. "
           "새 def 0(계약 6). 운영 경로: run_harness.run -> SR _build_theta_evaluator -> kcl_series_union -> _kcl_and_matching_edges(E-INST 두 회로가 지난다), SD _kcl_branch_map -> "
           "kcl_series_union. V3 인벤토리 기준 _kcl_and_matching_edges에 닿는 test가 base 140 -> 병합본 144(kcl_series_union 경유 호출이 더해짐)")
B["V10"] = ("spec card '재현할 수치'를 auditor가 격리 복제본에서 독립 실행으로 재현했다(reproduced_numbers 20개): kcl_series_union 그룹 수 9회로 x 입력 2종이 병합본에서 spec card 값과 "
            "같고 base(순서 3)와도 같다; SD _RAIL_NETS AST 참조 수 base 19 -> 병합본 18. 그 밖 이 기록의 수치(수집 813 -> 837, 822 passed·15 xfailed, DIFF-DUP 36/36, E-LIB·E-INST "
            "해시, V3 집계, 성능 관찰값)도 모두 auditor가 C:/g47/*에서 직접 쟀다(순서 3은 이 폴더 base_check.json). code-author·test-author 보고는 대조용으로만 봤다")

v3_basis = ("base 판 캐시 mutate_changed.py --root C:/g47/m --base 7535799 --head b7765b0 --pytest-ini <캐시>/pytest_gate.ini --timeout 720 --gmid-phase=2 --gmid-strict= "
            "--out C:/g47/out/v3_mut.jsonl -> verdict %s, exit %s, mutants %d, killed %d, survivors %d, exempt %d. 대상 def: kcl_series_union(23변이)·kcl_series_union.find(5변이) "
            "-- 바뀐 def 전체를 변이(spec card 모의 28개와 같은 수). 이 중 timeout으로 죽은 변이 %d개(%s) -- find 루프의 x = parent[x] 삭제·while 비교 뒤집기로 무한 루프가 되는 변이이며 "
            "spec card가 예고한 4개와 같다. 나머지는 test 실패(exit 1)로 죽었다. 기준 실행은 도구 안에서 통과(BaselineFailed 없음 -- B28 이력 포함 복제본에서 "
            "test_base_blob_reader_reads_the_base_tree 통과). --timeout 근거: 같은 명령 모양(make_clone 이력 포함 복제본, -x, --gmid-phase=2)으로 병합본 head에서 잰 기준 실행 시간 "
            "인벤토리 144(find) %.2fs·72(kcl_series_union) %.2fs(순서 3 T head 193.86s·198.22s) -> 720s = 최대 기준의 %.1f배(3배 이상). 등가 변이 면제 승인 없음(계약 1(d) 모양이라 "
            "경로 압축 삭제 등가 변이가 생기지 않는다). 인벤토리(병합본): kcl_series_union 72, find 144")
B["V3"] = v3_basis % (v3["verdict"], {"PASS": 0, "FAIL": 1}.get(v3["verdict"], 2), v3["mutants"], v3["killed"], len(v3["survivors"]),
                      res.get("exempt", 0), len(tos), ", ".join(tos), bf["elapsed_s"], bk["elapsed_s"], 720.0 / max(bf["elapsed_s"], bk["elapsed_s"]))
for k, v in B.items():
    rec["checks"][k]["basis"] = v
rec["checks"]["V3"]["verdict"] = "PASS" if v3["verdict"] == "PASS" else "FAIL"

dd = json.load(open(O + "diffdup_m.json", encoding="utf-8"))
DCMD = "PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g47/scripts/diff_dup.py C:/g47/m C:/g47/out/diffdup_m.json (summary_n_groups[%s][%d])"
rn = []
for c, (gi, ge) in dd["summary_n_groups"].items():
    rn.append({"name": "kcl_series_union 그룹 수 %s 입력 (i) current_forced" % c, "value": gi, "command": DCMD % (c, 0)})
    rn.append({"name": "kcl_series_union 그룹 수 %s 입력 (ii) []" % c, "value": ge, "command": DCMD % (c, 1)})
a_cmd = "PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g47/scripts/ast_struct.py measure %s C:/g47/out/%s (c5b_rail_nets_name_refs)"
rn.append({"name": "SD _RAIL_NETS AST 참조 수 base", "value": json.load(open(O + "ast_base.json", encoding="utf-8"))["c5b_rail_nets_name_refs"], "command": a_cmd % ("C:/g47/base", "ast_base.json")})
rn.append({"name": "SD _RAIL_NETS AST 참조 수 병합본", "value": json.load(open(O + "ast_m.json", encoding="utf-8"))["c5b_rail_nets_name_refs"], "command": a_cmd % ("C:/g47/m", "ast_m.json")})
rec["reproduced_numbers"] = rn

rec["auditor_run"] = {
 "time": sys.argv[2],
 "worktree": "C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-p9-kcl-edges-audit",
 "commands": [
  "환경: $PY = C:/Python314/python.exe(3.14.2), export APPDATA=C:/Users/HSLEE/AppData/Roaming, 결과 C:/g47/out, 스크립트 C:/g47/scripts/(사본 .ai/verification/20260930-p9-kcl-edges/scripts/)",
  "게이트 코드: C:/Python314/python.exe -P C:/g47/scripts/extract_gate.py C:/g47/base 7535799302a9ff7cfbfcadb2281d16bf136fadcf %s (git ls-tree + git cat-file blob, tools/gates/ 중 redteam/ 밖 22개)" % C,
  "격리: git clone -q -c core.longpaths=true --no-hardlinks --no-local --no-checkout C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-p9-kcl-edges-audit C:/g47/<이름>; git -C C:/g47/<이름> remote remove origin; git -C C:/g47/<이름> checkout -q --detach <rev> -- 순서 3: iso = T c8d55db, base = 7535799, eq = base; 순서 7: m = M b7765b0, eq = base·M 번갈아(git fetch -q --no-tags <audit worktree> role/audit/20260930-p9-kcl-edges 뒤 checkout --detach + clean -fdxq), 모두 remote 0, status 0줄",
  "V1: " + V1CMD,
  "수집·green: bash C:/g47/scripts/run_m.sh v1|green (green = 새 test 파일 -p merge_gate, GMID_RED_CAPTURE=C:/g47/out/red_M.jsonl, -rA)",
  "base red(순서 3): bash C:/g47/scripts/run.sh collect|base|red (red = GMID_RED_CAPTURE=C:/g47/out/red_T.jsonl GMID_INTERFACE_CARD=C:/g47/iso/docs/02-design/specs/20260930-p9-kcl-edges.interface.md ... -p merge_gate --continue-on-collection-errors, 루트 C:/g47/iso)",
  "DIFF-DUP: PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g47/scripts/diff_dup.py C:/g47/<base|m> C:/g47/out/diffdup_<base|m>.json",
  "구조 AST: PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g47/scripts/ast_struct.py selftest; ... measure C:/g47/<base|iso|m> C:/g47/out/ast_<base|T|m>.json",
  "E-LIB·E-INST: bash C:/g47/scripts/eq_o7.sh (C:/g47/eq에서 base·M 번갈아 einst.sh 2회씩 + e_lib.py 1회씩; 순서 3은 einst.sh C:/g47/eq base <회로> 3, e_lib.py C:/g47/eq)",
  "게이트 도구(V4·V5·V6·V7): bash C:/g47/scripts/tools_m.sh fast (base 판 캐시 도구, --root C:/g47/m --base 7535799 --head b7765b0, -P 없이; V4 --subject stick_diagram:kcl_series_union --subject stick_diagram:_kcl_and_matching_edges)",
  "V3: bash C:/g47/scripts/v3_o7.sh 720 (v3_inv.py 인벤토리 -> v3_baseline.py 기준 실행 시간 -> tools_m.sh v3 720 = mutate_changed.py --timeout 720 --gmid-phase=2 --gmid-strict= --out C:/g47/out/v3_mut.jsonl)",
  "reg_check: PYTHONPYCACHEPREFIX=C:/g47/pyc_reg_m C:/Python314/python.exe C:/g47/m/skills/analog-gmid-design/assets/tests/tools/reg_check.py --registry C:/g47/m/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root C:/g47/m",
  "receive 사전 판정: PYTHONPATH=%s C:/Python314/python.exe -P C:/g47/scripts/precheck_receive.py C:/g47/pre 7535799302a9ff7cfbfcadb2281d16bf136fadcf <scratch audit 커밋> 20260930-p9-kcl-edges" % C
 ]
}
with open(out, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
print("written", out, {k: v["verdict"] for k, v in rec["checks"].items()})
