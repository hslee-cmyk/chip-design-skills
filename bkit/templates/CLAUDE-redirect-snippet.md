<!--
이 블록을 프로젝트의 CLAUDE.md(또는 .claude/CLAUDE.md)에 붙여넣으면,
bkit이 PDCA 문서를 생성할 때 기본 플러그인 템플릿 대신 프로젝트 템플릿을 쓰게 된다.
CLAUDE.md는 bkit 스킬 SKILL.md의 산문보다 우선하므로 동작한다 (지시 레이어 override).
실제로 override할 템플릿만 .ai/bkit-templates/ 에 두면 된다 — 없는 것은 bkit 기본을 그대로 사용.
-->

## bkit 템플릿 override (PDCA 문서 생성 시)

PDCA(`/pdca`) 또는 sprint 문서를 생성할 때, 아래 표에 해당 템플릿이 **존재하면**
bkit 기본 템플릿(`${CLAUDE_PLUGIN_ROOT}/templates/...`) 대신 **이 프로젝트 템플릿을 사용**한다.
없으면 bkit 기본을 쓴다.

| 문서 | override 템플릿 (있으면 우선) |
|------|------------------------------|
| Plan | `.ai/bkit-templates/plan.template.md` |
| Design | `.ai/bkit-templates/design.template.md` |
| Analysis | `.ai/bkit-templates/analysis.template.md` |
| Report | `.ai/bkit-templates/report.template.md` |
