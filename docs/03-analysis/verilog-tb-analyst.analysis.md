# verilog-tb-analyst Gap Analysis

> **Project**: chip-design-skills
> **Date**: 2026-07-06
> **Status**: Complete
> **Plan**: [verilog-tb-analyst.plan.md](../01-plan/features/verilog-tb-analyst.plan.md) (v0.7)
> **Design**: [verilog-tb-analyst.design.md](../02-design/features/verilog-tb-analyst.design.md) (v0.4)
> **Implementation**: `agents/verilog-tb-analyst.md`

## Context Anchor

> Design 문서에서 그대로 복사.

| Key | Value |
|-----|-------|
| **WHY** | TB 분석서 작성 방법론(§0A/0B/0C)이 전담 agent 없이 방치되어 RTL 쪽과 비대칭 |
| **WHO** | xcelium-mcp를 사용해 RTL 디버깅을 수행하는 모든 프로젝트의 AI 에이전트 (1차 소비자: venezia-fpga) |
| **RISK** | xcelium-mcp 쪽 phase-0-discovery.md가 개정되는데 이 agent가 인지 못 하면 규칙 위반 분석서 생성 위험 |
| **SUCCESS** | §0A/0B 규칙을 빠짐없이 지키는 분석서 생성; `verilog-rtl-analyst`와 동일 품질 기준 |
| **SCOPE** | agent 정의 파일 + install.py 배포 등록만 |

## 전략적 정합성 (Strategic Alignment)

- Design의 핵심 결정(Option C 4-정본 로드, host 파라미터 자체 폐기, tool 가용성 기반 자동 분기)이 구현에 정확히 반영됨.
- Plan FR-03("정본 Read, 재서술 금지")이 실제로 지켜지는지가 이 feature의 핵심 원칙인데, **1차 gap-detector 분석에서 이 원칙 위반이 발견**되어 즉시 수정함(아래 참조).

## gap-detector 분석 결과 (bkit:gap-detector agent 호출, 수정 전 기준)

### 축별 Match Rate (수정 전)

| 축 | 점수 | 근거 |
|---|---:|---|
| Structural | 98% | tools 9개 전부, "0. 기준" 4개 정본이 Design §2.1 순서대로, §1 host 파라미터 없음(access_mode/ssh_host 잔존 없음) 확인, §2 Task() 파라미터 정확히 5개, HANDS OFF·Manifest 4필드 전부 존재 |
| Functional | 88% | **§3에서 phase-0-discovery.md §0A/0B 필수 항목을 그대로 나열 — "재서술 금지"(Plan FR-03) 원칙 위반 발견** |
| Contract | 100% | `verilog-rtl-debugger.md` §2 위임표 #2행과 5개 파라미터 이름·순서 완전 일치 |

**Overall (수정 전) = (0.3×98) + (0.4×88) + (0.3×100) = 94.6% ≈ 95%**

### Gap 목록 및 조치

| 심각도 | 내용 | 근거 | 조치 |
|---|---|---|---|
| 🟡 Important | §3(구 L104-109)이 §0A 필수 7종·§0B 필수 8종 항목명을 그대로 나열해 "재서술 금지" 원칙(Plan FR-03, Design §3) 위반 | `agents/verilog-tb-analyst.md` §3 | **즉시 수정** — 항목명 나열 제거, "§0A/§0B 절차·필수 항목대로 Write"로 순수 참조 위임으로 교체. 재배포 완료 |
| 🔵 Minor | "0. 기준" 조건부 심화 번호를 Design은 "4a/4b", agent 파일은 "3a/3b"로 표기 | Design §2.1 vs agent §0. 기준 | **수정 안 함** — agent 파일의 "3a/3b"(step 3의 하위 분기)가 Design의 "4a/4b"(step 3과 별개 단계처럼 보임)보다 구조적으로 더 정확한 표기. 기능 영향 없고, 오히려 agent 쪽이 맞음 — Design 쪽 표기가 사소하게 부정확했던 것으로 판단, 재론 불필요 |

**Critical gap 없음. Important 1건 즉시 수정 완료, Minor 1건은 실질적으로 문제 아님으로 판단.**

## Plan Success Criteria 최종 판정

### §4.1 Definition of Done
| 항목 | 판정 | 근거 |
|---|:---:|---|
| `verilog-rtl-analyst.md`와 동일 품질 기준 | ✅ Met | 왜 별도 agent/왜 opus/HANDS OFF/정직한 한계 전부 포함 |
| install.py 배포 등록 + 배포 테스트 | ✅ Met | 이번 세션 dry-run + 실배포(§3 수정 후 재배포까지) 확인 |
| phase-0-discovery.md §0A/0B/0C와 최종 대조 | ⚠️ Partial | §3 재서술 gap을 수정하며 원칙은 재확인했으나, 정본 문서 자체와의 전문 대조는 이 세션 범위 밖 |
| venezia-fpga 실사용 시나리오 검증 | ⚠️ Partial | 미실행 — 이 Check 단계 범위 밖 |

### §4.2 Quality Criteria
| 항목 | 판정 |
|---|:---:|
| `verilog-rtl-analyst`와 트리거 중복 최소화 | ✅ Met ("Do NOT use for"로 RTL/TB 명확 구분) |
| `verilog-rtl-debugger`와의 위임 인터페이스 자연스러움 | ✅ Met (Contract 100% 일치 확인) |

## Checkpoint 5 — Review Decision

Important gap 1건은 발견 즉시 수정·재배포 완료(agent 파일이 스스로 위반했던 원칙을 스스로 정정). Critical 없음, 남은 Minor 1건은 실질적 결함이 아님. 재계산하면 Functional Depth가 사실상 100%에 가까워지므로 Overall은 95%보다 높다고 판단.

**권장**: 그대로 진행(Report 단계로) — 90% 게이트 통과(수정 전에도 95%), 수정 후 더 개선.

---

## 2026-07-08 재검증 (Do 재진입 — Plan v0.7→v0.10, Design v0.4→v0.7)

이 문서 최초 작성(2026-07-06) 이후 Plan에 3차례 개정이 있었다: FR-10/11/12(부분로딩 폐기 → 4개 정본
전체 무조건 Read), FR-14(`tb_provenance` staleness hash 수신·헤더 기록), FR-15(ssh-mcp skill Read).
구현이 이를 반영하지 못해 Match Rate가 **95%→72%**로 재산정됐다. Design v0.5(FR-14)→v0.6(FR-15)→v0.7
(문서 자체의 4→5개 drift 수정)로 순차 반영 후, `agents/verilog-tb-analyst.md`를 Do 재진입으로 수정,
재배포, gap-detector 재검증.

| 항목 | 재검증 결과 |
|---|---|
| §0 5개 정본(phase-0-discovery/verilog-rtl/chip-verification/uvm-verification/ssh-mcp) 무조건 전체 Read, 조건부 quick-grep 분기 제거 | ✅ PASS (§0, L51-74) |
| Task() 6개 파라미터(`tb_provenance` 포함) + 헤더 기록 규칙(있으면 기록/없으면 "미기록" 명시) | ✅ PASS (§2 L103-113, §3 L128-131) |
| Manifest `provenance_recorded` 필드 + 5-skill 로딩 반영 | ✅ PASS (§Manifest L158-165) |

Design v0.6 문서 자체가 "4개→5개" 갱신을 3곳(§4.1a/§4.2/§5)에서 누락하고 폐기된 quick-grep을 가리키는
dangling 참조가 남아있던 것을 재검증 중 발견(구현이 Design보다 앞서 있던 역전 상태) — Design v0.7로 정리.
`/simplify` 패스에서 "0. 기준" 항목 2~4의 반복 상투구 제거, 죽은 "quick-grep" 용어 참조(§4, 실제로는
"패턴 스캔") 수정, Manifest 설명의 버전 이력 서술 제거, "분기 없이 전부 무조건"이라는 문구가 실제로는
5번(ssh-mcp)만 조건부인 것과 불일치했던 3곳을 정리 — 동작 변경 없음.

**최종 Match Rate: 96%** (Structural 100%, Functional/Contract/Behavioral 95% 내외 — caller측
`verilog-rtl-debugger.md`와의 실제 연동은 별도 검증 항목).

**Cross-dependency**: FR-14는 `verilog-rtl-debugger.plan.md` FR-10과 쌍을 이루는 계약 — 두 agent 파일
모두 이번 세션에서 동시 반영·재검증 완료(`verilog-rtl-debugger.analysis.md` 참조).
