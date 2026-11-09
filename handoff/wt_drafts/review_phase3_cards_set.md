# 독립 검토 -- phase 3 결정 반영 뒤 네 card + 승인 기록 3건 (2026-10-01)

검토자: 독립 reviewer(작성자 아님). 저장소 읽기 전용, scratch `C:/g144`(검토 뒤 삭제). gate `master` = `0f23786`(로컬 master와 같음).
도구: `git archive gate/master` 사본의 `tools/gates/role_paths.parse_spec_card`, `merge_gate.py parse-approval`, `weakening_diff.py`, `merge_gate.py diff-hash`.

## 판정

**조건부 PASS -- B 1, S 3, minor 6.** 네 card 본문의 phase 3 반영과 세 승인 기록의 원문 인용은 맞다(바이트 일치, 범위 초과 없음).
막는 것은 B26-1의 '승인 줄 배치' 4·5행 시점 하나다. 지금 적힌 대로는 한 번의 시도 안에서 실행할 수 없고, '두 번 시도'를 미리 계획에 넣어야 한다(아래 B1).

---

## (1) 승인 원문 -- 세션 jsonl과 바이트 대조

출처: `63c6146a-….jsonl` 7194행 `AskUserQuestion` `toolu_01KTtsbRiK7S3cv1coUsAyPw`(12:10:47Z = 21:10 KST). 이 세션의 마지막 AskUserQuestion이다(그 뒤 7239~7480행은 Agent 호출과 그 결과뿐).
답은 7241행 tool_result(12:14:58Z = 21:14 KST)에 있다. 질문 원문·선택지 label/description 쌍·답 blockquote를 Python으로 `in` 비교했다(`"…"`로 감싼 문자열, `"label" -- "description"` 쌍 모양).

| 기록 | 질문 | 선택지 2개(label·desc·쌍) | 답 `> label` | 시각·질문 머리 |
|---|---|---|---|---|
| `20261001-b26-phase3-cards` [card phase] | 일치 | 일치 | 일치 | 21:10/21:14, "질문 4개 중 [card phase]" 일치 |
| `20260930-b26-b40-reason-key` [U4 B40] | 일치 | 일치 | 일치 | 일치 |
| `20261001-b26-p9-signature-update` [U5 P9 시그] | 일치 | 일치 | 일치 | 일치 |

범위(scope·덮는 것)가 질문을 넘는가:
* phase3-cards: 네 card의 `phase: 3`, 순서 유지, ③ 문구 정정, design 30·U-03을 기다리지 않음 -- 모두 질문과 선택지 설명에 있다. '병합 순서 유지' 줄의 전체 사슬(P10b → DoD → 34 → 35 → B34 → b26pre → backfill → B26-1 → B33 → Phase 3 M)은 `user_decisions.md` 14행 확정 순서(+ U-BF·b26pre)를 옮긴 것이라 새 결정이 아니다. **넘지 않음.**
* b40: 계약 14의 키 삭제만 덮고 분기·세 키·B39·V3/V7 면제를 뺀다 -- 선택지 설명("이 키 삭제만", "분기와 나머지 세 키는 그대로")과 같다. **넘지 않음.**
* p9: 질문은 "주석 RailDeclaration"이고 기록은 `RailDeclaration`(또는 `"RailDeclaration"`)이다. 지금 단언의 `(list, "list")` 모양을 따른 것이고 `from __future__` 주석 문자열화 대비라 같은 기대로 본다 -- minor m1(한 줄 근거만 더하면 된다).
  그런데 '덮지 않는 것'은 해시가 실제로 묶는 범위와 어긋난다(S1).

## (2) 파서 실행

* `parse_spec_card(text, expect_id)` -- 네 card 모두 통과. 그 전 판(`.pre-phase3`)도 통과:

| card | phase | evidence | gate_change | approval | 절 |
|---|---|---|---|---|---|
| B34 `20260930-b34-grammar-explicit` | 3 (전 2) | red-green | no | before-phase3, **phase3-cards**(추가) | 12 |
| b26pre `20260930-b26-pre-test-strengthen` | 3 (전 2) | test-only | no | **phase3-cards**(새로 생김) | 11 |
| backfill `20261001-b26-backfill-interdig-final-audit` | 3 (전 2) | red-green | no | backfill-interdig-fix, **phase3-cards** | 11 |
| B26-1 `20260930-b26-rail-accessor-set` | 3 (전 2) | red-green | no | before-phase3, **phase3-cards** | 12 |

* `merge_gate.py parse-approval`(파일 이름을 `<id>.md`로 복사): phase3-cards exit 0(decision, target `Q-B34-PHASE-CARDS-PHASE3`), b40 exit 0(decision).
  p9는 자리표시자 그대로면 "diff target은 64자리 소문자 16진"으로 거부(채우기 전이니 맞다). 자리표시자를 64·40·40자리 가짜 16진으로 채운 사본은 exit 0이고 diff_path 1개로 파싱된다. 머리 밖 `<!-- -->` 주석은 파서에 걸리지 않는다(머리 안 `#` 줄만 금지).
* card 머리 `approval:` 줄은 `gate_change: yes`일 때만 `gate_change_ok`(merge_gate 731행)가 본다 -- 네 card 모두 `no`라 게이트에는 사람이 읽는 연결이다. 판정 기록 `approvals[]`는 로더 규칙 6(파일 존재·머리 파싱)이 본다.

## (3) 네 card 사이 일관성

* 순서: 네 card 모두 `… P10b → Phase 2 DoD → V3 binding(34) → V3 scope(35) → B34 → b26pre → backfill → B26-1`과 맞는다(B34 204행·259행은 b26pre·backfill을 생략한 짧은 꼴인데 `user_decisions.md` 14행 인용이라 모순은 아니다 -- minor m2).
* phase 3 문구: 네 card 모두 '결정됨', `--gmid-phase=3`, "Phase 2 DoD N6.3 목록에 들지 않음", ③ 정정은 새 기록이 한다(옛 기록 불변)로 같다.
* phase3-cards 기록 커밋 시점: B34("그 기록이 gate master에 커밋된 뒤 이 card를 커밋"), b26pre·backfill(같은 뜻), B26-1 표 2행("B34 순서 0 커밋보다 먼저, 별도 `Role: doc`") -- 서로 맞다.
* 착수 조건 명시: B26-1만 번호 붙은 착수 조건(5·6 = 34/35 병합, 7 = B34, 11 = phase3-cards 기록 + **Phase 2 DoD PASS**)이 있다. B34·b26pre·backfill은 순서 문장으로만 말하고 'Phase 2 DoD PASS'를 착수 조건으로 쓰지 않는다 -- S3.
  B34 205행은 "범위 card가 늦어져 현행 규칙으로 돌아도 통과하도록 두 규칙을 모두 쟀다"라 35 병합을 착수 조건으로 걸지 않는다(측정 대비라 모순은 아님, S3에서 함께 명시 권고).
* B26-1 '승인 줄 배치' 표 3행(b40 기록): "지금 채울 수 있다 -- 2와 같은 커밋 또는 그 뒤"인데 머리 줄은 아직 초안에 없다. 2행(phase3-cards)은 같은 조건인데 초안에 이미 있다. 같은 커밋으로 올릴 수 있으니 셋째 줄 `approval: 20260930-b26-b40-reason-key`를 지금 초안에 넣으면 순서 0 커밋 때 손볼 일이 하나 준다 -- minor m3.
  (b40 기록 본문 "B26-1 card의 머리 `approval:` 줄이 이 기록을 가리킨다"도 그때 참이 된다.)
* B26-1 착수 조건 2 "계획 정정 커밋(`draft_b26_plan_patch.md`)" -- `8356c1e`(계획 정정(A2, 승인 20260930-b26-before-phase3))로 이미 충족인데 '충족' 표시가 없다 -- minor m4.

## (4) U5 위험 두 가지 -- 실측과 절차 제안

### 실측(프로토타입 B26-1 test 변경, scratch 복제 `0f23786` 위 커밋 3개)

| 커밋 | 내용 |
|---|---|
| u5 | `test_dup_kcl_edges.py` 두 시그니처 test를 U5 기대로(목록에 `"rails"`, 앞 두 매개변수 루프, `rails` KEYWORD_ONLY·기본값 없음·주석 `(RailDeclaration, "RailDeclaration")`) |
| calls | 같은 파일 파라미터 test 2개의 직접 호출에 `rails=_b26_rails(nl)`(새 모듈 helper), `test_selftest_stick_diagram.py` 73행·474행 호출에 `rails=rail_declaration({"supply_nets": [...]})` 인라인 |
| fix | `test_selftest_sizing_recipe.py` topology dict 12개에 `"supply_nets": ["vdd", "gnd"]` 삽입 |

gate 판 `weakening_diff.py` 결과:

| 구간 | verdict | 발견 | diff_paths | diff_hash |
|---|---|---|---|---|
| base..u5 | FAIL | 2(두 시그니처 test '비교 완화') | P9 파일 1개 | `4998e7fe…` |
| base..calls | FAIL | 같은 2 | P9 파일 1개 | `6d03b274…` |
| base..fix | FAIL | 같은 2 | P9 파일 1개 | `6d03b274…` |
| u5..fix(호출·픽스처만) | **PASS** | **0** | [] | null |

`merge_gate.py diff-hash --base 0f23786 --head <calls|fix> <P9 경로>` = `6d03b274…`(도구 출력과 같다).

결론:
1. **기존 픽스처의 `supply_nets` 추가와 호출의 `rails=` 추가는 V5 발견이 아니다.** `features()`의 리터럴 비교는 `SequenceMatcher` opcode 중 `replace`·`delete`만 발견으로 세고 순수 삽입은 세지 않는다. `rails=` 추가는 `Assert`의 `Compare`를 바꾸지 않는다. 그래서 '승인 줄 배치' (6)행은 test-author가 기존 리터럴을 **바꾸거나 지우지** 않는 한 생기지 않는다(새 test 파일은 base 단위가 없어 발견 0).
2. **U5 변경은 반드시 발견이 난다** -- 단언이 강해져도 `cmp_ops`(정렬한 연산자 다중집합)가 달라지면 '비교 완화'로 센다. 그래서 diff 기록은 꼭 필요하다(발견 0 → 해시 null이 될 걱정은 없다).
3. **해시는 그 경로의 blob 전체를 묶는다.** P9 파일 안의 `rails=` 호출 추가가 해시를 `4998…` → `6d03…`로 바꿨다. 즉 p9 기록의 target은 그 파일의 base..T **전체** 변경(시그니처 단언 + 호출 `rails=` + helper)을 덮는다 → S1.

### S1 -- p9 기록 '덮지 않는 것'이 해시와 어긋남

기록은 "P9 계약 test의 다른 test·픽스처(넷리스트만 쓰는 직접 호출에 `rails=`를 더하는 것은 … 이 기록 밖 -- `weakening_diff.py`가 그 변경을 표시하면 따로 승인)"이라 적었다. 그러나 같은 경로의 변경은 한 해시에 들어가므로 '따로 승인'할 수 없다(경로마다 해시가 아니라 발견 경로 합집합에 해시 하나).
고칠 문장(제안): "target 해시는 이 경로의 base..T blob 변경 전체를 묶는다. 그 안의 직접 호출 `rails=` 추가·helper는 V5 발견이 아니다(실측: 삽입은 발견 아님) -- 이 기록은 그 줄들의 판정 불변을 승인하는 것이 아니라 같은 blob에 함께 실릴 뿐이다. `weakening_diff.py` 발견이 두 시그니처 test 밖(같은 파일의 다른 단위 포함)에서 나면 이 기록을 쓰지 않고 멈춘다." '채우는 법' 3에 "발견 단위가 정확히 두 시그니처 test인지 확인"을 더한다.

### B1 -- 기록 4·5행이 한 시도 안에서는 head 트리에 들어갈 수 없다(두 번 시도를 계획에 넣을 것)

근거(gate `0f23786` 코드):
* `weakening_diff.approved_hashes(root, ns.head)`와 `mutate_changed._approved(root, ns.head)` -- V5·V3 면제를 **head 트리**에서 찾는다.
* `merge_gate.receive`(1135~1168행): `old..M^1`은 `Role: test` 커밋만의 첫 부모 사슬이어야 하고(`_first_parent_chain(repo, M1, old, …)`), `M^1..M^2`는 `Role: code`만, **M 트리 = M^2(K) 트리**, 커밋 집합 = test 사슬 ∪ code ∪ {M, new}(끼어든 커밋 거부). 병합 규칙 9는 V5 basis 해시를 new 트리 기록에서 찾는다.
* 따라서 승인 기록은 test 사슬·code·M·audit 커밋 어디에도 넣을 수 없고, **T의 첫 부모 사슬 시작점(old = base 쪽 master)**에 있어야 한다. 그런데 기록 target은 T(4행)·K(5행)가 생긴 뒤에야 잴 수 있다.
  B26-1 표 4행 "test 커밋 T 뒤·auditor V5 판정 전", 주의 (a) "기록 커밋을 병합 후보 사슬에 넣는 방법은 오케스트레이터가 순서 6 전에 정한다", p9 기록 '채우는 법' 1("auditor가 V5를 재기 전")·2("diff_base = 판정 기록 base_commit과 같은 커밋")는 같은 시도 안에서는 실행할 수 없다.
* 선례는 모두 재시도였다: P5b `20260929-p5b-chain-tests`(diff_base `98bd969` ≠ 판정 base `7a1e191`, 기록이 base 커밋 `7a1e191`에 들어감 + 'R1 운반 blob'), P4 `20260930-p4-relocate-test-retire`(base `fb8ee35`가 기록 포함), P10b `d6a9778` → `0f23786`('재시도 개정'). 절차 정본은 design 05 §12 **'V5 승인 운반'**(U-42 채택).

제안 절차(4·5행을 한 번의 재시도로 묶음):
1. **1차 시도(병합 안 함, 계획된 측정 시도)**: 순서 0~3 그대로(T1). auditor 순서 3이 `weakening_diff.py --base B1 --head T1`을 `base_check.json`에 남긴다 -- 기대: FAIL, 발견 = 두 시그니처 test '비교 완화'뿐, `diff_paths` = [P9 경로]. 다른 경로·단위에서 발견이 나면 멈추고 (6) 승인을 묻는다.
   V5 FAIL은 예정된 것이므로 멈추지 않고 순서 5(K1)까지 가서 auditor가 병합 후보 상당(T1+K1)에서 V3를 잰다 -- 기대 생존 = `range(i + 1, …)` const− 1개(U3). 생존이 그 1개가 아니면 멈춘다.
2. **운반(정리 전에)**: 05 §12 (2)대로 발견 경로 blob을 `docs/03-analysis/<feature>-<design>/v5-carry/20260930-b26-rail-accessor-set/<blob id>.blob` + `paths.tsv`로. p9 기록: `diff_base` = B1, `diff_head` = T1, `diff_path` = P9 경로, `target` = 1의 `diff_hash`(= `merge_gate.py diff-hash`). v3-equiv-range 기록: 1에서 auditor가 `mutants()`로 잰 id@def 원본 해시.
   두 기록 + 운반 blob + card 개정(머리 `approval:` 줄 둘 추가, 1차 시도 기록) = `Role: doc` 커밋 하나, gate push(push 단독 실행·전체 출력 확인).
3. **2차 시도**: base B2 = 2의 master. 착수 전 `git diff --quiet B1 B2 -- <P9 경로>`(base blob 같음 → 해시 식 입력 같음). test-author는 `paths.tsv`대로 운반 blob을 `cp`로 둔다(P9 파일은 손으로 다시 쓰지 않는다 -- blob이 1바이트라도 다르면 해시가 바뀐다). 나머지 test 파일은 1차와 같게 다시 만든다(V5 발견이 없으므로 blob이 달라도 무방하나, 같으면 auditor 대조가 싸다).
   code-author는 K1의 면제 대상 def(`find_differential_pair_candidates`)를 `git show K1:<path>` → Edit로 **같은 글자**로 만든다(역할 agent에 cherry-pick/apply 금지 원칙). def 원본 해시가 다르면 v3-equiv-range가 자동 무효(착수 조건 8 마지막 문장) → 재승인.
4. auditor 순서 3·6: V5 base B2..병합본 `approved: true`, 해시 = 기록 target(B1·B2 사이 P9 blob 같음을 basis에 적는다 -- P5b 판정 기록 V5 basis 문장 모양). V3 exempt 1, 나머지 killed.
5. 병합 뒤 운반 디렉터리 삭제(`Role: doc`, 05 §12 (4)).

card·기록 문구 수정(제안): B26-1 표 4행 시점 = "1차 시도 T1 뒤(순서 3 V5 FAIL 기록 후)·2차 시도 착수 전, 05 §12 'V5 승인 운반'", 5행 = "1차 시도 K1 뒤·2차 시도 착수 전", 주의 (a)를 위 절차로 대체. p9 기록 '채우는 법' 1·2·4를 "1차 시도 T1", "diff_base = 1차 시도 base(2차 base와 P9 blob 같음)", "2차 병합본에서 auditor가 잰 diff_hash가 같아야 함"으로.
대안(재시도 비용을 줄이려면): 1차 시도를 순서 3에서 멈추고 p9만 운반하면 V3 면제(5행)가 또 한 번의 재시도를 부른다 -- 합치는 위 안이 싸다.

## (5) 남은 'Phase 2 진행 중'·phase 2 문장

* 네 card 본문: 'Phase 2 진행 중'은 모두 "A2 기록의 문구이며 phase3-cards가 바로잡는다"는 인용 맥락으로만 남았다. 
  측정 사실로 남은 `--gmid-phase=2`: B34 347행(V3 계획 실측 명령), B26-1 367행(V3 실행 인자), B34 301행(문서 시퀀스 모의 "phase 2" -- 같은 줄에 `phase: 3` 변형도 같은 결과라 적음). phase 2·3의 test 결과·strict·N/A가 같다는 실측(B34 304행)이 있어 사실로는 문제없다.
  다만 auditor가 명령을 그대로 베끼지 않도록 두 줄 끝에 "(판정 명령은 `--gmid-phase=3`)" 한 마디 -- minor m5.
* **S2 -- `b26_backfill_briefs.md`(21:03, 결정 21:14 이전)가 아직 phase 2다.** 117·156행(parse 확인 "phase 2"), 172·229·258행(역할 브리프 "phase 2"), 214행(자기 점검 `--gmid-phase=2`), **278행(auditor 순서 7 V1 `--gmid-phase=2`)**, 258행 approval 목록에 phase3-cards 없음.
  auditor가 이 브리프대로 V1을 쓰면 `v1_command_check(…, phase=card["phase"]="3")`가 `--gmid-phase=3` 토큰을 요구해 병합이 거부된다. `b26bf_kit/sim_launch_bf.sh`·`v3_replica.py`도 phase 2 전제인지 같이 갱신.
* `b34_briefs.md`는 `<P>` 자리표시자를 쓰고 60행에 "(가)면 `<P>` = 3"이라 적었다 -- 결정이 났으니 `<P>`를 3으로 박고, 57행 "design 30 승인·U-03까지 B34에 거는지는 문서에 없다"를 "phase3-cards가 기다리지 않는다고 정함"으로 -- minor m6. `b34_commit_plan.md` 35·102~103행((가)/(나) 조건문, `--gmid-phase=2` 예시)도 같은 정리.
* `phase3_followups_from_b26.md`는 design 30 쪽 정리 목록이라 결정과 맞다.

## 지적 목록

| # | 등급 | 대상 | 내용 | 조치 |
|---|---|---|---|---|
| B1 | B | B26-1 '승인 줄 배치' 4·5행, 주의 (a), p9 기록 '채우는 법' 1·2·4 | 기록이 head 트리에 있어야 하는데(V5·V3 둘 다 head에서 찾음) 병합 모양(M 트리 = K 트리, 끼어든 커밋 거부, test 사슬이 old에서 시작)상 같은 시도 안에 넣을 수 없다 | 계획된 2회 시도(05 §12 V5 승인 운반 + V3 면제 기록을 한 `Role: doc` 커밋으로) -- 위 (4) 절차 |
| S1 | S | p9 기록 '덮지 않는 것' | 해시가 P9 파일 blob 전체를 묶어 같은 파일의 `rails=` 호출 추가도 함께 실린다. '따로 승인'은 불가능 | 문장 교체 + 발견 단위 확인 단계 추가 |
| S2 | S | `b26_backfill_briefs.md` | phase 2·`--gmid-phase=2`(auditor V1 포함)·approval 목록 미갱신 | phase 3·`--gmid-phase=3`·phase3-cards 추가, 키트 스크립트 확인 |
| S3 | S | B34·b26pre·backfill | 'Phase 2 DoD PASS'·phase3-cards 기록 커밋·(B34·backfill) 34/35 병합을 착수 조건으로 명시하지 않음(순서 문장뿐) | B26-1 조건 11처럼 한 줄씩 |
| m1 | minor | p9 기록 | 주석 `"RailDeclaration"` 문자열 허용 근거 한 줄 | 기존 `(list, "list")` 모양을 따른다고 적기 |
| m2 | minor | B34 204·259행 | 순서 사슬이 b26pre·backfill을 생략 | 전체 사슬로 |
| m3 | minor | B26-1 머리 | b40 기록 줄이 2행과 같은 조건인데 아직 없음 | 셋째 줄 지금 추가 |
| m4 | minor | B26-1 착수 조건 2 | `8356c1e`로 충족 표시 없음 | '충족' 표기 |
| m5 | minor | B34 347행, B26-1 367행 | 측정 명령 `--gmid-phase=2` | "(판정 명령은 3)" 덧붙임 |
| m6 | minor | `b34_briefs.md` 57·60행, `b34_commit_plan.md` 35·102행 | 조건문·`<P>`가 결정 전 상태 | 3으로 확정 |

참고(지적 아님): b40 기록 id 접두 `20260930` ≠ `date: 2026-10-01` -- id는 사용자가 선택지 설명에서 본 이름이고 로더 규칙 6은 id 앞 8자리가 실제 날짜인지만 본다(통과).
B34 v2 → pre-phase3 차이(계약 8 새 프로세스 oracle, 계약 1~3 `pytest.raises`, 프로토타입 000)는 오케스트레이터 결정 0.6-6 범위이고 이번 phase 3 편집과 겹치지 않는다(phase 3 편집 diff = 머리 2줄 + 결정 5 문단만).

## 검토 환경 기록

* 처음 Python 경로 문자열 실수로 저장소 루트에 `g144q.json`(jsonl 추출물)이 생겼다. 바로 scratch로 옮겼고 `git status --short` 해시가 시작값(`168fd530…`)과 같아진 것을 확인했다. 저장소 내용 변경은 없다.
* 프로토타입 커밋은 scratch 복제(`C:/g144/c`, hooks 없음)에서만 했다. 끝에 `C:/g144` 삭제, 저장소 `status --short` 해시 재확인.
