#!/usr/bin/env bash
# 공격 10: 메인 세션 Edit / PowerShell Set-Content / general-purpose agent Edit (엔진 소스)
# 기대 근거: 05 §13.2 #10(EL1 exit 2), §5 오케스트레이터 판정 범위(overlaps_any), N3.12.1(오케스트레이터는 엔진 소스 쓰기 불가)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook control-main-doc --kind control --event PreToolUse --agent none --tool Edit --input-file inputs/control-main-doc.json
rt hook attack-main-edit --kind attack --event PreToolUse --agent none --tool Edit --input-file inputs/attack-main-edit.json
rt hook attack-powershell-set-content --kind attack --event PreToolUse --agent none --tool PowerShell --input-file inputs/attack-powershell-set-content.json
rt hook attack-general-purpose-edit --kind attack --event PreToolUse --agent general-purpose --tool Edit --input-file inputs/attack-general-purpose-edit.json
rt hook attack-empty-agent-type-edit --kind attack --event PreToolUse --agent empty --tool Edit --input-file inputs/attack-empty-agent-type-edit.json
