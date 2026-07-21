# verilog-rtl-debugger Gap Analysis

> **Project**: chip-design-skills
> **Date**: 2026-07-06
> **Status**: Complete
> **Plan**: [verilog-rtl-debugger.plan.md](../01-plan/features/verilog-rtl-debugger.plan.md) (v0.7)
> **Design**: [verilog-rtl-debugger.design.md](../02-design/features/verilog-rtl-debugger.design.md) (v0.1)
> **Implementation**: `agents/verilog-rtl-debugger.md`

## Context Anchor

> Design 문서에서 그대로 복사.

| Key | Value |
|-----|-------|
| **WHY** | xcelium-mcp 디버깅 워크플로우 Phase 2~4를 수행할 MCP-tool-aware agent가 없음 |
| **WHO** | xcelium-mcp를 사용해 RTL을 디버깅하는 모든 프로젝트의 AI 에이전트 (1차 소비자: venezia-fpga) |
| **RISK** | xcelium-mcp 쪽 요구사항과 이 repo의 구현이 별도 PDCA 사이클로 진행되어 drift 가능 |
| **SUCCESS** | 위임 매핑표의 7개 상황 전부를 올바른 agent에 위임; Phase 2~4는 다른 agent 호출 없이 직접 수행 |
| **SCOPE** | agent 정의 파일 + install.py 배포 등록만 |

## 전략적 정합성 (Strategic Alignment)

- PRD 없음(이 feature는 cross-repo 계약이라 §정합성 유지가 그 역할을 대신함) — N/A
- Plan의 핵심 문제(MCP-tool-aware 라우터 부재)를 구현이 실제로 해결하는가: **Yes** — frontmatter에 24개 MCP tool + Task 권한, 6개 위임 대상 라우팅 규칙이 모두 존재.
- Design의 핵심 결정(Option C 24개 전량+사용규율, 방법론 비내장, tb-analyst 계약 재사용)이 전부 구현에 반영됨.

## gap-detector 분석 결과 (bkit:gap-detector agent 호출)

### 축별 Match Rate

| 축 | 점수 | 근거 |
|---|---:|---|
| Structural | 97% | 24개 MCP tool 전량(7개 그룹 구성 Design §2.0과 일치), Write/Edit 없음(FR-02), "0. 기준" 4개 phase reference 전부, 7개 위임 라우팅표, Tool 3단 규율, HANDS OFF·Manifest 전부 존재 |
| Functional Depth | 96% | placeholder 없음, Task() 7개 패턴이 Design §2.2와 문구 수준 일치, FR-01~FR-09 1:1 대응 가능 |
| Contract | 98% | tb-analyst 위임 파라미터(env/target_type/target_name/target_paths/reason)가 `verilog-tb-analyst.design.md` §4.1과 이름·순서 문자 그대로 일치, 6개 위임 대상 전부 Task() 패턴으로 존재 |

**Overall Match Rate = (0.3×97) + (0.4×96) + (0.3×98) = 96.9% ≈ 97%**

### Gap 목록

| 심각도 | 내용 | 근거 |
|---|---|---|
| Minor | 24개 MCP tool명이 정본 `tool-map.md`(외부 xcelium-mcp repo)와 자동 대조 불가 — 이번 세션에서 그 문서를 Read해 수기 추출했으나 gap-detector는 재검증 못 함 | Design §2.0 |
| Minor | FR-08(install.py 등록)은 3개 문서(Plan/Design/구현) 범위 밖 — install.py 자체가 이 분석 범위 밖 | Plan FR-08 |

**Critical/Important gap 없음.**

## Plan Success Criteria 최종 판정

### §4.1 Definition of Done
| 항목 | 판정 | 근거 |
|---|:---:|---|
| `verilog-rtl-analyst.md` 등 기존 5개와 동일 품질 기준(model 근거, "왜 별도 agent인가") | ✅ Met | agent 파일 §"왜 별도 agent인가"/"왜 model: opus" 섹션 |
| install.py 배포 등록 + 실제 배포 테스트 | ✅ Met | 이번 세션 `--dry-run` 확인 후 실제 배포, `~/.claude/agents/verilog-rtl-debugger.md` 생성 확인 |
| xcelium-mcp 3개 문서 위임 매핑표와 최종 대조 | ⚠️ Partial | 이 repo 내 위임표(7개 상황)는 일관되나, 외부 xcelium-mcp repo 3개 문서와의 재대조는 이 세션 범위 밖(Plan §정합성 유지 절차 별도 수행 필요) |
| venezia-fpga 세션 실사용 시나리오 검증 | ⚠️ Partial | 미실행 — 실제 프로젝트 데이터 필요, 이 Check 단계 범위 밖 |

### §4.2 Quality Criteria
| 항목 | 판정 |
|---|:---:|
| `failure-taxonomy.md` 중복 적용 경계 명확화 | ✅ Met (taxonomy 직접 적용 없이 reviewer로 라우팅) |
| 다른 4개 agent와 툴/스코프 비충돌 | ✅ Met (고유 MCP tool, "Do NOT use for" 절로 경계 명시) |

## Checkpoint 5 — Review Decision

Critical/Important 이슈 없음(confidence ≥80% 기준 미해당 항목 없음). Minor 2건은 이 Check 단계 범위 밖의 외부 대조/실사용 검증 항목으로, 코드 수정을 요하는 gap이 아님.

**권장**: 그대로 진행(Report 단계로) — 90% 게이트(97%) 통과, Critical/Important 없음.

---

## 2026-07-08 재검증 (Do 재진입 — Plan v0.6→v0.8 FR-10, Design v0.1→v0.2)

이 문서 최초 작성(2026-07-06) 이후, `verilog-tb-analyst`와 함께 자매 Plan에 FR-10(분석서 staleness 체크 —
phase-0-discovery.md MUST 선행 Read, hash 불일치/미기록 시 stale 판정, `tb_provenance` 6번째 Task()
파라미터, Manifest staleness 필드)이 신설되어 Match Rate가 **97%→85%**로 재산정됐다(구현이 최신 Plan을
따라가지 못한 상태). Design v0.2로 반영(Option C 방침 재사용) 후 `agents/verilog-rtl-debugger.md`를
Do 재진입으로 수정, 재배포, gap-detector 재검증.

| 항목 | 재검증 결과 |
|---|---|
| (a) phase-0-discovery.md MUST, phase-2보다 먼저 | ✅ PASS (§0, L63/66-68) |
| (b) staleness 정의(hash 불일치 OR 미기록) §2 공통규칙 | ✅ PASS (§2, L110-114) |
| (c) #2 위임 Task()에 `tb_provenance` 6번째 파라미터, null 명시 전달 | ✅ PASS (§2 #2, L102) |
| (d) Manifest "staleness 체크 결과" 필드 | ✅ PASS (§Manifest, L155-156) |

잔여 Minor 2건(frontmatter description·§3 BLOCKER 목록이 phase-0-discovery.md 누락 언급) 즉시 수정·재배포.
이후 `/simplify` 패스에서 BLOCKER 규칙 중복 서술(§0/§3)과 cloud0 drift 사례 중복 서술(§2, tb-analyst.md와
중복)을 정리 — 동작 변경 없음, 문서 간결화만.

**최종 Match Rate: 97%** (Structural/Behavioral 100%, frontmatter 문구 정합성으로 -3%).

**Cross-dependency**: FR-10은 `verilog-tb-analyst.plan.md` FR-14와 쌍을 이루는 계약 — 두 agent 파일을
동시에 수정하지 않으면 한쪽이 보내는 `tb_provenance` 값을 다른 쪽이 못 받는다. 이번 세션에서 두 파일
모두 동시 반영·재검증 완료(`verilog-tb-analyst.analysis.md` 참조).
