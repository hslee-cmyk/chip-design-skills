# 3차 독립 검토 -- Phase 3 `30-module-split` 초안 v5 (UD-0 승인 요청 전)

검토자: 독립 검토 agent(초안 작성자·이전 검토자 아님). 저장소 읽기 전용(HEAD = gate `master` `7535799`), 상태 변경 git 없음.
측정은 `C:/g72/repo`(`git clone --no-hardlinks`, `7535799`)에서 했고 끝난 뒤 `C:/g72`를 지웠다. Python `C:/Python314/python.exe -B`.
대상: `draft_phase3_design_v5.md`, `draft_p3_g1.spec.md`, `draft_p3_t0.spec.md`, `draft_p3_d0a.spec.md`, `phase3_revision_log.md`(전 절), `review_phase3_drafts.md`, `review2_phase3_v3.md`.
대조: `draft_v3_exempt_binding.spec.md`, `draft_v3_scope_policy.spec.md`, `draft_b33.spec.md`(`b33_revision_log.md`는 없음), `draft_b26_1.spec.md`, `draft_b34.spec.md`, `user_decisions.md`,
`approval_20260930-b26-before-phase3.md`, `redteam_numbering.md`.

## 판정

**아직 승인 요청 준비가 안 됐다(not approval-ready).** 막는 것 4건:

* D0a `check`의 `order` 규칙과 `shim` 규칙이 적힌 그대로면 **M card가 통과할 수 없다**(B1·B2). 두 규칙은 참조 구현 모의 밖이라(design 부록 A 측정 한계) 한 번도 실행된 적이 없다.
* DoD E3 명령이 원문 그대로면 **아무것도 찾지 못해 공허 PASS**한다(B3, 실측).
* UD-0이 덮는다는 문서 개정의 문안이 없고, N3.10 개정 시점이 design 커밋과 D0b 사이에서 모순된다(B4). 그래서 승인 기록 diff를 만들 수 없다.

판정 이론(G1 MOVED 규칙, D-20·D-21 합성, redteam 번호, 순서)은 확정된 V3·B33·B26-1·B34 초안과 **모순이 없다**. 문제는 남은 옛 문장 몇 개다(S1).
Blocking 4건을 고치면 승인 질문을 올릴 수 있다. 질문 문안은 맨 끝에 있다.

---

## 1. Blocking

### B1. D0a `order`가 MOD8(과 MOD9)의 `stick_diagram` import를 위반으로 잡는다 → M8을 통과할 수 없다

* 문언: D0a 계약 4 `order` = "`--card` 파일의 import 문이 가리키는 트리 파일 중 **`--split` 파일이거나** 번호가 같거나 큰 다른 MOD 파일인 것".
  design §6.3의 `MP_ARGS`는 `stick_diagram.py`를 `--split`에 넣는다. 그런데 `stick_diagram.py`는 MOD7이다(N3.10, 계속 남는 파일).
* 실측(`7535799`):
  * `sizing_recipe.py:5302`가 `from stick_diagram import (Transistor, load_topology, …, assign_finger_geometry, run_topology_pipeline, repair_matching_safety, split_into_stacks, …)`를 한다.
    MOD8 대표 대상(`run_topology_pipeline_with_finger_fixup`·`resolve_stack_layout`)과 D-3의 `optimize_full_circuit_budget`(SD 레이아웃 함수 8개를 부른다 -- design §6.2 A-3)이 이 이름들을 쓴다.
    그래서 새 `sizing_layout_convergence.py`는 `stick_diagram`(MOD7)을 import해야 한다. MOD7 < MOD8이라 계층상 정당하다.
  * `design_report.py:32`가 `from stick_diagram import load_topology, _audit_result_json`를 한다. MOD9 쪽도 같은 경우일 가능성이 있다.
* 결과: M8(아마 M9도)에서 `check`가 `order`를 발견해 exit 1이 된다. MOD7 레이아웃 함수에 닿는 다른 경로는 없다.
  design §3 ORDER("⊆ {번호가 작은 MOD}(잔여 split 파일 없음)")도 MOD7이자 split인 파일을 어떻게 다룰지 정하지 않는다.
* 고칠 것:
  1. design §3 ORDER와 D0a 계약 4를 이렇게 바꾼다: "가리키는 파일이 N3.10 파일이면 그 번호가 `--card` 번호보다 작아야 한다(`--split`에 있어도 N3.10 번호로 판정). **N3.10 밖의** `--split` 파일은 허용하지 않는다."
  2. D0a 합성 oracle에 'split이자 N3.10인 작은 번호 파일을 import하는 card → 발견 0' 단계를 넣는다.

### B2. D0a `shim`이 중간 card마다 남은 정의를 위반으로 잡는다 → M1~M8을 통과할 수 없다

* 문언: D0a 계약 4 `shim`은 "head에 있는 `--split` 파일(N3.10·`--keep` 아님)의 최상위 문장이 docstring과 `from <MOD 줄기> import …` 밖에 있으면" 발견으로 친다.
  "그 파일의 단위가 전부 옮겨졌을 때만"이라는 조건이 없다.
* 이관 중 `sizing_recipe.py`는 '잔여 정의 + 재수출 목록'이다(design §2.1). M1 병합본에도 SR의 def·class·대입 수백 개와 `import json` 등이 남는다.
  그래서 M1~M8의 `check`는 SR(그리고 M4 전 TL, M9 전 DR)에서 `shim`을 발견한다. 최종 shim에서도 `from __future__ import annotations`(SR 35행)이 그 문언에 걸린다.
* 같은 card 안에서도 모순이다. D0a '무동작 판정 입력'은 "base = head 쌍의 `check`는 `move-set` 외 발견 0"이라고 하는데, 문언대로면 `shim`도 발견된다.
* 고칠 것:
  1. design §3 SHIM과 D0a 계약 4를 둘로 나눈다.
     (a) 중간 상태: head split 파일에서 base에 없던 최상위 문장은 `from <MOD> import` 재수출 줄뿐이다(남은 단위의 변경은 `changed`·`lost`가 맡는다).
     (b) 완전 shim: 그 파일에 배정된 단위가 하나도 남지 않은 card(`plan` 기준)에서만 "docstring + 재수출 줄 + (선택) `__future__` 줄 외 0"을 요구한다.
  2. 이름 집합 대조와 출처 동일성 대조는 두 경우 모두 그대로 둔다.
  3. 합성 oracle에 '부분 이동 card(잔여 정의 있음) → `shim` 0' 단계를 넣는다.

### B3. DoD E3 명령이 원문 그대로면 아무것도 찾지 못한다 → GONE-SHIM 공허 PASS

* §10 E3은 표 칸 안에 있어서 정규식의 `|`가 `\|`로 적혀 있다. auditor는 원문 .md를 읽는다. 원문 그대로 실행하면 `git grep -E`에서 `\|`가 문자 `|`로 해석된다.
* 실측(`7535799`, `C:/g72/repo`):

  | 명령 | 결과(파일 수) |
  |---|---|
  | `git grep -l -E "^[[:space:]]*(import\|from)[[:space:]]+(sizing_recipe\|topology_library\|design_report)\b" -- '*.py'`(원문) | **0** |
  | 같은 식, 역슬래시 없이 `|` | **57** |
  | 문자열 import 식(원문 `\|`) | **0** |
  | 같은 식, `|` | **6**(10줄) |

  E3 통과 기준은 "결과 ⊆ D-9 제외 집합"이다. 빈 결과는 언제나 통과하므로 **거부를 한 번도 하지 않는 판정**이다.
* 부록 A M22·M24 명령도 같은 모양이다. 그쪽은 측정 기록이라 판정에 영향은 없지만 재현 명령으로는 틀렸다.
* 고칠 것:
  1. E2·E3·E4·E6 명령을 표 밖 ```` ```bash ```` 블록에 둔다(§6.3 `MP_ARGS`처럼). 표에는 ID와 통과 기준만 남긴다.
  2. E3에 '거부 확인'을 더한다. 같은 명령을 Phase 3 전 base(M1 판정 기록 `base_commit`)에서 돌리면 결과가 비지 않아야 한다(지금 57파일·6파일).

### B4. UD-0이 덮는 문서 개정 문안이 없고, N3.10 개정 시점이 모순된다

* §9.1: "이 design의 UD-0 문서 개정도 design 커밋과 함께 승인 대상 diff에 든다." 선례 `20260922-10-test-separation-design`의 `diff_path`가 계획서·00·05·10을 함께 덮는다(실측).
  그런데 UD-0 목록 7개 항목의 문안이 `_drafts` 어디에도 없다. 계획 N3.10 표, 534행 제외 집합(D-9), N3.12.3 test-only 열거, `00-common` §3.2 103행·§10.1 431행, `10-test-separation` §5.6 '파일' 열, N3.10 MOD2 `rail_declaration`이 그것이다.
  확인 방법: `grep -l "rail_declaration.*대표 대상\|Phase 3 T0·T1"` → design 초안과 이력 로그뿐이다.
* N3.10 개정 시점이 두 곳에서 다르다.
  * UD-0 행: design 커밋 때 바꾼다("A-3 계산 결과 -- `load_topology`·`validate_theta_declaration_order` 위치, `optimize_full_circuit_budget` MOD8, `rail_declaration`").
  * §8 D0b 행: D0b가 "N3.10 표 개정(A-3 결과)"를 한다. 그리고 D0b는 B26-1·B34 병합 **뒤**에 처음 계산한다(§6.4).
  * 게다가 `validate_theta_declaration_order`의 목적지가 "그 둘의 MOD 이상"으로만 적혀 있어 개정 문안을 지금 쓸 수 없다.
* 이것이 승인 질문에 미치는 영향: 사용자는 문안이 없는 계획서 개정과, D0b가 나중에 계산할 **추가** N3.10 개정(F1 "규칙으로 안 풀리면 N3.10 표 개정(이 design 승인 범위)")을 한꺼번에 승인하게 된다.
  계획서 표 개정은 승인 대상이다(0.5 공격 16). 그런데 그 내용을 지금 볼 수 없다.
  참고: N3.10·N3.12.3은 `plan_tables_hash` 입력이 아니다(`merge_gate.py:107-176` 실측: N4.1·N4.2·N6.1·N3.12.2만). 그래서 `plan_tables` 승인은 필요 없다.
* 고칠 것:
  1. `draft_phase3_doc_patch.md`에 7개 항목의 교체 문안을 쓴다(계획 N3.10은 지금 HEAD에서 계산 가능한 3건 + D-19).
  2. 둘 중 하나를 design에 명시한다.
     (가) D0b가 B26-1·B34 병합본에서 위 목록 밖의 새 N3.10 충돌을 내면, 그 diff를 따로 사용자 승인(`target_kind: diff`)으로 받는다.
     (나) UD-0이 'A-3 계산 결과 그대로' 위임을 명시적으로 덮는다. 이 경우 질문 문안에 위임이라고 쓴다.
     권고는 (가)다. 메모리 원칙이 '승인은 diff로'이고, 지금 보이는 개정은 3+1건으로 작다.

---

## 2. Should-fix

| # | 위치 | 발견(근거) | 고칠 것 |
|---|---|---|---|
| S1 | design §5.3-5·§11-8, G1 '작성 전 실측' 2, revision log v5 '다른 초안에 넘기는 것', design §5.5.4 | **옛 문장.** (i) "세 card 초안은 각각 32·32·33" -- 지금 초안은 `draft_b33.spec.md:131` `33-v7-registry-edges`, `draft_v3_exempt_binding.spec.md:82` `34-…`, `draft_v3_scope_policy.spec.md:89` `35-…`(12:04~12:10 개정, `redteam_numbering.md` 확인). (ii) §5.5.4 "B33 초안 문언은 '같은 이름의 바인딩', chase로 고칠 것을 권함" -- B33 34행이 이미 "M 파일의 `from X import NAME`을 따라 X의 바인딩(재수출, 방문 집합)"이고, R2'(dunder 폴백 제거)와 계약 9도 개정됐다. (iii) "B33 V3 인벤토리 33,991 → 79,809" -- B33 256행 개정값은 **33,991 → 44,493**(79,809는 v1). | 사실 문장 갱신. 번호 배정 자체는 모두 일치한다(모순 없음) |
| S2 | design §9.1·§8.1 | (i) "Phase 2 DoD PASS(현재 남은 것: P9, P10, DoD E0~E5)"가 §8.1(P10b·면제 묶기·범위 정책·B34·B26-1)과 승인 A2(B34·B26-1은 `phase: 2`, "Phase 2 진행 중")와 어긋난다. (ii) T0·D0a·D0b는 `phase: 3` card다. 계획 991행 "이전 Phase DoD PASS"가 이 card들에도 걸리는지 적혀 있지 않다(§8.1은 "준비 가능"만, M card만 "Phase 2 DoD 뒤"). 게이트는 이 순서를 강제하지 않는다(`merge_gate.rule10_phase` 실측). (iii) §8.1 그림의 `┬/┴`는 G1이 B26-1 뒤처럼 읽히는데, 본문은 G1 base를 33·34·35 병합 뒤로만 둔다 | 남은 목록을 §8.1과 맞춘다. T0·D0a·D0b의 병합 시점(Phase 2 DoD 전 허용 여부와 근거)을 한 문장으로 정한다. 그림에서 필수 순서와 편의 순서를 구분한다 |
| S3 | design §2.3·§8 M10 | **M10 V3 비용이 추정돼 있지 않고 회로도 정해지지 않았다.** 실측: HEAD `run_harness.py::run`(422~529행) 변이 71개(`mutate_changed.mutants`). N2에서 옮겨진 몸체는 새 def(본문 전체)가 되고 `run()`에는 바뀐 문장·삭제 지점이 더해진다. 새 def의 인벤토리에는 새 E-INST test와, `run`을 거치는 이름 과대 근사 test 60개(§2.3 S12)가 들어간다. 파일럿 E-INST는 판당 7~8분(`dryrun_phase2_e4.md:68`)이다. **추정**: 약 70 변이 × 8분 이상 = 9시간 이상. 또 `--timeout` 600초에 가까워 느려진 변이가 '죽음'으로 세질 위험이 있다(B33 62행) | M10 행에 진입점 test의 회로를 가장 싼 library 회로로 지정한다. '작성 전 실측'에 변이 수와 변이 1개 실행 시간 측정을 넣는다. 다른 M card 비용과 함께 §8에 추정치를 적는다(아래 §5) |
| S4 | design §6.4 D-19 | **근거 하나가 D-19와 무관하다.** "이렇게 두면 MOD2 함수의 주석이 MOD3를 가리키는 위쪽 참조가 생기지 않는다"는 `RailDeclaration` 이야기다. A-2가 D-19와 무관하게 `RailDeclaration`을 MOD2에 둔다(MOD2 구조 제안 함수가 `rails: RailDeclaration` 주석을 단다). 그래서 D-19를 정당화하지 않는다. 또 MOD2 책임 '로딩'의 대표인 `load_topology` 자체가 A-3로 MOD3에 가므로 '책임' 근거는 반쪽이다 | D-19 근거를 'MOD2 = 스키마·선언 게이트(`validate_*`와 같은 성격), B37a `port_declaration`과 한 곳'으로 좁힌다. 사용자 질문에 두 선택지를 중립으로 둔다(아래 질문 문안) |
| S5 | G1 의도 31~32행, G1·T0·D0a의 'design v4' 인용 | G1 의도의 "이 card의 test worktree는 **지금** gate `master`에서 만든다"가 같은 card 34~37행·작성 전 실측 머리("실제 base는 B33·면제 묶기·범위 정책 병합 뒤")와 모순된다(v4 문장 잔재). G1 '결정 필요 항목'의 "design v4 §9.2 UD-5"와 D0a·T0의 "design v4 §x" 인용이 많다(절 번호는 v5와 같다) | G1 31~32행을 base 문장으로 바꾼다. 인용을 'design 30'(정식 경로)으로 통일한다 |
| S6 | design §5.2·부록 A G5/G5'·§9.2 UD-5 근거, revision log | **측정 수치 오기.** "v3 27단계", "`v3_regression` 27/27", "51 = v3 27 + 새 24" -- 원자료 `p3v3_g1_results.json` `counterexamples` 26개, `p3v4_g1_results.json` `v3_regression` 26/26(모두 참), 새 단계 25개(N1·N1b·N1c·P 2·N2·N3·N3b·N4·N5·N5ok·N6·N6ok·N7·N8a·N8b·N9a·N9b·N10·N11·N12·N13·S2 2·S5), 합 51. `adversarial_summary` 22/22 거부는 일치 | 26·25로 고친다(결론 불변) |
| S7 | design §7.2 m7·§10 E3 | 문자열 import 10곳 중 `test_d_move_tests.py:37`은 docstring 문장(`importlib.import_module("sizing_recipe")` 뒤 …)이고 import가 아니다(실측). F1이 이것을 두면 E3 셋째 명령이 제외 집합 밖 결과를 내 **거짓 FAIL**이 된다(안전한 쪽이지만 F1 범위 문장 "전부 B군 계약 test"가 틀렸다) | F1 범위에 그 docstring 갱신을 넣거나, E3 문자열 패턴을 AST 문자열 상수 호출로 바꾼다 |
| S8 | design §9.2 UD-1 | 기본안만 있고 대안이 없다. 추적 안 된 `smoke_run_harness_session18_save.py`는 `sizing_recipe`(SemiEmpiricalGmIdLUT·optimize_full_circuit_budget)와 `stick_diagram.save_instance_json`을 import한다(9·10행 실측). 그래서 F2 뒤에는 두 import 모두 깨진다 | 질문에 대안(추적 추가 후 F1 갱신 / 삭제)을 적는다(아래 문안) |

## 3. Minor

| # | 위치 | 내용 |
|---|---|---|
| m1 | §8 'card 수 15' | 목록을 세면 **16**이다: G1·T0·D0a·D0b(4) + M1~M6(6) + M8·M9·M10(3) + T1·F1·F2(3). |
| m2 | §10 E2 | `<캐시>`가 §10에 정의돼 있지 않다(05 §4.4 캐시 -- 인용으로 충분). V3에 `--gmid-phase=3`이 없다. 05 '…V1과 같은 값'과 맞추면 좋다. 변이 0이라 판정 영향은 없다. |
| m3 | §2.2·§8 F2 | "`stick_diagram` 임시 재수출 제거"에 규칙이 없다. SD에 남는 레이아웃 함수가 쓰는 이름(MOD2·MOD3로 간 `Transistor` 등)의 import는 남겨야 한다. '재수출만 지움 = SD 자신이 읽지 않는 이름'을 한 줄로 적는다. |
| m4 | §8 M7 | split 파일의 단위가 MOD7로 배정되면 그것을 옮길 card가 없다. 레지스트리 실측: 목적지가 `stick_diagram`뿐인 행 중 SD 밖 정의 0. A-5로 MOD7이 될 수는 있으므로 D0b에 'SD 밖 단위의 MOD7 배정 0' 단언을 넣거나, 생기면 M7을 실제 card로 둔다. |
| m5 | §8.1 | 그림이 면제 묶기 → 범위 정책 → B34 → B26-1을 한 줄로 고정한다. 결정(A1-a·A1-b·A2)과 초안(B34 '순서' 3·4)이 요구하는 것은 '34·35 → B26-1', 'B34 → B26-1', 'P9 → B34'뿐이다. B34와 34·35 사이 순서는 자유다. |
| m6 | §6.4 `_import_analog_grammar` | B34 초안 212행은 "M2(어댑터와 소비 함수를 MOD2로 이동)"라고 단정한다. design은 A-4/A-5에 따라 MOD2 또는 MOD3로 둔다. D0b 실측으로 정해진다는 문장을 B34 쪽 인계에 남기면 충분하다. |

---

## 4. 확정 초안과의 일관성(점검 (2))

| 항목 | design v5·G1/T0/D0a | 확정 초안 | 판정 |
|---|---|---|---|
| redteam 번호 | G1 32, B33 33, 면제 묶기 34, 범위 정책 35 | B33 `33-v7-registry-edges`(131·144·160행), 면제 `34-v3-exempt-binding`(82·220행), 범위 `35-v3-changed-scope`(89·225행) | **일치**. 단 design·G1의 "아직 32·32·33" 문장이 옛 사실(S1) |
| 병합 순서 | P9 → P10 → P10b → 34 → 35 → B34 → B26-1, B33 → G1, 33·34·35 → G1 | 면제: "P9·P10·P10b 뒤, 범위 앞, B26-1 앞"(11행). 범위: "묶기 뒤, B26-1 앞, G1 앞"(11행). B26-1: "P9 → B34 → B26-1"(20행). B33: "권고 B33 → G1"(244행) | **모순 없음**. B34와 34·35 사이는 결정이 없다(m5) |
| D-20(옮기며 바뀐 def·거부 후보 = 새 def 본문 전체) | G1 계약 4 | 범위 정책 계약 3 "base 같은 경로에 같은 qualname이 없는 def는 본문 전체", G1 계약 4 문장을 G1이 더함(B45) | **일치** |
| D-21(면제 대조 불변, id 모듈 = 파일 줄기) | G1 계약 4, §5.5.3 | 면제 묶기 계약 3("id가 이번 실행의 변이 id와 같지 않은 원소는 싣지 않는다", 70행), 해시 없는 옛 원소 14개 미적용(160·190행), `module_name` 47·362·374행(실측) | **일치** |
| 출력 키 | G1 `defs`·`moved`·`move_rejected` 추가, M card 기준 `not_targeted` = 0·`targets_by_def` = `{}` | 면제: `survivor_bindings`·`exempt_ignored`(74행). 범위: `not_targeted`·`targets_by_def`(79~81행, 안에 `def_header_changed`) | 겹침 없음, **일치** |
| B33과 G1 | `build_graph` 불변, 바인딩 노드 `::=`는 def 아님 | B33 계약 7·9·R3 `_is_source` | **일치**(§5.5.4 문장만 옛 사실 -- S1) |
| B26-1 계수 test와 T0 계약 10 | `stick_diagram.rail_declaration` 모듈 속성 교체, SR은 import하지 않음 | B26-1 계약 3(85~90행) | **일치**. D-19 대로면 M2 뒤에는 SD 재수출로 계수가 유지되고, M3(`load_topology` → MOD3)에서 깨진다는 design 설명이 맞다 |
| A2 범위 | B34·B26-1을 M1 전 착수 조건으로 | 승인 초안 '재검토' 절 | **일치** |

---

## 5. 사실 대조(점검 (4), `7535799`, `C:/g72/repo`) -- 15건 모두 일치

1. HEAD `7535799`이다. `git diff --stat cd64170 HEAD`은 tools·redteam 31·P9 spec·design 20·`.ai`뿐이고 엔진은 0이다.
2. `mutate_changed.py`의 줄 번호는 `make_clone` 53·323, `_rmtree_force` 61·406, `_strip_doc` 74, `def_hash` 84, `changed_defs` 88·364, diff 314, cat-file 359, `base_src` 361, `modname` 362, `mid` 374, 출력 398·402·407이다.
3. `reachability.py`의 줄 번호는 `module_name` 47, `_refs` 69, `build_graph` 97, `SOURCE_GLOBS` 172, `_is_source` 175, `base_defs`/`new_defs` 224~231이다.
4. `source_lint.py`의 줄 번호는 `compare` 212, `len(` 검사 129(`module_text`), 호출 268, `_is_empty_dict` 168이다.
5. 캐시는 SR 2391·2530·7697 셋 모두 `: dict = {}`이다. `topology_library.py:248`은 `lru_cache` 데코레이터이고 254행은 주석이다.
6. `run_harness.py`의 422행은 `def run`, 427행은 `topology_file`, 446행은 `optimize_full_circuit_budget(topo, spec, …)` 인자 줄이다.
7. SD의 `__file__`은 1050·8973행에 있다. future 줄은 SR 35·SD 32·TL 24행이다. 엔진 4파일의 `global`·star import는 0이다.
8. `git grep setattr`은 0건이다. `monkeypatch.`는 `test_df36_instance_relpath.py`의 `chdir` 4건뿐이다.
9. `_SIZING_RECIPE`는 60·221·222·261·262행에만 나온다.
10. redteam의 마지막 케이스는 `31-v3-git-history`이다. `rt.py`의 vcase는 1351행, `observe`는 613행, 선택 관찰은 599~621행이다. `run_all.py`의 `observed_equals`는 98행이다.
11. M22는 86파일이다. 문자열 import는 10줄·6파일이고, 그중 1줄은 docstring이다(S7).
12. S11 대입은 14줄·8파일이다.
13. 계획 줄 번호는 517·526·532·533·534·549·601·674·686·839·842·843·991·1000·1018·1078이다. `00-common`은 103·431·435행이다.
14. `test_ic5` `_DOMAIN_TABLE`은 21키이다. `test_dup_w_calc.py:442`가 `sizing_recipe.py` 경로를 쓴다.
15. `import_layering.py --root .`은 exit 0이고 `present` = `{"stick_diagram": 7}`이다(E0 출력 키 확인). U-03 승인 기록은 0건이다.

`MP_ARGS` 배열(§6.3)은 그대로 실행된다. 인자 14개, 마지막 원소가 `{"optimizer": "theta_search.py"}`이고 `json.loads`도 성공한다. `--plan`·`--registry` 경로는 `HEAD`에 있고 `--split` 다섯 파일도 모두 있다.
세 spec card 머리는 `role_paths.parse_spec_card`로 통과한다. G1은 phase 0.5·red-green·gate_change yes, T0은 phase 3·test-only·approval 2, D0a는 phase 3·red-green이고 셋 다 절 11개다.

---

## 6. card 수·순서·V3 비용 추정(점검 (5), 승인된 N2 + G1 이동 제외 가정)

* card는 16건이다(m1). 순서는 타당하다: G1 → D0a → D0b → M1…M10 → T1 → F1 → F2, T0는 B26-1 뒤 M1 전.
  단 B1·B2를 고치기 전에는 M1부터 `check`가 실패한다. M 번호순은 ORDER 때문에 필요하다.
* V3(변이 수, **추정** -- 근거는 실측 구조):

| card | V3 대상 | 추정 변이 | 근거 |
|---|---|---|---|
| G1·D0a | `tools/**`는 `_is_source` 밖 | 0 | `mutate_changed.py:315` targets = 소스 `.py`만 |
| T0·T1 | test만 | 0 | 같음 |
| D0b | 레지스트리·계획·contracts test | 0 | 같음 |
| M1~M6·M8·M9 | 새 MOD 파일 = 옮긴 단위뿐(옮긴 def 제외), shim·SD는 def가 빠지기만 한다 | **0**(card마다 `defs` = `[]` 요구) | G6' 통째 이동 거부 0. 실행 비용은 복제·`build_graph`·`moved_defs`(참조 구현 7.9~15.6초)와 card마다 E-LIB·E-INST(Phase 2 E4 측정 약 16분)뿐 |
| (위험) 거부된 이동 | D-20으로 새 def 본문 전체 | def당 평균 약 33(15,677/473) | F7로 card를 고치는 경로라 실제로는 변이로 가지 않는다 |
| F1 | 줄 머리 import만 바뀜 | 0 | 엔진·하네스의 함수 안 엔진 import 0(AST 실측) |
| F2 | 파일 삭제(`--diff-filter=AM` 밖) + SD import 줄 | 0 | 같음 |
| **M10** | 새 진입점(본문 전체) + `run()` 바뀐 문장 | **약 70** | HEAD `run` 변이 71(실측). 변이당 인벤토리 = 새 E-INST test + 이름 과대 근사 60 → **수 시간~9시간 이상**(S3) |

* 정리: Phase 3의 V3 비용은 사실상 M10 하나에 몰려 있다. 나머지는 G1이 이동 제외를 할 때만 0이다. 그래서 G1 → M 순서가 비용상 필수다(F5).

---

## 7. 사용자 결정의 제시 방식(점검 (3))

* UD-5: (가)·(나) 비교표와 권고가 중립적이다. 다만 수치의 '27단계'는 26이다(S6).
* UD-0 기본값 D-1~D-21에 회로 해석은 없다. 모두 코드 배치·판정 절차다.
  다만 **기준 쪽 변경 두 건이 UD-0 안에 묻혀 있다**. 질문 문안에 드러내야 한다:
  * **D-9**: 계획 534행 "추적 파일 전부 갱신"의 예외이다. 추적 파일 7개(`.ai/verification/**` 스크립트 6개 + `probe_stage_partition.py`)는 F2 뒤 import가 깨진 채 남는다.
  * **D-17**: F1 oracle 'import 줄 외 동일'에 D군 대입 14줄 예외를 둔다.
  * **D0b의 N3.10 추가 개정 위임**(B4)도 같은 성격이다.
* D-19는 UD-0 행에 들어 있지만 오케스트레이터 요청대로 따로 묻는 것이 맞다. 근거를 정리한 결과는 S4를 보라.
* 뒤에 올 승인(T0·T1·F1 V5)은 착수 전 결정이 아니라는 설명이 맞다. T0 계약 10은 B26-1 계약 test(판정 기준 소유자 = B26-1 승인)를 고친다. 이 점은 T0 '결정 필요 항목'에 이미 적혀 있다.

---

## 8. 승인 질문 문안(오케스트레이터용 -- **B1~B4 반영 뒤** 올린다)

> **[Phase 3 design 승인 -- 4건]**
>
> **UD-0. design `30-module-split`(10모듈 분할) 승인**
> Phase 3에서 할 일은 네 가지입니다. ① `sizing_recipe.py`·`stick_diagram.py` 등을 계획 N3.10의 10모듈로 **본문을 바꾸지 않고** 옮깁니다(모듈마다 card 1건, 이동 전용 도구로 AST 해시 동일 확인). ② 재수출 shim을 거쳐 추적 파일의 import를 갱신합니다. ③ shim과 `sizing_recipe.py`를 지웁니다. ④ MOD10 진입점을 만듭니다. card는 16건입니다.
> 이 승인이 함께 덮는 문서 개정은 첨부 diff에 있습니다. 계획 N3.10 표(`load_topology`·`validate_theta_declaration_order` → MOD3 쪽, `optimize_full_circuit_budget`는 Phase 3 동안 MOD8), N3.12.3 test-only 목록에 T0·T1 추가, `00-common` 진입점에 `topology_path` 인자, `10-test-separation` §5.6의 '파일' 열을 설명으로 바꾸는 것입니다.
> 기준에 닿는 기본값 두 가지를 알려 드립니다. (a) 판정 기록 스크립트 등 추적 파일 7개는 기록 보존을 위해 갱신하지 않으므로, shim 삭제 뒤 import가 깨진 채 남습니다. (b) 모듈 속성을 덮어써 계측하는 probe 8개는 덮어쓰기 대상을 새 모듈로 옮기고, 그 대입 줄만 'import 줄 외 동일' 검사에서 뺍니다.
> 이동 도구가 B26-1·B34 병합 뒤 계획 표와 다른 배정을 새로 계산하면 →
> - **승인 (Recommended)**: 그 계획 표 diff를 다시 여쭙습니다.
> - **승인 + 계산 결과 위임**: 다시 묻지 않고 계산 결과대로 표를 고칩니다.
> - **수정 요청 / 보류**
>
> **D-19. `rail_declaration`(B26-1의 전원 선언 접근자)을 둘 모듈**
> - **(가) MOD2 `topology_authoring` (Recommended)**: N3.10 MOD2 '대표 대상'에 이름을 더합니다. 선언 형식 검사(`validate_*`)와 같은 곳이고, 다음 B37a의 `port_declaration`도 같은 곳에 둡니다. 계층 위반은 없습니다(MOD3의 `load_topology`가 아래 번호를 부름).
> - **(나) 규칙대로 MOD3 `circuit_state_graph`**: 유일한 호출자 `load_topology` 옆에 둡니다. 계획 표 개정이 필요 없지만, 스키마 검사가 MOD2와 MOD3에 나뉩니다.
>
> **UD-5. 게이트 변경 G1(옮긴 정의를 '새 정의'로 보지 않게 V3·V6·V7 수정) 승인과 방식**
> 지금 게이트는 바이트 그대로 옮긴 함수도 새 함수로 봅니다. 그래서 엔진 이동 card는 변이 약 1.6만 개 때문에 판정할 수 없습니다. 어느 방식이든 약화는 없습니다(합성 반례 51단계 중 거부 단계 전부 거부, 실제 엔진 통째 이동 거짓 거부 0).
> - **(가) 전역 이동 인식 규칙 (Recommended)**: 게이트 변경 1회로 끝나고, card마다 추가 승인이 없습니다. Phase 3 안에서는 이동 도구가 이관표와 한 번 더 대조합니다.
> - **(나) 승인 기록에 선언한 이동만 인정**: M card 8건마다 승인 기록이 1건씩 더 필요합니다. 선언 안의 우회(조건부 재정의 등)는 (가)와 같은 규칙으로만 막을 수 있습니다.
>
> **UD-1. U-03 -- 추적되지 않는 스크립트 `smoke_run_harness_session18_save.py`(`sizing_recipe`·`stick_diagram.save_instance_json` import)**
> - **(가) 깨지게 둠 (Recommended, 계획 기본안)**: 추적 파일만 갱신합니다.
> - **(나) 지금 저장소에 추가(추적)하고 F1에서 함께 갱신**
> - **(다) 삭제** -- 사용자 작업입니다.
