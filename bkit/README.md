# bkit/ — bkit 워크플로우 customization 레이어

이 폴더는 **bkit(PDCA/sprint 플러그인) 동작을 customize**하기 위한 자산의 단일 소스다.
top-level `agents/` · `skills/` · `agent-kit/` · `hooks/` 는 **bkit 없이도 동작하는 standalone 칩 설계 자산**이고,
이 `bkit/` 아래는 **bkit가 있어야 의미가 있는 것**만 둔다.

```
bkit/
├── agents/      bkit 워크플로우용 에이전트 (copy-rename 방식, 아래 §1)
├── hooks/       bkit PDCA 단계를 보강하는 hook (union 병합, 아래 §2)
└── templates/   bkit PDCA/sprint 템플릿 override 소스 (아래 §3 — 주의: 비자명)
```

## 우선순위 (검증됨, bkit CUSTOMIZATION-GUIDE + 플러그인 코드 대조)

```
Managed > CLI > Project Local(.claude/settings.local.json)
        > Project Shared(.claude/settings.json) > User Global(~/.claude)  ← 최하위
```
"Project-level configurations override global configurations with the same name."
→ **project `.claude/` 가 최우선, 그 다음이 user global `~/.claude/`.**

그러나 "user global이 bkit을 customize하느냐"는 **컴포넌트마다 다르다**:

| 컴포넌트 | user global 적용 | 메커니즘 |
|---|---|---|
| **Hooks** | ✅ 잘 됨 (가산 union) | Claude Code가 plugin+user+project hook을 **전부 발동**. shadow 없음 |
| **Skills** | ✅ 됨 (project 우선) | bkit `skill-loader.js`: "project-local taking precedence" |
| **Agents** | ⚠️ 제한적 | 전역 호출·트리거는 됨. 단 bkit 오케스트레이터(cto-lead 등)는 **고정 Task() allow-list** → 자동 위임 안 함 |
| **Templates** | ❌ 안 됨 | bkit `getTemplatePath()` = `${CLAUDE_PLUGIN_ROOT}/templates/` **하드코딩**. config·precedence override 불가 |

## §1 agents — copy-rename

bkit agent는 `bkit:` 네임스페이스라 **같은 이름 override가 깔끔하지 않다.** bkit 권장 방식(가이드 line 1508):
플러그인 agent를 **새 이름으로 복사 후 수정**한다.
```bash
cp ~/.claude/plugins/cache/bkit-marketplace/bkit/<ver>/agents/starter-guide.md  bkit/agents/chip-guide.md
```
오케스트레이터(cto-lead/qa-lead)는 이들을 자동 위임하지 못하므로 **직접 호출 또는 CLAUDE.md 라우팅 표**로 부른다
(venezia-fpga CLAUDE.md의 "RTL Agent Routing" 패턴).
→ `install.py --only bkit` 가 `~/.claude/agents/`(공통) 또는 `--project`로 `<proj>/.claude/agents/` 에 설치.

## §2 hooks — 가산 union (공통화의 최적 지점)

bkit hook은 plugin `hooks.json` command hook. 여기에 hook을 추가하면 **bkit hook과 나란히 모두 실행**된다
(bkit hook을 *제거*하는 음수 override는 불가, *추가*만 가능).
→ `install.py --only bkit` (또는 `--only hooks`) 가 `~/.claude/hooks/`에 복사 + `~/.claude/settings.json`에 멱등 등록.

## §3 templates — ⚠️ 비자명 (config override 불가)

bkit은 PDCA/sprint 템플릿을 **플러그인 경로에서만** 읽는다 (`getTemplatePath` 하드코딩, 스킬 SKILL.md도
`${CLAUDE_PLUGIN_ROOT}/templates/...` 직참조). `bkit.config.json`의 `docPaths`는 **생성 문서의 출력 경로**일 뿐
template 소스가 아니다. 따라서 단순히 `~/.claude/templates`·project `templates/`에 둬도 **bkit이 안 읽는다.**

업그레이드-안전한 override 2가지:

- **(권장) 지시 레이어 역전** — project `CLAUDE.md`에 "PDCA 문서 생성 시 bkit 기본 템플릿 대신
  `.ai/bkit-templates/<name>` 를 사용하라"는 규칙을 둔다. CLAUDE.md는 SKILL.md 산문보다 우선하므로
  Claude가 우리 템플릿을 읽는다. → 스니펫: `bkit/templates/CLAUDE-redirect-snippet.md`
- **(대안) 플러그인 패치** — `install.py --patch-bkit-templates` 가 `bkit/templates/*.template.md` 를
  현재 설치된 플러그인의 `templates/`에 덮어쓴다. **플러그인 업그레이드 때마다 재실행 필요**(취약).
