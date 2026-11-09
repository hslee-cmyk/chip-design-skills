# 계획 개정 독립 검증 -- gain-budget v6.30 (O-91: 규칙 갈래 처리기 이음매 DEC-102·card RB-1·(10)(f))

- 대상: worktree `wt/plan-o91`, 브랜치 `plan/o91`, 커밋 `97ae32b5`(본문)·`98fc3919`(머리말 version), base master `3e2e7606`.
- 변경: gb plan +29/−8, gb history +1. oracle 계획 변경은 없다.
- 입력: 사용자 결정 O-91(`user_decisions.md` 712행), `extension_seam_analysis.md`(§2·§4·§5).
- 방법: 읽기만 했다. git은 `git -C`로 show·diff·grep만 썼다. 인용은 모두 직접 다시 쟀다.

## 점수: 89 / 100 -- 필수 2건(측정과 계약 test가 실제로 거부하는지 보장)

---

## 1. O-91 (1)(2) 반영, 범위

| 결정 | 반영 자리 | 판정 |
|---|---|---|
| (1) 확장 단위 = `rule_branch`, 처리기 = 소유 블록이 부르는 순수 함수(소유 블록이 자기 WRITES로 씀), 같은 하위 패키지 고정 표 `MappingProxyType`, 미등록 = 지금 정지 그대로, 계약 test 7, 발동 회로 있는 소유 블록 하나부터, 첫 처리기 = S-OS2 일반형(`icm_config`, current_reuse), 구현은 IT-1+IT-2 통합 병합 뒤 | DEC-102 새 행 (1)~(6), DEC-59·DEC-76 끝 문장, N3.4 '처리기는 writer가 아니다', N3.8 'IT-2 후속', N6.1 RB-1 행, N6.25 card RB-1, N2.1 O-91 행 | 충족 |
| (2) (10)(f)를 보호 대상 문장 '지원 판정은 `device.unsupported`만, 원소 분류는 `device.element_class`만 읽는다 -- 같은 양의 둘째 계산 0'으로 | N6.6 (10)(f) 보호 대상 + 측정 (i)(ii), O-88·O-89 행 끝 정정 표시 | 충족(측정 꼴은 M1) |
| 원래 취지와 다름 표시 | Status·DEC-102·O-91 행에 '원래 취지와 다름, 승인 O-91 (1)' | 충족 |

**범위 넘침**
- N3.8 'IT-2 후속'의 옛 문언 '대체하는 같은 변경에서 그 code 삭제'를 바꿨다(3절). O-91 본문에는 없지만 DEC-102 (4)('미등록 = 지금 정지 그대로')의 필연적 귀결이다. history에 경위가 있다.
- RB-1 범위 3(`…_undeclared`를 조건부 등록)도 O-91 본문 밖이다. 하지만 design 41:726이 '같은 후속 card'라고 적었고, DEC-76 조건(발동 ≥ 1)을 걸었으므로 허용한다.
- 그 밖의 넘침은 없다.

## 2. DEC-102 원칙 점검

**writer 하나 유지: 맞다.**
- 처리기는 compute block이 아니고, 반환값은 소유 블록이 자기 WRITES로 쓴다.
- `E/core/writer_table.py:39-43`을 직접 확인했다. `previous = index.get((kind, field))`에서 다른 writer가 이미 있으면 `WriterPermissionError("필드 … 에 writer 둘")`을 던진다. 처리기를 별도 블록으로 만들면 실제로 거부된다.
- `E/core/compute_block.py:13`: 블록은 `Projection` 하나만 받고, 선언 밖 열은 읽을 수 없다. '처리기 READS ⊆ 소유 블록 READS'가 구조로 보장된다.

**`MappingProxyType` 함수 표가 graph 규칙 2 밖인가: 그렇다.**
- 구조 규칙 G(`tests/structure/README.md:45`)는 모듈 수준 가변 캐시를 금지하고, 통과 예(:134)에 `MappingProxyType({...})`이 있다.
- 규칙 C(:41)는 층 순서와 `__all__` 공개 API를 요구하므로, 소유 하위 패키지 안에 두는 것이 맞다.
- 표는 함수 참조의 정적 표라 계산값·사본이 아니다(graph 규칙 2 대상 아님).
- 처리기 code는 블록 코드 해시에 들지 않는다. `compute_block.py:23`은 블록 함수 code, 중첩 code, `__wrapped__`만 해시한다. 실행 사이 재사용은 `engine_code_fp`(`core/engine_code_fp.py:22`, 실행마다 `pipeline/stage_a.py:33`)가 끊는다. 맞다.

**기존 등록·디스패치 장치를 다시 쓸 것이 있는가**
- grep 결과(`MappingProxyType`, `registry`, `dispatch`, `handlers`):
  - 갈래 디스패치 장치는 없다. 근거 §2 '분기 = if/elif 인라인'과 같다.
  - 같은 **꼴**의 정본 선례가 있다: `E/metrics/registry.py:66-75`. 행 tuple `_ROWS`를 `_build()`가 돌며 이름 중복이면 `ValueError`를 던지고, `MappingProxyType(dict(sorted(...)))`를 만든 뒤 `_REGISTRY = _build()`로 모듈 적재 때 한 번 만든다(`metric_registry()`가 읽기 전용으로 돌려줌).
  - 이 표는 'metric 이름 → 결과 필드'라 개념이 달라 그대로 재사용할 대상은 아니다. 하지만 DEC-102 (3)의 '같은 키 둘은 모듈 적재 때 거부'와 같은 꼴이므로 선례로 인용하면 design이 새 꼴을 발명하지 않는다(→ N1).
  - `core/failure_classes.py:63`도 `MappingProxyType` 표를 돌려주는 선례다.

**'미등록 = 비트 동일 정지'는 시험할 수 있는가: 할 수 있다. 다만 실행 분리가 필요하다(→ M2).**
- 처리기 표는 소유 블록의 입력 버전(이름 + 블록 코드 해시 + 투영 지문)에 들지 않는다.
- 그래서 test가 같은 실행(`open_run` 하나)에서 '등록'과 '미등록'을 차례로 돌리면 문제가 생긴다. 둘째 호출은 같은 입력 버전이라 graph reuse나 S3 graft(실행 수명 색인)로 첫 결과를 그대로 받는다. 이러면 (c)·(d) 비교가 공허하게 통과할 수 있다.
- 운영에서는 표가 엔진 코드와 함께 고정이라 문제없다. test 꼴만 정하면 된다.

**계약 test 7의 건전성과 충분성**
- (a) 키 중복 거부, (b) 반환 필드 ⊆ WRITES·겹침 fail-closed, (c) 미등록 정지 비트 동일, (d) 비발동 회로 무동작, (f) memo 금지, (g) 손계산 오라클: 건전하다.
- **(e) 이름 금지의 정의가 정밀하지 않다(→ N3).**
  - '회로·소자·θ 이름 0'이라고만 적었다.
  - 이미 정밀한 정의가 있다. 구조 규칙 E(:43)의 이름 집합 = library `*.topology.json`의 파일 이름·`topology_name`·소자·수동소자·이상원 이름·단자 넷·`terminals`·포트 키·`supply_nets`이고, 문자열 상수가 **정확히 같으면** FAIL이다.
  - 그런데 이 집합은 library만 덮고 heldout 4회로는 빠진다. DEC-102 (5)(d)가 '13회로'를 말하므로 (e)도 heldout 같은 항목을 넣어야 일관된다.
  - θ 이름은 소자 이름에서 오므로 따로 정의할 필요가 없다. 태그 키는 규칙 I(:47) `FORBIDDEN_LOOKUP_KEYS`가 정의한다.
- **근거 분석 §4.2에서 빠진 두 항목(→ N2):**
  - #1 '등록 키는 기존 정지 code 상수 목록에 있는 것만': 갈래 이름 발명을 막는다.
  - #2 '반환 subject ⊆ 그 갈래가 발동한 subject': 처리기가 갈래와 무관한 key(다른 출력·포트)를 쓰지 못하게 한다.
  - 계획 (a)(b)에는 이 둘이 없다.

**만들면 배선(배치 제한): 성립한다.**
- DEC-102 (6)으로 소비 회로가 있는 소유 블록만 둔다. RB-1은 `icm_config` 하나다.
- 두 출력 모두 DC 경로인 하위 갈래(c)는 발동 0이라 만들지 않는다.
- `…_undeclared`는 library 발동 ≥ 1일 때만 등록한다.
- 다른 정지 자리 10여 곳에는 미리 깔지 않는다.

## 3. 작성자의 이탈 -- `icm_config_differential_output_structure`를 남김

- **필요성: 있다.** DEC-102 (4)는 미등록 정지가 지금과 '같은 예외·분류·code·detail'이어야 한다(비트 동일). 따라서 RB-1 뒤에도 그 code는 미등록 정지의 code로 살아 있어야 한다. 옛 문언 'code 삭제'와는 함께 설 수 없다. 일관된다.
- **DEC-76과 맞는가: 맞다.**
  - (c) 하위 갈래는 계산을 만들지 않는다. 처리기가 그 갈래에서 미등록과 같은 fail-closed를 내는 것은 '발동 0 갈래를 만들지 않음'과 맞다. 안전망은 계산 규칙이 아니기 때문이다.
  - 옛 문언의 취지('일반형이 들어오면 죽은 fail-closed code를 남기지 않음')는 유지된다. 그 code는 미등록 정지와 (c) 사유로 실제로 쓰이는 살아 있는 code다.
- 다만 code 하나가 '구조 미지원(미등록)'과 '두 출력 모두 DC(미구현 하위 갈래)'라는 두 사유를 함께 싣게 된다.
  - detail에 사유 구분(예: `("sub_branch", …)`)이 없으면 판정 기록에서 두 경우를 가르기 어렵다.
  - 그러나 detail은 '비트 동일' 조건에 걸려 미등록 쪽 detail은 바꿀 수 없다. (c) 쪽 detail만 구분 칸을 더할 수 있는지는 design 몫이다(관찰).
- 이 바꿈은 이전 승인 문언을 고친 것이다. Status에도 '원래 취지와 다름' 표시를 두고 승인 질문에 함께 올리기를 권한다(→ N5). 지금은 history에만 경위가 있다.

## 4. RB-1 범위·착수·완료 조건

- **O-68 (2)와 일치:** 닫힘 행 둘, 입력 CM = x, 출력 CM = CMFB, `kvl_sensitivity` k ∈ {1, 2}, `saturation_window`, margin 대상 = 입력 둘, 새 풀이기 0.
- **O-85 (1)·O-87 (1)과 일치:** 결합 판정, 갈리면 `icm_config_feedback_outputs_split`(O-87이 IT-2c에서 이 card로 옮긴 예약 이름).
- **gb N3.8 판정 문단과 일치:** (10)(f)의 비공개 술어를 부르고, 둘째 구현 0.
- **착수 조건: 맞다.** 선행 = IT-1 + IT-2 통합 병합이다. 소유 블록 `icm_config`와 S-OS2 fail-closed 갈래가 IT-2c에서 생긴다. design 개정 → gap → 구현 → gap(S-7) 순서도 맞다.
- **n_front = 0 미확인: 처리가 맞다.**
  - 완료 판정은 `icm_config`·창 필드 수준에서 한다. 완료 보고에 n_front를 다시 재고, 0이면 'front 끝 효과 미확인'으로 보고한다.
  - 완료 조건 (3) '바뀐 필드 값의 엔진 소비자 ≥ 1'이 '만들면 배선'을 덮는다. 커널 ICMR 선언 제약과 세 metric이 소비자다.
  - IT-0 값은 직접 확인했다: `M-I3/current_reuse_telescopic_ota/AB/n_front` = 0, `…/SIM/n_front` = 0, `OS/13/S-OS2_tuple_nonempty(current_reuse_telescopic_ota)` = 1(`e98d0b0f` 기록).
- **`…_undeclared` 발동 수: 이미 기록에 있는 것으로 보인다(→ N4).**
  - 계획은 'IT-0 기록에 칸이 없어 미확인'이라고 적었다.
  - 그런데 IT-0 측정 스크립트(`combine_it0.py:111`, `measure_it0.py:286·397`)는 S-OS2 대상(차동 출력) 회로를 되먹임 선언 꼴로 `tuple_nonempty`와 `empty_tuple`로 나누어 센다.
  - `()` = 미선언 갈래(gb N6.6 '`feedback.elements = []`의 측정 구성 갈래')이므로 `empty_tuple`이 바로 `…_undeclared` 발동이다.
  - 계획 자신도 같은 문단에서 `OS/13/S-OS2_empty_tuple(cnr_ota)` = 1을 인용한다. 그 칸에 cnr_ota(heldout, 단계 A에서 정지)만 있으면 library 발동은 0이다(추정).
  - '칸 없음'이 아니라 '그 칸 = heldout 1·library 0(추정), 착수 때 재확인'으로 적으면 계획 안 모순이 없어진다. 결론(지금 등록하지 않음)은 같다.

## 5. (10)(f) 새 측정

- **대상: 맞다.** 상수 이름 수가 아니라 성질을 잰다. (i) 지원 판정 식의 입력 = `device.unsupported`뿐이다. (ii) 분류 술어 입력 = `device.element_class`뿐이다. O-88의 실패(`device.pins` gate 추정이 옛 이름 계수를 통과)를 정확히 겨눈다.
- **실현 가능성: AST로 할 수 있다. 다만 'git grep'으로는 안 된다(→ M1).**
  - (i)은 `device.kind` 열에서 나온 값(`projection.column("device", "kind")`이나 그 dict에 묶인 이름)이 `In`/`NotIn` 비교나 `==` 사슬(`or`)로 집합·목록·tuple·상수와 비교되는 `ast.Compare`를 찾으면 된다. 허용 예외는 `element_class == ELEMENT_SOURCE`와 `and`로 묶인 `kind == CURRENT_SOURCE` 하나다.
  - (ii)는 `device.pins`에서 나온 값에 대한 멤버십(`in`)이나 `len` 검사를 분류 문맥에서 찾으면 된다. 단자 넷 조회(`dict(pins)["g"]` 같은 첨자)는 허용이다.
  - 둘 다 파일 하나(`icm_config.py`) 안의 단순 데이터 흐름이라 보수적 규칙으로 구현할 수 있다. 문자열 grep으로는 데이터 흐름을 볼 수 없으므로 '또는 `git grep`'은 측정이 되지 않는다.
  - **양성 대조가 없다.** 이 검사가 실제로 거부하는지 보이려면 red 변형 둘이 필요하다. (가) design 41 v1.12.7 둘째 커밋 꼴(pins gate 유무로 MOS 추정) (나) `kind in SUPPORTED_*` 꼴. 이 둘을 넣으면 FAIL이어야 한다. O-86 M1이 (10)(a)(ii)에 같은 요구를 넣은 선례가 있다.

## 6. 인용 재측정

| 인용 | 확인 | 결과 |
|---|---|---|
| `E/core/writer_table.py:39-43` | `previous = index.get(...)` → `WriterPermissionError("… writer 둘")` | 맞음 |
| `E/core/compute_block.py:13` | '블록 함수는 `Projection` 하나만 받는다(선언 밖 열은 읽을 수 없다)' | 맞음 |
| `E/core/compute_block.py:23` | '코드 해시 = 블록 함수 code 객체(중첩 code 재귀, `__wrapped__` 사슬 포함)' | 맞음 |
| `E/core/engine_code_fp.py:22` | `def engine_code_fp(engine_root=None):` | 맞음 |
| `E/pipeline/stage_a.py:33` | '엔진 코드 지문 … 실행마다 여기서 한 번' | 맞음 |
| `tests/structure/README.md:41`·`:43`·`:45`·`:47`·`:134` | C 층·공개 API, E 회로 이름 금지, G 가변 캐시 금지, I 회로별 정보 금지, G 통과 예 `MappingProxyType` | 모두 맞음 |
| design 41:726 | S-OS2 code `icm_config_differential_output_structure`, detail `(("outputs", 출력 넷 tuple),)`, '`…_undeclared`도 … 같은 후속 card' | 맞음 |
| design 41:734 (3) `kvl_sensitivity` | 734행에 `kvl_sensitivity` 있음(같은 계산 목록) | 맞음 |
| IT-0 `e98d0b0f` `.ai/verification/20261021-it0-baseline.json` | `S-OS2_tuple_nonempty(current_reuse…)` = 1, n_front AB·SIM = 0, `S-OS2_empty_tuple(cnr_ota)` 키 있음 | 맞음 |
| 머리말 `version: 6.30` | `98fc3919`로 6.27 → 6.30 | 맞음(history에 누락 경위 기록) |

## 7. graph 단일 정본 점검(별도 항목)

| 규칙 | 점검 | 결과 |
|---|---|---|
| 1 writer 하나 / 둘째 생산자 | 처리기는 writer가 아니고, 소유 블록 하나가 쓴다(`WriterTable` 변경 0). 갈래 재판정 금지, 다른 블록 양은 READS로만. RB-1은 `kvl_sensitivity`·`saturation_window`·판정 술어를 부르고 다시 쓰지 않는다 | 통과 |
| 2 새 cache·memo·사본 | 표 = 함수 참조 정적 표(값 아님). 계약 test (f)가 memo 0을 강제 | 통과 |
| 3 같은 정의 = 하나 | 판정 자리는 소유 블록 하나, 결합 규칙은 gb N3.8 한 곳 | 통과 |
| 4 참조 전달 | 처리기는 투영만 받음 | 통과 |
| 6 정본 자리 없으면 멈춤 | '새 양이 필요하면 처리기가 아니라 계획에서 필드와 writer를 정한다(S-7)' | 통과 |
| 입력 버전 경계(관찰) | 처리기 code와 표는 블록 입력 버전 밖이다. 운영에서는 `engine_code_fp`가 실행 사이를 끊어 안전하다. test에서는 같은 실행 안에서 표를 바꾸면 S3 graft·reuse로 공허해진다 | M2로 처리 |

## 8. 계획 / history 분리, 머리말

- history H1 'v6.30'에 다음이 다 있다: 경위 (1)(2), 고르지 않은 후보, N3.8 문언 변경 이유, 바꾼 옛 문장 원문, 미확인, 머리말 정정. 좋다.
- 계획 DEC-102 행에 근거 문장('이름으로 고르는 엔진은 WP-05·규칙 E·I·… 어긋난다', '규칙 2 위반이 아니다: …')이 길게 들어 있다. 규칙 판단에 필요한 정의 경계라 대부분 허용하지만, '원래 취지와 다름'의 경위 부분은 history 참조로 줄일 수 있다(→ N6).
- 머리말 `version: 6.30`을 맞췄고, Status 이전 판 v6.29를 '승인됨(O-90)'으로 고쳤다. 맞다.

---

## 필수 수정 (must-fix)

**M1. (10)(f) 측정을 AST로 고정하고 red 변형 둘을 넣는다.**
- 문언 예: '측정 = `icm_config.py`에 대한 AST 검사(보수적 규칙). red 변형 (가) `device.pins` gate 단자 유무로 MOS를 추정하는 식 (나) `device.kind`를 kind 튜플·집합과 멤버십 비교하는 식 -- 이 둘을 넣으면 FAIL'. '또는 `git grep`'은 뺀다.
- 원칙 점검:
  - '게이트는 실제로 거부하는지 먼저 확인'(사용자 원칙)을 따랐다.
  - 선례: O-86 M1이 (10)(a)(ii)에 양성 대조를 넣었다(계획 (10)(a) (가)(나)를 grep으로 확인).
  - grep으로는 데이터 흐름을 볼 수 없다. O-88 실패 꼴(pins 추정)이 바로 이름 grep을 통과했다(history 경위 (2)).
  - 새 필드·장치는 없다(test 규칙만).

**M2. 계약 test (c)·(d)는 비교하는 두 경우(등록·미등록, 등록 전·후)를 각자 새 실행(`open_run`을 따로, 같은 스냅샷 lineage 재사용 없음)에서 돌린다고 적는다.**
- 처리기 표와 처리기 code는 소유 블록 입력 버전 밖이다(`compute_block.py:23`). 같은 실행이면 graph reuse나 S3 graft가 첫 결과를 돌려주어 비교가 공허해진다.
- 원칙 점검:
  - graph 규칙 2(재사용 = graph reuse와 S3 graft 두 길)에서 재사용 경로를 확인했다(`compute_block.py` 판정 순서: 같은 lineage 재사용 → `donors.find` graft → 계산).
  - 새 cache나 입력 버전 칸을 더하는 해법(표 지문을 입력 버전에 넣기)은 core 변경과 새 장치라 제안하지 않는다. test 꼴만 정한다.

## 권장 수정 (nice-to-fix)

- **N1:** DEC-102 (3)에 등록표 꼴의 선례로 `E/metrics/registry.py:66-75`(행 tuple → `_build()` 중복 `ValueError` → `MappingProxyType`, 모듈 적재 때 한 번)를 인용한다.
  - 원칙 점검: `MappingProxyType`·`registry`·`dispatch`를 grep했다. 갈래 디스패치는 없고, 같은 꼴의 표는 `metric_registry` 하나다(개념이 달라 재사용 아닌 꼴 인용). 새 장치 발명을 막는다.
- **N2:** 계약 test에 근거 §4.2의 두 항목을 되살린다. (a′) 등록 키 ∈ 기존 정지 code 상수, (b′) 반환 subject ⊆ 발동 subject.
  - 원칙 점검: 근거 문서 §4.2 #1·#2에 있었는데 계획 (5)에서 빠진 것을 대조로 확인했다. 갈래 이름 발명과 무관 key 쓰기(writer 하나 취지)를 막는다.
- **N3:** (e) 이름 금지의 정의를 '구조 규칙 E 이름 집합(`README.md:43`)과 heldout 4회로 같은 항목에 정확 일치하는 문자열 상수 0, 규칙 I 태그 키 조회 0'으로 적는다. θ 이름은 소자 이름에서 오므로 따로 두지 않는다.
  - 원칙 점검: 기존 정의(규칙 E)를 grep으로 확인했다. 새 이름 집합을 만들지 않고 기존 정의에 heldout 범위만 맞춘다(13회로 = d와 일치).
- **N4:** RB-1 범위 3·미확인의 '`…_undeclared` 발동 수 = IT-0 칸 없음'을 고친다. 'IT-0 `OS/13/S-OS2_empty_tuple` = 그 발동 수(`()` = 미선언 갈래), cnr_ota(heldout)만 -- library 0(추정), 착수 때 재확인'으로 적는다.
  - 원칙 점검: '만들기 전에 기록부터 확인' 원칙이다. `combine_it0.py:111`·`measure_it0.py:286·397`의 칸 정의와 계획 자신의 `S-OS2_empty_tuple(cnr_ota)` 인용을 대조했다.
- **N5:** N3.8 'IT-2 후속'의 code 유지(옛 'code 삭제' 문언 변경)를 Status에도 '원래 취지와 다름(이전 승인 문언 변경)'으로 표시하고 승인 질문에 함께 올린다.
  - 원칙 점검: '원래 취지와 다른 판단은 반드시 보고' 원칙이다. 지금은 history에만 있다.
- **N6:** DEC-102 행의 '원래 취지와 다름' 경위 설명을 history H1 'v6.30' 참조로 줄인다. 규칙 경계(writer·규칙 2·규칙 C·코드 해시)는 남긴다.

## 승인 준비 상태

- M1·M2를 반영하면 사용자 승인을 요청할 수 있다. 문언 몇 구절이라 재검증 없이 같은 승인 차례에서 넣어도 된다.
- N5는 승인 질문에 함께 올리기를 권한다.

## 미확인

- U1: `S-OS2_empty_tuple` 칸이 차동 출력 회로만 세는지(=`…_undeclared` 발동과 정확히 같은 집합인지)는 측정 스크립트 전문을 읽지 않아 추정이다(N4).
- U2: (10)(f) AST 검사의 허용 예외(`kind == CURRENT_SOURCE`)를 데이터 흐름으로 구별하는 규칙의 오탐률은 실측하지 않았다.
- U3: (c) 하위 갈래에서 detail에 구분 칸을 더할 수 있는지(미등록 쪽 비트 동일 유지와 함께)는 design 몫이라 판단하지 않았다.
