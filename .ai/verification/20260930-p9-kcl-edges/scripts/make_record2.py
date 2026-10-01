"""P9 2차 순서 7 판정 기록 조립(auditor). 1차 초안(attempt1_order7/record_draft_attempt1.json)을 읽어
2차 커밋·재사용 근거·새 측정(레지스트리 대조·reg_check·V4~V7)으로 고쳐 <out>에 BOM 없는 UTF-8로 쓴다."""
import json, sys
D = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-p9-kcl-edges-audit/.ai/verification/20260930-p9-kcl-edges/"
out, now = sys.argv[1:3]
rec = json.load(open(D + "attempt1_order7/record_draft_attempt1.json", encoding="utf-8"))
M2 = "93b18dba05e304a3ad93a8e34a3492ca8c964eb9"; K2 = "a410f310856d9969d4e6f9980535e52698bca8bd"; T2 = "6bf510b6c7bf427129224338cd64930f0343d5d0"
C = "C:/g47/gmid-gate-cache/7535799302a9ff7cfbfcadb2281d16bf136fadcf"
rec["test_commit"] = T2
rec["code_commit"] = K2
REUSE = ("[2차 재사용 근거 -- auditor 측정, scripts/o7_reuse.py, 결과 a2_reuse.json] 2차 병합본 M2 93b18db(부모 [T2 6bf510b, K2 a410f31], 트리 cc5dc16f = K2 트리, Role: doc·"
         "Change-Id 같음)과 1차 병합본 M1 b7765b0의 diff는 레지스트리 1파일뿐이고, stick_diagram.py blob(ca46b5cd)이 1차 K 16a71fa와 같으며, skills(2ac390f3)·skills/.../tests·"
         "library·workspaces·tools 트리 id가 M1과 같다. T2 트리 = 1차 T 트리(97e27db7, test blob 003c0d1d), base 같음. 그래서 엔진·test·하니스 트리에만 기대는 측정(V1 전체 실행, "
         "V3 변이, DIFF-DUP, 구조 AST, E-LIB, E-INST)은 1차 순서 7 측정(C:/g47/m = M1, attempt1_order7/)이 M2에도 그대로 성립한다. ")
ch = rec["checks"]
ch["V1"]["basis"] = REUSE + "1차 순서 7 측정: " + ch["V1"]["basis"].replace(
    "병합본 M b7765b047ac510b7150a3b99b102891e4083e970(부모 [T c8d55db, K 16a71fa], 트리 09cfe77f = K 트리, Role: doc·Change-Id 같음)을",
    "1차 병합본 M1 b7765b047ac510b7150a3b99b102891e4083e970(엔진·tests 트리가 M2와 같음)을") + \
    ". 2차 T2 수집 837(id 집합 1차와 같음)·T2 전체 822 passed·15 xfailed(2차 순서 3, base_check.json)"
v2 = ch["V2"]["basis"]
i = v2.index("나머지는 모두 충족한다. ")
v2_rest = v2[i + len("나머지는 모두 충족한다. "):]
v2_rest = v2_rest.replace("K 16a71fa(Role: code, 부모 T, stick_diagram.py +3/-14·레지스트리 +6/-6) -> M b7765b0(Role: doc, 부모 [T, K], 트리 = K 트리)",
                          "K2 a410f31(Role: code, 부모 T2, stick_diagram.py +3/-14·레지스트리 +6/-6) -> M2 93b18db(Role: doc, 부모 [T2, K2], 트리 = K2 트리)")
v2_rest = v2_rest.replace("base 7535799(gate master) -> T c8d55db(Role: test, 부모 base,", "base 7535799(gate master) -> T2 6bf510b(Role: test, 부모 base,")
v2_rest = v2_rest.replace("git diff T M = 위 2경로뿐", "git diff T2 M2 = 위 2경로뿐")
j = v2_rest.index("8(c): 308행")
v2_rest = v2_rest[:j] + (
    "8(c)(2차에서 다시 대조, M2 레지스트리): 308행 _metric_kcl_residual·428행 trace_vdd_to_gnd_branches·474행 _kcl_terminal_sign 세 행에 낡은 줄 번호 표기 0"
    "(1차 FAIL이던 428행 'SD:1216-1224'는 '이 함수 안 entry_net/exit_net' 이름 참조로 바뀜 -- AST로 trace_vdd_to_gnd_branches(1187행) 안 중첩 def entry_net·exit_net 실재 확인), "
    "세 행 모두 '부호 규약(_kcl_terminal_sign)'과 '레일 이름 집합'을 적는다; spec card가 낡았다고 지목한 4456·3882-3883·4448·SD:3580·SR:4469-4472·SD:3298·SD:3188-3212·"
    "'(stick_diagram 3148행)' 표기가 레지스트리 전체에 0. 472·473행 호출자 목록이 AST 호출 위치(계약 6)와 같다. 8(d): M2에서 reg_check.py --registry ... --root C:/g47/m2 -> "
    "'발견 0', exit 0. 1차 M1 -> M2 레지스트리 diff는 43·308·428·474행 4줄(문구 보강)뿐")
rec["checks"]["V2"]["verdict"] = "PASS"
ch["V2"]["basis"] = ("equivalence. 1차 시도는 계약 8(c)(428행 'SD:1216-1224' 잔존)로 V2 FAIL, 판정 기록 미커밋(attempt1_order7/record_draft_attempt1.json). 2차는 레지스트리만 고쳤다. "
                     + REUSE + v2_rest)
ch["V3"]["basis"] = (REUSE + "V3 대상(base->병합본 diff가 닿은 .py = stick_diagram.py, 바뀐 def kcl_series_union·kcl_series_union.find)과 변이 28개·변이 id·인벤토리(test 트리 같음)가 "
                     "1차와 같으므로 1차 실행 결과를 재사용한다. 1차 실행: " + ch["V3"]["basis"].replace("--head b7765b0", "--head b7765b0(1차 병합본 M1)"))
ch["V4"]["basis"] = ch["V4"]["basis"].replace("--head b7765b0", "--head 93b18db(2차 병합본, C:/g47/m2에서 새로 실행; 출력이 1차 M1 실행과 바이트 동일)").replace("--root C:/g47/m", "--root C:/g47/m2")
ch["V5"]["basis"] = ("base 판 캐시 weakening_diff.py --root C:/g47/m2 --base 7535799 --head 93b18db -> verdict PASS, findings 없음, diff_paths 없음, diff_hash null, approved false, exit 0. "
                     "2차 순서 3 base -> T2 출력과 같다(K2는 test를 건드리지 않았다). 새 test 파일 추가는 약화 대상이 아니다. 기록할 diff 해시 없음")
ch["V6"]["basis"] = "base 판 캐시 source_lint.py --root C:/g47/m2 --base 7535799 --head 93b18db -> verdict PASS, targets [skills/analog-gmid-design/assets/stick_diagram.py], findings 0, exit 0(2차 새 실행, 1차 출력과 바이트 동일)"
ch["V7"]["basis"] = ch["V7"]["basis"].replace("--root C:/g47/m --base 7535799 --head b7765b0", "--root C:/g47/m2 --base 7535799 --head 93b18db(2차 새 실행, 1차 출력과 바이트 동일)")
ch["V10"]["basis"] = ch["V10"]["basis"] + ". 2차: 엔진·test 트리가 1차 병합본과 같아 그룹 수·_RAIL_NETS 참조 수는 1차 측정이 M2에도 성립(재사용 근거는 V1 basis), 레지스트리 대조·reg_check·V4~V7은 M2에서 새로 쟀다"
ar = rec["auditor_run"]
ar["time"] = now
cmds = ar["commands"]
cmds = [c.replace("<scratch audit 커밋>", "<scratch audit 커밋(2차)>") for c in cmds]
cmds.insert(3, "격리(2차): C:/g47/iso2 = T2 6bf510b(순서 3), C:/g47/m2 = M2 93b18db(bash C:/g47/scripts/o7_attempt2.sh 93b18dba05e304a3ad93a8e34a3492ca8c964eb9: clone --no-hardlinks --no-local --no-checkout <audit worktree>, remote remove origin, checkout --detach; 1차 M1·K 객체 대조용 git -C C:/g47/m2 fetch -q --no-tags C:/g47/m HEAD -- remote 추가 없음), remote 0, status 0줄")
cmds.append("2차 재사용 조건·레지스트리 대조·reg_check·V4~V7: bash C:/g47/scripts/o7_attempt2.sh 93b18dba05e304a3ad93a8e34a3492ca8c964eb9 (o7_reuse.py -> reg_check.py --root C:/g47/m2 -> base 판 캐시 weakening_diff·source_lint·reachability·test_lint --root C:/g47/m2 --base 7535799 --head 93b18db)")
cmds.append("2차 순서 3: bash C:/g47/scripts/run2.sh collect|red (C:/g47/iso2), weakening_diff.py --root C:/g47/iso2 --base 7535799 --head 6bf510b")
ar["commands"] = cmds
v1 = [c for c in cmds if c.startswith("V1: ")]
assert len(v1) == 1
with open(out, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
print("written", {k: v["verdict"] for k, v in rec["checks"].items()})
