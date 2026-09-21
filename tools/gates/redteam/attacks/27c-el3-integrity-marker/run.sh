#!/usr/bin/env bash
# 공격 27c: integrity-failed 표지가 있으면 EL3(pre-commit·commit-msg·pre-merge-commit)가 exit 1 + 표지 경로·복구 절차(D-8)
# 기대 근거: spec card 20260921-gate-flow-liveness 계약 3(D-8), design 05 §3.3('대조 실패는 `<git-common-dir>/gmid-gate-cache/integrity-failed` 표지 … EL1·EL3는 이 파일이 있으면 … 거부', '무결성 실패 메시지는 … 복구 절차(… `integrity.py check --scope session`)를 적는다'), §8.1(EL3 = pre-commit·commit-msg·pre-merge-commit), §17(EL3 0 통과 / 1 차단), oracle (a)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt write '@{WORK}/rtl/core.v' --jtext '"module core;\n// rt 27c\nendmodule\n"'
rt git '@{WORK}' add rtl/core.v
rt githook control-pre-commit-no-marker --kind control --hook pre-commit --msg 'rt rtl tweak'
rt githook control-commit-msg-no-marker --kind control --hook commit-msg --msg 'rt rtl tweak'
rt githook control-pre-merge-commit-no-marker --kind control --hook pre-merge-commit --msg 'rt rtl tweak'
# §3.3 표지: 세션 시작 대조 실패가 남기는 파일
rt write '@{GITDIR}/gmid-gate-cache/integrity-failed' --jtext '"rt 27c marker\n"'
rt githook attack-pre-commit-marker --kind attack --hook pre-commit --msg 'rt rtl tweak'
rt githook attack-commit-msg-marker --kind attack --hook commit-msg --msg 'rt rtl tweak'
rt githook attack-pre-merge-commit-marker --kind attack --hook pre-merge-commit --msg 'rt rtl tweak'
