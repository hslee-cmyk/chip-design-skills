# agent-kit-routing-canon Planning Document

> **Summary**: RTL agent가 쓰는 일반 지식(라우팅 표·방법론·형식검증 템플릿·근거 사례)의 정본을 ai-memory로 모으고,
> 라우팅 지식의 3중 사본(bug-class-router.py·taxonomy·methodology §6)을 taxonomy 한 곳으로 단일화한다.
> agent·skill이 읽는 경로(`~/.claude/agent-kit/*`)는 유지하고 그 자리에는 ai-memory 배포본(생성물)을 둔다.
>
> **Project**: chip-design-skills (+ ai-memory, venezia-fpga 연동)
> **Version**: 0.1
> **Author**: HSLEE
> **Date**: 2026-11-11
> **Status**: Approved (2026-11-11)

---

## 1. Overview

### 1.1 배경 (2026-11-11 실측)
| # | 문제 | 위치 |
|---|---|---|
| P1 | 라우팅 표 3벌, 단위가 다름(class 단위 vs signature 단위) | `agent-kit/bug-class-router.py` ROUTES · taxonomy R표 · `methodology.md` §6 |
| P2 | 정본 표기가 거꾸로: taxonomy가 "routing 정본: bug-class-router.py" (2곳) | taxonomy 카탈로그·R표 머리말 |
| P3 | 축 혼동: taxonomy `Detect`(정적 확정 가능성)와 route(검증 owner)가 정의 없이 공존 → T4·T5가 Detect SIM / route FORMAL로 모순처럼 보임 | taxonomy 분포표·분류 머리줄 |
| P4 | class 단위 표는 손실: T4는 signature별로 Prover(R1)/sim(R2)로 갈리는데 router는 T4=FORMAL 하나 | router T4 vs R1·R2 |
| P5 | 일반 표에 venezia commit 해시(`example_commit`), 그중 6개는 evidence에 없음. T4는 `05a53c5`(sync-read, router)·`d68ae6a`(prescaler 로드, evidence E5) — 하위 패턴이 다른 두 예시 | router |
| P6 | router 실사용: 최근 6주 세션 실행 0건(Windows 1,614·cloud0 21 jsonl). 코드 호출은 venezia `.ai/experiments/run_regression.py`뿐 | — |
| P7 | `methodology.md`에 일반 방법론 + venezia 실험(§5) + 구축 이력(§8) 혼재, 상대 링크 3개 기존 깨짐 | `agent-kit/methodology.md` |
| P8 | cloud0에 `~/.claude/agent-kit` 미설치 | cloud0 |

### 1.2 결정 (사용자)
- 2026-11-11: failure-taxonomy 정본 = ai-memory `memory/rtl/`, 경로 `~/.claude/agent-kit/failure-taxonomy.md`는 배포본 유지(결정 A, 반영 완료 `fc191c33`/`7c87add`).
- 2026-11-11: methodology·property-library도 같은 방식으로 이동.
- 2026-11-11: evidence도 ai-memory로(권고 A 승인) — 영구메모리 쓰기 규칙을 "원시 instance 금지, 자기완결 정제 사례(코드 발췌·교훈 포함)는 허용"으로 개정.
- 2026-11-11: router 처리 = **A(삭제)**, 라우팅 정본 = taxonomy. 구조 변경 정의·게이트 정책(FR-12), "새 FSM vs 새 state" 판단 기준(FR-13)도 정본 단일화 범위에 포함.

## 2. Scope

### 2.1 In Scope
- ai-memory: taxonomy Routing 절, methodology·property-library·evidence 이동과 배포본, 쓰기 규칙 문언, 골드셋.
- chip-design-skills: agent-kit 정리(이동분 삭제, router 처리, evidence 이관분), `install_kit` manifest, agent 5개 문구, `pre-merge-check.py` 문구.
- 배포: 전역·프로젝트(venezia, alamo-c1) agent 재설치, cloud0 agent-kit 설치.
- venezia: `run_regression.py` router 검사 처리(별도 커밋).

### 2.2 Out of Scope
- `docs/01-plan`의 tb 계획서들에 있는 router 언급(이력 문서) — 이번에 고치지 않음(FR-11에 목록만).
- `boundary-classifier.py`·`harness_builder.py`·`pre-merge-check.py`·`adr-template.md`의 기능 변경(실행 부품, 키트 유지).
- taxonomy T1..T9 정의·signature 내용 자체의 개정.
- **알려진 한계(기록만)**: `boundary-classifier.py` 판정 정규식이 venezia 코딩 스타일(instance `u_` 접두어, FSM state = `` `define `` 매크로 arm)에 묶여 있어 다른 명명 규칙(`localparam`/`enum` state, `u_` 없는 instance)에서는 구조 변경을 LOCAL로 놓칠 수 있다 — 기능 변경이라 별도 과제.

## 3. Requirements

| ID | 요구 | 우선 | 상태 |
|---|---|---|---|
| FR-01 | **taxonomy "Routing (정본)" 절** (ai-memory `memory/rtl/failure-taxonomy.md`): (a) 축 정의 — `정적 확정`(STATIC/비정적: 읽기·lint·elaboration으로 확정 가능한가) ≠ `route`(검증 owner: STATIC-reviewer / FORMAL-prover / SIM-directed / ESCALATE-architect / RECLASSIFY); (b) class 요약표 T1..T9 기본 route·owner·조건, "세부는 S/R signature 표가 우선"; (c) 구조 라벨표 ARCH·IFACE·LOCAL·CDC; (d) "routing 정본: bug-class-router.py" 2곳 → 이 절로; (e) 분포표 `Detect` 열 이름 → `정적 확정` | High | Pending |
| FR-02 | **evidence → ai-memory** `memory/rtl/failure-taxonomy-evidence.md`(kind: evidence): E1~E6 본문 그대로 + 출처 표기("commit·경로는 venezia `db/design`에서만 재현 가능") + methodology §5(실제 RTL formal 실험) + router `example_commit` 이관(class/signature → venezia 예시 commit 표, T4는 `05a53c5`·`d68ae6a` 둘 다 하위 패턴별). 배포본 `~/.claude/agent-kit/evidence.md` | High | Pending |
| FR-03 | **methodology 일반부 → ai-memory** `memory/rtl/methodology.md`: §0~4·6·7·9·10, 모듈명·commit → 일반 표현(사례는 evidence 참조), §6 표 → "정본 = taxonomy Routing 절" 한 줄, 깨진 상대 링크 수정. §8(구축 이력) → 키트 `docs/` 이력 문서. 배포본 `~/.claude/agent-kit/methodology.md`(skill 22곳·agent 경로 불변) | High | Pending |
| FR-04 | **property-library → ai-memory** `memory/rtl/formal-property-library.md`: 내용 그대로, 링크 → `~/.claude/agent-kit/harness_builder.py` 등 절대경로, venezia 실험 링크 → evidence. 배포본 `~/.claude/agent-kit/property-library.md` | Medium | Pending |
| FR-05 | **영구메모리 쓰기 규칙 개정**(ai-memory README·`mcp_server.py` memory_propose 설명·INDEX 도메인 표): "원시 instance(그 repo가 있어야 이해되는 것) 금지, 자기완결 정제 사례 허용(출처·재현 범위 표기)" | High | Pending |
| FR-06 | **router 삭제(결정 A)**: `agent-kit/bug-class-router.py` 삭제. 라우팅은 agent가 taxonomy Routing 절·S/R 표를 직접 읽는다. 구조 라벨 판정(`--commit` 기능)은 기존 `boundary-classifier.py`·`pre-merge-check.py`가 담당 | High | Pending |
| FR-07 | **agent 문구** (키트 `agents/`): coder :11 도구 목록·:195~199 §6 실행 지시 → "taxonomy Routing 절·R표에서 route 확인"; reviewer :27·37·96·121·276·307 `[→bug-class-router.py]` → `[→taxonomy §Routing]`, :136 "정본 = R표 + router" → "정본 = taxonomy"; prover :23·110 "OWN 정본 = router + route 열" → "taxonomy Routing route=FORMAL 행·R표"; architect-advisor :23 도구 목록·구조 라벨 근거 → taxonomy 구조 라벨표; `agents/README.md` :20·61~62 | High | Pending |
| FR-08 | **`install_kit` manifest**: 설치 파일 목록(`~/.claude/agent-kit/.kit-manifest`)을 남기고, 다음 설치 때 목록에 있었으나 키트에서 사라진 파일만 삭제(ai-memory 배포본은 건드리지 않음) | High | Pending |
| FR-09 | `pre-merge-check.py` 안내 문구 → taxonomy Routing 절 | Low | Pending |
| FR-10 | **배포·연동**: `install.py --only kit`·`--only agents`·`--project venezia-fpga`·`--project alamo-c1-test`; venezia `run_regression.py` router 검사 3개 처리(A: 삭제 또는 taxonomy 표 확인으로); cloud0는 키트 병합 시 `--only kit`·`--only agents` | Medium | Pending |
| FR-11 | 이력 문서의 router 언급 목록 기록(수정 안 함): `docs/01-plan/features/verilog-tb-reviewer.plan.md`(4), `verilog-tb-architect-advisor.plan.md`(2) | Low | Pending |
| FR-12 | **구조 변경 정의·게이트 정책 정본 = taxonomy 구조 라벨표**(FR-01(c) 확장): ARCH/IFACE/LOCAL 정의(module·always·case·FSM arm·state·instance 추가/삭제, clock/reset 재배선), 라벨별 정책(ARCH 차단+ADR, IFACE 경고+fan-out 감사, LOCAL 통과→class 라우팅), 큰 변경 기준. `boundary-classifier.py`·`pre-merge-check.py` docstring은 정본 참조로(정규식·가중치 등 구현 세부는 코드 유지). `pre-merge-check.py` 사용법의 깨진 경로(`../../.ai/agent-proposals/…`) → `~/.claude/agent-kit/…` | Medium | Pending |
| FR-13 | **"새 FSM vs 새 state" 판단 기준 → ai-memory**(methodology 일반부 또는 별도 원칙): 책임 분해·동시성·수명 기준과 기본값. `adr-template.md`(양식 칸 유지)·architect-advisor §2.0은 정본 참조 | Medium | Pending |

## 4. Success Criteria
- 라우팅 지식의 정본이 taxonomy 한 곳: 키트 전체 `bug-class-router` 참조 0건(FR-11 이력 문서 제외), taxonomy에 "정본: router" 문구 0건.
- ai-memory eval_gate PASS(신규 문서 골드셋 질의 포함, MRR·P@1 ≥ 0.90), `render_global --check` 배포본 4개(taxonomy·evidence·methodology·property-library) 최신.
- 설치 후 `~/.claude/agent-kit`: 이동·삭제분은 키트 파일로 남지 않고 배포본 4개 존재(Windows·cloud0).
- reviewer agent 실검증 1건: SIM-RISK finding의 owner를 taxonomy 표에서 찾아 라우팅.
- venezia `run_regression.py`가 바뀐 구성에서 실패하지 않음(또는 router 검사 제거가 기록됨).

## 5. Risks
| 위험 | 대응 |
|---|---|
| agent가 표를 잘못 읽어 owner를 틀림(코드 조회가 없어짐, A) | class 요약표 + signature 표의 우선순위 규칙을 표 머리에 명시, 실검증 1건 |
| 배포본을 손으로 고침 | 표지 줄 + `render_global --check`, post-merge 자동 재배포 |
| methodology 일반화 과정의 의미 손실 | 일반화한 문장마다 evidence 절 참조를 남김, 분할안 사용자 검토 후 반영 |

## 6. 진행 순서
1. 이 plan 승인 (2026-11-11 승인, FR-06 = A)
2. ai-memory: FR-01·12·05 → FR-02·03·04·13(methodology 분할안은 반영 전 사용자 검토) → 골드셋·eval → push
3. 키트(브랜치): FR-06·07·08·09·12·13 → master 병합
4. FR-10 배포·venezia·cloud0(보류 중인 cloud0 키트 병합과 함께)
