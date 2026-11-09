#!/usr/bin/env bash
# track.sh -- harness 쪽 대기 명령(Bash run_in_background:true 로 띄운다. 한 호출 < 2 h).
# 쓰기: bash track.sh <JOB_DIR(Windows 경로)> [MAX_WAIT_S=7000] [POLL_S=30] [PROGRESS_FILE]
#   PROGRESS_FILE: 줄 수만 진행 표시로 찍을 파일(예: --out jsonl). 판정 아님.
# exit 0 = rc 파일 생김(실행 끝 -- rc 값은 출력 'RESULT rc=' 줄), 3 = 대기 상한 도달·아직 실행 중(같은 명령을 다시 건다),
#      4 = 비정상 종료(프로세스 없음 + rc 없음 -- 침묵 != 성공), 2 = 사용법·상태 오류.
# 같은 내용을 <JOB_DIR>/track.log 에도 덧붙인다.
set -euo pipefail
PY=C:/Python314/python.exe
HERE="$(cygpath -u "$(dirname "$0")")"
[ $# -ge 1 ] || { echo "usage: track.sh JOB_DIR [MAX_WAIT_S] [POLL_S] [PROGRESS_FILE]" >&2; exit 2; }
JOB_W="$1"; MAX_WAIT="${2:-7000}"; POLL="${3:-30}"; PROG_W="${4:-}"
JOB_U="$(cygpath -u "$JOB_W")"
RES="$JOB_U/job.resolved.json"; LJ="$JOB_U/launch.json"; LOG="$JOB_U/track.log"
[ -f "$RES" ] || { echo "missing $RES" >&2; exit 2; }
[ -f "$LJ" ] || { echo "missing $LJ (launch.ps1 not run?)" >&2; exit 2; }
jget() { "$PY" -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8'))[sys.argv[2]] or '')" "$1" "$2"; }
RC_U="$(cygpath -u "$(jget "$RES" rc)")"
STDOUT_U="$(cygpath -u "$(jget "$RES" stdout)")"
STDERR_U="$(cygpath -u "$(jget "$RES" stderr)")"
PID="$(jget "$LJ" ProcessId)"; CDATE="$(jget "$LJ" CreationDateUtc)"; T0="$(jget "$LJ" LaunchedAtUtc)"
PROG_U=""; [ -n "$PROG_W" ] && PROG_U="$(cygpath -u "$PROG_W")"
log() { local m; m="$(date '+%F %T') $*"; echo "$m"; echo "$m" >> "$LOG"; }
elapsed() { "$PY" -c "import datetime as d,sys;t=d.datetime.fromisoformat(sys.argv[1].replace('Z','+00:00'));print(int((d.datetime.now(d.timezone.utc)-t).total_seconds()))" "$T0"; }
pinfo() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$HERE/proc_info.ps1")" -ProcId "$PID" -CreationDateUtc "$CDATE" | tr -d '\r'; }
finish() {  # $1 = exit code
  log "elapsed_s=$(elapsed) stdout_bytes=$(stat -c %s "$STDOUT_U" 2>/dev/null || echo NA) stderr_bytes=$(stat -c %s "$STDERR_U" 2>/dev/null || echo NA)"
  if [ -f "$STDERR_U" ]; then log "--- stderr tail ---"; tail -n 15 "$STDERR_U" | tee -a "$LOG"; fi
  exit "$1"
}
# 래퍼 PID 파일과 launch.json의 PID가 같은지(래퍼가 막 떴으면 pid 파일이 아직 없을 수 있다)
PIDF_U="$(cygpath -u "$(jget "$RES" pid)")"
log "track start job=$JOB_W pid=$PID created=$CDATE max_wait=$MAX_WAIT poll=$POLL"
START=$SECONDS
while :; do
  if [ -f "$RC_U" ]; then
    RCV="$(tr -d '\r\n ' < "$RC_U")"
    log "RESULT rc=$RCV (rc file present)"
    finish 0
  fi
  INFO="$(pinfo)"
  ALIVE="$("$PY" -c "import json,sys;d=json.loads(sys.argv[1]);print('1' if d['alive'] and d['same_process'] is not False else '0')" "$INFO")"
  if [ "$ALIVE" != 1 ]; then
    sleep 2
    if [ -f "$RC_U" ]; then RCV="$(tr -d '\r\n ' < "$RC_U")"; log "RESULT rc=$RCV (rc file present)"; finish 0; fi
    log "ABNORMAL: process $PID gone (or PID reused: $INFO) and no rc file"
    finish 4
  fi
  if [ -f "$PIDF_U" ]; then
    PF="$(tr -d '\r\n ' < "$PIDF_U")"
    [ "$PF" = "$PID" ] || log "WARN pid file=$PF != launch.json ProcessId=$PID"
  fi
  if [ $((SECONDS - START)) -ge "$MAX_WAIT" ]; then
    log "WAIT_LIMIT: still running after ${MAX_WAIT}s of this call (total elapsed $(elapsed)s) -- re-arm the same track command"
    exit 3
  fi
  if [ -n "$PROG_U" ] && [ $(( (SECONDS - START) % 600 )) -lt "$POLL" ]; then
    log "progress: $(wc -l < "$PROG_U" 2>/dev/null || echo 0) lines in $PROG_W, elapsed $(elapsed)s"
  fi
  sleep "$POLL"
done
