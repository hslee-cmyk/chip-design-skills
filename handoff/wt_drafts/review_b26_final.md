# 독립 검토 -- B26 통합 질문(최종안)·b26pre v4·B26-1 v5 (사용자에게 묻기 전)

검토자: 독립 reviewer(작성자 아님). 2026-10-01. 저장소 읽기 전용(쓰기·상태 변경 git 없음), scratch `C:/g133`(끝에 삭제).
사본: `git archive a796468` + B34 코드 변경(`b26_reconcile/mk_b1.py`의 `build_b34`, 사이트 1·2·3·11·11b) = 모의 base `b1`. 엔진은 `766b5c2` 이후 같다(`git diff --stat 766b5c2 a796468 -- assets`는 test 2파일뿐).
gate 사실 확인은 `0f23786` 판 `merge_gate.py`·`role_paths.py`·계획서·conftest. Python `C:/Python314/python.exe -B`, `PYTHONHASHSEED=1`.

## 판정: **묻기 전에 고칠 것 3건 (F1~F3), 이후 'ready to ask'**

수치·등가·정리·C3 관련 사실은 독립 재측정으로 모두 맞았다. 세 결함은 질문 본문이나 착수 조건에 있다. 하나(F1)는 착수 순서상 지킬 수 없는 조건이다.

---

## 1. 변이 재측정 (질문 Q1의 사실)

방법: 변이마다 `b1`의 새 사본을 만들고 변이를 넣는다. 그다음 (i) **기존 test 전체**를 돌리고(작성자는 def 인벤토리만 돌렸다. 나는 `assets/tests` 전체, 시제품 제외 `--ignore`), (ii) 시제품만 따로 돌린다. 시제품은 b26pre v2 17, **내가 계약 11 문장만 보고 새로 쓴 trace test 2**(`layer1_fallback` 제외), 작성자 trace 시제품 2다.
변이 없는 사본 결과는 `2 failed, 869 passed, 15 xfailed` / 시제품 `21 passed`다. 2 failed는 `test_ts6_probe_relocate` 2개다(사본에 `.git` 없음). 작성자도 같은 이유로 이 둘을 제외했다. 아래 '생존'은 이 기준선과 실패 목록이 같다는 뜻이다.

| 표 행 | 변이(b1 줄) | 기존 test 전체 | 시제품 | 표의 판정 | 일치 |
|---|---|---|---|---|---|
| 1 | SR 11696 `split = find_min_crossover…` 삭제 | 생존 | 죽음 `test_b26pre_euler_fixup_group_split` | b26pre | O |
| 7·9 | SR 9404 `repaired_rows, … = repair_matching_safety(` 삭제 | 생존 | 죽음 `test_b26pre_ofcb_lutless_repair` | b26pre | O |
| 12 | SR 11800 `_backfill_interdig_ok(result)` 삭제 | 생존 | 생존 | 결함(backfill) | O |
| 15 | SR 11879 같은 문장(루프 뒤) 삭제 | 생존 | 생존 | 결함(backfill) | O |
| 20 | SD 2161 `if gm_id_roles is None: return None` 삭제 | 생존 | 생존 | 등가 | O |
| 21 | SD 2165 `if candidates is None: return None` 삭제 | 생존 | 생존 | 등가 | O |
| 34 | SD 4291 `open_terminals[0]` → `[-1]` | 생존 | 생존 | 등가 | O |
| 24 | SD 1563 `range(i + 1,` → `range(i + 0,` (const−) | 생존 | 생존(내 test·작성자 test 모두) | 등가 | O |
| 23 | SD 1563 `range(i + 2,` (const+) | 생존 | 죽음: 내 test 2개 + 작성자 test 2개 | trace | O |
| 22 | SD 1563 `range(i - 1,` (arith) | 생존 | 죽음: 내 `three_order` + 작성자 `three_branches_order` | trace | O |
| 41 | SD 4521 `if disp.case_collisions:` 삭제 | 생존 | 죽음 `test_b26pre_case_collisions` | b26pre | O |
| 49 | SD 6884 `mc["current_mirror"]` 루프 삭제 | 생존 | 죽음 `test_b26pre_full_audit_mirror_undisposed` | b26pre | O |
| 42 | SD 3278 `if inputs or outputs or …:` 삭제 | 생존 | 죽음 `test_b26pre_vsid_gap_fill_ports` | b26pre | O |

13행 14변이를 확인했다(요구 6행 이상). 생존 판정은 인벤토리가 아닌 **전체 suite**에서도 그대로였다. 인벤토리 근사 때문에 생긴 거짓 생존은 없다.
표 묶음 합계를 행별로 다시 셌다: 자기 계약 26 = E1 14(26~33·35~40) + E3 6(43~48) + E5 2(19·25) + 7(c) 1(18) + 직접 호출 3(4~6). b26pre 16, trace 2, backfill 2, 등가 4. 합 50. 질문 본문 수치와 같다.

### 1.1 '진짜 등가 4' -- 구별 입력 만들기 시도

| 등가 | 구별 입력이 없는 이유(코드로 확인, `a796468` 1504~1613·2051~2192·4280~4300) | 시도 |
|---|---|---|
| 가드 2161 삭제 | `_propose_gm_id_roles`는 `candidates is None`일 때만 `None`을 낸다. 같은 인자로 `find_differential_pair_candidates`를 다시 부르면 다시 `None`이고, 2165 가드가 같은 `None`을 낸다. 두 번째 호출은 순수 함수다(`suggest_vertical_stack_composites`의 `None`은 B34 뒤 `devs` 빈 경우뿐이고 print·전역 상태가 없다). 차이는 중복 계산 시간뿐이다 | gate 없는 `fx` 직접 호출: 원본·변이 모두 `None` |
| 가드 2165 삭제 | 대칭: `gm_id_roles`가 None이 아니면 `candidates`도 None이 아니다 | 같음 |
| `[0]`→`[-1]` | 바로 앞 `len(open_terminals) != 1 → continue` | 원소 1개 목록에서는 같다 |
| `range(i, …)` | 늘어난 짝 `j == i`는 같은 chain 객체다. 모든 `pos`에서 `a == b`로 `continue`하고 부작용(`seen`·`out`)이 없다 | 내 trace test와 작성자 `exp_trace` n=2·3 출력이 같다. 전체 suite도 생존 |

네 개 모두 등가 주장이 맞다. backfill 2개는 등가가 **아니다**. `exp_backfill3`를 `C:/g133/b1`에서 다시 돌렸다: max_rounds=1에서 원본 `interdig_ok=[False]`, 루프 뒤 삭제 변이 `[True]`, audit 3b `[True]`. max_rounds 2·3·5에서는 루프 안 삭제 변이가 `[True]`다. 질문의 '구별 입력 있음' 문장이 맞다.

### 1.2 정리 C1·C2가 동작을 바꾸지 않는지

* `b1 + C1·C2`(`b26v4c.cleanup`과 같은 치환): 기존 test 전체가 기준선과 같고(`2 failed[ts6], 869 passed`) 시제품 21 passed다.
* library 9회로 × `refine_differential_and_mirror_relations`·`propose_device_roles_gap_fill(topology device_roles)`·`_propose_L_roles` 반환이 원본과 **9/9 같다**(JSON 정규화 비교).
* E4: C1 뒤 남는 `gm_id_roles` 가드를 지우면 gate 없는 `fx`에서 `_propose_L_roles`가 **TypeError**를 낸다(원본·C1C2는 `None`). B26-1 계약 14 E4가 이 변이를 죽인다는 주장이 맞다(작성자 B 측정에서 `test_b26_e4_propose_gateless_direct`).

### 1.3 C3가 새 생존 7을 만드는지

* 분류 재실행(`plan_measure` 방식, 내 드라이버 `cls3.py`): 대상 A 299, B(C1·C2·C3) 313, C12 299. B에만 있는 21은 전부 `find_differential_pair_candidates` 루프 본문이다(들여쓰기가 바뀐 문장이 '바뀐 문장'으로 셈된다).
* 작성자의 REMAIN 7(`if a == b`·그 `continue`, `if ta.kind != tb.kind or ta.gate == tb.gate`·`continue`, `if key in seen`·`continue`, `seen.add(key)`)을 `b1 + C1·C2·C3` 사본에서 하나씩 지웠다. **7개 모두 전체 suite와 시제품 21에서 생존**했다. C3 base 자체는 기준선과 같다. 'C3는 새 생존 7'이 맞다.
* 관찰: 7개 중 `if a == b` 쌍은 등가로 보인다(a == b이면 gate도 같아 다음 가드가 건너뛴다). `kind/gate` 가드 삭제는 거울쌍 입력으로 죽일 수 있다. 질문의 '일부는 죽일 수 있고 일부는 등가로 보인다'와 맞는다.

### 1.4 시나리오 C(C1·C2 → 남는 1)

* 대상 id 차이를 직접 쟀다. C12 − A = 4: `_propose_L_roles stmt_delete body[5]`(지운 가드 바로 뒤 문장)와 `propose_device_roles_gap_fill body[40].body[9]` 삭제·cmp_flip 2(바뀐 `open_net`을 읽는 문장). A − C12 = 4: 지운 가드의 cmp_flip·`return` 삭제, `[0]` const±.
* 'def별 id가 A·B와 같다'는 주장도 맞다: `_propose_L_roles`·`propose_device_roles_gap_fill`의 C12 id 집합 = B, 나머지 def = A.
* 새 4개는 B 측정(`plan_B_proto.jsonl`)에서 모두 죽었다(E1 3, E1+b26pre 1). 그래서 '남는 1'이 맞다. 단 **299 = 299는 우연히 같은 수다**(4 빠지고 4 들어옴). F3 참고.

---

## 2. 계약 11 이탈(`layer1_fallback` 원소를 판정에서 뺌)

* **원칙상 맞다.** 코드 주석(SD 1584~1596)은 층위1 폴백이 'branch-composite 비교가 이미 찾은 걸 덮어쓰지 않고, **못 찾던 것만 보충**'한다고 적는다.
  그런데 중복 키가 `("layer1_fallback", frozenset)`라서 trace가 이미 찾은 `("Mi1","Mi2")`가 n=2에서 한 번 더 나온다. docstring의 '(direction, frozenset) 기준 direction별 1건'을 글자대로 읽으면 허용되지만, 주석 의도와는 어긋난다.
  해석이 갈리는 동작을 기준값으로 박지 않는 것은 '거짓 기준값 금지'와 맞는다. 백로그 B50으로 등록돼 있다(`backlog_additions.md` 24행). backfill과 달리 지금 사용자에게 물을 필요는 없다: 고칠지는 별도 card이고, B26-1 V3 대상과 무관하다.
* **빼도 죽는다(재측정).** 계약 11 문장만 보고 쓴 내 test(`TR`은 `vdd_to_gnd`·`gnd_to_vdd`만)로 돌렸다: const+ → 2 test 실패, arith → `three_order` 실패, const− → 통과(등가). 작성자의 원소 포함 판과 같은 결과다.
  폴백 루프의 변이(표 25행 `stmt_delete body[9]`)는 B26-1 E5가 죽이므로 판정에서 빠지는 것은 없다.
* 사소한 점: b26pre v4 '19 passed' 시제품(계약 10 v3 단언 + 계약 11 제외판)은 `C:/g127`과 함께 지워져 남아 있지 않다. 계약 11은 위에서 독립 재현했다. 계약 10 v3 단언은 N2w 대상이 아니라 질문에는 영향이 없다.

## 3. B26-1 v5 계약 15와 V3 집계·범위 정책

* **N2w와 맞는다.** 범위 정책(승인 `20260930-v3-changed-stmt-scope`) 아래에서 C1·C2는 B26-1이 이미 바꾸는 def 안의 바뀐 문장이다. 그래서 '지운 문장 바로 뒤 문장'과 '같은 블록 뒤쪽에서 바뀐 이름을 읽는 문장'이 새 대상이 된다(§1.4의 4개).
  계약 15가 판정을 숨기는 정리가 아니라는 점은 확인했다: 동작 불변(§1.2), 새 대상 4개는 계약 7(e) E1·b26pre가 죽인다.
* **299 집계**: 'V3 계획' 1의 '착수 base 299, C1·C2 뒤에도 299'는 수로는 맞다. 하지만 같은 대상이라는 뜻이 아니다 → F3.
* backfill card의 구현은 code-author 몫이다('사전 측정한 후보 하나'). 299는 그 후보(두 줄 삭제)를 전제한다. 이 전제는 auditor 재측정 문장이 덮는다(그대로 둬도 된다).

## 4. Q-B34-PHASE

`0f23786` `merge_gate.py`에서 확인한 사실:
* 1009 `if phase_tok != [phase]` 실패, 1213 `v1_command_check(…, phase=card["phase"])`, 1042 `strict_set`의 `if c["phase"] == card["phase"]`, 1210 conftest에 `--gmid-phase`가 있을 때만(있음). 1193·1311 `rule10_phase`. 줄 번호 모두 맞다.
* 게이트는 card phase를 '현재 Phase'와 대조하지 않는다(맞음).
* `rule10_phase`의 N/A 허용(계획 N4.2 도입: V7=2, V8=4, V9=6b): phase 2·3 모두 V8·V9 N/A 가능, V1~V7 PASS 필수로 **같다**.
* strict 집합: 병합된 판정 기록 32건 중 phase 2 = 15건, `activated_ic_case` 합집합 **빈 집합**. phase 3 = 0건으로 빈 집합. **같다**.
* conftest xfail: 저장소 `gmid_ic` 표식 Phase는 1·4·6a·6b·6c뿐이고 2·3 표식은 0개다. `--gmid-phase=2`와 `3`의 수집·xfail·결과가 **같다**.
* 따라서 네 card에서 실제로 갈리는 것: 머리 `phase:` 값, 판정 기록 V1 명령의 `--gmid-phase=` 토큰, Phase별 판정 기록 분류(Phase 2 DoD 뒤에 `phase: 2`면 어느 DoD에도 안 잡힘 / `phase: 3`이면 Phase 3 DoD N6.3에 'A2 앞당김' 줄 필요), 승인 기록 `20260930-b26-before-phase3` ③ 문구(B34·B26-1만 해당).

---

## 고칠 것

**F1 (차단) -- B26-1 착수 조건 8이 지킬 수 없는 순서다.**
`draft_b26_1.spec.md` 착수 조건 8과 승인 필요 목록 ①은 '등가 면제 승인 기록 커밋'을 **착수 전** 조건으로 둔다. 그런데 Q1의 면제 문안 `target`은 `…:<B26-1 병합본 AST 경로>@<그 def 원본 해시>`이다. 면제 묶기 규칙(`20260930-v3-exempt-binding`, 원소 = 변이 id@head def 해시)상 이 값은 code 커밋 K 뒤 auditor가 `mutants()`로 잴 때만 나온다. 질문 문안 자신도 'auditor가 병합본에서 확정해 적는다'고 쓴다.
고칠 것: 착수 조건 8을 'Q1 답 기록(`user_decisions.md`) + b26pre 병합 + backfill 병합'으로 바꾼다. 면제 기록은 'K 뒤·병합 전, auditor 측정 id·해시로 커밋하고 card `approval` 줄 갱신'(P10b `d6a9778` → `0f23786` 선례)으로 옮긴다. 재시도에서 `find_differential_pair_candidates`가 바뀌면 재승인(묶기 규칙)이라는 한 줄도 더한다. 질문 Q1 1번 (d)에도 '기록은 구현 뒤 해시로 커밋'을 한 구절 넣는다.

**F2 (질문 사실) -- Q-B34-PHASE가 질문 본문에 없고, 대상 card 하나가 빠졌다.**
* 통합 질문은 Q-B34-PHASE를 `pending_questions.md`로 가리키기만 한다. 거기에는 '선택지 후보' 메모만 있어 AskUserQuestion에 그대로 실을 본문이 없다.
* 대상 목록이 'B34·b26pre·B26-1'로 적혀 있다. **backfill card(`20261001-b26-backfill-interdig-final-audit`, 머리 `phase: 2`, 순서상 Phase 2 DoD 뒤)가 빠졌다.** 네 card 모두 같은 문제다.
* `pending_questions.md` '보탬'의 'phase 2/3 선택이 V1 실행 옵션과 **strict 집합**을 바꾼다'는 strict 집합에 대해 틀린 말이다(§4: 둘 다 빈 집합). `b34_briefs.md` §0.2 표가 맞다.
* 제안 본문(사실만): "B34·b26pre·backfill·B26-1 네 card는 Phase 2 DoD 뒤에 병합되는데, 머리는 `phase: 2`이고 A2 기록 ③은 'Phase 2 진행 중'이라 적었습니다. 게이트는 card phase를 현재 Phase와 대조하지 않고, phase 2·3에서 test 결과·엄격 집합(둘 다 빈 집합)·N/A 허용이 같습니다. 달라지는 것은 판정 기록 V1의 `--gmid-phase=` 값과 어느 Phase 기록으로 셀지(DoD 집계), A2 문구뿐입니다. 선택지: (Recommended) 네 card `phase: 3` + 'Phase 3 M card 전' 유지 + ③ 정정 decision 기록(design 30 승인·U-03을 기다리지 않는다고 명시) / 네 card를 Phase 2 DoD 앞으로 당겨 `phase: 2` 유지."

**F3 (정확성, 경미) -- 수치 문구 세 곳.**
* (a) Q1 배경 '대상은 301개이고, 지금 test로는 그중 50개가 살아남습니다' → '대응이 있는 264개 중 50개(새 문장 37개는 B26-1 계약 몫, 병합본에서 auditor가 잼)'. 같은 이유로 1번 '결과: 남는 생존 0'에 '대응 있는 변이 기준'을 붙인다.
* (b) B26-1 v5 'V3 계획' 1 'C1·C2 뒤에도 299(정리 없음과 같은 수)' → '299(수는 같지만 대상 4개가 바뀜: 정리로 4개가 빠지고 지운 가드 바로 뒤 문장 1·`open_net`을 읽는 문장 3이 들어온다. 새 4개는 계약 7(e) E1·b26pre가 죽임 -- 측정 B)'.
* (c) 계약 15 '판정'에 같은 새 대상 4개가 죽어야 한다는 문장을 한 줄 더한다(auditor가 '대상 소멸'만 보고 새 대상을 놓치지 않게).

## 질문 구성 평가

* Q1: 사용자 몫이 맞다(면제 = 판정 범위 축소 약화, DEC-40). 선택지 4개가 서로 배타적이다. 권고(1번)는 원칙(약화 최소, test를 실제 동작에 배선)과 측정에 맞다. Q1-BF는 이미 답했으므로 묻지 않는 것이 맞다.
* Q2: 사용자 몫이 맞다(A2 범위 밖의 관찰 가능한 반환 변경). `git grep unavailable_reason`(0f23786) 소비처가 0곳임을 확인했다(엔진 자기 정의뿐).
* Q3: 사용자 몫이 맞다(기대값 변경, 작성자≠검증자). `test_dup_kcl_edges.py` 281~298행 단언 문구가 질문과 같다.
* 참고(묻지 않음): C1은 두 번 부르는 `find_differential_pair_candidates`의 중복 계산을 그대로 둔다. 캐시 원칙상 백로그 후보지만 범위 밖이다.

## 재현

`C:/g133`(삭제됨): `setup133.py`(archive a796468 → base·b1, 작성자 스크립트를 경로만 바꿔 복사) → `mk_b1.py` → `mrun.py 8`(§1 표·C12) → `mrun2.py`(C3 7) → `cls3.py`(A·B·C12 id 비교) → `c12eq.py`(library 9/9·E4) → `exp_backfill3.py`.
merge_gate 확인은 `git show 0f23786:tools/gates/merge_gate.py`·`role_paths.py`·계획서·conftest.
