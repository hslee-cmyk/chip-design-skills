# verilog-tb-analyst Completion Report

> **Status**: Complete
>
> **Project**: chip-design-skills
> **Version**: 0.10 (Plan) / 0.7 (Design)
> **Author**: HSLEE
> **Completion Date**: 2026-07-08
> **PDCA Cycle**: #2 (Plan v0.1→v0.7 최초 사이클 + v0.8→v0.10 FR-14/15 재진입 사이클)

> 이 feature는 Next.js/BaaS 웹앱이 아니라 **markdown agent 정의 파일 1개**(`agents/verilog-tb-analyst.md`)를
> 만드는 작업이다. 템플릿의 DB/UI/배포 관련 섹션은 N/A 처리했다.

---

## Executive Summary

### 1.1 Project Overview

| Item | Content |
|------|---------|
| Feature | verilog-tb-analyst |
| Start Date | 2026-07-03 |
| End Date | 2026-07-08 |
| Duration | 6일 (최초 사이클 2026-07-03~07-06 완료 + FR-14/15 재진입 사이클 2026-07-07~07-08) |

### 1.2 Results Summary

```
┌─────────────────────────────────────────────┐
│  Match Rate: 96% (target: 90%)               │
├─────────────────────────────────────────────┤
│  ✅ Complete:     15 / 15 FR (FR-01~FR-15)   │
│  ⏳ In Progress:   0 / 15                    │
│  ❌ Cancelled:     0 / 15                    │
└─────────────────────────────────────────────┘
```

### 1.3 Value Delivered

| Perspective | Content |
|-------------|---------|
| **Problem** | xcelium-mcp 디버깅 워크플로우의 Phase 0A/0B/1A(TB 공유 컴포넌트·테스트케이스 분석서 작성)를 전담하는 agent가 없어, RTL 쪽(`verilog-rtl-analyst`)과 구조적으로 비대칭이었다 — `verilog-rtl-debugger`나 Claude가 매번 즉흥적으로 수행. |
| **Solution** | `verilog-rtl-analyst`와 동일 컨벤션(정본 Read, 재서술 금지, `.ai/analysis/**`만 Write)으로 `verilog-tb-analyst` agent를 신설했다. 방법론은 xcelium-mcp가 관리하는 `phase-0-discovery.md`를 런타임 Read하고, TB 코드 해석에 필요한 verilog-rtl/chip-verification/uvm-verification 3개 skill을 전체 Read, 원격 TB 소스는 ssh-mcp tool로 세션 내 가용성만으로 자동 판단해 접근한다. |
| **Function/UX Effect** | TB 분석서 부재/stale 시 이 agent가 자동으로 §0A/0B 형식에 맞춰 작성 — env prefix 누락·필수 항목 누락 같은 규칙 위반 없이 일관된 품질을 보장한다. v0.10부터는 `verilog-rtl-debugger`가 sim tool로 계산한 staleness hash(`tb_provenance`)를 받아 분석서 헤더에 기록(또는 미기록을 명시)해, 캐시 재사용 여부를 다음 세션이 정확히 판단할 수 있게 됐다. |
| **Core Value** | RTL/TB 양쪽 분석서 작성이 대칭적인 전담 agent 구조를 갖게 되어, xcelium-sim skill과 `verilog-rtl-debugger`가 "탐색·판별"에만 집중할 수 있다. |

---

## 1.4 Success Criteria Final Status

> Plan §4.1/§4.2에서.

| # | Criteria | Status | Evidence |
|---|---------|:------:|----------|
| SC-1 | §0A/0B 규칙(env prefix, 필수 항목, 4단계 절차)을 빠짐없이 지키는 분석서 생성 | ✅ Met | §3, phase-0-discovery.md 참조 위임(재서술 없음) |
| SC-2 | `verilog-rtl-analyst`와 동일 품질 기준 | ✅ Met | "왜 별도 agent인가"/"왜 model: opus"/HANDS OFF/정직한 한계 전부 포함 |
| SC-3 | install.py 배포 등록 + 배포 테스트 | ✅ Met | `install.py --only agents` 3회 재배포, glob 기반 자동 등록 확인 |
| SC-4 | FR-10/11/12: 4개 정본 전체 무조건 Read(부분로딩 폐기) | ✅ Met | §0 "0. 기준", gap-detector 재검증 PASS |
| SC-5 | FR-14: `tb_provenance` 수신·헤더 기록(미기록 명시) | ✅ Met | §2/§3, Manifest `provenance_recorded` |
| SC-6 | FR-15: ssh-mcp skill Read | ✅ Met | §0 항목 5 |
| SC-7 | venezia-fpga 실사용 시나리오 검증 | ⚠️ Partial | 미실행 — 실제 프로젝트 세션 필요, 이번 사이클 범위 밖 |

**Success Rate**: 6/7 criteria met (86%) — 나머지 1건은 실사용 검증으로 다음 세션 이관.

## 1.5 Decision Record Summary

| Source | Decision | Followed? | Outcome |
|--------|----------|:---------:|---------|
| [Plan] | `verilog-rtl-analyst.md` 구조 벤치마크(frontmatter/"0. 기준"/HANDS OFF/Manifest) | ✅ | 자매 agent 컨벤션 일관성 유지 |
| [Plan] | 원격 TB 소스 접근 — host 파라미터 불필요, tool 가용성으로 자동 판단 | ✅ | §1, `mcp__ssh__*` 스키마 직접 확인 후 확정 |
| [Plan v0.9] | 부분로딩(§8만, 조건부 grep) 방침 폐기 → 전체 skill Read | ✅ | drift 위험이 절약 컨텍스트보다 크다고 판단, §0 전면 재작성 |
| [Design v0.5, Option C] | FR-14를 기존 §4.2/§4.3 구조 확장으로 문서화(신규 섹션 신설 안 함) | ✅ | Task() 6번째 파라미터 + Manifest 필드 + 에러처리 1행으로 최소 침습 반영 |
| [Design v0.6] | ssh-mcp skill을 "0. 기준" 5번째 정본으로 편입, 단 tool 가용 시에만 조건부 | ✅ | 유일한 조건부 항목으로 명시, 나머지 4개와 구분 |
| [/simplify] | "0. 기준" 반복 상투구·죽은 quick-grep 참조·Manifest 버전 이력 서술 정리 | ✅ | 동작 변경 없이 문서 간결화 |

---

## 2. Related Documents

| Phase | Document | Status |
|-------|----------|--------|
| Plan | [verilog-tb-analyst.plan.md](../01-plan/features/verilog-tb-analyst.plan.md) (v0.10) | ✅ Finalized |
| Design | [verilog-tb-analyst.design.md](../02-design/features/verilog-tb-analyst.design.md) (v0.7) | ✅ Finalized |
| Check | [verilog-tb-analyst.analysis.md](../03-analysis/verilog-tb-analyst.analysis.md) | ✅ Complete (96%) |
| Report | 현재 문서 | ✅ Complete |

---

## 3. Completed Items

### 3.1 Functional Requirements

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-01 | frontmatter (name/description/tools/model) | ✅ Complete | |
| FR-02 | Tool 목록: Read/Write/Edit/Glob/Grep/Bash + ssh-mcp 3종 | ✅ Complete | |
| FR-03 | phase-0-discovery.md MUST Read, 재서술 금지 | ✅ Complete | |
| FR-04/05/06 | §0A/0B/0C 위임(공유 컴포넌트/테스트케이스/캐시 관리) | ✅ Complete | |
| FR-07 | HANDS OFF — `.ai/analysis/tb_*.analysis.md`만 Write | ✅ Complete | |
| FR-08 | Manifest 형식 | ✅ Complete | |
| FR-09 | install.py 등록 | ✅ Complete | |
| FR-10/11/12 | verilog-rtl/chip-verification/uvm-verification 전체 Read(부분로딩 폐기) | ✅ Complete | Do 재진입 사이클에서 반영 |
| FR-13 | 원격/로컬 자동 판단(host 파라미터 불필요) | ✅ Complete | |
| FR-14 | `tb_provenance` 수신 + 헤더 기록(미기록 명시) | ✅ Complete | Do 재진입 사이클에서 반영, rtl-debugger FR-10과 페어 |
| FR-15 | ssh-mcp skill Read | ✅ Complete | Do 재진입 사이클에서 신설·반영 |

### 3.2 Non-Functional Requirements

| Item | Target | Achieved | Status |
|------|--------|----------|--------|
| Cross-repo Consistency | phase-0-discovery.md §0A/0B/0C와 100% 일치(재서술 아님) | 참조 위임 구조로 재서술 없음 확인 | ✅ |
| 컨벤션 일관성 | `verilog-rtl-analyst.md`와 구조·톤 동일 | 섹션 순서·스타일 일치 | ✅ |
| 보조 스킬 전체 로드 | 절 번호로 범위 제한 안 함 | §0 1~4는 전체, 5는 tool 가용성만 조건 | ✅ |

### 3.3 Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Agent 정의 파일 | `agents/verilog-tb-analyst.md` | ✅ |
| 배포 산출물 | `~/.claude/agents/verilog-tb-analyst.md` | ✅ |
| install.py 등록 | `install.py`(glob 기반 자동 등록) | ✅ |

---

## 4. Incomplete Items

### 4.1 Carried Over to Next Cycle

| Item | Reason | Priority | Estimated Effort |
|------|--------|----------|------------------|
| venezia-fpga 실사용 시나리오 수동 검증(Design §5 시나리오 1/2/3b/6~9) | 실제 프로젝트 세션 필요, 이번 사이클 범위 밖 | High | 1 세션 |
| phase-0-discovery.md 원본과 §0A/0B/0C 전문 재대조 | 이 세션 범위 밖(원칙 준수는 확인, 원문 전수 대조는 별도) | Medium | 30분 |

### 4.2 Cancelled/On Hold Items

| Item | Reason | Alternative |
|------|--------|-------------|
| - | - | - |

---

## 5. Quality Metrics

### 5.1 Final Analysis Results

| Metric | Target | Final | Change |
|--------|--------|-------|--------|
| Match Rate (최초 사이클) | 90% | 95% | +5%p |
| Match Rate (FR-14/15 재진입 후) | 90% | 96% (72%→96%) | +24%p 회복 |
| Structural | - | 100% | - |

### 5.2 Resolved Issues

| Issue | Resolution | Result |
|-------|------------|--------|
| §3이 §0A/0B 필수 항목명을 그대로 나열(재서술 금지 원칙 위반, 최초 사이클에서 발견) | 항목명 나열 제거, 순수 참조 위임으로 교체 | ✅ Resolved |
| 부분로딩(조건부 quick-grep 분기)이 skill 개정을 자동 반영 못함 | 4개 정본 무조건 전체 Read로 전환 | ✅ Resolved |
| `tb_provenance` 수신 경로·헤더 기록 규칙 부재 | Task() 6번째 파라미터 + §3 기록 규칙(있으면 기록/없으면 "미기록" 명시) | ✅ Resolved |
| ssh-mcp tool 사용 판단 기준 정본을 Read하는 지시 누락 | "0. 기준" 5번째 항목으로 편입(조건부: tool 가용 시만) | ✅ Resolved |
| Design v0.6 문서 자체가 "4개→5개" 갱신을 3곳에서 누락(구현이 문서보다 앞서 있던 역전) | Design v0.7로 문서 hygiene 정리 | ✅ Resolved |
| "0. 기준" 반복 상투구, 죽은 "quick-grep" 참조, Manifest 버전 이력 서술 | `/simplify` 패스로 정리 | ✅ Resolved |

---

## 6. Lessons Learned & Retrospective

### 6.1 What Went Well (Keep)

- **재서술 금지 원칙**을 초기부터 명시적으로 세워뒀던 덕에, 최초 사이클 gap-detector가 §3의 원칙 위반(항목명 그대로 나열)을 곧바로 잡아냈다.
- 부분로딩 폐기 결정(FR-10/11/12)이 "컨텍스트 절약 vs 유지보수 비용"이라는 트레이드오프를 명시적으로 재본 결과였다 — 이 판단 기준이 자매 agent(`verilog-rtl-debugger`)의 FR-10에도 그대로 적용되어 두 feature가 일관된 원칙을 공유하게 됐다.
- gap-detector 재검증이 구현뿐 아니라 Design 문서 자체의 staleness(4→5개 누락)까지 잡아냈다.

### 6.2 What Needs Improvement (Problem)

- ssh-mcp skill Read(FR-15)처럼 "이미 쓰고 있는 tool의 사용 판단 기준 skill을 Read하라"는 지시가 애초 설계에서 빠지기 쉽다 — tool 목록에 넣는 것과 그 tool의 사용법 skill을 Read하게 하는 것이 별개 결정이라는 점이 뒤늦게 드러났다.
- Design 문서가 구현보다 뒤처지는 역전 상태(v0.6이 "4개"라고 쓴 채 구현은 이미 "5개")가 발생한 것은, Do 재진입 시 구현만 고치고 Design 갱신을 빠뜨리기 쉽다는 신호.

### 6.3 What to Try Next (Try)

- Do 재진입 체크리스트에 "구현 수정 후 Design 문서의 숫자/카운트 표기도 함께 갱신했는지" 항목을 표준으로 추가.
- tool 목록에 새 tool 그룹을 추가할 때, "그 tool의 사용 판단 기준을 담은 skill이 있는가"를 자동으로 점검하는 체크리스트 항목화.

---

## 7. Process Improvement Suggestions

### 7.1 PDCA Process

| Phase | Current | Improvement Suggestion |
|-------|---------|------------------------|
| Plan | 부분로딩 폐기처럼 근본적 방침 변경이 소급 반영에 여러 사이클 소요 | 방침 변경 시 영향받는 모든 자매 feature를 한 번에 나열하는 체크리스트 |
| Do | 재진입 시 어떤 항목만 손대면 되는지 매번 파악 필요 | §6.2에 "완료/재작업 대상" 구분을 표준 포맷으로(이번 사이클에서 시작함) |
| Check | Design 자체의 staleness도 gap-detector가 잡아낸 것이 유용 | Design 문서도 정기적으로 gap-detector 대상에 포함 |

### 7.2 Tools/Environment

| Area | Improvement Suggestion | Expected Benefit |
|------|------------------------|------------------|
| install.py | 배포 후 배포본 diff 자동 확인 스텝 추가 | 재배포 누락 방지 |

---

## 8. Next Steps

### 8.1 Immediate

- [ ] venezia-fpga 세션에서 실사용 시나리오(Design §5) 수동 검증
- [ ] phase-0-discovery.md 원본과 §0A/0B/0C 전문 재대조

### 8.2 Next PDCA Cycle

| Item | Priority | Expected Start |
|------|----------|----------------|
| venezia-fpga 실사용 검증 세션 | High | TBD |

---

## 9. Changelog

### v0.10 (2026-07-08)

**Added:**
- FR-10/11/12: verilog-rtl/chip-verification/uvm-verification 전체 skill Read(부분로딩 폐기)
- FR-14: `tb_provenance` 수신 + 헤더 기록 규칙
- FR-15: ssh-mcp skill Read

**Changed:**
- "0. 기준" 구조를 조건부 quick-grep 분기에서 무조건 전체 Read(1개 조건부 예외만 유지)로 전환

**Fixed:**
- Design v0.6의 "4개→5개" 갱신 누락 3곳 정리
- "0. 기준" 반복 상투구·죽은 quick-grep 참조·Manifest 버전 이력 서술 정리(/simplify)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-07-08 | Completion report 작성 — 최초 사이클(2026-07-03~06) + FR-14/15 재진입 사이클(2026-07-07~08) 통합 | HSLEE |
