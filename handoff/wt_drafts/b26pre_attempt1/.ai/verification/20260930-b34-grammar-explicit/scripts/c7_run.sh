#!/usr/bin/env bash
# B34 순서 7 계약 7(analog-grammar 있음, base 대 M): c7_digest(14 진입점 x 9회로, seed 1·2), E-LIB, E-INST 두 회로.
# 같은 경로 C:/g299/eq에서 base -> M 순서로(출력 경로 차이 배제). 결과 C:/g299/out/.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
export TMP=C:/g299/tmp TEMP=C:/g299/tmp
B=7243f2846210c0dba62329acb77885f84a26ff76
M=c851e54aa6a4c330a3545eb75d477e961cd25d62
PY=C:/Python314/python.exe; O=C:/g299/out; E=C:/g299/eq
for tag in base m; do
  if [ $tag = base ]; then rev=$B; else rev=$M; fi
  git -C $E checkout -q -- . ; git -C $E clean -fdxq; git -C $E checkout -q --detach $rev
  echo "$tag HEAD $(git -C $E rev-parse HEAD) status $(git -C $E status --porcelain | wc -l)" >> $O/c7_status.txt
  for s in 1 2; do
    PYTHONHASHSEED=$s PYTHONDONTWRITEBYTECODE=1 $PY -P C:/g299/scripts/c7_digest.py $E $O/c7_${tag}_seed$s.json >> $O/c7_status.txt 2>&1
    echo "c7 $tag seed$s exit $?" >> $O/c7_status.txt
  done
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 $PY -P C:/g299/scripts/e_lib.py $E $O/elib_$tag.json > $O/elib_$tag.txt 2>&1
  echo "elib $tag exit $?" >> $O/c7_status.txt
  for cir in folded_cascode current_reuse_telescopic_ota; do
    bash C:/g299/scripts/einst.sh $E $tag $cir >> $O/c7_status.txt 2>&1
  done
done
git -C $E checkout -q -- . ; git -C $E clean -fdxq
echo "eq final status $(git -C $E status --porcelain | wc -l)" >> $O/c7_status.txt
echo DONE >> $O/c7_status.txt
