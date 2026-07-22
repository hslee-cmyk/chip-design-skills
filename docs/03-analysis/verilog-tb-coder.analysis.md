# verilog-tb-coder Analysis Report

> **Analysis Type**: Gap Analysis (Design vs Implementation)
>
> **Project**: chip-design-skills
> **Analyst**: gap-detector agent + HSLEE
> **Date**: 2026-07-22
> **Design Doc**: [verilog-tb-coder.design.md](../02-design/features/verilog-tb-coder.design.md)

> 이 feature는 markdown agent 정의 파일 1개다. 템플릿의 웹앱 전용 섹션은 N/A. static-only Match Rate:
> `Structural×0.2 + Functional×0.4 + Contract×0.4`.

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | Fix Sub-cycle 근본원인이 TB일 수 있음이 확인됐는데 TB 전담 구현 agent 부재 + 일반 TB 코딩 수요 |
| **WHO** | xcelium-mcp workflow-v2 및 사람의 직접 TB 코딩 요청 |
| **RISK** | spec 정당화가 허술하면 진짜 RTL 버그를 TB로 숨기는 결과(anti-tautology 위반) |
| **SUCCESS** | 스코프 내 수정 + self-check(1차 필터) + verilog-tb-reviewer 항상 인계 |
| **SCOPE** | `agents/verilog-tb-coder.md` 신설만 |

---

## Strategic Alignment Check

### Plan Success Criteria Status

| # | Criteria | Status | Evidence |
|---|---|:---:|---|
| SC-1 | 스코프 내 변경만, 근거 불충분 시 STOP-and-Ask | ✅ Met | §3/§4(agent L96-116) |
| SC-2 | anti-tautology — self-check은 1차 필터일 뿐, `verilog-tb-reviewer` 항상 인계 | ✅ Met | §0/§3/§5 4곳에서 반복 강조(agent L38-41, L93, L104, L130) — 호출 맥락 무관 무조건 |
| SC-3 | 구조적 변경은 `verilog-tb-architect-advisor`로 route(사람 직접 아님) | ✅ Met | §4(c)(agent L114), 양방향 참조 확인(advisor L12/L16-17) |
| SC-4 | "Fix 모드/General 모드" 이원화 부재 | ✅ Met | §2/§8에서 명시적으로 부재를 서술(agent L65-66, L163-164) |

**Success Rate**: 4/4 met

### Decision Record Verification

| Source | Decision | Followed? | Deviation |
|--------|----------|:---:|---|
| [Plan 0.4] | formal 파라미터 스키마 없음, 자유 형식 프롬프트 | ✅ | 없음 |
| [Design] | Option C — spec 위치 3단계 + STOP-and-Ask 구체 예시 5개 + 프롬프트 예시 2개 | ✅ | 없음, Design §4.1 예시와 agent §2 예시 문자 그대로 일치 |

---

## 1. Gap Analysis (Design vs Implementation)

### 1.1 Structural Match — 98%

Design §7.2 Implementation Order 10개 항목 전부 확인:

| 항목 | 위치 | 상태 |
|---|---|:---:|
| Frontmatter | L1-24 | ✅ |
| §0 권한경계 | L33-44 | ✅ |
| §1 Mandatory Setup(4 skill, 조건부 ssh-mcp) | L48-58 | ✅ |
| §2 Task() 입력(권장구조+예시2) | L62-89 | ✅ |
| §3 spec 위치 확인(3단계) | L96-99 | ✅ |
| §4 STOP-and-Ask 표(5예시, (c)→advisor) | L110-116 | ✅ |
| §5 Definition of Done | L123-130 | ✅ |
| §6 Handoff | L134-141 | ✅ |
| §7 HANDS OFF | L145-150 | ✅ |
| §8 정직한 한계 | L154-164 | ✅ |

### 1.2 Functional Depth — 99%

가장 중요한 확인(anti-tautology 유지 여부): self-check이 "1차 필터일 뿐"이고 `verilog-tb-reviewer`가
항상 최종 판단을 내린다는 서술이 §0/§3(2곳)/§5 총 4곳에서 일관되게 반복됨 — Plan 0.2/0.4가 확정한
"호출 맥락 무관 무조건" 원칙이 약화되지 않음.

- tools/model 정확히 일치(Plan FR-02와 문자 그대로 일치), `model: sonnet`이 파일 내 근거(L42-43)로 자체 정당화됨
- §2 예시 2개가 Design §4.1과 완전히 동일
- "Fix 모드/General 모드" 이원화 흔적 없음(오히려 명시적으로 "없다"고 서술)

### 1.3 Contract/Consistency Match — 100%

- `verilog-tb-architect-advisor` 참조가 실제 존재하는 agent와 정확히 일치, **양방향 참조**(coder→advisor, advisor→coder) 확인됨
- Handoff(§6)이 Plan FR-11 6개 필드 모두 커버
- `install.py --only agents --dry-run` glob 인식 재확인(frontmatter `---` 시작 확인)

### 1.4 Match Rate Summary

```
┌─────────────────────────────────────────────┐
│  Structural Match Rate:   98%                │
│  Functional Match Rate:   99%                │
│  Contract Match Rate:    100%                │
│  ─────────────────────────────────────────── │
│  Overall Match Rate:     99.2%               │
│  = (Structural×0.2)+(Functional×0.4)+(Contract×0.4) │
└─────────────────────────────────────────────┘
```

**Verdict: PASS (≥90%)** — Critical/Important gap 없음.

---

## 2. Minor Findings (조치 불필요, 기록용)

| # | 내용 | 판단 |
|---|---|---|
| 1 | "0. 기준" 라벨을 `verilog-tb-analyst.md`처럼 쓰지 않고 `verilog-rtl-coder.md` 스타일인 "1. Mandatory Setup"으로 명명 | 기능 영향 없음(4개 정본 무조건 전체 Read라는 동작 자체는 동일) — 유지 |
| 2 | Plan FR-12 문구("install.py AGENTS 목록에 등록")가 실제 메커니즘(glob 자동 인식)과 다름 | Design §7.2에서 이미 정정 반영됨 — Plan 문서 자체의 문구는 report/archive 단계에서 정리 권장 |

---

## 3. Next Steps

- [x] Match Rate ≥ 90% 확인 → iterate 불필요, report 단계로 진행 가능
- [ ] (선택) Plan FR-12 문구 정정은 report 단계에서 함께 기록

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-22 | 초안 — gap-detector 실행 결과(99.2%, Critical/Important 없음) 반영 | HSLEE |
