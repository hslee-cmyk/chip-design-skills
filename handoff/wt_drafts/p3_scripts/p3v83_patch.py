# v8.2 -> v8.3 design patch (7차 검토 S1·S2·m1·m2 + B26 묶음 답 반영). 바꿀 문자열이 정확히 한 번 있어야 한다(아니면 중단).
# 사용: C:/Python314/python.exe -B p3v83_patch.py <draft_phase3_design_v8.md>
import sys
P = sys.argv[1]
s = open(P, "rb").read().decode("utf-8")
E = []  # (old, new)

# 0. 머리
E.append(("> **[초안 v8.2 -- 저장소 미반영]**", "> **[초안 v8.3 -- 저장소 미반영]**"))
E.append(("> **v8.2(2026-10-01)**: 오케스트레이터 결정(원칙:",
 "> **v8.3(2026-10-01)**: 7차 검토 `review7_phase3_v82.md`와 B26 묶음 답 반영 -- §10 E5 판정 python의 `rails` 계약값 판정을 **정확 일치**로(`hv == {\"__dc__\": \"RailDeclaration\", \"nets\": want}` -- 계약 밖 필드가 끼면 FAIL, S1), 계약값 `supply_nets`를 HEAD가 아니라 **비교 시작 판(P2D) library**에서 `git show`로 읽음(판정 python 인자에 `$P2D`, m1), 승인 질문 UD-0 (c) 기본안에 비용 문장과 '계약 모양 시제품으로 실측'(m2). "
 "**A2-③은 결정됨**(사용자 답 2026-10-01 B26 묶음 [card phase] \"phase 3 + 정정 기록 (Recommended)\", decision 기록 `20261001-b26-phase3-cards`) -- 승인 질문에서 빼고(질문 4개, S2) §9.2 A2-③ 행·§11-11·§6.4·D-28 (e)·E5 행을 결정 사실로 고침, 네 card(B34·b26pre·backfill·B26-1)가 Phase 3 DoD N6.3 목록(`^phase: 3$` spec card)에 든다는 문장(§8.1·§9.1·D-23), §6.4에 B40 반환 키 삭제(U4)와 B26-1 등가 면제의 모듈 접두 처리(U3). "
 "재측정 = `a796468`, 스크래치 `C:/g149`, 스크립트 `_drafts/p3_scripts/p3v83_*`, 실측 부록 A F4v83. 사본 `draft_phase3_design_v8.v8.2.md`, 대응표 `phase3_revision_log.md` '초안 v8.2 → v8.3' 절, 정정 요약 부록 K.\n"
 "> **v8.2(2026-10-01)**: 오케스트레이터 결정(원칙:"))

# 1. §6.4 (A2-③ 인계 -> 결정 사실, 네 card Phase 3 DoD 목록)
E.append(("1001행)이라 Phase 2 DoD의 N6.3 판정 기록 목록에 들지 않는다(인계: 두 card 초안의 `phase: 2`와 승인 기록 A2 ③의 \"Phase 2 진행 중에 병합\" 문장이 이 순서와 어긋난다 -- §11-11).",
 "1001행)이라 Phase 2 DoD의 N6.3 판정 기록 목록에 들지 않는다(v8.3: 네 card(B34·b26pre·backfill·B26-1) 초안은 `phase: 3`이고, 승인 기록 A2 ③의 \"Phase 2 진행 중에 병합\" 문구는 decision 기록 `20261001-b26-phase3-cards`(사용자 답 2026-10-01)가 'Phase 2 DoD 뒤·Phase 3 M card 전(card `phase: 3`)'으로 바로잡았다 -- 그래서 네 card는 **Phase 3 DoD**의 N6.3 목록에 든다, §9.1·§11-11)."))
E.append(("`load_topology`·`l_sharing_classes`·`_metric_kcl_residual` 등 본문 | B34 사이트 표, B26-1 계약 4·5·6 |",
 "`load_topology`·`l_sharing_classes`·`_metric_kcl_residual` 등 본문, `propose_device_roles_gap_fill`의 `refined is None` 분기 반환에서 `unavailable_reason` 키 삭제(B40 -- v8.3, 사용자 답 U4·승인 `20260930-b26-b40-reason-key`; 새 def·이동 단위 변화 없음), 동작 불변 정리 C1·C2(`_propose_L_roles` 중복 None 가드, `open_terminals[0]` -- U3; 최상위 정의 수 불변) | B34 사이트 표, B26-1 계약 4·5·6·13·15 |"))
E.append(("**배정(D-19 -- 사용자에게 따로 묻는다, v6)**:",
 "**B26-1 등가 면제와 M card 이동(v8.3 -- 사용자 답 U3, 기록 `20261001-b26-v3-equiv-range`)**: B26-1은 `find_differential_pair_candidates`의 `range(i + 1, …)` const− 변이 1개를 '변이 id@def 원본 해시'로 면제한다. 변이 id는 `<모듈>:<qualname>:<연산자>:<AST 경로>`라(`draft_v3_exempt_binding.spec.md` 14행) 모듈 접두 `stick_diagram:`을 지니고, 묶기 규칙상 def 해시가 바뀌면 자동 무효다. "
 "M card가 그 def를 다른 MOD로 옮기면 id가 더는 맞지 않는다 -- **그래도 옮길 것이 없다**: (1) 면제는 B26-1 card 자신의 V3 판정(그 card의 base→head, def는 아직 `stick_diagram`)에서 쓰이고 끝난다 -- B26-1은 확정 순서상 M1 전에 병합된다(§8.1) "
 "(2) M card에서 그 def는 G1 이동 인식으로 '옮긴 정의'라 변이 대상이 아니다(E2 ① `mutants` = 0, `defs` = `[]`) (3) DoD E2가 V3를 다시 도는 것은 M1~M6·M8·M9 판정 기록뿐이고(§10 `$S/cards.txt`), 네 card의 판정 기록은 Phase 3 DoD 목록에 들어도 다시 판정하지 않는다(§9.1). "
 "그 def를 **바꾸는** 뒤 card(Phase 4 이후)는 V3 대상이 되고 def 해시가 달라져 면제가 어차피 무효이므로, 모듈과 상관없이 새 면제 승인이 필요하다. "
 "M card 안에서 그 def에 V3를 재는 card가 생기면(이동 인식 밖 -- E2 ①이 FAIL) 그것은 이동이 아니라 변경이라 재승인 대상이다.\n\n"
 "**배정(D-19 -- 사용자에게 따로 묻는다, v6)**:"))

# 2. §8.1 표
E.append(("| P10b | Phase 2 DoD | Phase 2 마지막 card(P9·P10은 `a796468`에 병합됨). Phase 2 DoD의 N6.3 판정 기록 목록은 design 20 §8 card뿐이다 -- **B34·B26-1은 들지 않는다**(A2로 앞당긴 Phase 4 몫, §6.4) |",
 "| P10b | Phase 2 DoD | Phase 2 마지막 card(P9·P10은 `a796468`에 병합됨). Phase 2 DoD의 N6.3 판정 기록 목록은 design 20 §8 card뿐이다 -- **B34·B26-1은 들지 않는다**(A2로 앞당긴 Phase 4 몫, §6.4). v8.3: 네 card(B34·b26pre·backfill·B26-1)는 `phase: 3`(기록 `20261001-b26-phase3-cards`)이라 Phase 3 DoD의 `^phase: 3$` 목록에 든다(§9.1) |"))
E.append(("| Phase 2 DoD PASS | T0·D0a·D0b(phase 3 card) | 계획 991행 \"이전 Phase DoD PASS\"(D-23). 확정 순서상 B26-1·B33 뒤라 자동으로 성립한다 |",
 "| Phase 2 DoD PASS | T0·D0a·D0b(phase 3 card) | 계획 991행 \"이전 Phase DoD PASS\"(D-23). 확정 순서상 B26-1·B33 뒤라 자동으로 성립한다 |\n"
 "| Phase 2 DoD PASS | B34·b26pre·backfill·B26-1(phase 3 card -- v8.3) | 계획 991행 \"이전 Phase DoD PASS\"(D-23). 확정 순서 그대로라 자동으로 성립한다. design 30 승인·U-03은 기다리지 않는다(기록 `20261001-b26-phase3-cards` 범위 설명) |"))
E.append(("* **phase 3 card의 병합 시점(D-23)**: T0·D0a·D0b는 spec card `phase: 3`이고 계획 991행 공통 착수 조건 \"이전 Phase DoD PASS\"가 이 card들에도 걸린다(기본값 = Phase 순서 그대로).",
 "* **phase 3 card의 병합 시점(D-23)**: T0·D0a·D0b는 spec card `phase: 3`이고 계획 991행 공통 착수 조건 \"이전 Phase DoD PASS\"가 이 card들에도 걸린다(기본값 = Phase 순서 그대로). "
 "v8.3: B34·b26pre·backfill·B26-1도 `phase: 3`이다(사용자 답 2026-10-01, 기록 `20261001-b26-phase3-cards`) -- \"이전 Phase DoD PASS\"는 확정 순서(Phase 2 DoD 뒤)로 자동 성립하고, design 30 승인·U-03은 그 기록이 기다리지 않는다고 정했다."))

# 3. §9.1
E.append(("둘을 넣은 것은 틀렸다). 게이트 card(`phase: 0.5`)",
 "둘을 넣은 것은 틀렸다). **v8.3**: 네 card(B34·b26pre·backfill·B26-1)는 spec card `phase: 3`(사용자 답 2026-10-01, 기록 `20261001-b26-phase3-cards`)이라 **Phase 3 DoD의 N6.3 판정 기록 목록**에 든다 -- Phase 2 DoD가 `git grep -l -E '^phase: 2$' <H> -- docs/02-design/specs`로 모은 것과 같은 방식(`^phase: 3$`)이면 네 card가 잡힌다. "
 "Phase 3 DoD는 그 판정 기록을 각 card 병합 때 기록 그대로 센다(다시 판정하지 않는다 -- E2가 V3를 다시 도는 것은 M card뿐이고, E5는 P2D 대 마지막 병합본 비교라 네 card의 의도된 변경은 D-28 (e) 목록으로 이미 들어 있다). 몫은 A2로 앞당긴 Phase 4 몫이라 계획 1001행대로 Phase 4 행 범위에서 빠지지 않는다. 게이트 card(`phase: 0.5`)"))

# 4. §9.2 머리·A2-③ 행
E.append(("### 9.2 사용자 결정(진짜 사용자 몫만 -- 질문 5개(v8: A2-③ 추가), 문안은 `_drafts/phase3_approval_question.md`)",
 "### 9.2 사용자 결정(진짜 사용자 몫만 -- 질문 4개(v8: A2-③ 추가, v8.3: A2-③은 2026-10-01 답으로 결정되어 뺌), 문안은 `_drafts/phase3_approval_question.md`)"))
i = s.index("| **A2-③** | (v8, 5차 검토 S3; v8.1 -- 6차 검토 N3)")
j = s.index("\n", i)
E.append((s[i:j],
 "| **A2-③** | (v8, 5차 검토 S3; v8.1 -- 6차 검토 N3; **v8.3 결정됨**) B34·B26-1과 그 사이 card 둘(앞선 test 보강 card `20260930-b26-pre-test-strengthen`, backfill 결함 card `20261001-b26-backfill-interdig-final-audit`) -- 네 card의 병합 Phase "
 "| **결정됨**(2026-10-01, 사용자 답 B26 묶음 [card phase] \"phase 3 + 정정 기록 (Recommended)\", decision 기록 `20261001-b26-phase3-cards`): 네 card `phase: 3`, 순서 B34 → b26pre → backfill → B26-1 그대로 Phase 2 DoD 뒤·Phase 3 M card 전 병합. 승인 기록 `20260930-b26-before-phase3` ③의 'Phase 2 진행 중' 문구는 그 새 기록이 바로잡는다(옛 기록은 고치지 않음). design 30 승인·U-03을 기다리지 않는다. 판정 기록 V1은 `--gmid-phase=3`(§11-11). 네 card는 Phase 3 DoD N6.3 목록에 든다(§9.1) "
 "| 이 승인 질문에서 묻지 않는다(이미 답함). `_drafts/pending_questions.md` Q-B34-PHASE는 닫음(2026-10-01) |"))

# 5. D-23 행
E.append(("| D-23 | (v6) T0·D0a·D0b(`phase: 3`)도 Phase 2 DoD PASS 뒤에 병합한다. 그 전에는 준비(초안·실측)만. v7: 확정 순서(§8.1)상 B26-1·B33 뒤라 이 조건은 자동으로 성립한다 |",
 "| D-23 | (v6) T0·D0a·D0b(`phase: 3`)도 Phase 2 DoD PASS 뒤에 병합한다. 그 전에는 준비(초안·실측)만. v7: 확정 순서(§8.1)상 B26-1·B33 뒤라 이 조건은 자동으로 성립한다. v8.3: B34·b26pre·backfill·B26-1도 `phase: 3`(기록 `20261001-b26-phase3-cards`) -- 같은 조건이 걸리고 확정 순서상 자동 성립, design 30 승인은 기다리지 않는다(그 기록). Phase 3 DoD `^phase: 3$` 목록에 네 card가 더해진다(§9.1) |"))

# 6. D-28 (e) A2-③ 문장
E.append(("**A2-③ 답과의 관계**: (나)로 네 card가 P2D 앞에 오면 `rails`가 P2D에도 있으므로 판정 python은 P2D `masked.rails`를 '없음 또는 HEAD와 같음'으로 받는다.",
 "**계약값 판정(v8.3, 7차 검토 S1·m1)**: HEAD `masked.rails`는 `{\"__dc__\": \"RailDeclaration\", \"nets\": <P2D library의 그 회로 `supply_nets` 정렬 집합>}`와 **정확히 같아야** 한다 -- 계약 1은 필드 `nets` 하나짜리 값 전체이므로 계약 밖 필드(예: 극성)가 끼면 FAIL이고(B26-2가 극성 필드를 더하는 것은 F2 뒤 기본값이라 이 창 밖 -- 앞당기면 이 목록·상수를 고치는 design 개정), 계약값은 비교 시작 판의 선언이다(P2D와 HEAD 사이에 library `supply_nets`가 바뀌면 FAIL -- HEAD에서 읽으면 같은 값이 양쪽에 들어가 걸리지 않는다). "
 "**A2-③ 답(v8.3 결정)**: 사용자 답 'phase 3 + 정정 기록'(기록 `20261001-b26-phase3-cards`)으로 네 card는 P2D 뒤에 오므로 기본안에서 P2D `masked.rails`는 `<ABSENT>`이다. 판정 python이 'P2D = HEAD와 같은 값'도 받는 것은 대안 (c-2)(B0 판에는 이미 `rails`가 있다) 때문이고, (나) 분기는 없어졌다."))

# 7. §10 E5 블록 판정 python
E.append(("$PY - \"$O\" \"$ISO\" <<'PYEOF'\nimport hashlib, json, os, re, sys\nsys.stdout.reconfigure(encoding=\"utf-8\")\nO, ISO = sys.argv[1], sys.argv[2]          # O = 출력 경로(<iso> 밖), ISO = HEAD로 되돌린 <iso>(계약값의 supply_nets를 HEAD library에서 읽는다)",
 "$PY - \"$O\" \"$ISO\" \"$P2D\" <<'PYEOF'\nimport hashlib, json, os, re, subprocess, sys\nsys.stdout.reconfigure(encoding=\"utf-8\")\nO, ISO, P2D = sys.argv[1], sys.argv[2], sys.argv[3]   # O = 출력 경로(<iso> 밖), ISO = <iso>(git), P2D = 비교 시작 판 -- 계약값의 supply_nets를 P2D library에서 git show로 읽는다(v8.3, 7차 검토 m1)"))
E.append(("    for n in sorted(m1[\"circuits\"]) if m1 else []:   # 뺀 키의 계약값(B26-1 계약 1·2·8): HEAD = RailDeclaration(nets = 그 회로 supply_nets), P2D = 없음 또는 같은 값\n"
          "        nets = json.load(open(os.path.join(ISO, \"skills\", \"analog-gmid-design\", \"assets\", \"library\", n + \".topology.json\"), encoding=\"utf-8\")).get(\"supply_nets\")\n",
 "    for n in sorted(m1[\"circuits\"]) if m1 else []:   # 뺀 키의 계약값(B26-1 계약 1·2·8): HEAD = RailDeclaration(nets = P2D library의 그 회로 supply_nets) 정확 일치, P2D = 없음(기본안) 또는 같은 값(대안 c-2 B0)\n"
 "        g = subprocess.run([\"git\", \"-C\", ISO, \"show\", \"%s:skills/analog-gmid-design/assets/library/%s.topology.json\" % (P2D, n)], capture_output=True)\n"
 "        nets = json.loads(g.stdout.decode(\"utf-8\")).get(\"supply_nets\") if g.returncode == 0 else None\n"))
E.append(("        cok = (want is not None and isinstance(hv, dict) and hv.get(\"__dc__\") == \"RailDeclaration\" and hv.get(\"nets\") == want\n               and (bv == \"<ABSENT>\" or bv == hv))",
 "        cok = (want is not None and hv == {\"__dc__\": \"RailDeclaration\", \"nets\": want}   # 정확 일치 -- 계약 밖 필드가 끼면 FAIL(v8.3, 7차 검토 S1)\n               and (bv == \"<ABSENT>\" or bv == hv))"))
E.append(("print(\"E5 E-LIB rails 계약 FAIL %s (HEAD %s, P2D %s, 기대 nets %s)\" % (n, hv, bv, nets))",
 "print(\"E5 E-LIB rails 계약 FAIL %s (HEAD %s, P2D %s, 기대 nets(P2D library) %s)\" % (n, hv, bv, nets))"))

# 8. §10 E5 행 (iv)와 실측 문장
E.append(("(iv) **빼낸 필드의 계약값(B26-1 계약 1·2·8)**: 회로마다 HEAD `masked.rails` = `{\"__dc__\": \"RailDeclaration\", \"nets\": <그 회로 HEAD topology `supply_nets`의 정렬 집합>}`이고 P2D `masked.rails`는 `<ABSENT>` 또는 HEAD와 같다 -- 아니면 `E5 E-LIB rails 계약 FAIL <회로>`.",
 "(iv) **빼낸 필드의 계약값(B26-1 계약 1·2·8)**: 회로마다 HEAD `masked.rails`가 `{\"__dc__\": \"RailDeclaration\", \"nets\": <그 회로 **P2D** library topology `supply_nets`의 정렬 집합>}`와 **정확히 같고**(다른 필드가 있으면 FAIL -- v8.3, 7차 검토 S1; 계약값은 비교 시작 판의 선언이라 `git -C \"$ISO\" show \"$P2D:…/library/<회로>.topology.json\"`에서 읽는다 -- 7차 검토 m1) P2D `masked.rails`는 `<ABSENT>`(기본안 -- 네 card가 P2D 뒤, 기록 `20261001-b26-phase3-cards`) 또는 HEAD와 같다(대안 (c-2) B0 판) -- 아니면 `E5 E-LIB rails 계약 FAIL <회로>`."))
E.append(("P2D `e_lib.py` 해시를 바꾼 고장 입력 = `E5 INVALID: e_lib_p3(MASK 없음) ≠ e_lib on P2D`.",
 "P2D `e_lib.py` 해시를 바꾼 고장 입력 = `E5 INVALID: e_lib_p3(MASK 없음) ≠ e_lib on P2D`. v8.3 재측정(부록 A F4v83 -- 고친 판정 python을 design에서 그대로 뽑아 같은 다섯 시나리오 + 둘): 위 넷은 같은 결과, `RailDeclaration`에 계약 밖 필드를 더한 시제품(p4)과 HEAD library `supply_nets`에 넷을 더한 시제품(p5)이 `E5 E-LIB rails 계약 FAIL` + `FAIL`(v8.2 판정 python은 둘 다 `PASS` -- 같은 입력으로 재현)."))

# 9. §11-11
i = s.index("11. (v7; v8 -- 5차 검토 S3) 사용자 승인 기록 문장과의 충돌(이 design이 정하지 않는다):")
j = s.index("\n12. (v7) 확인 요청(오케스트레이터)", i)
E.append((s[i:j],
 "11. (v7; v8 -- 5차 검토 S3; **v8.3 해소됨**) 사용자 승인 기록 문장과의 충돌: 승인 기록 `20260930-b26-before-phase3` 27·28행 ③은 B26-1·B34를 \"Phase 2 진행 중에 병합하는 것(card `phase: 2`)\"이라 적었는데,\n"
 "    확정 순서는 둘(과 그 사이 b26pre·backfill -- 넷)을 Phase 2 DoD **뒤**에 둔다. **해소(2026-10-01)**: 사용자 답 B26 묶음 [card phase] \"phase 3 + 정정 기록 (Recommended)\" -- decision 기록 `20261001-b26-phase3-cards`가 ③의 병합 시점 문구를\n"
 "    'Phase 2 DoD 뒤·Phase 3 M card 전(card `phase: 3`)'으로 바로잡고(옛 기록은 고치지 않음), 네 card 초안 머리는 `phase: 3`·`approval: 20261001-b26-phase3-cards`다. 계획 1001행(\"먼저 병합하는 card의 spec card `phase` 값은 병합 시점의 진행 Phase다\")과 맞다.\n"
 "    그 기록은 design 30 승인·U-03을 기다리지 않는다고 적었다. 그래서 이 항목은 승인 질문에서 빠졌고(v8.3, 7차 검토 S2), `_drafts/pending_questions.md` Q-B34-PHASE는 닫혔다.\n"
 "    게이트 사실(`0f23786` 실측, 결정 근거로 남김): `merge_gate.rule10_phase`(532~549행)는 card `phase`를 진행 Phase와 대조하지 않는다. V1 명령 대조(1008~1010행)는 `--gmid-phase=`가 card `phase`와 같은지 본다 -- 그래서 **네 card 판정 기록의 V1은 `--gmid-phase=3`**이다.\n"
 "    `strict_set`(1042행 `if c[\"phase\"] == card[\"phase\"]: keys |= set(c[\"activated_ic_case\"])`)은 같은 Phase card의 엄격 집합인데, 네 card는 `activated_ic_case`가 없고 그 앞에 병합된 phase 3 card도 없어 자기 strict 집합은 빈 집합이며 뒤 phase 3 card의 집합도 바꾸지 않는다.\n"
 "    이 design은 넷을 'Phase 3 M card 전에 병합되는 앞당긴 card'로 다루고, Phase 3 DoD N6.3 목록(`^phase: 3$`)에 든다(§9.1)."))

# 10. 부록 A 행 + 한계 + 부록 K
E.append(("\nv8.2 추가 한계: F3v82의 HEAD 대용은",
 "\nv8.3 추가 한계: F4v83의 p4·p5도 계약 모양 시제품이다(B26-1 실물이 아님). 보이는 것은 '고친 판정 python이 계약 밖 필드와 P2D 대비 library `supply_nets` 변경을 거부한다'이고, v8.2 판정 python이 같은 입력을 받아들였다는 대조다. E-INST 입력은 v8.2와 같은 실측 모양(P2D 대용 `a796468` df36·p3, HEAD 대용 p1 p3)을 `C:/g149`에서 다시 떴다.\n"
 "v8.2 추가 한계: F3v82의 HEAD 대용은"))

for o, n in E:
    c = s.count(o)
    if c != 1:
        sys.exit("count %d for: %r" % (c, o[:120]))
    s = s.replace(o, n)
open(P, "wb").write(s.encode("utf-8"))
print("applied", len(E))
