#!/usr/bin/env bash
# 잘못된 구현 변형마다 그 변형이 겨냥한 단계만 담은 측정 케이스(32v-<변형>)를 시제품 복제본에서 돌린다.
#   bash run_variants.sh <scratch C:/g<n>> <시제품 복제본 이름(p)> <출력 이름표> <변형:단계,단계> ...
# 결과: g1_kit/out/var_<이름표>.jsonl(변형마다 run_all 로그의 케이스 줄에 variant를 더해 append) + .txt
set -euo pipefail
S="$1"; C="$2"; L="$3"; shift 3
K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/g1_kit
PY=C:/Python314/python.exe
# (pre-r1g) 가드 C:/g* -> C:/g[0-9]*(setup_clones.sh·run_noop.sh와 같게 -- 검토 minor 1)
case "$S" in C:/g[0-9]*) ;; *) echo "scratch must be C:/g<n>"; exit 2;; esac
mkdir -p "$S/tmp_$L"
export TMP="$S/tmp_$L" TEMP="$S/tmp_$L" TMPDIR="$S/tmp_$L"
export PYTHONIOENCODING=utf-8
# (pre-dafe) 옛 G1_SCOPE=1·G1_SCOPE_DIR export는 뺐다 -- install_proto.py가 a17b8bd(card 35 병합본) 앵커라 범위 정책이 도구 안에 있고 G1_SCOPE는 무시된다.
# 자식 bash는 APPDATA·HOME·USERPROFILE을 잃는다 -> 없으면 pytest(사용자 site-packages)가 안 보여 V3 BaselineFailed(setup_clones.sh 머리 참조)
export HOME=C:/Users/HSLEE USERPROFILE='C:\Users\HSLEE' APPDATA='C:\Users\HSLEE\AppData\Roaming' LOCALAPPDATA='C:\Users\HSLEE\AppData\Local'
"$PY" -B -c "import pytest" || { echo "[중단] $PY에서 pytest를 import하지 못한다(APPDATA·사용자 site-packages 확인)"; exit 2; }
for spec in "$@"; do
  V="${spec%%:*}"; ST="${spec#*:}"
  "$PY" -B "$K/gen_attack32.py" "$S/$C" --scope "--only-stages=$ST" "--name=32v-$V-x" > /dev/null
  set +e
  G1_VARIANT="$V" "$PY" -B "$S/$C/tools/gates/redteam/run_all.py" --phase 0.5 --mode direct --only "32v-$V-x" --repo "$S/$C" >> "$K/out/var_$L.txt" 2>&1
  set -e
  LOG=$(ls -t "$S/$C/tools/gates/redteam/logs/"*-direct.jsonl | head -1)
  "$PY" -B -c "import json,sys;[print(json.dumps(dict(json.loads(l),variant=sys.argv[2]),ensure_ascii=False)) for l in open(sys.argv[1],encoding='utf-8') if '\"case\"' in l]" "$LOG" "$V" >> "$K/out/var_$L.jsonl"
  echo "variant $V done" >> "$K/out/var_$L.txt"
done
