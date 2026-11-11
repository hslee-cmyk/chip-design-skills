---
name: kb-promote
description: |
  프로젝트 docs/solutions/의 솔루션을 상위 지식 계층으로 격상하는 skill.
  [A] 카테고리 반복 → critical-patterns.md (project Required Reading)
  [B] toolflow/System-level → 영구메모리 ai-memory/memory/ (전 PC·프로젝트 전역)
  capture→curate→격상→recall 루프의 "격상" 단계를 담당.
  트리거: kb-promote, kb-global 격상, ai-memory 격상, 영구메모리 격상, promote to global, 전역 격상, 일반화 격상,
    sync_rules [B], sync_rules [A], toolflow 격상, critical-patterns, principles 추가.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# /kb-promote — 격상 skill ([A] critical-patterns + [B] 영구메모리 ai-memory)

`docs/solutions/`의 솔루션을 두 계층으로 격상한다:
- **[A]** 카테고리 내 반복 패턴 → `docs/solutions/patterns/critical-patterns.md` (코딩 전 강제 회독)
- **[B]** 툴플로우/환경 솔루션 → `ai-memory/memory/<domain>/` (별도 repo, 전 PC·프로젝트 공유)

> **ai-memory 규칙(Phase 7·8, 2026-11-11)** — [B]가 반드시 지킬 것:
> - ID 절(`## P-<KEYWORD> · …`)마다 제목 바로 아래 `<!-- rel: … -->` 한 줄(별칭·관계). 없으면 `kb_index`가 실패하고
>   `eval_gate` FAIL → ai-memory push 차단. 형식·타입·관계 정본 = `$AM/ontology.yaml`, 검증 = `kb_index.py --check`.
> - 관계는 한쪽에만 적는다(역관계는 색인이 만든다). 예: RTL 패턴 → `generalizes=T4`, 증명 템플릿 → `proven_by`는 실패분류 쪽.
>
> 관계: `/solution-capture`(대화 → `docs/solutions`) → **`/kb-promote`(`docs/solutions` → [A]/[B])**.
> `/wrap`(작업 종료)은 교훈이 이미 `docs/solutions`에 있으면 이 skill [B]로, 없으면 `memory_propose`로 넘긴다.

**경로 변수**:
```
KB_PY     = /c/Users/HSLEE/Documents/Todoc/fpga/.tools/kb-venv/Scripts/python.exe
AM        = ${AI_MEMORY_REPO:-~/ai-memory}     # 영구메모리 정본 repo (git)
KB_GLOBAL = $AM/memory/<domain>/               # rtl/ toolflow/ preference/ decision/
EVAL_GATE = $AM/tools/eval_gate.py             # 재색인(온톨로지 검증 포함) + eval + PASS 캐시
ONTOLOGY  = $AM/ontology.yaml                  # 노드 타입·관계·필수 규칙 (Phase 7)
CRIT_PATH = docs/solutions/patterns/critical-patterns.md
```

---

## 격상 절차 (5단계)

### Step 1 — 후보 탐지

```bash
KB_PY=/c/Users/HSLEE/Documents/Todoc/fpga/.tools/kb-venv/Scripts/python.exe
"$KB_PY" docs/solutions/sync_rules.py --dry-run
```

출력에서 [A], [B] 섹션을 확인한다:
- `[A] 없음` + `[B] 없음` → 이미 완료. 종료.
- [A] 또는 [B] 목록 있음 → Step 2로.

---

### Step 2 — 내용 미리보기 + 승인 게이트 (BLOCKING)

각 후보를 사용자에게 보여주고 승인을 받는다. **승인 없이 Step 3 진입 금지.**

#### [B] 후보 처리 (건별)

**먼저 중복 확인** — 같은 원칙이 ai-memory에 이미 있으면 새 절 대신 그 절에 합친다(같은 정의 = 노드 하나):
```bash
"$KB_PY" "$AM/tools/kb_search.py" "<증상·원인 한 줄>" --node-type Pattern -k 3   # 결과의 nodes·neighbors 확인
```

각 [B] 후보 솔루션 파일을 읽어 아래 형식으로 제시:

```
━━━ [B] 후보 N/M ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<solution-id>  (← <파일 경로>)

증상: <fm의 symptom 또는 H2 Symptoms 내용 1-2줄>
원인: <root_cause 또는 Root cause 내용 1줄>
해결: <solution 핵심 1줄>

→ 제안 원칙명: P-<KEYWORD> (<대상 ai-memory memory/ 파일>에 추가 | 기존 P-<X>에 병합)
→ 관계(rel): <예: generalizes=T6; alias=…>   (기존 노드와 이어지는 것이 없으면 alias만)

[1] 격상  [2] 건너뜀  [3] 원문 보기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### [A] 후보 처리 (카테고리별)

sync_rules.py [A]가 보고한 파일들은 **미기여·미격상(fresh) 솔루션만**:
- `contributed_from`에 없는 것 (critical-patterns.md에 아직 기여 안 됨)
- `kb_promoted_ids`에 없는 것 (영구메모리 [B]로 이미 격상 안 됨)

이 파일들을 읽어 **공통 패턴 초안**을 합성한 뒤 제시:

```
━━━ [A] 후보: [<category>] ━━━━━━━━━━━━━━━━━━━━━━
솔루션 N개: <file1>, <file2>, ...

합성 초안:
────────────────────────────────────
## P-<KEYWORD> · <짧은 제목>

**증상 공통점**: <여러 솔루션에서 반복되는 증상>
**근본 원인 패턴**: <공통 원인>

```verilog / python / bash
// BAD
<공통 잘못된 패턴>

// GOOD
<올바른 패턴>
```

**체크포인트**: <코딩 전 확인해야 할 사항>
────────────────────────────────────

critical-patterns.md에 추가할까요?
[1] 추가  [2] 건너뜀  [3] 초안 수정 후 추가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**합성 규칙**:
- 프로젝트 고유 모듈명·신호명 제거 → 일반 패턴으로 추상화
- 여러 솔루션의 공통 원인·증상만 추출 (개별 instance 제외)
- BAD→GOOD 코드쌍은 최대한 짧고 명확하게
- 불확실하면 "수정 후 추가"를 기본으로 제안

---

### Step 3 — 승인된 항목 작성

#### [B] 승인된 항목

**기존 파일에 추가** (같은 domain이면):
```
$AM/memory/toolflow/toolflow-patterns.md  ← toolflow 계열
$AM/memory/rtl/rtl-patterns.md            ← RTL 계열
```

**신규 파일 생성** (새 domain이면):
```markdown
---
kind: pattern
domain: <domain>
scope: global
tags: [<관련 태그>]
promoted_from: []
---

# <도메인명> 일반 패턴 (전 프로젝트 적용) — 장기 지식

> 특정 프로젝트의 버그 instance가 아니라, 일반화되는 원칙.
```

원칙 작성 규칙:
- 섹션 헤딩: `## P-<KEYWORD> · <짧은 제목>` (`P-` 뒤는 대문자·숫자·하이픈 — ontology.yaml Pattern ID 형식)
- **헤딩 바로 아래 rel 주석 한 줄(필수)**:
  ```markdown
  ## P-FIFOEMPTY · FIFO empty 플래그를 pop과 같은 사이클에 갱신
  <!-- rel: generalizes=T4,T6; alias=fifo empty,동시 pop,empty flag -->
  ```
  - `alias=` 검색 단서 3~6개(한/영). 키워드 검색과 질의 속 별칭 주입에 쓰인다.
  - RTL 원칙이면 해당 실패분류로 `generalizes=T#`. 툴플로우는 보통 alias만(관계가 없으면 경고만 나고 통과).
  - 허용 관계·대상 타입은 `ontology.yaml relations` — 모르는 관계·없는 노드를 적으면 색인 실패.
- **증상** / **근본 원인** / BAD→GOOD 코드쌍 / **원칙** 구조
- 작성 직후 검증: `"$KB_PY" "$AM/tools/kb_index.py" --check` → 마지막 줄 `OK`

#### [A] 승인된 항목

`docs/solutions/patterns/critical-patterns.md`에 추가:

```markdown
## P-<KEYWORD> · <짧은 제목>
> ⚠️ 코딩 전 확인 필수

**반복 패턴**: <카테고리>에서 <N>회 발생

**체크포인트**:
- <확인 사항 1>
- <확인 사항 2>

```<언어>
// ❌ BAD
<잘못된 패턴>

// ✅ GOOD
<올바른 패턴>
```
```

---

### Step 4 — 메타데이터 등록

#### [B] promoted_from 등록

격상한 ai-memory 파일의 `promoted_from:` 목록에 솔루션 ID 추가. `$AM/INDEX.md`의 그 파일 행도 갱신한다
(1줄 요약·트리거에 새 ID, **노드 열** = `Pattern N개`처럼 타입별 개수/ID. 신규 파일이면 4열짜리 행을 새로 추가):

```yaml
promoted_from:
  - <solution-id>   # 신규 추가
  - <기존 id>       # 기존 유지
```

> 이 목록이 있어야 `sync_rules.py [B]`에서 "이미 격상됨"으로 인식한다.

#### [A] contributed_from 등록

`docs/solutions/patterns/critical-patterns.md` 프론트매터의 `contributed_from:` 목록에
패턴 합성에 사용한 솔루션 ID를 추가:

```yaml
---
contributed_from:
  - <solution-id-20260624>   # 신규 추가
  - <기존-solution-id-...>   # 기존 유지
---
```

> 이 목록이 있어야 `sync_rules.py [A]`에서 "이미 기여됨"으로 인식한다.
> 등록하지 않으면 다음 실행 때 동일 솔루션이 다시 [A] 후보로 나타난다.

---

### Step 5 — bkit 감사 로그 기록

승인·작성 완료 직후, 커밋 **전에** 격상 이벤트를 bkit audit/decisions에 남긴다.

```bash
KB_PY=/c/Users/HSLEE/Documents/Todoc/fpga/.tools/kb-venv/Scripts/python.exe

# [A] critical-patterns 격상 시
"$KB_PY" docs/solutions/sync_rules.py --record-promo \
  --type A \
  --category <카테고리명> \
  --ids "<id1>,<id2>,..." \
  --target "docs/solutions/patterns/critical-patterns.md" \
  --reason recurrence

# [B] 영구메모리(ai-memory) 격상 시
"$KB_PY" docs/solutions/sync_rules.py --record-promo \
  --type B \
  --ids "<solution-id>" \
  --target "ai-memory/memory/<domain>/<파일명>.md" \
  --reason toolflow
```

→ `.bkit/audit/YYYY-MM-DD.jsonl` + `.bkit/decisions/YYYY-MM-DD.jsonl` 두 파일에 기록된다.  
`[record-promo] audit 기록` + `decision 기록` 두 줄이 출력되면 완료.

---

### Step 6 — 커밋 + push + 검증

#### [B] 영구메모리(ai-memory) 변경 시 (eval_gate 필요)

```bash
# ⓪ 골드셋 보강 — 새 원칙마다 질의 1개(실제 증상 문장). 지식이 늘어도 검색 품질을 잴 수 있게 한다
#    $AM/eval/queries.json  ← {"query": "<증상 문장>", "relevant": ["P-<KEYWORD>"], "nodes": ["P-<KEYWORD>"]}
# ① eval (memory/ 변경 → 캐시 무효화 → 반드시 실행. 재색인·온톨로지 검증 포함, ~7분)
KB_PY=/c/Users/HSLEE/Documents/Todoc/fpga/.tools/kb-venv/Scripts/python.exe
AM="${AI_MEMORY_REPO:-$HOME/ai-memory}"
"$KB_PY" "$AM/tools/eval_gate.py"
# → [eval-gate] PASS 확인 후 commit/push (FAIL이면 골드셋·원칙 점검)
```

```bash
# ② ai-memory commit + push (메시지는 scratchpad 임시 파일 → -F)
git -C "$AM" add memory/<domain>/<수정된 파일> INDEX.md eval/queries.json
git -C "$AM" commit -F "$TMPF"
GIT_SSH_COMMAND="/c/Windows/System32/OpenSSH/ssh.exe" git -C "$AM" push
```

#### [A] critical-patterns.md 변경 시 (eval_gate 불필요)

```bash
# 프로젝트 내 파일이므로 eval 없이 바로 커밋
git add docs/solutions/patterns/critical-patterns.md
TMPF=$(mktemp /c/Users/HSLEE/AppData/Local/Temp/claude/msg_XXXXXX.txt)
echo "docs: add recurring pattern to critical-patterns.md" > "$TMPF"
git commit -F "$TMPF"
```

#### 최종 검증

```bash
"$KB_PY" docs/solutions/sync_rules.py --dry-run
# → [A] 없음, [B] 없음 이어야 완료
```

---

## 알려진 제약

**pre-push hook (cache-only 모드, ai-memory repo)**: `memory/`·`eval/`·`sources.yaml`·`ontology.yaml`·`tools/kb_*` 변경 push 시
`eval_gate.py --gate` — 캐시 HIT이면 즉시 통과, MISS면 즉시 BLOCK. (failure-taxonomy도 이제 `ai-memory/memory/rtl/`이 정본.)
Step 6 ① eval_gate.py 실행(~7분)으로 캐시 구성 → 재push. 캐시 TTL: 8시간. 캐시 키 = 코퍼스 + ontology + 골드셋 + 검색 코드.

**온톨로지 검증 실패**: `[graph ERROR] … rel 주석 없음` / `없는 노드` / `관계의 도착 타입` → Step 3 rel 주석을 고친다.
`[graph warn] 관계 없음`은 경고일 뿐 통과다(툴플로우 패턴에 흔함).

**bkit heredoc 가드**: `git commit -m "$(cat <<'EOF'...)"` 차단.
우회: scratchpad 임시 파일에 메시지 쓰고 `git commit -F <path>` 사용.

**git push SSH**: `GIT_SSH_COMMAND="/c/Windows/System32/OpenSSH/ssh.exe"` 필요.

**[A] 합성 판단**: 카테고리 파일이 서로 다른 근본 원인이면 합성 불가 → "[3] 초안 수정 후 추가"로 분리 작성.

---

## 빠른 참조

```bash
KB_PY=/c/Users/HSLEE/Documents/Todoc/fpga/.tools/kb-venv/Scripts/python.exe

# 1. 후보 확인
"$KB_PY" docs/solutions/sync_rules.py --dry-run

# 2. [B] eval (ai-memory memory/ 수정 후, 재색인 포함)
"$KB_PY" ~/ai-memory/tools/eval_gate.py

# 3. [B] 온톨로지 검증만 / 재색인만 (eval 없이)
"$KB_PY" ~/ai-memory/tools/kb_index.py --check
"$KB_PY" ~/ai-memory/tools/kb_index.py

# 4. [B] preflight 검색 테스트
"$KB_PY" .ai/rag/preflight.py "<격상한 패턴 키워드>"

# 5. 격상 완료 확인
"$KB_PY" docs/solutions/sync_rules.py --dry-run   # → [A] 없음, [B] 없음
```
