# P10 / P10b 초안 정정 기록 (2026-09-30, HEAD = gate master `cd64170`)

입력: `draft_p10_b22.spec.md`(P10 `20260930-p10-df23-inventory`), `draft_p10b.spec.md`(P10b `20260930-df23-registry-record`), `p10_prep/`(regen_df23.py, df23_inventory.candidate.json,
regen_report.md, check_contracts.py, b22_lines.md). 저장소 읽기 전용(`git show`·`git grep`·`parse_spec_card` import만, `-B`), scratch `C:/g34`(끝나고 삭제).
편집 전 사본: `draft_p10_b22.spec.prev.md`, `draft_p10b.spec.prev.md`, `p10_prep/regen_df23.prev.py`, `p10_prep/check_contracts.prev.py`,
`p10_prep/df23_inventory.candidate.prev.json`, `p10_prep/regen_report.prev.md`, `p10_prep/regen_report.preamble.prev.md`.

## 1. 계약 3 열 이름 -- `수정 Phase`

* 실측: 계획 909행 DF 표 머리 `| ID | 결함 | 위치(함수) | 수정 Phase | 비고 |`. '담당 Phase'라는 열은 없다('담당 Phase'는 N4.1·TS7의 말이고 E3·N6.2 문장도 '담당 Phase'를 쓴다).
* P10: 계약 3을 "N5.2 DF 표 **`수정 Phase` 열**(test는 머리 줄에서 이 열 이름을 찾는다 -- 없으면 FAIL)"로 고쳤다. 의도·원칙·결정 필요 항목·실측 1의 '담당 Phase 열/담당 4' 문구도 같이.
  목록 필드 이름 `phase`와 E3의 '담당 Phase'(개념)는 그대로 두고, 의도 절에 "값은 `수정 Phase` 열에서 읽는다"를 적었다. 토큰 파싱 규칙(괄호 깊이 0 쉼표, 앞머리 N6.1 이름, `2` 제외)도 계약에 적었다.
* P10b: 10행·120행의 "담당 Phase 열/담당 열" → "`수정 Phase` 열". §8.2 표 머리 `담당 Phase`는 레지스트리 표 열 이름이라 그대로.
* 점검기: 머리에 `수정 Phase`가 없으면 오류(이전: 'Phase'가 든 첫 열을 추측).

## 2. 메시지뿐 + DF 번호(계약 2·3 충돌) -- 안 B 채택

* 선택: **계약 3을 `role == "동작을 정함"` 항목으로 좁히고, 메시지뿐 항목의 `plan_mapping`은 옛 목록 이월 값 그대로 둔다.** (준비 후보가 쓴 안 A -- `메시지뿐(관련 DF-…)` 재표기 + `related_plan_mapping` -- 는 버림.)
* 근거: (1) `role`(동작을 정하는가)과 `plan_mapping`(어느 DF 이야기인가)은 다른 사실이다. 안 A는 role 사실을 plan_mapping 문자열 접두어에 한 번 더 적어 두 필드가 따로 틀어질 수 있다(근거 하나만 둔다는 원칙).
  (2) 계약 2가 이미 "메시지뿐 → `해당 없음`"을 정하므로 계약 3의 "phase ∈ 수정 Phase 토큰"은 원래 동작 항목에 대한 문장이다 -- 범위를 적어 모순을 없애는 것이 문장 뜻 그대로다.
  (3) 이월한 수동 분류를 덜 고친다(생성기 변경 = 재표기 두 줄 삭제). (4) P10b §8.2는 동작 항목만 묶으므로 영향 없음(§8.1은 role·phase 축뿐).
* 반영: P10 계약 2 끝(메시지뿐 plan_mapping은 이월 값이어도 됨), 계약 3 제목·첫 문장, 거부/통과 입력(동작 DF-30+`4` 거부, 메시지뿐 `DF-31(…)`+`해당 없음` 통과). P10b '거부해야 할 입력'의 '발견하면 안 되는 것'에 한 구절.
  생성기 `regen_df23.py` 재표기 삭제·`PHASE_RULE` 문구, 점검기 계약 3 범위·합성 selftest(`check3_synthetic`).
* 결과: 메시지뿐 73항목이 `plan_mapping` DF-31 48·DF-30 21·DF-29 2·DF-34 2를 그대로 가진다. `related_plan_mapping`은 동작 63항목(레일→DF-19 62, 기타→DF-23 1)에만. 그 밖의 값(515·302/213·by_phase) 불변.

## 3. 레일 판정 정의 -- B26 용어와 대조

* 계약 3에 적은 정의: 동작 항목 ∧ `context == "운영"` ∧ `literal` ∈ R → `plan_mapping`이 `DF-19`/`DF-26`으로 시작. R = `A/library/*.topology.json` 각 파일 최상위 `supply_nets` 원소의 합집합
  (선언 없는 `_TEMPLATE` 제외, 대소문자 변환·접두어 없음). HEAD R = {agnd, gnd, vdd, vss}(파일별 실측: vdd/gnd 6개, vdd/vss 1개(nmcnr), vdd/vss/agnd 2개(pushpull 둘)).
* B26-1(`draft_b26_1.spec.md`) 계약 1 "레일 여부는 선언 `supply_nets`의 원소인가로만 정한다(대소문자 변환·접두어 규칙 없음)"와 같은 정의다. 다른 점 하나를 계약에 적었다: B26 사전 조사
  (`prep_b26_supply_nets.md` §1)는 N(넷 레일 판정)과 V(`spec["vdd"]` 스칼라 전압 키, MG1)를 나누는데 이 규칙은 리터럴 값으로 가르므로 둘 다 DF-19에 묶인다. DF-19 `수정 Phase` 열이
  `supply_nets`·`supplies_v`·MG1을 함께 적으므로 모순이 아니고 N/V 구분은 B26 card 몫. 대문자 `VDD`·`GND`·`VSS`(SR `_DEFAULT_RAIL_HI/LO`)는 library 어휘가 아니라 목록 항목이 아님을 적었다.
* 픽스처 문맥 `vdd`·`gnd` 12항목(`context` = `픽스처(…)`)은 규칙 밖(Phase 3) -- 후보 실측과 같다(운영 레일 62 = 전부 DF-19).

## 4. DF-29 위치 0 -- E3 문구는 바꿀 필요 없음

* design 20 E3(220행) 통과 기준 = "목록이 있고 항목마다 담당 Phase가 적혀 있다" -- DF-29~DF-34를 말하지 않는다. 그러므로 **E3 판정 기준 변경 없음, 사용자 승인 기록 불필요.**
* 'DF-29~DF-34의 위치가 목록에'는 계획 N6.2 `2`(1017행) DoD 문장(그리고 N6.1 999행 "DF-29~DF-34 포함")이다. DF-29 `위치(함수)` 열 이름은 P5b(`6612902`)에서 전부 삭제돼 cd64170 엔진에
  정의 0(`git grep`: SR 5015 docstring 언급 한 줄뿐). 남은 DF-29 관련 항목은 SR 4737·4743 예외 메시지 2개(메시지뿐). 문장을 "base 엔진에 있는 위치"로 읽으면 글자 그대로 충족된다 -- 판정 기준을
  약화하는 해석이 아니라 없는 대상을 요구하지 않는 것이다.
* P10 반영: 의도 절에 'DoD 문장의 읽기' 단락(판정 기준 변경 아님), 계약은 DF별 최소 항목 수를 요구하지 않음, '재현할 수치'에 auditor가 DF-29~DF-34별 동작 항목 수를 세고 DF-29 = 0이면
  P5b 판정 기록을 근거로 인용. P10 초안에는 원래 "DF-29~DF-34 위치"를 요구하는 계약 문장이 없었다(계약 3의 행 목록에 DF-29 `2, 7a`가 있을 뿐 -- 토큰 {7a}로 명시).
* 선택 사항(결정 아님): N6.2 1017행 문장을 "(Phase 2에서 삭제된 DF-29 위치 제외)"로 다듬고 싶다면 계획서 개정이다. N6.2는 EL3 판정 표 목록(N4.1·N4.2·N6.1 Phase 열·N3.12.2)에 들지 않지만
  DoD 문장이므로, 한다면 오케스트레이터 계획 개정 + 사용자 확인이 안전하다. 이 정정에서는 하지 않았다.

## 5. `function` 정의 통일

* 정의(P10 계약 1, P10b가 인용): 그 줄을 감싼 **모듈 최상위 정의 단위**(데코레이터 줄 포함) -- 최상위 `def` → 이름, 최상위 `class`의 직속 메서드 → `Class.method`, class 본문의 다른 줄 → `Class`,
  어디에도 없으면 `<module>`, 중첩 def·class·lambda는 감싼 단위로 올림. **모든** 항목 비지 않음(형식 `<module>` | 식별자 | 식별자.식별자).
* 근거: 레지스트리 §3 74~83행이 메서드를 `SemiEmpiricalGmIdLUT.<메서드>`로 적는다 -- '최상위 def만'으로는 메서드 줄이 `<module>`이나 class 이름으로 뭉개져 레지스트리 이름으로 grep할 수 없다.
  후보 생성기 `func_resolver`가 이미 이 규칙이다(후보 값: `SizingContext` 5·`InfeasibleSizingError` 1·`SemiEmpiricalGmIdLUT.__init__`·`.cgg_absolute` 각 1, 빈 값 0/515).
* 판정 분담: 형식·비지 않음 = 영구 test(계약 1), 값이 정의대로인가(줄 번호에 묶임) = auditor 계약 7 (d). 점검기에 독립 구현 `function_of`와 7(d)를 더했다(selftest에 중첩·데코레이터·클래스 본문 사례).
* P10b '결정 필요 항목' 첫 점을 "반영됨"으로 바꾸고 정의를 옮겨 적었다. §8.2 `함수` 칸 정의에 `Class`·`Class.method` 포함을 적었다. '재현할 수치'에 후보 값(동작 213, 묶음 52, 빈 값 0)을 비교용으로 더했다.

## 6. 작성 전 실측·쓰기 경로·작성자≠검증자

* P10 '작성 전 실측' 1에 계획 909행 머리·N6.1 989·N6.2 1017·E3 220·DF-29 이름 정의 0·library R·레지스트리 §3 근거를, 새 1b에 준비 스크립트 결과(515/302/213, phase 분포, 보정 176/176·414/414,
  결정론, 점검기 결과, 옛 목록 거부)를 적었다. 5에 목록 소비자 `git grep` 결과(design 194행 정정, `probe-df23-summary.md` §B 한 줄 표지, review 문서는 이력)를 적고, 결정 필요 항목에 §B 표지 줄을 더했다.
* 목록 쓰기: 오케스트레이터가 N3.12.3 순서 1에서 card base가 될 gate master 머리 C(문서 커밋 직전)에 `mk_df23_inventory.py`(= reconcile 판 `regen_df23.py`)를 돌려
  `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json`에 쓴다(`measured_at` = C = 문서 커밋의 부모). 경로 대조(계획 N3.12.2, HEAD 실측): 626행 오케스트레이터
  `docs/03-analysis/**`(레지스트리 제외) -- 목록·생성기·요약 문서, 624행 `docs/02-design/**`, 638·640행 SKILL.md·references, 618행 test-author `A/tests/**`, 621·622행 auditor, 603행 레지스트리 = code-author.
* 작성자≠검증자: `check_contracts.py`는 생성기와 같은 쪽(준비 = 오케스트레이터)이 썼으므로 **오케스트레이터 사전 점검 전용**(커밋하지 않음, test-author·auditor에게 건네지 않음, 출력은 증거 아님).
  영구 판정 = test-author가 interface card 계약 1~5 문장만으로 쓰는 test, 계약 7·8 = auditor 자신의 스크립트. P10 oracle 절과 점검기 docstring에 같은 문장을 적었다.
  (지시문의 "check_contracts.py = auditor 교차 점검 도구" 안은 채택하지 않았다 -- 목록 작성 쪽 코드로 목록을 판정하게 되어 §14 위반.)
* 그 밖: '분리한 것' 표 첫 행 처리 칸을 P10b 방식(도구 규칙 + auditor 실제 대조)으로, design §8 P10b 행 문안은 P10b 초안 문안을 쓰도록 연결.

## 7. 재실행 결과 (scratch `C:/g34`, 판정 기록 아님)

* 생성: `regen_df23.py --repo <R> --commit cd64170 --prev-measured-at 1e2e243 --out … --report … --preamble … --calibrate` exit 0. 두 번 생성 sha256 동일
  `4f73189196e2b810c511211b9e0221e1a83df40cef619d14eff2a30fdd170fef`(이전 후보 `2ce78cbe…` -- 차이는 2절 메시지뿐 plan_mapping뿐). `df23_inventory.candidate.json`·`regen_report.md` 갱신,
  preamble 머리에 reconcile 한 단락, 4절 plan_mapping 문장 정정.
* 점검: `check_contracts.py --selftest` PASS. 후보 `--repo <R> --base cd64170 --docs` → 계약 1·2·3·4·7a·7b·7c·7d PASS, 계약 5 FAIL 20건(19줄, 문서 커밋 전이라 기대대로 = `b22_lines.md`).
  cd64170의 옛 목록 JSON → 계약 1(416)·2(1284)·3(118)·4 FAIL, 7a~7d는 `measured_at` 없음으로 FAIL(거부 확인).
* 파일 sha256: `regen_df23.py` `b4a75e92551da35503e048ec1abc5f9195c282cd769fd4496ac932b34b284e27`, `check_contracts.py` `70811fb5d44fa11b6e3886d1079060fabbc87133d64cc870b8eb85e965781a23`.
* 머리 검증: `tools/gates/role_paths.py parse_spec_card(text, expect_id)` -- P10 `20260930-p10-df23-inventory` test-only/no, P10b `20260930-df23-registry-record` red-green/no, 둘 다 approval
  `20260923-20-dead-code-dup-design`, 11개 절 모두 파싱. 저장소 `git status`는 시작과 같다(-B, 쓰기 없음).

## 8. 사용자 결정

없음. E3 판정 기준은 바꾸지 않는다(4절). 남은 사용자 몫은 기존 그대로: library topology.json 주석 보류(2026-09-30 결정), B26-2 D1.
선택적으로 계획 N6.2 1017행 DF-29 문구 다듬기(4절 끝)는 원하면 계획 개정으로 할 수 있으나 필요하지 않다.
