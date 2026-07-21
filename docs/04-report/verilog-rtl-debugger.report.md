# verilog-rtl-debugger Completion Report

> **Status**: Complete
>
> **Project**: chip-design-skills
> **Version**: 0.8 (Plan) / 0.2 (Design)
> **Author**: HSLEE
> **Completion Date**: 2026-07-08
> **PDCA Cycle**: #2 (Plan v0.1→v0.6 최초 사이클 + v0.7→v0.8 FR-10 재진입 사이클)

> 이 feature는 Next.js/BaaS 웹앱이 아니라 **markdown agent 정의 파일 1개**(`agents/verilog-rtl-debugger.md`)를
> 만드는 작업이다. 템플릿의 DB/UI/배포 관련 섹션은 N/A 처리했다.

---

## Executive Summary

### 1.1 Project Overview

| Item | Content |
|------|---------|
| Feature | verilog-rtl-debugger |
| Start Date | 2026-07-03 |
| End Date | 2026-07-08 |
| Duration | 6일 (최초 사이클 2026-07-03~07-06 완료 + FR-10 재진입 사이클 2026-07-07~07-08) |

### 1.2 Results Summary

```
┌─────────────────────────────────────────────┐
│  Match Rate: 97% (target: 90%)               │
├─────────────────────────────────────────────┤
│  ✅ Complete:     10 / 10 FR (FR-01~FR-10)   │
│  ⏳ In Progress:   0 / 10                    │
│  ❌ Cancelled:     0 / 10                    │
└─────────────────────────────────────────────┘
```

### 1.3 Value Delivered

| Perspective | Content |
|-------------|---------|
| **Problem** | xcelium-mcp 6-phase 디버깅 워크플로우의 Phase 2~4(시뮬레이션 실행, bisect/CSV 추출, FSM 전이 대조)를 수행할 MCP-tool-aware agent가 없어, 기존 5개 verilog-rtl-* agent(정적 분석/코드 작성 전용)로는 라이브 디버깅을 자율 수행할 수 없었다. |
| **Solution** | `mcp__xcelium-mcp__*` 24개 tool 접근권을 가진 신규 agent `verilog-rtl-debugger`를 신설해 Phase 2~4를 직접 소유하고, 그 외 작업(분석서 작성/RTL 수정/리뷰/formal 증명/아키텍처 판단)은 7개 상황별로 기존 5개 agent + 자매 agent `verilog-tb-analyst`에게 Task()로 위임하는 라우터로 구현했다. |
| **Function/UX Effect** | RTL 디버깅 요청 시 이 agent가 bisect→CSV→FSM 대조 루프를 자율 수행하고, 분석서 갱신·수정 코드 작성처럼 스코프 밖 작업은 자동 위임 — 매번 5개 agent 중 무엇을 호출할지 수동 판단할 필요가 없어짐. v0.8(FR-10)부터는 분석서 staleness(hash 비교)를 phase-2 진입 전에 강제해, 낡은 분석서를 신뢰한 채 디버깅이 진행되는 실패 모드(venezia-fpga T-002에서 실측)를 원천 차단한다. |
| **Core Value** | xcelium-mcp를 쓰는 모든 RTL 프로젝트(venezia-fpga 등)에서 디버깅 결과물의 완성도가 기존 5개 agent의 검증된 품질 기준을 그대로 상속받고, 분석서 캐시가 항상 hash로 검증된 상태로만 신뢰된다. |

---

## 1.4 Success Criteria Final Status

> Plan §4.1/§4.2에서.

| # | Criteria | Status | Evidence |
|---|---------|:------:|----------|
| SC-1 | `agents/verilog-rtl-debugger.md` 작성 완료, 기존 5개 agent와 동일 품질 기준(model 근거, "왜 별도 agent인가") | ✅ Met | `agents/verilog-rtl-debugger.md` §"왜 별도 agent인가"/"왜 model: opus" |
| SC-2 | install.py 배포 등록 + 배포 테스트 | ✅ Met | `install.py --only agents` 실행, `~/.claude/agents/verilog-rtl-debugger.md` 생성 확인(이번 세션 3회 재배포) |
| SC-3 | 위임 매핑표 7개 상황 전부를 올바른 agent에 위임 | ✅ Met | §2 위임표 #1~#7, gap-detector Contract 축 98% |
| SC-4 | FR-10: staleness 체크가 phase-2보다 먼저 강제됨 | ✅ Met | §0 "0. 기준" 순서, §2 공통규칙 staleness 정의, gap-detector 4개 하위항목 전부 PASS |
| SC-5 | venezia-fpga 실사용 시나리오 검증 | ⚠️ Partial | 미실행 — 실제 프로젝트 세션 필요, 이번 PDCA 사이클 범위 밖 |

**Success Rate**: 4/5 criteria met (80%) — 나머지 1건은 실사용 검증으로 다음 세션 이관.

## 1.5 Decision Record Summary

| Source | Decision | Followed? | Outcome |
|--------|----------|:---------:|---------|
| [Plan] | MCP tool 24개 전량 부여(Option C, 문서화된 사용 규율) | ✅ | 라이브 루프 중단 위험 없음, "자주 사용/확인 후 사용/필요 시" 3단 규율로 tool 목록 비대화 완화 |
| [Plan] | Phase 2~4 방법론 비내장 — 런타임 Read | ✅ | `~/.claude/skills/xcelium-sim/references/*.md` 5개 파일 매 실행 Read, drift 자동 반영 |
| [Design] | 6개 위임 대상 Task() 계약 확정, TB 행은 tb-analyst Design 재사용 | ✅ | §2.2/§4.1, Contract 축 98~100% |
| [Plan v0.8] | FR-10: staleness 체크 phase-2 선행 강제 + `tb_provenance` 6번째 파라미터 | ✅ | Do 재진입으로 반영, gap-detector 재검증 97% |
| [/simplify] | BLOCKER 규칙·cloud0 drift 사례의 파일 내/파일 간 중복 서술 정리 | ✅ | 동작 변경 없이 문서 간결화, tb-analyst.md 상호 참조로 전환 |

---

## 2. Related Documents

| Phase | Document | Status |
|-------|----------|--------|
| Plan | [verilog-rtl-debugger.plan.md](../01-plan/features/verilog-rtl-debugger.plan.md) (v0.8) | ✅ Finalized |
| Design | [verilog-rtl-debugger.design.md](../02-design/features/verilog-rtl-debugger.design.md) (v0.2) | ✅ Finalized |
| Check | [verilog-rtl-debugger.analysis.md](../03-analysis/verilog-rtl-debugger.analysis.md) | ✅ Complete (97%) |
| Report | 현재 문서 | ✅ Complete |

---

## 3. Completed Items

### 3.1 Functional Requirements

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-01 | frontmatter (name/description/tools/model) | ✅ Complete | |
| FR-02 | Tool 목록: MCP 24개 + Read/Glob/Grep + Task, Write/Edit 없음 | ✅ Complete | |
| FR-03 | 7개 위임 상황 라우팅 규칙 | ✅ Complete | |
| FR-04 | Phase 2~4 방법론 비내장, 런타임 Read | ✅ Complete | |
| FR-05 | RTL 분석서 부재/stale → verilog-rtl-analyst 위임 | ✅ Complete | |
| FR-06 | 근본원인 확정 → coder → reviewer 체인 | ✅ Complete | |
| FR-07 | 라이브-디버깅 특화 Trigger, 기존 5개와 비충돌 | ✅ Complete | |
| FR-08 | install.py 등록 | ✅ Complete | |
| FR-09 | TB 분석서 부재/stale → verilog-tb-analyst 위임(+ fallback) | ✅ Complete | |
| FR-10 | staleness 체크 phase-2 선행 강제 + `tb_provenance` 파라미터 + Manifest 필드 | ✅ Complete | Do 재진입(v0.8) 사이클에서 반영 |

### 3.2 Non-Functional Requirements

| Item | Target | Achieved | Status |
|------|--------|----------|--------|
| Cross-repo Consistency | xcelium-mcp 위임 매핑표와 100% 일치 | 로컬 위임표 7개 상황 일치 확인 | ✅ |
| Trigger 비충돌 | 기존 5개 agent와 키워드 충돌 없음 | "Do NOT use for"로 명시적 경계 | ✅ |
| Tool 최소 권한 | 불필요한 tool 미부여 | Write/Edit 없음(FR-02) | ✅ |

### 3.3 Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Agent 정의 파일 | `agents/verilog-rtl-debugger.md` | ✅ |
| 배포 산출물 | `~/.claude/agents/verilog-rtl-debugger.md` | ✅ |
| install.py 등록 | `install.py`(glob 기반 자동 등록) | ✅ |

---

## 4. Incomplete Items

### 4.1 Carried Over to Next Cycle

| Item | Reason | Priority | Estimated Effort |
|------|--------|----------|------------------|
| venezia-fpga 실사용 시나리오 수동 검증(Design §5 시나리오 1~4, 3b) | 실제 프로젝트 세션 필요, 이번 사이클 범위 밖 | High | 1 세션 |
| xcelium-mcp 3개 외부 문서와의 위임 매핑표 최종 재대조 | 수동 대조가 유일한 안전장치, cross-repo라 자동화 불가 | Medium | 30분 |

### 4.2 Cancelled/On Hold Items

| Item | Reason | Alternative |
|------|--------|-------------|
| - | - | - |

---

## 5. Quality Metrics

### 5.1 Final Analysis Results

| Metric | Target | Final | Change |
|--------|--------|-------|--------|
| Match Rate (최초 사이클) | 90% | 97% | +7%p |
| Match Rate (FR-10 재진입 후) | 90% | 97% (85%→97%) | +12%p 회복 |
| Structural | - | 100% | - |
| Behavioral | - | 100% | - |

### 5.2 Resolved Issues

| Issue | Resolution | Result |
|-------|------------|--------|
| Staleness 체크 없이 Phase 2 직행(venezia-fpga T-002 실측) | phase-0-discovery.md를 phase-2보다 먼저 MUST Read, staleness 정의 명문화 | ✅ Resolved |
| `tb_provenance` 전달 경로 부재(hash를 낼 수 있는 쪽과 기록해야 하는 쪽이 분리) | Task() 6번째 파라미터로 명시적 전달(null도 명시), tb-analyst FR-14와 페어링 | ✅ Resolved |
| frontmatter/§3이 "0. 기준"의 phase-0-discovery.md 추가를 반영 못함(재검증에서 발견) | 두 곳 모두 5개 파일 세트로 갱신 | ✅ Resolved |
| BLOCKER 규칙 파일 내 중복 서술, cloud0 drift 사례 파일 간 중복 서술 | §3→"0. 기준" 참조로 축약, tb-analyst.md §1 상호 참조로 전환 | ✅ Resolved |

---

## 6. Lessons Learned & Retrospective

### 6.1 What Went Well (Keep)

- **정본 Read·재서술 금지 원칙**이 Phase 2~4 방법론 전체를 agent에 내장하지 않고 런타임 Read하게 해, xcelium-sim skill 개정이 자동 반영되는 구조를 만들었다.
- Cross-repo 계약(§정합성 유지)을 Plan 문서 최상단에 못박아둔 덕에, xcelium-mcp 쪽 버전이 여러 차례 바뀌는 동안에도 "어느 버전을 기준으로 확인했는지"를 놓치지 않았다.
- gap-detector로 재검증하는 루틴이 Design 문서 자체의 staleness(§4.1a 등, 4→5개 갱신 누락)까지 잡아냈다 — 구현이 문서보다 앞서는 역전 상태를 방치하지 않을 수 있었다.

### 6.2 What Needs Improvement (Problem)

- FR-10(staleness 체크)이 처음부터 Plan에 없었던 것은, "분석서가 있으면 신뢰 가능하다"는 암묵적 가정을 초기 설계에서 검증하지 않았기 때문이다 — 실사용(venezia-fpga)에서야 실패 모드가 드러났다.
- `tb_provenance`처럼 "한 agent가 계산하고 다른 agent가 기록하는" 값은 설계 초기에 Task() 계약 양쪽을 동시에 검토하지 않으면 반쪽만 반영되기 쉽다(FR-10/FR-14 동시 등록 필요성이 뒤늦게 발견됨).

### 6.3 What to Try Next (Try)

- 자매 agent 쌍(A가 값을 만들고 B가 그 값을 소비하는 구조)을 설계할 때는 Plan 단계에서부터 "누가 계산, 누가 기록"을 명시하는 계약 표를 양쪽 Plan에 동시에 만드는 것을 표준 절차화.
- Design 문서의 숫자 표기(정본 개수 등)가 구현과 함께 갱신되는지 gap-detector 재검증에 상시 포함.

---

## 7. Process Improvement Suggestions

### 7.1 PDCA Process

| Phase | Current | Improvement Suggestion |
|-------|---------|------------------------|
| Plan | cross-repo 요구사항 변경을 수동 대조로만 감지 | xcelium-mcp 쪽 문서 버전을 주기적으로 자동 diff하는 점검 루틴 고려 |
| Do | 재진입 시 어떤 항목만 손대면 되는지 매번 파악 필요 | §6.2 Implementation Order에 "완료/재작업 대상" 구분을 처음부터 표준 포맷으로 넣기(이번 사이클에서 시작함) |
| Check | gap-detector가 구현뿐 아니라 Design 자체의 staleness도 잡아낸 것이 유용 | Design 문서도 정기적으로 gap-detector 대상에 포함 |

### 7.2 Tools/Environment

| Area | Improvement Suggestion | Expected Benefit |
|------|------------------------|------------------|
| install.py | 배포 후 배포본 diff 자동 확인 스텝 추가 | 재배포 누락 방지 |

---

## 8. Next Steps

### 8.1 Immediate

- [ ] venezia-fpga 세션에서 실사용 시나리오(Design §5) 수동 검증
- [ ] xcelium-mcp 3개 외부 문서와 위임 매핑표 최종 재대조

### 8.2 Next PDCA Cycle

| Item | Priority | Expected Start |
|------|----------|----------------|
| venezia-fpga 실사용 검증 세션 | High | TBD |

---

## 9. Changelog

### v0.8 (2026-07-08)

**Added:**
- FR-10: staleness 체크(hash 비교) phase-2 선행 강제
- Task() 6번째 파라미터 `tb_provenance`(nullable)
- Manifest "staleness 체크 결과" 필드

**Changed:**
- "0. 기준" 순서 재정렬(phase-0-discovery.md를 phase-2보다 먼저)

**Fixed:**
- frontmatter/§3의 phase-0-discovery.md 누락 언급 정정
- BLOCKER 규칙·cloud0 drift 사례 중복 서술 정리(/simplify)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-07-08 | Completion report 작성 — 최초 사이클(2026-07-03~06) + FR-10 재진입 사이클(2026-07-07~08) 통합 | HSLEE |
