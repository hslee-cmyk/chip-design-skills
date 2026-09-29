#!/usr/bin/env bash
# 공격 30: 행 3(나) 재판정 통과 캐시 `rejudged` -- 통과 구간 기록, 마지막이 아닌 캐시 구간 건너뜀, 마지막 줄은 항상 재판정, 실패·깨진 줄·로그 밖 쌍 제외
# 기대 근거: spec card 20260929-rejudge-cache '관찰 가능한 계약' 1~8, '거부해야 할 입력', '무동작 판정 입력', design 05 §3.3 행 3(나)(2026-09-29 개정)·§13.2 #22 (f)·§13.5 N-06, oracle (a)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
# 관찰값: rejudge-obs = integrity.py check의 행 3b 행 수·실패 수·요약 행, rejudged-file = C의 줄(커밋 id를 라벨 B0·C1·F·C3로).
# 순서가 곧 입력이다: 각 단계의 C는 앞 단계가 남긴 것(+ 이 스크립트가 적은 줄)이다.
set -e
rt() { "$PY" -B "$RT" "$@"; }
L="--label B0 --label C1 --label F --label C3"

# --- 1. 로그 B0 B0 / B0 C1 / C1 F(마지막 줄 = 위조), C 없음 ---------------------------------------------
# 계약 8: 행 3b는 --scope session에만 있다 -> 다른 scope는 3b 행이 없고 C를 만들지 않는다
rt rejudge-obs scope-push-no-row3b --kind control --scope push $L
rt rejudged-file scope-push-no-cache --kind control $L
# 무동작 판정 입력 + 거부해야 할 입력 1(C가 빈 때): 변경 전과 같은 구간별 행, 위조 구간 실패
rt rejudge-obs first-no-cache-last-forged --kind attack $L
# 계약 1(통과 구간은 C에 있다)·계약 4(실패 구간은 적지 않는다)
rt rejudged-file first-no-cache-cache-file --kind control $L

# --- 2. 같은 로그, C에 마지막 줄 위조 구간(C1 F)을 적어 둔다 = 공격 22 (f)의 기록된(마지막 줄) 형태 ---------
rt write '@{GITDIR}/gmid-gate-cache/rejudged' --append --jtext '"@{C1} @{F}\n"'
# 계약 2(B0 C1은 마지막이 아니고 C에 있다 -> 건너뜀)·계약 3(마지막 줄은 C에 있어도 재판정 -> ok false)·계약 6(요약 행)
rt rejudge-obs cache-last-forged --kind attack $L
# 계약 4 뒷문장: C에 있던 마지막 줄 구간이 재판정에서 실패하면 C에서 뺀다
rt rejudged-file cache-last-forged-cache-file --kind control $L

# --- 3. gate master를 C3로 옮기고 로그에 F C3를 덧붙인다(위조 구간 C1 F가 마지막이 아니게 된다) -------------
rt advance '@{C3}'
rt write '@{GATE}/gmid-accept-log' --append --jtext '"@{F} @{C3} 2026-09-29T10:02:00\n"'
# 거부해야 할 입력 2: C에 없는, 마지막이 아닌 위조 구간 -> 재판정해 실패. B0 C1만 건너뜀(계약 2·6)
rt rejudge-obs nonlast-forged-not-cached --kind attack $L
rt rejudged-file nonlast-forged-not-cached-cache-file --kind control $L

# --- 4. C를 형식이 깨진 줄·현재 로그에 없는 쌍으로만 채운다(위조 구간은 없음) -----------------------------
# 줄: 필드 1개 / 필드 3개(앞 둘은 로그에 있는 통과 쌍) / 40자리지만 16진이 아님 / 형식은 맞지만 로그에 없는 쌍 2개 / 빈 줄
rt write '@{GITDIR}/gmid-gate-cache/rejudged' --jtext '"@{B0}\n@{B0} @{C1} extra\ngggggggggggggggggggggggggggggggggggggggg hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh\n@{B0} @{C3}\n@{C3} @{F}\n\n"'
# 거부해야 할 입력 3 + 계약 5: 깨진 줄·로그 밖 쌍은 무시 -> 세 구간 모두 재판정, 위조 구간 실패, 요약 행 없음
rt rejudge-obs garbage-cache-nonlast-forged --kind attack $L
# 계약 5: 다시 쓴 C에는 깨진 줄·로그 밖 쌍이 남지 않는다(계약 1: 통과한 두 구간만)
rt rejudged-file garbage-cache-rewritten --kind control $L

# --- 5. C에 마지막이 아닌 위조 구간(C1 F)을 적어 둔다 = review31 N-06 형태(§13.5 알려진 한계) -------------
rt write '@{GITDIR}/gmid-gate-cache/rejudged' --append --jtext '"@{C1} @{F}\n"'
# 계약 2·6: C에 있는 마지막이 아닌 구간 둘(B0 C1, C1 F)은 재판정하지 않는다 -> 행 3b는 마지막 줄 한 행 + 요약 행 `캐시 통과 2구간`
rt rejudge-obs nonlast-forged-cached --kind control $L
# 계약 4·5: 건너뛴 쌍은 로그에 있으므로 남고, 마지막 줄 통과 쌍은 계속 있다
rt rejudged-file nonlast-forged-cached-cache-file --kind control $L

# --- 6. 계약 7: role_paths.ensure_cache는 C를 지우지 않는다 -------------------------------------------------
# ensure_cache가 지우는 대상(40자리 16진 디렉터리, `.tmp-` 접두)을 하나씩 두고 EL1 호출로 캐시를 채운다
rt write '@{GITDIR}/gmid-gate-cache/0000000000000000000000000000000000000000/rt30.txt' --jtext '"rt 30 stale\n"'
rt write '@{GITDIR}/gmid-gate-cache/.tmp-rt30/rt30.txt' --jtext '"rt 30 tmp\n"'
rt hook warm-cache --kind record --event PreToolUse --agent none --tool Write --input-file inputs/warm-cache.json
rt exists ensure-cache-ran-stale-dir --kind precondition --path '@{GITDIR}/gmid-gate-cache/0000000000000000000000000000000000000000'
rt exists ensure-cache-ran-tmp --kind precondition --path '@{GITDIR}/gmid-gate-cache/.tmp-rt30'
rt rejudged-file ensure-cache-keeps-rejudged --kind control $L
