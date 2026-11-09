# 계획 개정 독립 검증 -- gain-budget v6.28 · oracle-portability v0.6.17 (O-85)

- 대상: worktree `wt/plan-o85`, 브랜치 `plan/o85`, 커밋 `bdd13d5b`, base master `8c2357bc`. 4개 파일, +19/−5.
- 입력:
  - 사용자 결정 O-85(`user_decisions.md` 706행)
  - `design41_v1126_validation.md` §4 S-FB1(4.1~4.4)·R1·R2(142·170행)
  - `oracle_design_v039_validation.md` §4 DV-21
- 방법: 읽기만 했다. git은 `git -C`로 show·diff·grep만 썼다. 인용은 모두 직접 다시 쟀다.

## 점수: 90 / 100 -- 필수 1건(동적 측정의 공허함 방지)을 고치면 승인 요청 가능

---

## 1. O-85 (1)~(3) 반영 여부, 범위

| 항목 | 반영 자리 | 판정 |
|---|---|---|
| (1) DV-21: 두 출력 판정이 같을 때만 그 판정, 갈리면 정의 불능(사유 이름은 design), 0개, 생기면 계획부터 | gb N3.8 판정 문단 '**차동 출력**'(588행). O-67 (1) '차동 출력 회로의 측정 구성' 인용 구절 '(두 출력 판정이 같을 때 -- 갈리면 그 문단대로 정의 불능)'. 슬루 행은 '이 결합된 판정'을 읽는다고 명시. oracle N3.9 448행 인용, DR-25 | 충족 |
| (2) S-FB1: (10)(a) = 'DC 망을 만드는 자리에 루프 절단이 적용되지 않음' (i) 정적 (ii) 동적 (iii) 의미 = (10)(e), history 기록, 게이밍 기각 | gb N6.6 (10)(a)(1514행), history H1 'v6.28'('IT-0 정적 0은 이름이 달라 통과 -- 옛 측정은 이름을 쟀다', 게이밍 기각) | 충족(아래 M1) |
| (3) 지원 밖 원소(S1 `device.unsupported`) → 정의 불능, READS에 `device.unsupported`(둘째 계산 제거), code `icm_config_feedback_element_unsupported`, 오라클 인용 | gb N3.8 '**지원 밖 원소**', (10)(f) READS, oracle N3.9 '지원 밖 원소' 인용, DR-25 (2) | 충족 |

**(10)(f)에 더한 'grep으로 `icm_config.py`의 지원 kind 상수 참조 0'은 범위 안이다.**
- O-85 (3)은 'READS에 `device.unsupported`(**둘째 계산 제거**)'를 결정했다.
- R2(검증 170행)가 지적한 둘째 계산이 바로 'design (다)가 `s1_values` 상수 튜플로 지원 밖을 다시 판정'하는 것이다.
- 이 grep은 그 제거를 확인하는 완료 조건이라 결정의 집행에 해당한다. 새 결정이 아니다.

**그 밖의 범위 넘침: 없다.**
- oracle DR-25 (3) '`bias_not_gate_only`는 참조만, 바꾸지 않음'은 손대지 않는다는 선언이라 넘침이 아니다.

## 2. (10)(a) 실현 가능성

**(i) 정적: 호출 구문을 별칭·import 경로와 무관하게, docstring을 빼고 센다 -- AST로 건전하게 구현할 수 있다.**
- docstring과 주석은 `ast.Call`이 아니므로 AST 걷기에서 자동으로 빠진다.
- 별칭·경로 무관을 지키는 방법: 모듈마다 import해서, 모듈 전역 이름 가운데 순수 함수 객체와 `is`로 같은 것을 찾아 별칭 집합을 만든다.
  - 이렇게 하면 `from … import f as g`, 패키지 재export(`gmid_engine.authoring`), `mod.sub.f` 속성 경로가 모두 같은 객체로 풀린다.
  - 그다음 AST에서 `Call.func`가 그 별칭(Name 또는 Attribute 사슬)인 것을 센다.
- **남는 구멍(권장 N1):**
  - 함수를 값으로 넘기는 경우는 '호출 구문'에 잡히지 않는다(`h = f; h(x)`, `map(f, …)`, `partial(f)`).
  - 정적 조건을 '호출 구문'이 아니라 '**그 함수 객체의 참조(load)**'로 세면 이 구멍이 닫힌다.
  - 또 대상 범위를 엔진 소스로 정하고 `tests/`는 빼야 한다. 순수 함수의 단위 test는 '넷 자리에만'을 깨기 때문이다.
- (10)(f)(호출 자리 넷: `spec_elements`·`spec_views`·`icm_config`·`noise_plan`)와는 충돌하지 않는다.
  - (i)은 '그 넷 자리에만, `E/sizing` 전체·`ss_nodal`·`_helpers_nodal.py`에는 0'이라 (10)(f)의 넷을 허용 집합으로 정확히 받는다.
  - S-FB1의 측정 꼴 충돌(옛 `E/metrics` 0)이 해소됐다.

**(ii) 동적: code object로 센다 -- 실현할 수 있다. 다만 공허함 검사가 없다(→ M1).**
- 실행 환경은 Python 3.14라 `sys.monitoring`을 쓸 수 있다.
  - PY_START, PY_RETURN/PY_UNWIND로 구간 함수(`dc_writer_plan`·`run_kernel`·`seal_dc`의 `__code__`)의 깊이를 세면 된다.
  - 그 안에서 순수 함수 `__code__`의 PY_START를 센다. 이름 묶기와 무관하다.
  - `sys.setprofile`도 같은 일을 할 수 있다.
- 주의 1: `dc_writer_plan`·`seal_dc`가 `@compute_block`로 감싸져 있으면 구간 기준은 감싼 함수가 아니라 원 함수(`__wrapped__.__code__`)의 code다.
- 주의 2: graph reuse로 블록이 건너뛰어지면 그 실행에는 구간이 없다. 측정 실행은 reuse 없이(새 입력 버전) 돌려야 한다.
- **M1 -- 양성 대조(non-vacuity)가 없다.**
  - history 스스로 'IT-0 동적 측정은 래퍼가 호출을 못 봤을 가능성(측정이 공허함)'을 적었다.
  - 그런데 새 문언도 '구간 호출 0'만 요구한다.
  - 같은 실행에서 다음 둘을 함께 요구해야 측정이 실제로 거부할 수 있음을 보일 수 있다.
    - (가) 같은 계수기가 구간 **밖**의 호출 ≥ 1을 본다. 예: spec 로드의 `spec_elements`, 봉인 뒤 `icm_config`.
    - (나) red 변형: 구간 안에서 그 함수를 부르게 한 변형에서 계수 > 0.
  - 측정 실행에 쓸 입력도 정해야 한다. 예: 13회로 + (8)(b) 선언 되먹임 toy.
  - 이는 '게이트를 만들면 실제로 거부하는지 먼저 확인'(사용자 원칙)과 같은 요구다.

**(iii) 의미 판정 = (10)(e) 손계산 일치: 있다.**
- (10)(e)(저항 toy·Rf∥Cf toy, '선언 소자를 끊지 않은 봉인점 회로로 잰 창 = 손계산')를 그대로 인용한다.
- '`icm_config`의 호출은 끝점 식별만'도 적었다.

**(10)(f)와 남은 충돌: 없다.**
- 권장 N2: IT-2c 착수 조건 목록에는 이 (10)(a) 변경이 없다. design 41:812 L10 (a)의 '멈춤 S-FB1'과 IT-0 LC(`it0 spec:49`) 측정 꼴을 IT-2c card가 새 문언으로 바꾸도록 (iv)를 한 줄 두면 card 작성 때 빠지지 않는다.

## 3. DV-21 문장의 물리

결론('두 출력 판정이 갈리면 정의 불능')은 맞다. 근거 문구 '과잉 구속'은 정확하지 않다(→ 권장 N3).

- **닫힘을 더하는 경우**
  - 측정 벤치의 DM 닫힘은 입력 둘을 이상 원천으로 구동한다((in+ − in−) = −(Vop − Von), 입력 CM = x). 엔진에서는 닫힘 행 k개(Schur)가 입력 노드의 행을 대신한다.
  - 그러면 한쪽에 선언된 DC 경로(예: Rf o_a–in_a)는 그 원천이 구동하는 마디에 붙은 부하가 될 뿐이다. 연립은 풀리며, 모순되는 구속(풀 수 없는 과잉 구속)은 생기지 않는다.
  - 실제 문제는 **선언 DC 되먹임이 되먹임으로 작동하지 않는다**는 것이다. 이상 닫힘이 DM을 정하고, 선언 경로는 우회된다. 그래서 측정이 선언 구성의 ICMR이 아니게 된다.
  - 루프 이득으로 보면 한쪽 경로의 DM 루프(½βA_d)와 이상 닫힘(무한 이득)이 겹치는데, 닫힘이 지배한다. 검증 보고서의 '같은 DM 변수에 구속이 둘'은 이 뜻으로는 맞다. 다만 '과잉 구속'은 '해가 없다'로 읽힐 수 있다.
- **닫힘을 빼는 경우**
  - 선언 그대로 쓰면 한쪽 입력만 출력에 묶이고, 반대 입력은 원천이 구동한다.
  - 되먹임이 CM과 DM을 섞으므로 O-67 (1)이 전제한 대칭 차동 구성이 아니다. '비대칭 측정'이라는 표현은 맞다.
- **CMFB와의 일치**
  - 두 판정이 '없음'으로 같으면: DM·입력 CM은 닫힘이, 출력 CM은 CMFB가 정한다. 맞다.
  - 두 판정이 '있음'으로 같으면: DM은 선언 되먹임이, 입력 CM은 x 훑기가, 출력 CM은 CMFB가 정한다. 맞다.
  - 갈리는 경우만 위 두 문제가 생기므로 정의 불능이다. CMFB는 출력 CM만 정하고 DM·입력 DC는 정하지 않는다는 전제와 어긋나지 않는다.
- 권고: 계획 문장의 '과잉 구속' 구절을 '닫힘이 그 입력을 구동해 한쪽 선언 DC 경로가 되먹임으로 작동하지 않음(선언 구성이 아니게 됨)'으로 바꾼다. 결정 내용은 같고 근거 문구만 바뀐다(사용자 원문 O-85의 표현이라 바꿀 때 한 줄 보고 권고).

## 4. 인용 재측정

| 인용 | 확인 | 결과 |
|---|---|---|
| `E/graph/s1_values.py:29` | `SUPPORTED_SOURCE_KINDS = ("current_source",)` | 맞음 |
| `s1_values.py:129`·`:146`(요청 목록) | 129 `S1_STRUCTURE_WRITER = "s1_structure"`, 146 `STRUCTURE_WRITES`에 `("device", "unsupported")` | 맞음. 계획 본문에는 이 두 줄 인용이 없지만 사실은 맞다(writer·쓰기 목록) |
| `E/graph/s1_structure.py:69`·`:79` | `put("device", "unsupported", …)`(MOS / 수동·이상원) | 맞음 |
| `E/graph/CONTRACT.md:154` | `unsupported` 행, 값 = 분기 이름 | 맞음 |
| `E/graph/CONTRACT.md:394` | `*_kind_unsupported` | `s1_dc_conduction` | 지원 밖 원소 존재 | 맞음 |
| `E/sizing/writer_plan.py:129` | `def dc_writer_plan(projection):` | 맞음 |
| `E/sizing/kernel_run.py:65` | `def run_kernel(ctx, theta, parent, w_request, raise_on_violation):` | 맞음 |
| `E/sizing/seal.py:34` | `def seal_dc(snapshot, calls, lut, …):` | 맞음 |
| `docs/02-design/specs/20261021-it0-baseline.spec.md:49` | LC 행: (i) `git grep "_feedback_cuts\|input_terminal_nets" -- E/sizing E/search E/metrics` 0, (ii) 모듈 속성 래퍼 | 맞음(history 인용 그대로) |
| oracle design `5838cc67` 480행 | `dc_feedback_judgment_undefined` 오류 분류 | 맞음 |
| 같은 1609행 | DV-21 멈춤 | 맞음 |
| 같은 1640행 | 대응표 '차동 출력 두 출력 판정이 갈림 … 사유 미정(DV-21 멈춤)' | 맞음 |
| 같은 1813행 | §20 OP-5 행 | 맞음 |
| `spec_elements.py:28`·`spec_views.py:31`(history) | `from ._feedback_cuts import input_terminal_nets`(첫 검증 때 확인한 사실과 같은 자리) | 맞음 |

## 5. graph 단일 정본 점검(별도 항목)

| 규칙 | 점검 | 결과 |
|---|---|---|
| 1 writer 하나 / 둘째 계산 금지 | '지원 밖'은 S1 `device.unsupported`(writer `s1_structure` 하나)를 READS로 읽는다. kind 상수 목록 재판정은 grep으로 0을 강제한다 | 통과(개선) |
| 2 새 cache·슬롯·값 칸 | 0. 차동 결합 판정은 블록 안 지역 결합이고, 결과는 기존 `config` None + `undefined` code뿐이다 | 통과 |
| 3 같은 정의 = 하나 | 결합 규칙과 지원 밖 규칙은 gb N3.8 한 문단에 있다. oracle은 '다시 적지 않고 인용'. O-67 (1)·슬루 행도 '결합된 판정'을 인용한다 | 통과 |
| 4 참조 전달 | 해당 없음 | -- |
| READS 넓힘 | `device.unsupported` 하나(θ 무관 S1 필드, 입력 버전을 거침) | 통과 |
| 이름 | code 이름 `icm_config_feedback_element_unsupported`는 O-85 (3)이 정했다. DV-21 사유 이름은 design에 맡겼다 | 맞음 |

## 6. 계획 / history 분리

- 계획에는 규칙이 있다: 결합 규칙, 지원 밖 규칙, (10)(a) (i)~(iii), 게이밍 금지.
- history H1 'v6.28'과 oracle history v0.6.17에 경위, 물리 근거, 'IT-0 정적 0은 이름이 달라 통과', 바꾼 옛 문장 원문(N3.8 '이상 전압원', (10)(a) 옛 판정 원문, (10)(f) READS 원문)이 있다. O-85 (2)가 요구한 history 기록을 충족한다.
- 작은 점: gb 588행 차동 출력 문장의 '…때문이다'(물리 근거 한 문장)는 경위 성격이다. 짧아서 허용하지만, N3를 반영할 때 history 참조로 줄여도 된다.

---

## 필수 수정 (must-fix)

- **M1 (10)(a)(ii) 양성 대조.**
  - 같은 측정 실행에서 (가) 구간 밖 호출 ≥ 1을 보고 (나) 구간 안에서 부르게 한 red 변형에서 계수 > 0임을 함께 요구한다.
  - 측정 입력(예: 13회로 + (8)(b) 선언 되먹임 toy)과 reuse 없는 실행을 명시한다.
  - 옛 측정이 공허했을 가능성을 history가 스스로 적었으므로, 새 측정이 실제로 거부할 수 있음을 완료 조건으로 보여야 한다.

## 권장 수정 (nice-to-fix)

- **N1:** (i) 정적을 '호출 구문'이 아니라 '그 함수 객체의 참조(load)'로 센다. 값으로 넘기는 우회를 막기 위해서다. 대상 범위를 엔진 소스(`tests/` 제외)로 적는다.
- **N2:** IT-2c 착수 조건에 (iv)를 더한다: design 41:812 L10 (a)의 '멈춤 S-FB1'과 card 측정 행을 (10)(a) 새 문언으로 바꾼다.
- **N3:** DV-21 근거 구절 '과잉 구속'을 '닫힘이 그 입력을 구동해 한쪽 선언 DC 경로가 되먹임으로 작동하지 않음(선언 구성이 아님)'으로 정밀화한다. 결정 내용은 같고 근거만 바뀐다. 사용자 원문 표현이라 한 줄 보고한다.
- **N4:** (ii)의 구간 기준 code는 `@compute_block` 래퍼가 아니라 원 함수의 `__code__`라고 한 구절 적는다.

## 승인 준비 상태

- M1을 반영하면 사용자 승인을 요청할 수 있다. 문언 한두 구절이라 재검증 없이 같은 승인 차례에서 넣어도 된다.
- N3은 사용자 원문 표현을 고치는 것이라 승인 요청 때 함께 묻기를 권한다.

## 미확인

- U1: `dc_writer_plan`·`seal_dc`·`run_kernel`이 `@compute_block` 등으로 감싸져 있는지, 감쌌다면 `__wrapped__`가 있는지(구간 code 식별) 열람하지 않았다.
- U2: IT-0 동적 측정이 실제로 공허했는지(래퍼가 import 묶음 때문에 호출을 못 봤는지)는 실행으로 확인하지 않았다. history가 '미확인'으로 적은 것과 같다.
- U3: 엔진 닫힘 행(Schur k×k)이 입력 노드 KCL 행을 대신하는 꼴인지(3절 물리 설명의 엔진 쪽 전제)는 design 41 원문으로 확인하지 않았다. 오라클 벤치(이상 원천 구동)에서는 설명이 그대로 성립한다.

---

## 추가 검증 -- gain-budget v6.29 정오 (2026-10-21, `wt/plan-o89` `plan/o89` 커밋 `0796d9e4`, base master `e87092b3`)

- 입력:
  - 사용자 결정 O-88·O-89(`user_decisions.md` 709·710행)
  - `adopted_fix_audit.md` A2(13행)
  - design 41 `design/it2c-o79` HEAD `072561f5`
- 변경: gb plan 5줄, gb history 1줄. oracle 계획 변경은 없다.
- 읽기만 했다. git은 `git -C` + show·diff·grep만 썼다.

### 점수: 97 / 100 -- 필수 0건, 사용자 승인 요청 가능

### (1) (10)(f) READS 일곱, MOS 식별, 이상 전류원 제외, 'kind 상수 참조 0' 유지

- 새 문언: '`icm_config` READS에 S1 필드 일곱 `device.element_class`·`device.kind`·`device.pins`·`device.dc_nets`·`device.unsupported`·`node.is_rail`·`node.port_direction`(writer `s1_structure`, `E/graph/s1_structure.py:56-57·63-65·69·73-75·79·82`)'.
  - MOS 식별 = `device.element_class == ELEMENT_MOS`(`E/graph/s1_values.py:22`; 선례 `E/metrics/dc_metrics.py:40`·`E/metrics/achievability.py:108`). `device.pins`는 단자 넷 조회에만 쓴다.
  - 이상 전류원 제외 = `device.element_class == ELEMENT_SOURCE and device.kind == CURRENT_SOURCE`(`s1_values.py:24`·`E/sizing/s2_values.py:22`; 선례 `E/metrics/ss_circuit.py:19·57`).
  - 'ELEMENT_*·CURRENT_SOURCE는 분류·kind 어휘이고 지원 kind 튜플이 아님'과 '지원 밖 판정은 `device.unsupported`만 … `git grep`으로 `icm_config.py`의 지원 kind 상수 참조 0'이 유지됐다.
- 일곱 개 모두 O-88·O-89 (1)과 일치한다.

**인용 재측정**(`git show HEAD:…`, 모두 맞음):

| 인용 | 내용 |
|---|---|
| `s1_structure.py:63` | `put("device", "element_class", x.name, ELEMENT_MOS)` |
| `s1_structure.py:73` | `put("device", "element_class", x.name, element_class)` |
| `s1_structure.py:56-57·64-65·69·74-75·79·82` | 앞 검증 그대로(`is_rail`·`port_direction`·`kind`·`pins`·`unsupported`·`dc_nets`) |
| `s1_values.py:22` | `ELEMENT_MOS = "mos"` |
| `s1_values.py:24` | `ELEMENT_SOURCE = "ideal_source"` |
| `sizing/s2_values.py:22` | `CURRENT_SOURCE = "current_source"` |
| `metrics/ss_circuit.py:19` | `from gmid_engine.sizing import CURRENT_SOURCE` |
| `metrics/ss_circuit.py:57` | `elif not (element_class == ELEMENT_SOURCE and kind == CURRENT_SOURCE):` |
| `metrics/dc_metrics.py:40` | READS에 `("device", "element_class")` |
| `metrics/achievability.py:108` | `cls = dict(p.column("device", "element_class"))` |

### (2) 낡은 문언이 남았는가

- 두 계획 HEAD 전수에서 'element_class 불요'와 '`device.kind`로 충분'을 grep했다.
- **gb Status(11행)의 정정 설명 인용 2건뿐이다.** oracle 계획에는 0건이다.
- 그 밖의 잔존은 없다.

### (3) N3.8 판정 문단(590행)의 순수 함수 입력 구절을 그대로 둔 것

- **맞다.** 그 구절은 '`icm_config`는 S1 READS `device.pins`·`node.port_direction`에서 부르고'다. 절단 넷 순수 함수의 입력(소자 단자 넷 × 입력 포트 넷 집합)을 무엇에서 얻는지를 적은 것이지, 블록 READS 목록이 아니다.
- 절단 넷 계산에는 선언 수동소자의 단자(`device.pins`)와 입력 포트(`node.port_direction`)만 필요하다. 원소 분류(`element_class`)는 이 함수의 입력이 아니다. BFS의 MOS·이상원 구분에만 쓰이고, 그것은 (10)(f) READS 목록이 정한다.
- 원칙 점검: 블록 READS 목록의 정본 자리를 grep했다. 계획에서는 (10)(f) 한 곳뿐이고, oracle 계획은 이 목록을 인용하지 않는다(history 기재와 같음). 두 자리에 목록을 두면 사본이 생기므로, 그대로 두는 것이 graph 규칙 3에도 맞다.

### (4) design 41 `072561f5`(41:731/734/812)와 계획의 일치

- **731행 READS:** S1 필드 `("device", "element_class")`·`kind`·`pins`·`dc_nets`·`unsupported`·`node.is_rail`·`node.port_direction`. 일곱 개와 순서가 같고 출처 주석('`device.element_class`는 v1.12.7 셋째 커밋(O-88, MOS 식별)')이 있다. **일치.**
- **734행 (가)·(나):**
  - 입력 = '블록 READS의 S1 필드 일곱', 줄 번호 `56-57·63-65·69·73-75·79·82`로 계획과 같다.
  - 이상 전류원 = `element_class == ELEMENT_SOURCE and kind == CURRENT_SOURCE`(선례 `ss_circuit.py:57`, import `:19`, 정의 `s2_values.py:22`).
  - MOS = `device.element_class == ELEMENT_MOS`(`s1_values.py:22`; writer `s1_structure.py:63·73`; 선례 `dc_metrics.py:40`·`achievability.py:108`).
  - `device.pins`는 단자 넷 조회에만, `MOS_TERMINAL_NAMES` 공개 export 사용. **일치.**
- **812행 L10 (i):**
  - READS 일곱 단언과 '`icm_config.py`의 지원 kind 상수 참조 0(`MOS_KINDS`·`SUPPORTED_PASSIVE_KINDS`·`SUPPORTED_SOURCE_KINDS` 모두, 예외 없음 -- 계획 (10)(f))'.
  - 'MOS는 `element_class`(원소 분류 어휘라 지원 kind 상수 아님)', '이상 전류원 술어, `CURRENT_SOURCE`는 kind 어휘'.
  - **일치.** design이 지원 kind 튜플 셋을 이름으로 적었는데, 계획의 '지원 kind 상수'와 같은 뜻이다.

### (5) graph 단일 정본 점검(별도 항목)

| 규칙 | 점검 | 결과 |
|---|---|---|
| 1 writer 하나 / 둘째 계산 | MOS·이상원 분류는 S1 정본 필드 `device.element_class`(writer `s1_structure` 하나)를 읽는다. kind 문자열로 분류를 다시 추정하던 '불요' 문언을 없앴다 | 통과(개선) |
| 2 새 cache·슬롯·값 칸 | 0 | 통과 |
| 3 같은 정의 = 하나 | READS 목록 자리는 (10)(f) 하나. design 731·734·812가 같은 목록 | 통과 |
| READS | `device.element_class` 추가(θ 무관 S1 필드, 입력 버전을 거침) | 통과 |
| 관찰(백로그 후보) | 이상 전류원 술어 `element_class == ELEMENT_SOURCE and kind == CURRENT_SOURCE`가 `ss_circuit.py:57` 등에 이미 있다(design 734: `current_basis.py:90`·`kernel_context.py:80`도 같은 술어). `icm_config`가 같은 꼴을 하나 더 쓴다 | 규칙 위반 아님 -- 저장 값이 아니라 같은 상수로 쓴 판정 식이고 선례를 따른다. 공용 helper로 묶을지는 O-89 백로그 A4('current_source' 리터럴 3중)와 함께 다룰 일 |

- 원칙 점검(관찰):
  - '이상 전류원 여부'를 담는 기존 S1 필드나 공용 helper가 있는지 확인했다. design 734('재사용 helper는 없고 같은 술어가 … 각자 같은 상수로')와 `ss_circuit.py:57` 실측 모두 없음이다.
  - 새 필드를 만들면 사용자 결정 없이 graph 필드를 더하게 된다. 그래서 수정안으로 내지 않고 백로그 관찰로만 둔다.

### (6) 계획 / history 분리

- 계획에는 규칙만 있다: READS 일곱, MOS·이상원 술어, 상수 구분 한 구절. N2.1 O-88·O-89 (1) 행이 있다.
- history H1 'v6.29'에는 다음이 있다.
  - 경위: 검증자 문구를 정본 필드 확인 없이 옮긴 것, design·계획 불일치, S-7.
  - N3.8 구절을 그대로 둔 이유, oracle을 바꾸지 않은 이유.
  - 바꾼 옛 문장 원문.
- 맞다.

### 결론

- **필수 수정: 없음.**
- **권장:** 없음. 위 관찰 하나는 백로그 A4와 묶을 것.
  - 원칙 점검: 수정안을 내기 전에 정본 필드(`device.element_class`), 선례(`ss_circuit.py:57`), 계획 안 READS 목록 자리(grep 1곳)를 확인했다. 새 필드·사본 제안은 하지 않는다.
- **사용자 승인 요청 가능.**
