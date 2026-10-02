#!/usr/bin/env bash
# 20260930-v3-exempt-binding 순서 7 (auditor): 병합본 격리 복제본 C:/g186/isom, base 판 게이트 코드 C:/g186/gmid-gate-cache/<dd60db6>(git cat-file 추출)
export APPDATA="C:/Users/HSLEE/AppData/Roaming" PYTHONDONTWRITEBYTECODE=1
C=C:/g186/gmid-gate-cache/dd60db6515b6fe80ab16349835c19aa75d4f292f
PY=C:/Python314/python.exe
R=C:/g186/isom
O=C:/g186/o7
B=dd60db6515b6fe80ab16349835c19aa75d4f292f
M=5a602d43e67e6b0c8c45cb028c1f92473add8601
T=8b1f9293681df57e79522c8a2262342ef07f87b3
case "$1" in
tools)
  for t in mutate_changed weakening_diff source_lint reachability; do
    extra=""
    [ $t = mutate_changed ] && extra="--pytest-ini $C/pytest_gate.ini --out $O/v3_ref.jsonl --gmid-phase=0.5 --gmid-strict="
    (cd $R && $PY $C/$t.py --root $R --base $B --head $M $extra > $O/ref_$t.txt 2>&1)
    echo "ref_$t exit $?" >> $O/status.txt
  done
  (cd $R && $PY $C/test_lint.py --root $R --base $B --head $M --module-dir tools/gates --subject mutate_changed:main --subject mutate_changed:bind_hash --subject mutate_changed:approved_index --subject mutate_changed:exempt_decision > $O/ref_test_lint.txt 2>&1)
  echo "ref_test_lint exit $?" >> $O/status.txt
  (cd $R && $PY $C/weakening_diff.py --root $R --base $B --head $T > $O/ref_weakening_diff_T.txt 2>&1)
  echo "ref_weakening_diff_T exit $?" >> $O/status.txt ;;
df36)
  mkdir -p $O/df36tmp
  rm -f $O/df36_v3.jsonl
  s=$(date +%s)
  (cd $R && TEMP=$O/df36tmp TMP=$O/df36tmp TMPDIR=$O/df36tmp $PY $R/tools/gates/mutate_changed.py --root $R --base 070cf6937e2841bdd3b4781eb9b8ba5bba9cc606 --head b29be01 --pytest-ini $C/pytest_gate.ini --gmid-phase=2 --gmid-strict= --out $O/df36_v3.jsonl > $O/df36_v3.txt 2>&1)
  echo "df36 exit $? $(( $(date +%s)-s ))s left=$(ls -A $O/df36tmp | wc -l)" >> $O/status.txt ;;
esac
