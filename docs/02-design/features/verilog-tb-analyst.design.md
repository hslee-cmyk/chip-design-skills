# verilog-tb-analyst Design Document

> **Summary**: TB 분석서(`.ai/analysis/tb_{env}_*.analysis.md`) 전담 agent의 내부 구조 설계. "0. 기준" 절에서 5개 정본(xcelium-sim phase-0-discovery.md + 보조 3종 + ssh-mcp skill)을 **전체 파일 무조건 Read**하고(Plan v0.9 FR-10/11/12 — 부분로딩 방침 폐기, v0.10 FR-15 — ssh-mcp 판단 기준 추가), `verilog-rtl-debugger`가 Task()로 위임할 때 쓰는 호출 계약(6개 파라미터 — FR-14 `tb_provenance` 추가), 분석 **대상**(TB 소스)이 로컬이 아니라 원격 호스트에 있을 수 있다는 점을 agent의 **세션 내 tool 가용성 자동 판단**만으로 해결한 스캔 절차를 다룬다.
>
> **Project**: chip-design-skills
> **Version**: 0.7
> **Author**: HSLEE
> **Date**: 2026-07-08
> **Status**: Draft
> **Planning Doc**: [verilog-tb-analyst.plan.md](../01-plan/features/verilog-tb-analyst.plan.md) (v0.10)

> 이 feature는 Next.js/BaaS 웹앱이 아니라 **markdown agent 정의 파일 1개**를 만드는 작업이다. 템플릿의 DB 스키마/UI/Clean Architecture 레이어 섹션은 해당 사항이 없어 "N/A" 처리했고, "API Specification"은 이 agent의 실제 인터페이스인 **Task() 호출 계약**으로 대체했다.

---

## Context Anchor

> Plan 문서에서 그대로 복사.

| Key | Value |
|-----|-------|
| **WHY** | TB 분석서 작성 방법론(§0A/0B/0C)이 전담 agent 없이 방치되어 RTL 쪽과 비대칭 |
| **WHO** | xcelium-mcp를 사용해 RTL 디버깅을 수행하는 모든 프로젝트의 AI 에이전트 (1차 소비자: venezia-fpga) |
| **RISK** | xcelium-mcp 쪽 phase-0-discovery.md가 개정되는데 이 agent가 인지 못 하면 규칙 위반 분석서 생성 위험 — 수동 대조 외 안전장치 없음 |
| **SUCCESS** | §0A/0B 규칙(env prefix, 필수 항목, 4단계 절차)을 빠짐없이 지키는 분석서 생성; `verilog-rtl-analyst`와 동일한 품질 기준 |
| **SCOPE** | agent 정의 파일(`agents/verilog-tb-analyst.md`) 작성 + `install.py` 배포 등록만 |

---

## 1. Overview

### 1.1 Design Goals

- Plan의 FR-01~FR-14를 구체적인 agent 파일 섹션 구조로 번역한다.
- "0. 기준" 절의 4개 정본을 **전체 파일 무조건 Read**한다(Plan v0.9 FR-10/11/12) — v0.4까지의 Option C(핵심 고정+온디맨드 심화, 조건부 분기)는 부분로딩 목록의 drift 위험이 절약분보다 크다는 판단에 따라 Plan 단계에서 폐기되어, 이 문서에서도 더 이상 설계 선택지가 아니다.
- `verilog-rtl-debugger` ↔ `verilog-tb-analyst` 간 Task() 호출 계약을 이 문서에서 확정한다 — 두 Plan 문서 §7.2가 공통으로 "미정"이라 표시했던 항목. v0.5에서는 FR-14(`tb_provenance` staleness hash 전달)를 계약에 추가 반영한다.

### 1.2 Design Principles

- **정본 Read, 재서술 금지** (Plan §1.2, FR-03/10/11/12) — 이 원칙이 아래 모든 섹션 설계의 최우선 제약.
- **HANDS OFF** — `.ai/analysis/tb_*.analysis.md` 외 어떤 파일도 Write/Edit하지 않는다(FR-07).
- **`verilog-rtl-analyst.md` 구조 벤치마크** — frontmatter, "0. 기준", HANDS OFF, Manifest 섹션 순서를 그대로 재사용해 두 "-analyst" agent 간 일관성을 유지한다.

---

## 2. Architecture Options

### 2.0 Architecture Comparison

> **v0.4→v0.5 변경 배경**: v0.1~v0.4에서 Checkpoint 3으로 선택했던 "0. 기준" 로드 전략 Option C(핵심 고정+온디맨드 심화, 조건부 분기)는 Plan v0.9(2026-07-08)에서 명시적으로 폐기되었다 — 부분로딩 목록이 skill 개정을 자동으로 못 따라가는 drift 위험이, 그 목록이 절약하는 컨텍스트보다 크다고 판단(FR-10/11/12). 이제 4개 정본은 무조건 전체 Read이며, 이는 Plan이 이미 확정한 단일 경로이므로 **더 이상 이 문서의 설계 선택지가 아니다** — §2.1에 그대로 반영한다.
>
> 이번 개정에서 실제 설계 자유도가 남아있는 지점은 Plan v0.8의 FR-14(`tb_provenance` staleness hash, Task() 6번째 파라미터)를 §4 Task() 계약에 **얼마나 상세히 문서화하는가**다. 아래 비교는 이 축을 다룬다.

| Criteria | Option A: Minimal Patch | Option B: Full Redesign | Option C: Pragmatic |
|---|:-:|:-:|:-:|
| **접근** | §4.1 파라미터 표에 행만 추가 | §4.1 행 추가 + 신규 §4.1b(Provenance JSON 스키마 상세 정의) 신설 | §4.1 행 추가 + 기존 §4.2/§4.3 구조를 확장해 필요한 규칙만 편입 |
| §4.1b 신설 여부 | 없음 | 있음 | 없음 |
| §4.2 Manifest | 미반영 | `provenance_recorded` + `hash` 필드 | `provenance_recorded`(bool) 1개만 |
| §4.3 에러 처리 | 미반영 | 상세 케이스 분기 | "미기록" 명시 규칙 1행 |
| §5 Test Plan | 미반영 | 신규 시나리오 2개 | 기존 시나리오 1/2에 provenance 검증 조건 추가 |
| **문서 볼륨** | ~+10줄 | ~+80줄 | ~+35줄 |
| **Risk** | FR-14 핵심 의도("값 없으면 조용히 생략 않고 명시적 '미기록' 남김")가 문서에서 유실 — Do 단계에서 그 규칙이 구현 안 될 위험 | 과설계 — phase-0-discovery.md §0C가 이미 정의한 JSON shape(`{"files":[...],"combined_sha256"}`)를 재서술하는 것과 다르지 않아 "정본 재서술 금지"(§1.2) 원칙과 긴장 | 낮음 |
| **Recommendation** | — | — | **기본 선택** |

**Selected**: **Option C — Pragmatic**
**Rationale**: 이 문서는 처음부터 "정본 Read, 재서술 금지"(§1.2 Design Principles)를 일관되게 지켜왔다. Option B의 §4.1b는 이미 정본(phase-0-discovery.md §0C)이 정의한 스키마를 다시 적는 셈이라 그 원칙에 어긋난다. Option A는 문서 볼륨은 가장 작지만 FR-14가 강조하는 "미기록을 명시적으로 남긴다"(조용히 생략 금지) 규칙이 어디에도 적히지 않아 Do 단계 구현 시 누락될 위험이 크다 — 직전 gap 분석에서 실제로 이 조합(파라미터만 있고 기록 규칙 없음)이 발견된 결함 패턴이었다. Option C는 기존 §4.2/§4.3 표 구조를 그대로 확장해 그 규칙만 명시적으로 담는다.

### 2.1 "0. 기준" 절차 (Component Diagram 대체)

> **v0.5 갱신(Plan v0.9 FR-10/11/12)**: v0.4까지의 quick-grep 조건부 분기(uvm_/hdl_top/hvl_top 매치 유무로 4a/4b 로드 여부 판정)는 폐기됐다. 4개 정본을 **분기 없이 무조건 전체 Read**한다 — grep 오판정(매크로로 축약된 UVM 코드 등, v0.4 §4.3 Risk였던 항목) 자체가 구조적으로 사라진다.

```
0. 기준 — 시작 시 반드시 로드 (분기 없음, 5개 전부 무조건 Read)
┌─────────────────────────────────────────────────────────────┐
│ 1) ~/.claude/skills/xcelium-sim/references/phase-0-discovery.md│
│    §0A/0B/0C 전체                                              │
├─────────────────────────────────────────────────────────────┤
│ 2) ~/.claude/skills/verilog-rtl/SKILL.md 전체                 │
├─────────────────────────────────────────────────────────────┤
│ 3) ~/.claude/skills/chip-verification/SKILL.md 전체            │
├─────────────────────────────────────────────────────────────┤
│ 4) ~/.claude/skills/uvm-verification/SKILL.md 전체             │
├─────────────────────────────────────────────────────────────┤
│ 5) ~/.claude/skills/ssh-mcp/SKILL.md 전체 (v0.6 신설, Plan FR-15)│
│    mcp__ssh__file_read/file_grep/file_ls 사용 판단 기준 정본    │
└─────────────────────────────────────────────────────────────┘
```

> **참고(Plan v0.9 반영)**: 4개 스킬 정본은 전부 `~/.claude/skills/**` 경로 — **로컬 파일**이며 원격 호스트와 무관하다(스킬은 항상 로컬에 배포됨). 원격 접근 이슈는 이 "0. 기준" 절이 아니라, 아래 §2.2/§4.1에서 다루는 **분석 대상 TB 소스 파일 접근**에만 해당한다.
>
> **(v0.6 신설, Plan FR-15)** `ssh-mcp` skill은 이 agent가 실제로 사용하는 tool(`mcp__ssh__file_read`/`file_grep`/`file_ls`, §4.1a)의 사용 판단 기준을 담은 정본이라 다른 4개와 동일한 원칙(재서술 금지, 런타임 Read)으로 §0에 편입한다 — 단, 이 skill이 다루는 `ssh_run`/`ssh_bg_run`/`ssh_bg_poll`/`ssh_bg_kill`(장시간 명령 실행·백그라운드 job 관리)은 이 agent가 쓰는 tool 범위 밖이라 실질적으로 참조하는 내용은 파일 읽기 관련 판단 기준에 한정될 수 있다. `mcp__ssh__*`가 이 세션에서 애초에 가용하지 않은(=TB가 로컬인) 프로젝트에서는 §4.1a 판단에 따라 이 항목 자체가 로드 대상이 아니다.

### 2.2 Delegation Flow (Data Flow 대체)

```
[Claude 또는 verilog-rtl-debugger — mcp__xcelium-mcp__* 권한 있음]
       │ sim_discover(sim_dir="") 호출 → sim_dir(대상 경로) 확정 (Plan FR-13)
       ▼
xcelium-sim skill (Phase 0/1A) — 분석서 부재/stale 감지
       │
       ▼
verilog-rtl-debugger  ──Task(env, target_type, target_name,──►  verilog-tb-analyst
       ▲                target_paths, reason, tb_provenance)          │
       │ (agent 미배포 시 fallback,                    │ 세션 내 mcp__ssh__* 가용 여부로 자체 판단:
       │  §1.2 영구 유지 원칙)                          │   있으면 → mcp__ssh__file_ls/file_grep/file_read
       │                                                │   없으면 → 로컬 Glob/Grep/Read      (§4.1a)
       │                                                │ §0A/0B 절차 수행(로컬 Read로 정본 참조)
       └──────────────────────────────────────  .ai/analysis/tb_{env}_*.analysis.md
                                                 (로컬 Write, 신규/갱신 + Manifest 반환)
```

> **(2026-07-06 재수정)** 이 agent는 원격 호스트가 무엇인지(cloud0인지, 다른 이름인지)는 물론, "로컬이냐 원격이냐" 자체도 파라미터로 받지 않는다 — `mcp__ssh__file_read`/`file_grep`/`file_ls` tool 스키마에 애초에 host 인자가 없고(MCP 서버 등록 시점에 고정, `mcp__xcelium-mcp__*`와 동일 구조), 그 tool들이 이 세션에서 사용 가능한지 여부로 스스로 판단하면 그만이기 때문이다. venezia-fpga가 아닌 다른 프로젝트에 배포될 때도 agent 파일 자체는 무수정 — 그 프로젝트의 `.mcp.json`에 ssh-mcp가 등록돼 있는지만 다를 뿐.

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| "0. 기준" §1 (필수, 전체) | `~/.claude/skills/xcelium-sim/references/phase-0-discovery.md` (로컬) | 분석서 구조·갱신규칙 정본 |
| "0. 기준" §2 (필수, 전체 — Plan v0.9 FR-10) | `~/.claude/skills/verilog-rtl/SKILL.md` 전체 (로컬) | SV 문법(§8 covergroup/assertion) + RTL 합성·CDC·FSM 규칙(§1~§7, §11) |
| "0. 기준" §3 (필수, 전체 — Plan v0.9 FR-11) | `~/.claude/skills/chip-verification/SKILL.md` 전체 (로컬) | 듀얼탑 아키텍처 + Reference Model/Scoreboard/AMS 아날로그 모델 교체 등 |
| "0. 기준" §4 (필수, 전체 — Plan v0.9 FR-12) | `~/.claude/skills/uvm-verification/SKILL.md` 전체 (로컬) | UVM 계층 구조 + RAL/coverage subscriber/report catcher 등 |
| "0. 기준" §5 (필수, 전체 — v0.6 신설, Plan FR-15) | `~/.claude/skills/ssh-mcp/SKILL.md` 전체 (로컬) | `mcp__ssh__file_read`/`file_grep`/`file_ls` 사용 판단 기준 정본 |
| Task 호출자 | `verilog-rtl-debugger` (Plan FR-09) | 분석서 부재/stale 시 위임 + `target_paths` 사전 확정(`sim_discover`) + `tb_provenance` 전달(Plan FR-14 상대편, `verilog-rtl-debugger.plan.md` FR-10) |
| **분석 대상 스캔 (Plan FR-13)** | `mcp__ssh__file_ls`/`file_grep`/`file_read`(host 인자 없음, 세션에서 가용 시) 또는 로컬 `Glob`/`Grep`/`Read`(비가용 시) | TB 소스가 로컬이 아니라 원격에 있는 프로젝트(venezia-fpga는 현재 `cloud0`)에서는 로컬 tool로 도달 불가 — agent가 tool 가용성만으로 자동 분기 |

---

## 3. Output Format (Data Model 대체)

이 agent의 "데이터 모델"은 실질적으로 **출력 분석서 파일 포맷**이다 — 정확한 필드/구조는 phase-0-discovery.md §0A/0B가 정본이므로 여기서는 재서술하지 않고, agent가 Write하는 대상 경로 규칙만 명시한다.

| 파일 종류 | 경로 패턴 | 필수 항목 정본 |
|---|---|---|
| 공유 컴포넌트 분석서 | `.ai/analysis/tb_{env}_{component_name}.analysis.md` | phase-0-discovery.md §0A (env prefix 필수: `lgc`/`uvm`/`dsv`/`ams`) |
| 테스트케이스 분석서 | `.ai/analysis/tb_{env}_{test_name}.analysis.md` | phase-0-discovery.md §0B |

> **헤더 provenance 기록 (v0.5 신설, Plan FR-14, Option C)**: 두 분석서 모두 헤더에 `tb_provenance`를 기록한다 — Task() 호출에 값이 있으면 그대로 기록(재계산 안 함), 없으면 **"hash 미기록(caller가 tb_provenance 미전달)"을 명시적으로** 남긴다(조용히 생략 금지). 필드 스키마 자체는 phase-0-discovery.md §0C가 정본이므로 여기서 재정의하지 않는다.
>
> **N/A**: §3.2 Entity Relationships, §3.3 SQL/MongoDB Schema — 이 feature는 관계형/문서 DB를 다루지 않음.

---

## 4. Task() 호출 계약 (API Specification 대체)

Plan 양쪽 문서(§7.2)가 공통으로 "미정"이라 남겨둔 인터페이스를 여기서 확정한다.

### 4.1 호출 시그니처

`verilog-rtl-debugger`(또는 fallback 시 Claude)가 이 agent를 호출할 때 전달하는 파라미터:

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|:---:|---|
| `env` | `"lgc" \| "uvm" \| "dsv" \| "ams"` | Yes | 대상 검증 환경 — 분석서 파일명 prefix에 그대로 사용 |
| `target_type` | `"component" \| "test"` | Yes | §0A(공유 컴포넌트) vs §0B(테스트케이스) 중 어느 절차를 따를지 |
| `target_name` | `string` | Yes | component_name 또는 test_name — 출력 파일명에 사용 |
| `target_paths` | `string[]` | Yes | 스캔 대상 순수 절대경로(들) — §0A "include/import 대상 식별" 또는 §0B "테스트 파일 스캔"의 시작점. 로컬이든 원격이든 이 필드 하나만 사용(§4.1a) |
| `reason` | `"missing" \| "stale"` | Yes | 신규 작성인지 갱신인지 — §0C 캐시 관리 규칙(갱신 시점=파일 수정 시만) 판단에 사용 |
| `tb_provenance` | `{"files":[{"path","sha256"}],"combined_sha256"} \| null` | No (nullable) | **(v0.5 신설, Plan FR-14)** staleness hash — 호출자(`verilog-rtl-debugger`)가 `sim_batch_run`/`sim_regression`/`sim_bridge_run` 반환값에서 이미 계산해 전달. 이 agent는 재계산하지 않고 §3 분석서 헤더에 그대로 기록(§4.3 참조) |

> **(2026-07-06 — 5개 파라미터로 확정, 2026-07-08 — 6번째 `tb_provenance` 추가로 v0.5 갱신)** 초안에서 `access_mode`/`ssh_host` 2개 필드를 추가했었으나, `mcp__ssh__file_read`/`file_grep`/`file_ls` tool 스키마를 직접 확인한 결과 **host 인자 자체가 없음**을 확인 — 접속 대상은 MCP 서버 등록 시점(`.mcp.json`, `mcp__xcelium-mcp__*`와 동일한 SSH stdio transport)에 이미 고정되므로, 호출자가 호스트 정보를 이 agent에 전달할 이유도 방법도 없다. 시그니처는 한 차례 v0.1의 5개 파라미터로 되돌아갔고, v0.5에서 hash 전달 경로(`tb_provenance`) 6번째 파라미터가 추가됐다 — 이 값은 host 문제와 무관하게 sim tool 접근권이 있는 쪽만 계산 가능하다는 별개 제약에서 비롯된다.
>
> **호출 전제(Plan FR-13)**: 호출자가 `sim_discover(sim_dir="")`(MCP tool)로 `sim_dir`(스캔 시작 경로)만 확정해서 `target_paths`로 넘긴다. 이 agent는 `sim_discover`를 직접 호출하지 않고, 그 경로가 로컬인지 원격인지 신경 쓰지 않는다(§4.1a).

### 4.1a 원격/로컬 스캔 절차 — tool 가용성 기반 자동 분기 (Plan FR-13)

| 이 세션에서 `mcp__ssh__*`가 | 파일 목록 조회 | 패턴 스캔 | 파일 읽기 |
|---|---|---|---|
| **사용 가능** (그 프로젝트에 ssh-mcp 등록됨) | `mcp__ssh__file_ls` | `mcp__ssh__file_grep` | `mcp__ssh__file_read` |
| **사용 불가** (등록 안 됨 = TB가 로컬) | `Glob` | `Grep` | `Read` |

- 호출자가 알려주는 게 아니라 **agent 자신이 frontmatter `tools:` 목록/세션 상태로 즉시 판단** — 파라미터 불필요.
- §0A 대상 식별(`include`/`import` 스캔)은 위 표의 "패턴 스캔" 행으로 수행 — 어느 tool을 쓰든 절차는 동일. (v0.6: §2.1의 조건부 quick-grep 분기는 폐기되어 더 이상 스캔 결과가 로딩 범위를 좌우하지 않는다.)
- **로컬 `Read`/`Glob`/`Grep`의 고정 용도**(위 분기와 무관하게 항상 로컬): (1) §2.1 "0. 기준" 5개 정본 스킬 Read, (2) 기존 `.ai/analysis/tb_*.analysis.md` 출력 파일 확인.
- **호스트/경로 표기**: `target_paths`는 순수 경로 문자열만 담는다. 초안에서 `cloud0:<path>` prefix(v0.2) → `access_mode`+`ssh_host` 별도 필드(v0.3) 순으로 검토했으나, **`mcp__ssh__*` tool에 애초에 host 인자가 없어 이 논의 자체가 불필요**했음이 밝혀져 전부 폐기(Plan §7.2 최종 해소).
- **왜 `Bash`+`ssh <host>`로 하지 않는가**: `mcp__ssh__*` 전용 tool을 쓰면 이 문제 자체가 생기지 않지만, 참고로 원격 로그인 셸이 bash가 아닐 수 있다는 점(venezia-fpga의 cloud0는 tcsh)이 다른 xcelium-mcp 문서(`xcelium-mcp-v4-sim-lifecycle.plan.md`)에 이미 함정으로 기록돼 있다.

### 4.2 반환 (Manifest, Plan FR-08)

| 필드 | 설명 |
|---|---|
| `written` | 작성/갱신한 `tb_*.analysis.md` 경로 목록 (신규/갱신 구분) |
| `loaded_refs` | 이번 실행에서 실제로 Read한 정본 목록 (v0.6부터 §2.1의 5개 전부가 매번 고정 — 조건부 로딩이 없어져 감사 목적이 "로드 여부 확인"에서 "실제 실패 없이 5개 다 로드됐는지 확인"으로 축소. `mcp__ssh__*` 비가용 세션에서는 5번 항목이 애초에 로드 대상이 아님도 함께 기록) |
| `remote_scanned` | `mcp__ssh__*`를 사용했을 때 실제 접근한 경로 목록(§4.1a "사용 가능" 분기 시) — 원격 접근 실패 여부 감사용 |
| `provenance_recorded` | `boolean` **(v0.5 신설, Plan FR-14)** — 이번 실행에서 `tb_provenance`를 헤더에 기록했는지 여부(호출자가 값을 전달했을 때만 `true`; 미전달 시 `false`이며 헤더엔 "미기록" 문구가 남음) |
| `blockers` | 미해결 BLOCKER (예: phase-0-discovery.md 자체를 못 찾음, SSH 접속 실패) |

### 4.3 에러 처리 (Error Handling 대체)

| 상황 | 처리 |
|---|---|
| `~/.claude/skills/xcelium-sim/references/phase-0-discovery.md` 부재 | BLOCKER로 명시적 중단 — 방법론을 임시로 내장하지 않음(Plan §1.2 원칙과 동일하게, "-analyst" 계열도 재서술 fallback 금지) |
| `mcp__ssh__*`가 사용 가능한 세션인데 `target_paths` 접속·조회 실패 | BLOCKER, Manifest `blockers`에 사유 기록(연결 실패 vs 경로 부재 구분) — **로컬 `Glob`/`Grep`으로 조용히 바꿔치기하지 않음**(호출자 의도와 다른 경로를 임의로 스캔할 위험 방지) |
| `tb_provenance`가 Task() 호출에 없음(nullable, caller 미전달) | **(v0.5 신설, Plan FR-14)** 에러 아님 — 정상 경로. 분석서 헤더에 "hash 미기록(caller가 tb_provenance 미전달)"을 명시적으로 기록(조용히 생략 금지), Manifest `provenance_recorded=false` | 

> **N/A**: §7 Security Considerations(XSS/CSRF/암호화 등) — 웹 입력·인증 표면이 없음. 유일한 안전장치는 §3(HANDS OFF: 지정 경로 외 Write 금지)과 위 표의 `mcp__ssh__*` 읽기 전용 사용(Write는 로컬 `.ai/analysis/**`에만, 원격에는 절대 Write 안 함 — HANDS OFF 원칙이 원격에도 동일 적용, 어떤 프로젝트의 어떤 호스트든 무관).

---

## 5. Test Plan (검증 계획)

Plan §4.1 Definition of Done을 실행 가능한 시나리오로 구체화한다. 이 feature는 curl/Playwright 대상이 없는 로컬 markdown agent이므로 템플릿의 L1/L2/L3 자동화 테스트 대신 **수동 시나리오 검증**으로 대체한다.

| # | 시나리오 | 절차 | 성공 기준 |
|---|---|---|---|
| 1 | lgc env 공유 컴포넌트 분석, `tb_provenance` 포함 (원격, ssh-mcp 등록된 세션) | `env=lgc, target_type=component, target_paths=[...], tb_provenance={...}`로 실제 원격 `*.inc` 파일 대상 호출 | §4.1a "사용 가능" 분기로 `mcp__ssh__*` 사용, 출력 파일명에 `tb_lgc_` prefix, §0A 필수 항목 7종 모두 채워짐, "0. 기준" 5개 정본 전부 Read(Manifest `loaded_refs`로 확인, **v0.6**: 조건부 로딩 없음), **분석서 헤더에 전달받은 `tb_provenance` 값이 그대로 기록**되고 Manifest `provenance_recorded=true`(**v0.5**, FR-14) |
| 2 | uvm env 테스트케이스 분석, `tb_provenance` 없음(caller 미전달) (원격) | `env=uvm, target_type=test, target_paths=[...]`로 `tb_provenance` 생략 후 실제 원격 `*_test.sv`(uvm_test 상속) 대상 호출 | §0B 필수 항목 8종 모두 채워짐, **분석서 헤더에 "hash 미기록(caller가 tb_provenance 미전달)"이 명시적으로 남고** Manifest `provenance_recorded=false`(**v0.5**, FR-14 — 조용히 생략 안 됨을 검증) |
| 3 | phase-0-discovery.md 부재 시뮬레이션 | 경로를 일시적으로 다른 이름으로 바꾼 뒤 호출 | BLOCKER로 명시적 중단, 임시 방법론 내장 없이 실패 |
| 4 | HANDS OFF 검증 | 분석 대상 TB 코드(원격)나 RTL 파일 자체 수정 여부 확인 | `.ai/analysis/tb_*.analysis.md` 외 어떤 파일도 변경되지 않음, 원격 호스트에는 어떤 Write도 발생하지 않음 |
| 5 | Task() 위임 검증 | `verilog-rtl-debugger`가 실제로 §4.1 시그니처(**6 파라미터**, 호스트 필드 없음, **v0.5**: `tb_provenance` 포함)로 이 agent를 호출 | 6개 파라미터 전달, Manifest(§4.2, `remote_scanned`+`provenance_recorded` 포함) 정상 수신 |
| 6 | 원격 접속 실패 처리 | `mcp__ssh__*`는 세션에 등록돼 있지만 연결이 안 되는 상태(VPN 미연결 등)에서 호출 | §4.3대로 BLOCKER 명시적 중단, 로컬 `Glob`/`Grep`으로 조용히 바꿔치기하지 않음 |
| 7 | tool 가용성 기반 자동 분기 검증 | `mcp__ssh__*`가 **세션에 아예 등록 안 된**(다른 프로젝트를 흉내낸) 상태로 동일 Task() 호출 | 파라미터 변경 없이 agent가 로컬 `Glob`/`Grep`/`Read`만으로 동일한 §0A/0B 산출물 생성 — 이 agent가 호스트/모드 파라미터 없이도 프로젝트별로 자동 적응함을 검증(§4.1a) |

> venezia-fpga 세션에서의 최종 수동 검증(Plan §4.1 4번째 항목)은 시나리오 1~2를 실제 프로젝트 데이터로 재현하는 것으로 충족한다.
> **v0.5에서 시나리오 삭제**: v0.4의 "grep 미스 edge case"(舊 시나리오 3)는 quick-grep 조건부 로딩 자체가 폐기(§2.1)되어 더 이상 성립하지 않는 시나리오라 제거했다.

---

## 6. Implementation Guide

### 6.1 File Structure

```
agents/
└── verilog-tb-analyst.md   (v0.5부터: 기존 파일 수정 — 07-06 최초 작성분이 이미 배포돼 있음, FR-10/11/12/14 반영한 갱신)

install.py                   (AGENTS 목록 — 이미 등록됨, 확인만)
```

> **N/A**: §9 Clean Architecture, §10 Coding Convention Reference — markdown agent 정의 파일에는 Presentation/Application/Domain/Infrastructure 레이어나 TypeScript import 순서가 적용되지 않는다.

### 6.2 Implementation Order

> **v0.5 갱신 범위**: 아래 1~6은 최초 구현(완료됨) 기준 순서를 그대로 유지하되, **v0.5에서 실제로 손대야 할 항목은 2번(조건부 로딩 제거)과 3번(6번째 파라미터+헤더 기록 규칙 추가)뿐**이다. 1/4/6은 변경 없음 — Do 재진입 시 건드리지 않는다.

1. [x] Frontmatter 작성 (`name`/`description`(Use it when/Do NOT use for/Triggers)/`tools`/`model`) — FR-01, `verilog-rtl-analyst.md` 벤치마크. **`tools:`에 `mcp__ssh__file_read`/`file_grep`/`file_ls` 포함 필수**(FR-02, Plan v0.5) — 완료(2026-07-06), v0.5에서 변경 없음
2. [ ] **"0. 기준" 절 수정** — §2.1(v0.6)대로 조건부 quick-grep 분기(구 4a/4b)를 제거하고 5개 정본 전체를 무조건 Read로 교체(ssh-mcp skill 포함) — FR-10/11/12/15 (**Do 재진입 대상**)
3. [ ] **Task() 입력·출력 처리 절 수정** — §4.1의 6번째 파라미터 `tb_provenance` 수신 로직 추가 + §3 헤더 기록 규칙(있으면 그대로 기록/없으면 "미기록" 명시) + §4.2 Manifest `provenance_recorded` 필드 추가 — FR-14 (**Do 재진입 대상, `verilog-rtl-debugger.plan.md` FR-10과 동시 반영 필수**)
4. [x] HANDS OFF 하드 제약 절 작성 — `.ai/analysis/**` 외 로컬 Write 금지 + 원격 호스트에도 어떤 Write도 하지 않음(읽기 전용, `mcp__ssh__*`엔 write용 tool 자체를 부여하지 않음) — FR-07, 완료·변경 없음
5. [ ] §0A/0B/0C 위임 절 — 재서술 없이 phase-0-discovery.md 참조로 위임(기존 유지), **원격/로컬 스캔 절차(§4.1a)** 문구는 변경 없음 — FR-04/05/06/13
6. [x] `install.py` AGENTS 목록 등록 — FR-09, 완료·변경 없음
7. [ ] §5 Test Plan 시나리오 1~2(provenance 포함/미포함), 5(6-파라미터 Task 검증)로 자체 점검 후 `install.py --only agents` 재배포

### 6.3 Session Guide

파일 1개짜리 agent 정의 작업이라 모듈 분할이 불필요 — 단일 세션 권장.

| Session | Phase | Scope | Turns |
|---------|-------|-------|:-----:|
| Session 1 | Design (v0.1~v0.4) | 전체 | 완료 |
| Session 2 | Do | `agents/verilog-tb-analyst.md` 최초 작성 + install.py 등록 | 완료(2026-07-06) |
| Session 3 | Check | gap 분석 — Match Rate 72%(Plan v0.9 기준), FR-10/11/12/14 미반영 확인 | 완료(2026-07-08) |
| Session 4 (현재) | Design (v0.5) | §2.1 조건부 로딩 폐기 + §4 FR-14 계약 반영 | 완료 |
| Session 5 | Do (재진입) | §6.2 항목 2/3만 수정 — `verilog-rtl-debugger.plan.md` FR-10과 동시 진행 | 15-20 |
| Session 6 | Check + Report | §5 시나리오 1/2/5 재검증 + gap 재분석 | 15-20 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-06 | 초안 — Checkpoint 3에서 Option C(핵심 고정+온디맨드 심화) 채택. Plan §7.2의 미정 항목이었던 Task() 호출 계약(§4)을 이 문서에서 확정. 템플릿의 웹앱 전용 섹션(DB/UI/Clean Architecture)은 N/A 처리 | HSLEE |
| 0.2 | 2026-07-06 | **Plan v0.5(cloud0 원격 접근) 반영** — 분석 대상 TB 소스가 cloud0에 있다는 사실을 반영: §2.2 Delegation Flow에 `sim_discover` 사전 확정 단계 추가, §2.3에 `mcp__ssh__*` 의존성 추가, §4.1에 `target_paths`가 cloud0 원격 경로임을 명시, §4.1a 신설(cloud0 원격 스캔 절차 — 경로 표기 컨벤션 `cloud0:` prefix 확정, 로컬 Glob/Grep/Read를 `mcp__ssh__file_ls`/`file_grep`/`file_read`로 대체, `Bash`+`ssh` 미사용 이유), §4.2 Manifest에 `remote_scanned` 필드 추가, §4.3에 cloud0 접속 실패 처리 추가, §5 Test Plan에 시나리오 7(cloud0 접속 실패) 추가, §6.2 Implementation Order 갱신. "0. 기준"의 4개 스킬 정본은 로컬이라 이 변경과 무관함을 §2.1에 명시해 혼동 방지 | HSLEE |
| 0.3 | 2026-07-06 | **"cloud0" 하드코딩 제거 — 호스트 무관 일반화 (Plan v0.6 반영)**: cloud0는 venezia-fpga만의 SSH 설정값이라는 지적 반영. §4.1의 `target_paths` "cloud0:" 문자열 prefix 방식을 폐기하고, `access_mode`(`"local"`\|`"ssh"`) + `ssh_host`(nullable) 구조화 필드로 대체 — 경로 문자열은 순수 경로만 담음. §4.1a를 access_mode 분기표로 재작성(ssh/local 두 경로 모두 명시), §2.2 다이어그램·§2.3 Dependencies·§4.2 Manifest·§4.3 에러 처리·§5 Test Plan(시나리오 8 `access_mode="local"` 검증 추가)·§6.2 Implementation Order 전반에 걸쳐 "cloud0" 하드코딩 표현을 "원격 호스트(프로젝트별 상이, venezia-fpga는 현재 cloud0)"로 일반화 | HSLEE |
| 0.4 | 2026-07-06 | **`access_mode`/`ssh_host` 파라미터 자체를 폐기 — tool 가용성 기반 자동 분기로 최종 단순화 (Plan v0.7 반영)**: "ssh-mcp/xcelium-mcp는 이미 등록 시점에 host를 설정하는데 agent가 host를 알 파라미터까지 필요한가"라는 지적에 `mcp__ssh__file_read`/`file_grep`/`file_ls` tool 스키마를 직접 로드해 확인 — 세 tool 모두 **host 인자가 없음**(설명: "on this server"), 접속 대상은 MCP 서버 등록 시점에 고정됨을 확인. §4.1 Task() 시그니처를 v0.1의 5개 파라미터(env/target_type/target_name/target_paths/reason)로 되돌리고, §4.1a를 "세션 내 `mcp__ssh__*` 가용 여부로 agent가 스스로 로컬/원격을 판단"하는 표로 재작성. §2.2 다이어그램·§4.2 Manifest·§4.3 에러 처리·§5 Test Plan(시나리오 6/7/8 갱신)·§6.2 Implementation Order에서 `access_mode`/`ssh_host` 언급 전부 제거 | HSLEE |
| 0.7 | 2026-07-08 | **Do 재진입 후 gap-detector 재검증에서 발견된 Design↔구현 drift 정리(문서 hygiene, 구현 변경 없음)**: `agents/verilog-tb-analyst.md`가 실제로는 Match Rate 96%까지 FR-10/11/12/14/15를 전부 반영했는데, 이 Design 문서 자체가 v0.6에서 "4개→5개" 갱신을 §4.1a·§4.2·§5 세 곳에서 누락했고 §4.1a에 이미 폐기된 quick-grep(§2.1 조건부 분기)을 가리키는 dangling 참조가 남아있던 것을 발견 — 구현이 문서보다 앞서 있던 역전 상태. §4.1a "4개 정본" 문구와 quick-grep 잔재 참조 정리, §4.2 Manifest `loaded_refs` "4개"→"5개", §5 시나리오 1 "4개 정본"→"5개" 수정 | HSLEE |
| 0.6 | 2026-07-08 | **FR-15 신설(ssh-mcp skill Read) 반영**: 이 agent가 이미 `mcp__ssh__file_read`/`file_grep`/`file_ls`를 쓰도록 설계돼 있었는데(FR-02), 그 tool 사용 판단 기준을 담은 `ssh-mcp` skill을 "0. 기준"에서 Read하도록 지시한 적이 없던 공백을 발견 — FR-03/10/11/12와 동일한 "정본 Read, 재서술 금지" 원칙을 이 tool 그룹에도 적용. §2.1 "0. 기준" 다이어그램에 5번째 정본으로 추가(이 agent가 쓰지 않는 `ssh_run`/`ssh_bg_*` 관련 내용은 참조 범위 밖일 수 있음을 명시), §2.3 Dependencies·§6.2 Implementation Order·상단 Summary에 반영. `mcp__ssh__*`를 쓰지 않는 `verilog-rtl-debugger`는 대상 아님 | HSLEE |
| 0.5 | 2026-07-08 | **Plan v0.9(FR-10/11/12 전체 skill Read 전환) + v0.8(FR-14 tb_provenance) 반영 — gap-detector 재검증 후 Design 갱신**: 2026-07-08 재검증에서 이 Design(v0.4)이 이미 폐기된 Plan v0.7 시절 Option C(부분로딩)를 그대로 채택 중이고, 07-06 배포된 `agents/verilog-tb-analyst.md`도 이를 따르고 있어 실제 Match Rate가 72%까지 떨어진 것을 확인(agents/verilog-rtl-debugger.md 쪽 FR-10 미반영과 쌍을 이루는 결함). **§2.0 Architecture Comparison 재구성**: 舊 Option A/B/C(로드 정밀도 축)는 Plan v0.9가 이미 확정해 더 이상 설계 선택지가 아니므로 폐기, FR-14 문서화 상세도를 새 비교축으로 Checkpoint 3 재실행 → **Option C(Pragmatic, 기존 §4.2/§4.3 구조 확장)** 채택. **§2.1** quick-grep 조건부 분기(4a/4b) 제거, 4개 정본 무조건 전체 Read로 교체. **§2.2/§2.3** Task() 다이어그램·Dependencies에 `tb_provenance` 반영. **§3** 분석서 헤더 provenance 기록 규칙 신설(재서술 없이 phase-0-discovery.md §0C 참조). **§4.1** 6번째 파라미터 `tb_provenance`(nullable) 추가. **§4.2** Manifest `provenance_recorded` 필드 추가. **§4.3** "미기록 명시" 에러처리 행 추가(舊 grep-미스 시나리오 행 삭제 — 조건부 로딩 폐기로 더 이상 성립 안 함). **§5** 시나리오 1/2에 provenance 검증 조건 편입, 舊 시나리오 3(grep 미스) 삭제, 시나리오 번호 재정렬(5→8→7개). **§6.2** 완료/재작업 항목 구분(1/4/6 완료, 2/3만 Do 재진입 대상), **§6.3** Session Guide에 Session 3(Check, 72% 확인)·Session 4(현재 Design v0.5)·Session 5/6(Do 재진입/재검증) 추가. `verilog-rtl-debugger.plan.md` FR-10과 동시 반영 필수(Do 재진입 시 순서 주의) | HSLEE |
