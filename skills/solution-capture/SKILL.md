---
name: solution-capture
description: |
  해결한 비자명 RTL/검증 문제를 대화 내역에서 발췌해 프로젝트 docs/solutions 자산으로 구조화하는 skill.
  compound-engineering의 compound-docs 발췌 로직을 이 프로젝트의 지식 시스템(T1..T9 스키마,
  validate.py, kb-global 격상)에 이식한 것. 지식 시스템 상세: chip-design-skills/docs/05.
  다음 상황에서 사용:
  (1) 버그/이슈를 해결한 직후 — "그게 됐다/고쳤다/해결됨" 등 확인 시 자산화
  (2) 여러 번 시도해야 풀린 비자명 디버깅, 비자명 근본원인을 기록할 때
  (3) 대화에 흩어진 증상·시도·근본원인·해결·예방을 한 자산으로 정리할 때
  단순 오타·자명한 문법오류·즉시 고친 사소한 수정은 자산화하지 않는다.
  트리거: solution-capture, 자산화, 해결 기록, 그게 됐다, 고쳤다, 해결됨, docs/solutions,
    solved, that worked, it's fixed, capture solution, document fix, RTL 버그 기록.
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
---

# solution-capture — RTL 해결 자산화 skill

대화에서 **방금 해결한 비자명 문제**를 발췌해 `<project>/docs/solutions/<T*>/`에 검증된 자산으로 남긴다.
이 시스템의 단기 계층(L2 프로젝트). 일반화되면 전역 `kb-global/principles`로 격상한다.

> 핵심: 이 skill의 가치는 **대화 내역에서 자산화할 내용을 발췌·구조화**하는 것이다.
> 스키마/검증/격상은 우리 것을 쓴다 — plugin compound-docs의 Rails 스키마가 아니다.

**경로 변수**: `KB_PY = <workspace>/.tools/kb-venv/Scripts/python.exe` (공유 venv).
**스키마 정본**: `<project>/docs/solutions/schema.yaml`. **검증**: `validate.py`. **동기**: `sync_rules.py`.

---

## 7-Step 자산화 절차 (순서 고정)

### Step 1 — 자산화 대상인지 판단
- 발동: "그게 됐다 / 고쳤다 / 해결됨 / that worked / it's fixed" 또는 `/solution-capture` 수동 호출.
- **비자명만**: 여러 번 시도·비자명 근본원인·미래 세션/타프로젝트가 득 볼 것.
- **제외**: 단순 오타, 자명한 문법오류, 즉시 고친 사소한 수정 → 자산화하지 않고 종료.

### Step 2 — 대화에서 컨텍스트 발췌 (이 skill의 핵심)
대화 히스토리에서 아래를 추출한다. 빠진 필수 항목이 있으면 **사용자에게 묻고 대기**(추측 금지):
- **module**: 어느 모듈/컴포넌트 (예: `d_i2c/ext_i2cSlave`)
- **symptom**: 관찰된 증상/에러 (정확한 메시지·신호)
- **investigation**: 실패한 시도(무엇이 안 됐고 왜) — 미래의 잘못된 경로 회피용
- **root cause**: 기술적 근본 원인 (무엇이 아니라 **왜**)
- **solution**: 무엇이 고쳤나 (코드/파라미터/제약 변경, 가능하면 BAD→GOOD)
- **prevention**: 재발 방지법
- **verifier**: 어느 게이트가 잡나 — `static | formal | sim | pnr`
- **evidence**: 증거 유형 — `lint_log | sby_cex | waveform | utilization_rpt | timing_rpt | hw_observed`

### Step 3 — 기존 문서 확인 (중복 방지)
```bash
grep -ri "<핵심 증상/신호>" <project>/docs/solutions/
ls <project>/docs/solutions/<예상 T-카테고리>/
```
유사 문서가 있으면: 새로 쓰되 교차참조 / 기존 갱신(같은 근본원인일 때) 중 사용자에게 확인.

### Step 4 — 파일명 생성
`[증상-요약]-[module]-[YYYYMMDD].md` (lowercase, 하이픈, < 80자).
예: `fifo-ptr-offbyone-fwdfifo-20260622.md`

### Step 5 — frontmatter 작성 + 검증 (BLOCKING 게이트)
`docs/solutions/schema.yaml`의 enum에 맞춰 frontmatter 작성:
```yaml
---
module: <경로>           # 또는 "System"
date: <YYYY-MM-DD>
problem_type: <T1..T9 또는 toolflow>   # protocol_spec|port_integration|clock_reset_cdc|
                                       # timing_cycle|fsm_corner|pointer_handshake|
                                       # structure_style|fpga_ram|width_truncation|toolflow
component: <fsm|datapath|fifo|register_map|cdc_sync|clock_gen|io_primitive|memory|
            top_integration|testbench|constraints|toolchain>
root_cause: <schema.yaml의 root_cause enum>
verifier: <static|formal|sim|pnr>
evidence: <lint_log|sby_cex|waveform|utilization_rpt|timing_rpt|hw_observed>
resolution_type: <rtl_fix|param_fix|constraint_fix|sdc_fix|filelist_fix|tool_flag|testbench_fix>
severity: <critical|high|medium|low>
target: <FPGA 디바이스, 선택>
tags: [<lowercase-하이픈>, ...]
related: [<교차참조 경로>, ...]
---
```
**카테고리 = problem_type의 `_`→`-`** (예: `timing_cycle` → `timing-cycle/`).
작성 후 **반드시 검증** — 실패 시 고칠 때까지 Step 6 진입 금지:
```bash
"$KB_PY" <project>/docs/solutions/validate.py <작성한 파일>
```

### Step 6 — 자산 작성
`docs/solutions/<카테고리>/<파일명>` 에 본문 작성 (시드 문서 구조):
```markdown
---
<검증 통과한 frontmatter>
---

# <한 줄 제목>

## Symptoms
- <관찰된 증상>

## Investigation (실패한 시도)
- <안 됐던 시도 → 왜>

## Root cause
<기술적 근본 원인, 가능하면 코드>

## Solution
<무엇이 고쳤나. BAD→GOOD 코드쌍 권장>

## Prevention
<재발 방지·체크 포인트>

## Verifier
<static|formal|sim|pnr> — <어떻게 잡(았/는)지 근거>
```

### Step 7 — 교차참조 · bkit 동기 · 격상 판단
```bash
"$KB_PY" <project>/docs/solutions/sync_rules.py   # regression-rules 동기 + 승격 후보 리포트
```
- 유사 문서 있으면 양쪽에 `related:`/`[링크]` 추가.
- **같은 류 3건+** → `docs/solutions/patterns/common-solutions.md` 에 일반화 패턴 등재.
- **치명/반복** → `docs/solutions/patterns/critical-patterns.md` (코딩 전 강제 회독).

---

## 결정 메뉴 (작성 후 — 사용자 응답 대기)
```
✓ 자산 생성: docs/solutions/<카테고리>/<파일명>
다음:
1. 계속 진행 (기본)
2. bkit regression-rules 동기 (sync_rules.py)
3. 일반 원칙으로 격상 — 전역 kb-global/principles (전 프로젝트 공유)  ← 일반화될 때
4. 관련 문서 링크
5. 자산 보기
```

**옵션 3 (전역 격상)** — 여러 프로젝트에 일반화되는 원칙일 때:
1. `chip-design-skills/kb-global/principles/` 정본(git)에 일반화 형태로 추가
   (특정 instance 금지, frontmatter: `kind`/`domain`/`tags`).
2. commit + push (pre-push eval 게이트 통과 필요).
3. `"$KB_PY" <workspace>/.tools/kb-global/kb_index.py` 재색인 → 전 프로젝트 공유.
⚠️ 런타임 `.tools/kb-global`엔 원칙을 쓰지 말 것 (인덱스 전용·비버전관리).

---

## 하지 말 것
- plugin compound-docs의 Rails 스키마(build_error 등)·카테고리 사용 금지 → **우리 T1..T9** 사용.
- frontmatter 검증(Step 5) 건너뛰기 금지(BLOCKING).
- 개인 선호·휘발 맥락은 자산화 대상 아님 (그건 Claude memory). durable·shareable한 기술 지식만.
- 모호한 서술("뭔가 이상했다") 금지 — 정확한 증상·신호·근본원인.

## 참고
- 지식 시스템 전체: `chip-design-skills/docs/05-knowledge-system-architecture.md`
- 스키마 enum 전체: `<project>/docs/solutions/schema.yaml`
- 영감: compound-engineering `compound-docs` (발췌 로직), 스키마/격상은 본 프로젝트 고유.
