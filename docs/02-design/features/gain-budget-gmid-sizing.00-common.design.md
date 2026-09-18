---
template: design
version: 1.8
plan_version: 5.19
---

# gain-budget-gmid-sizing -- 00-common Design Document

> **Summary**: 13개 design 문서가 공유하는 정의를 한 곳에 모은다. 구현 주체 분류 양식(WP-21), 용어→코드 이름 대응, 영역 표기 규약(DEC-67), 옛 키 거부 게이트 공통 형식(DEC-68·69), 실패 규약의 코드 형식(N3.14), 판정 기록·승인 기록 스키마(N3.12.5), 판정에 쓰는 계획서 표(V 도입·IC 담당·Phase 순서)를 검증 도구가 직접 읽는 규칙(N4.1·N4.2·N6.1), 성능 측정 명령(N6.3), 무동작 판정 방법.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (오케스트레이터)
> **Date**: 2026-09-18 · **Status**: v1.8 -- v1.7은 승인됨(`20260918-00-common-design`). v1.8은 `05-role-separation`에 따른 개정(§8.1 옵션 표기·증거 소비자(gate는 실행하지 않는다)·red 플러그인을 부르는 곳·로더 규칙 10의 V4 oracle 대조, §8.2 해시 입력·`staged_diff`, §9.1 변경 정의, 교차 참조)이고 05의 승인이 덮는다. 독립 검증 review21~27 반영, 판정 표 사본 제거(§2 정정).
> **Planning Doc**: [gain-budget-gmid-sizing.plan.md](../../01-plan/features/gain-budget-gmid-sizing.plan.md) v5.19 · N6.1 `0(문서)` 행

Context Anchor: 계획서에 `## Context Anchor` 절이 없어 옮기지 않는다(계획서 N1이 목적·범위의 정본이다).

---

## 0. 이 문서를 읽는 법

* **정의의 정본은 계획서다.** 이 문서는 계획서 정의를 되풀이하지 않고 절 번호·ID로 인용하며(N9.4), 계획서가 정하지 않은 것만 더한다: (a) 코드·JSON이 쓸 **이름과 형식**, (b) 여러 design 문서가 같은 방식으로 해야 하는 **절차**, (c) 실행 가능한 **명령**.
* 다른 design 문서는 이 문서를 `00-common §n`으로 인용한다. 이 문서의 정의가 모자라면 인용하는 쪽에서 재서술하지 않고 이 문서를 고친다(N9.4).
* 구성안: **C -- 판정 입력만 기계 판독**(2026-09-18 사용자 선택)에 **정정 하나**(§2): 판정 표의 소비자가 검증 도구(merge gate, test)면 계획서를 **직접 읽고 사본을 두지 않는다**. 엔진이 실행 중에 쓰는 표(실패 클래스, 옛 이름)만 코드 상수로 두고 계획서와의 일치 test를 붙인다. 코드 상수는 **첫 소비 코드와 같은 변경 단위에서** 만든다(WP-01).
* 명령의 `$PY`는 프로젝트 인터프리터 `C:\Python314\python.exe`다(프로젝트 CLAUDE.md).
* 이 문서가 인용하는 코드 개수·위치는 2026-09-18 AST 실측이고, 실제 수정 범위는 해당 spec card가 그 시점에 AST로 다시 센다.

---

## 1. 범위 (N9.2-1)

| 이 문서 절 | 구현하는 계획서 절·ID |
|---|---|
| §3 구현 주체 분류 양식 | WP-21, N9.1 `00-common` 행 |
| §4 용어→코드 이름 대응 | N0.4 용어집(정의는 N0.4가 정본) |
| §5 영역 표기 규약 | DEC-67, N0.4 '영역', N4.1 IC5 |
| §6 옛 키 거부 게이트 공통 형식 | DEC-68, DEC-69, N3.16 |
| §7 실패 규약의 코드 형식 | N3.14, N3.10, DF-37 |
| §8 판정 기록·승인 기록 스키마 | N3.12.5, N3.12.6 양식 행, N4.3 공격 15 |
| §9 판정에 쓰는 계획서 표 읽기(V 도입·IC 담당·Phase 순서) | N4.1, N4.2, N6.1, N3.12.4 EL4, N4.3 공격 16 |
| §10 성능 측정 명령 | N6.3 '성능', DF-35 |
| §11 무동작 판정 방법 | N0.4 '무동작 증명', WP-05, DEC-47, DF-35·36 |
| §12 판정식 모음 | N9.2-3 |

범위 밖: 쓰기 경로표 glob·hook·게이트 알고리즘은 `05-role-separation`, S1·S2 필드 이름은 6a·6b design이 정한다(정한 뒤 §4 표에 한 줄을 더한다).

---

## 2. 구성안 (Checkpoint 3)

| 기준 | A 문서 중심 | B 전부 기계 판독 | **C 판정 입력만 기계 판독** |
|---|---|---|---|
| 판정 표(옛 키·V 도입·IC 담당·실패 클래스·영역 토큰) | 문서 표. 각 Phase 코드가 옮겨 적음 | JSON 정본, 문서는 생성물 | **코드 상수 하나 + 계획서 표와의 일치 검사** |
| 용어집·영역 규약·분류 양식 | 문서 | JSON | 문서 |
| 지금 만드는 파일 | 양식 2 | 양식 2 + 데이터 파일 여럿 | **양식 2** |
| WP-21 | 위반(사본마다 AI가 옮겨 적음) | 지킴 | 지킴 |
| WP-01 | 지킴 | 위반(소비 코드 없는 표를 먼저 만듦) | 지킴(첫 소비 코드와 같은 변경 단위) |
| 정본 수 | 1 + 사본 n | 2(계획 N0.4와 JSON) | 1(계획) + 일치 검사로 묶인 코드 상수 |

**선택: C**(2026-09-18 사용자 선택). 근거는 위 두 원칙 행이다.

**정정(2026-09-18, 사용자 "대안으로 고치고")**: 위 세 안은 모두 '표를 어딘가에 옮겨 둔다'는 전제였고 **'소비자가 원본을 직접 읽는다'는 선택지가 빠져 있었다**. 그래서 v1.0~v1.3은 V 도입·Phase 순서·IC 담당 표를 merge gate·test 쪽 코드 상수로 옮기고, 사본과 원본을 맞추는 자기검사와 '어느 판을 읽나' 규칙을 덧댔다 -- 그 규칙은 상수가 gate 코드와 같은 파일에 있어 구현할 수 없었다(review24 R-04). 정정 규칙: **사본은 소비자가 원본을 읽으면 안 될 때만 둔다.** 엔진은 실행 중에 문서를 읽으면 안 되므로 실패 클래스 표(§7)와 옛 이름 표(§6)만 사본(코드 상수 + 일치 test)이고, 검증 도구가 쓰는 표(§9)는 계획서를 직접 읽는다. 사본이 막던 경로(계획서 표 한 칸 수정으로 검사를 끄기)는 **EL3(커밋 시점)과 EL4(병합 시점)의 '판정 표 변경은 승인 기록 필수'**가 막는다 -- 계획서 개정은 오케스트레이터의 직접 커밋이 정상 경로라 EL4만으로는 발동하지 않는다(review26 T-03).

---

## 3. 구현 주체 분류 양식 (WP-21)

### 3.1 판정 순서

항목마다 아래를 **위에서부터** 묻고 처음 "예"인 부류로 정한다.

| 순서 | 질문 | 예이면 부류 | 고정 수단 |
|---|---|---|---|
| 1 | 결과가 **구조로 가를 수 없는 회로 해석**인가(계획서가 J ratify로 넘긴 것) | `AI 제안→사람 확정` | 승인 기록 + 데이터(`structure.json` 등). 이후 코드가 그 데이터를 읽는다 |
| 2 | 결과가 **판정·기준값·보고 수치·다음 단계의 입력**인가 | `코드` | 정본 구현 하나 + test(N3.12.3 흐름). 부트스트랩 산출물은 N4.3 거부 증명 + 승인 기록 |
| 3 | 그 밖(작성·검토·결함 탐색) | `AI 직접` | 산출물의 독립 검증(WP-13, N3.12) |

* 1번 부류도 **"어디가 구조로 못 가르는지 찾아내는 일"은 코드**다(`review_needed` 산출). 한 기능이 두 행으로 나뉘는 것이 정상이다 -- 예: DC 역할 유도(코드, 못 가르는 그룹을 `review_needed`로 낸다)와 그 그룹의 역할 결정(제안 → 확정).
* 2번에 "AI가 규칙 문장을 읽고 직접 적용한다"는 선택지는 없다(WP-21). 구현하다 드러난 규칙의 빈칸은 그 design 문서가 알고리즘으로 정하고 test로 고정한다.
* 3번 산출물이 다음 단계 입력이 되면(예: design 문서의 판정식) 그 **입력으로 쓰이는 부분**은 2번이다 -- 문서는 식을 적고 코드가 계산한다(WP-03).
* 데이터 파일(JSON Schema, 양식)은 판정 입력이면 2번 `코드`다.

### 3.2 분류 표 양식

모든 design 문서는 `## 구현 주체 분류` 절에 아래 열 그대로 표를 둔다.

| 항목 | 결과물 | 부류 | 판정 근거(§3.1 순서 번호와 이유) | 고정 수단 | 구현 소유 | 판정 기준 소유 | 산출 spec card 또는 승인 기록 |
|---|---|---|---|---|---|---|---|

* `부류` 값은 `코드` / `AI 제안→사람 확정` / `AI 직접` 셋뿐이다.
* `구현 소유`·`판정 기준 소유`의 허용 값: `오케스트레이터`(N3.12.1 의도 권한. 문서·양식·부트스트랩 ① 산출물) / `gmid-code-author` / `gmid-test-author` / `gmid-verification-auditor` / `사용자`(승인·ratify) / `독립 검증 agent`(AI 직접 산출물 검토). 한 칸에 한 값이다. **두 칸이 같은 값이면 안 된다**(WP-13).
* 부트스트랩 산출물(N3.12.6 ①)은 구현 소유 `오케스트레이터`, 판정 기준 소유 `사용자`(N4.3 거부 로그 승인)다.
* 부류가 `코드`인데 spec card 칸이 비어 있으면 그 항목은 구현되지 않는다 -- 열린 질문으로 처리한다(N9.2-8).

### 3.3 이 문서 자신의 분류

| 항목 | 결과물 | 부류 | 판정 근거(§3.1 순서 번호와 이유) | 고정 수단 | 구현 소유 | 판정 기준 소유 | 산출 spec card 또는 승인 기록 |
|---|---|---|---|---|---|---|---|
| 이 문서 | design 문서 | `AI 직접` | 3 -- 작성 | 독립 검증 → 사용자 승인 | `오케스트레이터` | `독립 검증 agent` | 승인 기록(§16) |
| 판정 기록 스키마 초안 | `.ai/verification/_schema.json` | `코드` | 2 -- merge gate 판정 입력 | 독립 검증 측정(§15) → 0.5 공격 15 | `오케스트레이터` | `사용자` | CC-1 |
| 승인 기록 양식 | `.ai/approvals/_TEMPLATE.md` | `코드` | 2 -- V5 판정 입력 | 0.5 공격 15(머리 형식 위반 거부) | `오케스트레이터` | `사용자` | CC-1 |
| merge gate 로더·승인 기록 파서·red 해시 | 판정 기록 로더, `parse_approval_header`, `red_failure_hash`, red 수집 플러그인 | `코드` | 2 -- 병합 판정 | 0.5 공격 15 | `오케스트레이터` | `사용자` | CC-1 |
| 계획서 판정 표 읽기 | `read_plan_tables`·`plan_phase_tokens` | `코드` | 2 -- N/A 판정 입력 | 0.5 공격 16(표 파손 거부, 승인 없는 표 개정 거부) | `오케스트레이터` | `사용자` | CC-2 |
| 계측 인터페이스 | MOD10 `search`·`output_dir`·`instrument`·`activations_out` 인자, 평가 커널 빌더의 감싸기 | `코드` | 2 -- 보고 수치·판정 입력 | red-green | `gmid-code-author` | `gmid-test-author` | CC-7, CC-8 |
| xfail 생성과 표식 대조 | conftest `--gmid-phase`·`--gmid-strict`·`--gmid-dod`, `gmid_ic` 표식(케이스 키), 표식-계획서 대조 test | `코드` | 2 -- xfail 만료 판정 | 계획서 N4.1 직접 대조(§9.3) | `gmid-test-author` | `사용자`(계획서 N4.1 승인) | CC-3 |
| 실패 규약 코드 | §7 | `코드` | 2 -- exit code·실패 레코드 | red-green | `gmid-code-author` | `gmid-test-author` | CC-4 |
| 옛 키 게이트 | §6 | `코드` | 2 -- 로드 거부 | red-green | `gmid-code-author` | `gmid-test-author` | CC-5 |
| 영역 토큰 | `DOMAINS` | `코드` | 2 -- 로드 거부 | red-green | `gmid-code-author` | `gmid-test-author` | CC-6 |
| 계측 도구 | `tests/tools/measure_search_perf.py`, `tests/tools/noop_proof.py` | `코드` | 2 -- 보고 수치·판정 | red-green + auditor 재실행 | `gmid-code-author` | `gmid-test-author` | CC-7, CC-8 |
| margin 정규화 | `normalized_margin` | `코드` | 2 -- 실패 캐시 정렬 입력 | red-green | `gmid-code-author` | `gmid-test-author` | CC-9 |

---

## 4. 용어→코드 이름 대응 (N0.4의 구현 이름)

정의는 N0.4가 정본이다(용어집 최종본 = N0.4 + 이 표. N9.1 `00-common` 행). 이 표는 **코드·JSON에서 그 개념을 부르는 이름**만 적는다. 이름 규칙은 DEC-68이다. 표에 없는 개념에 코드 이름을 붙이는 design 문서는 **같은 커밋에서 이 표에 한 줄을 더한다**.

| N0.4 용어 | 코드·JSON 이름 | 값 집합 | 정한 곳 |
|---|---|---|---|
| 영역 | `domain` | `"dc"` / `"ac_struct"` / `"ss"` / `"ls"` | 이 문서 §5 |
| 봉인 전 AC 값의 표기 | 예약: `qualifier` ∈ `"bound"`(상한) / `"estimate"`(추정) | 값 모양·거부 함수는 봉인 전 값을 처음 내는 design(6b 또는 7b)이 정한다 | 이름만 이 문서 |
| status | `status` | `"declared"` / `"derived"` / `"proposed"` / `"review_needed"` / `"ratified"` | N0.4 |
| 실패 레코드 | `FailureRecord`(Python), JSON `{class, devices, margin, detail}` | §7 | N3.14, 이 문서 §7 |
| 판정 값 | pytest 결과 | `PASS` / `FAIL` / `XFAIL` | N3.12.3 |
| auditor 검사 판정 | `checks.Vn.verdict` | `"PASS"` / `"FAIL"` / `"N/A"` | N3.12.5 |
| 판정 유형 | `evidence_type` | `"red-green"` / `"equivalence"` / `"test-only"` | N3.12.3 |
| 커밋 역할 트레일러 | `Role:` | `code` / `test` / `audit` / `doc` | N3.12.4 EL3 |
| Phase 이름 | `phase` | 계획서 N6.1에서 읽은 `phase_order`(§9.2) | N6.1 |
| 극성 | 극성 값 | `"nmos"` / `"pmos"` | DEC-68, N3.16 |
| 발동 계수 | `activations` | `{<분기 또는 기능 ID>: int}` | 이 문서 §11(분기 ID 목록은 6a) |

---

## 5. 영역 표기 규약 (DEC-67)

규칙은 DEC-67과 N0.4 '영역'이 정본이다. 이 절은 **어디에 어떤 모양으로 붙이는지**만 정한다.

| 대상 | 표기 위치 | 형식 | 검사 |
|---|---|---|---|
| design 문서의 규칙·판정식·표 행 | 행마다 `영역` 열, 또는 규칙 문장 머리의 `(DC)` / `(AC구조)` / `(ss)` / `(ls)` | 절 머리 선언으로 대신하지 않는다(N0.4) | 각 design 문서의 독립 검증 항목 |
| S1 관계 엣지 | 필드 `domain` | §4 값 집합 | 6a 로드 게이트(엣지마다 필수, 값 집합 밖 거부) |
| metric 선언 | 필드 `domain` | `"dc"` / `"ss"` / `"ls"`(`ac_struct`는 수치가 아니라 metric에 쓰지 않는다) | 6a GB0 로드 게이트(N6.1 6a '영역 표기') |
| S2 필드 | 영역별 하위 묶음 `dc` / `ss` / `ls` | 필드 이름은 6b design | 6b |
| 게이트 함수(N4.1 IC5 이름 집합) | docstring의 `영역:` 한 줄. 값은 §4 영역 값 하나 이상(쉼표 구분), 또는 영역 판정이 없는 스키마·경로 게이트는 `영역: 없음(스키마)` | IC5 '검사하지 않는 것' 절과 같은 docstring | IC5 test(N4.1 IC5, Phase 1 `10-test-separation`) |

* 상수 `DOMAINS = ("dc", "ac_struct", "ss", "ls")`는 MOD2 `topology_authoring.py`에 두고, 첫 소비자인 6a S1 엣지 `domain` 로드 검사와 같은 변경 단위(CC-6)에서 만든다. IC5 docstring 검사는 `DOMAINS`가 생기기 전(Phase 1)에도 돌아야 하므로 허용 문자열을 test-author가 §4 표에서 옮겨 둔다(oracle (d)). 두 곳에 같은 값 집합이 생기므로 CC-6이 "IC5 허용 영역 문자열 = `DOMAINS`" 대조 test를 함께 넣는다.
* `ac_struct`는 **값**이다. DEC-68의 `ac_` 접두사 규칙은 **키 이름**(`ac_excite`)에 대한 것이라 충돌하지 않는다.

---

## 6. 옛 키 거부 게이트 공통 형식 (DEC-68·69)

선례는 `sizing_recipe.py:validate_no_legacy_vs_key`다(지금은 `_build_theta_evaluator`에서 다른 필드를 읽은 **뒤**에 한 번 불린다 -- 아래 배선이 이 순서를 바로잡는다). 모든 MG 단계의 옛 이름 거부는 **표 하나 + 읽기 함수 하나 + 게이트 함수 하나**로 한다(WP-14).

### 6.1 표 `LEGACY_NAMES` (MOD2 `topology_authoring.py`)

```python
@dataclass(frozen=True)
class LegacyName:
    old: str      # 옛 이름(N3.16 '흡수되는 옛 이름' 열)
    new: str      # 정본 이름(N3.16 '정본 이름' 열)
    where: str    # 파일 종류(JSON_KINDS의 원소)
    scope: str    # 그 파일 안의 위치. JSON pointer 접두, 세그먼트 "*"는 아무 키. "" = 문서 전체
    match: str    # "key"(그 위치의 매핑 키) | "value"(그 위치의 문자열 값, value_from_* 참조 포함)
    stage: str    # "MG0" | "MG1" | "MG2" | "MG3"(N3.16 '단계' 열)
    reason: str   # 한 줄. N3.16 행 개념 이름 또는 DEC ID

JSON_KINDS = ("topology", "sizing_spec", "structure", "instance", "derived_bounds", "regression_baseline", "harness_spec")
```

* `JSON_KINDS`는 엔진이 읽는 JSON 파일 종류 전부다(2026-09-18 AST 실측: topology, `.derived.json` 사이드카, instance.json, 회귀 기준 JSON). `harness_spec`만 파일이 아니라 `SPECS[circuit]["spec_fn"]()`의 반환 dict다(7b 이관 전까지). 새 종류의 JSON을 읽게 되면 그 변경이 이 튜플에 원소를 더한다.
* **표에 행이 있다 = 그 이름 변경이 끝났다.** 행은 이름을 바꾸는 변경 단위에서 더한다. 활성 단계를 따로 두지 않는다. 행이 없는 종류도 로더는 거친다(§6.2).
* 7b 전 topology 안의 metric 선언(`sizing_roles.metrics`)은 `where="topology"`, `scope="/sizing_roles/metrics/*"`다.
* `match="value"`는 N3.16 끝 주의(문자열 값 안의 이름은 키 검색에 걸리지 않는다)를 막는 행이다.

### 6.2 읽기 함수와 게이트 함수

```python
def load_json_checked(path: str, where: str) -> dict:
    """영역: 없음(스키마). §8.1 로더 규칙 1~3(UTF-8 BOM 없음, 중복 키 거부, 모든 수가 유한)으로 JSON을 읽고
    곧바로 reject_legacy_names(doc, where)를 부른 뒤 돌려준다.
    검사하지 않는 것: 새 키가 DEC-68 규칙을 따르는지(스키마 로더의 미지 필드 거부가 한다)."""

def reject_legacy_names(doc: Mapping, where: str) -> None:
    """영역: 없음(스키마). where가 같은 LEGACY_NAMES 행 전부를 scope·match대로 훑는다.
    검사하지 않는 것: 표에 없는 옛 이름."""
```

* 걸린 곳을 **전부** 모은 뒤 한 번에 `SchemaRejectedError`(§7)를 낸다. 개수 상한으로 잘라 보여주지 않는다(WP-03).
* 실패 레코드: `class="SCHEMA_REJECTED"`, `devices=[]`, `margin=null`, `detail={"gate": "legacy_names", "where": ..., "path": ..., "hits": [{"pointer", "old", "new", "stage", "reason"}]}`. 메시지는 옛 이름·새 이름·`reason`을 모두 담는다.
* **배선 규칙**: 엔진 모듈(`skills/analog-gmid-design/assets/*.py`, Phase 3 뒤 MOD1~MOD10)에서 파일을 읽는 `json.load`/`json.loads` 호출은 `load_json_checked` 안에만 있어야 한다. 파일을 읽지 않는 깊은 복사 관용구 `json.loads(json.dumps(x))`는 CC-5에서 `copy.deepcopy`로 바꾼다(예외 규칙을 두지 않는다). test-author가 AST로 "`load_json_checked` 밖의 `json.load`/`json.loads` 0"을 단언한다. 2026-09-18 AST 실측 대상은 `sizing_recipe.py` `json.load` 7·`json.loads` 3, `stick_diagram.py` 11·1, `design_report.py` 1, `topology_to_markdown.py` 2이고, 그중 인라인 self-test 안의 것은 TS1(Phase 1)에서 사라진다 -- CC-5 spec card가 TS1 뒤 AST로 다시 센다.
* 하네스 spec은 `spec_fn()` 반환 **직후** `reject_legacy_names(spec, "harness_spec")`를 부른다.
* **대체**: MG1 변경 단위(Phase 4, CC-5)에서 `validate_no_legacy_vs_key`를 `vs` 행(`where="topology"`, `scope="/device_roles/*"`, `match="key"`, `stage="MG0"`)으로 옮기고 옛 함수를 삭제하고 레지스트리를 갱신한다(WP-14).

### 6.3 N3.16 → 옛 이름 행 옮기기 규칙

`LEGACY_NAMES`(code-author)와 test의 기대 목록(test-author)은 둘 다 이 규칙으로 계획서 N3.16에서 **각자** 옮긴다.

| N3.16 칸 | 옮기는 값 |
|---|---|
| '흡수되는 옛 이름' | 백틱 안 토큰 중 **JSON 키 또는 JSON 문자열 값으로 쓰이는 이름**만 행이 된다. 코드 식별자(`_DEFAULT_RAIL_HI/LO`, `_RAIL_NETS`, `spec.get(...)` 같은 코드 조각)는 행이 아니라 V6 소스 lint·해당 DF의 대상이다. 서술(백틱 없는 문장)은 행이 아니다 |
| '정본 이름' | `new` |
| '단계' | 칸의 `MG0`~`MG3` 토큰. 괄호 설명(`MG1(코드)`, `MG0(문서)`)은 그 토큰이 어느 쪽 이름 변경인지 말한다 -- JSON 쪽 토큰만 쓴다. MG 토큰이 없는 행(`--`, `7a`, `7b`, `Phase 4(…)`)은 이 표의 대상이 아니다(metric 이름 통일 등은 해당 design이 자기 게이트를 둔다) |
| `where`·`scope` | **옛 이름이 지금(이관 전) 놓인 곳**이다. N3.16 '저장 위치' 칸은 새 이름이 갈 곳이라 쓰지 않는다. 옛 이름을 library·`SPECS` 반환 dict에서 JSON 탐색으로 찾은 파일 종류가 `where`, 위치가 `scope`다(예: `vs`는 topology의 `/device_roles/*` -- 현재 `validate_no_legacy_vs_key`가 보는 곳과 같다). 탐색에서 0건이면 N3.16 행이 말하는 옛 위치를 쓴다. `scope` 세그먼트 `*`는 매핑 키와 리스트 원소 둘 다를 뜻한다(`/netlist/*`) |
| 한 칸에서 정본이자 옛 이름인 것(`_paper_target_spec`) | 옛 이름 쪽은 MG0 행의 뜻(사용자 확정 스펙을 담던 컨테이너 → `_declared_target_spec`)만 행이 된다. 논문 값 기록으로서의 `_paper_target_spec`은 정본으로 남는다 |

* **단계 필터**: 기대 목록은 그 spec card의 `Phase`까지 **끝난 MG 단계**의 행만이다(MG0 즉시·MG1 Phase 4·MG2 6a 착수 전·MG3 7b, DEC-69). 뒤 단계 행을 넣으면 red가 영원히 FAIL한다.

### 6.4 red test 형식 (test-author)

* **기대 목록은 test-author가 계획서 N3.16에서 §6.3 규칙으로 직접 옮긴다.** 코드의 `LEGACY_NAMES`를 읽어 케이스를 만들지 않는다(V4 취지). oracle (d), 출처는 spec card에 계획서 N3.16 행과 그 판의 커밋 해시로 적는다.
* 케이스마다: library topology를 로드해 해당 위치에 옛 이름을 넣은 변형(WP-07) → `SchemaRejectedError`와 `hits`에 그 이름이 있음을 단언한다.
* **오거부 0**: 변형하지 않은 library 회로 전부가 통과함을 같은 파일에서 단언한다(WP-02).

---

## 7. 실패 규약의 코드 형식 (N3.14)

분류·발생·처리·exit code는 N3.14가 정본이다(SCHEMA_REJECTED 행과 탐색 루프 규칙 포함). 이 절은 파이썬 형식만 정한다.

### 7.1 위치와 클래스 구조

N3.10 import 규칙(번호가 작은 모듈 쪽으로만)과 레지스트리 목적지(`InfeasibleSizingError` → MOD4)에 맞춰 둘로 나눈다.

```python
# MOD2 topology_authoring.py -- 로드 게이트가 raise하므로 MOD2
class SchemaRejectedError(Exception): ...      # N3.14: Exception 직접 하위

@dataclass(frozen=True)
class FailureRecord:
    failure_class: str            # JSON 키 "class"
    devices: tuple[str, ...]
    margin: float | None          # §7.2
    detail: Mapping[str, object]
    def to_json(self) -> dict: ...   # {"class", "devices", "margin", "detail"}

# MOD4 gmid_sizing_engine.py -- 레지스트리 목적지
class InfeasibleSizingError(ValueError): ...   # 기존 클래스(Phase 3에서 MOD4로 이동)
class StructureUnresolvedError(InfeasibleSizingError): ...
class InfeasibleTargetError(InfeasibleSizingError): ...
class NonconvergentError(InfeasibleSizingError): ...
class SealViolationError(InfeasibleSizingError): ...
class SearchFailedError(InfeasibleSizingError): ...

@dataclass(frozen=True)
class FailureClass:
    exc: type | None          # 후보 실패 레코드는 None
    exit_code: int | None     # 후보 실패 레코드는 None
    parent: str | None        # 후보 실패 레코드의 상위 분류

FAILURE_CLASSES: Mapping[str, FailureClass]
CANDIDATE_FAILURE_CLASSES: tuple[type, ...]    # N3.14 '탐색 중 처리'가 실패 기록인 예외 클래스
def exit_code_for(exc: BaseException) -> int: ...
```

* 모든 N3.14 예외와 `SchemaRejectedError`는 `.record: FailureRecord`를 갖는다. exit code·실패 캐시·보고는 이 한 형식만 읽는다.
* **raise 위치 규칙**: N3.14 예외는 MOD4 이상에서만 raise한다. MOD3(구조 유도)은 `status`(`review_needed`·`undetermined`)를 돌려주고, 그것을 소비하는 MOD4·MOD6이 `StructureUnresolvedError`로 바꾼다(MOD3가 MOD4를 import하지 않게). `SchemaRejectedError`는 MOD2 이상 어디서나 raise할 수 있다.
* 후보 실패 레코드(`structure_inconsistent`, `local_infeasible`)는 예외 없이 `FailureRecord`만 만든다.
* **`FAILURE_CLASSES` 키 규칙**(N3.14 표 → 키): `분류` 칸에서 괄호 앞 대문자 토큰이 키다. 괄호로 시작하는 행(`(후보 실패 레코드 class = \`x\`, 분류 Y의 하위)`)은 백틱 안 `x`가 키이고 `parent=Y`다. 같은 키가 두 행이면(STRUCTURE_UNRESOLVED와 그 최종 해 행) exit code가 같아야 하고 한 항목이다. `예상 밖 예외` 행은 키가 아니라 `exit_code_for`의 기본값 1이다. exit code 칸은 첫 정수를 읽고, `--`이면 `None`이다. `exc`의 클래스 이름은 `예외` 칸의 첫 백틱 토큰과 같아야 한다.
* `exit_code_for`: `type(exc).__mro__`를 앞에서부터 보며 `FAILURE_CLASSES`에 `exc`로 등록된 첫 클래스의 exit code를 돌려준다. 없으면 1. 기반 `InfeasibleSizingError`는 등록하지 않는다 -- Phase 4 이후 직접 raise하지 않으므로, 나오면 1(예상 밖)로 드러난다.
* 파이프라인 진입점은 최상위에서 예외를 잡아 `exit_code_for`로 종료한다. 지금 하네스 `run()`이 모든 예외를 삼키고 0으로 끝나는 것은 DF-37이다.
* **도입 시점**: N3.14 클래스 전부와 `FAILURE_CLASSES`·`exit_code_for`는 Phase 4(`40-defect-fixes` 'N3.14 실패 클래스 도입')에 만든다. 소비자는 진입점 exit code와 §9.3 N3.14 일치 test다. Phase 4에 발생 지점이 없는 클래스의 red는 진입점 exit code 대응(합성 raise → exit code)으로 만든다.

### 7.2 margin (CC-9, Phase 5)

* `def normalized_margin(magnitude: float, tol: float | None) -> float | None` (MOD2): `tol`이 `None`이거나 0이면 `None`, 아니면 `magnitude / tol`. 분모의 선택은 N3.14 정규화식이 정본이고, 부르는 쪽이 그 클래스의 분모를 넘긴다. margin을 계산하는 곳은 이 함수 하나다(IC9).
* 첫 소비자는 실패 캐시 정렬(N3.5, Phase 5)이라 그 변경 단위(`50-failure-cache`)에서 만든다(WP-01).

### 7.3 삼키지 않기

* `SchemaRejectedError`가 `ValueError` 하위가 아닌 이유와 남은 광범위 except 처리는 N3.14 SCHEMA_REJECTED 행과 **DF-37**이 정본이다(개수와 범위는 DF-37). 기반 클래스를 잡는 `except InfeasibleSizingError` 핸들러를 `CANDIDATE_FAILURE_CLASSES`로 바꾸는 것도 DF-37이다. 지점별 red(그 지점을 지나는 경로에서 `SchemaRejectedError`·N3.14 예외가 진입점 exit code로 나온다)는 CC-4 범위다.

---

## 8. 판정 기록·승인 기록 스키마 (N3.12.5)

### 8.1 판정 기록 `.ai/verification/_schema.json`

필드 목록은 N3.12.5가 정본이다. 스키마는 JSON Schema draft 2020-12이고 모든 객체가 `additionalProperties: false`다. 검증기는 `jsonschema`(U-38 확정)다.

| 필드 | 타입·형식 | 필수 |
|---|---|---|
| `id` | `YYYYMMDD-<slug>`, slug는 소문자·숫자·하이픈 | 예 |
| `spec_card` | `docs/02-design/specs/<id 형식>.spec.md` | 예 |
| `evidence_type` | `red-green` / `equivalence` / `test-only` | 예 |
| `base_commit`, `test_commit` | 40자리 **소문자** 16진 | 예 |
| `code_commit` | 40자리 소문자 16진. `test-only`이면 `null`(N3.12.3: 순서 4·5 생략) | 예 |
| `red` | `{test_ids: [제어 문자 없는 고유 문자열, 1개 이상], failure_hashes: [64자리 소문자 16진, 1개 이상]}` | `red-green`일 때만 필수, 그 밖에는 금지 |
| `equivalence` | `{commands: [str, 1개 이상], outputs_hash: 64자리 소문자 16진}` | `equivalence`일 때만 필수, 그 밖에는 금지 |
| `checks` | `V1`~`V10` 열 개 키 전부. 값 `{verdict: PASS/FAIL/N/A, basis: 공백 아닌 문자 1개 이상}` | 예 |
| `reproduced_numbers` | `[{name: str, value: number, command: str}]` | 예(빈 배열 허용) |
| `approvals` | 승인 기록 id 배열(고유, 형식은 `id`와 같다) | 예(빈 배열 허용) |
| `auditor_run` | `{time: date-time, worktree: str, commands: [str, 1개 이상]}` | 예 |

* 정규식은 끝을 `$` 대신 `(?![\s\S])`로 닫는다 -- 파이썬 `re`(jsonschema가 쓴다)의 `$`는 끝 개행 앞에서도 맞는다(review21 C-08).

**해시의 정의와 소비자**:

* `failure_hashes[i]` = `red_failure_hash(test_ids[i], exc_type)` = `sha256(UTF-8(f"{test_id}\n{exc_type.__module__}.{exc_type.__qualname__}"))`. 함수는 `tools/gates/merge_gate.py` 하나에 두고 auditor가 기록할 때 쓴다. 메시지·경로는 넣지 않는다(worktree 경로와 실수 repr 때문에 재현되지 않는다). **소비자**: auditor가 격리 복제본(`05-role-separation` §12-7)에서 `red.test_ids`를 base에 대해 실행해 이 해시를 계산·기록한다(V2 red 재현). merge gate는 push된 코드를 실행하지 않으므로(계획 N3.12.0) 이 값을 다시 재지 않고 로더 규칙(형식·길이)만 판정한다.
* **red 수집**(merge gate 모듈이 pytest 플러그인이다. auditor가 격리 복제본에서 **base 판** 게이트 코드로 부른다 -- 복제본 안의 `tools/gates/`가 아니라 `05-role-separation` §4.4 캐시 디렉터리를 `PYTHONPATH` 맨 앞에 두고 `-P`로 현재 디렉터리를 빼야 캐시 판이 쓰인다 -- `-m`은 현재 디렉터리를 `PYTHONPATH`보다 앞에 넣는다, review33 M2-01): 실행은 복제본 루트에서 `PYTHONPYCACHEPREFIX=<빈 임시 디렉터리> $PY -P -m pytest -c <캐시>/pytest_gate.ini --rootdir=<복제본 루트> --confcutdir=<복제본 루트> -p merge_gate --continue-on-collection-errors --gmid-phase=<spec card Phase> --gmid-strict=<§9.3 엄격 집합, 정렬·쉼표 구분, 비면 값 없음> …`(두 옵션은 항상 `=` 한 토큰 형식이다)이고(CC-3 전에는 두 `--gmid-*` 옵션이 없다), 병합본에서 엄격 대상 케이스는 PASS여야 하며 XPASS는 엄격 대상이 아닌 케이스에서만 나온다, 플러그인은 환경 변수 `GMID_RED_CAPTURE`가 가리키는 파일에 (test id, 예외 타입)을 JSON으로 쓴다. test id는 rootdir 기준 pytest node id다.
  * 실행 단계 실패: `pytest_runtest_makereport`에서 `call.when ∈ {"setup", "call"}`이고 `call.excinfo`가 있을 때 `call.excinfo.type`(fixture 실패도 red로 잡는다).
  * 수집 단계 실패(신규 모듈을 test 파일 머리에서 import하는 경우): `pytest_exception_interact(node, call, report)`에서 `report`가 `CollectReport`일 때, test id = 그 모듈의 node id, 예외 타입 = `call.excinfo.value.__cause__`의 타입(pytest는 import 오류를 `Collector.CollectError`로 감싸고 원인을 `__cause__`에 둔다 -- review24 R-02 실측, pytest 9.0.2). `__cause__`가 없으면 `call.excinfo.type`. 이 훅이 수집 오류에서 불리는지는 0.5 공격 15의 '수집 단계 ImportError red' 케이스로 실측해 고정한다.
  * **허용 예외 타입**(red 수집 플러그인이 강제 -- 허용 밖 타입은 red로 기록하지 않는다, N3.12.3 순서 3): `builtins.AssertionError`, `builtins.Failed`(pytest `Failed`의 `__module__`은 `"builtins"`다 -- review27 X-01 실측, pytest 9.0.2), 그리고 **신규 심볼**을 import하는 경우에 한해 `builtins.ImportError`·`builtins.ModuleNotFoundError`·`builtins.AttributeError`. 그 밖의 타입으로 된 red는 red로 인정하지 않는다.
  * **신규 심볼 판정**: 입력은 interface card의 '신규 시그니처' 절(N3.12.5)을 **(모듈, 심볼) 쌍** 목록으로 읽은 것이다. 모듈은 점 표기(`topology_authoring`, 패키지면 `a.b`), 신규 모듈 전체면 심볼 `*`. 예외에서 쌍을 만든다: `ModuleNotFoundError` → (`name`, `*`) / `from M import X`의 `ImportError` → (`name`, `name_from`) / `AttributeError` → (`obj.__name__`, `name`)(pytest 9.0.2 실측: 모듈 머리 AttributeError는 `CollectError`로 감싸지지 않고 그대로 온다). 그 쌍이 목록에 있을 때만 신규 심볼 import다 -- 모듈만 대조하면 그 모듈의 오타·삭제된 기존 심볼 ImportError까지 red로 인정된다(review26 T-09, Python 3.14 실측: `from json import NEW_SYMBOL`의 `name`은 `'json'`).
  * `--continue-on-collection-errors`가 필요한 이유: 수집 오류 하나가 세션을 멈추면 같은 실행의 실행 단계 red가 기록되지 않는다(review25 Q-03).
* `outputs_hash` = `commands`를 순서대로 실행한 표준출력 바이트를 이어 붙인 것의 `sha256`. **소비자**: auditor가 격리 복제본에서 base·병합본에 같은 명령을 실행해 대조하고 기록한다(V2 equivalence). merge gate는 형식만 판정한다.
* `test-only`의 증거는 `checks.V2.basis`에 적는다(N4.2 V2).

**로더 규칙**(merge gate 로더. 1~3은 `load_json_checked`(§6.2)와 같은 규칙이다):

1. 파일 머리가 UTF-8·UTF-16(LE/BE)·UTF-32(LE/BE) BOM이면 BOM을 명시해 거부한다(Windows PowerShell 5.1 `Out-File` 기본값이 UTF-16LE BOM이다). 그다음 UTF-8로 디코드하고 실패하면 거부한다.
2. `json.loads(..., object_pairs_hook=중복 키 거부, parse_constant=거부)` -- 중복 키와 `NaN`·`Infinity` 리터럴을 거부한다.
3. 로드 뒤 모든 값을 재귀로 훑는다. 수는 `float(x)`로 바뀌고(`OverflowError`도 거부) `math.isfinite`여야 한다(`1e400`, 401자리 정수). 문자열은 UTF-8로 인코딩되고(짝 없는 서로게이트 거부) 범주 `Cc`(C0·C1 제어 문자)·`Cs` 문자가 없어야 한다.
4. 스키마 검증(`_schema.json`).
5. **로드 대상은 이번 병합의 판정 기록 하나** `.ai/verification/<이번 spec card id>.json`이다(과거 기록을 훑지 않는다). 파일 이름의 id = `id` = `spec_card` 파일 이름의 id.
6. `id`와 `approvals` 원소의 앞 8자리가 실제 날짜(`datetime.strptime(..., "%Y%m%d")`). `approvals`의 id마다 `.ai/approvals/<id>.md`가 있고 §8.2 머리 파싱을 통과한다.
7. `red.test_ids`와 `red.failure_hashes` 길이 같음.
8. `auditor_run.time`이 RFC 3339의 **부분집합** 정규식 `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})(?![\s\S])`(대문자 `T`·`Z`, 윤초 불허)에 맞고 `datetime.fromisoformat`으로 읽힌다(`format: date-time`은 형식 검사기 설치 여부에 따라 강제 여부가 달라지므로 로더가 한다).
9. **보이는 문자 규칙**: `checks.Vn.basis`, `red.test_ids` 원소, `equivalence.commands` 원소, `reproduced_numbers[].name`·`command`, `auditor_run.worktree`·`commands` 원소는 유니코드 범주 `Z*`·`Cc`·`Cf`가 아니고 U+3164·U+115F·U+1160·U+FFA0(한글 채움 문자)도 아닌 문자를 하나 이상 가진다.
10. spec card `Phase`가 base 판 계획서의 `phase_order`(§9.2)에 없으면 거부한다. `checks.Vn.verdict == "N/A"`이면 그 Phase가 `v_intro[Vn]`보다 `phase_order`에서 앞이고, `basis`가 `도입 <Phase>: <사유>` 형식으로 시작하며 그 `<Phase>`가 `v_intro[Vn]`과 같다(N4.2 v5.19 형식). `checks.V4.verdict == "PASS"`이면 `basis`가 `oracle 대조: `로 시작하는 줄을 하나 이상 가진다 -- auditor가 기대값마다(V4 도구가 `UNJUDGED`로 낸 assert 포함) spec card 'oracle 종류와 출처'와 대조한 결과다(V4 (2) 검출기는 확실한 복사만 잡으므로, 계획 N4.2 V4 (2)).

**변경 주체**: 부트스트랩 ①의 초안은 오케스트레이터가 쓰고, 이후 변경은 게이트 변경 spec card와 승인 기록이 있을 때 `gmid-code-author`만 한다(N3.12.2). auditor 경로에서 빠져 있고, auditor의 `.ai/verification/<id>.json`·`<id>/**` 쓰기는 **자기 판정 중인 변경의 id만**이다(`05-role-separation`의 EL1 glob이 disputes의 '자기 변경 id만' 규칙과 같은 방식으로 강제한다). 스키마를 바꾸는 변경의 판정 기록은 **base의 스키마**로 검증한다(바꾼 스키마로 자기 판정을 검증하지 않는다).

### 8.2 승인 기록 `.ai/approvals/_TEMPLATE.md`

N3.12.5의 네 항목(사용자 원문 인용, 날짜, 대상, 범위)을 담는다. V5가 기계로 읽는 부분은 머리 블록뿐이다.

```
---
id: YYYYMMDD-<slug>
date: YYYY-MM-DD
target_kind: diff
target: <diff 해시 64자리 소문자 16진>
diff_base: <40자리 소문자 16진>
diff_head: <40자리 소문자 16진>
diff_path: <경로 하나>
scope: <한 줄>
---
```

* 파서 대상: `.ai/approvals/`에서 이름이 `_`로 시작하지 않는 `.md`(양식 `_TEMPLATE.md`는 제외). 줄 끝은 `\r?\n`이다(autocrlf worktree의 CRLF 체크아웃).
* 머리 규칙: 한 줄에 `key: value` 하나. 값은 `: ` 뒤 전부이고 앞뒤 공백을 뗀다. 주석 줄 금지. 허용 키는 `id`, `date`, `target_kind`, `target`, `diff_base`, `diff_head`, `diff_path`(반복 가능, 한 줄에 경로 하나), `scope`이고 **모르는 키는 거부**한다. 파일은 UTF-8, BOM 없음.
* 값 형식: `id`는 §8.1 `id` 형식이고 파일 이름 `<id>.md`와 같다 / `date`는 `YYYY-MM-DD` 실제 날짜 / `target_kind` ∈ {`diff`, `staged_diff`, `decision`, `plan_tables`} / `scope`는 비지 않음.
* `target_kind: plan_tables`(계획서 판정 표 변경의 승인, §9.1): `target` = 변경 뒤 계획서를 `read_plan_tables`와 쓰기 경로표 파서(`05-role-separation` §4·§15.2 -- 쓰기 경로표도 v5.19에서 판정 표 보호 목록에 들었다)로 파싱한 값을 키 정렬 JSON으로 직렬화한 바이트의 `sha256`(64자리 소문자 16진). `diff_*` 키는 금지다. EL3·EL4가 같은 식으로 다시 계산해 대조한다.
* `target_kind: decision`이면 `target`은 결정 ID 목록이고 `,`로 나눈 뒤 각 원소의 공백을 뗀다(예: `U-26, J1`). `diff_*` 키는 금지다.
* `target_kind: diff`이면 `diff_base`·`diff_head`(40자리 소문자 16진)와 `diff_path`(1개 이상, 탭·개행 없음)가 필수이고 `target`은 64자리 소문자 16진이다. **diff 해시**는 diff 출력이 아니라 **blob id**로 만든다 -- diff 출력은 저장소 로컬 설정(`diff.suppressBlankEmpty` 등)에 흔들리고 로컬 설정은 환경 변수로 끌 수 없다(review23·24 실측). 경로를 정렬해 경로마다 `git rev-parse --verify --quiet <commit>:<path>`(없으면 `-`)로 base·head blob id를 얻고, `sha256(UTF-8("".join(f"{path}\t{base_blob}\t{head_blob}\n" for path in sorted(diff_paths))))`이다. blob id는 파일 내용의 해시이므로 같은 내용 변경에는 같은 값이 나온다. 거부: 경로가 정규화되지 않음(`./`, `..`, 역슬래시, 끝 `/`), 양쪽 모두 없음, base·head blob이 같음(바뀌지 않은 경로), `git cat-file -t`가 `blob`이 아님(디렉터리). V5는 같은 식으로 다시 계산해 `target`과 비교한다.
* `target_kind: staged_diff`(커밋과 **함께 들어가는** 승인 -- topology 변경과 `Role: user` 커밋, `05-role-separation` §8.2-5): `diff`와 같되 `diff_head`는 금지다(아직 없는 그 커밋의 id를 적을 수 없다, review30 R-14). `diff_path`는 `.ai/approvals/**`를 뺀 바뀐 경로 전부이고(승인 기록 자신은 해시 입력에서 뺀다 -- 넣으면 해시가 자기 내용에 기댄다), head blob은 EL3에서 index, EL4에서 그 커밋 트리의 blob이다. EL3는 (HEAD, index), EL4는 (첫 부모, 그 커밋)으로 같은 식을 다시 계산해 `target`과 비교한다.
* design 문서의 승인은 `target_kind: diff`이고 `diff_path`는 그 design 문서와 그 문서가 기댄 개정 파일 전부다(§16).
* 본문은 `## 사용자 원문`(인용 블록, 원문 그대로)과 `## 범위 설명` 두 절이다.
* **파서의 위치는 하나**: `tools/gates/merge_gate.py:parse_approval_header`. V5(`weakening_diff.py`)는 이것을 import한다.

---

## 9. 판정에 쓰는 계획서 표 -- V 도입·IC 담당·Phase 순서

내용은 계획서 N4.1·N4.2·N6.1이 정본이고 **사본을 두지 않는다**. 이 표들의 소비자는 검증 도구(merge gate, test)뿐이라 계획서를 직접 읽으면 된다(§2 정정). 사본이 막던 경로 -- 계획서 표 한 칸을 고쳐 검사를 끄는 것 -- 는 EL3와 EL4가 막는다: 이 표들의 **파싱 값이 바뀌면** 승인 기록 필수다(N3.12.4 EL3는 커밋 시점, EL4는 병합 시점).

### 9.1 읽기 함수 (`tools/gates/merge_gate.py`, 부트스트랩 ①)

```python
@dataclass(frozen=True)
class ICPart:
    phase: str
    sub: bool          # 칸의 괄호 안에서만 나오는 Phase

@dataclass(frozen=True)
class PlanTables:
    v_intro: Mapping[str, str]                    # N4.2: V1~V10 → 도입 Phase
    ic_parts: Mapping[str, tuple[ICPart, ...]]    # N4.1: IC1~IC11 → 담당 Phase들
    ic_test: Mapping[str, str]                    # N4.1: IC → '강제 test' 칸의 첫 백틱 토큰(test 함수 이름)
    phase_order: tuple[str, ...]                  # N6.1: Phase 순서

def plan_phase_tokens(cell: str) -> tuple[set[str], set[str]]: ...   # (괄호 밖 토큰, 괄호 안 토큰)
def read_plan_tables(plan_path: str) -> PlanTables: ...               # 표를 못 읽으면 SchemaRejectedError와 같은 뜻의 거부
```

* **어느 판을 읽나**: merge gate는 **base 판** 계획서를 읽는다. 병합하려는 쪽 계획서를 읽으면 그 병합이 자기 판정 규칙을 바꿀 수 있기 때문이다. 계획 개정은 병합된 다음 병합부터 적용된다. test(§9.3)는 자기가 도는 worktree의 계획서를 읽는다 -- 그 계획서의 판정 표가 base와 다르면 이미 EL4가 승인 기록을 요구한다.
* 거부: 표를 못 읽으면 merge gate는 아무것도 판정하지 않고 거부한다(WP-02). N4.3 공격 16 (ii)가 이것을 증명한다.
* **판정 표 변경 검사**(N3.12.4): 앞 판과 뒤 판 계획서를 같은 `read_plan_tables`로 파싱해 **파싱 값**(`v_intro`, `ic_parts`, `ic_test`, `phase_order`와 쓰기 경로표 파싱 값 `write_paths` -- 비교 대상은 `plan_tables` 해시 입력 객체 전체, `05-role-separation` §15.2)이 다르면 변경이다(원문 문장 수정은 변경이 아니다). 두 곳에서 같은 함수로 한다.
  * **EL3(커밋 시점)**: 앞 판 = HEAD, 뒤 판 = staged 계획서. 오케스트레이터의 직접 커밋(계획서 개정의 정상 경로)이 여기서 걸린다. 뒤 판을 못 읽으면 차단.
  * **EL4(병합 시점)**: 앞 판 = base, 뒤 판 = head(병합할 브랜치 끝 커밋). 뒤 판을 못 읽으면 거부.
  * 변경이 있으면 승인 기록(`target_kind: plan_tables`, `target` = 뒤 판 파싱 값의 해시, §8.2)이 필요하다.
  * 두 검사가 뒤 판을 못 읽으면 막으므로 흐름 안에서는 깨진 계획서가 base에 들어가지 않는다. hook을 우회한 커밋 등 흐름 밖에서 base가 깨지면 merge gate는 판정하지 않고 거부하고(공격 16 (iii)), 복구는 사용자가 한다.
  * 부트스트랩 설치(N3.12.6 ④) 전의 계획서 개정에는 hook이 없다 -- 사용자 승인 커밋으로 한다.
  * **상태 기반 검사**(review27 N-03): `git revert`·`cherry-pick`·`merge`·`commit-tree`는 pre-commit hook을 돌리지 않으므로(git 2.52 실측) 변경 시점 검사만으로는 빠지는 경로가 있다. 그래서 merge gate는 병합마다 **현재 base 계획서의 판정 표 파싱 값 해시에 대응하는 `plan_tables` 승인 기록이 있는지**도 확인한다. 어떤 경로로 들어왔든 승인되지 않은 판정 표 상태에서는 병합이 진행되지 않는다. 우회 명령 전수, 해시 직렬화 형식, 승인 기록을 index와 작업 트리 중 어디서 찾는지 등 구현 세부는 `05-role-separation`이 정하고 0.5 공격 재생 케이스로 고정한다(§17).

### 9.2 토큰화와 표 읽기 규칙

* **표 위치**: 절 제목 줄(`### N4.1 `, `### N4.2 `, `### N6.1 `, `### N3.14 `로 시작하는 줄) 아래 **첫 표**. 셀은 이스케이프되지 않은 `|`로 나눈다(`\|`는 셀 안 문자). 행마다 셀 수가 머리 셀 수와 다르면 거부(표 파손 -- review22 N-01이 이 경우였다). 절이나 표를 못 찾아도 거부.
* **토큰화** `plan_phase_tokens`:
  1. 괄호 밖 문자열 = 셀에서 `\([^()]*\)`를 (중첩이 없어질 때까지) 반복해 지운 것. 괄호 안 문자열 = 지운 괄호들의 안쪽.
  2. 각 문자열에서 정규식 `(?<![0-9A-Za-z.\-])(0\.5|[1-5]|6[abc]|7[abc])(?=$|[\s,;:)*~/])`의 모든 일치를 모은다. 뒤쪽은 공백·문장부호·끝만 허용하므로 `2레일`, `0.5는`, `DEC-60`은 토큰이 아니다.
  3. 실측(v5.19 계획서): IC1~IC11·V1~V10의 괄호 밖 집합이 전부 비지 않고, 괄호 안 토큰은 IC7 `{6c}` 하나뿐이며, N6.1은 빈 집합 행이 정확히 `0`·`0(문서)` 둘이다.
* **값 만들기**:
  * `v_intro[Vn]` = N4.2 `도입` 칸의 괄호 밖 토큰. 원소가 정확히 하나가 아니면 거부. 괄호 안 설명(V1의 "0.5는 redteam 스크립트")은 도입 Phase가 아니다.
  * `ic_parts[ICn]` = N4.1 `담당 Phase` 칸의 괄호 밖 토큰마다 `ICPart(phase, sub=False)`, 괄호 안 토큰마다 `ICPart(phase, sub=True)`. "이후 매 Phase"(IC7)는 별도 필드가 필요 없다 -- 표식 Phase 이후 모든 Phase에서 그 test가 활성이기 때문이다.
  * `phase_order` = N6.1 `Phase` 칸에서 토큰 집합이 빈 행을 뺀 나머지 행의 토큰(행마다 정확히 하나, 아니면 거부)을 순서대로. 빈 집합 행은 정확히 둘(`0`, `0(문서)`)이어야 한다 -- 이 두 행은 변경 흐름을 타지 않아 spec card `Phase` 값이 될 수 없다(N6.1 공통 착수 조건 줄의 주).

### 9.3 소비자

* **merge gate**: 로더 규칙 10(§8.1)의 `N/A` 판정이 `v_intro`와 `phase_order`를 쓴다.
* **TS7 xfail**(test-author, CC-3): test 케이스는 자기 담당 Phase와 케이스 키를 표식 `@pytest.mark.gmid_ic("<IC>", phase="<Phase>", case="<case>")`로 단다(parametrize 케이스마다 달 수 있다 -- IC11의 2레일 케이스는 `phase="4", case="rail2"`, 3레일 케이스는 `phase="6a", case="rail3"`, 선행 거부 케이스는 `phase="6a", case="reject"`). 케이스가 하나뿐인 IC는 `case=""`다. 케이스 키 = `"<IC>:<case>"`. conftest가 `--gmid-phase=<Phase>` 옵션(기본값 없음 -- 없거나 `phase_order` 밖이면 수집 오류, V1 실행에서 auditor가 spec card `Phase`를 넘긴다)과 비교한다. **xfail 조건**: 표식 Phase가 현재 Phase보다 뒤이거나, **같고 그 케이스 키가 엄격 대상이 아닐 때**다(reason = `"<IC> -- 담당 Phase <phase> -- 만료: <phase> DoD"`, N3.12.3 '만료 = 그 Phase DoD'). 표식 Phase가 현재보다 앞이면 언제나 활성이다. **엄격 대상**(표식 Phase = 현재 Phase인 케이스에만 뜻이 있다):
  * `--gmid-dod`: 그 Phase DoD 판정 실행 -- 표식 Phase가 현재 Phase인 케이스 전부.
  * `--gmid-strict=<IC:case,...>`: **이번 spec card의 '활성화 IC 케이스' 필드(N3.12.3) ∪ 같은 Phase에서 이미 병합된 card들의 그 필드**. 누적이므로 활성화된 케이스를 뒤 card가 다시 깨면 그 card의 V1에서 FAIL한다(review26 T-02).
  * **merge gate가 이 집합을 계산한다**: base의 판정 기록 중 spec card `Phase`가 같은 것들의 spec card 필드와 이번 spec card 필드의 합집합. 그리고 판정 기록 `auditor_run.commands`의 V1 명령에 `--gmid-phase=<Phase>`와 정확히 그 집합(정렬, 쉼표 구분)의 `--gmid-strict`가 있는지 대조한다. 다르면 거부(auditor가 빠뜨려도 조용히 통과하지 않는다). **CC-3 병합 전**(conftest에 `--gmid-*` 옵션이 아직 없을 때)에는 이 대조를 하지 않는다 -- 옵션을 주면 pytest가 모르는 옵션으로 끝나고 빼면 거부되어 Phase 1 앞쪽 card가 모두 막히기 때문이다(review27 N-02). 그때는 엄격 대상도 없다(xfail 선언 자체가 CC-3에서 생긴다).
  * **모르는 케이스 키 거부**: conftest는 `--gmid-strict`에 들어온 키마다 수집된 test 중 그 `gmid_ic` 표식(IC·case)이 있고 그 표식 Phase가 현재 Phase인지 확인하고, 아니면 수집 오류로 끝낸다(오타 키·표식 없는 키·Phase가 맞지 않는 키가 조용히 통과하지 않게 -- review27 N-01. 모의 실측에서 동작 확인). 케이스 키 이름을 바꾸는 test 변경은 그 Phase에서 이미 병합된 spec card 필드의 옛 키를 무효로 만들므로, 그 변경의 spec card가 옛 키 → 새 키 대응을 '활성화 IC 케이스' 필드에 함께 적는다.
  엄격 대상 케이스는 xfail 없이 PASS여야 한다. 그래서 담당 Phase의 앞쪽 card는 막히지 않고, 케이스를 활성화하는 card부터 그 Phase의 모든 뒤 card와 DoD에서 PASS가 확인된다. 같은 Phase에 표식이 같은 케이스 둘(IC11 `reject`·`rail3`)은 각자 활성화 card에서 따로 엄격해진다(review26 T-01). IC11의 선행 거부 케이스(N4.1)는 N4.3 공격 13의 실행 Phase인 `6a` 표식을 단다.
* **표식과 계획서 대조**(test-author, CC-3의 test): IC마다 `ic_test[IC]` 함수에 달린 표식 Phase 집합 = `{p.phase for p in ic_parts[IC]}`. 표식이 계획서에 없는 Phase를 달거나 계획서 Phase에 표식이 없으면 FAIL. 이 test가 읽는 것은 계획서 원본과 test 파일 자신의 표식뿐이라 사본이 없다.
* **N3.14 표**(CC-4): 실패 클래스 표는 **엔진이 실행 중에 쓰므로**(exit code) 엔진이 문서를 읽을 수 없어 코드 상수 `FAILURE_CLASSES`(§7.1)로 둔다. 같은 파일의 test가 `read_plan_tables`와 같은 표 읽기 규칙으로 N3.14 표를 읽어 §7.1 키 규칙으로 만든 {키: (예외 클래스 이름, exit code, parent)}가 `FAILURE_CLASSES`와 같은지 단언한다(사본이 정당한 유일한 경우라 일치 test를 붙인다).
* oracle (d): spec card '오라클 출처'에 사용자가 승인한 계획서 절과 그 판의 커밋 해시를 적는다.

---

## 10. 성능 측정 명령 (N6.3)

측정 조건은 N6.3이 정본이다. 명령은 이것 하나이고 다른 design 문서와 판정 기록은 이 절을 인용한다.

```bash
$PY skills/analog-gmid-design/assets/tests/tools/measure_search_perf.py \
    --worktree <측정할 worktree 루트> \
    --circuit <파일럿 회로 키(N0.4 '기존 4개 회로'의 파일럿)> \
    --out <측정 worktree 밖의 경로>
```

* **소유**: 도구는 `gmid-code-author`(`tests/tools/`), 도구의 test는 `gmid-test-author`, 실행과 수치는 auditor(N6.3).
* **적용 시작**: CC-7이 병합된 **다음** 동작 변경 spec card부터 card마다 auditor가 audit worktree에서 1회 실행한다(harness background, WP-12). 그 앞 card(TS4, DF-35·36, CC-4 앞부분, CC-7 자신 -- Phase 4 순서는 §11.1)는 card 단위 측정을 하지 않는다. N6.3의 요구는 Phase 단위('Phase 4부터 매 Phase 보고')이므로 Phase 4 보고는 Phase 4의 마지막 병합 card에서 잰 값으로 채운다.
* **결과 위치와 읽는 쪽**: auditor 부속 산출물 `.ai/verification/<spec card id>/perf.json`(N3.12.1). N6.3 'Phase 보고'는 그 Phase에서 병합 순서상 마지막 동작 변경 card의 `perf.json`이고, 7b·7c 예산 게이트(DEC-34)는 base 브랜치 first-parent 병합 순서상 최신 `perf.json`을 읽는다.
* **선행 조건**: DF-35·DF-36(하네스·산출물 절대 경로)과 아래 계측 인터페이스(CC-7).

### 10.1 계측 인터페이스(엔진 쪽, CC-7)

* 운영 진입점 `run_gmid_design_pipeline(spec, *, search, output_dir, instrument=None, activations_out=None)`(MOD10). `search`는 탐색 설정(`grid_points_per_theta`, `search_method`, `slsqp_kwargs` -- 지금 `SPECS[circuit]`에 있고 spec에는 없는 값)이다. 하네스 `run()`은 `spec_fn()` 반환값에 자기 기본값(`floorplan_target`, `max_layout_retry_rounds`)을 채운 spec과 `search`를 이 진입점에 넘기고, 받은 `output_dir`·`instrument`·`activations_out`을 그대로 넘긴다.
* `instrument`는 세 메서드를 갖는다: `on_start(spec, search)`(진입점이 실제로 쓸 spec과 탐색 설정으로 한 번 부른다), `wrap_search(fn) -> fn`, `wrap_evaluate(fn) -> fn`.
* **감싸는 지점은 각각 한 곳이다**:
  * `wrap_evaluate`: 평가 커널 빌더(Phase 3 전 `_build_theta_evaluator`, 이관 뒤 MOD6의 같은 함수) **안에서 반환 직전에** 평가 함수를 감싼다. 빌더를 부르는 곳이 여럿이어도(2026-09-18 AST: 운영 코드 6곳, `presolve_warm_start`의 재빌드 포함) 모든 평가가 감싸진다.
  * `wrap_search`: θ 탐색 1회 = **레이아웃 수렴 루프를 뺀** θ 탐색 함수 호출. 지금은 `optimize_full_circuit_budget` 안의 인라인 코드(평가 커널 빌더 호출 뒤 grid·slsqp 분기)라 감쌀 함수가 없다(review24 R-05). **CC-7이 이 부분을 함수로 추출한다**(동작 보존 추출이라 그 spec card는 `equivalence`). Phase 3는 이동만 하므로(N3.10 이동 규칙) 추출은 Phase 4다. 추출된 함수의 목적 모듈은 MOD6이다.
  * `instrument`는 인자로 전파하지 않고 진입점이 설정하는 **`contextvars.ContextVar` 하나**(MOD6에 둔다)로 빌더와 탐색 함수에 닿는다. 진입점이 끝나면 되돌린다. `instrument=None`이면 감싸지 않는다(동작 불변).

### 10.2 도구 절차

1. `--worktree`를 `cwd`로 하는 **별도 프로세스**를 띄운다. `sys.path` 맨 앞은 `<worktree>/skills/analog-gmid-design/assets`와 `<worktree>/workspaces`다. 자식 환경은 `PYTHONHASHSEED=1`(TS1 시드 집합의 첫 값)이다. 자식은 하네스 `run(circuit, output_dir=<임시>, instrument=<도구 객체>)`를 부른다(하네스가 운영 경로의 유일한 스크립트 진입점이다).
2. **사전 검사**: `--out`이 측정 worktree 밖이고, import한 운영 경로 모듈의 `__file__`과 하네스의 LUT 경로(`run_harness.LUTFILE`)·library 경로가 모두 `<worktree>` 안이어야 한다. 아니면 `status="failed"`, `failure_class="tool_measurement_setup"`으로 결과를 쓰고 exit 8.
3. 실행 전후 `git -C <worktree> status --porcelain`이 같아야 한다. 다르면 `failed`(`tool_worktree_dirty`, exit 8). 결과 파일은 **이 대조가 끝난 뒤** `--out`에 쓴다.
4. `wrap_search`: `time.perf_counter`로 잰 값이 `wall_clock_s`다. 진입점 호출 전체도 따로 재서 `pipeline_wall_clock_s`로 적는다(레이아웃 수렴 포함). 둘 다 적으므로 N6.3 '탐색 1회 wall-clock'은 `wall_clock_s`다.
5. `wrap_evaluate`: 호출마다 (시간, 결과)를 모은다. 실패한 호출도 넣는다. `eval_count` = 감싼 평가 함수의 호출 수(탐색 쪽 캐시가 막지 않은 호출 전부 = 캐시 미스, 실패 재평가, 캐시를 거치지 않는 경로).
6. **예외**: 진입점 호출 전체를 잡는다(로드 게이트 `SchemaRejectedError`, 레이아웃 단계 예외 포함). `status="failed"`, `failure_class` = `FAILURE_CLASSES`에서 찾은 분류 이름(없으면 `tool_unexpected:<모듈.클래스>`)을 쓰고, 도구는 `exit_code_for(exc)`로 끝난다.

### 10.3 출력 JSON

`{circuit, commit, pythonhashseed, spec_digest, topology_digest, lut_digest, search, status, failure_class, wall_clock_s, pipeline_wall_clock_s, eval_count, eval_median_s, eval_times_s, eval_outcomes, machine{platform, processor, cpu_count, python, numpy}}`

* `pythonhashseed` = 자식에 준 값(1). `status` ∈ `ok` / `failed`, 실패해도 파일을 쓴다(WP-11). `eval_outcomes[i]` ∈ `ok` / 실패 레코드 class 이름.
* `spec_digest` = `on_start`가 받은 spec을 키 정렬 JSON으로 직렬화한 바이트의 `sha256`. LUT 객체는 문자열 `"lut:<lut_digest>"`로 바꾸고, 그 밖의 직렬화할 수 없는 값이 있으면 `failed`(`tool_measurement_setup`). 엔진 레지스트리의 `spec_fingerprint`(등급 R2, 해상도 키만 봐서 스펙 동일성을 뜻하지 않는다)는 쓰지 않는다. 이 계산은 도구 안의 함수다.
* `search` = `on_start`가 받은 탐색 설정 그대로. `topology_digest` = topology 파일 바이트 `sha256`. `lut_digest` = `run_harness.LUTFILE` 파일 바이트 `sha256`.
* 6b 첫 작업의 cProfile 계측(N6.1 6b)은 `--profile <path>` 옵션으로 같은 도구에 더한다(6b design이 옵션을 켠다).

**도구 exit code**(N3.14 exit code와 겹치지 않게 그 다음 번호부터, 도구 실패 분류 순서대로): 0 = 측정 완료·무동작 PASS / N3.14 예외는 `exit_code_for` 값 / 8 = `tool_measurement_setup`·`tool_worktree_dirty` / 9 = 무동작 FAIL(`tool_noop_fail`) / 10 = 결정론 FAIL(`tool_nondeterministic`).

---

## 11. 무동작 판정 방법 (N0.4 '무동작 증명')

정의는 N0.4다(발동 계수 0 + 그 회로의 산출물이 Phase 전후 동일). 이 절은 두 조건을 재는 방법이다.

### 11.1 대상과 입력

* 대상: spec card 'library 회로 적용 여부'(N3.12.3)에서 **기능이 필요 없다고 적은 회로** 전부.
* **적용 시작**: CC-8이 병합된 다음 동작 변경 spec card부터 card마다 적용한다. 그 전에 병합되는 Phase 4 card가 비지 않도록 Phase 4 순서를 **TS4 → DF-35 → DF-36 → CC-4 앞부분(실패 클래스·`FailureRecord`·`exit_code_for`, DF-37의 하네스 `run()` 몫) → CC-7·CC-8 → 나머지**로 둔다(N6.1 Phase 4 행 v5.19). 두 도구의 실패 처리와 oracle이 CC-4 앞부분에 기댄다. 그 앞 card의 무동작은 이렇게 다룬다: TS4는 test만 바꾸므로 엔진 산출물이 바뀌지 않는다. DF-35·DF-36은 library 회로 전부에 필요한 수정이다(경로·산출물 형식, 무동작 대상 회로가 없다). CC-4 앞부분은 실패 경로(예외 클래스·exit code)만 바꾸므로 성공한 실행의 산출물은 그대로이고, 그 증거는 성공 경로의 `equivalence`(그 spec card)다. CC-7·CC-8의 엔진 쪽 변경(계측 인자, θ 탐색부 추출)은 인자 기본값에서 동작 불변이고 그 증거는 각 spec card의 `equivalence`다. 옛 커밋에 도구를 소급 적용하지 않는다(review24 R-01: 옛 커밋에는 인자·경로 수정이 없어 실행되지 않는다).
* spec card 필드 '무동작 판정 입력'(N3.12.3): 볼 **발동 계수 ID 목록**(1개 이상 -- 비어 있으면 FAIL. 조건이 공허하게 참이 되지 않게)과, 병합본이 더하는 **새 산출물 필드마다의 무발동 값**.

### 11.2 산출물을 만드는 진입점

도구가 생기는 Phase 4는 Phase 3(모듈 분할) 뒤라 진입점은 하나다.

| Phase | 사이징 스펙 선언 회로 | 스펙 미선언 회로 |
|---|---|---|
| 4 ~ 6a 전 | 하네스 `run(circuit, output_dir=…, activations_out=…)` → MOD10 진입점(§10.1) | 실행 경로 없음 -- 무동작 판정 대상이 되지 않는다 |
| 6a 이후 | 같은 진입점 | 6a 구조 진입점(`structure.json`까지. 이름과 인자는 6a design, `output_dir`·`activations_out`을 같은 뜻으로 받는다) |

진입점은 `activations_out` 경로에 `activations`를 쓴다(엔진은 경로만 받고 spec card를 모른다). 이 인자는 CC-8과 같은 변경 단위에서 더한다.

### 11.3 발동 계수

* `activations: {<ID>: int}`는 **비교 대상 산출물에 쓰지 않는다**. 도구가 준 `activations_out` 임시 경로에만 쓴다. 섞어 쓰면 새 계수 키 자체가 산출물 차이가 된다.
* 조건: spec card가 적은 ID 전부의 계수가 병합본에서 0. 적은 ID가 `activations`에 없으면 FAIL이다(계수기가 배선되지 않은 것이다, WP-01).

### 11.4 산출물 동일

* **비교 대상**: `output_dir`에 생긴 JSON 산출물 `*.instance.json`, `*.structure.json`. HTML 보고서는 비교하지 않는다(JSON에서 생성되는 표시물이다).
* **정규화**: 키 정렬, 들여쓰기 없음, 실수는 파이썬 `repr` 직렬화 바이트.
* **경로 누출 검사**: 산출물을 JSON으로 파싱해 모든 문자열 값을 훑고, `os.path.normcase(os.path.normpath(x))`가 `<worktree>` 루트나 `output_dir`의 같은 정규화 값으로 시작하거나 그것을 포함하면 FAIL(`tool_noop_fail`, detail "경로 누출" -- DF-36 위반. 치환해서 넘기지 않는다). 원시 바이트에서 찾지 않는다(JSON 이스케이프 때문에 놓친다).
* **판정식**: `sha256(정규화(base 산출물)) == sha256(정규화(병합본 산출물))`. **허용오차 없음** -- 기능이 발동하지 않았으면 그 회로의 계산 경로는 바뀌지 않았으므로 비트 단위로 같아야 한다. 계산 경로를 공유하는 리팩터링은 무동작 증명이 아니라 `equivalence`다(N3.12.3).
* **새 필드**: 병합본을 base 구조로 투영해 비교한다. 투영은 재귀다 -- 매핑은 base에 있는 키만 남기고, 리스트는 길이가 같아야 하며 원소별로 투영한다(길이가 다르면 FAIL). 투영으로 빠진 키 각각은 spec card의 무발동 값과 같아야 한다. 선언이 없으면 FAIL이다(WP-02).
* **예외로 끝난 실행**: base와 병합본이 모두 예외로 끝나면, 두 `FailureRecord.to_json()`의 정규화 해시가 같을 때만 PASS다(같은 실패가 같은 곳에서 났다). 한쪽만 예외이거나 레코드가 다르면 FAIL. 예외 실행에는 산출물 비교를 하지 않는다.
* **결정론 사전 검사**: base와 병합본을 각각 `PYTHONHASHSEED` 1~5(TS1과 같은 시드 집합)로 실행해, 각 쪽 다섯 해시가 모두 같아야 한다. 다르면 이 방법을 쓸 수 없다 -- `tool_nondeterministic`으로 FAIL하고 비결정 산출물을 DF로 올린다(NFR-4). 비교에는 시드 1의 산출물을 쓴다.

### 11.5 도구와 명령

`skills/analog-gmid-design/assets/tests/tools/noop_proof.py`(code-author 구현, test-author test). §10.2 절차 1~3(별도 프로세스, 경로 사전 검사, worktree 청결)를 base와 병합본 각각에 적용한다.

```bash
$PY skills/analog-gmid-design/assets/tests/tools/noop_proof.py \
    --base-worktree <base worktree> --head-worktree <audit worktree> \
    --circuit <circuit> --spec-card <spec card 경로> \
    --out <두 worktree 밖의 경로>
```

auditor는 결과를 `.ai/verification/<spec card id>/noop-<circuit>.json`에 둔다(N3.12.1 부속 산출물).

* **IC7 계약 test와의 관계**: IC7 `test_all_library_topologies_run`은 worktree 하나 안에서 돈다. 이 test가 이 도구에서 쓰는 것은 **발동 계수 부분**(§11.3, 필요 없는 기능의 계수 0)뿐이고, base와의 산출물 비교(§11.4)는 auditor가 이 명령으로 한다. 계약 test가 code-author 도구의 함수에 기대는 구조이므로, 그 함수 자체는 CC-8의 test-author test(합성 입력으로 FAIL을 보이는 red)가 지킨다(WP-13).

---

## 12. 판정식 모음 (N9.2-3)

| 판정 | 식 | 입력 | 절 |
|---|---|---|---|
| margin | `magnitude / tol`, `tol ∈ {None, 0}`이면 `None` | N3.14 정규화식의 분모 | §7.2 |
| exit code | `FAILURE_CLASSES`에서 `type(exc).__mro__` 첫 등록 클래스의 값, 없으면 1 | 예외 | §7.1 |
| 평가 시간 중앙값 | `statistics.median(eval_times_s)`(실패 호출 포함) | §10 출력 | §10 |
| 무동작 | 지정 ID(1개 이상) 계수 전부 0 ∧ 경로 누출 없음 ∧ 정규화 해시 같음(양쪽 예외면 실패 레코드 해시 같음) ∧ 양쪽 결정론 사전 검사 통과 | §11 | §11 |
| diff 해시 | `sha256(경로별 "path\tbase_blob\thead_blob\n"의 정렬 연결)` | 승인 기록 머리 | §8.2 |
| red 재현 | `red_failure_hash(test_id, exc_type)` 일치 | 판정 기록 `red` | §8.1 |
| Phase 토큰 | §9.2 정규식, 괄호 밖/안 분리 | 계획서 표 셀 | §9.2 |

수치 기준(예산 등)은 이 문서에 두지 않는다(WP-03).

---

## 13. 코드로 만드는 것 목록

| 표 | 위치 | 구현 소유 | 첫 소비자(같은 변경 단위) | Phase |
|---|---|---|---|---|
| 판정 기록 스키마 | `.ai/verification/_schema.json` | `오케스트레이터`(부트스트랩 ① 초안), 이후 `gmid-code-author` | merge gate 로더 | 지금 초안, 소비 0.5 |
| 승인 기록 양식 | `.ai/approvals/_TEMPLATE.md` | `오케스트레이터` | `parse_approval_header`(V5) | 지금 생성, 소비 0.5 |
| 로더, `read_plan_tables`, `plan_phase_tokens`, `parse_approval_header`, `red_failure_hash`, red 수집 플러그인 | `tools/gates/merge_gate.py` | `오케스트레이터`(부트스트랩 ①) | merge gate | 0.5 |
| `SchemaRejectedError`, `FailureRecord` | MOD2 | `gmid-code-author` | 로드 게이트, 진입점 exit code | 4 |
| N3.14 예외 계층, `FAILURE_CLASSES`, `CANDIDATE_FAILURE_CLASSES`, `exit_code_for` | MOD4 | `gmid-code-author` | 진입점 exit code | 4 |
| `LEGACY_NAMES`, `JSON_KINDS`, `load_json_checked`, `reject_legacy_names` | MOD2 | `gmid-code-author` | MG1 로드 게이트 | 4 |
| 계측 인터페이스(`search`, `output_dir`, `instrument`, `activations_out`, `ContextVar`), θ 탐색부 추출 함수 | MOD10 진입점, MOD6 빌더·탐색 함수, 하네스 `run()` | `gmid-code-author` | CC-7·CC-8 도구 | 4 |
| `normalized_margin` | MOD2 | `gmid-code-author` | 실패 캐시 정렬 | 5 |
| `DOMAINS` | MOD2 | `gmid-code-author` | S1 엣지 `domain` 로드 검사 | 6a |

---

## 14. 역할별 산출물 -- 작업 묶음 목록 (N9.2-5)

아래 CC는 **작업 묶음**이다. 발행 문서가 N3.12.3 단위(red 하나로 판정되는 관찰 가능한 계약 하나 = spec card 한 건)로 spec card를 나눈다. 판정 유형·oracle은 묶음 안의 spec card가 따를 기본값이다. 부트스트랩 산출물(CC-1·CC-2)은 spec card가 아니라 N3.12.6 ①~③(작성 → 거부 증명 → 승인 기록)으로 들어간다.

| ID | 내용 | 판정 유형 | 구현 소유 / 판정 기준 소유 | oracle | 발행 문서 |
|---|---|---|---|---|---|
| CC-1 | merge gate 로더(§8.1 로더 규칙 전부 + diff·`staged_diff`·`plan_tables` 해시 재계산 -- red·outputs 해시는 auditor가 재고 gate는 형식만), red 수집 플러그인, `parse_approval_header`, `red_failure_hash`, diff 해시 재계산(V5), U-38 의존성 선언 | 부트스트랩 | `오케스트레이터` / `사용자`(N4.3 공격 15 거부 로그) | 공격 15 케이스는 `tools/gates/redteam/`에 데이터로 두고 케이스마다 기대(거부/통과)를 적는다: 로더 규칙마다 거부 케이스 1개 이상 + review21·22·23 독립 검증 케이스(보고서 표에서 옮긴다) + 오거부 0 = 올바른 기록 3종 | `05-role-separation` |
| CC-2 | `read_plan_tables`·`plan_phase_tokens`(§9.1·§9.2), 표 파손 거부, EL4의 판정 표 diff 승인 검사 | 부트스트랩 | `오케스트레이터` / `사용자`(N4.3 공격 16) | (d) 계획서 N4.1·N4.2·N6.1 | `05-role-separation` |
| CC-3 | conftest `--gmid-phase`·`--gmid-strict`·`--gmid-dod` 옵션, `gmid_ic` 표식(케이스 키)과 xfail 생성, 표식-계획서 N4.1 대조 test(§9.3) | test-only가 아니라 TS7 선언의 일부(N3.11 TS7, Phase 1) -- 대조 test의 red는 표식이 계획서와 다른 합성 test 파일에서 FAIL | `gmid-test-author` / `사용자`(계획서 N4.1 승인) | (d) 계획서 N4.1(승인 판 커밋 해시) | `10-test-separation` |
| CC-4 | **앞부분**(Phase 4에서 CC-7·CC-8보다 먼저): §7.1(MOD2·MOD4 형식), 진입점 exit code(DF-37의 하네스 `run()` 몫), §9.3 N3.14 부분. **나머지**: DF-37 광범위 except 재raise | red-green | `gmid-code-author` / `gmid-test-author` | (a) 예외 계층·exit code 불변식, (d) 계획서 N3.14 | `40-defect-fixes` |
| CC-5 | `LEGACY_NAMES`·`JSON_KINDS`·`load_json_checked`·`reject_legacy_names`로 `validate_no_legacy_vs_key`와 파일 읽기 `json.load` 전부 대체, 깊은 복사 관용구를 `copy.deepcopy`로(TS1 뒤 AST 계수가 0이면 해당 없음)(MG1 단위) | red-green | `gmid-code-author` / `gmid-test-author` | (d) 계획서 N3.16에서 test-author가 옮긴 기대 목록 | `40-defect-fixes` |
| CC-6 | `DOMAINS`와 S1 엣지·metric 선언 `domain` 로드 검사, IC5 허용 영역 문자열 = `DOMAINS` 대조 test | red-green | `gmid-code-author` / `gmid-test-author` | (a) 값 집합 밖·누락 거부 | `6a-structure-stage` |
| CC-7 | θ 탐색부 함수 추출(`equivalence` card) + 계측 인터페이스(§10.1) + 성능 측정 도구(§10.2·§10.3). DF-35·CC-4 앞부분 뒤 | red-green | `gmid-code-author` / `gmid-test-author` | (a) 구성으로 정답이 정해진 합성 입력(N0.4 (a)): worktree 밖 경로 설정 → exit 8, 탐색이 예외를 내게 한 입력 → `status=failed`·파일 존재·그 예외의 exit code | `40-defect-fixes` |
| CC-8 | `activations_out` 인자 + 무동작 판정 도구(§11). DF-35·36·CC-4 앞부분 뒤 | red-green | `gmid-code-author` / `gmid-test-author` | (a) 구성으로 정답이 정해진 합성 입력: 발동 1건 → exit 9, 무발동 값 선언 없는 새 필드 → exit 9, 시드에 따라 달라지는 필드 → exit 10, 빈 ID 목록 → exit 9 | `40-defect-fixes` |
| CC-9 | `normalized_margin`(§7.2) | red-green | `gmid-code-author` / `gmid-test-author` | (a) 손계산(분모 0·`None` → `None`) | `50-failure-cache` |

---

## 15. DoD 측정 명령 (N9.2-6, N6.2 `0(문서)`)

| 완료 조건 | 명령 | 통과 기준 |
|---|---|---|
| `_schema.json`이 있고 스키마 밖 필드를 거부함 | 독립 검증 agent가 자기 케이스로 `jsonschema.Draft202012Validator(schema, format_checker=FormatChecker())`를 실행한다. 작성자 스크립트 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/common00_schema_reject_check.py`(결과 `.txt`에 append)는 참고다(WP-13) | 올바른 기록 3종(red-green·equivalence·test-only) 통과, 스키마 담당 거부 케이스 전부 거부. 로더 담당 케이스(§8.1 로더 규칙)는 기록만 |
| `_TEMPLATE.md`가 있음 | `test -f .ai/approvals/_TEMPLATE.md` | 존재 |
| 공통 정의가 한 곳에 모임 | 이 문서 §3~§12 | 독립 검증 agent가 N9.1 `00-common` 행의 항목 전부를 이 문서 절에 대응시킴 |
| V/IC 표·Phase 순서 | 이 문서 §9 | 검증 도구가 계획서에서 직접 읽는 규칙(사본 없음, 표 내용의 정본은 N4.1·N4.2·N6.1) |
| 성능 측정 명령이 실행 가능한 형태로 한 곳에 고정됨 | 이 문서 §10 | 명령·출력 형식·절차가 한 절에 있음. 도구 자체는 CC-7(Phase 4) |

"이후 design 문서가 재서술하지 않고 인용함"은 각 design 문서의 독립 검증 항목이다(N6.2 `0(문서)`).

---

## 16. 착수 조건 확인 (N9.2-7)

* N6.1 `0(문서)` 착수 조건(N0.4·DEC-67·68·69·N3.12.5·N3.14·N4.1·N4.2·N6.3 확정) → 계획서 v5.19.
* 관련 U: U-38 확정(승인 기록 `20260918-u38-jsonschema`). J: 없음.
* 이 문서의 승인 기록은 사용자 승인 시 `.ai/approvals/<승인일>-00-common-design.md`로 만든다. `target_kind: diff`이고 `diff_path`는 이 문서, 계획서·history(v5.19 개정), `.ai/verification/_schema.json`, `.ai/approvals/_TEMPLATE.md` 다섯이다(한 승인이 이 문서와 그것이 기댄 개정을 함께 덮는다). blob 해시는 커밋된 내용을 덮으므로 승인 기록은 **이 문서와 개정이 커밋된 뒤**에 그 커밋을 `diff_head`로 만든다.

---

## 17. 열린 질문 (N9.2-8)

없음. 이 문서가 정하지 않고 넘긴 것은 넘긴 곳이 정한다(그 문서의 착수 범위다):

| 넘긴 것 | 정하는 곳 |
|---|---|
| S1·S2 필드 이름, 6a 구조 진입점 이름 | 6a·6b design |
| `qualifier` 값 모양과 거부 함수 | 봉인 전 값을 처음 내는 design(6b 또는 7b) |
| 기존 `InfeasibleSizingError` raise 지점의 분류 | `40-defect-fixes` |
| 레지스트리·N3.10의 `optimize_full_circuit_budget` 목적지 불일치(MOD6 대 MOD8) | `30-module-split` |
| EL1 glob('자기 변경 id만'), EL3 허용 조합표, U-38 의존성 선언 파일·버전 | `05-role-separation` |
| **게이트 구현 세부**: hook을 거치지 않는 git 명령 전수와 그 차단·상태 검사 방법, `PlanTables` 해시의 직렬화 형식과 계산 CLI, 승인 기록을 index·작업 트리 중 어디서 찾는지, 옛 승인 표로 되돌리는 변경의 처리, V1 명령 식별 방법과 빈 엄격 집합 표기, 신규 하위 모듈·클래스 속성·인스턴스 속성 import의 신규 심볼 판정, EL3 판정 표 검사의 구현 주체(review27 N-04~N-10). 이 문서는 원칙(무엇을 막는가)만 정하고, 동작은 0.5 공격 재생의 실행 증거로 고정한다(WP-21 -- 산문 규정은 게이트가 실제로 거부한다는 증거를 대신하지 못한다) | `05-role-separation` |
| 각 CC의 spec card 분할 | 발행 문서(§14) |

이 문서를 쓰며 드러난 계획서 빈칸은 v5.19에서 닫았다(history '`00-common` 구성안 C와 v5.19 계획 보완').

---

## 18. 구현 안내

### 18.1 순서

이 문서가 지금 만드는 것은 양식 둘(§8)이다. 나머지는 §14가 각 Phase에서 만든다. 순서는 N6.1: CC-1·CC-2(0.5 부트스트랩) → CC-3(1) → Phase 4: TS4 → DF-35 → DF-36 → CC-4 앞부분 → CC-7·CC-8 → CC-4 나머지(DF-37 광범위 except)·CC-5와 나머지 DF → CC-9(5) → CC-6(6a).

### 18.2 Module Map

| 모듈 키 | 내용 | 발행 문서 |
|---|---|---|
| `common-forms` | §8 양식 둘 | 이 문서 |
| `common-gate-tables` | CC-1, CC-2 | `05-role-separation` |
| `common-ic-table` | CC-3 | `10-test-separation` |
| `common-failure-legacy` | CC-4, CC-5 | `40-defect-fixes` |
| `common-measure` | CC-7, CC-8 | `40-defect-fixes` |
| `common-margin` | CC-9 | `50-failure-cache` |
| `common-domain` | CC-6 | `6a-structure-stage` |

### 18.3 Session Guide

`common-forms`만 이 세션 범위다. 다른 모듈은 발행 문서의 Phase 세션에서 구현한다(`/pdca do gain-budget-gmid-sizing --scope <모듈 키>`).
