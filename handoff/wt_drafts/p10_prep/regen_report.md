# P10 준비 -- DF-23 목록 재측정 보고 (gate master `cd64170`, 2026-09-30)

> **2026-09-30 reconcile 뒤 재생성**: 5절 ①~⑤를 초안 두 card에 반영했다(`../p10_reconcile_log.md`). 목록 값의 변화는 5-② 한 가지 -- 메시지뿐 73항목의 `plan_mapping`을 이월 값 그대로 둔다(`related_plan_mapping`은 동작 항목 63개에만). 점검기에 7(d)(`function` 재계산)와 계약 1 `function` 형식(전 항목), 계약 3 '수정 Phase' 헤더 이름 대조를 더했다. 새 sha256은 `../p10_reconcile_log.md`.

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
* `plan_mapping` 재분류(P10 규칙): `신규…` 동작 항목 139 중 레일 62 → `DF-19`, 기타 1 → `DF-23`; 메시지뿐의 DF 표기 73은 이월 값 그대로 둔다(5-② reconcile 안 B -- 계약 3은 동작 항목만 본다. 처음 후보는 `메시지뿐(관련 DF-…)`로 바꿨었다).

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

---

(아래는 regen_df23.py 자동 출력)

# DF-23 목록 재측정 보고 (regen_df23.py)

* 재측정 커밋 `measured_at` = `cd6417026696091fd0ce02603a11a3729af3147e`, 옛 목록 측정 커밋 = `1e2e243d192b93befacb52647455c02900c9734f` (`git rev-list --count`: 101커밋 차이).
* 항목 수: 옛 590 -> 새 515.

### role별

| 값 | 옛 | 새 | 차 |
|---|---:|---:|---:|
| 메시지뿐 | 324 | 302 | -22 |
| 동작을 정함 | 266 | 213 | -53 |

### plan_mapping별(새 목록의 P10 재분류 전 값 = related_plan_mapping 우선)

| 값 | 옛 | 새 | 차 |
|---|---:|---:|---:|
| 신규(계획 DF-29~34 목록 밖) | 370 | 368 | -2 |
| DF-31(회로별 보상 함수) | 57 | 57 | +0 |
| DF-30(회로별 metric 함수) | 40 | 37 | -3 |
| DF-29 | 62 | 0 | -62 |
| DF-34 | 20 | 20 | +0 |
| DF-33 | 12 | 12 | +0 |
| DF-30(신규 위치) | 7 | 7 | +0 |
| DF-31 | 7 | 7 | +0 |
| DF-29(신규 위치) | 10 | 2 | -8 |
| DF-30 | 4 | 4 | +0 |
| DF-32 | 1 | 1 | +0 |

### plan_mapping별(새 목록 최종값)

| 값 | 옛 | 새 | 차 |
|---|---:|---:|---:|
| 신규(계획 DF-29~34 목록 밖) | 370 | 305 | -65 |
| DF-31(회로별 보상 함수) | 57 | 57 | +0 |
| DF-30(회로별 metric 함수) | 40 | 37 | -3 |
| DF-19 | 0 | 62 | +62 |
| DF-29 | 62 | 0 | -62 |
| DF-34 | 20 | 20 | +0 |
| DF-33 | 12 | 12 | +0 |
| DF-30(신규 위치) | 7 | 7 | +0 |
| DF-31 | 7 | 7 | +0 |
| DF-29(신규 위치) | 10 | 2 | -8 |
| DF-30 | 4 | 4 | +0 |
| DF-32 | 1 | 1 | +0 |
| DF-23 | 0 | 1 | +1 |

### 동작 항목 plan_mapping별(재분류 전 값)

| 값 | 옛 | 새 | 차 |
|---|---:|---:|---:|
| None | 324 | 302 | -22 |
| 신규(계획 DF-29~34 목록 밖) | 148 | 139 | -9 |
| DF-29 | 40 | 0 | -40 |
| DF-34 | 18 | 18 | +0 |
| DF-30(회로별 metric 함수) | 17 | 16 | -1 |
| DF-33 | 12 | 12 | +0 |
| DF-31(회로별 보상 함수) | 11 | 10 | -1 |
| DF-30(신규 위치) | 7 | 7 | +0 |
| DF-31 | 6 | 6 | +0 |
| DF-30 | 4 | 4 | +0 |
| DF-29(신규 위치) | 2 | 0 | -2 |
| DF-32 | 1 | 1 | +0 |

### kind별

| 값 | 옛 | 새 | 차 |
|---|---:|---:|---:|
| circuit(파생 이름) | 414 | 356 | -58 |
| net | 117 | 101 | -16 |
| device | 30 | 32 | +2 |
| path | 11 | 10 | -1 |
| 어휘 충돌: 역할 라벨(넷 이름 아님) | 7 | 7 | +0 |
| 어휘 충돌: spec 키(소자 이름과 동일 문자열) | 5 | 5 | +0 |
| circuit | 4 | 4 | +0 |
| element(passive/source) | 2 | 0 | -2 |

### phase별(새 목록만 -- 옛 목록엔 phase 없음)

| phase | 전체 | 동작을 정함 |
|---|---:|---:|
| 3 | 61 | 61 |
| 4 | 63 | 63 |
| 6b | 1 | 1 |
| 7a | 27 | 27 |
| 7b | 46 | 46 |
| 해당 없음 | 317 | 15 |

### 항목 대응(키 = 파일·리터럴·줄 내용, 같은 키는 줄 순서로 짝)

| 구분 | 전체 | 동작을 정함 |
|---|---:|---:|
| 줄까지 같음 | 74 | 12 |
| 옮겨감(내용 같고 줄 다름) | 435 | 201 |
| 사라짐(옛에만) | 81 | 42 |
| 나타남(새에만) | 6 | 0 |

옮겨간 항목의 역할 변화(옛->새): {('동작을 정함', '동작을 정함'): 200, ('메시지뿐', '메시지뿐'): 223, ('동작을 정함', '메시지뿐'): 11, ('메시지뿐', '동작을 정함'): 1}

#### 사라진 동작 항목(옛 목록 기준, 파일·옛 함수별 -- 함수 '' 는 옛 커밋 blob에서 다시 구한 이름)

* sizing_recipe.py `_telescopic_class_ab_open_loop_response`: 14
* sizing_recipe.py `<module>`: 9
* sizing_recipe.py `_telescopic_class_ab_open_loop_gains`: 6
* sizing_recipe.py `_psrr_telescopic_class_ab_cmfb`: 3
* sizing_recipe.py `_cmrr_telescopic_class_ab_cmfb`: 3
* sizing_recipe.py `_load_telescopic_topology_cached`: 3
* sizing_recipe.py `_telescopic_open_loop_device_names`: 1
* sizing_recipe.py `_psrr_telescopic_class_ab`: 1
* stick_diagram.py `suggest_headroom_stack_groups`: 1
* sizing_recipe.py `_cmrr_telescopic_class_ab`: 1

#### 사라진 메시지 항목(파일·옛 함수별 상위 15)

* sizing_recipe.py `_psrr_telescopic_class_ab_cmfb`: 7
* sizing_recipe.py `_cmrr_telescopic_class_ab`: 5
* sizing_recipe.py `_psrr_telescopic_class_ab`: 5
* sizing_recipe.py `SizingContext`: 4
* sizing_recipe.py `_cmrr_telescopic_class_ab_cmfb`: 4
* sizing_recipe.py `_telescopic_open_loop_device_names`: 2
* sizing_recipe.py `_telescopic_class_ab_open_loop_gains`: 2
* sizing_recipe.py `_load_telescopic_topology_cached`: 1
* stick_diagram.py `suggest_headroom_stack_groups`: 1
* sizing_recipe.py `_mna_solve_smallsignal`: 1
* sizing_recipe.py `_hashable_key`: 1
* sizing_recipe.py `<module>`: 1
* sizing_recipe.py `_nmcnr_predict`: 1
* sizing_recipe.py `_feed_gm_target_convention`: 1
* sizing_recipe.py `_cmfb_amp_gain_diode_load`: 1

#### 나타난 동작 항목(전부)

| 파일:줄 | 함수 | 리터럴 | role_reason | plan_mapping | phase | 분류 출처 | 줄 |
|---|---|---|---|---|---|---|---|

#### 나타난 메시지 항목(파일·함수별)

* sizing_recipe.py `SizingContext`: 2
* sizing_recipe.py `_mna_solve_smallsignal`: 1
* sizing_recipe.py `_feed_gm_target_convention`: 1
* sizing_recipe.py `_resolve_nulling_resistor_ohm`: 1
* sizing_recipe.py `_hashable_key`: 1

#### 규칙으로 분류된(이월·상속 아님) 동작 항목 -- 오케스트레이터 검토 대상

0개

#### 역할 재판정(이월 대응은 됐지만 새 규칙의 role이 옛 role과 다름)

13개
* sizing_recipe.py:835 역할 재판정 동작을 정함->메시지뿐 (docstring/설명 문자열) `miller_ota()가 이렇게 쓴다). fT를 지정하면 준정적 조건(fT<=margin*f_nqs)도 같이 검사한다.`
* sizing_recipe.py:2967 역할 재판정 동작을 정함->메시지뿐 (docstring/설명 문자열) `nmcnr_predict_ac_response()`(4-노드 KCL 정확해, sympy 유도 + ngspice/실트랜지스터 재조립`
* sizing_recipe.py:3023 역할 재판정 메시지뿐->동작을 정함 (식별자 참조(호출/디스패치 값)) `return _nmcnr_predict(spec, ctx)["dc_gain_db"]`
* sizing_recipe.py:3040 역할 재판정 동작을 정함->메시지뿐 (문자열 안(설명/오류 메시지)) `f"nmcnr_pm_deg: 0dB 교차가 {len(crossings)}개(notch=True)라 PM 하나로 대표할 수 "`
* sizing_recipe.py:4573 역할 재판정 동작을 정함->메시지뿐 (docstring/설명 문자열) `current_reuse_telescopic_topology()`가 이미 그렇게 사이징한다 -- 실측 gm(M1a)=gm(M4a)).`
* sizing_recipe.py:4737 역할 재판정 동작을 정함->메시지뿐 (문자열 안(설명/오류 메시지)) `f"telescopic_class_ab MNA 특이행렬(노드 {unknown_nodes[int(dead[0])]} 고립 또는 소자 "`
* stick_diagram.py:4187 역할 재판정 동작을 정함->메시지뿐 (문자열 안(설명/오류 메시지)) `f"(two_stage_ota의 M4/M6 실례 -- 둘 다 authoritative 태그가 있었지만 M4는 "`
* stick_diagram.py:4198 역할 재판정 동작을 정함->메시지뿐 (문자열 안(설명/오류 메시지)) `f"(two_stage_ota의 M4/M6, `.ai/context.md` 세션38 §1-⑳(b) 참고).")`
* stick_diagram.py:4215 역할 재판정 동작을 정함->메시지뿐 (문자열 안(설명/오류 메시지)) `f"budget()`, two_stage_ota의 M4/M6이 실제 사례).")`
* stick_diagram.py:4529 역할 재판정 동작을 정함->메시지뿐 (문자열 안(설명/오류 메시지)) `f"`two_stage_ota` M3/M4·`current_reuse_telescopic_ota` M13/M22·`nmcnr_"`
* stick_diagram.py:5401 역할 재판정 동작을 정함->메시지뿐 (docstring/설명 문자열) `없이 각 쌍이 그 자체로 필요한 대응을 준다(실측 확인: current_reuse_telescopic_ota`
* topology_library.py:464 역할 재판정 동작을 정함->메시지뿐 (주석) `cgg2 = C_Ltot * 0.1  # 초기 추정(miller_ota_topology와 같은 관례)`
* run_harness.py:276 역할 재판정 동작을 정함->메시지뿐 (docstring/설명 문자열) `nmcnr_predict_ac_response()` 배선) -- `.ai/context.md` 세션37 참고."""`

## 보정(calibration): 옛 측정 커밋 `1e2e243d192b93befacb52647455c02900c9734f`에서 같은 스캐너 대 옛 목록

* 어휘: 옛 n_devices 102/n_nets 101/n_circuits 10 대 재수집 102/101/10; mos 집합 같음=False, passive 집합 같음=False, per_circuit 같음=True, circuits 같음=True
* exact 항목: 옛 176, 재스캔 176, 공통 176, 옛에만 0, 재스캔에만 0
* exact 항목 role_reason 일치 176/176
* exact 항목 function 일치 155/162
  * sizing_recipe.py:8822 옛 `_evaluate` 새 `_build_theta_evaluator`
  * sizing_recipe.py:8831 옛 `_evaluate` 새 `_build_theta_evaluator`
  * sizing_recipe.py:8866 옛 `_evaluate` 새 `_build_theta_evaluator`
  * sizing_recipe.py:9241 옛 `_evaluate` 새 `_build_theta_evaluator`
  * sizing_recipe.py:10746 옛 `_centering_dev` 새 `search_stage_budget_L_warm_start`
  * sizing_recipe.py:10748 옛 `_centering_dev` 새 `search_stage_budget_L_warm_start`
  * sizing_recipe.py:10749 옛 `_centering_dev` 새 `search_stage_budget_L_warm_start`
* stem 줄: 옛 414, 재스캔 414, 공통 414, 옛에만 0, 재스캔에만 0
* stem 공통 줄 role(옛, 재스캔) 분포: {('동작을 정함', '메시지뿐'): 14, ('메시지뿐', '메시지뿐'): 323, ('동작을 정함', '동작을 정함'): 76, ('메시지뿐', '동작을 정함'): 1}
  * sizing_recipe.py:893 옛 동작을 정함/식별자 참조(호출/디스패치 값) -> 재스캔 메시지뿐/docstring/설명 문자열 `miller_ota()가 이렇게 쓴다). fT를 지정하면 준정적 조건(fT<=margin*f_nqs)도 같이 검사한다.`
  * sizing_recipe.py:3146 옛 동작을 정함/식별자 참조(호출/디스패치 값) -> 재스캔 메시지뿐/docstring/설명 문자열 `nmcnr_predict_ac_response()`(4-노드 KCL 정확해, sympy 유도 + ngspice/실트랜지스터 재조립`
  * sizing_recipe.py:3202 옛 메시지뿐/문자열 안(설명/오류 메시지) -> 재스캔 동작을 정함/식별자 참조(호출/디스패치 값) `return _nmcnr_predict(spec, ctx)["dc_gain_db"]`
  * sizing_recipe.py:3219 옛 동작을 정함/코드 줄(수동 확인 필요) -> 재스캔 메시지뿐/문자열 안(설명/오류 메시지) `f"nmcnr_pm_deg: 0dB 교차가 {len(crossings)}개(notch=True)라 PM 하나로 대표할 수 "`
  * sizing_recipe.py:4752 옛 동작을 정함/식별자 참조(호출/디스패치 값) -> 재스캔 메시지뿐/docstring/설명 문자열 `current_reuse_telescopic_topology()`가 이미 그렇게 사이징한다 -- 실측 gm(M1a)=gm(M4a)).`
  * sizing_recipe.py:5049 옛 동작을 정함/코드 줄(수동 확인 필요) -> 재스캔 메시지뿐/문자열 안(설명/오류 메시지) `f"telescopic_class_ab MNA 특이행렬(노드 {unknown_nodes[int(dead[0])]} 고립 또는 소자 "`
  * sizing_recipe.py:5249 옛 동작을 정함/코드 줄(수동 확인 필요) -> 재스캔 메시지뿐/문자열 안(설명/오류 메시지) `f"cmfb_stage2_devices를 다시 볼 것(_cmrr_telescopic_class_ab_cmfb docstring 참고)")`
  * sizing_recipe.py:5359 옛 동작을 정함/코드 줄(수동 확인 필요) -> 재스캔 메시지뿐/문자열 안(설명/오류 메시지) `f"_cmrr_telescopic_class_ab_cmfb()와 동일한 가드, docstring 참고")`
  * stick_diagram.py:4371 옛 동작을 정함/코드 줄(수동 확인 필요) -> 재스캔 메시지뿐/문자열 안(설명/오류 메시지) `f"(two_stage_ota의 M4/M6 실례 -- 둘 다 authoritative 태그가 있었지만 M4는 "`
  * stick_diagram.py:4382 옛 동작을 정함/코드 줄(수동 확인 필요) -> 재스캔 메시지뿐/문자열 안(설명/오류 메시지) `f"(two_stage_ota의 M4/M6, `.ai/context.md` 세션38 §1-⑳(b) 참고).")`
  * stick_diagram.py:4399 옛 동작을 정함/코드 줄(수동 확인 필요) -> 재스캔 메시지뿐/문자열 안(설명/오류 메시지) `f"budget()`, two_stage_ota의 M4/M6이 실제 사례).")`
  * stick_diagram.py:4713 옛 동작을 정함/코드 줄(수동 확인 필요) -> 재스캔 메시지뿐/문자열 안(설명/오류 메시지) `f"`two_stage_ota` M3/M4·`current_reuse_telescopic_ota` M13/M22·`nmcnr_"`
  * stick_diagram.py:5585 옛 동작을 정함/식별자 참조(호출/디스패치 값) -> 재스캔 메시지뿐/docstring/설명 문자열 `없이 각 쌍이 그 자체로 필요한 대응을 준다(실측 확인: current_reuse_telescopic_ota`
  * topology_library.py:464 옛 동작을 정함/코드 줄(수동 확인 필요) -> 재스캔 메시지뿐/주석 `cgg2 = C_Ltot * 0.1  # 초기 추정(miller_ota_topology와 같은 관례)`
  * run_harness.py:275 옛 동작을 정함/식별자 참조(호출/디스패치 값) -> 재스캔 메시지뿐/docstring/설명 문자열 `nmcnr_predict_ac_response()` 배선) -- `.ai/context.md` 세션37 참고."""`
