# P10 준비 -- DF-23 목록 재측정 보고 (gate master `cd64170`, 2026-09-30)

읽기 전용 측정. 저장소·작업 트리 쓰기 없음(소스는 `git show <commit>:<path>` blob만). 산출물:

| 파일 | 내용 |
|---|---|
| `p10_prep/regen_df23.py` | 재측정 생성기. `--repo <저장소> --commit <커밋> --out <json> [--report <md>] [--preamble <md>] [--prev-measured-at 1e2e243] [--calibrate]` |
| `p10_prep/df23_inventory.candidate.json` | `cd64170`에서 잰 후보 목록 (515항목) |
| `p10_prep/check_contracts.py` | 계약 점검기(생성기와 코드 공유 없음). `<json> [--repo R --base C] [--docs] [--selftest]` |
| `p10_prep/b22_lines.md` | 문서 백로그 B22 (b) 대상 19줄과 바꿀 문안 |

재현 명령(이 보고서를 만든 그대로):

```
python -B regen_df23.py --repo <R> --commit cd64170 --prev-measured-at 1e2e243 \
    --out df23_inventory.candidate.json --report regen_report.md --preamble regen_report.preamble.md --calibrate
python -B check_contracts.py df23_inventory.candidate.json --repo <R> --base cd64170 --docs
```

두 번 실행한 JSON의 sha256이 같다(결정론, 아래 '검증').

## 1. 결과 요약

* `measured_at` = `cd6417026696091fd0ce02603a11a3729af3147e`. 항목 **515**(메시지뿐 302 · 동작을 정함 213). 옛 목록 590(324·266).
* 동작 항목 phase: `4` 63(DF-19 62 + DF-23 1) · `3` 61(픽스처) · `7b` 46(DF-31 16, DF-33 12, DF-34 18) · `7a` 27(DF-30) · `6b` 1(DF-32) · `해당 없음` 15(어휘 충돌 9, 회로 이름 없는 파일 이름 규약 6).
* 동작 항목 (function, 파일) 묶음 52개, `function` 빈 값 0(옛 목록 동작 90개가 `''`).
* **DF-29 동작 항목 0**: 옛 DF-29 42항목(telescopic class_ab 개루프·CMRR/PSRR 함수, `_TELESCOPIC_FIXED_BASE`, `_load_telescopic_topology_cached`)이 P5b 삭제로 전부 사라졌다. 남은 DF-29 관련은 메시지 2줄(`메시지뿐(관련 DF-29(신규 위치))`). 계획 N6.2 Phase 2 DoD 문장 "DF-29~DF-34의 위치가 목록에 들어 있고"를 판정할 때 DF-29는 "Phase 2에서 삭제되어 위치 0"으로 읽어야 한다(오케스트레이터 판단 사항, 아래 5-④).
* `check_contracts.py` 결과(`--base cd64170 --docs`): 계약 1·2·3·4·7a·7b·7c PASS, 계약 5 FAIL 19줄(20건 -- `known-incidents.md:104`에 삭제 이름 두 개) = `b22_lines.md` 대상 그대로. 옛 목록에 돌리면 계약 1(measured_at 없음, 빈 function 90)·2·3·4 FAIL(거부 확인).

## 2. 방법 -- 옛 목록과 비교 가능하게 유지한 것

옛 목록의 `method` 문자열을 그대로 싣고, 모호했던 매개변수는 `method_params`에 적었다.

* **어휘**: `library/*.topology.json`의 netlist 소자·단자 넷, `passive_elements`·`ideal_sources` 이름·단자, `supply_nets`, 회로 이름(파일 이름). 길이 2 미만 넷 이름(A/B/X/Y)은 전체 어휘에서 제외(회로별 수는 포함 -- 옛 목록과 같은 셈법). 종류는 netlist `kind`가 정한다(nmos/pmos = device).
* **정확 일치**: scope 파일의 문자열 상수(AST `Constant`, f-string 조각 포함)가 어휘와 같으면 한 항목. 경로는 `\.(topology|instance)\.(json|md)$` 또는 `<회로>.topology.json`. role_reason은 AST 부모(dict key/Dict/딕셔너리 조회 키/get() 키/호출 인자/키워드 인자/비교/멤버십/IfExp/상수 대입/컨테이너 원소/경로 조립) -- 옛 목록 라벨 그대로.
* **줄기 보충**: 줄기 집합 = 옛 목록 `stems` 합집합 9개(`class_ab`, `common_gate`, `current_reuse`, `folded_cascode`, `miller`, `ngcc`, `nmcnr`, `telescopic`, `two_stage`), 대소문자 무시, 한 줄 한 항목, 정확 일치 항목이 있는 줄은 건너뜀. `pushpull`/`sf_` 줄기는 scope에 0회라 빠져도 누락 없음(grep 확인).
* **수동 분류 이월**: `plan_mapping`·`new_subcategory`·`context`·'어휘 충돌' kind는 옛 목록에서 (파일, 리터럴, 줄 내용) 일치로 이월 → 없으면 같은 함수 상속 → 없으면 규칙. `cd64170`에서 **규칙으로만 분류된 동작 항목 0**(전부 이월).

**보정(calibration)**: 같은 스캐너를 옛 측정 커밋 `1e2e243`에서 돌려 옛 목록과 대조(자동 출력 끝 절). 어휘 수 102/101/10 일치, per_circuit·circuits 일치, 정확 일치 항목 176/176 동일(누락·추가 0), role_reason 176/176 동일, 줄기 줄 414/414 동일. 차이는 세 가지뿐이고 모두 의도한 정정이다:
0. 어휘 종류: 옛 목록은 `MP`/`MN`(folded_cascode netlist의 pmos/nmos 다이오드 레퍼런스)을 passive로 적었다(`mos 집합 같음=False`). 재측정은 netlist `kind`대로 device로 적는다 → 픽스처 2항목 kind `element(passive/source)` → `device`(자동 출력 kind 표의 −2/+2).
1. `function` 7건: 옛 목록은 **안쪽** 중첩 def(`_evaluate`, `_centering_dev`)를 적었고 새 규칙은 계약 1 문장대로 **최상위** def(`_build_theta_evaluator`, `search_stage_budget_L_warm_start`)를 적는다.
2. 줄기 줄 role 15건: 옛 규칙이 docstring 산문(`miller_ota()가 …`)·f-string 오류 메시지·주석을 '동작을 정함'으로 잡은 14건을 메시지뿐으로, 실제 코드 `return _nmcnr_predict(spec, ctx)["dc_gain_db"]` 1건을 동작으로 바로잡았다. 이 중 `cd64170`에 남은 13건이 자동 출력 '역할 재판정' 목록이다.

## 3. 담당 Phase 규칙 (계획 표에서 파싱 -- 항목별 손 입력 없음)

* 닫힌 집합: 계획 N6.1 순서표 Phase 열에서 `2` 뒤의 것 + `해당 없음` = {3, 4, 5, 6a, 6b, 6c, 7a, 7b, 7c, 해당 없음} -- 초안 계약 2와 같다.
* `plan_mapping`이 `DF-n`이면 N5.2 DF 표 그 행의 Phase 열(헤더 이름은 **`수정 Phase`** -- 초안 계약 3은 '담당 Phase' 열이라 적었다. 문구 정정 필요, 5-①)을 깊이 0 쉼표로 나눠 조각마다 앞의 Phase 토큰을 뽑고 `2`를 뺀다.
  * 토큰 하나 → 그것(DF-19 `4`, DF-23 `4`, DF-30 `7a`, DF-31 `7b`, DF-33 `7b`).
  * **여러 개 → 조각 괄호 안에 '교체'가 든 토큰 중 N6.1 순서로 가장 이른 것**(없으면 가장 이른 토큰). 근거: 항목의 Phase는 그 이름 종속을 **실제로 없애는** Phase다(design §1 "교체는 Phase 4·7a"). DF-32 `6b(… VDsat 바닥으로 교체), 6c(IC4 PASS로 확인)` → `6b`. DF-34 `4(PDK 상수 … 복사 제거), 7b(… 데이터 항목으로 교체하고 함수 삭제)` → `7b` -- 목록 항목은 회로 이름·파일 경로·`_spec_*` 함수 이름이고, Phase 4 몫은 PDK 상수 복사 제거라 이름 종속을 없애지 않는다. DF-29 `2, 7a` → `7a`(현재 동작 항목 없음).
* DF 밖 항목(초안 '결정 필요 항목' 기본안 그대로): 레일 넷 이름 리터럴(운영) → `plan_mapping` `DF-19`로 옮기고 `4`(DF-19 행 위치 열이 "레일 넷 이름을 동작 조건으로 쓰는 운영부 함수"를 적는다 -- DF-26은 같은 변경 단위의 DEC-60 구현 행이라 DF-19를 고름), 기타 넷·소자 이름 → `DF-23` `4`, 픽스처 넷리스트 → `3`+사유(MOD7), 어휘 충돌 → `해당 없음`+사유, 회로 이름이 없는 파일 이름 규약(`*.topology.json`, `.topology.json`, `.topology.md`, `.instance.json`) → `해당 없음`+사유. 옮긴 항목은 원래 값을 `related_plan_mapping`에 남긴다.
* 픽스처의 `vdd`/`gnd`(fixture 함수 안, context 픽스처)는 레일 규칙이 아니라 픽스처 규칙(`3`)을 따른다 -- 동작 조건이 아니라 테스트 넷리스트 데이터라서. 점검기의 레일 규칙도 `context == "운영"`만 본다.

## 4. 옛 목록 대비 변화 (자세한 표는 자동 출력)

* 동작 항목 266 → 213: 사라짐 42(P5b telescopic class_ab 삭제 41 -- 개루프·CMRR/PSRR 함수·`_TELESCOPIC_FIXED_BASE`·`_load_telescopic_topology_cached`·레지스트리 키, P5 `suggest_headroom_stack_groups` 1), 역할 재판정으로 메시지뿐이 된 11(+동작이 된 1), 나타남 0.
* 메시지 항목 324 → 302: 사라짐 39(삭제된 함수들의 docstring·주석), 나타남 6(줄 내용이 바뀐 메시지 줄), 역할 재판정 +11/−1.
* 줄 번호: 대응된 509항목 중 줄까지 같음 74, 내용 같고 줄만 옮겨감 435.
* `plan_mapping` 재분류(P10 규칙): `신규…` 동작 항목 139 중 레일 62 → `DF-19`, 기타 1 → `DF-23`; 메시지뿐의 DF 표기 73 → `메시지뿐(관련 DF-…)`(5-②).

## 5. 오케스트레이터 결정·정정 필요 항목

1. **초안 계약 3의 열 이름**: 계획 N5.2 DF 표 헤더는 `| ID | 결함 | 위치(함수) | 수정 Phase | 비고 |` -- '담당 Phase'가 아니라 **'수정 Phase'**. test가 헤더 이름으로 열을 찾으면 실패한다. 계약 문구를 "'수정 Phase' 열"로 고치거나 "헤더에 'Phase'가 든 열"로 적을 것.
2. **계약 2·3 충돌(메시지뿐 + DF 번호)**: 옛 목록에서 메시지뿐 102항목이 `plan_mapping`에 DF 번호를 가진다(DF-31 47 등). 계약 2는 메시지뿐 → `해당 없음`, 계약 3은 `DF-`로 시작하면 phase ∈ Phase 열 토큰이라 둘을 동시에 만족할 수 없다. 후보는 `plan_mapping`을 `메시지뿐(관련 DF-31(…))`로 바꾸고 원래 값을 `related_plan_mapping`에 두었다(`DF-`로 시작하지 않으니 phase_reason 필수 규칙으로 들어감). 다른 안은 계약 3을 "`role == 동작을 정함`이고 `plan_mapping`이 `DF-`로 시작하는 항목"으로 좁히는 것 -- 그 경우 생성기에서 이름 바꾸기를 빼면 된다(한 줄).
3. **계약 3 레일 규칙의 판정 방법**: "레일 넷 이름 리터럴을 동작 조건으로 쓰는 항목"을 test가 어떻게 가려낼지 계약에 적을 것. 점검기는 "리터럴 ∈ base library `supply_nets` 합집합, role 동작, context 운영" -- 이 정의로 62항목, 전부 DF-19. `ctx.spec["vdd"]`처럼 spec 전압 키로 쓰는 `vdd`도 옛 분류대로 레일에 들어 있다(옛 목록 분류 이월).
4. **DoD의 'DF-29 위치'**: 현재 DF-29 동작 항목 0(위 1절). E3 판정("목록이 있고 항목마다 담당 Phase")에는 영향 없음.
5. **`function`의 정의**: 초안 P10 계약 1 "최상위 def 이름, 모듈 수준이면 `<module>`"과 P10b "최상위 def·class 이름(메서드면 `Class.method`)"이 조금 다르다. 후보는 P10b 쪽(클래스 메서드면 `Class.method`, 클래스 본문이면 클래스 이름 -- 예: `SizingContext` 1건)을 따랐고 중첩 함수는 최상위 이름이다. 두 문장을 하나로 맞출 것.
6. 초안 '재현할 수치'의 비교 값("590항목 … 사라짐 42")은 그대로 맞다(이 생성기로 재확인: 동작 사라짐 42).

## 6. 검증 (이 보고서 작성자가 돌린 것 -- 판정 기록이 아니다)

* `check_contracts.py --selftest` PASS(합성 거부 입력 8종 + 통과 3종 + Phase 토큰 파서).
* 후보에 변이를 넣어 점검기가 잡는지: 줄 번호 +1 → 7a FAIL, 정확 일치 항목 1개 삭제 → 7b·4 FAIL, 동작→메시지 → 2·4·7c FAIL, 레일 항목 DF-23으로 → 3·4 FAIL, DF-30 항목 phase 4 → 3 FAIL, DF-34 항목 phase 4 → 3은 PASS(허용 토큰)·4 FAIL.
* 두 번 생성한 JSON sha256 동일: `2ce78cbebab5c5b861d2a706036e893afc3a9560373065ed24d325ea3c4aebcf`.
