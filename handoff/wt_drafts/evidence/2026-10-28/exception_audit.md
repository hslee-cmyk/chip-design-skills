# 예외 전수 감사 (2026-10-28)

이 감사는 독립 읽기 전용으로 했고, 질문에 답하기 위한 것이다. 사용자 질문 원문은 다음과 같다.

> "예외로 했던 것들의 대부분은 계획이 엔진에 반영되지 않아서 임시로 예외로 둔 것으로 기억하는데 전수로 내 말이 맞는지 확인해"

## 0. 대상과 기준 커밋

| 층 | 경로 | 커밋 |
|---|---|---|
| 계획(승인본) | chip-design-skills `docs/01-plan/features/*.plan.md` (gain-budget, oracle-portability, graph-consumption, headroom-chain, offset-strategy, offset-trim, analog-topology-json-library, verilog-*) | master `9d153f2f` |
| 계획(작성 중) | `wt/plan-v6383` diff `9d153f2f..HEAD` | 브리핑 때 `770288a1`, 읽은 시점 `ebbae815` (다른 agent가 편집 중이며, 이 감사는 쓰지 않음) |
| design | `wt/design-v115/docs/02-design/features/` (v1.15.1) | `17d11bdc` |
| 엔진 code | `wt/integ-it12/skills/analog-gmid-design/gmid_engine` (tests 제외, 비테스트 .py 약 420개) | `d759838a` |
| 결정 기록 | `wt/_drafts/user_decisions.md`, `*.history.md` | 근거 grep용 |

감사가 끝난 뒤 `git -C wt/integ-it12 status --porcelain` 출력이 빈 것(0줄)을 확인했다. 산출물은 이 파일 하나다.

## 1. 방법(재현)

1차 후보는 scratchpad의 스크립트 `scan.py`로 뽑았다. 패턴은 아래와 같다.

```
문서 정규식: 예외|생략|건너뜀|건너뛴|폴백|fallback|임시|미구현|당분간|as-built 유지|as-built|정의 불능|기록만|unmeasured|표지만|보류|우회|skip
code 정규식: ^\s*except\s*(Exception|BaseException)?\s*(as \w+)?\s*:|except\s*\(|NotImplemented|TODO|FIXME|XXX|임시|미구현|fallback|폴백|unmeasured|\bskip|as-built|당분간|보류|우회|pass\s*$|\.get\([^)]*,\s*[^)]+\)
python scan.py doc  <plan_dir>   plan_master.txt .plan.md     # 562줄
python scan.py doc  <v6383_dir>  plan_v6383.txt  .plan.md     # 576줄
python scan.py doc  <design_dir> design.txt      all          # 821줄
python scan.py code <gmid_engine> code.txt                    # 433줄 (tests/ 제외)
```

2차는 6개 구획으로 나눠 사람이 읽는 방식으로 분류했다. 구획마다 쓴 추가 grep(`continue`, `return None`, 넓은 except, `git log -S` 등)은 각 부록 끝에 적었다. 정규식에 걸리지 않는 표현도 문단을 읽어 잡았다. 예: '정지 대신 기록', '통과로 둔다', 'N/A', '면제'.

다음 경우는 예외로 세지 않고 수만 기록했다.
- fail-closed 정지·거부
- 이력 서술, 결정 레지스터 상태 칸의 '미구현'
- Python 예외 클래스 설명
- 무의미한 dict 기본값
- 거부를 모으는 `continue`, 다시 raise하는 `except`

같은 예외를 한 층 안에서 여러 번 언급하면 한 항목으로 묶었다. **층 사이 중복은 지우지 않았다.** 같은 예외가 계획·design·code에 각각 나오면 세 번 센다. 층별 상태를 따로 보이기 위해서다.

분류 기준은 다음과 같다.
- (A) 계획이나 결정은 있는데 엔진·design에 반영되지 않아 임시로 둔 예외
- (B) 원칙·물리에서 나온 정당한 예외
- (C) 근거가 없거나 as-built 동작을 정당화하는 예외
- (D) 기타: 사용자 승인 정책, gate 끔, 기본 비활성 기능, 절차

## 2. 분류별 수

| 층 | 구획 | 항목 | A | B | C | D |
|---|---|---|---|---|---|---|
| 계획 | gain-budget N0~N5 + v6383 diff (부록 1) | 41 | 13 | 11 | 7 | 10 |
| 계획 | gain-budget N6 + 다른 plan 전부 (부록 2) | 66 | 21 | 26 | 4 | 15 |
| **계획 소계** | | **107** | **34 (32%)** | **37 (35%)** | **11 (10%)** | **25 (23%)** |
| design | 40-engine (부록 3) | 34 | 13 | 5 | 2 | 14 |
| design | 41·42·00~30·oracle·offset·기타 (부록 4) | 55 | 17 | 17 | 3 | 18 |
| **design 소계** | | **89** | **30 (34%)** | **22 (25%)** | **5 (6%)** | **32 (36%)** |
| code | metrics·graph·search (부록 5) | 37 | 14 | 15 | 5 | 3 |
| code | lut·authoring·sizing·layout·core·convergence·pipeline·report·루트 (부록 6) | 30 | 8 | 9 | 4 | 9 |
| **code 소계** | | **67** | **22 (33%)** | **24 (36%)** | **9 (13%)** | **12 (18%)** |
| **합계(층 사이 중복 포함)** | | **263** | **86 (33%)** | **83 (32%)** | **25 (10%)** | **69 (26%)** |

참고 사항:
- 버린 hit는 약 1,700줄이다(구획별 수는 부록 참조).
- 부록 1의 P1-01·02는 계획에서는 해소됐지만 엔진 반영이 남아 있다. 이것을 A로 다시 세면 계획 층 A는 36이 된다.
- 부록 5에서 A 14건 가운데 E5-01·02·14는 새 LUT에서는 발동하지 않는다. 옛 LUT를 쓸 때만 남는 잔재다.

## 3. 판정: 사용자 말 '대부분 A'

**부분적으로만 참이다. 전체 예외를 기준으로 하면 거짓이고, '임시' 예외만 보면 참이다.**

1. **전체 예외 중 A는 약 1/3이다(263건 중 86건, 33%).** 층마다 32~34%로 비슷하고, 과반인 층이 하나도 없다. 나머지는 두 갈래다.
   - B(32%): 정의역 밖, 측정 구성상 무의미, 상한 인증, 격자 폴백 같은 원칙·물리 예외
   - D(26%): 사용자가 승인한 정책 예외(U-87 LUT memo, G-8 허용 목록, DEC-86 gate 끔, U-51, R7 등), 기본 비활성 기능, 진단용 '기록만'
2. **'임시로 둔 예외'만 놓고 보면 사용자 기억이 맞다.** 정당한 예외(B)와 승인된 정책(D)을 빼면 A 86 대 C 25로 A가 약 77%다. 또 A의 출처는 거의 모두 as-built CONTRACT·ROADMAP이다. 엔진 작성자가 계획 요구를 줄여 두었고, 뒤에 계획·design이 이를 '복원/삭제' 대상으로 적었다(부록 3 요지). design이 스스로 만든 A형 예외는 거의 없다.
3. **A에는 대부분 대체 card가 있다.**
   - 계획 층: 34건 중 card 없는 것은 2~3건이다.
   - design 층: 대체로 card가 있다. ME-1·EO-1·LA-1·IT-2d·DE-1·SF-1·GV-1 등이다.
   - code 층: card를 찾지 못한 것이 많다. 부록 5에서 7건, 부록 6에서 2건이다(§5).
4. 반대 방향의 사실도 있다. **C 25건은 '계획 미반영'이 아니라 근거가 없거나 as-built를 정당화하는 예외다.** 이 중 다수가 code 층(9건)에 있고, 계획·design 어디에도 근거가 없다(§4).

## 4. ⚠ fail-open 및 C 핵심 목록

| # | 위치 | 내용 | 분류 | 대체 card | 상태 |
|---|---|---|---|---|---|
| 1 | `metrics/sensitivity_gate.py:16·30-33`, `search/gate_run.py:45-52`, `find_front.py:72-75` | 감도 게이트가 검사 못한 섭동(None)을 오류로 세지 않는다. 하나도 못 재도 verdict `ok`이고, gate가 None이면 note도 없다(커밋 `d0ba5bde`) | C ⚠ | 없음 | 남음 |
| 2 | `search/find_front.py:103` | `counted_rails` 미선언 + `supply_current_dc` 제약이면 `not_computed` 표지만 남기고 통과 | A ⚠ | SF-1 범위 8 (미병합) | 남음 |
| 3 | `authoring/spec_constraints.py:265` | 출처 `pending_spice` 제약은 판정 없이 통과(`judged False`) | A ⚠ (사용자 결정 U-35/U-17) | ME-1 | 남음 |
| 4 | `authoring/spec_settings.py:38` | `search_method="precision"`을 받아들이고 정지하지 않음. 계획 PR-1·U-66 '조용한 폴백 없음' 위반 | A ⚠ | PR-1 | 남음 |
| 5 | 계획 DEC-74 / O-118·U-108 (gb), offset-strategy:561·offset-trim | 계통 offset을 커널 판정에서 빼고 front 전용, 'ΔW=0 → 0(통과)' | A ⚠ (gb에서는 근거 오류로 정정) | DE-1 (c) 미착수 | gb 계획에서는 해소, 엔진·offset-strategy/trim 문서에는 남음 |
| 6 | `search/iv_gain_l.py:125-127` | 평가할 앵커가 없으면 `anchors[-1]`로 닫고 이득 0 dB 가정 | A ⚠ | LA-1 범위 15 | 남음 |
| 7 | `search/iv_currents.py:151·167` | 미지수 ≠ 1인 행을 조용히 `continue` | A ⚠ | LA-1 범위 13 | 남음 |
| 8 | `start_intervals.py:384`, `iv_area.py` `area_bounds` | 실행 불가 `final = bottom`을 칸 0으로 사용. 충돌 소자는 기록 없이 `continue` | A ⚠ | GC card | 남음 |
| 9 | `sizing/writer_plan.py:124` | 출력 넷이 F′ 안인 경우(계획 O-64 (1)의 공백)에 as-built `kvl_fixed`를 잠정 유지 | C ⚠ | 없음 | 남음 |
| 10 | `l_classes._main_path_starts` | current_reuse에서 첫 뷰를 쓰는 fail-open을 '기록만' 함. GV-1 범위에서도 명시적으로 제외됨 | C ⚠ | 없음 | 남음 |
| 11 | design v1.15.1 `cm_reference_undetermined` | 평형 검사 생략 예외 | C ⚠ | 계획 v6.38.3 DEC-105 (7)이 금지(검증 대기) | 남음 |
| 12 | `metrics/dc_metrics.py:115-118`, `layout/passives.py:21` | 값 미정 수동소자는 면적에서 빠지고 head 면적 미선언은 0.0. front를 내고 `review_needed` note만 | A/C ⚠ (약) | 없음 | 남음 |
| 13 | `sizing/block_columns.py:744-780` | 입력 창 미측정·미수렴이어도 진행하고 `unmeasured`/`unsettled` 표지만(커밋 5eace7f8 "종래보다 나빠지지 않는다") | C △ | 없음(IT-2d가 판정 창을 따로 둠) | 남음 |
| 14 | `lut/derived_fns.py:117-130` | `tol_vdsat_max`가 표나 칸이 없으면 0.0. 정의 불능을 숫자로 메움(층 0 출발 곡선만) | C △ | 없음 | 남음 |
| 15 | `search/macro_poles.py:137-157` `zc_fallback` | 영점 상쇄 R 등에 θ 상자 기하 중점 자리값을 씀. O-127/B80·B81 결함 유형과 같은 꼴(출발값 전용) | C (원칙 충돌 소지) | 없음 | 남음 |
| 16 | `metrics/block_gain_model.py:20-23` | L bin 안 극값 세분이 미구현이라는 사실이 docstring에만 있음 | C | 없음(UB-1 포함 안 됨) | 남음 |
| 17 | design 40 R18 | 지속 진동을 '사용자 승인'으로 적은 as-built 계약 | C | -- | 남음 |
| 18 | design 40 ng-area-budget | 임의 상수 곱으로 면적 예산을 우회 | C | 없음 | 남음 |
| 19 | 계획 K-h | 비레일/레일 g=s 비대칭. 계획이 스스로 '물리 근거 없음, 보존만'이라고 적음 | C | 백로그 B-G3만 | 남음 |
| 20 | 계획·design oracle O-01·X-D1 | 출처 미확인 상수 다섯(`*_TOP_K_MAX`·`INTEGRAL_K_MAX`·`ZOOM_*`) | C/A | 백로그 X-D1만 | 남음 |
| 21 | oracle O-09·O-10 | `off_current_A`가 없으면 문턱 0·`W_ref` 대체값. 게이트 전용 이상 전압 넷 조건은 검사 안 함 | C | 없음 | 남음 |
| 22 | 계획 I-H3 (P1-16) | V/V 행용 eps 건너뜀 문턱이 A/V 행에도 걸림(단위 불일치) | C | 없음 | 남음 |
| 23 | U-123 `legacy_adapter` | 부하 이중 계상(nmcnr SR 약 1.93배 과소) | A | OP-12 | 남음 |

## 5. (A) 중 대체 card가 없는(또는 미래 card뿐인) 항목

| 출처 | 항목 | 비고 |
|---|---|---|
| 계획 P2-02 / design D40-10 | current_reuse 슬루·정착 판정을 AP-1까지 대기 | AP-1은 '미래 card'라 기한이 없다. 착수하려면 계획 개정이 필요하다 |
| 계획 O-01 / X-D1 | oracle 출처 미확인 상수 다섯 | 백로그만 있다 |
| design P-03 | 레지스트리 '보류' | card가 아니라 Phase 4 배선 몫이다 |
| code E5-04 | MOD8 재필터 몫 = 0 | card 미확인 |
| code E5-05 `search/eval_budget.py:12·18` | `reserve_evals=0`, "U15 `layer0_budget` 전" | U15가 엔진에 없다 |
| code E5-06 | docstring이 'card C'에 맡김 | 현 계획에 그 card가 없다 |
| code E5-16 `graph/s1_values.py:29` | 이상 전압원 미구현 → 기록만 | 정지하므로 fail-closed. rail 대체 경로는 있다 |
| code E5-20·21 | 수동소자 면적·`counted_rails` 미선언 처리 | 21은 SF-1 범위 8과 겹치는지 확인이 필요하다 |
| code E5-22 | U-47 | card가 아니라 열린 이슈다 |
| code E6-02 `sizing/writer_plan.py:257` | DEC-76 다중 입력 뿌리 | 정지(fail-closed)다. 이 안전망이 영구로 남는다 |
| code E6-05 `sizing/seal_kcl.py:9` | 봉인 3 `exclude_nets`를 선언할 자리가 없음 | 더 엄격한 쪽이다(무해) |

## 6. 그 밖에 발견한 것(참고)

- **낡은 문언이 남아 있다.**
  - `search/constraints.py:13·15`의 "VDSAT 접근자 없음", "ss_linearize 없음": 지금은 둘 다 있다.
  - `find_front.py:9`의 "모든 점이 pending_front": 지금은 사실이 아니다.
  - design 40:1219의 U11 '잠정': 이미 U13으로 대체됐다.
  - 계획 P1-14·15(gmb '임시', CGG−CGD 근사): LUT v2에 열이 있어 해소됐을 가능성이 높다.
- **계획 내부 문언이 서로 맞지 않는다(P1-29).** N3.6은 '정착은 기록만'이라고 적고, DEC-90 (2)·O-145는 정착을 oracle이 판정한다고 적는다.
- **design 40 §8의 '복원' 21행(R2~R26)은 엔진 상태를 행별로 확인하지 못했다.** 후속 확인이 필요하다.
- **IT-2c/2d가 아직 병합되지 않았다.** integ-it12에 `icm_config`·`dc_window_cfg`가 0건이다.
- **SF-1 병합 순서 위험(P1-38).** `swing_out_v` 삭제가 소비자보다 먼저 병합되면 출력 범위 요구에 공백이 생긴다.

## 7. graph 단일 정본 규칙 점검(별도 항목)

- 이 감사는 새 계산·cache·필드를 제안하지 않는다.
- 이 감사에서 D로 분류한 LUT memo·디스크 캐시(U-87)와 블록 안 local memo는 N3.3·N3.5의 승인 예외 목록과 일치한다.
- `zc_fallback`(§4 #15)은 상자 중심 자리값으로 종속 양을 정하는 것이다. O-127 위반 소지로 따로 표시했다.

---

# 부록: 구획별 전수 표 (구획 agent 작성, 원문 그대로)


## 부록 1. 계획 gain-budget N0~N5 + v6383 diff

### part1 -- 계획 gain-budget N0~N5(1~1200행) + plan-v6383 diff 예외 감사 (fork 1)

- 읽은 판: master `chip-design-skills` HEAD `9d153f2f` (`docs/01-plan/features/gain-budget-gmid-sizing.plan.md` v6.38.2), plan-v6383 worktree HEAD **`ebbae815`** (브리핑 시점 `770288a1`에서 한 커밋 진행 -- 넷째 커밋까지 포함해 diff `9d153f2f..ebbae815`를 읽음). 쓰기 없음.
- 행 번호: `GB:` = master gain-budget plan 행, `v3:` = plan-v6383 HEAD의 같은 파일 행(+diff hunk 시작 행), `HC:`/`GC:` = headroom-chain/graph-consumption plan(v6383).
- 범위 밖으로 발견한 것(다른 fork 몫): N6 card 본문(1200행 이후)의 IT-1·SF-1·LA-1 예외 문언 일부는 v6383 diff에 걸린 것만 다뤘다.

#### 1. 예외 표

| key | 위치(파일:행) | 내용 한 줄 | 분류 | 근거 | 대체 card/규칙 | 상태 | fail-open |
|---|---|---|---|---|---|---|---|
| P1-01 | GB:274 DEC-74, GB:223 DEC-23, GB:266 DEC-67 (c), GB:2446(N7) | 계통 offset `offset_sys_mv`를 커널 판정에서 빼고 front에서만 판정하는 "front 전용 예외" | C → 계획 해소, 엔진 A | 원 근거 'θ 프레임 봉인점에서 구조적 0'은 "근거 오류"(O-118 1번); 계획 대체 = 커널 + front 판정 W 재판정(U-108, O-119). 계획 문언: "커널에서 빼면 탐색이 offset 위반 점을 받아들이는 fail-open" | 있음: card DE-1 (c) ("DE-1 (c) 착수 전") | 계획 해소 / 엔진 남음 | ⚠ (엔진이 아직 커널 판정 안 하면 fail-open) |
| P1-02 | GB:223 DEC-23, GB:396(O-62 (3)) | 'ΔW = 0 → 0(통과)' 엔진 1차 규칙 | C | O-118 1번이 "근거 오류"로 삭제(일반형 (나′)에서 ΔW=0이어도 성분 (1)(2)가 남음) | 있음: DEC-23 (나′) / card DE-1 (c) | 계획 해소(엔진 반영은 DE-1) | ⚠ (통과로 처리하던 규칙) |
| P1-03 | GB:223 DEC-23 ("지금 엔진은 A_dm = 0일 때만 `gain_zero`로 정의 불능, `offset_systematic.py:51-52`") | A_dc 정의 불능 갈래가 엔진에서 정확히 0일 때만 발동(분해능 이하 갈래 미구현) | A | 계획 문장이 as-built와의 차이를 명시, 판정 자리 = DE-1 (c) | 있음: card DE-1 (c) | 남음 | 확신도 낮음(분해능 이하 A_dc는 큰 σ로 실패 쪽이라 fail-open 아닐 가능성) |
| P1-04 | GB:1190 I-H2 | A_dc 생산자 둘(`offset_analysis.py:74`, `offset_systematic.py:50`) -- graph 규칙 1 위반 용인 | A | O-71 '별도 위험'; 갈래 판정 자리 하나 = DE-1 (c)(GB:223) | 있음: DE-1 (c) | 남음 | - |
| P1-05 | GB:11(v6.35.1), GB:648 | `l_classes._main_path_starts`(L 주인 할당) current_reuse에서 첫 뷰 규칙 사용 -- "current_reuse 첫 뷰 대신 fail-open은 기록만" | C | "다른 축(L 주인 할당)으로 둔다"만 있고 고칠 card 지정 없음; 같은 결함의 achievability·block_residual은 GV-1로 감 | 없음(GV-1 범위 밖으로 명시) | 남음 | ⚠ |
| P1-06 | GB:11(v6.35.1), N6.27 GV-1 | achievability·block_residual이 판정 gain 전달 뷰를 첫 뷰 규칙으로 고르는 둘째 생산자 용인 | A | "기존 위반을 IT-2c에서 고치지 않고 card GV-1로"(원래 취지와 다름 승인 O-117) | 있음: card GV-1 | 남음 | - |
| P1-07 | v3:304 DEC-105 (1), N7 U-133 | as-built `E/search/iv_gain_l.py:125-127`: 평가 앵커 없으면 가장 긴 앵커로 닫고 이득 0 dB 가정 margin | A | O-164: as-built 결함으로 지목, 대체 = 정의 불능 fail-closed | 있음: card LA-1 범위 15 | 남음 | ⚠ (상수 0 dB 가정 = 폴백 기본값) |
| P1-08 | v3:304 DEC-105 (7) | design v1.15.1의 `cm_reference_undetermined` 평형 검사 생략 예외 | C | v6.38.3 넷째 커밋: "평형 검사를 건너뛰는 생략 예외는 두지 않는다"(외부 CM 기준 미선언 = fail-closed) -- design이 근거 없이 둔 생략 | 있음: DEC-105 (7)(계획 v6.38.3, 검증 대기) | design 남음(계획 개정 미승인) | ⚠ |
| P1-09 | GB:263 DEC-64, HC:70·161, GC:53·367·397 | as-built 쓰기 계획이 입력 포트 '같은 DC' 엣지(`input_tie`)·공동 y 키 유지 -- "IT-1이 병합되기 전까지 엔진 as-built는 `input_tie`를 쓴다(결정과 as-built 불일치, F-5)" | A | 결정 B2·K-3·O-13; v6.38.3 O-168/DEC-106으로 IT-1 범위 재작성 | 있음: card IT-1(integ/it12에 구현·master 미병합, v6.38.3 범위 재작성) | 남음(master) | - |
| P1-10 | GB:1500·1525·1555(N6.5 IT-1 범위 4, IT-Q1) | 다중 입력 W4 뿌리 y 묶음·창 '미구현(발동 0)' + 정지 안전망 | B(DEC-76) → v6.38.3 대체 | DEC-76·F-IT9(발동 0); v6.38.3이 DEC-106으로 정지 분기 삭제, "그 밖의 다중 입력은 정의 불능 정지" | 있음: DEC-106 / IT-1 재작성 | 계획 개정 중(검증 대기) | - (fail-closed) |
| P1-11 | GB:224 DEC-24, GB:291 DEC-92 (ii)(b), v3:224·269·291·632·2222 | 영점 상쇄 저항 = 구조 규칙 R=1/Σgm 기본 + θ 폴백 | A | O-33 (10)이 대체("구조 규칙은 출발값, θ 연속 성분"), v6.38.3이 문언 정렬; 엔진 상태 '미구현', as-built '구조 규칙 고정값 + 폴백 θ' 경로 삭제를 SF-1 범위 9가 소유 | 있음: card SF-1 범위 9 | 남음 | - |
| P1-12 | GB:663(N3.8 metric 표), GB:1998 VB-1 | `offset_sys_mv` 지금 oracle 미측정(`verified_by.py:45`) | A | "엔진 measure 연결 card VB-1" | 있음: card VB-1 | 남음 | 확신도 낮음(미측정 = 판정 보류 꼴이면 fail-open 아님) |
| P1-13 | GB:271 DEC-72, GB:189 NFR-5, GB:279 DEC-79/80, GB:1197 | 모델 오차(성능·면적 축) 측정 전 "여유 판정 보류"·"검증 대기"(통과로도 실패로도 세지 않음) | A | 7a SPICE 대조(U-11) 미실행이 이유 | 있음: card ME-1(7a) (면적 축 몫 확신도 낮음) | 남음 | - (보류 명시) |
| P1-14 | GB:641 N3.8 gmb | LUT `GMBS` 열 생기기 전 VS 축 수치미분 gmb를 '임시'로 표시 | A | U-27 LUT 재생성 전 임시 | 있음: U-27(LUT 재생성) | 해소 가능성 높음(v3:304가 `sky130_lut_v2` W 슬라이스에 GMBS 열 있다고 기술) -- 계획 문언 낡음, 확신도 중 | - |
| P1-15 | GB:1147 DF-28, N3.8 스탬프 문단 | CGS·CGB 열 전 CGG−CGD 근사 스탬프·'검증 대기' | A | U-27 전 임시 | 있음: U-27 | 해소 가능성 높음(v2 기준 폭 표에 CGS·CGB 열, v3:304) -- 문언 낡음, 확신도 중 | - |
| P1-16 | GB:1191 I-H3 | 전도 행(A/V)에 V/V 행용 `\|rate\| ≤ float eps` 건너뜀 문턱이 그대로 걸림(단위 다른 비교) | C | "판정 영향 없음, 기록만"; 근거 측정 없음 | 없음("미정 -- 수요가 생기면 card") | 남음 | 확신도 낮음 |
| P1-17 | GB:266 DEC-67 "예외(명문화, O-26 (4))", GB:661 | 봉인 전 값 금지의 예외 -- 풀이 공간 상위집합 위 상한 인증(`block_gain_bound`·`headroom_bound`) | B | 물리 결정자: 상위집합 위 상한은 수학적으로 안전 쪽('상한'으로만 표기, 값으로 안 씀). `headroom_bound` 포함은 "오케스트레이터 해석, 사용자 변경 가능" | 규칙 자체 | 유지 | - |
| P1-18 | GB:243 DEC-44, GB:472·477·486·497·685, J1 | 교류접지 예외(뷰 한정)·바이어스 레플리카 -- 사람 공동분석 ratify, 엔진은 `review_needed`까지 | B | 회로 해석은 사용자 공동분석(DEC-44) | 규칙 자체(J1 ratify, structure.json) | 유지 | - |
| P1-19 | GB:101·262 DEC-63, GB:485 | pass 셀은 follower 묶음 밖(J10 예외), 다출력 버퍼·흡수 안 되는 pass = `기록만` 분기 | B | 셀 정의(gate가 신호 경로 밖); `기록만` 분기는 DEC-59로 탐색 전 정지(GB:258, v3:632 "항상 DEC-59 정지") | 규칙 자체 | 유지 | - (fail-closed) |
| P1-20 | GB:270 DEC-71 (3), GB:275 DEC-76 | 경로 열거 예산 초과 시 가지 단위 축소 폴백 -- '미구현(발동 0)' + 정지 안전망 | B | DEC-76/WP-01(발동 0 폴백은 만들지 않음, 정지 안전망) | 규칙 자체(발동 회로 생기면 구현) | 유지 | - (fail-closed) |
| P1-21 | GB:270 DEC-71 (4) | 역산 불가·LUT 비단조 소자는 격자 탐색으로 폴백, 사유 기록 | B | 물리 결정자: 비단조 구간에서 역함수 정의 불능; 사용자 결정 A1(역산은 후보 생성, 격자가 검증) | 규칙 자체 | 유지 | - |
| P1-22 | GB:270 DEC-71 (4)(b) "예외" | R5′ (4)(iii) '이득 행 재개방' 후보에 한해 S 소자 L 역산 고정 해제 | D | 사용자 결정 O-160 F-3, "원래 취지와 다름(승인 O-162)" | 규칙 자체 | 유지 | - |
| P1-23 | GB:270 DEC-71 (2)(3) | 버퍼 블록 AC 제약 빈칸 → rout 상한 대체, 그것도 없으면 '층 0 무동작'·출발 구간 탐색·'성능 판정 보류' | B | 실측(자명해 수렴, `pushpull_follower_buffer`), 사용자 Q5b(2026-10-08), WP-01 | 규칙 자체 | 유지 | - (보류 명시) |
| P1-24 | GB:272 DEC-73 (3)(b) | 층 0 조합이 봉인 실패로 소진되면 외층 대체 경로 + '층 0 조립 실패 경로'·'성능 판정 보류' | D | O-33, Q5b 선례 "조용한 대체 아님" | 규칙 자체 | 유지 | - |
| P1-25 | GB:222 DEC-22, GB:233 DEC-34, GB:274 DEC-75, GB:454 GB9, GB:900 N3.13 | bisection·전역 샘플 등 '기본 비활성'(선언으로 켬) | D | DEC-75(사용자), WP-02: 끄는 것을 skip 분기로 만들지 않음 | 규칙 자체 | 유지 | - |
| P1-26 | GB:615, GB:1802 PR-1 | 정밀 경로(내층 DP) 선언 시 `precise_path_not_implemented` 정지 | A(정지) | U-66 "(가)", design은 U-33 측정 뒤 | 있음: card PR-1(정지만), 구현 card 없음(조건부) | 남음 | - (fail-closed, 예외 정의 밖 -- 참고용) |
| P1-27 | GB:164, GB:296 DEC-96 (3) | PVT 코너: 합격 = TT 27°C 한 조건, 코너 메타 '기록만', ss/ff 오라클 옵션 범위 밖 | D | 사용자 승인 P-14(2026-10-12) 범위 결정 | 없음(마일스톤 1 뒤) | 유지 | - |
| P1-28 | GB:590 N3.6 (i), GB:289 DEC-90 (2) | SPICE 합격 실행에서 측정 불가 제약은 `spice_unverifiable[]`로 사유 기록 | B | 측정 구성상 불가능한 제약(물리) | 규칙 자체 | 유지 | 확신도 낮음(합격 계산에서 빠지면 fail-open 가능 -- design 확인 필요) |
| P1-29 | GB:590 vs GB:289 | GB:590은 "정착은 기록만", GB:289 DEC-90 (2)는 "정착은 oracle `.tran`이 판정"(O-145) -- 낡은 문언 | C | O-145로 대체됐는데 N3.6 문장 미갱신 | 있음: DEC-90 (2) | 문언 남음 | 확신도 중 |
| P1-30 | GB:666 metric 표 슬루, GB:297 DEC-98 (6), GB:349 O-124 | 슬루: 엔진 판정 값 없음, 'oracle 판정 대상' `unmeasured_front`, held-out 슬루 선언 회로 최종 front는 U-112까지 빔 | D | O-122·O-124(원래 취지와 다름 승인); U-112 닫힘(front 제외·기록) | 규칙 자체(oracle 판정) | 유지 | - |
| P1-31 | GB:668 metric 표 | `ff_gm_ratio`·`block_residual`·`nqs_ratio` 보고 전용·미측정 | D | 보고 전용 metric(판정 없음) | - | 유지 | - |
| P1-32 | GB:285 DEC-86, GB:31·72·74·119~121·236~241·740~899·1036~1105 | 역할 분리 gate·V1~V10·Phase 0.5·spec card 전부 끔(가벼운 절차) -- 그 안의 V6 `optional_stages` 화이트리스트 예외, 순서 4·5 생략(test-only), N/A 도입 전 Phase 포함 | D | 사용자 2026-10-07 "phase3를 가벼운 절차로", 남는 것 넷(WP-13·기준 약화 보고 등) | 일부 일반 test로 이식(GB:1038·1057) | 폐기 상태 유지 | - |
| P1-33 | GB:304 DEC-105 (1) 옛 문언 'A_max가 미상이면 비활성' | 이득 L 하한 활성 조건 예외 | C | 이미 삭제됨("옛 'A_max가 미상이면 비활성' 삭제") | 있음: DEC-105 (1)/L-2 | 해소(계획) | - |
| P1-34 | v3:304 DEC-105 (1)(v6.38.3), N7 U-133 | found_db 없는 블록이 있는 뷰 → 출발 단계 이득 L 하한 정의 불능(층 역전 회피) | B | 물리·층 순서: 출발 단계는 층 0 기준점을 못 읽음; 0 dB 가정은 ⚠ 상수 발명으로 기각 | 규칙 자체(검증 대기) | 개정 중 | - (fail-closed 아님: 정의 불능 표시 후 진행 -- 출발값이라 판정 영향 없음, 확신도 중) |
| P1-35 | v3:304 R7 (가) | 선언 범위 고리 B가 합 행 위반 시 `StartConflict` 기록만(재개방 촉발은 R-1′ 행만) | B | O-158 (A′) ②: 출발 단계는 판정 아님, 거부는 커널 뒤 | 규칙 자체 | 유지 | - |
| P1-36 | v3:2503 U-128 U2 | 단일 출력 5회로 `offset_sys_mv` 선언 보류 | D | "원래 취지와 다름(O-168)" -- 출력 기준 선언·상한 근거 형식이 계획·design에 없음 | 없음(계획·design 개정 필요) | 남음 | 확신도 낮음(제약 미선언 → 판정 안 함) |
| P1-37 | v3:386(N2.1 O-168 행) | DEC-106 결정 문언 '입력 포트들을' → '선언된 차동 입력쌍'으로 좁힘(그 밖 정의 불능) | B | 물리 결정자 범위(같은 원이 같은 CM으로 구동) -- "승인 때 확인" | 규칙 자체 | 검증 대기 | - |
| P1-38 | GB:2178(SF-1) | `swing_out_v` 삭제가 소비자보다 먼저 병합되면 출력 범위 요구 공백(fail-open) | D | O-155 M-1: 원자적 통합 병합 규칙으로 막음 | 있음: 병합 규칙(SF-1) | 해소(규칙) | ⚠(규칙 어기면) |
| P1-39 | GB:386 O-73 | "IT-0은 as-built로 병행"(SD-1 data card 전) | A | DUT/응용 망 분리 1단계 card SD-1 전까지 as-built 사용 | 있음: SD-1·AP-1 | 확신도 낮음(IT-0 완료 여부 미확인) | - |
| P1-40 | GB:11(v6.34.1) B77 | 용량만 결측인 점에서 DC metric까지 정의 불능(원래 취지와 다름) | A | "B77 미해결" → 뒤 커밋 "IT-2d에서 해소" | 있음: IT-2d | 계획상 해소 | - (보수 쪽) |
| P1-41 | GB:294 DEC-97 (4) | 시간 예산 300 s를 front 전체에 쓸지 '보류' -- cProfile 뒤 재질의 | D | U-47·U-49 측정 대기(결정 보류, 규칙 우회 아님) | U-47 | 남음 | - |

#### 2. 예외가 아니라고 버린 hit (수만)

- 후보: master grep 줄(gain-budget 1~1200행) 179 + v6383 diff 고유 hit 45 = **224**.
- 위 41항목에 묶인 hit 약 85. **버린 hit 약 139**. 종류별:
  - 결정 레지스터 상태 칸 '미구현'(DEC-01·03·06·29·30·31·36·43 등 구현 진도 표기, 우회 아님) 약 35
  - Python 예외 클래스·N3.14 실패 규약(`InfeasibleSizingError`·`예상 밖 예외 전파`·`test_no_broad_except`) 약 8
  - fail-closed 정지(DEC-59 `기록만` 분기 정지, DEC-60 `supply_nets` 거부, DEC-61, 정밀 경로·counted_rails 보류 정지, O-145 SR 정의 불능 front 제외 등) 약 40
  - 정의 불능 → front 제외(`unmeasured_front`) 같은 fail-closed 정의 불능 갈래(O-53·O-61·O-79·O-85·O-115 등 N2.1 행 서술) 약 30
  - N5.2 DF 표(옛 엔진 결함 = 새 엔진 재발 금지 계약 목록, LT-1로 옛 엔진 삭제) 약 6
  - 역사·용어 서술(Status 줄 경위, '임시 파일 → 교체', '임시 지문 두지 않음', 용어집 '기준 약화' 정의 등) 약 20
- 판단: N5.2 DF-14·DF-20·DF-37(옛 엔진의 except 폴백·폴백 상수)은 새 엔진 재발 금지 계약이라 계획 예외가 아님(엔진 code 쪽 fork가 실제 잔존 여부를 확인할 몫).

#### 3. 분류별 수 (41항목)

| 분류 | 수 | 비율 | 항목 |
|---|---|---|---|
| A (계획 있음, 엔진·design 미반영이라 임시) | 13 | 32% | P1-03, 04, 06, 07, 09, 11, 12, 13, 14, 15, 26, 39, 40 |
| B (물리·원칙 정당) | 11 | 27% | P1-10, 17, 18, 19, 20, 21, 23, 28, 34, 35, 37 |
| C (근거 없음·근거 오류·as-built 정당화) | 7 | 17% | P1-01, 02, 05, 08, 16, 29, 33 |
| D (사용자 범위 결정·선택 기능·gate 끔 등) | 10 | 24% | P1-22, 24, 25, 27, 30, 31, 32, 36, 38, 41 |
| 합 | 41 | 100% | |

- C 7 가운데 계획에서 이미 해소: P1-01(계획), 02, 33 -- 다만 P1-01·02는 엔진 반영(DE-1 (c))이 남아 실질은 A로 이어짐. 이를 A로 겹쳐 세면 A 15(37%).
- A 13 가운데 P1-14·15(LUT 열)는 데이터상 해소됐을 가능성이 높고 계획 문언만 낡음(확신도 중).

- A 중 대체 card 없음: 없음(13개 모두 card 있음; P1-26 PR-1은 정지만 하는 card이고 구현 card는 조건부).
- C 중 대체 card 없음: P1-05(`_main_path_starts` 첫 뷰 fail-open), P1-16(eps 건너뜀 문턱).
- fail-open ⚠: P1-01(엔진 offset 커널 판정 미반영), P1-02(ΔW=0 통과 -- 계획 삭제됨), P1-05, P1-07(0 dB 가정), P1-08(design CM 평형 검사 생략), P1-38(병합 순서 어기면).

#### 4. 사용한 명령

```
### 후보 줄(공통 스캐너 -- 부모가 작성)
python scan.py doc <master>/docs/01-plan/features plan_master.txt .plan.md
###   DOC 정규식: 예외|생략|건너뜀|건너뛴|폴백|fallback|임시|미구현|당분간|as-built 유지|as-built|정의 불능|기록만|unmeasured|표지만|보류|우회|skip
grep '^gain-budget' plan_master.txt | awk -F: '$2<=1200'
### grep 밖 표현 보강(문맥 ±120자)
python -X utf8 -c "...re.compile(r'통과로|N/A|정지 대신|면제|비활성|꺼진|끈다|gate 끔|기록만|폴백|fallback|예외 규칙|교류접지 예외|상한 예외|unmeasured|미측정|임시|당분간|as-built|건너|생략|보류|우회|정의 불능')... for i in range(1200)"
python -X utf8 -c "...for pat in ['fail-open','승인 예외','iv_gain_l','GMBS','CGS·CGB','U-27']..."
### v6383 diff
git -C wt/plan-v6383 log --oneline 9d153f2f..HEAD      # HEAD = ebbae815
git -C wt/plan-v6383 diff -U0 9d153f2f ebbae815 -- docs/01-plan | (+줄만, 같은 정규식 + 통과로|면제|비활성|fail-open, history 파일·Status 11행 제외, 파일·hunk·단어별 중복 제거)
```

## 부록 2. 계획 gain-budget N6 + 다른 plan

### part2 -- 계획 층(master `9d153f2f`): gain-budget N6 이후(1200행~끝) + 나머지 *.plan.md

범위: master `chip-design-skills/docs/01-plan/features/` -- gain-budget-gmid-sizing.plan.md 1200행~끝, oracle-portability(op), graph-consumption(gc), headroom-chain(hc), offset-strategy(os), offset-trim(ot), analog-topology-json-library, verilog-*. (v6383 diff는 fork 1 담당.)
상태 확인용 엔진 = `wt/integ-it12` `d759838a`(읽기만). gb = gain-budget-gmid-sizing.plan.md.
같은 예외의 반복 언급은 한 행으로 묶었다(위치 칸에 대표 행 + 동반 행).

#### 표

| key | 위치(파일:행) | 내용 한 줄 | 분류 | 근거 | 대체 card/규칙 | 상태 | fail-open ⚠ |
|---|---|---|---|---|---|---|---|
| P2-01 | gb:2178, :2231, :2186 | DE-1 병합 전 기간에는 범위 끝 이득 행을 `oracle_judged`로 표기하고 `unmeasured_front`로 보냄 | A | "DE-1 미병합 기간"; **원래 취지와 다름, 승인 O-162**; 재검증 5 G-4·6 H-3 | 있음: DE-1(N6.8) | 남음(엔진 `oracle_judged` 0건, SF-1·TB-1 미착수) | 아님(판정 보류이고 통과로 세지 않음) |
| P2-02 | gb:2186, :2128-2130 | current_reuse 슬루·정착 판정은 AP-1까지 '판정 대기' | A | O-128 Q5 '전류원 부하 표지 AP-1까지 fail-closed'; AP-1은 "정본 자리 없음 -- 계획 개정 착수 조건"(규칙 6) | 있음: AP-1(N6.22, **미래 card, 착수 조건 = 계획 개정**) | 남음 | 아님 |
| P2-03 | gb:2201 | TB-1 필드는 병합 때 엔진 소비자 0(‘만들면 배선’을 뒤로 미룸) | A | O-146 K2 'O-144 J3 이연 범위'; as-built `vds_saturation`도 test만 읽음 | 있음: 행동 소비자 = headroom card(같은 행에 명시) | 남음 | 아님(소비자 미배선 부채) |
| P2-04 | gb:1831(F-LA12), :1874, :1926(X-LA2), :1904, :1822(F-LA3) | as-built 층 0 = '최소형'(`layer0_center.py` 시작점 하나), `gain_budget_db` 출력 없음, 버퍼 rout 국소 AC 제약 E10 미구현이라 front 0 회로가 생김 | A(만들어진 경위는 C) | X-LA2 "계획 결정 없이 축소 상태 유지 -- D18 재발형 as-built 이탈"; U-49 '복원'(2026-10-08); FR-4·DEC-03 미구현; B80 | 있음: LA-1(N6.14) 범위 1·9 | 남음(`gain_budget_db`는 엔진에서 override 선언 자리에만 있음) | 아님(front 0 = 결과 없음). 단 무결정 축소라 원칙 위반(D18형) |
| P2-05 | gb:1849(LA-1 범위 13) | `iv_currents`가 미지수 둘 이상인 행을 건너뛰어 θ 전류가 정해지지 않고, 층 0 점 GBW가 목표에 못 미침 | A | B85, O-140 D8; 근거 `evidence/2026-10-26/design_v115_plan_defects.md` §6.1 | 있음: LA-1 범위 13 | 남음(`search/iv_currents.py:151, :167` `continue`) | ⚠(확신도 중간): 기록 없이 건너뛰는지는 fork 5가 확인할 것 |
| P2-06 | gc:226, :464, :655, :793; gb LA-1 범위 15 (a) | `gain_l_bounds`: 원소가 없으면 앵커를 건너뛰고, 앵커가 모두 빠지면 `found = anchors[-1]`(최대 앵커)를 L 하한으로 씀 | A | v0.14.3 "분기 소유 = 상위 LA-1 범위 15 (a)", O-165 (a) | 있음: LA-1 범위 15 (a) | 남음(`search/iv_gain_l.py:126`) | ⚠ 값 대체 폴백(`SRC_GAIN_L` 충돌 기록은 있음) |
| P2-07 | gc:226(F-G32), :440, :454, :604(X-G11), :779(U-G13) | `start_intervals`: 최상 칸이 실행 불가면 `final = bottom`, 아래 끝도 불가면 이분 탐색을 건너뛰고 실행 불가 점을 칸 0으로 씀; 빈 사다리면 `_report`에서 IndexError | A | O-10 (4), O-13 (가-1), X-G11(원래 취지와 다름 승인) | 있음: GC card(N3.6-3, GC-5 범위) | 남음(`search/start_intervals.py:378-396` 그대로) | ⚠ 실행 불가 점이 칸 0이 됨 |
| P2-08 | gc:460, :793, :655 | `area_bounds`가 충돌 소자의 W_min gm/ID 하한을 기록 없이 건너뜀(`iv_area.py:68-69`); `matching_bounds`의 `SRC_MATCH_L` 사유 누락; `iv_noise.py:77-78` | A | O-10 (4), FR-G12 "표지만 세우고 안 읽으면 조용한 대체·생략" | 있음: GC-5(1회차 전류 충돌 다섯 자리) | 남음(`area_bounds`가 `nodes is None`이면 `continue`) | ⚠ 기록 없이 건너뜀 |
| P2-09 | gc:213(F-G19); gb:1462(F-IT1), :1454 | K-3 미구현: 입력 DC 미선언 회로에서 이웃 입력 포트를 '같은 DC' 변(`input_tie`)으로 이음 | A | B2·K-3, O-14 (2) "구현은 아직" | 있음: IT-1(N6.5) | **해소**(엔진 `.py`에서 `input_tie` 0건, `sizing/CONTRACT.md`에만 문언이 남음) | -- |
| P2-10 | gb:1808(PR-1), :2404(U-66) | `search_method = "precision"`을 선언하면 정지해야 함(정밀 경로 미구현) | A | DEC-73·76, U-66 (가) "조용한 폴백 없음" | 있음: PR-1(N6.13) | 남음: 엔진 `authoring/spec_settings.py:38`이 `"precision"`을 받아들이는데, 정지시키는 코드가 엔진 어디에도 없음(`git grep search_method`) | ⚠ 계획은 fail-closed인데 엔진은 기본 경로로 조용히 진행 |
| P2-11 | gb:1377(F-LT7), :1389, :1403, :1428(X-LT2) | 옛 원본이 없으면 layout SD 대조 test를 skip(skip 자리 17개, test 항목 73개); copy_audit 규칙 D·G 면제 | A | L-2 (3), LT-1 "legacy 삭제로 깨지는 test" | 있음: LT-1(N6.4) 순서 1·X-LT2 | 남음(`tests/layout/conftest.py:30` `pytest.skip`; `tools/spice_oracle/legacy_adapter.py` 존재 = LT-1 순서 3 미완) | ⚠(test 층) skip이 통과처럼 보임 |
| P2-12 | op:343, :514; gb:2460(U-123) | `legacy_adapter` 출력 부하 이중 계상: '이 계획에서 고치지 않는다'의 예외로 LT-1 삭제 전까지 재측정 경로를 고침 | A | O-157 S6, B89; **원래 취지와 다름, 승인 O-162** | 있음: OP-12, EO-1 '출력 부하 한 번만', LT-1 순서 3 | 남음(U-123 '미결 -- 수정·재측정') | ⚠ 지금 nmcnr SR 약 1.93배 과소 |
| P2-13 | op:18, :510 | OP-7 bin 경계는 선언 기록만 하고, 엔진 쪽 경계 방향 구현은 WB-1이 맡음 | A | v0.6.19, 상위 DEC-105 (2), O-165 (a) | 있음: WB-1 범위 0 | 남음 | 아님 |
| P2-14 | op:430 | 오라클 1단계에서 I_off ≤ ε·ID는 '2단계 대기'로 남김(통과로 세지 않음) | A | O-50 G3, 2단계 판정 = 엔진 EO-1 쪽 | 있음: oracle 2단계 + EO-1 | 남음 | 아님 |
| P2-15 | gb:2373(U-35) | `pending_7a` 제약은 7a 전까지 판정에 쓰지 않음; 두 회로는 제약 0이라 '사이징 판정 보류' | A | U-35 "7a 재도출 전까지", RC4 | 있음: ME-1(7a)·U-44 재도출 | 남음(7a 미실행) | 아님 |
| P2-16 | gb:1944(LA-Q3), :1966-1974, :1993; ot:391, :737 | 모델 오차(DEC-72)가 측정되지 않은 축은 '보류'로 두고 외층 기본값 '켬' 유지 | A | DEC-72 미구현, F-23 "경로가 구현되면" | 있음: ME-1, PW-1a·PW-1b, LA-2 | 남음 | 아님(보류는 통과가 아님) |
| P2-17 | gb:1354(N6.3 (i)), :2030, :2038, :1883; gc:576, :657, :658, :692; hc:531, :542; os:480, :528; ot:528, :600, :811 | 엔진 점을 oracle 입력으로 내는 생산자가 없어 SPICE 다리가 '보류'이고 card는 미완료 | A | N6.3 (i)(iv), O-44 (1) | 있음: EO-1(N6.20) | 남음 | 아님(보류 card를 병합할지는 사용자에게 올림) |
| P2-18 | gb:2434(U-96) | card C가 병합되기 전까지 card B는 블록 결과 색인 상한을 '보고만' 함 | A | U-96 (나), X-8 | 있음: card C(design 40 §2.4.14 (5)) | 확인 못 함(확신도 낮음) | ⚠(확신도 낮음): 상한을 넘어도 거부하지 않는 기간 |
| P2-19 | gb:2441(U-103); op:451 | as-built oracle servo는 이득 1이라 정의('출력을 봉인점에 묶음')를 어기는 회로가 있음(nmcnr 147 mV) | A | O-116 "정확 고정 + 오차 조건 -- 구현은 oracle card" | 있음: oracle card(OP-5 계열) | 남음(확신도 중간) | ⚠ 고치기 전 as-built 값으로 ICMR·스윙 판정을 하면 정의 위반 값 |
| P2-20 | ot:460 | Δ_T 입력 경로 미구현(F-23) | A | F-23 | 있음: TR-TL | 남음 | 아님 |
| P2-21 | os:672(W-1) | '만들면 배선'의 예외: 제품 진입점이 없어서(U16 미병합) 사슬 실행기의 제품 경로가 test 하네스임 | A | design E-S13 "`run_gmid_design_pipeline`은 자리만, U16 미병합"; 승인 칸 '필요' | 있음: U16 card | 남음 | 아님. 단 '만들면 배선' 절대원칙의 승인 대상 |
| P2-30 | gb:2251; N3.3 승인 예외 | LUT 조회 memo(graph 밖 cache) | B | graph 규칙 2 승인 예외(N3.3·N3.5), LUT 내용을 키로 한 순수 함수 | 해당 없음(정당 예외) | 유지 | 아님 |
| P2-31 | gb:2425(U-87) | LUT 파생표 디스크 캐시를 실행 사이에 유지 -- "원래 취지의 예외로 기록" | B | 사용자 결정 2026-10-15; 키 = LUT 내용 + 코드 버전으로 완결 | 해당 없음 | 유지 | 아님 |
| P2-32 | gb:1681; hc:139, :515 | DEC-67 상위집합 상한 예외: `headroom_bound` 상한 인증, VDsat 결측 격자점에 정의역 하한 0 | B | 상한 인증일 뿐 값으로 쓰지 않음(O-26 (4)) | 해당 없음 | 유지 | 아님 |
| P2-33 | gc:208, :702, :772 | 봉인 9의 `_off_current`는 전도 술어 단일화 대상에서 뺌 | B | 검증 경로(판정 권한)라 독립이 필요함, O-16 (3) | 해당 없음 | 유지 | 아님 |
| P2-34 | gb:1742(X-FX1), :1785 | FX-1: 단계 A가 봉인된 값(첫 칸 봉인 해)을 한 번 읽는 예외 | B | O-26 (3) 승인, 곡선 동작점 고정점의 물리 | 있음: design 41 개정 대상 | 남음(design 개정 전) | 아님 |
| P2-35 | gb:1734 | FX-1: 첫 칸 봉인이 실패하면 고정점을 돌리지 않고 '추정' 동작점을 그대로 씀("fail-closed 아님") | B(확신도 중간) | 출발 단계 값은 '추정' 표기(DEC-67), 판정은 봉인 몫 | 해당 없음 | 계획만(FX-1 미구현) | 아님(추정 표기 + 기록) |
| P2-36 | gb:1835 | 층 0: 역산 불가·비단조 구간이면 그 소자만 격자 폴백하고 사유를 기록 | B | DEC-71 (4), LUT 비단조 | 해당 없음 | 계획만(LA-1) | 아님 |
| P2-37 | gb:1885, :2394(U-56), :1845 | gain·rout 제약이 없는 회로 / 층 0 무동작 / 조립 실패 경로 -> '성능 판정 보류'로 탐색·보고 | B | DEC-71 (3) Q5b, LA-Q2(O-38 (1)), "표기 없는 대체 금지" | 해당 없음 | 남음(보고 배선 = LA-1 범위 9) | 아님 |
| P2-38 | gb:2362(U-24) | 공통모드 루프 제약이 선언되지 않으면 정지하지 않고 T_cm 보고 + `cm_loop_unconstrained` 경고 | B(확신도 중간) | Q1 R31 "예외 확정" | 해당 없음 | 구현됨(`graph/s1v_values.py`) | 아님(경고) |
| P2-39 | gb:1304, :1313, :2384(U-46) | 엔진 예측과 SPICE의 노드전압·ID 차는 합격 조건이 아니고 T8에 기록만 | B | 사용자 확정 2026-10-07 8번(합격 = 스펙 + 포화) | 해당 없음 | 유지 | 아님 |
| P2-40 | gb:1333 | A' 손분석점과 front 점의 전력·면적 차는 기록만 | B | U-76 (6) | 해당 없음 | 유지 | 아님 |
| P2-41 | gb:1595 | 약반전 꼬리 toy의 과보수(SPICE보다 좁음)는 단언하지 않고 기록만 | B | I-H3, 손계산은 보수 쪽이고 정확값은 oracle | 해당 없음 | 유지 | 아님 |
| P2-42 | gb:1658(SH-Q1) | 엔진은 `generator_sha256`을 기록만 하고 대조하지 않음 | B | O-18 (가), 대조는 oracle·OP-8 한 곳 | 해당 없음 | 유지 | 아님 |
| P2-43 | gb:1689 | 선언 슬루는 엔진에서 'oracle 판정 대상'으로 unmeasured 표시 | B | O-122, O-144 P0(SR ∝ θ 전류가 틀림), oracle `.tran`이 정본 | 해당 없음 | 남음(DE-1·VB-1) | 아님 |
| P2-44 | gb:1354(N6.3 (ii)), :1762(7), :2038 | SPICE로 정의되지 않는 값만 바꾸는 card의 SPICE 다리 = '대상 없음' | B | N6.3 (ii) 측정 구성상 무의미, 판정 소비자 0을 `git grep`으로 증명 | 해당 없음 | 유지 | 아님 |
| P2-45 | gb:2423(U-85) | 층 0 끌어올림 s = max(0, 식) | B | 목적 = 기준 전류 하한 충족 | 해당 없음 | 유지 | 아님 |
| P2-46 | hc:14-30, :83, :140, :304, :328, :568, :631 | 포화 면제 집합 = spec 선언 {triode, off}만; 엔진 자동 면제는 금지 | B | C-3, O-53 B1, D-2 "의도는 사용자만 정한다" | 해당 없음 | 유지 | 아님 |
| P2-47 | hc:300, :470(X-12), :564, :660(U-H15), :671 | 출발 단계의 포화 불가 판정은 기록만 하고 정지하지 않음(봉인이 거부) | B | U-H15 (가): 칸 판정은 상자 전체가 불가능함을 증명하지 못함 | 해당 없음 | 유지 | 아님(봉인 fail-closed) |
| P2-48 | hc:85 | 출발 단계에서 전도하지 않는 미선언 MOS는 기록만(봉인 9가 거부) | B | O-55 U1 | 해당 없음 | 유지 | 아님 |
| P2-49 | hc:385(SD-3), :425(R3-d), :126 | 관측 항목·지켜지는 소자 없음은 기록만 | B | Z가 X의 동작 조건이 아님 | 해당 없음 | 유지 | 아님 |
| P2-50 | op:278 | MC A·B 공통 성분은 기록만 | B | 판정 = 있음/없음·비트 동일 | 해당 없음 | 유지 | 아님 |
| P2-51 | op:475, :484, :624 | 네이티브 MC 연속 칸은 동일성 판정에서 빼고 차·표준오차만 기록(크기 판정 = TR-7) | B | 표본열이 달라 비트 동일이 정의되지 않음, O-2 | 해당 없음 | 유지 | 아님 |
| P2-52 | op:485 | A_dc 정의 불능 갈래가 발동한 회로의 σ·V_id* 칸은 비트 동일 예외 | B | O-61 P7, O-62 (3) | 해당 없음 | 유지 | 아님 |
| P2-53 | gc:270, :276 | 사본 규칙 L-4의 '출력 함수 면제'(엔진 reader 0, 보고 경로에만 도달) | B | N3.1-2 정의 | 해당 없음 | 유지 | 아님 |
| P2-54 | op:573, :620 | 옛 LUT 생성기를 실행 경로 없는 출처 보존본으로 남김('옛 코드 삭제' 원칙의 예외) | B | 엔진 선언 출처 sha256이 묶여 있음, X-10·D-2 승인(O-1), 실행 경로 0을 grep 측정 | 해당 없음 | 유지 | 아님 |
| P2-55 | os:27 | 사용자가 결정한 값과 fixture 지정은 상수 발명 금지의 예외(출처 병기) | B | 사용자 지정 | 해당 없음 | 유지 | 아님 |
| P2-60 | gc:394, :555(K-h), :808(B-G3) | 비레일 g = s는 정지, 레일 g = s는 `fixed_vgs`로 허용하는 비대칭 | C | 계획 스스로 "물리 근거 없음(P-1, 보존만)" | 없음(백로그 B-G3뿐) | 남음 | 아님(비레일 쪽은 정지) |
| P2-61 | op:99(NFR-P2), :626(X-D1), :433, :604 | '출처 미확인 기존 상수' 5개(`NYQUIST_K_MAX`·`NOISE_TOP_K_MAX`·`INTEGRAL_K_MAX`·`ZOOM_POINTS`·`ZOOM_ROUNDS`)의 값·동작을 그대로 옮김 | C | X-D1 수용(O-3) "출처 확인 없이"; "출처 유도는 백로그" | 없음(백로그) | 남음 | 아님(확신도 중간) |
| P2-62 | gb:273(DEC-74), :1583, :1688, :2446(U-108); os:133, :211, :303, :390, :444, :561; ot:279, :311 | DEC-74 'front 전용 예외': 계통 offset을 커널 판정에서 뺌(근거 'θ 봉인점에서 구조적으로 0') | C(근거 오류) | O-118 1번: 근거가 오류; U-108 확정(O-119) = 커널 + front 재판정 | 있음: U-108 / DE-1 (c) | gain-budget은 해소. **os·ot는 옛 예외를 그대로 인용**(U-108·O-118·O-119 언급 0건; os:561 "ΔW 없으면 0이라 통과로만 나온다") | ⚠ 문서 잔존: 하위 계획을 따르면 성분 (1)(2)를 커널에서 판정하지 않음 |
| P2-63 | op:119, :348 | 차동 이득 판정 상수 `1e-3`(출처 미확인)을 예외로 유지(D-c) | C | O-6 D-c | 있음: O-43 D1 (d) `.tf` 직접 측정 | **해소**(예외 목록에서 빠짐) | -- |
| P2-64 | gc:454, :468, :469, :779 | 선택 후보가 모두 전류 충돌이면 빈 사다리 -> 상자 중심에서 출발해 탐색 계속(정지하지 않음) | D(확신도 낮음) | O-13 (가), "출발 단계는 판정 단계가 아님" | 있음: GC card | 남음(`layer0_center.py:654-656` `_box_centre`) | ⚠(확신도 낮음): θ 기저 원칙 O-127이 '상자 중심 자리값'을 결함(B80·B81)이라 함 -- 충돌 여부 재검토 필요 |
| P2-70 | gb:1762(DT-1 (6)) | 순수 리팩터링 card인데 domain 칸 하나만 변화표로 판정 | D | v6.19 3차 감사 N6 | 해당 없음 | 계획 | 아님 |
| P2-71 | gb:2038; N6.3 (iii) | DE-1·LA-1은 EO-1을 병합 선행으로 둠(일반 규칙은 완료 판정 선행) | D | O-126, 검증 m2 | 해당 없음 | 계획 | 아님 |
| P2-72 | gb:1263 | 층 0은 DC 범위 필드를 READS하지 않는데, R6가 DE-1 (e)를 READS하는 예외 | D | O-159 E-1 | 해당 없음 | 계획 | 아님 |
| P2-73 | gb:1327, :2414(U-76 (1)) | A' 완료에서 회로별 예외는 그 회로의 대조표 + 사용자 결정으로만 | D | WP-02, `criteria_weakened` | 해당 없음 | 규칙 | 아님(기본은 fail-closed) |
| P2-74 | gb:1889 | 봉인점이 없는 B81 회로는 front ≥ 1 조건에서 빼고 따로 보고 | D | O-143 (1) | 있음: B81 백로그 | 남음 | 아님(통과로 세지 않음) |
| P2-75 | gb:1544(X-IT12) | 같은 이름 `dc_window_def_refined`에 다른 기준을 싣는 예외 | D | O-49 P5 | O-109 C1으로 대상 소멸 | **해소** | -- |
| P2-76 | gb:1353; op:468, :642, :643, :783 | ICMR(X-29)·swing(X-32) 정의를 전환한 칸에 card별 예외 승인 | D | O-34 (1) 규칙으로 대체 | 있음: O-34 '정의를 바꾼 칸 = 동작 변경 기준' | **해소** | -- |
| P2-77 | op:487 | 측정 결과를 담은 옆 선언은 검증자가 써서 저장소에 둠(작성자≠검증자의 예외) | D | v0.6.3.1, OP-7 선례 | 해당 없음 | 유지 | 아님 |
| P2-78 | op:551, :156, :625 | 완료 조건 8a '엔진 무변경'의 예외: `E/tests/`에 선언만 읽는 test 추가, glob 한 줄 변경 | D | X-13, DV-4 (가) | 해당 없음 | 유지 | 아님 |
| P2-79 | gb:2389(U-51) | 보상 단 θ의 계수 기반 폴백(SLSQP가 maxiter 안에 수렴 못 하면 GB5 규칙값으로 고정하고 다시 풂, '추정' 표기·기록) | D | 사용자 결정 2026-10-12 | 해당 없음 | 엔진 미구현(`compensation_fixed_fallback` 0건) | 아님(기록·추정 표기) |
| P2-80 | gb:2454(U-117) | F 소자 = 층 0 격자 폴백 축 | D | O-141 (7) 미결 | 미결 | 남음 | 확인 못 함 |
| P2-81 | os:41, ot:735 | 핵심 층 재작성 금지의 예외(N5 승인 항목) / DEC-96 (3)에 'T-29 범위 판정' 예외를 더함 | D | X-17 | 해당 없음 | 계획 | 아님 |
| P2-82 | os:409, :609, :479 | M2 측정용 spec을 저장소 밖 임시 경로에 둠(library 무변경) | D | DO-8 | 해당 없음 | 절차 | 아님 |
| P2-83 | verilog-rtl-debugger:51, :228; verilog-tb-analyst:230, :241 | agent가 없을 때 Claude가 직접 수행하는 폴백을 영구 유지('임시 대체 아님') | D | v0.3 정정 | 해당 없음(gmid 엔진 무관) | 유지 | 아님 |

#### 분류별 수(행 = 묶은 예외 하나)

| 분류 | 수 | 해소 | 남음/계획 | ⚠ |
|---|---|---|---|---|
| A | 21 (P2-01~21) | 1 (P2-09) | 20 | 8 (P2-05·06·07·08·10·11·12·19 -- 확신도 낮음 P2-18 포함 시 9) |
| B | 26 (P2-30~55) | -- | 정당 예외 유지 | 0 |
| C | 4 (P2-60~63) | 1 (P2-63) + gain-budget 쪽 P2-62 | 2.5 (P2-60, P2-61, os·ot에 남은 P2-62) | 1 (P2-62 문서 잔존) |
| D | 15 (P2-64, P2-70~83) | 2 (P2-75, P2-76) | 13 | 1 (P2-64, 확신도 낮음) |
| 합계 | 66 | 4 | -- | 10~11 |

A 비율: 66건 중 21건(32 %). 엔진·design 반영 대기를 이유로 든 예외(A)만 놓고 보면, A 21건 가운데 20건은 대체 card가 실제로 있다. AP-1(P2-02)은 card가 있지만 '미래 card'이고 착수 조건이 계획 개정이다(정본 자리 없음).
B·D는 대부분 물리·측정 구성·절차 이유이고 '미구현'을 이유로 들지 않는다.

**A인데 대체 card가 없는 것**: 없음. 대체 card가 사실상 비어 있는 것은 P2-02 AP-1(미래 card, 계획 개정 필요) 하나.

**C 목록**: P2-60 K-h(물리 근거 없음·보존만, 백로그만), P2-61 X-D1 출처 미확인 상수 5개(백로그만), P2-62 DEC-74 front 전용 예외(근거 오류, gain-budget은 해소, os·ot는 잔존), P2-63 `1e-3`(해소).

#### 버린 hit
- 범위 안 grep 줄: gain-budget 1200행 이상 166줄 + 나머지 계획 217줄 = **383줄**.
- 표에 매핑한 줄은 약 125줄. **버린 줄은 약 258줄**이다:
  - '정본 우회 재계산'의 '우회'
  - fail-closed 정지 문언(DEC-76 다중 입력 뿌리 '미구현(발동 0) -> 정지' gb:1496·1521·1551, os:240·242·465·484·664 trim·compare 미구현 거부, NFR-G6·NFR-H6 등)
  - '보류를 통과로 세지 않는다' 규칙 문장
  - 역사 서술(history 인용·옛 판 문언)
  - 결정 대기 항목(U-47·U-115 '보류' = 사용자 미결정)
  - '대상 없음'이 결정 소멸을 뜻하는 경우
  - 폐기된 design 목록(gb:2516-2526)
  - verilog 계획의 일반 'fallback' 단어
- 제외 근거: 브리핑의 'fail-closed 정지 자체는 예외가 아니다'.
- 참고: DEC-76 다중 입력 뿌리 정지는 '미구현이라 정지'다. 정지라서 제외했지만 대체 card가 없다(안전망을 영구로 둠).

#### 재현 명령
```
S=<scratchpad>/exc; F=/c/Users/HSLEE/Documents/Todoc/fpga
### 후보 줄 (scan.py DOC 정규식: 예외|생략|건너뜀|건너뛴|폴백|fallback|임시|미구현|당분간|as-built 유지|as-built|정의 불능|기록만|unmeasured|표지만|보류|우회|skip)
python scan.py doc $F/chip-design-skills/docs/01-plan/features $S/plan_master.txt .plan.md
awk -F: '$1=="gain-budget-gmid-sizing.plan.md" && $2>=1200' $S/plan_master.txt | wc -l      # 166
grep -v '^gain-budget' $S/plan_master.txt | wc -l                                               # 217
### 강한 키워드 문맥
grep -n '예외\|폴백\|fallback\|임시\|미구현\|기록만\|unmeasured\|면제\|건너\|통과로\|생략\|표지만\|보류' <plan>.plan.md
grep -n '근거 없음' graph-consumption.plan.md headroom-chain.plan.md
grep -n 'U-108\|O-118\|O-119' offset-strategy.plan.md offset-trim.plan.md     # 0건 -> P2-62 잔존
### 엔진 상태(wt/integ-it12 d759838a, tests 제외)
git -C $F/wt/integ-it12 grep -n -E 'input_tie|anchors\[-1\]|_box_centre|search_method|oracle_judged|compensation_fixed_fallback' -- skills/analog-gmid-design/gmid_engine ':!skills/analog-gmid-design/gmid_engine/tests'
sed -n 376,392p .../search/start_intervals.py; sed -n 64,70p .../search/iv_area.py; git grep -n continue .../search/iv_currents.py
```

## 부록 3. design 40-engine

### part3 -- design 40-engine 예외 전수 (fork 3)

- 대상: `wt/design-v115/docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` (design v1.15.1, HEAD 17d11bdc, 2337행·644 KB)
- 계획 대조: master `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` (9d153f2f)
- 엔진 상태 대조: `wt/integ-it12/skills/analog-gmid-design/gmid_engine` (d759838a, tests 제외), oracle은 `tools/spice_oracle`
- 1~82행(머리 변경 이력)은 역사 서술이라 제외. 83행부터 절(clause) 단위로 추출.

#### 재현 명령
```
### 절 단위 후보 추출(83행부터, 문장/표 칸으로 쪼갬)
python scratchpad/exc/clauses3.py <40-engine.design.md> > p3_clauses.txt   # 165 절
###   regex: 예외|생략|건너뜀|건너뛴|건너뛰|폴백|fallback|임시|미구현|당분간|as-built 유지|정의 불능|기록만|unmeasured|표지만|보류|우회|\bskip|면제|N/A|통과로|통과시|정지 대신|정지하지 않|멈추지 않|무시|경고만|느슨|완화
### 별도 정독: §8(1866-1918, 축소 표 R1~R33), §9(1920-2035), §3.10.8~3.10.11(1569-1637), §2.4.1·2.4.10(198-222, 654-682)
### 엔진 상태(1회 grep, tests 제외):
grep -rlE "<패턴>" gmid_engine --include=*.py | grep -v /tests/
###   패턴: pending_wiring W_adjustable not_computed counted_rails_undeclared _wire_sweep_memo compensation_fixed_fallback
###         record_only output_range oracle_judged relaxation_decision fallbacks passive_value_undeclared _budget_stop
```
`as-built` 단어는 169회 -- 대부분 현황 서술이라 예외 항목으로 세지 않음(아래 표에 예외로 쓰인 것만).

#### 전수 표

| key | 위치(40-engine:행) | 내용 한 줄 | 분류 | 근거 | 대체 card/규칙 | 상태(엔진 d759838a) | fail-open ⚠ |
|---|---|---|---|---|---|---|---|
| D40-01 | 213·241·700 | LUT 파생표 디스크 캐시를 실행 사이 유지 -- '처음 실행은 항상 계산' 취지의 **예외**로 기록 | D(사용자 승인 정책 예외) | U-87, 사용자 2026-10-15 "LUT는 관리복잡도가 없다", 계획 N3.3 승인 예외 | 없음(영구 승인) | 남음(`lut/table_cache.py`) | 아니오 |
| D40-02 | 208-215·654-661·1312·1340·1342 | graph 밖 허용 셋(LUT memo·S3 색인·실행 계수) + G-8 허용 모듈 목록, DC 블록 슬라이스 키를 memo 키 성분으로 | D(승인 구조 예외) | 결정 G-1·G-2', N3.3 승인 예외, CLAUDE.md graph 규칙 2 | -- | 남음(승인) | 아니오 |
| D40-03 | 444·449-461·852·882 | `_wire_sweep_memo`가 임시 컨텍스트에서 첫 평가를 돌리고 버림(상한 재기용 우회) | A | as-built f23aec8 결함, XRUN-F1 card A가 삭제 | XRUN-F1 card A | **해소**(`search/search_context.py:132` 임시 평가 없음, `lut/sweep_memo.py` 없음) | -- |
| D40-04 | 560 | 용량만 결측이어도 `metrics_aux`·`metrics_ss`가 결측 전체를 막아 모든 metric 정의 불능 -- IT-2d B77에서 해소 | A | 계획 v6.34.2 O-111·O-112, '카드 IT-2d B77에서 해소' | card IT-2d(B77) | **남음**(`metrics/metrics_aux.py:164` 결측 하나면 전 요청 `passive_value_undeclared`) | 아니오(정의 불능 쪽) |
| D40-05 | 800 | `l_bin_search`가 예산 확인을 단락 평가로 건너뛰고 `wall_budget` 정지를 `converged`로 남김 | A | as-built 결함, 설계 NFR-4 정지 사유 수정 | §2.4.13 l_search 정지 사유 | **해소**(`search/l_bin_search.py:47` `_budget_stop`) | -- |
| D40-06 | 801 | 규칙 H 짝·고아 검사에서 `tests/` 바로 아래 파일(conftest) 제외 | D | 구조 검사기 정의역(경로 성분 1개) | -- | 남음 | 아니오 |
| D40-07 | 806 | 결정성 변화 중 'strict xfail 제거·형식 변경'은 승인 불필요(기록만) | D(절차) | 기준 강화 방향이라 승인 면제 | -- | 남음 | 아니오 |
| D40-08 | 1029 | `supply_current_dc` 제약 + `counted_rails` 미선언 -- **as-built는 `not_computed`로 지나감(red)**, design은 실행 전 보류 정지 | A | 계획 v6.38.2 DEC-105 (9), card SF-1 범위 8, 사용자 N12 | card SF-1 범위 8 | **남음**(`search/find_front.py:103` 항상 `not_computed` note, `search/objectives.py:10` '쓰지 않는다') | **⚠ fail-open**(선언된 판정 제약이 조용히 미판정) |
| D40-09 | 1019 | 출력 범위 `undeclared`이면 R8·R10 (i) 요구 행을 두지 않고 범위 끝 양은 정의 불능 | B | O-154 Q1(선언이 없으면 요구도 없음 -- 미측정 거부 아님), 키 누락은 거부(O-157 S8) | card SF-1·DE-1·SB-1 | 엔진 미구현(`output_range` 0건) | 아니오(표지는 명시) |
| D40-10 | 1035·1910 | current_reuse는 AP-1까지 정착(·슬루) **판정 대기** | A | 'AP-1까지 판정 대기', AP-1 = 미래 card(계획 N6.22) | card AP-1(미래) | 남음 | **⚠**(선언 spec이 판정 없이 대기 -- 미래 card라 기한 없음) |
| D40-11 | 1409·2186·2199 | 슬루·정착은 엔진 값 없음 → `unmeasured_front`(사유 `oracle_judged`) → oracle 판정 | D | DEC-98 (6), O-124, O-122(원래 취지와 다름 승인), O-145 | card SF-1 범위 6(b), VB-1 | 엔진 미구현(`oracle_judged` 0건) | 아니오(front 밖으로 보냄) |
| D40-12 | 1216 | 소자 제거 극한에서 정의가 사라지는 metric은 그 손실 행에서만 뺌 | B | 물리: 감지 넷이 DC로 뜨면 PM·GBW 미정 | -- | -- | 아니오 |
| D40-13 | 1239·1588·1617 | 보상 단 폴백(SLSQP maxiter 미수렴 시 보상 θ를 GB5 규칙값으로 고정해 재풀이, '추정' 표시) | D | U-51 사용자 결정 "(나)로"(2026-10-12) | -- | 엔진 미구현(`compensation_fixed_fallback` 0건) | 아니오('추정'·기록) |
| D40-14 | 1462·1513-1517·1904(R21)·2279 | LY5 `W_adjustable=False` 즉시 완화 | A | as-built `layout/CONTRACT.md:217,306-311` 축소, 계획 LY5 마지막 문장 | §3.10.2 P-3, U12 | **해소**(`convergence/relaxation.py` "즉시 완화하지 않는다") | -- |
| D40-15 | 1895(R12) | MOD8 루프·LY7 재평가·판정 축 재필터 미구현(`pending_wiring`) | A | as-built `layout/CONTRACT.md` 4.14, 계획 DEC-79 (b)·LY7 | §3.9 U14 | **부분**(convergence 패키지 있음, `layout/contract_output.py:16` 재검증 상태는 늘 `pending_wiring` -- 소비가 끝까지 배선됐는지 미확인) | 확인 필요 |
| D40-16 | 1174·1908(R25) | LUT FC 위반 칸 **사유 기록 없는 선형 폴백**, VS 축 선형 | A | as-built `lut/CONTRACT.md`, 계획 DEC-87 | R25 복원(VS Hermite·사유 기록) | **부분 해소**(`lut/point_query.py:10` 폴백 사유 `OpPoint.fallbacks` 기록, VS Hermite r7 구현; 폴백 자체는 DEC-87 정책으로 남음) | 아니오(기록됨) |
| D40-17 | 1564·1877(R7) | `rule_branch_coverage.json` 안 만듦, `기록만` 분기 유지 | D(축소 유지 승인) | 사용자 2026-10-08 Q1, DEC-59 안전망 | -- | 남음(`graph/loop_classify.py:18` record_only는 항상 DEC-59 정지) | 아니오(정지) |
| D40-18 | 1669·1699·1964(R19·Q10) | oracle이 `pm_undefined`를 일괄 INCOMPLETE; 결정 A('RHP=불안정')를 oracle에서 완화 | A(as-built 이탈) + D(완화는 Q10 승인) | as-built `[ng-cmfb-pm]`, 사용자 Q10/U-58 | §4-5~7 | **해소**(`tools/spice_oracle/oracle_compare.py:396` Nyquist Z·과도 판정) | 아니오 |
| D40-19 | 1898(R18)·1918(R33) | 지속 진동을 undetermined로 둔 계약에 '사용자 승인'이라 적음(실제 결정 4번은 unstable) | **C** | as-built 계약이 결정과 모순되는 승인을 주장(근거 없음) | R33 되돌림 | design 해소(엔진·oracle 재확인 안 함) | 당시 ⚠(불안정을 미정으로) |
| D40-20 | 1488·1529 | DEC-80 (ii) 면적 모델 오차 선언 전까지 탐색축 대 판정축 차를 **기록만**, `review_needed` 승격 안 함 | A | 선언값 부재(DEC-80 (ii)), 모델 오차 측정 card ME-1 | card ME-1(N6.19) | 남음 | ⚠(약: 차가 커도 판정 없음) |
| D40-21 | 1554 | ME_k 미측정이면 제약 여유 판정 '보류'(통과·실패 아님) | A | DEC-72 모델 오차 측정 미실행 | card ME-1(7a) | 남음(`search/find_front.py:81` `judgment_pending model_error_unmeasured_front_estimated`) | 아니오(통과로 세지 않음) |
| D40-22 | 1915·1931·1952-1953·1970(R32·Q5b) | gain·rout 제약 없는 회로는 층 0 끄고 '성능 판정 보류'로 탐색(folded·common_gate) | D | 사용자 U-56(Q5b), spec 값 부재 | spec 값 추가 시 소멸 | 남음 | 아니오(보류 표지) |
| D40-23 | 1878·1918(R31) | U-24 정지에서 포트쌍 CM 루프 뷰를 빼고 보고+경고 | D(design 이탈, 사용자 수용) | design이 두 결정 충돌 해소로 만듦 → 사용자 2026-10-08 수용 | -- | 남음 | 경고로 진행(승인됨) |
| D40-24 | 2002·2267 | 파일럿 CMFB 루프 뷰에서만 Vbias2 교류접지(J1 예외), `ac_ground_view` 뷰 한정 예외 | B | J 공동분석 사용자 결정(2026-10-08), 뷰별 교류접지 물리 | -- | 남음 | 아니오 |
| D40-25 | 2001 | 복합 diode 규칙 D1 -- N3.2-2 (나) 보류 | D | J12-h 결정 | -- | 남음 | 아니오 |
| D40-26 | 1592·1612·1630·3.10.8(R28) | 정밀 경로·bisection 기본 비활성, 정밀 경로 선언 시 `unsupported_rule_branch` 정지 | D(계획 승인) | DEC-73·75·76, U-66 (가) | card PR-1(정지) | 남음(정지=fail-closed) | 아니오 |
| D40-27 | 1750·1757·1784·2078·2079 | 비 diff_pair 궤도 불일치·규칙 전 측정값은 crosstab에 **기록만** | D(진단) | 사용자 2026-10-12 "3번 권고대로" | -- | 남음(`graph/orbit_matching_crosstab.py`) | 아니오 |
| D40-28 | 1841 | `[ng-area-budget]`이 임의 양수 상수 곱으로 면적 예산 우회 | **C**(as-built) | 근거 없는 상수(상수 발명) | §7.1 규칙으로 대체 | 해소(design 대체; 엔진 `search/find_front.py:88-100` S-3b 면적 예산 경로) | -- |
| D40-29 | 1856 | LUT 정리 시 사용 중·링크·폴더 밖 파일 건너뜀 | B(안전) | 사용자 2026-10-08 | -- | 남음 | 아니오 |
| D40-30 | 3.10.8 TS7 | 계약 test를 `xfail(strict=True)`로 시작 | D | P N3.11 | 담당 단위 완료 시 제거 | 남음 | 아니오(strict) |
| D40-31 | 1013·1406·1684·1687-1689·1429 | 정의역 밖(출력 범위 미선언·follower 범위 밖 계단·잡음 부분집합 누락·창 결측)은 정의 불능 → INCOMPLETE/front 제외 | B | O-145·O-157 S1 (3)·O-128 Q5, 측정 구성 정의역 | -- | 일부 미구현(SF-1) | 아니오(fail-closed) |
| D40-32 | 1690 | 슬루 계단 규칙 O-119의 예외: 구성·계단은 spec 항목 `tran.config/step` | D | O-131 원문 구성 규칙 | -- | 미구현(SF-1) | 아니오 |
| D40-33 | 1880-1912(§8 R2~R6, R8~R11, R13~R17, R20, R22, R23, R26 -- 21행) + R1 | as-built ROADMAP·CONTRACT가 계획 요구(GB3·GB4 DOF·SP1·블록 국소 모델·n_starts·L 동치류·미러 전류 강제·ΔA_tie 등)를 '범위 밖·연기'로 축소 | A | 출처 열이 as-built 문서(R §0.2 D18 등), 사용자 2026-10-08 '복원' 결정 | 각 행 '복원' → §3.x·41 §x | 개별 미확인(예: R20 `layout/floorplan.py:71` grid*grid 아직 있음 -- 다른 용도인지 미확인) | ⚠ 가능(행별 상태 미확인) |
| D40-34 | 207(§2.4.1 단계 B 층) | `residual_probe`·`dof_numeric` 블록 배선을 U17 ②로 연기(동작 변경 회피) | A | v1.9.1 D5 '근거: 동작 변경 회피' | U17 ② | 확인 필요(`search/residual_probe.py` 있음, 층 0 소비 미확인) | 아니오 |

#### 분류별 수 (34항목)
| 분류 | 수 | 비율 |
|---|---|---|
| A (계획 있음·엔진/as-built 미반영으로 둔 것) | 13 (D40-03,04,05,08,10,14,15,16,18,20,21,33,34) | 38 % |
| B (원칙·물리 정당) | 5 (09,12,24,29,31) | 15 % |
| C (근거 없음·as-built 정당화) | 2 (19,28) | 6 % |
| D (사용자 승인 정책·진단 기록·절차) | 14 (01,02,06,07,11,13,17,22,23,25,26,27,30,32) | 41 % |

- A 13 중 해소 4(03,05,14,18), 부분 2(15,16), 남음 5(04,08,10,20,21), 확인 필요 2(33,34).
- 버린 후보: 절 165개 중 약 95개(Python 예외 전파 설명 -- `ValueError`·`FailureRecord` 재연·계수, fail-closed 정지·거부, '예외 없음' 부정문, 비지배 필터 '통과', 역사 서술). 1~82행 머리 이력 hit 약 90은 통째 제외.
- 이 파일 범위 판단: design 40은 A 항목 대부분을 '복원/삭제' 대상으로 적고 있어 design 층에서 새로 만든 A형 예외는 거의 없다. A의 출처는 거의 전부 as-built CONTRACT·ROADMAP(엔진 작성자 축소)이다.

#### ⚠ 핵심
1. D40-08 `counted_rails` 미선언 + `supply_current_dc` 제약 → 엔진이 `not_computed`로 통과(fail-open, card SF-1 범위 8 미병합).
2. D40-10 current_reuse 정착 판정 AP-1(미래 card)까지 대기 -- 기한 없는 판정 공백.
3. D40-20 면적 모델 오차 선언 전 '기록만'(review_needed 승격 없음).
4. D40-33 §8 '복원' 21행의 엔진 상태가 행별로 미확인.
5. (범위 밖 메모) 엔진 `search/macro_poles.py:143-144` 영점 상쇄 R `zc_fallback` = θ 상자 기하 중점 -- design 40에는 없고 계획 DEC-24 'θ 폴백'과도 다른 상자 중심 자리값(O-127 '상자 중심 자리값으로 종속 양을 정하면 결함' 저촉 후보). 엔진 층 fork가 확인할 것.

## 부록 4. design 나머지

### part4 -- design 문서(40-engine 제외) 예외 전수

- 대상: `wt/design-v115/docs/02-design/features/` HEAD `17d11bdc` (v1.15.1). 40-engine 제외. design.history는 근거로만 읽음.
- 계획 대조: master `9d153f2f` `docs/01-plan/features/*.plan.md` (N2.1·N5.3·N6). 엔진 상태: `wt/integ-it12` HEAD `d759838a` (tests 제외, grep 한 번씩).
- 판정 기준: 규칙 적용을 끄거나 우회하는 것만 항목화. fail-closed 정지·`정의 불능`→metric 거부·front 제외는 예외가 아님(버림). 같은 예외가 여러 줄에 반복되면 한 항목.

#### 재현 명령

```
cd wt/design-v115/docs/02-design/features
### 1차 후보(41 + 기타 문서)
python -c "import re;rx=re.compile(r'예외|생략|건너뜀|건너뛴|폴백|fallback|임시|미구현|당분간|as-built 유지|기록만|표지만|보류|우회|skip|면제|N/A|통과로|정지 대신|waive|exempt|대체값|unmeasured|정의 불능|as-built')
for f in FILES: [print(f,i,l[:300]) for i,l in enumerate(open(f,encoding='utf-8'),1) if rx.search(l)]"
### 엔진 상태
cd wt/integ-it12/skills/analog-gmid-design/gmid_engine
grep -rn --include=*.py -e <code> . | grep -v '^./tests/'   # code = model_error_ref, layer0_budget, domain.ties, kvl_fixed,
   # cm_loop_unconstrained, compensation_fixed_fallback, macro_root_missing, icm_config, dc_window_cfg, lut_hermite_nonmonotone_cell ...
sed -n 140,160p search/iv_currents.py   # LA-1 범위 13 '건너뜀'
```

#### 후보 hit 수와 버린 수

| 문서 | grep hit 줄 | 항목화 | 버림(단어 일치·fail-closed·이력 문장·폐기 대안·Python 예외 클래스 등) |
|---|---|---|---|
| 41-gain-budget | 192 | 26 | 166 |
| 42-gap-checklist | 41 | 4 (41과 중복 3은 병합) | 37 |
| 00/05/10/20/30 (역할 분리·test 분리·삭제·모듈 분할) | 113 | 6 | 107 |
| oracle-portability | 122 | 9 | 113 |
| offset-strategy | 30 | 5 | 25 |
| offset-trim | 21 | 2 | 19 |
| analog-topology / verilog-* (5개) | 23 | 1 | 22 |
| 계 | ~542 | 55 | ~487 |

#### 전수 표

##### gain-budget 41 (엔진 설계 본문)

| key | 위치(파일:행) | 내용 한 줄 | 분류 | 근거 | 대체 card/규칙 | 상태 | fail-open ⚠ |
|---|---|---|---|---|---|---|---|
| G41-01 | 41:87, 692, 788-789, 1997, 2056 (42:241 D-Q5) | 모델 오차·r̂·분해능 미측정 값은 '보류'. 거부·정지 안 하고 산출물에 '추정' 표지. `model_error_ref` = None → 보고 '보류' | A | DEC-72·77. 7a SPICE 대조(ME-1) 전이라서 둔 것으로 명시 | 있음: ME-1(N6.19), PW-1b, EO-1 | 남음. 엔진 `metrics/verified_by.py`에 칸은 있으나 값 생산자(ME-1)는 없음 | ⚠ (표지만 남기고 진행) |
| G41-02 | 41:818, offset-s:652·681 | SPICE oracle 대조 다리 '보류' -- 채울 card EO-1, 그 뒤 OP-5·OS-V | A | 계획 N6.3 (i), EO-1 미구현을 이유로 듦 | 있음: EO-1(N6.20), OP-5, OS-V | 남음 | ⚠ (검증 공백) |
| G41-03 | 41:862 (17행 D-13, 1135) | 층 0 E10 규칙 '미구현' -- as-built 층 0은 최소형 | A | 계획 DEC-71 상태 칸 '미구현 -- card LA-1 F-LA1', B80 증거 | 있음: LA-1(N6.14) | 남음(`layer0_budget` 호출 1곳, E10 없음) | -- (빠진 기능, 우회 아님) |
| G41-04 | 41:1723 | `iv_currents.py:149-151`의 '미지 원소 ≠ 1이면 건너뜀'을 LA-1 범위 13에서 삭제 | A | DEC-104 R3, O-151 U5·U6 | 있음: LA-1 범위 13 | 남음 -- 엔진 `search/iv_currents.py` `if len(unknown) != 1: continue` 그대로 | ⚠ (조용한 skip) |
| G41-05 | 41:937 | F 둘 이상 고리 처리 '미결 U-117' -- 그때까지 F 격자 폴백 축에서 위반 기록과 함께 버림 | A | U-117, O-141 (7) 'LA-1 design 착수 때 재측정 뒤 결정' | 있음: LA-1 design | 남음 | -- (버림 = fail-closed) |
| G41-06 | 41:672, 699, 1777, 1819 | `domain.ties` y 묶음·뿌리별 포화 창 '미구현(발동 0)', 그 경우 정지 | A | DEC-76 '발동 0 폴백·분기는 구현하지 않음', O-13 (2) | 조건부: N6.5 범위 4(발동 회로가 들어오면) | 남음(정지 경로) | -- (정지) |
| G41-07 | 41:740 (17행 S-B) | 용량만 결측이어도 metric 모두 정의 불능 -- '원래 취지와 다름(작음)', IT-2d에서 해소 | A | B77, O-111·O-112. card 경계 때문에 생긴 과잉 거부 | 있음: IT-2d | design만 존재. 엔진에 `icm_config`·`dc_window_cfg` 0건 -> IT-2c/2d 미병합 | -- (과잉 거부) |
| G41-08 | 41:722 (17행 G7) | 출력 넷이 F′ 안인 경우 = 계획 O-64 (1) 공백 -- as-built `"kvl_fixed"`를 그대로 씀, 공동분석 대기 | C | 계획 규칙 없음. design은 '공백'이라 적고 as-built 동작을 잠정 유지 | 없음(공동분석 대기, card 없음) | 남음: `sizing/writer_plan.py:124`, `s2_values.py:115` | ⚠ |
| G41-09 | 41:1493 | 비기준 슬라이스 L bin 보간 중점 미검증 -- '중점 미검증' 표지만, WB-1 착수 때 재측정 | A | Q-DC3. WB-1(현 DE-1로 개명, v6.38.2) 착수를 이유로 듦 | 있음: WB-1 -> DE-1 | 남음(엔진에 표지 코드 0) | ⚠ (표지만, 그나마 미구현) |
| G41-10 | 41:240 | U-24 정지 대신 CM 루프 제약 미선언이면 T_cm만 보고, T_cm(0) > 1이면 경고 `cm_loop_unconstrained` | D | 사용자 결정 2026-10-08(U-24) | 해당 없음(spec 미선언 = 판정 대상 없음) | 엔진 구현(5건) | ⚠ (경고만) |
| G41-11 | 41:954, 1664 | R7 (가) 합 행 위반이 나머지 경계에서 생기면 `StartConflict` 기록만, 재개방은 R-1′ 행만 | D | 사용자 결정 O-158 (A′) ② | 해당 없음 | 엔진 `StartConflict` 32건(구현) | ⚠ (위반 기록 뒤 진행) |
| G41-12 | 41:1790 | 범위 끝 이득 행은 자르지 않고 '이득 행 재개방' 표지만 R6 필드에 둠, 탐색 개방은 층 0 | D | O-159 E-3, O-160 F-3 | 층 0(LA-1)이 소비 | 소비자(층 0)가 아직 없음 | ⚠ (소비자 없는 표지) |
| G41-13 | 41:1715 | 매크로 1-D 근 모두 없음 -> 상자 기하 중심 대체값 + '추정' | D | 계획 v6.38 후속 정정 '41 §6.5', 감사 §2.5(θ 독립 성분이라 θ 기저 위반 아님) | 해당 없음 | 엔진(`search/macro_poles.py:17`)은 '출발점 사용 + `macro_root_missing` 보고만' -- design과 다름(gap) | ⚠ (대체값으로 진행) |
| G41-14 | 41:1458 (PQ2) | N_T,i 초과는 정지 대신 절단 + '추정' | D | DEC-76, 사용자 결정 PQ2 | 해당 없음 | -- | ⚠ (부분 탐색) |
| G41-15 | 41:872 (869) | 층 0 국소 문제가 자명해(AC 제약 없음)지면 층 0을 끄고 '성능 판정 보류'로 보고, 회로를 빼지 않음 | D | 사용자 결정 Q5b(DEC-71 (3) '사이징 대상에서 뺀다' 대신) | 해당 없음 | 엔진 `performance_judgement_deferred` 0건 | ⚠ |
| G41-16 | 41:1912 | 피드스루 없는 점이 없으면 B '미상' -> 잡음 resolution 무한대, 판정 보류 | B | 물리: 1/f 측정 정의역 밖(`no_feedthrough_free_point`) | -- | 엔진 3건 | ⚠ (보류 = 거부 아님) |
| G41-17 | 41:499 (42:126) | Fritsch–Carlson 위반 칸: 역산 실패, 순방향 조회는 선형 폴백 + 사유 기록 | B | DEC-87, 수치(단조 보간 조건 불성립) | -- | 엔진 `lut/lut_set.py:124-173` | -- |
| G41-18 | 41:939, 968, 1006, 1070, 1108, 1350 | S 역산 실패·L 역산 괄호 없음·매크로 실패 -> 그 소자/동치류만 격자 폴백 | B | DEC-71 (4) '역산은 후보 수단, 격자가 검증·폴백' -- 알고리즘 정의 | -- | 일부 구현 | -- |
| G41-19 | 41:1041 | IDu 비단조 구간·격자 전용 칸은 knee 계산에서 건너뛰고 `knee_interval_skipped` 기록 | B | 수치 정의역 밖(§7.10 반례) | -- | 엔진 코드 0건(미구현) | -- |
| G41-20 | 41:717 | `saturation_window` 영 기울기(`|rate| ≤ eps`) 건너뜀을 전도 행에도 적용 | B | 수치: 0 기울기 = 그 방향 제약 없음 | -- | 구현 | -- |
| G41-21 | 41:695, 738 (가) | 커널 창 미수렴이 KCL 측정 구성 창 metric을 정의 불능으로 만들지 않음 | B | DEC-103 프레임 원칙(설계점 질문 ≠ 섭동 질문), O-109 D2 | -- | IT-2c 미병합 | -- |
| G41-22 | 41:147, 407, 427, 1031 | 뷰 한정 교류접지 예외 J-C (ratified `ac_ground_exception`) | B | 회로 사실(바이어스 레플리카 넷), 사용자 ratify | -- | 엔진 8건 | -- |
| G41-23 | 41:935 | 버퍼 블록 출력 follower는 rout 제약으로 gm이 정해지므로 S로 봄(E10) | B | 물리(rout = 1/gm) | -- | E10 미구현(G41-03과 같음) | -- |
| G41-24 | 41:343 | `main_path_ambiguous`는 FF 후보 묶음이 있는 뷰에서만 판정 | B | 논리(FF가 없으면 주경로를 고를 이유 없음). 단 발견 경위는 as-built U1b 오발동 | -- | 엔진 2건 | -- |
| G41-25 | 41:403 | `name_order` 동률이 같은 자기동형 궤도면 review 생략 | B | 대칭(어느 쪽이든 같은 결과). 오케스트레이터 결정(사용자 결정 아님) | -- | 엔진 2건 | -- |
| G41-26 | 41:1123, 1152, 1164 | '(as-built 유지)' 표지 셋: `resolution_gate_unmet` 정지, 조립 실패 -> 다음 조합, `state_count_over_budget` 종료 | D | 표지는 as-built이나 동작은 정지/정상 탐색 | -- | `resolution_gate_unmet` 엔진 0건 | -- |
| G41-27 | 41:1668, 1930 (42:263) | tol 표 디스크 캐시 = U-87 승인 예외(graph 단일 정본 규칙의 예외) | D | U-87 사용자 승인, 계획 N3.3·N3.5 승인 예외 목록 | -- | 브랜치(PART) | -- |
| G41-28 | 41:812 | 약반전 꼬리 toy의 과보수(SPICE보다 좁음)는 단언하지 않고 기록만 | D | 백로그 I-H3(test 단언 예외) | 없음(백로그) | -- | -- |

##### gain-budget 42 (gap 표) -- 41과 겹치지 않는 것

| key | 위치 | 내용 | 분류 | 근거 | 대체 | 상태 | ⚠ |
|---|---|---|---|---|---|---|---|
| G42-01 | 42:191 (D-G4) | SLSQP maxiter 미수렴 시작점만 보상 단 GB5 고정 재풀이, `compensation_fixed_fallback` 기록·'추정' | D | 사용자 결정 U-51 | -- | 엔진 0건(MISS) | ⚠ |
| G42-02 | 42:205 | orbit 분할은 차동 입력 p/n일 때만 review, 나머지는 crosstab 기록만 | B | 대칭 정의(입력쌍만 정합 필수) | -- | MISS | -- |
| G42-03 | 42:297 (D-P6) | 면적 모델 오차 기록만 | A | DEC-72 측정 전(ME-1과 같은 계열) | ME-1 | MISS | ⚠ |
| G42-04 | 42:104 | SP1 `기록만` 분기 -> `unsupported_rule_branch` 정지는 FR-1과 함께 MISS | A | FR-1 미구현 | FR-1 | 엔진 `unsupported_rule_branch` 19건 -- 구현됨(42 표가 낡음) | -- |

##### 공통·역할·test·삭제·모듈 분할 (00/05/10/20/30)

| key | 위치 | 내용 | 분류 | 근거 | 대체 | 상태 | ⚠ |
|---|---|---|---|---|---|---|---|
| P-01 | 00:260, 10:468 | 하네스 `run()`이 모든 예외를 삼키고 0으로 끝남 = DF-37 | A | 결함으로 등재, 40-defect-fixes CC-4에서 고침 | 있음: CC-4/DF-37 | 해소로 보임(엔진 `pipeline/stage_a·b.py`가 `exit_code_for` 사용, pipeline에 `except Exception` 0) | (해소 전 ⚠) |
| P-02 | 05 전체, 00:124·289·319, 30:32·354·497 | 역할 분리 gate·V1~V10·V3 등가 변이 면제(`exempt`)·면제 묶기 | D | 계획 N3.12·N4.2·N4.3 '폐기(2026-10-07, gate 끔)' | -- | 대상 소멸(gate 끔) | 검증 gate 전체가 꺼짐(사용자 결정) |
| P-03 | 20:18·62·156·205 | 레지스트리 D 등급 '보류'(배선은 Phase 4) -- G-1 걸리는 항목은 삭제 안 하고 보류 | A | U-02 승인 '보류(Phase 3 이동·Phase 4 배선)' | Phase 4 배선 | 확인 안 함(레지스트리) | -- |
| P-04 | 20:106·113 | 재구현 oracle의 V4 `target_kind: decision` 면제 | D | 승인 `20260923-v4-decision-exempt` | -- | gate 끔으로 소멸 | -- |
| P-05 | 30:95·620·1107 | `stick_diagram` 임시 재수출, F2에서 삭제 | A | WP-14, card F2 | 있음: F2 | 새 `gmid_engine`에는 해당 파일 없음(옛 엔진) | -- |
| P-06 | 30:600·745·753 | probe 대입 줄 F1 oracle 예외, 계획 534행 '추적 파일 전부 갱신'의 예외 | D | D-17, 승인 질문(v6) | -- | 옛 엔진 단계 | -- |

##### oracle-portability

| key | 위치 | 내용 | 분류 | 근거 | 대체 | 상태 | ⚠ |
|---|---|---|---|---|---|---|---|
| O-01 | op:33, 1280, 1506, 1884 | 값 원칙의 예외: '출처 미확인 기존 상수' 다섯(`*_TOP_K_MAX`·`INTEGRAL_K_MAX`·`ZOOM_POINTS`·`ZOOM_ROUNDS`) 값·동작 그대로 이동, 유도는 백로그 | A | NFR-P2 허용 예외, O-3 X-D1. N4 동일성 유지를 위해 유도를 뒤로 미룸 | 없음(백로그 X-D1, card 없음) | 남음 | -- |
| O-02 | op:65, 1279, 1505 | 차동 이득 상대 폭 `1e-3` 예외 | A -> 해소 | O-6 D-c -> O-43 D1 (d)에서 `.tf`로 대체 | OP-5 | 해소(design 문언상 삭제) | -- |
| O-03 | op:1447-1449, 1321, 1348, 1507, 1567, 1666 | 완료 조건 8a '엔진 diff 0'의 예외 둘(X-13 test 새 파일, `test_verified_by.py:64` glob 한 줄); 엔진 주석 결함은 고치지 않고 알림 | D | 계획 v0.5.1 8a, v0.6.5 O-9 | -- | 확인 안 함 | -- |
| O-04 | op:666, 1552 | 기술자 `extra_sources` '임시안' -- '파일마다 정본 한 곳'과 D-9가 충돌, 계획 개정 뒤 확정 | D | S-7(계획 먼저) | 계획 개정 필요(card 없음) | 남음(임시) | -- |
| O-05 | op:418, 717, 1173 | 계획 N4-2a 예외: 검증자 측정 옆 선언은 검증자가 씀 | B | 작성자≠검증자 원칙 | -- | -- | -- |
| O-06 | op:1096, 1251, 1256 | MC 표본열 동일성 판정에서 제외, 차·표준오차 기록만 | B | 네이티브 MC 표본열이 기준선과 다름(X-17) | -- | -- | -- |
| O-07 | op:484, 1454 | 끝 확정 (4) 검사 면제: `end_cause` ∈ {rail, rail_filter, stage1}이고 지목 점 = 원 범위 `pass_point_id`일 때만 | B | 1단계가 이미 확정한 끝 | -- | -- | -- |
| O-08 | op:1934 | 차동 회로 σ 칸 (가-1) 비트 동일 예외는 A_dc 정의 불능 갈래 발동 회로만 | B | 승인 O-61 P7(정의 변경) | -- | -- | -- |
| O-09 | op:959, 161 | `judge.off_current_A` 없으면 문턱 0; `legacy_adapter`의 `lut_reference_width_m` 대체값(dump `W_ref_m` 없을 때) | C | 옛 코드 동작 기술, 근거 문장 없음 | 없음 | 남음(오라클·legacy) | ⚠ (대체 기본값) |
| O-10 | op:1868 | 게이트 전용 이상 전압 넷 조건이 지금 검사되지 않음(스키마는 설명문만) | C | v0.3.9 검증 N2가 사실만 기록 | 확인 못 함 | 남음 | ⚠ (검사 공백) |

##### offset-strategy / offset-trim / 기타

| key | 위치 | 내용 | 분류 | 근거 | 대체 | 상태 | ⚠ |
|---|---|---|---|---|---|---|---|
| S-01 | os:30, 117, 214, 639 | front 판정 k·σ_in + |V_id*|는 DEC-74 'front 전용 예외 자리' 하나 | B | 물리: θ 프레임 봉인점에서 V_id* = 0이라 커널에서 못 잼(DEC-74, O-43 D1 (c)) | 자리 = DE-1 (c) | 미구현(DE-1) | -- |
| S-02 | os:364, 725, 869 | 구조 규칙 M (M-c)(M-d) 예외: `plan_session.py` 같은 세션 여러 `run_stage_a`, 세션 인스턴스 속성 | D | 40이 예약한 예외, OS-5·TR-3 몫 | OS-5 | 미구현 | -- |
| S-03 | os:366, 402, 453, 687 | spec None이면 계획 없이 `run_stage_b` `skipped` 보고서(diagnostic False) | D | 하네스와 같은 출력 파일을 내기 위함, '계산 안 함' 표지 | -- | 엔진 `stage_b.py:140-142` | -- |
| S-04 | os:512 | 승인 파일 있으면 국면 2 미구현 -> `trim_phase2_not_open` | A | TR-2 국면 2 미구현 | TR-2 이후 | 정지(fail-closed) | -- |
| S-05 | ot:186, 698 | trim 미선언이면 trim 블록 호출 0, 예외 열 둘(`offset_adjoint` None, `fixed_values`) | D | design N 부류 예외 열 | -- | -- | -- |
| S-06 | ot:1001 | trim 잔여 정지의 '지금 계획의 임시 규칙' | A -> 해소 | T-39 (가)로 닫힘 | -- | 해소 | -- |
| V-01 | verilog-* 5개 | agent 미배포면 Claude가 직접 수행(FR-09 fallback), 정본 skill 부재는 BLOCKER | B | 배포 상태 원칙(gmid 엔진과 무관) | -- | -- | -- |

#### 분류별 수 (55항목)

| 분류 | 수 | 비율 | 항목 |
|---|---|---|---|
| A (계획/결정이 있는데 엔진·design에 반영되지 않아 임시) | 17 (남음 12, 해소·소멸 5) | 31 % | G41-01·02·03·04·05·06·07·09, G42-03·04, P-01·03·05, O-01·02, S-04·06. 해소·소멸 = G42-04(엔진 구현됨, 42 표가 낡음), P-01(DF-37 해소로 보임), P-05(옛 엔진), O-02, S-06 |
| B (원칙·물리 근거) | 17 | 31 % | G41-16~25, G42-02, O-05~08, S-01, V-01 |
| C (근거 없음·as-built 정당화) | 3 | 5 % | G41-08, O-09, O-10 |
| D (사용자/오케스트레이터 결정, 승인 예외, 과정) | 18 | 33 % | G41-10~15·26·27·28, G42-01, P-02·04·06, O-03·04, S-02·03·05 |

- 41 본문만 보면: A 8 / B 10 / C 1 / D 9 -- A는 3할 남짓. 엔진 설계 쪽 '예외'의 다수는 A가 아니라 B(물리 정의역·알고리즘 폴백)와 D(사용자 결정으로 정지 대신 기록·경고·추정 표지)다.
- 단, A로 분류한 것은 모두 진짜 '미구현 대기'(ME-1·EO-1·LA-1·IT-2d·DE-1 card가 실제로 있음). A 중 대체 card가 없는 것: O-01(X-D1 백로그), P-03(card 아닌 Phase 4 배선).

#### fail-open ⚠ (정지 대신 진행·통과)

1. G41-04 `iv_currents.py` 미지 원소 ≠ 1 조용한 `continue` -- LA-1 범위 13 대기, 엔진에 그대로.
2. G41-08 출력 넷 ∈ F′ 공백을 as-built `kvl_fixed`로 잠정 처리 -- 계획 규칙도 card도 없음 (C).
3. G41-01 / G42-03 모델 오차 미측정이면 거부 없이 '추정' 표지 -- ME-1 전까지 모든 판정이 이 상태.
4. G41-02 SPICE 다리 '보류' -- EO-1 전 독립 검증 없음.
5. G41-13 매크로 근 없음 -> 상자 중심 대체값: design과 엔진(출발점 + 보고만)이 다름.
6. G41-09·G41-12 소비자/코드 없는 표지(중점 미검증, 이득 행 재개방).
7. G41-10·11·14·15, G42-01 사용자 결정으로 정지 대신 경고·기록·절단·보류.
8. O-09·O-10 오라클 대체 기본값(문턱 0, W_ref)과 검사 공백 (C).

#### 범위 밖 메모

- 40-engine은 다른 fork 몫. G41-13 엔진 불일치, G41-04 `continue`는 엔진 code 층 감사와 겹친다.
- 계획 N3.12·N4.2·N4.3 역할 분리 gate 전체 '폐기(gate 끔)'는 계획 층 사항이다(P-02).

## 부록 5. code metrics·graph·search

### part5 -- 엔진 metrics/·graph/·search/ 예외 감사 (fork 5)

- 대상: `wt/integ-it12/skills/analog-gmid-design/gmid_engine/{metrics,graph,search}` (tests 제외), HEAD `d759838a`, 읽기 전용.
- 대조 계획: master `9d153f2f` `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(v6.38.2), design `wt/design-v115` `17d11bdc`.
- 작업 뒤 `git -C wt/integ-it12 status --porcelain` = 빈 출력(확인함).

#### 재현 명령 (gmid_engine 디렉터리에서)

```
grep -rnE "except\b|NotImplemented|TODO|FIXME|임시|미구현|fallback|폴백|unmeasured|\bskip|as-built|당분간|보류|우회" --include=*.py metrics graph search      # 151줄
grep -rnE "^[[:space:]]*except" --include=*.py metrics graph search                    # except 절 44개(문맥 ±4줄 전수 확인)
grep -rnE "^\s*continue\b|: continue" --include=*.py metrics graph search | wc -l     # 185
grep -rnE "return None\b" --include=*.py metrics graph search | wc -l                 # 116
grep -rnE "\.get\([^)]*, *(-?[0-9]|math\.|np\.|float)" --include=*.py metrics graph search   # 숫자 기본값 .get 40줄
git -C <wt> log -S"<기호>" -- <경로>   # 근거 커밋 찾기
```

#### 표

| key | 위치(파일:행) | 내용 한 줄 | 분류 | 근거 | 대체 card/규칙 | 상태 | fail-open |
|---|---|---|---|---|---|---|---|
| E5-01 | search/seal7_pending.py:1-40, eps_sweep.py:12-13·38, find_front.py:9-10·112-114 | 봉인 7이 VDSAT 열 부재로 미정이면 `pending_front`로 따로 두는 '임시 스위치'(파일 머리: VDSAT 접근자가 생기면 무동작·삭제 가능) | A | 머리 docstring "스위치가 꺼지는 조건 ... 이 파일은 지워도 되는 무동작 상태", 계획 DEC-88, 커밋 `30c64e11`(2026-10-08) | 대체 = lut VDSAT 접근자(`lut/vdsat_query.py`, `vdsat_tolerance.py` 이미 있음). 파일 삭제 card는 없음 | 반쯤 해소: VDSAT 열 있는 LUT에서는 발동 0, 열 없는 옛 LUT에서만 발동. 남은 docstring(find_front:9 "모든 점은 pending_front에만", constraints.py:13 "VDSAT 접근자가 없어")은 낡음 | 아님(대기 점은 최종 front 제외) |
| E5-02 | search/constraints.py:13·15 | "봉인 7 포화 여유는 VDSAT 접근자가 없어 행을 만들 수 없다", "spec 성능 제약은 MOD5 `ss_linearize`가 없어 여기서 재지 않는다" | A | 미구현 시점 docstring(커밋 `30c64e11`) | 대체됨: `metrics/ss_linearize.py`·`search/ss_constraints.py`가 있음. VDSAT 행은 아직 constraint_rows에 없음(봉인 7 판정은 sizing 봉인에서) | 문언 낡음(ss 부분 해소, 봉인 7 행 미추가) | 아님 |
| E5-03 | search/kernel.py:153 | `constraint_rows`의 `undefined`(tol_V None 소자)를 `_undefined`로 받아 버림. constraints.py:14는 "판정 보류 -- 통과로 세지 않는다"고 적음 | D | tol_V None 소자는 sizing 봉인 6(`seal_bulk_reverse.py:7` "tol_V 미정 소자는 undefined")에서 이미 보고서를 undefined로 만들어 그 점이 SEALED가 될 수 없다 -- 상류 봉인이 막음 | 해당 없음 | 남음(버리는 반환값) | 아님(상류 봉인이 막음). 단 docstring과 실제가 다름 |
| E5-04 | search/eps_sweep.py:10·84, find_front.py:11·86 | 판정 축 재필터 몫 T_refilter = 0, "MOD8 미구현이라 0(기록)", note `not_run ... layout_axis_refilter_is_mod8` | A | docstring "MOD8 미구현", 커밋 `30c64e11` | 대체 = `convergence.converge`(MOD8/U16)가 front를 받아 함. 계획 card 명시는 찾지 못함 | 남음(기록됨) | 아님(note로 드러남) |
| E5-05 | search/eval_budget.py:12·18 | `reserve_evals=0` -- "층 0 gain 예산 U15가 들어오기 전" | A | docstring "as-built 소비자 ... U15 `layer0_budget`이 들어오기 전" | 대체 = U15 `layer0_budget`(코드에 없음, grep 0). 계획 card LA-1(층 0 조립)이 층 0 예산 범위 | 남음 | 아님(예산만 넉넉해짐) |
| E5-06 | search/find_front.py:41-49 | `_e_total`: "N_T(as-built 0)", "card C가 계산 자리 하나로 정하며 이 식을 지운다" | A | docstring 문언 | 대체 = 'card C'(XRUN-F1 card C로 보임). 현 계획 N6에서 card C 행 찾지 못함 | 남음 | 아님(보고용 상한식) |
| E5-07 | search/find_front.py:36-38·101 | `_LAYER0_REFINEMENTS_OUT_OF_SCOPE`: GB3 블록 분해·GB4 블록 gain 상한표, LR5 knee, GB5 층 0 근사식을 범위 밖으로 기록 | A | 계획 DEC-71 (3)(6)·DEC-73, F-LA1 "as-built 층 0 최소형", F-LA12(B80) | card LA-1(N6.14) 범위 1~15 | 남음(LA-1 미구현) | 아님(note 기록) -- 단 B80: 8회로 front 0점의 원인 |
| E5-08 | search/start_intervals.py:22·276-282, _helpers_curves.py:105-109, iv_gain_l.py, iv_currents.py:107, macro_poles.py | 곡선 조회 동작점 = 추정점(VDS = 포화 경계·헤드룸 예산 중점 격자, VSB = 첫 VS 격자) | A | 계획 N6.9 card FX-1 '사실 (B1)~(B3)'(base `b2c72a01`) | card FX-1(출발 단계 고정점 1회) | 남음 | 아님(출발값, 판정에 안 씀 EP-7) |
| E5-09 | search/macro_poles.py:9·137-157·180-182 | 영점 상쇄 저항: 구성 소자 전류를 모르면 `zc_fallback` = θ 상자 기하 중점, 그것도 없으면 그 저항을 망에서 뺌(열림); 그 밖 engine 저항도 상자 기하 중점 고정 | C | 이유 기록은 주석 한 줄("대체값 = θ 상자 기하 중점")뿐, 계획·design에 `zc_fallback` 0건. 커밋 `bfa2f533`(U13). 상자 중심 자리값은 O-127/DEC-104가 결함 유형으로 지목(B80·B81) | 직접 대체 card 없음. 관련: LA-1 범위 13(매크로 gm의 θ 전류 전파, O-140 D8/B85) | 남음 | 아님(매크로는 출발값 전용, 판정 미사용) -- 원칙 충돌 소지 |
| E5-10 | search/macro_poles.py:203-207 | `at_target`: MNA 특이 → (|H| = 0.0, PM None) | C | 사유 기록 없음 | 없음 | 남음 | 아님(0은 목표 미달 쪽, 출발값 전용) |
| E5-11 | search/macro_poles.py:13-15·345-361 | 매크로 풀이 실패 시 `macro_root_missing`/`macro_nonconvergent` 기록만 하고 출발점 사용("둘 다 보고만, 정지 아님") | B | 매크로 = 출발값, 판정에 안 씀(EP-7, docstring) | 해당 없음 | 남음(설계 의도) | 아님 |
| E5-12 | search/iv_currents.py:19·112, macro_poles.py:6 | 용량 계수 cdrain = cdd, **없으면 cgd**로 대신함 | C | 사유 기록 없음. Cdd(≈Cgd+Cdb)를 Cgd로 대신하는 물리 근사 | 없음 | 남음 | 아님(출발값) -- 원칙상 다른 정의의 양을 대신 씀 |
| E5-13 | metrics/block_gain_model.py:20-23 | "설계와 다른 점(기록)": (1) 저항 컨덕턴스 후보에 이웃 gds 안 넣음 (2) **L bin 내부 극값 세분 미구현** (3) 기둥 VDS 독립 축(상위 집합) | C | as-built 차이를 docstring에만 기록. design 41/42·계획에 'bin 내부 극값' 0건 | UB-1(N6.15)은 U9 통합만 하고 이 세분은 범위에 없음 → 대체 card 없음 | 남음 | (2)는 인증 상한 A_i,max가 과소일 수 있음 -- 실행 가능한 점을 막는 쪽(fail-closed 쪽 오류), fail-open은 아님 |
| E5-14 | metrics/ss_linearize.py:24·39·58 | GMBS 열 없는 옛 LUT이면 `GMB_VS_CELL_SECANT` "임시 근사"(설계 MOD1 2.8) | A | 상수 주석 "설계 MOD1 2.8 임시" | 대체 = GMBS 열(lut CONTRACT r6 4.4) -- 열이 있으면 이미 정본 사용. 옛 LUT 지원 제거 card 없음 | 반쯤 해소(새 LUT은 열 사용) | 아님(`gmb_model`로 결과마다 표기) |
| E5-15 | metrics/metrics_aux.py:108-127 | VDSAT 열 없음(`lut_column_unavailable`)이면 `sat_v` None으로 두고 진행("근사하지 않는다") | B | 열 부재 = 정의 불능을 None으로 표시, 소비자가 미정으로 다룸 | 해당 없음 | 남음 | 아님 |
| E5-16 | graph/s1_values.py:29 | `SUPPORTED_SOURCE_KINDS = ("current_source",)` -- "이상 전압원은 교류접지 (3) 미구현 -> 기록만" | A | 주석 '미구현', 설계 2.2 | 별도 구현 card 없음. 대체 경로 = 중간 rail `supply_nets`(DEC-101 (2), 계획 SD-1 표 2106행 '확인') | 남음 | 아님: `pipeline/stage_a.py:241-250` unsupported → STATUS_STOPPED(fail-closed) |
| E5-17 | graph/s1v_build.py:14·47, pipeline/stage_a.py:239 | `stop_on_unsupported=False` 진단 모드(호출자가 findings로 판정) | B | docstring "정지 규칙을 우회하는 경로가 아니다", stage_a가 STOPPED 판정 | 해당 없음 | 남음 | 아님(확인: stage_a 250행) |
| E5-18 | graph/structure_load.py:138-139 | `structure.json` 없으면 빈 사실로 진행 | B | 선언은 선택. stage_a가 `declared_comparison: not_performed`로 보고 | 해당 없음 | 남음 | 아님 |
| E5-19 | metrics/sensitivity_gate.py:16·30-33·40, search/gate_run.py:45-52, find_front.py:72-75 | 감도 게이트: 값 None인 섭동은 "검사하지 못한 것 -- 오류로 세지 않는다", 그래도 verdict `ok`; 보고 없음·모든 변수가 읽는 소자면 gate None → note 없이 생략; front[0]만 검사, `error`도 note만 | C | docstring 한 줄 외 근거 없음(커밋 `d0ba5bde` U7). 계획·design에 '미검사=ok' 규칙 없음 | 없음 | 남음 | ⚠ (미검사 섭동이 있어도 `ok`, gate None이면 흔적 없음) |
| E5-20 | metrics/dc_metrics.py:115-118, find_front.py:76-80 | 값 미정 수동소자는 면적에서 빠지고 head 면적 미선언은 0.0; front는 그대로 내고 `review_needed`(DEC-79) note | A | 계획 DEC-79, docstring "수동소자 면적·값 미선언(DEC-79) -- review_needed" | card SF-1(spec 선언 형식·library spec data, N6.28)이 선언을 채우는 쪽. 엔진 규칙 대체 card 없음 | 남음 | ⚠(약): 면적 목적이 과소로 front에 들어감, note로만 드러남 |
| E5-21 | metrics/dc_metrics.py:112, objectives.py:8-10, find_front.py:103 | `counted_rails` 미선언이면 모든 rail 사용, note `not_computed ... needs_counted_rails_declaration` | A | DEC-78, docstring "spec 선언 대기" | SF-1 / SB-1(N6.31 공급 요구 하한)과 연결, 직접 card 불명 | 남음 | 아님(note) |
| E5-22 | search/slsqp_outer.py:18 | 재시작 반경 규칙 '격자 반경 × 2^m'의 m은 "U-47 보류, S-7" | A | 계획 U-47 "300 s를 front 전체에 쓸지는 보류" | U-47(열린 이슈, card 아님) | 남음 | 아님 |
| E5-23 | search/start_intervals.py:25, iv_area.py:15 | U11 임시 `fit_to_area_budget`을 U13 gm/ID 상한으로 대체했다는 기록 | A | design 40:1219 "as-built U11, 잠정" | U13으로 대체 완료 | 해소됨(design 40:1219 문언은 낡음 -- part 범위 밖 메모) | 아님 |
| E5-24 | search/iv_matching_l.py:72-83 | σ_VGS 정의 불능 gm/ID 점이면 더 큰 gm/ID 마디로 올라가 첫 정의점 사용, 없으면 원래 예외 | B | docstring: 입력 gm/ID는 하한 이상 어디든 가능 → 하한 위 첫 정의점이 가장 가까운 실현값 | 해당 없음 | 남음 | 아님 |
| E5-25 | search/iv_matching_l.py:131-145, iv_noise.py:87-90, _helpers_guard.py:32-44 | LUT 실패 시 offset·noise 가드 출발 구간을 `inactive`(사유 기록)로 끄고 진행 | B | 출발 구간 보조 경계일 뿐 판정은 ss 제약이 함, 사유를 `inactive`에 기록 | 해당 없음 | 남음 | 아님 |
| E5-26 | search/ss_constraints.py:14-17·69-88, ls_constraints.py:35-58, eps_sweep.py:34-44, find_front.py:108-111 | 값 None·분해능 0/None이면 행 없이 `unmeasured`; 최종 front는 '봉인 + 모두 측정'만, 나머지는 `unmeasured_front` | B | S-1, NFR-5 | 해당 없음 | 남음 | 아님(fail-closed 확인) |
| E5-27 | metrics/pending_metrics.py:1-20, catalog.py:10, constraint_classes.py:41 | 레지스트리 밖 metric 제약 = `unmeasured`/`metric_computation_pending` note("합격을 막지도 허락하지도 않는다") | A | docstring: 계산 대기 이름(U7·U8) | U7·U8로 전부 옮겨 `PENDING_METRIC_ROWS = ()` | 해소됨(표 비어 무동작) | 표에 이름이 다시 생기면 ⚠(front를 거르지 않음) -- 지금은 발동 0 |
| E5-28 | metrics/ls_fields.py:45-57·66-68 | LUT가 ID(VGS_max)를 못 내면 None, κ 셀 상한 미상 None → 그 방향 total None → 슬루 행 `unmeasured` | B | 정의 불능 표시, E5-26 경로로 fail-closed | 해당 없음 | 남음 | 아님 |
| E5-29 | metrics/device_sigma.py:20-30 | 폭이 모델 bin 밖이면 finger 분할 σ/√n 환산 | B | docstring: 모델 카드 slope 식의 면적 환산과 같은 방향 | 해당 없음 | 남음 | 아님 |
| E5-30 | metrics/block_gain_rows.py:13-23 | 특이 행렬 행은 NaN, 소비자(block_gain_bound.py:205)가 유한·양수 행만 씀 | B | docstring "유효하지 않은 행 NaN" | 해당 없음 | 남음 | 아님 |
| E5-31 | metrics/mna_solve.py:36, noise_transfer.py:78, _helpers_probe.py:82-87·96-105, noise_analysis.py:82·214, noise_integral.py:243, noise_devices.py:35 | 수치 특이·LUT 실패를 Undefined(사유 코드)로 바꿈 | B | 정의 불능 표시(numeric/definitional) | 해당 없음 | 남음 | 아님 |
| E5-32 | metrics/block_residual.py:39·52, block_model.py:129 | 풀지 않은 넷 전압 = 0.0(소신호 교류접지·탭 0 = gm 항 없음) | B | docstring "나머지는 탭 0 -> gm 항 없음, gds 부하만" | 해당 없음 | 남음 | 아님(보고 전용 진단) |
| E5-33 | search/kernel.py:62-66, gate_run.py:26-30, residual_probe.py:58-62 | `metrics_aux` 필드 없음(KeyError) → 빈 목록/None | D | 보고·진단 전용 | 해당 없음 | 남음 | 아님(단 E5-19 gate None으로 이어짐) |
| E5-34 | search/area_decl.py:28-35 | PDK 양 미선언(`pdk_quantity_undeclared`)만 None, 그 밖 거부는 다시 던짐 | B | 선택 선언 | 해당 없음 | 남음 | 아님 |
| E5-35 | search/layer0_center.py:398-402, slsqp_outer.py:158-161·192-196 | `_Abort`(eval/wall 예산) → 정지 사유 기록 후 중단 | B | 예산 정지(DEC-34·80) | 해당 없음 | 남음 | 아님 |
| E5-36 | search/kernel.py:127-141, metrics/ss_evaluate.py:113-115 | `CANDIDATE_FAILURE_CLASSES`만 잡아 후보 실패로 기록(넓은 except 아님) | B | kernel.py:13 "넓은 except 없음" | 해당 없음 | 남음 | 아님 |
| E5-37 | metrics/loop_analysis.py:68-76, curve_checks.py:9 | 이름만 `fallback`(PM 정의 불가 사유 선택) / LUT 선형 폴백 칸 보고(lut 쪽 예외의 보고자) | D | 예외가 아니라 사유 선택·보고 | lut 선형 폴백 자체는 lut 범위(design 42:126 DEV) | 남음 | 아님 |

#### 분류별 수 (metrics·graph·search, 37행)

| 분류 | 수 | 비율 |
|---|---|---|
| A (계획·결정 있음, 미반영으로 임시) | 14 (E5-01,02,04,05,06,07,08,14,16,20,21,22,23,27) | 38% |
| B (원칙·물리상 정당) | 15 (E5-11,15,17,18,24,25,26,28,29,30,31,32,34,35,36) | 41% |
| C (근거 없음·as-built 정당화) | 5 (E5-09,10,12,13,19) | 14% |
| D (기타) | 3 (E5-03,33,37) | 8% |

합 37행.

A 14건 중 해소/반쯤 해소: E5-01·02·14(반쯤), E5-23·27(해소). 대체 card가 **명시적으로 없는** A: E5-04(MOD8 재필터), E5-05(U15 layer0_budget), E5-06('card C'), E5-16(이상 전압원 -- 대체 경로는 있음), E5-20·21(엔진 규칙 card 불명), E5-22(U-47 열린 이슈).

#### fail-open ⚠
- E5-19 감도 게이트: 미검사 섭동을 오류로 세지 않고 `ok`, gate None이면 note도 없음(C).
- E5-20 수동소자 면적 미정 → 면적 과소로 front 포함, `review_needed` note만(A, 약).
- E5-27 계산 대기 metric은 front를 거르지 않음 -- 지금은 표가 비어 발동 0(잠재).

#### 버린 hit
- 예외 아님으로 버린 것: 키워드 hit 151줄 중 위 표에 들지 않은 ≈105줄(docstring의 '우회한 블록'(FF 용어)·`fd_jacobian skip`(고정 변수 열 = 정의상 평가 불필요)·`unmeasured` 필드 전달 등), `continue` 185개 중 구조 필터(종류·소속 걸러내기) ≈180개, `return None` 116개 중 위 표에 묶인 것 외 '정의 불능 표시'·탐색 실패 표시 ≈100개, 숫자 기본값 `.get` 40줄 중 계수·정렬 키(`get(n, 0)+1`, `get(n, -1)`) 36줄.
- TODO/FIXME/NotImplemented: 0건.

## 부록 6. code 나머지 모듈

### part6 -- 엔진 code 예외 감사 (lut·authoring·sizing·layout·core·convergence·pipeline·report·루트 .py)

- 대상: `wt/integ-it12/skills/analog-gmid-design/gmid_engine` HEAD `d759838a`(tests·metrics·graph·search 제외, 읽기만).
- 대조 계획: master `9d153f2f` `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`. 대조 design: `wt/design-v115` `17d11bdc` 41·40.
- 경로 접두 `E/` = `gmid_engine/`.

#### 전수 표

| key | 위치(파일:행) | 내용 한 줄 | 분류 | 근거 | 대체 card/규칙 | 상태 | fail-open |
|---|---|---|---|---|---|---|---|
| E6-01 | E/sizing/theta_schema.py:18-28(zero_cancel) | 영점 상쇄 R: 구조 규칙이 통과하면 R = 1/Σgm로 고정(θ 아님), 통과 못 하면 `ss_resistance` θ로 '폴백' | A | 커밋 48cf0684(2026-10-08) 'DEC-92 (3)(a) 기본 + (b) 폴백'. 계획 DEC-92 (3)은 O-33 (10)·감사 A12로 'R은 늘 θ, 구조 규칙은 출발값만'으로 바뀜(plan:291, 상태 '미구현'). 엔진이 옛 (a)/(b)를 유지 | 있음: LA-1 F-LA11·X-LA5(plan:1830·1930) | 남음 | 아님(탐색 자유도 축소, 판정 통과 아님) |
| E6-02 | E/sizing/writer_plan.py:257, s2_values.py:94 | 입력 포트 W4 뿌리 둘 이상 → `unsupported_rule_branch` 정지 | A | 'DEC-76 미구현'(커밋 14e0ca2a). 계획 DEC-76(발동 0 폴백은 만들지 않고 정지 안전망)·IT-1 범위 4·IT-Q1 (나)(plan:1496·1521·1551) | **없음**(발동 회로가 들어오면 구현 -- DEC-76) | 남음 | 아님(fail-closed) |
| E6-03 | E/sizing/seal_saturation.py:37-39, seal.py:14 | LUT에 VDSAT 열이 없으면 봉인 7 행 tol None → undefined → `sealed=None` | A | 계획 DEC-88 '열이 생기기 전에는 봉인 7을 정의 미확정으로 표시, 2/(gm/ID) 대신 안 씀'(plan:287), N6.1 순서 1 MOD1 'VDsat(VDSAT 열, DF-25)'(plan:1211) | 있음: MOD1 VDSAT 열(LUT 재생성) | 남음(옛 12-L 세트 사용 시) | 아님(undefined는 통과가 아님; 탐색은 search/seal7_pending으로 대기 -- 범위 밖) |
| E6-04 | E/lut/lut_set.py:360-361 | 중점 파일에 VDSAT 열이 없으면 그 열만 건너뜀(ID·GM은 필수) | A | E6-03과 같은 DEC-88 '열 대기' | 있음: MOD1 | 남음 | 아님 |
| E6-05 | E/sizing/seal_kcl.py:9 | 봉인 3 `exclude_nets`(사유 선언 넷 제외) 선언 자리가 없어 0개 | A | 커밋 b1b3a370 '선언 자리가 아직 없어'. 계획 N3.6 항목 3 'exclude_nets는 사유가 선언된 넷만'(plan:575) | **없음**(선언 자리 card 없음) | 남음 | 아님(제외 0 = 더 엄격) |
| E6-06 | E/lut/derived_fns.py:4 | LUT memo 호출 형식 as-built `lookup(region, fn, key, compute)` 유지, `memo.call` 전환은 U17 ③ | A | docstring 'as-built ... 전환은 U17 ③' | 있음: U17 ③ | 남음 | 아님(규칙 우회 아님 -- 인터페이스 형식) |
| E6-07 | E/lut/vgs_current_density.py:10 | 옛 sizing '임시 우회'(gm_id_for_target로 같은 양 풀기)를 이 함수가 대체 | A | DEC-88 `vgs_for_current_density` | 있음(이 함수) | **해소됨** | 아님 |
| E6-08 | E/authoring/spec_constraints.py:265, :37-38 | `source.kind == pending_spice` 제약은 `judged False`(보고만), `pending_constraints`도 판정·정지 대상 아님 | A | 계획 U-17·U-35 'pending_7a: 7a SPICE 대조에서 기준값을 읽는다, 그 전까지 판정에 쓰지 않는다'(plan:2355·2373) | 있음: ME-1(7a, plan:2010) | 남음 | ⚠(그 제약은 판정 없이 front 통과 -- 사용자 결정 U-35로 승인된 fail-open) |
| E6-09 | E/sizing/block_columns.py:744-755, input_window.py:51-65 | 입력 창을 못 재면(연립 특이·정의역 밖·VDSAT/tol 미정) '종래 사상'(요청 y·순서 창)으로 풀고 `unmeasured` | C | 커밋 5eace7f8(2026-10-08) '종래보다 나빠지지 않는다'. design 41 4.7-0 A6 (a)는 as-built 사실 표이고 4.7-2 항목 4가 그대로 유지(출력 전용 상태, metric은 `dc_window_cfg`를 읽음) -- 물리 근거 없이 as-built 동작 유지 | 없음(전용 card 없음; 판정 창은 IT-2c `dc_window_cfg`가 fail-closed) | 남음 | 아님(판정 밖 θ 범위), 단 θ y 범위가 측정 없이 정해짐 |
| E6-10 | E/sizing/block_columns.py:756-780 | tol 미정이거나 k_max 안 미수렴이면 마지막 잰 창을 y 범위로 그대로 쓰고 `unsettled` | C | design 41 4.7-0 A6 (b)(c) as-built, 4.7-2 항목 5 '출력 전용' | 없음 | 남음 | △(정지 대신 진행, 판정은 아님 -- 상태 표지) |
| E6-11 | E/lut/derived_fns.py:117-130 | `tol_vdsat_max`: docstring은 '보수(최댓값)'인데 표를 못 만들거나 칸이 없으면 0.0 | C | 옛 `CurveBook.tol_vdsat` 이식(docstring), 커밋 686d946c. 0은 보수 방향이 아님 -- 정의 불능을 숫자로 메움 | 없음 | 남음 | △(층 0 출발 곡선 전용 -- search/_helpers_curves.py:94; 최종은 봉인 7) |
| E6-12 | E/layout/passives.py:21 | 값(`passive_value`)이 None인 수동소자는 판정 축 면적 입력에서 빠짐 | C | docstring '탐색 축과 같은 제외' -- 일관성 근거만, 물리 근거·계획 문장 없음 | 없음 | 남음 | ⚠(값 미정 소자 면적이 0으로 빠져 면적 과소 가능) |
| E6-13 | E/sizing/_helpers_seal.py:22-33, seal_*.py | tol None 행 → 항목 undefined(통과로 바꾸지 않음) | B | 계획 N3.14 공통 실패 규약(정의 불능 ≠ 통과) | -- | 유지 | 아님 |
| E6-14 | E/sizing/seal_conduction.py:42 | 전류 ≤ 0 소자는 봉인 9 행에서 제외 | B | 전도 여유는 전도 소자에만 정의(DEC-88 '전도 MOS'); 전도 MOS 전류 > 0은 θ 정의역(`current_cone`, theta_schema.py:30) | -- | 유지 | 아님 |
| E6-15 | E/sizing/block_columns.py:330-335, 450-456 | 반복 중 LUT 정의역 이탈(VDS 하한 아래 `lut_curve_undefined` 등)은 이전 값 유지, strict 검증에서 재검사 | B | 반복 중 과도 이탈은 해가 아님; 수렴 뒤 `strict=True`가 fail-closed(:626 주석) | -- | 유지 | 아님 |
| E6-16 | E/sizing/block_columns.py:356-360 | 목표 전류밀도가 분지 밖이면 ±inf 반환(이분 브래킷용) | B | 단조 역산의 정의역 끝 표현(lut `lut_target_out_of_range`) | -- | 유지 | 아님 |
| E6-17 | E/sizing/block_columns.py:616-648 | Gauss-Seidel 미수렴·strict 위반 → Newton으로 전환, `SccLog.fallback`에 사유 기록 | B | 수치 방법 갈래(s2_values.py:375 method 집합), Newton도 실패하면 예외 | -- | 유지 | 아님 |
| E6-18 | E/lut/point_query.py:37-62, _helpers_interp.py:28·141·181 | Hermite 불가 칸은 선형 보간, `OpPoint.fallbacks`에 사유 기록 | B | DEC-87 FC 정책(Fritsch-Carlson 단조 조건 -- 수학적 정의역), '조용한 선형 폴백 금지' | -- | 유지 | 아님 |
| E6-19 | E/lut/derived_fns.py:49-60, :93-98 | VDS 엣지 비용 하한: tol_vdsat 표 실패·미정 칸 = 0, VDSAT 열 없으면 0 | B | docstring '하한을 낮추는 쪽' -- 달성가능성 하한은 낮을수록 보수(가지치기 덜 함) | -- | 유지 | 아님 |
| E6-20 | E/lut/mismatch_sigma.py:45-51 | 모델 블록이 쓰지 않는 mismatch 변수 slope = 0 | B | SPICE 모델 카드에서도 그 변수 기여 0(docstring); 기준 0·소자 ≠0은 `lut_mismatch_slope_unscalable`로 실패 | -- | 유지 | 아님 |
| E6-21 | E/sizing/size_and_seal_local.py:109, input_window.py:68 | `rails.get(net, 0.0)`·`slope.get(net, 0.0)` | B | 전력 = 레일 끝 항만(정의), 고정 넷 감도 = 0(정의) | -- | 유지 | 아님 |
| E6-22 | E/lut/midpoint_checks.py:98-121 | 쓰지 않는 중점은 사유와 함께 `skipped`에 남김 | D | 검증 대상 정의역 밖(폭 다름·bin 밖·앵커 등), 조용히 버리지 않음 | -- | 유지 | 아님 |
| E6-23 | E/lut/derived_fns.py:103-114, 133-140 | `reference_vds`·`param_row`: 곡선 미정이면 다음 VDS/None | D | 층 0 출발값 표의 빈칸 | -- | 유지 | 아님 |
| E6-24 | E/sizing/block_columns.py:539, 700, 717 | Newton 기울기·tolerance·내부점 탐색 실패 → None/continue | D | 내부 탐색 갈래(호출자가 None을 정지/다음 갈래로) | -- | 유지 | 아님 |
| E6-25 | E/lut/table_cache.py:208-342 | 디스크 캐시 I/O 실패 → 경고·캐시 끔·재계산 | D | 계획 승인 예외 U-87(파생표 디스크 캐시); 실패해도 값은 재계산이라 결과 불변 | -- | 유지 | 아님 |
| E6-26 | E/core/blas_env.py:108,123 | BLAS 후보 라이브러리·기호 탐색 실패 → 다음 후보 | D | 플랫폼 탐색, 못 찾으면 정지(docstring :18) | -- | 유지 | 아님 |
| E6-27 | E/authoring/spec_settings.py:195,220, spec_constraints.py:310 | `{"pending": ID}` 칸은 값 None + 결정 ID로 담고 중복 검사에서 제외 | D | design_spec_format 1.5 결정 대기 표지(실행 전 정지, spec_constraints.py:36) | -- | 유지 | 아님 |
| E6-28 | E/authoring/spec_noise_testbench.py:7,13 | 항목 칸 '설계 미정 -- 설계 공백으로 보고', topology None이면 존재 검사 건너뜀 | D | 로드가 meta 불일치로 어차피 거부; 설계 공백은 docstring에 보고만 | design 공백(card 없음) | 남음 | 아님 |
| E6-29 | E/pipeline/stage_b.py:142 | 단계 A가 ok 아니면 단계 B `skipped` | D | 상태 보고(진단 GB4는 따로) -- 정지의 한 형태 | -- | 유지 | 아님 |
| E6-30 | E/layout/crossover.py:67-97·250-364, patterns_common_centroid.py:119-136·173-494, patterns_interdigitate.py:45-80, mirror_trail.py:175, _helpers_hubleaf.py:96-120 | 레이아웃 짝짓기·패턴 표 실패 → 순서대로 짝짓기 / crossover 허용 배치로 폴백('절대 실패하지 않는다'), `node_pairing_fallback_used` 기록 | D | 2026-07-28 사용자 요청(옛 layout 이식, docstring); crossover 수는 출력에 남음 | -- | 유지 | 아님(품질 저하가 수치로 보고됨) |

#### 분류별 수 (항목 30)

| 분류 | 수 | 비율 |
|---|---|---|
| A (계획 반영 대기) | 8 (E6-01~08; 해소 1 = E6-07) | 27% |
| B (원칙·물리) | 9 (E6-13~21) | 30% |
| C (근거 없음/as-built 정당화) | 4 (E6-09~12) | 13% |
| D (기타·탐색 갈래·상태) | 9 (E6-22~30) | 30% |

- fail-open ⚠: E6-08(pending_spice 제약 판정 제외 -- 사용자 승인 U-35), E6-12(값 None 수동소자 면적 제외). △(판정 밖 진행): E6-10, E6-11.
- (A) 중 대체 card 없음: E6-02(DEC-76 다중 입력 뿌리 -- 정책상 '발동 회로 올 때'), E6-05(봉인 3 exclude_nets 선언 자리).
- (A) 중 계획과 엔진이 어긋난 채 남은 것: E6-01(DEC-92 (3) 개정 미반영, LA-1 대기).

#### 버린 hit

스캐너 hit 400줄(except 60·continue 133·주석 73·skip/undefined 78·pass 1·`.get(k, 기본값)` 55, 겹침 포함) 중 위 30항목으로 묶고 나머지 버림:
- authoring `continue` ~40건: 모두 `hits.append(...)` 뒤 continue -- 거부 누적(fail-closed), 예외 아님.
- `except ... raise with_device(...)`·`attach_partial; raise`·`compute_block` 실패 등록 후 재발생 등 ~25건: 재발생, 예외 아님.
- `.get(k, 0)` 카운터·정렬 키·인접표 빈 tuple ~48건: 무의미한 기본값.
- lut `*_undefined` raise ~25건: fail-closed 정지 자체.
- 정의 불능 → 정지(stage_a.py:232 `count_budget_undefined`, converge.py:47 `sealed is not None`): fail-closed라 제외.
- layout·convergence 순회 continue(seen/used/길이 0 등) ~50건: 알고리즘 순회.

#### 재현

```bash
### 후보 스캔(디렉터리별, tests 제외)
python p6scan.py except,comment,skip,pass,getdef,continue   # scratchpad/exc/p6scan.py
### 패턴: ^\s*except\b | ^\s*continue\b | TODO|FIXME|XXX|임시|미구현|as-built|당분간|보류|우회|폴백|fallback|NotImplemented
###       | \bskip|unmeasured|undefined|정의 불능 | ^\s*pass\s*$ | \.get\([^()]*,\s*[^)]
### 근거 커밋
git -C wt/integ-it12 log -S"DEC-92 (3)(b) 폴백" --format='%h %ad %s' --date=short -- skills/analog-gmid-design/gmid_engine   # 48cf0684
git -C wt/integ-it12 log -S"종래 사상" ...            # 5eace7f8
git -C wt/integ-it12 log -S"선언 자리가 아직 없어" ... # b1b3a370
git -C wt/integ-it12 log -S"DEC-76 미구현" ...        # 14e0ca2a
git -C wt/integ-it12 log -S"표를 못 만들면 0" ...     # 686d946c
### 계획 대조
grep -n -E "\| DEC-(76|87|88|92) |U-17 |U-35 |exclude_nets|F-LA11|X-LA5" chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md
```
