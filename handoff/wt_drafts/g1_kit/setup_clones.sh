#!/usr/bin/env bash
# G1 키트 측정 복제본: $1 = scratch(C:/g<n>), $2 = 원본 저장소(읽기만), $3 = 체크아웃할 rev(선택, 예: gate master sha -- 없으면 원본 HEAD).
# base 복제본 b, 시제품 복제본 p(install_proto.py + 공격 32 측정판).
# 실제 저장소에는 쓰지 않는다(clone --no-local, clone -c core.autocrlf=false -- 복제본 config에 남는다, origin 제거). 훅: 로컬 clone은 원본의 core.hooksPath를 가져오지 않는다 --
# (pre-dafe) 옛 'config core.hooksPath <빈 폴더>' 쓰기 대신 복제본에 core.hooksPath 설정이 없고 .git/hooks에 *.sample 밖 파일이 없음을 단정한다.
# (pre-dafe) MSYS2 자식 bash는 APPDATA·HOME·USERPROFILE을 잃는다 -> Python 사용자 site-packages(pytest)가 안 보여 V3 기준 실행이
#   'No module named pytest'(exit 1) -> BaselineFailed(exit 2)가 됐다(옛 noop 기준선 28·31·34·35·v3_survivor FAIL의 원인, 2026-10-06 실측).
#   그래서 다시 export하고 pytest import를 단정한다(run_noop.sh·run_attack32.sh·run_variants.sh도 같다).
# (pre-r1g) 옛 'git -c core.autocrlf=false clone'은 그 설정을 복제본 config에 남기지 않는다 -- 이 머신은 C:/Program Files/Git/etc/gitconfig에
#   core.autocrlf=true라 셋째 인자 REV의 checkout이 바뀐 파일을 CRLF로 꺼냈다(검토 review_g1_dafe S1 실측: 계획서 CRLF 1,191줄). 그래서 'git clone -c core.autocrlf=false'로
#   복제본 config에 남기고, REV checkout 뒤 core.autocrlf = false와 계획서 CRLF 0줄을 단정한다. 이미 있는 복제본은 재사용하되 REV(없으면 원본 HEAD)에 있는지 단정한다.
set -euo pipefail
S="$1"; SRC="$2"; REV="${3:-}"
K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/g1_kit
PY=C:/Python314/python.exe
case "$S" in C:/g[0-9]*) ;; *) echo "scratch must be C:/g<n>"; exit 2;; esac
export HOME=C:/Users/HSLEE USERPROFILE='C:\Users\HSLEE' APPDATA='C:\Users\HSLEE\AppData\Roaming' LOCALAPPDATA='C:\Users\HSLEE\AppData\Local'
"$PY" -B -c "import pytest" || { echo "[중단] $PY에서 pytest를 import하지 못한다(APPDATA·사용자 site-packages 확인)"; exit 2; }
mkdir -p "$S"
WANT=$(git -C "$SRC" rev-parse --verify "${REV:-HEAD}^{commit}")
PLAN=docs/01-plan/features/gain-budget-gmid-sizing.plan.md
for n in b p; do
  if [ -e "$S/$n" ]; then
    # 재사용: 원하는 rev에 있어야 한다(옛 판은 확인 없이 continue -- 검토 minor 2)
    test "$(git -C "$S/$n" rev-parse HEAD)" = "$WANT" || { echo "[중단] 이미 있는 $S/$n HEAD $(git -C "$S/$n" rev-parse --short HEAD) != ${REV:-원본 HEAD} ${WANT:0:7} -- 새 scratch를 쓴다"; exit 2; }
  else
    git clone -c core.autocrlf=false -q --no-hardlinks --no-local "$SRC" "$S/$n"
    git -C "$S/$n" remote remove origin
    if [ -n "$REV" ]; then git -C "$S/$n" checkout -q --detach "$REV"; fi
    test "$(git -C "$S/$n" rev-parse HEAD)" = "$WANT"
  fi
  test "$(git -C "$S/$n" config --get core.autocrlf)" = false || { echo "[중단] $S/$n core.autocrlf가 false가 아니다"; exit 2; }
  "$PY" -B -c "import sys;n=open(sys.argv[1],'rb').read().count(b'\r\n');sys.exit('[중단] %s CRLF %d줄' % (sys.argv[1], n) if n else 0)" "$S/$n/$PLAN"
  test -z "$(git -C "$S/$n" config --get core.hooksPath || true)"
  test -z "$(ls "$S/$n/.git/hooks" | grep -v '\.sample$' || true)"
done
echo "b $(git -C "$S/b" rev-parse --short HEAD)  p $(git -C "$S/p" rev-parse --short HEAD)"
"$PY" -B "$K/install_proto.py" "$S/p"
"$PY" -B "$K/gen_attack32.py" "$S/b"
"$PY" -B "$K/gen_attack32.py" "$S/p" --scope
git -C "$S/p" diff --stat
"$PY" -B -c "import ast,sys;[ast.parse(open(f,encoding='utf-8').read()) for f in sys.argv[1:]];print('parse ok')" \
  "$S/p/tools/gates/reachability.py" "$S/p/tools/gates/mutate_changed.py" "$S/p/tools/gates/source_lint.py" "$S/p/tools/gates/redteam/lib/rt.py"
