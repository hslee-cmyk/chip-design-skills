#!/usr/bin/env bash
# D0b 계약 test 모양 시제품을 복제본의 커밋 하나에서 돌린다(측정 전용).
#   bash run_proto_test.sh <복제본 루트> <rev> <출력 txt>
set -u
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
ROOT=$1; REV=$2; OUT=$3
case "$ROOT" in C:/g162/*) ;; *) echo "scratch must be under C:/g162"; exit 2;; esac
K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_d0b
git -C "$ROOT" checkout -q --detach "$REV"
mkdir -p C:/g162/tmp/pt && cp "$K/test_p3_registry_dest.proto.py" C:/g162/tmp/pt/test_p3rd_proto.py
P3RD_ROOT=$ROOT P3RD_TOOL=C:/g162/tmp/move_plan_proto.py PYTHONIOENCODING=utf-8 PYTHONPYCACHEPREFIX=C:/g162/tmp/pyc \
  C:/Python314/python.exe -B -m pytest -q -p no:cacheprovider --rootdir=C:/g162/tmp -c /dev/null C:/g162/tmp/pt/test_p3rd_proto.py > "$OUT" 2>&1
echo "proto test rev=$REV exit=$?"
tail -12 "$OUT"
