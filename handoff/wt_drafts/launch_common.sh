# launch_common.sh -- _drafts 착수 0단계 launch 스크립트 8개(v3_binding·v3_scope·b34·b26pre·backfill·b26_1·b26_1_carry·b33)가
# 맨 앞에서 source하는 공통 함수. review_launch_scripts.md(2026-10-02) r1 반영:
#   S1  실제 저장소 판별 = 정규화한 git-common-dir 비교(문자열 비교 금지 -- 끝 '/', C:/…, 대소문자, worktree 경로 모두 같은 저장소)
#   m3·m5 임시 파일 = 상태 파일 옆 디렉터리(TMPDIR·TMP·TEMP 복원 -- 자식 bash는 TEMP·TMP를 잃어 Python이 C:\WINDOWS\Temp에 쓴다)
#   m6  '선행 card 병합' 판정 하나 = gate 트리의 판정 기록 .ai/verification/<id>.json: id 일치, checks = V1~V10 정확히, verdict 전부 PASS·N/A
#   m8  measured rev 단일 출처 규약 하나 = 문서에서 정해진 앵커의 **마지막** 출현(재측정 문단을 덧붙이는 방식과 맞음). 앞선 출현은 전부 그 rev의 조상이어야 한다
# 원칙(B1): EL1(PreToolUse)이 판정하는 git 명령(worktree add/remove, branch -D, push, reset·checkout --·restore·update-ref 등 참조 이동)은
#   스크립트 안에서 실행하지 않는다 -- 스크립트 안에서 돌면 EL1이 바깥 `bash …` 문자열만 보고 판정을 건너뛴다. 오케스트레이터가 단독 호출하도록 명령을 출력만 한다.
# 이 파일은 함수 정의만 한다(source 시 부작용 없음). 실패는 return 1 -- 부르는 쪽 set -e가 멈춘다.

LC_R_REAL=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
LC_W_REAL=/c/Users/HSLEE/Documents/Todoc/fpga/wt
LC_GATE_REAL=/c/Users/HSLEE/Documents/Todoc/fpga/gmid-gate.git
LC_PY=/c/Python314/python.exe

# 경로 정규화(없는 경로도 됨): C:/·C:\·/c/ 표기 통일 -> 절대·'..' 해석 -> C:/ 형식 -> 소문자 -> 끝 '/' 제거
lc_norm() {
  local q
  [ -n "${1:-}" ] || return 1
  q=$(cygpath -u -- "$1") || return 1
  q=$(realpath -m -- "$q") || return 1
  q=$(cygpath -m -- "$q") || return 1
  q=${q%/}
  printf '%s' "$q" | tr '[:upper:]' '[:lower:]'
}
lc_same_path() { local a b; a=$(lc_norm "$1") || return 2; b=$(lc_norm "$2") || return 2; [ "$a" = "$b" ]; }

# <저장소 경로> -> 정규화한 git-common-dir(실패하면 return 1)
lc_common_dir() {
  local c
  c=$(git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  [ -n "$c" ] || return 1
  lc_norm "$c"
}

# S1: R이 실제 저장소(같은 git-common-dir -- 별칭·worktree 포함)인지 판정해 LC_REAL=1|0을 정한다.
#   --repo를 썼는데(R 문자열 != R_REAL) 실제 저장소로 정규화되면 거부(exit 2): 모래상자 전용 완화·상태 파일 분리가 실제 저장소에 적용되는 경로를 닫는다.
#   복제본 모드에서 remote gate가 실제 gate를 가리켜도 거부(출력되는 push·fetch가 실제 gate로 간다).
lc_repo_guard() {   # <R> <R_REAL 문자열>
  local R=$1 RR=$2 rc cr g
  cr=$(lc_common_dir "$RR") || { echo "[중단] 실제 저장소 $RR의 git-common-dir을 읽지 못했다" >&2; exit 2; }
  rc=$(lc_common_dir "$R") || { echo "[중단] --repo $R가 git 저장소가 아니다(git-common-dir 없음)" >&2; exit 2; }
  if [ "$rc" = "$cr" ]; then
    [ "$R" = "$RR" ] || { echo "[중단] --repo $R는 실제 저장소(git-common-dir $cr)를 가리킨다 -- 실제 저장소에서는 --repo를 쓰지 않는다(별칭·worktree 경로 포함, review_launch_scripts S1)" >&2; exit 2; }
    LC_REAL=1
  else
    g=$(git -C "$R" config --get remote.gate.url 2>/dev/null || true)
    if [ -n "$g" ] && lc_same_path "$g" "$LC_GATE_REAL"; then
      echo "[중단] 복제본 $R의 remote gate가 실제 gate($g)를 가리킨다 -- 모래상자 gate로 바꾼다" >&2; exit 2
    fi
    LC_REAL=0
  fi
}

# 실제 모드: 값이 실제 값과 같은 경로여야 한다 / 복제본 모드: 실제 값과 다른 경로여야 한다. <이름> <값> <실제 값>
lc_need_real() { lc_same_path "$2" "$3" || { echo "[중단] 실제 저장소에서는 $1을 바꾸지 않는다($2)" >&2; exit 2; }; }
lc_need_sandbox() {
  case "$2" in /*|[A-Za-z]:[/\\]*) ;; *) echo "[중단] $1은 절대 경로로($2 -- interface_card --out·cd 서브셸이 상대 경로를 다르게 푼다)" >&2; exit 2 ;; esac
  if lc_same_path "$2" "$3"; then echo "[중단] --repo(복제본) 사용 시 $1 모래상자 값 필수(실제 값 $3 보호)" >&2; exit 2; fi
}

# 오케스트레이터가 단독 호출할 push 명령(출력용). Bash 도구 셸은 APPDATA를 자식에 넘기지 않아(실측: printenv APPDATA 빈 값) gate pre-receive(EL4)의
# Python이 사용자 site의 jsonschema를 못 읽는다('로더 규칙 4 jsonschema import 실패' -- B26-1 착수 스크립트 실측). `env NAME=값 git …`은 EL1이 env를 벗겨
# `git push`로 판정한다(role_hooks._unwrap; GIT_CONFIG* 이름만 거부).
lc_push_cmd() {   # <R>
  printf "env APPDATA='C:\\\\Users\\\\HSLEE\\\\AppData\\\\Roaming' LOCALAPPDATA='C:\\\\Users\\\\HSLEE\\\\AppData\\\\Local' git -C %s push gate master:master" "$1"
}

# m3·m5: 임시 디렉터리 = <상태 파일>.tmpd(모래상자 실행은 모래상자 안). mktemp는 TMPDIR(POSIX), Python은 TMPDIR·TEMP·TMP(Windows 형)를 읽는다.
lc_tmp_setup() {   # <상태 파일>
  local d="$1.tmpd"
  mkdir -p "$d"
  export TMPDIR="$d"
  TMP=$(cygpath -w -- "$d"); TEMP=$TMP
  export TMP TEMP
}

# m6: 선행 card 병합 판정(단일 기준). <R> <rev> <id> -- 0 = 병합(판정 기록 V1~V10 전부 PASS·N/A), 1 = 아님(이유 stderr)
lc_pred_ok() {
  local R=$1 rev=$2 id=$3
  git -C "$R" cat-file -e "$rev:.ai/verification/$id.json" 2>/dev/null || { echo "   선행 $id: 판정 기록 없음(${rev:0:7})" >&2; return 1; }
  git -C "$R" show "$rev:.ai/verification/$id.json" | "$LC_PY" -B -c "
import json, sys
o = json.loads(sys.stdin.buffer.read().decode('utf-8'))
want = ['V%d' % i for i in range(1, 11)]
ck = o.get('checks') or {}
v = {k: (c or {}).get('verdict') for k, c in ck.items()}
bad = []
if o.get('id') != sys.argv[1]: bad.append(('id', o.get('id')))
if sorted(ck, key=lambda k: int(k[1:]) if k[1:].isdigit() else 99) != want: bad.append(('checks', sorted(ck)))
if not set(v.values()) <= {'PASS', 'N/A'}: bad.append(('verdict', v))
if bad:
    sys.stderr.write('   선행 %s: 판정 기록이 병합 기준(V1~V10 전부 PASS·N/A, id 일치)에 맞지 않음 %r\n' % (sys.argv[1], bad)); sys.exit(1)
" "$id"
}

# m8: measured rev 단일 출처. <R> <파일> <grep BRE 앵커(백틱 안 7~40자 hex를 담는다)> -> 마지막 출현의 짧은 rev(문서 표기 그대로)를 출력.
#   출현 0이면 실패. 둘 이상이면 앞선 출현 rev가 전부 마지막 rev의 조상이어야 한다(아니면 '마지막 = 최신' 규약이 깨짐 -- 멈춤).
lc_meas_short() {
  local R=$1 f=$2 pat=$3 all last x lr
  all=$(grep -o -- "$pat" "$f" | sed -E 's/.*`([0-9a-f]{7,40})`.*/\1/') || { echo "[중단] measured rev 앵커가 $f에 없다: $pat" >&2; return 1; }
  [ -n "$all" ] || { echo "[중단] measured rev 앵커가 $f에 없다: $pat" >&2; return 1; }
  last=$(printf '%s\n' "$all" | tail -1)
  lr=$(git -C "$R" rev-parse --verify -q "$last^{commit}") || { echo "[중단] measured rev $last를 $R에서 찾지 못했다" >&2; return 1; }
  for x in $(printf '%s\n' "$all" | sed '$d'); do
    git -C "$R" merge-base --is-ancestor "$x" "$lr" 2>/dev/null \
      || { echo "[중단] $f의 measured rev 앵커가 여럿이고 앞선 $x가 마지막 $last의 조상이 아니다(마지막 = 최신 규약 위반)" >&2; return 1; }
  done
  [ "$(printf '%s\n' "$all" | wc -l | tr -d ' ')" = 1 ] || echo "   (measured rev 앵커 $(printf '%s\n' "$all" | wc -l | tr -d ' ')개 -- 마지막 $last 사용, 앞선 것은 전부 조상)" >&2
  printf '%s' "$last"
}

# 착수 조건 명령에서 선행 card id(판정 기록 경로 또는 card chk 인자)를 뽑는다. <명령 문자열> -> id 줄들
lc_pred_ids_of() {
  printf '%s\n' "$1" | grep -oE '\.ai/verification/[0-9]{8}-[a-z0-9-]+\.json|(^|[^A-Za-z_])chk [0-9]{8}-[a-z0-9-]+' \
    | sed -E 's#^\.ai/verification/##; s#\.json$##; s#^.*chk ##' | sort -u || true
}
