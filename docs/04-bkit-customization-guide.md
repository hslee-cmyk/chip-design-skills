# bkit Customization 가이드 — Agents · Hooks · Templates

bkit(Vibecoding Kit, PDCA/sprint 플러그인)의 **동작을 customize**하는 검증된 방법을 정리한다.
출처: bkit `CUSTOMIZATION-GUIDE.md` + **플러그인 실제 코드 대조**(`~/.claude/plugins/cache/bkit-marketplace/bkit/<ver>/`).
이 repo(`chip-design-skills`)가 그 customization의 **단일 소스**이고 `install.py`가 배포한다.

> 핵심 결론 한 줄: **Hooks는 공통화가 잘 되고(union), Skills는 project 우선으로 override되며,
> Agents는 추가는 되나 bkit 오케스트레이터에 자동 위임 안 되고, Templates는 config override가 불가하다.**

---

## 1. 우선순위 (Precedence)

bkit `CUSTOMIZATION-GUIDE.md` 원문 (line 668–672):

```
1. Managed Settings    (최고, 기업/IT 통제)
2. Command Line Args
3. Project Local       .claude/settings.local.json   (개인, gitignore)
4. Project Shared      .claude/settings.json          (팀 공유)
5. User Global         ~/.claude/settings.json        (최하위)
```

> "Project-level configurations override global configurations with the same name."

→ **project `.claude/` 가 최우선, 그 다음이 user global `~/.claude/`.**
하지만 "user global이 bkit을 customize하느냐"는 **컴포넌트마다 다르다** (§2).

---

## 2. 컴포넌트별 override 동작 (검증)

| 컴포넌트 | user global 적용? | 메커니즘 / 근거 |
|---|---|---|
| **Hooks** | ✅ **잘 됨 (가산 union)** | Claude Code가 plugin + user + project hook을 **전부 발동**. 서로 shadow 안 함. bkit hook은 plugin `hooks/hooks.json`의 command hook(`${CLAUDE_PLUGIN_ROOT}` 사용) |
| **Skills** | ✅ 됨 (project 우선) | bkit `lib/skill-loader.js:4` — "Loads skills from two layers with project-local taking precedence" |
| **Agents** | ⚠️ **제한적** | user/project agent는 전역에서 *호출·트리거*는 되지만, bkit 오케스트레이터(cto-lead/qa-lead/pm-lead)는 **고정 `Task()` allow-list**라 자동 위임 안 함. bkit agent는 `bkit:` 네임스페이스라 같은 이름 override도 깔끔하지 않음 |
| **Templates** | ❌ **안 됨** | bkit `lib/core/platform.js:78` `getTemplatePath()` = `getPluginPath('templates/...')` **하드코딩**. 스킬 SKILL.md도 `${CLAUDE_PLUGIN_ROOT}/templates/plan.template.md` 직참조. `bkit.config.json`의 `docPaths`는 **생성 문서 출력 경로**일 뿐 template 소스가 아님 |

---

## 3. repo 구조 — standalone vs bkit 레이어

판단 기준은 **"bkit 없이도 의미가 있나?"**:

```
chip-design-skills/
├── agents/        skills/   agent-kit/   hooks/   ← standalone (bkit 무관, 단독 동작)
└── bkit/                                           ← bkit 워크플로우에 *결합*되는 것만
    ├── agents/      (copy-rename 방식, §6)
    ├── hooks/       (bkit PDCA 보강 hook, §5)
    └── templates/   (PDCA/sprint 템플릿 override 소스, §7)
```

- `verilog-rtl-*` 4개, 6개 스킬 → bkit 무관하게 동작 → **top-level 유지**
- bkit PDCA 단계를 가로채는 hook, bkit 템플릿 교체본 → **`bkit/` 아래**

---

## 4. install.py 사용법

```bash
PY="C:/Python314/python.exe"; cd .../chip-design-skills

python install.py                 # 전체 → ~/.claude/ (skills+agents+kit+hooks+bkit-agents)
python install.py --dry-run       # 미리보기
python install.py --only hooks    # 한 컴포넌트: skills|agents|kit|hooks|bkit-agents

# project scope (bkit 우선순위상 project가 user global보다 우선):
python install.py --only agents --project /path/to/proj   # -> proj/.claude/agents/
python install.py --only hooks  --project /path/to/proj   # -> proj/.claude/hooks/ + settings.json

# bkit 템플릿 직패치 (§7-b):
python install.py --patch-bkit-templates
```

- hooks는 `hooks/`(standalone) + `bkit/hooks/`의 `*.py`를 **자동 발견** → 복사 + `settings.json`에 **멱등 등록**(파일 stem으로 dedupe).
- user scope는 설치 시점에 **절대경로를 계산**해 넣어 머신 포터블. project scope는 `${CLAUDE_PROJECT_DIR}` 사용.

---

## 5. Hook 추가 레시피 (공통화의 최적 지점)

bkit hook을 *제거*하는 음수 override는 불가 — **추가(union)만** 가능. 새 hook 추가:

1. `hooks/<name>.py` (또는 `bkit/hooks/<name>.py`) 작성. stdin JSON(`tool_name`, `tool_input`) 읽고,
   차단하려면 **exit 2 + stderr 메시지**, 통과는 exit 0. 오류 시 **fail-open(exit 0)**.
2. (선택) sidecar `hooks/<name>.json` 으로 트리거 지정. 기본값 `{"event":"PreToolUse","matcher":"Write|Edit"}`.
   예: Bash 대상이면 `{"event":"PreToolUse","matcher":"Bash"}`.
3. `python install.py --only hooks` 로 `~/.claude/`에 등록.

**user scope 공통 등록이 안전한 이유**: 정책에 안 걸리는 입력에서 **fail-open(통과)** 하도록 짜면,
모든 프로젝트에서 bkit hook과 나란히 돌아도 무해하다.

기존 예시:
- `hooks/guard-submodule-formal.py` — 공유 RTL submodule(`db/design`)에 formal/lint scratch 쓰기 차단. env `GUARD_SUBMODULE_DIRS`/`GUARD_DEDICATED_DIR`로 프로젝트별 조정.
- `hooks/guard-bash-nul.py` — MSYS bash에서 `> nul`(실제 파일 생성) 차단, `/dev/null` 유도. matcher=Bash.

---

## 6. Agent customization (copy-rename + 라우팅)

bkit agent는 `bkit:` 네임스페이스라 동명 override가 깔끔하지 않다. bkit 권장 방식(가이드 line 1508):

```bash
cp ~/.claude/plugins/cache/bkit-marketplace/bkit/<ver>/agents/starter-guide.md  bkit/agents/chip-guide.md
# bkit/agents/chip-guide.md 를 수정 후:
python install.py --only bkit-agents              # -> ~/.claude/agents/ (공통)
python install.py --only bkit-agents --project P  # -> P/.claude/agents/ (팀 공유)
```

**제약**: 오케스트레이터(cto-lead 등)는 고정 `Task()` allow-list라 이 agent를 자동 위임하지 못한다.
→ **직접 호출**하거나, **project CLAUDE.md에 라우팅 표**를 둬서 트리거로 부른다
(venezia-fpga CLAUDE.md "RTL Agent Routing" 패턴 — PDCA 단계별 advisor→coder→reviewer/prover).

---

## 7. Template override — config 불가, 2가지 우회

bkit은 PDCA/sprint 템플릿을 **플러그인 경로에서만** 읽는다(§2). 따라서:

### (a) 권장 — 지시 레이어 역전 (업그레이드 안전)
project `CLAUDE.md`(또는 `.claude/CLAUDE.md`)에 "PDCA 문서 생성 시 bkit 기본 템플릿 대신
`.ai/bkit-templates/<name>` 가 있으면 그걸 우선 사용"이라는 규칙을 둔다. CLAUDE.md는 SKILL.md 산문보다
우선하므로 Claude가 우리 템플릿을 읽는다. 스니펫: `bkit/templates/CLAUDE-redirect-snippet.md`.

### (b) 대안 — 플러그인 직패치 (취약)
```bash
python install.py --patch-bkit-templates   # bkit/templates/*.template.md -> 설치된 플러그인 templates/
```
플러그인 디렉토리는 **버전별**(`.../bkit/<ver>/`)이라 **업그레이드 때마다 재실행** 필요.

---

## 8. 검증 (배포 후 확인)

```bash
# 1) settings.json 병합 무결성 (기존 키 보존 + hooks 추가 확인)
python -c "import json;d=json.load(open(r'C:\Users\<U>\.claude\settings.json',encoding='utf-8'));print(sorted(d.keys()));[print(b.get('matcher'),[h['command'] for h in b['hooks']]) for b in d['hooks']['PreToolUse']]"

# 2) Claude Code 세션에서
/hooks      # 병합된(plugin+user+project) hook 목록 — 새 세션부터 반영
/agents     # 설치된 agent 목록
```

> ⚠️ hook은 **세션 시작 시 로드** — 등록 직후 현재 세션엔 미반영. 새 세션/재시작 후 `/hooks`로 확인.

---

## 9. 근거 파일 (재확인용)

| 주장 | 위치 |
|------|------|
| 우선순위 hierarchy | `bkit/<ver>/CUSTOMIZATION-GUIDE.md` line 665–675 |
| copy-rename 방식 | 같은 파일 line 1508 |
| 템플릿 하드코딩 | `bkit/<ver>/lib/core/platform.js:78-79` (`getTemplatePath`→`getPluginPath`) |
| 스킬 project 우선 | `bkit/<ver>/lib/skill-loader.js:4`, `:372` |
| bkit hook 등록 | `bkit/<ver>/hooks/hooks.json` (command hook, `${CLAUDE_PLUGIN_ROOT}`) |
| docPaths=출력경로 | `bkit/<ver>/bkit.config.json` `pdca.docPaths` |
| 오케스트레이터 allow-list | bkit agent 정의 `cto-lead.md` 등 `Task(...)` 고정 목록 |

---

## 10. RD-PDCA Team Overlay — PDCA 단계 세분화

bkit의 9-phase는 frozen 상수라 **단계 추가/분할은 fork 외 불가**(§2 templates와 같은 한계). 대신 bkit Agent Team이
**이미 각 phase를 council/swarm으로 fan-out**한다는 점을 이용해, "phase 세분화 = phase 안의 sub-step council" 로 구현한다.

### 구조 (2-tier 병행)
```
Tier 1 (coarse, bkit 그대로):  /pdca = pm→plan→design→do→check→act→qa→report→archive  (상태머신·게이트·audit·Trust)
Tier 2 (fine, project-local):  chip-cto-lead 가 한 phase를 sub-step council/swarm으로 위임 (verilog-rtl-* agents)
```
- bkit `cto-lead`는 고정 allow-list라 `verilog-rtl-*`를 못 부른다 → `chip-cto-lead`(병행, 대체 아님)가 그 공백을 메운다.
  선례: bkit `pm-lead-skill-patch.md`(lead를 plugin 수정 없이 project-local 확장).
- `chip-cto-lead`는 phase를 **전이하지 않는다**(bkit 소유). 현재 phase 안만 세분화.

### Swappable 설계 (대규모 업데이트 대비)
sub-step은 **데이터**다 — agent·템플릿은 읽거나 생성만 한다:

| 구성 | 위치 | 역할 |
|------|------|------|
| 프로파일(단일 소스) | `bkit/workflow/substeps.<profile>.json` | phase별 sub-step·owner·gate·checklist |
| 도메인 lead | `bkit/agents/chip-cto-lead.md` | `.ai/rd-pdca-substeps.json` 읽어 Task fan-out (하드코딩 없음) |
| 생성기 | `install.py --gen-rd-pdca [--profile N] --project DIR` | 프로파일 → `.ai/rd-pdca-substeps.json` + `.ai/bkit-templates/{design,do,analysis}.template.md` 생성 |

→ 도메인 교체 = **JSON 한 개 수정/추가 후 재생성**. agent·생성기 불변. 상세: `../bkit/workflow/README.md`.

### 공통형 프로파일 (`common`, venezia-fpga 기준 digital RTL/FPGA)
| phase | pattern | sub-steps (⛔=gate) |
|-------|---------|---------------------|
| design | council | system-arch⛔, block-partition⛔, interface-regmap, cdc-reset, verif-plan |
| do | swarm | rtl-impl, testbench-sim, synth-pnr, top-integration |
| check | council | static-review⛔(reviewer), formal-prove⛔(prover), design-impl-gap(gap-detector) |

### 사용 절차
```bash
python install.py --only bkit-agents                              # chip-cto-lead 배포 (~/.claude/agents)
python install.py --gen-rd-pdca --project <repo>                  # 프로파일+템플릿 생성
# <repo>/CLAUDE.md 에 .ai/bkit-templates/CLAUDE-redirect-snippet.md 붙여넣기 (bkit이 템플릿 읽도록, §7)
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1                      # 진짜 council/swarm 병렬 (없으면 prose-fallback)
# 이후 Design/Do/Check phase에서 chip-cto-lead 호출 → sub-step 게이트 fan-out
```

### 한계
- Agent Teams 플래그 없으면 병렬 council/swarm이 **prose-fallback**(순차 산문)으로 동작.
- analog/lab measurement sub-step은 코드 게이트 불가 → checklist + `.ai/` 산출물로만(PASS는 사람).
- `owner`가 bkit 소속(qa-strategist 등)이면 네임스페이스로 위임 실패 가능 → `chip-cto-lead`가 `/pdca`로 handoff.

---

## 관련 문서
- `../bkit/workflow/README.md` — RD-PDCA 프로파일 스키마 + 교체 절차
- `../bkit/agents/chip-cto-lead.md` — 병행 도메인 lead
- `../bkit/README.md` — 이 가이드의 요약 + repo 레이어 설명
- `../agent-kit/methodology.md` — RTL 도메인 방법론(Constrain & Escalate)
- venezia-fpga `CLAUDE.md` — 이 패턴을 실제 적용한 프로젝트(RTL Agent Routing)
