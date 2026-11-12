---
kind: episode
id: EP-2026-11-12-claude-md-restructure
project: chip-design-skills
date: 2026-11-12
slug: claude-md-restructure
commits: [a9d37ae8, e9d8bc55, 334b9ee5]
transcript: C:\Users\HSLEE\.claude\projects\C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills\7660cc1e-3837-45a1-aff1-4608848a4f71.jsonl
---
<!-- rel: about=P-CLAUDE-MD-SCOPE,P-INSTR-MOVE-THEN-COMPRESS,P-HOOK-TEST-ENV,P-INSTR-PLACEMENT,P-INSTR-CONCISE,P-OBLIGATION-NOT-PROSE,P-AUTO-MEMORY-LIMIT; alias=CLAUDE.md 개정,rules 압축,의무 hook,report-bundle,O-229 -->

# 키트 CLAUDE.md 개정(Anthropic 가이드) + 의무 적용 + rules 압축

## 목표
71줄·15.8KB CLAUDE.md를 가이드(사실=CLAUDE.md, 절차=skill, 상시 모듈=rules, 반드시=hook)대로 나누고, 반복 누락되던 보고 지시(원칙 26)를 의무 hook으로 강제.

## 결정 (사용자 원문 인용)
- 계획 승인 — "승인할께. 진행해"
- 짧고 연상 가능한 문장 — "claude.md에 문장을 작성할때는 인공지능이 알고 있는 기존 지식을 활용할 수 있게 연상가능하게 해서 문장자체가 짧도록 작성해"
- rules도 압축 — "rules밑에 있는 것도 압축안을 만들어" → 4차 판정 뒤 "승인"
- 원칙 27 삭제(PREF-LANG 중복), 원칙 26 정본을 skill `report-bundle`로

## 실패와 원인
- 1단계 분할 독립 대조 Major 3 → 범위 문단 축소·원칙 26 강제 공백·cloud0 `ASK_GATE_PRINCIPLES`가 옛 파일 지시 → 정본 이동 시 소비자(다른 호스트 settings 포함) 누락
- 실세션 Stop hook 미발동 → hook 프로세스에 APPDATA가 없어 user site의 PyYAML import 실패, 의무 파일을 못 읽음 → `_import_yaml`이 user site를 직접 추가
- headless `claude -p --resume`의 `/compact`는 실제 압축 안 함 → 사용자 대화형 /compact로 실측(rules 재주입 확인)
- rules 압축 판정 Major 7→3→1→0 — 짧은 한정어(적용 대상·시점·승인)가 범위를 정함
- cloud0에서 ob_common 수동 실행 SyntaxError → 시스템 python3 3.6으로 돌림(hook 등록은 venv 3.12) — 오경보

## 결과
- kit: CLAUDE.md 22줄·3.3KB, rules 4개, skill report-bundle, `.ai/obligations.yaml`; rules 13,687B → 10,622B (`334b9ee5`)
- ai-memory: ob_* hook 4개 + 12 test, P-CLAUDE-MD-SCOPE·P-INSTR-CONCISE·P-INSTR-PLACEMENT·P-AUTO-MEMORY-LIMIT·P-OBLIGATION-NOT-PROSE (`f257da5`까지)
- 실세션: 빠진 보고 묶음 1회 차단 → 보완 확인; /compact 뒤 rules 재주입 확인
- 교훈 승격(사용자 승인): P-HOOK-TEST-ENV · P-INSTR-MOVE-THEN-COMPRESS · P-AUTO-MEMORY-LIMIT 보강 — ai-memory toolflow/claude-code-instructions.md
