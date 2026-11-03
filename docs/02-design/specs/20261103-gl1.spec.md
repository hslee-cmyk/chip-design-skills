---
id: 20261103-gl1
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
---

> **[상태 2026-11-04] design 승인(O-226 위임 A-29), 독립 검증 `wt/_drafts/evidence/2026-11-04/gl1_validation.md` G1·m1·m2·m4 반영. 착수 = `design/gl1` master 병합 + 순서 0 커밋(이 파일과 interface card) 뒤. 권고 R-G1~R-G4 = 위임 A-28 채택. ⑩ 결정 모순 점검은 안 함(O-225).**
> 줄 번호 = master `7620f5ee`(design v1.16.3 병합본, 계획 v6.38.8; design 40의 §2.4.11 뒤 줄은 `design/gl1`에서 밀린다). 엔진 `.py`는 `c0b41eee`와 같다(`git diff --name-only` = `CONTRACT.md` 넷뿐). `E/` = `skills/analog-gmid-design/gmid_engine/`, `S/` = `E/tests/structure/`, `P:` = gain-budget 계획, `D40:` = design 40. 판정 기록 자리 = `.ai/verification/20261103-gl1.json`. interface card 자리 = `docs/02-design/specs/20261103-gl1.interface.md`(같은 폴더 `interface_card_draft.md`).

## 착수 조건

| # | 무엇 | 왜 막나 | 처리 |
|---|---|---|---|
| G-1 | **GL-1 design 절 병합**: `design/gl1`(승인 A-29) | 계획 P:1328·P:1361이 design → gap을 card 앞에 둔다. 검증 끝남 | 오케스트레이터 master 병합 |

사용자 몫 없음.

## 의도

N6.3 '엔진 코드를 바꾸는 변경 단위는 (a)(b) green'을 판정할 검사가 없다. GL-1은 그 두 검사와 기준선 래칫, 공유 호출 감사 도구를 만든다. 이것이 있어야 다음 엔진 card부터 graph 단일 정본 확인이 '판정 불능'이 아니게 된다(P:1514).

사용자 결정: O-182 Q-GL1 (가1)(검사 전용 card, 기존 위반 래칫), O-183 표 #10(감사 도구는 GL-1), O-225(13회로 변화표 유보), O-226(위임), 위임 A-6(공통 선행 맨 앞), 위임 A-28(R-G1~R-G4). 승인 사실은 근거가 아니다(O-208).

**변경 종류**: 엔진 동작 불변(P:2577 '엔진 동작 변경 없음'). N6.3 표에 맞는 행이 없다. 결정성 행만 적용하고, 동작 쪽은 엔진 소스 diff 0으로 판정한다.

## 관찰 가능한 계약

계약 전문 = interface card. 요약:

1. **G 확장 lint**: `check_g8`이 design 40 §2.4.10 ① 표 일곱 행(kind 여덟)과 §2.4.6 클로저 호출(kind 하나, R-G1)을 거부한다(interface §1). 허용 모듈 14개 밖은 예외 없음.
2. **값 타입 위치**: `check_value_types`가 ② 주석·대입을 거부한다. 타입 목록은 AST로 frozen dataclass 전수에서 모은다. 등록부를 두지 않는다(interface §2).
3. **래칫**: 키 = (kind, path, detail), 줄 번호 무관. 기준선 밖 추가·수 증가 → 진짜 트리 test red. 줄임은 red 아님(interface §3).
4. **감사 도구**: 정의 모듈 해석(재수출 포함), 자리별 인자 잎, 쌍 분류 B·not_B·D, `--touching`으로 N6.3 (ii) 범위, 정적 한계 기록(interface §4).
5. **fail-closed**: 기준선 파일 없음·형식 오류는 실패. 도구 입력 오류는 종료 코드 2. skip·xfail 없음.
6. **결정성**: lint 결과 순서 고정, 기준선 바이트 동일, 도구 산출물 넷 바이트 동일(다른 `PYTHONHASHSEED`).
7. **엔진 불변**: 이 card 커밋들의 diff에서 `E/` 중 `tests/` 밖 변경 0, `tools/` 변경은 `tools/audit/` 새 파일 하나뿐. 엔진이 새 이름을 import 0.

## 재작성 범위

(엔진 인용 용도 = 재작성 범위와 lint 대상 구문뿐, 원칙 8. 엔진은 고치지 않는다.)

| 파일 | 주체 | 범위 |
|---|---|---|
| `S/structure_checks.py` | code | 부분: `check_g8`, `check_value_types`, `G8_ALLOWED_MODULES`, `baseline_doc`, `dump_baseline`, `load_baseline`, `ratchet`, `RatchetResult`. 기존 `_mutable_value`, `_module_level`, `engine_files` 재사용. `copy_audit` 면제는 적용하지 않는다(design 40 §2.4.10 '이 밖은 예외 없음'). `check_g` 변경 0 |
| `tools/audit/scan_shared_calls.py` | code | 신규. 근거 스크립트 `wt/_drafts/evidence/2026-10-29/shared_pure_fn_audit/scan_shared_calls.py`의 해석 부분을 옮기고, 엔진 실행(`_module_map` exec)을 뺀다. 인자 잎·쌍 분류를 더한다 |
| `S/README.md` | code + test | 검사기 행(code), 픽스처·test 행(test) |
| `S/fixtures/rule_g8/**`, `rule_vt/**`, `shared_calls/**`, `S/test_g8_lint.py`, `S/test_value_types_lint.py`, `S/test_g8_baseline.py`, `S/test_scan_shared_calls_tool.py` | test | 신규 |
| `S/g8_baseline.json` | **audit** | 신규(판정자가 병합본에서 생성, R-G2) |

역할 표지: `S/structure_checks.py`는 앞 card에서 test 역할이 썼다(`e776cdf5`, `686a0c26`). 그때는 검사기가 부속이었고 이 card에서는 검사기가 피검물이다. 그래서 code 주체가 쓴다(WP-13). `agents/gmid-code-author.md` 경로표(폐기된 N3.12.2 인용)에 이 자리가 없어 브리핑에서 명시한다. 정의 파일 자리는 D40 §2.4.10 '구조 규칙 A~K의 정의 파일'에서 왔다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `structure_checks` (`S/`, fixture `checks`) | `check_g8` | `def check_g8(root: Path) -> tuple[int, list[Violation]]` |
| `structure_checks` | `check_value_types` | `def check_value_types(root: Path) -> tuple[int, list[Violation]]` |
| `structure_checks` | `G8_ALLOWED_MODULES` | `tuple[str, ...]` |
| `structure_checks` | `baseline_doc` | `def baseline_doc(violations, record_id, base_commit) -> dict` |
| `structure_checks` | `dump_baseline` | `def dump_baseline(doc) -> bytes` |
| `structure_checks` | `load_baseline` | `def load_baseline(path) -> dict` |
| `structure_checks` | `ratchet` | `def ratchet(violations, doc) -> RatchetResult` |
| `structure_checks` | `RatchetResult` | 불변 값(`new`, `stale`) |
| `tools/audit/scan_shared_calls.py` | CLI | `--engine <dir> --out <dir> [--touching <상대 경로> ...]` |

새 이름 충돌 0: 위 이름과 `test_g8_lint`, `test_value_types`, `test_g8_baseline`, `test_scan_shared_calls`, `g8_baseline`을 `E/`, `tools`, `docs/02-design/specs`에서 `git grep` = 전부 0건. `tools/audit` 없음. test glob: `rglob("test_*.py")`는 규칙 H(`structure`는 교차 폴더 `CROSS_CUTTING_TEST_DIRS`), json glob은 `*.topology.json`, `*.sizing_spec.json`뿐이라 `g8_baseline.json`과 안 겹친다. `engine_code_fp`는 `tests`를 뺀다(`core/engine_code_fp.py:16`).

## graph 단일 정본

* 새 graph 필드 0, 블록 입력·출력 변경 0, 엔진 코드 변경 0. 소유표 행 추가 0.
* 새 cache·memo·sctx 슬롯·결과 값 칸 0. `g8_baseline.json`은 설계 값이 아니라 검사 기록이고 엔진이 읽지 않는다.
* 같은 입력 재계산 래칫: 새 B 0, 이 card 배정 B 없음. 도구는 이 래칫의 측정 수단이다. 기준선(`shared_pure_fn_audit.md` §2.1)은 이 card가 바꾸지 않는다.
* 소유표 대조(c), G-10(d): 건드린 회로 0이라 '대상 없음'(증거 = 엔진 diff 0).
* **표지**: ②는 frozen dataclass 본문을 뺀다(design 문언). `EvalResult`는 frozen이라(`facts_master_summary.txt`) 결과 객체 값 칸은 ②가 못 잡는다. 그 자리는 소유표 대조 (c) 몫이다.

## 소비자

| 새 def·도구 | 소비자 |
|---|---|
| `check_g8`, `check_value_types`, `load_baseline`, `ratchet` | `S/test_g8_baseline.py` 진짜 트리 test. 매 변경 뒤 전체 test(N6.3)로 병합 순간 배선된다 |
| `baseline_doc`, `dump_baseline` | 이 card와 이후 card 판정자의 기준선 생성·줄임 명령(§10.4 행) |
| `tools/audit/scan_shared_calls.py` | N6.3 '같은 입력 재계산 0' (iv): 판정자 측정(§10.4 행). 첫 소비 = 다음 엔진 card(IT-1 + IT-2) 판정 |

엔진 소비자 0은 정상이다(엔진 밖 검사 도구). 오케스트레이터는 이후 audit 브리핑에 §10.4 행을 넣어야 소비가 실제로 일어난다.

## 판정 유형 근거

red-green. red = 새 함수·도구 부재(`AttributeError`, 도구 종료 코드 ≠ 0 단언). 계획이 base를 '검사 없음 -- red'로 적었다(P:2575 (1)). 새 함수라 허용(N3.12.3 순서 3). 키워드 추가 `TypeError`는 쓰지 않는다.

'거부한다'를 공허하지 않게 하는 추가 증거(memory '실제로 거부한다'): 판정자가 격리 복제본의 엔진에 kind마다 위반 한 줄을 넣어 `ratchet.new`가 그 키로 늘어남을 본다.

**다리 상태**(N6.3 (ii), 어휘 둘뿐).

| 다리 | 상태 | 증거 |
|---|---|---|
| 정의 toy | 있음 | interface §1~§4 |
| 봉인 불변식 | 대상 없음 | 엔진 소스 diff 0 |
| SPICE oracle | 대상 없음 | 엔진 소스 diff 0, `git grep`으로 엔진 안 새 이름 소비 0 |
| 변화표 | 대상 없음 | 엔진 소스 diff 0이면 값 변화 0 |

**판정 기록 문언**(N6.1 측정 게이트 표 대조). 표 머리는 GL-1을 범위에 넣고 '각 card 13회로 변화표' 행은 'base sha와 미완료(보류 다리)'를 적는다. 'SPICE 다리' 행의 card 목록에 GL-1은 없다. 네 다리는 N6.3에서 동작 변경 card의 것이고 P:2577은 '엔진 동작 변경 없음'이다. 그래서 **base sha는 `base_commit`에 적고, '미완료(보류 다리)'는 적지 않고 위 '대상 없음'을 적는다**(R-G3). 엔진 소스 diff가 0이 아니면 이 판정은 무효이고 FAIL이다. 스키마(`_schema.json`)에 보류 칸이 없어 상태는 `checks.V2.basis`와 `reproduced_numbers`에 적는다.

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 합성 입력. 픽스처 소스를 손으로 읽어 기대 목록을 쓴다. 피검 함수로 기대값을 만들지 않는다. 진짜 트리 기준선은 기대값이 아니라 기록이고 판정자가 만든다.

## 거부해야 할 입력

- 경계: 허용 모듈과 같은 파일 이름의 다른 폴더, 바로 옆 불변 값(`tuple`·`frozenset`·`None`), 지역 dict, 데코레이터 대 호출형 `lru_cache`, `lru_cache(...)(f)` 한 건, 중첩 함수·매개변수를 넘긴 `memo.call`.
- 같은 키 여러 건(`count`), 첫 줄·끝 줄 위반, 빈 트리.
- 기준선: 파일 없음, 형식 오류 전 항목(interface §3), 기준선 밖 키 하나, 같은 키 수 +1.
- 도구: interface §4 종료 코드 2 입력 전부.

## library 회로 적용 여부

회로를 돌리지 않는다. 구조 검사는 회로와 무관하다. library 13 변화표·SPICE = 대상 없음(위). held-out 0개 -- A' 일반성 판정 정지(이 card 무관). 회로·소자 이름은 검사기·도구에 0.

**병합 때 연기 시험**: P:1427 '유지하는 것' 선택 기준 (i)을 지나는 회로가 없다(엔진 코드 경로 변경 0). 규칙대로 toy로 대신하고 사유를 판정 기록에 적는다.

## 무동작 판정 입력(무발동 값)

`S/fixtures/rule_g8/good`, `rule_vt/good`에서 위반 0. 줄 번호만 밀린 위반 목록에서 `ratchet` 둘 다 빈 tuple. 기존 규칙 A~M test 결과 불변.

## 재현할 수치

판정 기록 값만 인용(숫자를 박지 않는다): kind별 기준선 행 수·위반 수, 기준선 `id`, 병합본 `new`·`stale` 수, 도구 산출물 sha256 2회, 감사 도구 class별 callee 수와 `limits.json`, 전체 test 통과·실패 수.

참고용 시제품 값(**기준선 아님**, 근거 = `facts_master_summary.txt`, `facts_master.jsonl`; 판정자에게 주지 않는다): 허용 밖 attr 59건 13파일, cached_property 3, default_factory 4, id 2, 모듈 수준 값 타입 10, frozen dataclass 335개.

## 결정 필요 항목

사용자 결정 필요 없음. 권고 넷은 부록 B.

| 항목 | 물리 결정자 | 식·원문 | 실측 | 판정 |
|---|---|---|---|---|
| 전부 | 없음(검사 도구, 값·봉인 무관) | 해당 없음 | 부록 B 경로 | 맞음 |

## 원래 취지와 다름

1. **`g8_memo_lookup_form` 추가**: §2.4.10 표는 `memo.call`만 적는다. as-built에 `memo.call` 호출이 0이라 그대로면 공허하다. §2.4.6 '`lookup`은 없앤다'를 근거로 기존 자리를 래칫한다(R-G1).
2. **기준선 소유 = 판정자, stale은 red 아님**: 계획은 소유자를 정하지 않았다(R-G2).
3. **'각 card 미완료' 문언을 GL-1에 안 씀**: R-G3.
4. **감사 도구의 자동 판정 범위가 좁다**: N6.3 (iv) '인자가 읽는 graph 필드를 대조해 B 분류'를 자동 확정으로 읽으면 못 미친다. 정적으로 안 풀리는 자리는 D이고 판정자 손 분류다(R-G4).
5. **§2.4.10 ③ SC-a·SC-b lint, ④ 동적 짝은 범위 밖**: N6.37은 ①②만 적는다. 표지만 한다(부록 C).
6. 공통 선행 15 → 16 card(A-6, 이미 기록).

## 절차

(DEC-86 넷, 정본 N6.3)

1. 코드 작성 주체와 test·기대값 작성 주체 분리(WP-13).
2. 깨진 test·기준 약화는 숨기지 않고 보고(`broken_tests`, `criteria_weakened`, `retired_tests`).
3. 변경당 커밋 1.
4. 매 변경 뒤 새 test 체계 전체 실행. 코드 단계 기대 red = `test_rule_g8_baseline_ratchet` 하나.

* 판정 기록: 독립 검증자, `.ai/verification/20261103-gl1.json`(`_schema.json`). `approvals` = 빈 배열. 구현 뒤 design ↔ 구현 gap.
* 흐름 = N3.12.3 순서 1~6 역할 분리(폐기된 gate·push 절차 제외, 앞 card 관행). 순서 0 커밋 = spec card + interface card. 브리핑 = `briefs.md`.

## 작성 전 실측

(스크립트·결과 = 같은 폴더. 엔진 import·실행 0, O-225 '(나)'.)

1. 사실 재측정: `measure_facts.py master`, `measure_facts.py it12`(`integ/it12` `b9351eac`), `measure_b_trace.py master`. **안 잼**: 전체 test 실행, 진짜 구현, 기준선.
2. 엔진 인용 용도: 재작성 범위, lint 대상 구문(`memo.lookup`, `.column`, `.value`)뿐. 자리·이름은 design 문언과 원칙에서 유도했다.
3. 이름 충돌: 0(위 '신규 시그니처').
4. 원칙의 계약화: fail-closed = 계약 5, 엔진 불변 = 계약 7.
5. 쓰기 경로: 역할 표지 참조.
6. 계획서 소비자: 지우는 이름 0.
7. 미배선: 소비자 표. 새 def 전부 호출자 ≥ 1.
8. 기존 test: `generality/conftest.py`가 같은 모듈을 읽고 `check_a`·`check_b`·`library_names`만 쓴다(변경 없음). `integ/it12`의 `tests/structure` diff 0.
9. 승인 줄: 머리 `approval` 없음(그 형식 id 없음).
10. 범위 계약: 'card 커밋들의 diff'로 판정.
11. test 이름: 판정자 충돌 재확인.
12. 같음 판정: 정렬 목록·바이트 비교, `set` 비교 없음.
13. red 모양: '판정 유형 근거'.
14. 상수·회로 이름: 허용 목록·kind 이름은 design 고정 목록, 숫자 상수 0, 회로 이름 0.

**다음 card 영향**(측정): 시제품으로 `integ/it12`에만 있는 위반 0, master에만 있는 위반 1(`sizing/block_columns.py` `_Circuit.members`, IT가 없앰). IT 병합 때 `stale` 1이고 판정자가 줄이면 된다. IT를 막지 않는다.

---

## 부록 A. design 문언 (`design/gl1`에 반영됨, 정본은 그 브랜치 머리)

**A-1. 40 §2.4.10 ④ 뒤에 절 추가**

> **GL-1 design(계획 N6.37, 사용자 결정 O-182·O-183 #10)**. 범위 = ①②와 공유 호출 감사 도구. ③④는 이 card 범위가 아니다.
>
> *자리*: 검사기 = `E/tests/structure/structure_checks.py`의 `check_g8`, `check_value_types`, 기준선 함수 `baseline_doc`, `dump_baseline`, `load_baseline`, `ratchet`. 기존 `check_g`는 바꾸지 않는다(그 test는 위반 0을 단언하고 ①②는 기존 위반을 래칫으로 다루므로 나눈다). 도구 = 저장소 루트 `tools/audit/scan_shared_calls.py`. 기준선 = `E/tests/structure/g8_baseline.json`, 기록 id = 파일의 `id` 칸(첫 값 `20261103-gl1-baseline`). 판정 기록 = `.ai/verification/20261103-gl1.json`.
>
> *① kind*: 표 일곱 행을 `g8_attr_container`, `g8_class_container`, `g8_default_factory`, `g8_cached_property`, `g8_cache_call`, `g8_module_cache`, `g8_id_call`, `g8_memo_call_form`으로 나눈다. §2.4.6이 없애기로 한 클로저 호출은 `g8_memo_lookup_form`으로 잡아 기존 자리를 래칫한다. '등'으로 적힌 목록은 고정한다: 가변 값 = 규칙 G `MUTABLE_CONSTRUCTORS`와 같은 판정, 모듈 수준 캐시 객체 = `BoundedLRU`, `LutMemo`, `OrderedDict`, `WeakValueDictionary`. 복사 등록부 면제는 적용하지 않는다.
>
> *② 타입 목록*: 엔진 전체(tests 제외) 클래스 중 `dataclass(frozen=True)` 이름의 AST 수집. 이름 단위다. 값 타입 등록부는 없다. 컨테이너에는 `tuple(...)` 등 생성자로 감싼 형태도 포함한다. frozen dataclass 본문은 제외하므로 결과 객체 값 칸은 ② 대상이 아니고 §2.4.8 소유표 대조가 맡는다.
>
> *래칫*: 행 키 = (kind, 경로, 안정 이름), 값 = 수. 줄 번호는 키가 아니다. 현재 수 > 기준선 수 = 새 위반(병합 정지). 현재 수 < 기준선 수 = 남은 칸(`stale`)이고 실패가 아니다. 판정자가 card마다 병합본에서 줄인 기준선을 판정 커밋에 넣는다. 기준선 생성·갱신은 판정자만 한다. 코드·test 작성 주체는 쓰지 않는다. 행 추가·수 증가는 기준 약화다(`criteria_weakened`, 사용자 승인). 파일 없음·형식 오류는 실패다.
>
> *감사 도구*: 입력 = 엔진 폴더, 출력 = `calls.json`, `shared.tsv`, `b_candidates.tsv`, `limits.json`. 대상 엔진을 import·실행하지 않는다. 호출을 정의 모듈로 해석하고(재수출 포함), 인자를 필드(`column`, `value`의 리터럴 종류·필드)·매개변수·리터럴·전역 잎으로 치환한다. 호출 모듈이 다른 두 자리의 쌍은 같은 치환 + 필드 잎 ≥ 1 = B, 다른 치환 + 양쪽 필드 잎 ≥ 1 + 매개변수 잎 0 = 아님, 그 밖 = D(판정 불가)다. `--touching`은 N6.3 (ii) 범위다. 도구는 확정 판정자가 아니다. D와 B는 판정자가 자리마다 G0~G7 근거로 손 분류한다(N6.3 (i)). 메서드 호출은 해석하지 않고 수를 기록한다.
>
> *판정*: 엔진 동작 불변. 다리 = 정의 toy, 나머지 '대상 없음'(증거 = 엔진 소스 diff 0). 결정성은 항상 잰다.

**A-2. 40 §10.4 표에 행 추가**

> | G 확장·값 타입 래칫(N6.3 (a)(b)) | `$PY -P -m pytest skills/analog-gmid-design/gmid_engine/tests/structure -q` (`test_rule_g8_baseline_ratchet`) |
> | 기준선 줄임(판정자, stale ≠ 0일 때) | `structure_checks.baseline_doc` + `dump_baseline`을 병합본에서 실행, diff가 줄임뿐인지 확인. 판정 기록 `reproduced_numbers`에 판정 커밋 기준 `stale` 수를 적고, 0이 아니면 FAIL. |
> | 같은 입력 재계산 측정(N6.3 (iv), 판정자) | `$PY tools/audit/scan_shared_calls.py --engine skills/analog-gmid-design/gmid_engine --out <evidence> --touching <card 커밋들이 바꾼 엔진 파일>` 뒤 자리별 손 분류 |

**A-3. 40:578(`id(` 행) 낡은 실측 정정**: '(쓰임과 무관하게. as-built 실측 tests 제외 0건)' → '(쓰임과 무관하게)'. 기존 자리는 기준선에 든다. '단계 ③이 전부 해소한다'는 문장은 '기존 위반은 GL-1 기준선으로 래칫하고, 해소 자리는 정하지 않는다(표지)'로. 근거: `facts_master.jsonl`(`metrics/noise_analysis.py:72`, `metrics/resolution.py:38`), 파일 목록도 bd19cc6과 다름.

**A-4. 42 D-GL1 행**: 판정 `MISS` → GL-1 병합 때 충족으로. D40:2238 '(미작성)' 삭제, 이 절 인용.

## 부록 B. 권고 (위임 A-28로 채택, 재검토 = LA-1 완료 13)

| ID | 권고 | 근거 | 대안 | 원래 취지와 다름 |
|---|---|---|---|---|
| R-G1 | `g8_memo_lookup_form`을 만들어 기존 `memo.lookup`·`lookup_persistent` 자리를 래칫 | `git grep`: 엔진에 `memo.call` 호출 0, `memo.lookup(_persistent)` 22파일 23자리. §2.4.6이 없애기로 함. `memo.call` 행만 만들면 진짜 트리에서 영원히 안 걸림(원칙 10). 없애는 일은 이 card 몫이 아니다(동작 불변) | `memo.call` 행만 ⚠ 공허한 게이트 / 지금 `lookup` 제거 ⚠ 엔진 변경, N6.37 위반 | §2.4.10 표에 한 kind 추가 |
| R-G2 | 기준선 = 판정자가 병합본에서 생성·커밋, 줄임도 판정자, stale은 red 아님 | 코드·기대값 주체가 기준선을 소유하지 않음(원칙 18). N6.3 변경 종류 표 '기준선은 기록이고 갱신은 검증자 변화표 근거'. test 커밋 때는 검사기가 없어 test 주체가 만들 수 없음 | stale도 red ⚠ 코드 주체가 같은 변경에서 기준선을 고치게 됨, 다른 card 정지 / test 주체 2차 커밋 ⚠ 왕복 + 1 | 계획에 소유자 문언 없음(유도) |
| R-G3 | GL-1 판정 기록 = base sha + 다리 '대상 없음', '미완료' 안 씀, 완료 계수에 듦 | N6.3 다리는 동작 변경 card 것, P:2577 '엔진 동작 변경 없음', 값 변화 0. 엔진 diff ≠ 0이면 FAIL이라 fail-open 아님 | '각 card' 문언대로 미완료 ⚠ 채울 내용 없는 보류가 LA-1 13까지 남음 | 측정 게이트 표 '각 card' 글자 |
| R-G4 | 도구는 쌍 분류를 내되 확정 판정자로 쓰지 않음. D가 다수여도 받아들임 | 시제품(`measure_b_trace.py`, `b_trace_master.tsv`, 조잡한 시제품이라 구현 판정률 아님): 공유 callee 149개 중 D 147, 감사 B 21개 중 20이 D·1 없음, 감사 C 70개 전부 D. 감사도 손 분류였다(`shared_pure_fn_audit.md` §1). 완료 (5)는 toy만 요구. 실효 가치 = N6.3 (ii) 자리 전수 목록 | 자리 목록만, 분류 없음 ⚠ 완료 (5) 미달 / 모듈 간 추적까지 ⚠ 범위·시간, 그래도 메서드 호출 벽 | N6.3 (iv)를 자동 확정으로 읽을 때와 다름. LA-1 13 재점검 후보 |

⑩ 결정 모순 점검: **안 함**(O-225 유보, LA-1 재점검). 작성자 자기 점검: O-182·O-183·O-225·A-5·A-6과 충돌 찾지 못함. R-G3는 A-5 목록에 GL-1이 없어 충돌 아님으로 읽었다.

## 부록 C. 표지 (이 card가 고치지 않음)

- **§2.4.10 ③ SC-a·SC-b lint**: 만드는 card 없음. `S/` `git grep` `SC-a|SC-b` 0건, `test_no_raw_duplicated_writes` `git ls-files` 0건. 42 D-GR11 = PART. N6.3 (a)(b)에 없어 병합을 막지 않는다. 계획 소유 자리 없음.
- **기존 위반 해소 자리 없음**: D40 '단계 ③이 전부 해소'는 낡았고(`git log`로 단계 ③ 완료 미확인, 위반 남음) 해소 card가 없다. 래칫은 늘지 않게만 한다.
- **`id()` 기존 자리 2**: `metrics/resolution.py:38`의 `memo`는 블록 안 dict라 O-15 (E) 승인 예외일 수 있다. 미확인, 기준선에 그대로 든다.
- **새 B 기준선**: 감사 §2.1은 엔진 `b12792ab` 기준이다. 도구 첫 실행 때 줄이 다를 수 있다.
- **미측정**: master 전체 test 현재 상태. 코드 착수 전 test 작성 주체가 base에서 먼저 돌린다(`briefs.md`).
