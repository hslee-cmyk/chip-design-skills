# 7차 독립 검토 -- Phase 4 `40-defect-fixes` 초안 v0.9.1 → v0.9.2 델타

검토자: 독립 검토 agent(작성자 아님). 저장소 읽기 전용(`git show HEAD:` 읽기 1회뿐, 상태 변경 git 없음). 스크래치 `C:/g152`(끝나고 삭제).
**루프 종료 규칙**: v0.9.2 변경이 만든 결함만 적는다. v0.9.1 이전 문장의 결함과 v0.9.2 뒤에 다른 문서가 바뀌어 생긴 어긋남은 '참고'로만 둔다.

대상(diff로 확인): `draft_phase4_design.v091.md` → `draft_phase4_design.md`(21:46), `phase4_approval_question.v091.md` → `phase4_approval_question.md`(21:48),
`decision_package.v2.md` → `decision_package.md`(21:48), `phase4_revision_log.md` 'v0.9.1 → v0.9.2' 절, `p4_scripts/p4v091_dag.py` + out.

## 판정

**막는 것(blocking) 없음. 고칠 것(should-fix) 2건은 모두 새 원칙 P-37(E-LIB 비교)에 있다. minor 4건.**
사용자 결정 반영(점검 1), 백로그 번호 바꾸기(점검 3), DAG(점검 4), #30 E2 문구(점검 5)는 정확하다.
P-37은 선례 `20260930-phase2-e4-baseline`의 모양(직전 Phase DoD 대상 커밋과 비교, 의도된 필드만 따로 판정)을 바르게 따랐다.
다만 Phase 3 7차 검토 S1이 찾은 'nets만 보는 구멍'을 막는 문장이 없다. 빼는 키 목록도 승인 diff 밖(DoD 브리핑)에 맡겼다.

---

## 1. 점검 결과

| # | 점검 | 결과 |
|---|---|---|
| 1 | 결정 반영 = `user_decisions.md` | **일치.** 아래 1.1 |
| 2 | P-37·#17 (c) 대 Phase 3 v8.2 E5·선례 | 모양은 일치. **S1·S2** |
| 3 | B48~B50 → B51~B53 | **완료.** 아래 1.2 |
| 4 | `p4v091_dag.py` 재실행 | 스크래치 사본(출력 `C:/g152/out`): exit 0, `SUMMARY scenarios=24 unexpected=0`. 머리 주석 줄을 빼면 `_drafts/p4_scripts/out/p4v091_dag.out.txt`와 같다. 새 간선이 코드에 있다: `BF` 기본 노드(B26pre → BF → #1), `PH3rec` → 네 card, `E2rec` → P2DoD, `U3` → #1. 새 assert 3개(163·164·176~178행)도 통과한다. C8(대안 + 확정 순서)은 순환이고, 이는 기대대로다 |
| 5 | #30 E2 문구 대 `patch_e2_wording.py` NEW | **일치.** NEW 문구 안의 "현재 승인 `20260929-p4-scan-exempt` 1건"이 #30이 고칠 대상이다. #30은 이 문구를 '현재 승인 … 1건'이라고 정확히 인용한다. 근거 '재검토' 절은 `approval_20261001-p2dod-e2-wording.md`의 원문과 같다(면제 0이면 '면제되지 않은 발견 0' = '발견 0'). 요약형 'exit 0, 면제되지 않은 발견 0(현재 면제 … 1건)'도 NEW와 뜻이 같다. 참고 m3 |

### 1.1 결정 대조 (점검 1 -- 지어낸 결정 없음)

| 결정 | `user_decisions.md` / 승인 초안 | v0.9.2 반영 |
|---|---|---|
| Q-B34-PHASE | "phase 3 + 정정 기록 (Recommended)". 네 card `phase: 3`, M card 전 순서 유지, A2 ③ 정정 decision 1건, design 30 승인·U-03을 기다리지 않음(`approval_20261001-b26-phase3-cards.md` scope) | 같다(머리 14행, §3.2, §7.3, §9-19). 네 card = #45·B26pre·backfill·#1로 같다 |
| U-BF | "결함으로 고침 (Recommended)", 결함 card는 b26pre 뒤·B26-1 앞, 기록 id `20261001-b26-backfill-interdig-fix` | 같다. 조건 없는 기본 노드 |
| U3 | "정리 2줄 + 면제 1". C1·C2, `range` const− 1개 면제, "code 커밋 K 뒤 auditor 측정 해시로 병합 전 커밋" | 같다. id `20261001-b26-v3-equiv-range`는 B26-1 card의 id 후보다(지어낸 id 아님). '착수 조건 아님'은 v0.9.2 작성 시점 card(`draft_b26_1.spec.pre-r1.md` 452행)와 같다. 그 뒤 바뀐 내용은 참고 R1 |
| U4 | "추가 승인 1건", `20260930-b26-b40-reason-key`(키 삭제만) | 같다. '분기와 나머지 세 키는 그대로'는 승인 초안 scope 원문이다 |
| U5 | "갱신 승인", 새 기대 = 두 매개변수 + 키워드 전용·기본값 없음 `RailDeclaration rails` | 같다 |
| Q-P2DOD-E2 | "문구 정정", DoD 측정 판 H가 정정 커밋을 포함 | 같다. Phase 4 몫은 기록 '재검토' 절뿐이다(새 결정 아님 -- 재검토 절이 미리 적은 일) |
| U2-a 소멸 | `b26_survivor_final_question.md` 13행(N2(b) + 넓힌 T6, N2d 안 씀)·51행(SR 11802는 N2w 대상 아님) | 근거와 같다 |
| v0.9.1 m-2 정정 | 승인 초안 질문 원문 "phase 2·3에서 test 결과·strict 집합(둘 다 빈 집합)·N/A 허용이 같습니다" | 같다 |

### 1.2 백로그 번호 (점검 3)

* 네 파일에서 `B(48|49|50)`(뒤에 숫자 없음)을 모두 찾았다. design 20·67·92·145·702·868행과 `decision_package.md` 114행만 나오고, 모두 '옛 번호 → 새 번호' 설명 문맥이다. 승인 질문에는 0건이다.
* B48~B50을 Phase 4 항목의 현재 번호로 쓰는 곳은 남아 있지 않다.
* 새 번호의 뜻은 `patch_backlog.py --with-p4`의 B51~B53 문안(87~94행)과 같다(B51 VS 보간, B52 sf_pushpull 그룹, B53 analog-grammar 동봉).
* `phase4_revision_log.md` 161·167행에는 B48~B50이 남아 있다. v0.5 개정 기록(이력) 문장이므로 고치지 않는 것이 맞다.

---

## 2. Should-fix

### S1. P-37·#17 (c)·E11이 빼낸 `meta["rails"]`를 값 전체 정확히 같음으로 판정하라고 적지 않는다 -- Phase 3 S1 구멍을 그대로 물려받는다 (v0.9.2 결함)

* Phase 3 7차 검토 `review7_phase3_v82.md` S1이 재현한 내용이 있다. Phase 3 E5 판정식은 `hv.get("nets") == want`만 본다. 그래서 `RailDeclaration`에 계약 밖 필드(`polarity: str = 'junk'`)가 끼어도 `E5 E-LIB/E-INST PASS`가 난다. 고칠 방법은 `hv == {"__dc__": "RailDeclaration", "nets": want}`(값 전체 같음)이다. 그런데 Phase 3 v8.2(21:19 판)에는 이 수정이 아직 들어가지 않았다.
* v0.9.2는 이 구멍을 닫는 문장 없이 'Phase 3 v8.2 E5 `MASK_META = ("rails",)`와 같은 모양'이라고 적는다(#17 (c), P-37). 문장은 이렇다.
  * #17 (c): "`meta["rails"]`는 … 해시에서 빼고 계약값(nets = `supply_nets`, polarity = §10.3 구조 규칙 결과)으로 따로 판정"
  * E11 판정 칸: "E-LIB 9/9 로드 + 위 비교에서 **목록 밖** 차이 0". 빼낸 키 자체의 계약 판정은 통과 기준에 없다.
* Phase 4에서는 이 구멍이 더 넓다. 판정할 성분이 둘(`nets`·`polarity`)이고, base `P3D`에 이미 `rails`가 있다. 그런데 #17이 그 값을 바꾸므로 Phase 3에 있던 `bv == hv` 보호가 처음부터 없다.
* 계약값을 어디서 가져오는지도 적혀 있지 않다.
  * (i) `nets`의 기준 판: Phase 3 m1과 같은 문제다. HEAD library에서 읽으면 P3D와 HEAD 사이의 `supply_nets` 변경을 놓친다. #53~#55가 topology 데이터를 바꾼다.
  * (ii) `polarity` 기대값: 'polarity = 구조 규칙 결과'를 엔진이 계산한 값으로 채우면 작성자=검증자 순환이 된다.
* **고칠 것**: P-37·#17 (c)·E11에 다음을 적는다.
  * (a) 빼낸 키는 **값 전체 정확히 같음**으로 판정한다. 예: `masked.rails == {"__dc__": "RailDeclaration", "nets": …, "polarity": …}`. 계약 밖 필드는 0개다.
  * (b) `nets` 기대값 = P3D `masked.rails.nets`(또는 P3D library `supply_nets`). 이 값을 바꾸는 card(#53~#55)가 있으면 그 card 차이표를 따른다.
  * (c) `polarity` 기대값 = 9회로 고정 표(DoD 판정 자료, 엔진 호출 아님). 아니면 §10.3 규칙을 판정 쪽에서 따로 구현한 것.
  * (d) E11 통과 기준에 '빼낸 키 계약 판정 FAIL 0'을 더한다.
  * (e) `ports`·`device_roles`(#47)의 '기대 차이표'도 같은 정확 일치로 판정한다.

### S2. 빼는 키 목록(판정 기준)을 승인 diff 밖 'DoD 브리핑'에 맡겼고, P-37을 '기준에 닿는 것'이 아니라 일반 원칙 기본안에 넣었다 (v0.9.2 결함)

* E11: "빼는 키 목록은 card 계약에서 유도해 **DoD 브리핑에 박는다**". 현재 목록에는 `[미확인]`(#21)도 남아 있다.
* 선례 쪽(Phase 3 v8.2 D-28 (e)) 원문: "목록은 판정 기준이라 auditor가 늘리지 않는다. 사이 card의 계약이 바뀌면 이 목록과 상수를 고치는 design 개정(승인 대상 diff)이 필요하다". 같은 문서 UD-0 행: "판정 기준인 비교 판·빼는 필드 목록(D-28)은 사용자 몫". Phase 3은 이것을 승인 질문의 '기준에 닿는 기본값 (c)'로 드러냈다.
* v0.9.2 승인 질문은 P-37을 UD-0 '원칙 기본안 P-1~P-37'의 예시 끝에 한 구절로만 넣었다(24행). '기준에 닿는 것'(30행)에는 없다. 그러면 목록을 DoD 때 브리핑 작성자(오케스트레이터)가 정한다. 해시에서 빼는 키를 늘리는 것은 판정을 약하게 하는 쪽이다. 이것이 사용자 승인 없이 열려 있다.
* **고칠 것**:
  * (a) 빼는 키 목록과 각 키의 계약값 출처를 design §6 E11에 상수로 고정한다. 목록을 바꾸려면 design 개정(승인 diff)을 거친다고 적는다. #21 `[미확인]`은 '#21 card 작성 전 실측. 들어가면 design 개정'으로 적는다.
  * (b) 승인 질문 '기준에 닿는 것'에 한 줄을 더한다. 예: "(c) Phase 4 완료 판정의 라이브러리 회로 재측정 = Phase 3 완료 커밋과 비교, 해시에서 빼는 항목 `rails`·`ports`·`device_roles`는 각 card 약속값과 정확히 같아야 함"

---

## 3. Minor

| # | 내용 |
|---|---|
| m1 | **P-37 점검이 #1을 빠뜨렸다.** v0.9.2 머리 18행의 '이 문서 점검 결과'는 #17·#47·#53~#55·#21을 훑는다. 하지만 이 문서가 계약을 정하는 49건에 든 **#1**(B26-1, `meta["rails"]`를 처음 더하는 card)은 빠졌다. #1 oracle (c)는 여전히 'E-LIB 9/9·E-INST'뿐이다. Phase 3 검토 F3v82 실측으로는 원래 `e_lib.py` 해시가 9회로 모두 다르다. #1 card 계약 8('`rails` 제외')이 실제 판정을 덮으므로 위험은 없다. 다만 #1 (c)에 '`meta["rails"]` 제외, 계약값 판정(card 계약 8)'을 한 구절 더해야 #17 (c)와 모양이 같아진다 |
| m2 | 승인 질문 24행 "라이브러리 회로 재측정은 **Phase 2·3** 완료 판정과 같은 방식"에서, Phase 3 쪽은 아직 사용자 답 전이다(Phase 3 UD-0 (c), 대안 c-2 = B0 비교). P-37의 근거는 승인된 선례 `20260930-phase2-e4-baseline` 하나로 충분하다. 그러니 'Phase 2 완료 판정(승인된 선례)과 같은 방식'으로 좁히는 편이 사실과 맞다. Phase 3 답이 c-2로 와도 P-37은 그대로라고 한 줄 적는다 |
| m3 | #30 '문서 몫'에서 design 20을 누가 커밋하는지가 없다. code-author는 설계 문서를 쓰지 않는다(역할 정의). "같은 card에서 고친다"에 '오케스트레이터 문서 커밋, 그 card 병합과 같은 묶음'을 더한다. #30 oracle 번호가 (a) 다음 바로 (d)인 것도 정리한다. 면제 줄이 사라진 뒤 승인 기록 `20260929-p4-scan-exempt`가 가리키는 `path::rule`이 남아도 스캐너·gate가 문제 삼지 않는지는 #30 card 작성 때 확인할 일로 적는다 |
| m4 | E2 base는 'Phase 3 DoD 병합본'이고 E11 base는 'Phase 3 DoD 대상 커밋 `P3D`'로, 같은 판을 두 이름으로 부른다. `P3D` 정의('Phase 3 DoD 측정 기록의 대상 커밋')를 한 번 적고 E2도 같은 기호로 쓴다 |

## 4. 참고 (v0.9.2 결함 아님 -- 오케스트레이터 재대조용)

* **R1**: `draft_b26_1.spec.md`가 v0.9.2 뒤(22:20)에 '두 번 시도 절차'로 바뀌었다. 면제 기록 `20261001-b26-v3-equiv-range`는 이제 "1차 시도 code 커밋 K1 뒤·**2차 시도 착수 전**, 착수 조건 8"이다(419·437행). Phase 4 v0.9.2의 "K 뒤·병합 전 -- 착수 조건 아님"(머리 16행, §3.2 #1 행, §3.3 도식, §5.1 #1, §7.3)은 당시 card(`pre-r1` 452행)와는 맞았다. 하지만 지금 card와는 다르다. 다음 판에서 card를 인용하는 방식으로 고친다.
* **R2**: Phase 3 v8.2 S1(판정식 한 줄)이 Phase 3 쪽에서 고쳐지면, P-37의 'Phase 3 E5와 같은 모양'은 고친 판을 가리켜야 한다.

## 5. 재현

* `diff` 세 쌍, `phase4_revision_log.md` 397~425행, `user_decisions.md` 전문, 승인 초안 4개(b26-phase3-cards·p2dod-e2-wording·b26-b40-reason-key·backfill), `patch_e2_wording.py`, `patch_backlog.py` 87~94행을 확인했다.
* `draft_phase3_design_v8.md`(v8.2) 4·705·957~1018·1047행과 `review7_phase3_v82.md`를 읽었다.
* `git show HEAD:.ai/approvals/20260930-phase2-e4-baseline.md`를 읽었다.
* `C:/Python314/python.exe -B C:/g152/p4v091_dag.py`(사본) → `SUMMARY scenarios=24 unexpected=0`.
* `git -C <repo> status --short`는 검토 전후 같다(36줄).
