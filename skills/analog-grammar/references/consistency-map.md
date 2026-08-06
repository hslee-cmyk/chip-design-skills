# Consistency Map

## 사용법

SKILL.md 원칙 수정 시:
1. 아래 맵에서 해당 원칙의 반영 위치 확인
2. 모든 반영 위치를 함께 업데이트
3. SKILL.md 내부 요약(절대 규칙 표, 파이프라인 표, 참조 파일 목록)도 확인
4. **수정 후: `../skill-validation-prompt.md` 절차로 일관성 검증**

## 원칙별 반영 위치

| 원칙 | SKILL.md 섹션 | reference 반영 위치 |
|------|--------------|---------------------|
| LLM에게 "이 회로가 뭐냐" 먼저 안 묻는다(회상 vs 분석) | 절대 규칙 #1 | DESIGN.md §1 |
| ASSUMPTIONS 절 생략 금지, INPUT/BIAS 구조적 미구별 | 절대 규칙 #2 | DESIGN.md §1 "구조적으로 판정 불가능한 단 하나" |
| UNRESOLVED/낮은 coverage는 상류 netlist 의심 신호 | 절대 규칙 #3 | DESIGN.md §4 "Fig.3 부분 성공" |
| 6단계 파이프라인 구조·각 단계 invariant | 파이프라인 표 | DESIGN.md §3 |
| L1 idiom 11종·priority·판정 근거 | (SKILL.md에는 요약 없음, DESIGN.md가 정본) | DESIGN.md §2 표 |
| current-mirror가 gate뿐 아니라 source까지 그룹핑 | (알려진 한계 절 상단부에 미기재 — 별도 강조 없음) | DESIGN.md §2 "주의" 문단 |
| YAML DSL 대신 `@idiom` 데코레이터 레지스트리 | "새 idiom 추가" | DESIGN.md §2 "왜 YAML DSL을 안 썼나" |
| Stage 6a(시그니처)/6b(서술) 분리, LLM은 6b만 | "LLM이 담당하는 것" | DESIGN.md §3 마지막 문단 |
| 새 idiom 추가 시 회귀 테스트 필수 | "새 idiom 추가" | DESIGN.md §6 4번 |
| Fig.2 실증(current-reuse 자동 검출) | (SKILL.md에는 요약 없음) | DESIGN.md §4 |
| 알려진 한계 5종(R/C/L·folded/telescopic·SC·L2·입력 스키마) | "알려진 한계" | DESIGN.md §5(첫 4개), SKILL.md 자체(5번째, 이 skill 반입 특유의 한계라 DESIGN.md에는 없음) |
| 이 프로젝트로 반입된 경위(analog-gmid-design과의 관계) | "Cross-Skill 참조" | DESIGN.md §7 |

## Cross-Skill 참조

| 원칙 | 본 skill | 참조 skill |
|------|---------|-----------|
| 입력 netlist 추출(PDF→netlist) | 워크플로 입력 형식 | `circuit-topology-extraction`(별도 반입 예정) |
| matching 후보(current_mirror/diff_pair) 오탐 재검증 | 절대 규칙 #1 표 (6)번, "Cross-Skill 참조" | `analog-gmid-design` > `references/analog-grammar-integration.md` |

## 마커 규약

- **형식**: `[→DESIGN.md §X]` — 이 skill의 마커는 다른 skill(analog-gmid-design 등)과
  달리 자기 자신의 섹션이 아니라 **항상 `references/DESIGN.md`의 섹션 번호**를 가리킨다
  (analog-gmid-design SKILL.md의 `[→§X]`가 `gm-id-methodology.md`를 가리키는 것과
  동일한 관례).
- **용도**: SKILL.md 절대 규칙 각 항목이 DESIGN.md의 어느 절에서 상세 근거를 갖는지 추적.
- **수정 시**: DESIGN.md 섹션 번호가 바뀌면 SKILL.md의 모든 `[→DESIGN.md §X]` 마커를
  함께 갱신한다.

## 변경 이력

- 2026-08-06 (반입): "아날로그 기능분석기.zip"(analog-grammar 패키지, 원 SKILL.md +
  DESIGN.md + assets 4개 스크립트 + examples 2개)를 이 저장소의 skill 관리 컨벤션에
  맞춰 반입. 원본 대비 변경: (1) 최상위 README.md 제거(이 저장소 Check 6 "폴더 내
  README.md 없어야 함" 규칙, 내용은 SKILL.md에 흡수), (2) `scripts/`→`assets/`
  디렉토리명 변경(다른 skill 컨벤션과 통일), (3) SKILL.md에 "참조 파일"/
  "Cross-Skill 참조" 섹션 신설(analog-gmid-design 연동 명시), (4) DESIGN.md §2 L1
  idiom 표에 "current-mirror가 gate+source를 함께 본다"는 주의 문단과 §7("이 프로젝트로
  반입된 경위") 신설. 코드(`netclass.py`/`idioms.py`/`sfg.py`/`analyze.py`)는
  원본 그대로(바이트 단위 무변경, 회귀 없음).
