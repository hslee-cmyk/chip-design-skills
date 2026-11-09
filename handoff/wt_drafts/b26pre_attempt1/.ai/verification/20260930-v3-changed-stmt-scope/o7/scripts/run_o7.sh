#!/usr/bin/env bash
# 20260930-v3-changed-stmt-scope 순서 7 (auditor): 참고 도구(V3~V7) -- base 판 게이트 코드(4a286f0 git cat-file 추출), 병합본 격리 복제본 C:/g259/iso
export APPDATA="C:/Users/HSLEE/AppData/Roaming" PYTHONDONTWRITEBYTECODE=1 TEMP=C:/g259/tmp/o7 TMP=C:/g259/tmp/o7 TMPDIR=C:/g259/tmp/o7
mkdir -p C:/g259/tmp/o7
C=C:/g259/gmid-gate-cache/4a286f0fad4f9beafd26647e1f95a89086e07919
PY=C:/Python314/python.exe
R=C:/g259/iso
O=C:/g259/out
B=4a286f0fad4f9beafd26647e1f95a89086e07919
M=a17b8bd3cc746518f9297d905bedd4f631c26e47
T=0ef74303697c5fa555acbdc21c7ed522252cd1b2
for t in mutate_changed weakening_diff source_lint reachability; do
  extra=""
  [ $t = mutate_changed ] && extra="--pytest-ini $C/pytest_gate.ini --out $O/v3_ref.jsonl --gmid-phase=0.5 --gmid-strict="
  (cd $R && $PY $C/$t.py --root $R --base $B --head $M $extra > $O/ref_$t.txt 2>&1)
  echo "ref_$t exit $?" >> $O/status.txt
done
(cd $R && $PY $C/test_lint.py --root $R --base $B --head $M --module-dir tools/gates --subject mutate_changed:main --subject mutate_changed:_replace_def > $O/ref_test_lint.txt 2>&1)
echo "ref_test_lint exit $?" >> $O/status.txt
(cd $R && $PY $C/weakening_diff.py --root $R --base $B --head $T > $O/ref_weakening_diff_T.txt 2>&1)
echo "ref_weakening_diff_T exit $?" >> $O/status.txt
