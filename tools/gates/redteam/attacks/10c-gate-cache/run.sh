#!/usr/bin/env bash
# 공격 10c: 캐시 훼손 / 캐시 읽기·실행(허용) / 캐시로 리다이렉트·cp(거부)
# 기대 근거: 05 §13.2 #10c, §4.4 캐시 대조, §6.2 저장소 내부 규칙 예외(review31 N-07·review32 M-09)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook warm-cache --kind record --event PreToolUse --agent none --tool Write --input-file inputs/warm-cache.json
rt hook allow-run-cache-script --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/allow-run-cache-script.json
rt hook allow-pythonpath-cache --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/allow-pythonpath-cache.json
rt hook allow-ps-pythonpath-cache --kind control --event PreToolUse --agent none --tool PowerShell --input-file inputs/allow-ps-pythonpath-cache.json
rt hook attack-redirect-into-cache --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/attack-redirect-into-cache.json
rt hook attack-cp-into-cache --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/attack-cp-into-cache.json
rt tamper-cache tamper
rt hook attack-after-tamper --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-after-tamper.json
rt hook control-after-tamper --kind control --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/control-after-tamper.json
