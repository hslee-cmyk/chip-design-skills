#!/usr/bin/env bash
# 공격 10b: 역할 밖 쓰기·트레일러 없는 역할 밖 커밋·역할 밖 병합은 통과(오거부 0), 판정 환경 이름은 예외
# 기대 근거: 05 §13.2 #10b, §5 판정 범위, §8.2-1·(라), §9.2-3, review31 N-01·N-12
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook pass-temp-write --kind control --event PreToolUse --agent none --tool Write --input-file inputs/pass-temp-write.json
rt hook pass-other-skill-write --kind control --event PreToolUse --agent none --tool Write --input-file inputs/pass-other-skill-write.json
rt hook pass-rtl-write --kind control --event PreToolUse --agent none --tool Write --input-file inputs/pass-rtl-write.json
rt hook attack-other-skill-conftest --kind attack --event PreToolUse --agent none --tool Write --input-file inputs/attack-other-skill-conftest.json
rt hook attack-other-skill-pyproject --kind attack --event PreToolUse --agent none --tool Write --input-file inputs/attack-other-skill-pyproject.json
rt trailerless pass-trailerless-rtl-commit --kind control --path rtl/core.v --jtext '"module core;\n// changed\nendmodule\n"'
rt git '@{WORK}' worktree add -q '@{SB}/rtlside' -b rt10b/side '@{B0}'
rt write '@{SB}/rtlside/rtl/alu.v' --jtext '"module alu;\nendmodule\n"'
rt git '@{SB}/rtlside' add -A
rt git '@{SB}/rtlside' commit -q -m 'rtl alu'
rt git '@{WORK}' worktree add -q '@{SB}/rtlmain' -b rt10b/main '@{B0}'
rt write '@{SB}/rtlmain/skills/verilog-rtl/notes.md' --jtext '"# notes\nmore\n"'
rt git '@{SB}/rtlmain' add -A
rt git '@{SB}/rtlmain' commit -q -m 'rtl notes'
rt git '@{SB}/rtlmain' merge --no-ff --no-commit rt10b/side
rt el3 pass-outside-merge-el3 --kind control --cwd '@{SB}/rtlmain' --msg 'merge rtl side'
rt git '@{SB}/rtlmain' commit -q -m 'merge rtl side'
rt el4 pass-outside-merge-el4 --kind control --old '@{B0}' --new rt10b/main
