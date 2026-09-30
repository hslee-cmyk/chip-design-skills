---
id: 20260930-registry-grade-fix
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260923-u02-d-list
---
## 의도

design `20-dead-code-dup` v1.2 §3 REG·§7·§8 P7·§10 E0: 레지스트리 `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`를 Phase 2 결과에
맞춰 바로잡는다 -- (1) §7 'D -- 운영 경로 호출 0'에 있으나 실제로는 운영 경로에서 불리는 R-4 항목을 §7에서 빼고 맞는 등급으로 옮긴다
(§7 제목이 사실이 되게), (2) P5·P5b에서 지워지고 P6에서 옮겨진 이름을 §7에서 뺀다, (3) 남는 §7 항목마다 처리(보류와 담당 Phase)를
기계가 읽는 열로 적는다, (4) §2 개념별 정본 표의 중복 셀을 Phase 2 실측으로 고친다. 그리고 이 상태를 지키는 검사 도구 `reg_check.py`를
만든다(DoD E0). A = `skills/analog-gmid-design/assets`.

설계와 다른 두 가지(오케스트레이터 결정, 2026-09-30):
* **판정 유형**: design §8은 P7을 test-only(문서)로 적었지만 E0 도구가 code 커밋을 만들므로 red-green이다(P2 교훈 -- code 커밋이 있으면 test-only가 아니다).
* **도구 위치와 E0 판정식**: design §10 E0은 `tools/gates/reg_check.py`와 "§7 남은 집합 = U-02 승인표 '보류' 집합"을 적었다. 그러나 (a) `tools/gates/`는
  게이트 코드라 게이트 변경이 되고, 이 도구는 판정 게이트가 아니라 DoD 측정 도구다 -- P4 `engine_dup_scan`과 같은 `A/tests/tools/reg_check.py`에 둔다.
  (b) U-02 승인 기록(`20260923-u02-d-list`)은 '보류' 항목을 목록으로 적지 않았다 -- 그래서 E0을 "§7 모든 행이 엔진에 실재하고(삭제·이관 항목 0)
  `처리` 열이 '보류(Phase n)' 형식이며 §1 집계가 §7 행 수와 맞다"로 기계화한다. design §10 E0 문구를 같은 뜻으로 고친다.

**정본은 topology 무관이어야 한다**(사용자 원칙 2026-09-30): §2에서 정본(제안)으로 적힌 것 가운데 넷·소자·회로 이름이나 이름 집합 상수를 읽는
것은 정본으로 두지 않고 상태 칸에 그 사실과 백로그를 적는다(예: 레일 넷 집합 행 -- `_DEFAULT_RAIL_HI/_LO`는 넷 이름 리터럴, B26).

## 관찰 가능한 계약

1. **R-4 정정**: 운영 경로 호출자가 있는 `render_report`(`audit_current_forced.py`에서 호출), `gm_from_fT`(`sizing_recipe` 안 호출),
   `_optimize_theta_slsqp_block_coordinate`(`sizing_recipe` 안 호출), `SharedFingerWCandidate`(`stick_diagram` 안 생성)가 §7에 없고, §3~§5 중
   §0 사용 규칙에 맞는 등급 표에 호출자 근거(파일:함수)와 함께 있다.
2. **삭제·이관 이름 제거**: P5·P5b에서 지운 이름과 P6에서 `A/tests/tools/`로 옮긴 이름(`RegressionVerdict`, `_run_optimize_multistage_case`,
   `run_regression_case`, `find_interleaved_symmetric_splits`)이 §7 표에 없다. 이력은 spec card·판정 기록에 있으므로 레지스트리에는 남기지 않는다.
3. **처리 열**: §7 모든 표에 `처리` 열이 있고 값이 `보류(Phase <p>)`로 시작한다(`<p>`는 계획서 Phase 순서의 원소 -- 예 `3`, `4`, `6a`). 사유는 같은 행
   비고에 둔다. 예: `build_toy_lut`·`_invq_newton` -- workspaces 사용·엔진 docstring 인용(P6 보류), `check_multi_leaf_hub_parity` -- 엔진
   docstring 인용·IC5 목록, topology_authoring 행 -- 배선 승인 필요.
4. **§1 집계**: §1 표의 D 열이 §7 소절(파일별) 표의 행 수와 같다.
5. **§2 정본 표 실측 반영**: 최소한 다음 셀을 사실에 맞춘다 -- W 계산 행(정해진 VGS의 W = L·ID/IDu는 `size_transistor`와 다른 질문이라
   중복이 아니다, P4 실측; PMOS W 차이는 결함 후보 B24), union-find 행(같은 L 동치류와 다른 묶음을 같은 개념으로 세지 않는다, P4), 레일 넷
   집합 행(이름 기반 상수는 정본이 아니다 -- `supply_nets` 선언에서 읽는 경로가 정본 후보, B26), CMRR 행(telescopic 사슬 삭제, P5b 반영 확인).
   그리고 **§2 모든 행의 정본(제안) 칸**에 넷·소자·회로 이름 리터럴이나 이름 집합 상수를 읽는 함수를 정본으로 두지 않는다 -- 그런 함수는
   '정본 후보(<함수> -- <무엇을 이름으로 읽는지>, B26 해소 뒤 확정)' 형태로 적는다. 1차 시도 auditor 실측으로 해당하는 행: 전류미러 그룹
   (`true_current_mirror_groups` -- `_DEFAULT_RAIL_HI/_LO`), 노드 DC 전압(`propagate_node_voltages` -- 기본 인자 `rail_hi/rail_lo=_DEFAULT_RAIL_*`),
   MNA 소자 스탬프(`build_ac_network` -- `{"gnd": 0.0}`). §7 `DiodeStackMember`·`DiodeStack`의 처리 값은 비고대로 `find_diode_stacks`와 같은 Phase로.
6. **도구** `A/tests/tools/reg_check.py`(신규 시그니처 표): `check(registry_text, engine_names)`가 발견 목록을 돌려주고, `main(argv)`는
   `--registry <레지스트리 경로> --root <저장소 루트>`로 엔진 정의 이름(`A/*.py` 최상위 def·class와 클래스 메서드 `Class.method`,
   `workspaces/run_harness.py` 최상위)을 AST로 모아 판정한다. 발견을 한 줄 JSON(`{"rule", "section", "name", "detail"}`)씩 출력하고 발견 0이면
   exit 0, 1개 이상 1, 입력 오류(없는 파일·§7 없음) 2. 규칙:
   * `stale`: §7 표 첫 칸의 백틱 이름(메서드는 `Class.method`)이 엔진 정의 이름에 없다.
   * `disposition`: §7 표에 `처리` 열이 없거나, 값이 정규식 `^보류\(Phase [0-9]+[a-z]?\)`에 맞지 않는다.
   * `count`: §1 표의 파일별 D 열 값과 §7 해당 소절 표의 행 수가 다르다(소절 제목의 괄호 수도 같아야 한다).
   병합본 레지스트리에 `main`을 돌리면 exit 0(발견 0).
7. 엔진 소스·다른 test는 바뀌지 않는다(레지스트리는 문서, 도구는 `A/tests/tools/`).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `reg_check` | `*` | 신규 모듈 `A/tests/tools/reg_check.py` |
| `reg_check` | `check` | `def check(registry_text: str, engine_names: set) -> list` |
| `reg_check` | `main` | `def main(argv: list) -> int` |

## 판정 유형 근거

red-green: 도구가 base에 없어 계약 6의 test가 base에서 ImportError(red), base 레지스트리는 `stale`·`disposition`·`count` 발견이 있다(삭제·이관 이름 잔존,
처리 열 없음). code 커밋(도구 + 레지스트리 정정)을 병합한 병합본에서 green.

## oracle 종류와 출처

(a) 구성 입력: 규칙마다 합성 레지스트리 조각과 합성 엔진 이름 집합(발견해야 할 것·발견하면 안 되는 것) -- 기대는 계약 6의 규칙 문장.
(d) 실측 원자료: R-4 판정·§2 셀의 근거는 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/`의 인벤토리와 Phase 2 판정 기록(P4·P5·P5b·P6).

## 거부해야 할 입력

규칙마다 합성 조각 -- 엔진에 없는 이름이 §7에 있음(`stale`), `처리` 열 없음·`보류` 아닌 값·Phase 없는 값(`disposition`), §1 D 열과 행 수 불일치(`count`)
→ 발견, exit 1. 레지스트리 파일 없음·§7 제목 없음 → exit 2. 발견하면 안 되는 것: 백틱 없는 설명 칸의 이름, §7 밖 표의 이름, 메서드 `Class.method`가
엔진에 있는 경우.

## library 회로 적용 여부

해당 없음(문서·도구). 엔진 불변이라 E-LIB·E-INST는 base와 같다.

## 무동작 판정 입력(무발동 값)

엔진·library·다른 test 전부 -- 판정이 base와 같다.

## 재현할 수치

없음.

## 결정 필요 항목

없음(U-02 승인 1항 '유지·등급 정정(운영 경로에 살아 있는 9개 -- 레지스트리 §7 제목이 틀렸다)'과 '보류'). 설계와 다른 두 가지는 의도 절에 적었다.

## 재시도 기록

1차 시도(2026-09-30, test 351869a, code 8525f36, 판정 기록 25c53ce): V2 FAIL -- (1) 계약 5: §2 정본 칸에 이름 상수·리터럴을 읽는 함수 셋이 남음
(전류미러 그룹 `true_current_mirror_groups`, 노드 DC 전압 `propagate_node_voltages`, MNA 소자 스탬프 `build_ac_network`) -- 계약 5가 명시한 네 행 밖이었지만
의도 절의 원칙("정본은 topology 무관 -- 정본으로 두지 않고 상태 칸에 사실과 백로그")에 해당 (2) 계약 3: `DiodeStackMember`·`DiodeStack` 처리 Phase 4가
비고("`find_diode_stacks`의 판단을 따른다", 그쪽은 Phase 3)와 불일치. 나머지(R-4 정정·삭제 이름 제거·§1 집계·도구·red-green)는 PASS. 계약 5를 §2 전 행으로
명시하고 같은 id로 1부터 다시 한다. test는 1차 blob을 쓰되 1차 auditor V3 생존 변이 두 분기(§1에 §7 소절 파일 행 없음, §1 D≠0인데 §7 소절 없음)의
합성 케이스를 더한다.
