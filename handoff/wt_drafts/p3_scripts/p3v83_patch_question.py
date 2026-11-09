# v8.2 -> v8.3 승인 질문 patch (7차 검토 S2·m2, B26 묶음 답 A2-③ 결정). 바꿀 문자열이 정확히 한 번 있어야 한다.
# 사용: C:/Python314/python.exe -B p3v83_patch_question.py <phase3_approval_question.md> <_drafts 디렉터리> <judge v8.3 추출본>
import hashlib, os, sys
P, D, J = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(P, "rb").read().decode("utf-8")
E = []
E.append(("# Phase 3 승인 질문 문안 -- design `30-module-split`(초안 v8.2)", "# Phase 3 승인 질문 문안 -- design `30-module-split`(초안 v8.3)"))
E.append(("오케스트레이터가 AskUserQuestion으로 **다섯 질문**을 한 번에 올린다(v8: A2-③ 추가 -- 5차 검토 S3).",
 "**v8.3(7차 검토 `review7_phase3_v82.md` -- '고친 뒤 승인 요청 가능')**: S1 design §10 E5 판정 python의 `rails` 계약값 판정을 정확 일치로, m1 계약값 `supply_nets`를 P2D library에서 읽음(둘 다 판정을 더하는 쪽, 아래 UD-0 (c) 문장에 반영),\n"
 "m2 UD-0 (c) 기본안의 비용 문장과 '계약 모양 시제품으로 실측', S2 **A2-③ 삭제** -- 2026-10-01 B26 묶음 [card phase] 답 \"phase 3 + 정정 기록 (Recommended)\"(decision 기록 `20261001-b26-phase3-cards`)로 이미 결정됐다. 개정 전 사본 `phase3_approval_question.v8.2.md`.\n"
 "오케스트레이터가 AskUserQuestion으로 **네 질문**(UD-0·D-19·UD-5·UD-1)을 한 번에 올린다(v8에서 더한 A2-③은 v8.3에서 뺐다 -- 다시 묻지 않는다)."))
i = s.index("UD-1 → 같은 design 승인 기록의 범위 설명에 U-03 답으로 적는다, **A2-③ → 새 decision 승인 기록**")
j = s.index("\n", i)
E.append((s[i:j], "UD-1 → 같은 design 승인 기록의 범위 설명에 U-03 답으로 적는다. A2-③은 `20261001-b26-phase3-cards`로 이미 기록됐다(이 질문 밖)."))
E.append(("> **[Phase 3 design 승인 -- 5건]**\n>\n",
 "> **[Phase 3 design 승인 -- 4건]**\n>\n"
 "> (참고: B34·test 보강·backfill·B26-1 네 card의 Phase는 2026-10-01 B26 묶음 [card phase]에서 이미 답하셨습니다 -- `phase: 3`, Phase 3 이동 card 전 병합. 다시 묻지 않습니다.)\n>\n"))
E.append(("빼는 필드는 card 계약에서 유도하고 실측으로 확인했습니다 -- E-LIB의 `load_topology` `meta[\"rails\"]` **하나**(B26-1이 더하는 키, 계약값 = 그 회로의 `supply_nets` 선언).",
 "빼는 필드는 card 계약에서 유도하고 **계약 모양 시제품**(B26-1 실물이 아니라 계약 1·2만 흉내 낸 것)으로 실측했습니다 -- E-LIB의 `load_topology` `meta[\"rails\"]` **하나**(B26-1이 더하는 키). 그 값은 \"`nets` = 그 회로의 `supply_nets` 선언(비교 시작 판 기준)\" 하나짜리 값과 **정확히 같아야** 하고, 다른 필드가 끼거나 사이에 선언이 바뀌면 실패입니다."))
E.append(("(파일럿에서 그 값이 저장 함수까지 넘어가지만 파일에 0회 -- 실측).\n",
 "(파일럿에서 그 값이 저장 함수까지 넘어가지만 파일에 0회 -- 실측).\n"
 ">   기본안의 비용: 빼는 필드 목록은 design에 박힌 상수라, 그 사이 card의 계약이 바뀌거나 새 엔진 card가 끼면 design 개정(승인 diff)을 다시 받아야 합니다(판정자가 목록을 늘릴 수 없음).\n"))
i = s.index(">\n> **A2-③. B34·B26-1(과 그 사이 card 둘)을 병합할 Phase")
j = s.index("Q-B34-PHASE를 닫는다 -- 오케스트레이터 몫.)\n", i) + len("Q-B34-PHASE를 닫는다 -- 오케스트레이터 몫.)\n")
E.append((s[i:j], ""))
E.append(("v8.2에서 고친 것(오케스트레이터 결정):",
 "v8.3에서 고친 것(7차 검토): E5 판정 python -- `rails` 계약값 정확 일치(S1)·계약값 `supply_nets`를 P2D library에서(m1), 둘 다 판정을 더하는 쪽이라 UD-0 (c) 문장에만 반영. A2-③ 결정 반영(§9.2·§11-11·§6.4·D-23·D-28 (e) -- 네 card가 Phase 3 DoD `^phase: 3$` 목록에 듦, B26-1 등가 면제는 M card 이동을 따라갈 필요 없음).\n"
 "v8.2에서 고친 것(오케스트레이터 결정):"))
for o, n in E:
    c = s.count(o)
    if c != 1:
        sys.exit("count %d for: %r" % (c, o[:100]))
    s = s.replace(o, n)
# 대상 판 해시 절을 다시 쓴다
k = s.index("## 대상 판 해시(")
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
F = ["draft_phase3_design_v8.md", "draft_p3_g1.spec.md", "draft_p3_t0.spec.md", "draft_p3_d0a.spec.md", "p3_doc_amendments.md",
     "p3_scripts/e_inst_p3_proposed/e_inst_p3.py", "p3_scripts/e_lib_p3_proposed/e_lib_p3.py"]
old82 = {"draft_phase3_design_v8.md": "dc2a887b2c11f382", "p3_doc_amendments.md": "5104bfe4c23aeebf",
         "p3_scripts/e_lib_p3_proposed/e_lib_p3.py": "c6b82fc7b4cd974c", "p3_scripts/e_inst_p3_proposed/e_inst_p3.py": "7d26134ad00ec504",
         "draft_p3_g1.spec.md": "3a99df21414d6e99", "draft_p3_t0.spec.md": "35f7e3e7850a2847", "draft_p3_d0a.spec.md": "1f9592d491303132"}
lines = ["## 대상 판 해시(v8.3 작성 완료 시점, sha256 앞 16자리 -- 질문 때 다시 계산해 승인 기록에 적는다. v8.3에서 바뀐 것은 design 하나(판정 python 포함), 나머지는 v8.2와 같다)", ""]
for f in F:
    v = h(os.path.join(D, f))
    lines.append("* `%s` `%s`%s" % (f, v, "" if v == old82[f] else "(v8.2: `%s`)" % old82[f]))
lines.append("* 판정 python(design §10 E5 `PYEOF` 블록을 그대로 뽑은 것 -- design 해시에 포함, 따로 적는 것은 재측정 대조용) `%s`(v8.2: `37fecfeae03308fd`)" % hashlib.sha256(open(J, "rb").read()).hexdigest()[:16])
lines.append("* 재측정 스크립트 `p3_scripts/p3v83_judge_scenarios.sh` `%s`, 출력 `p3_scripts/p3v83_judge_scenarios.out.txt` `%s`(design 부록 A F4v83)" %
             (h(os.path.join(D, "p3_scripts/p3v83_judge_scenarios.sh")), h(os.path.join(D, "p3_scripts/p3v83_judge_scenarios.out.txt"))))
s = s[:k] + "\n".join(lines) + "\n"
open(P, "wb").write(s.encode("utf-8"))
print("applied", len(E))
