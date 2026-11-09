#!/usr/bin/env bash
# post_p10b_runbook.sh 사전 시험용 모래상자(C:/g101) 만들기 -- 실제 저장소·gate는 읽기만 한다.
#   r        = 메인 저장소 복제본(--no-hardlinks --no-local), P10b 3커밋(4294048까지) ff + 합성 audit 커밋
#   gate.git = r에서 뜬 bare 사본(가짜 gate). pre-receive·gate-runner·accept-log를 실제 gate와 같은 모양으로 설치
# 합성 audit 커밋은 tools/gates/gate_config.json의 gate_path·workspace_path와 tools/gates/gate/pre-receive의 실행 경로만
# 모래상자 경로로 바꾼다(EL3 commit hook과 EL4 pre-receive가 실제 gate 대신 모래상자 gate를 보게 하려고).
# 사용: bash post_p10b_dryrun_setup.sh   (C:/g101이 없을 때만)
set -euo pipefail
export HOME=/c/Users/HSLEE   # MSYS2 자식 bash는 HOME=/home/HSLEE라 전역 user.name/email을 못 읽는다(실측)
test -n "$(git config --get user.email)"
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
S=/c/g101
PY=/c/Python314/python.exe
ID=20260930-df23-registry-record

test ! -e "$S/r"
test ! -e "$S/gate.git"
mkdir -p "$S"
git clone -q --no-hardlinks --no-local --no-checkout "$R" "$S/r"
git -C "$S/r" config core.longpaths true
git -C "$S/r" checkout -q master
test "$(git -C "$S/r" rev-parse HEAD)" = a796468889741bb7eb8da121ffefb0589cb2b769
# P10b 병합본(4294048)까지 ff -- push 직후 gate master 모양 흉내. role/audit 브랜치 머리(36a6ec8, 1차 판정 V3·V4 FAIL)는
# 쓰지 않는다 -- 실제 push는 재시도 뒤라 sha가 달라지므로 runbook은 sha가 아니라 커밋 제목으로 P10b audit를 찾는다.
git -C "$S/r" merge -q --ff-only 429404809ad09b9bef303df20087c998caa9d345
test "$(git -C "$S/r" rev-parse HEAD)" = 429404809ad09b9bef303df20087c998caa9d345

# 합성 audit 커밋(모래상자 gate 경로 + pre-receive 실행 경로만 바꿈)
"$PY" -B - "$S/r" <<'EOF'
import json, sys, os
r = sys.argv[1]
p = os.path.join(r, "tools", "gates", "gate_config.json")
raw = open(p, "rb").read()
crlf = b"\r\n" in raw
cfg = json.loads(raw.decode("utf-8"))
cfg["gate_path"] = "C:/g101/gate.git"
cfg["workspace_path"] = "C:/g101/r"
out = json.dumps(cfg, ensure_ascii=False, indent=2) + "\n"
if crlf:
    out = out.replace("\n", "\r\n")
open(p, "wb").write(out.encode("utf-8"))
q = os.path.join(r, "tools", "gates", "gate", "pre-receive")
b = open(q, "rb").read()
old = b"C:/Users/HSLEE/Documents/Todoc/fpga/gmid-gate.git/gate-runner.py"
assert b.count(old) == 1
open(q, "wb").write(b.replace(old, b"C:/g101/gate.git/gate-runner.py"))
EOF
git -C "$S/r" add -- tools/gates/gate_config.json tools/gates/gate/pre-receive
git -C "$S/r" commit -q -m "audit: $ID 판정 기록(DRY-RUN 합성 -- 모래상자 gate 경로만 바꿈, 실제 판정 아님)" --trailer "Role: audit" --trailer "Change-Id: $ID"
SYN=$(git -C "$S/r" rev-parse HEAD)

# 가짜 gate
git clone -q --bare --no-hardlinks --no-local "$S/r" "$S/gate.git"
rm -rf "$S/gate.git/hooks"
mkdir -p "$S/gate.git/hooks"
git -C "$S/r" show "HEAD:tools/gates/gate/pre-receive" > "$S/gate.git/hooks/pre-receive"
git -C "$S/r" show "HEAD:tools/gates/gate/gate-runner.py" > "$S/gate.git/gate-runner.py"
BASE=$("$PY" -B -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8'))['baseline_commit'])" "$S/r/tools/gates/gate_config.json")
printf '%s %s 2026-10-01T00:00:00\n%s %s 2026-10-01T00:00:01\n' "$BASE" "$BASE" "$BASE" "$SYN" > "$S/gate.git/gmid-accept-log"

# 복제본 remote·hook 배선(실제 저장소와 같은 모양)
git -C "$S/r" remote remove origin
git -C "$S/r" remote add gate "C:/g101/gate.git"
git -C "$S/r" fetch -q gate
git -C "$S/r" branch -q --set-upstream-to=gate/master master
git -C "$S/r" config core.hooksPath "C:/g101/r/.githooks"
# EL3 무결성 행 5·6은 설치된 역할 hook(.claude/hooks, 추적 밖 파일)을 본다 -- 실제 체크아웃에서 읽어 복사
mkdir -p "$S/r/.claude/hooks"
cp "$R/.claude/hooks/"role_*.py "$S/r/.claude/hooks/"
cp "$R/.claude/settings.json" "$S/r/.claude/settings.json"
test "$(git -C "$S/r" rev-parse gate/master)" = "$SYN"
echo "모래상자 준비: r HEAD = gate master = $SYN (P10b 4294048 + 합성 audit)"
