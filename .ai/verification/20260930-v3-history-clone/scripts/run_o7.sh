#!/usr/bin/env bash
# B28 순서 7 (auditor): 병합본 격리 복제본 C:/g17/isom, base 판 게이트 코드 C:/g17/gmid-gate-cache/<cd64170>(git cat-file 추출)
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
C=C:/g17/gmid-gate-cache/cd6417026696091fd0ce02603a11a3729af3147e
PY=C:/Python314/python.exe
R=C:/g17/isom
O=C:/g17/o7
B=cd6417026696091fd0ce02603a11a3729af3147e
M=2b41e79a44900797ea799c7c0a2c983dfc4c889f
ID=20260930-v3-history-clone
case "$1" in
strict)
  V1="PYTHONPYCACHEPREFIX=$O/pyc_v1 PYTHONPATH=$C \$PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R $R/skills/analog-gmid-design/assets/tests --gmid-phase=0.5 --gmid-strict= -rA"
  PYTHONPYCACHEPREFIX=$O/pyc_s PYTHONPATH=$C $PY -P C:/g17/iso/.ai/verification/20260930-df36-instance-relpath/scripts/strict_check.py $R $B $ID "$V1" > $O/strict.txt 2>&1
  echo "strict exit $?" >> $O/status.txt ;;
v1)
  rm -rf $O/pyc_v1; mkdir -p $O/pyc_v1
  s=$(date +%s)
  (cd $R && PYTHONPYCACHEPREFIX=$O/pyc_v1 PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R $R/skills/analog-gmid-design/assets/tests --gmid-phase=0.5 --gmid-strict= -rA > $O/v1.txt 2>&1)
  echo "v1 exit $? $(( $(date +%s)-s ))s" >> $O/status.txt ;;
redteam)
  mkdir -p C:/g17/tmpm
  (cd $R && TEMP=C:/g17/tmpm TMP=C:/g17/tmpm PYTHONDONTWRITEBYTECODE=1 $PY tools/gates/redteam/run_all.py --phase 0.5 --mode direct --repo $R > $O/rt_full.txt 2>&1)
  echo "rt_full exit $? $(date -Iseconds)" >> $O/status.txt
  (cd $R && TEMP=C:/g17/tmpm TMP=C:/g17/tmpm PYTHONDONTWRITEBYTECODE=1 $PY tools/gates/redteam/run_all.py --cases 0.5 --mode direct --repo $R > $O/rt_cases.txt 2>&1)
  echo "rt_cases exit $? $(date -Iseconds)" >> $O/status.txt ;;
tools)
  for t in mutate_changed weakening_diff source_lint reachability; do
    extra=""
    [ $t = mutate_changed ] && extra="--pytest-ini $C/pytest_gate.ini --out $O/v3_ref.jsonl --gmid-phase=0.5 --gmid-strict="
    (cd $R && PYTHONDONTWRITEBYTECODE=1 $PY $C/$t.py --root $R --base $B --head $M $extra > $O/ref_$t.txt 2>&1)
    echo "ref_$t exit $?" >> $O/status.txt
  done
  (cd $R && PYTHONDONTWRITEBYTECODE=1 $PY $C/test_lint.py --root $R --base $B --head $M --module-dir tools/gates --subject mutate_changed:main --subject mutate_changed:make_clone --subject mutate_changed:_run_git --subject mutate_changed:_rmtree_force > $O/ref_test_lint.txt 2>&1)
  echo "ref_test_lint exit $?" >> $O/status.txt
  (cd $R && PYTHONDONTWRITEBYTECODE=1 $PY $C/weakening_diff.py --root $R --base $B --head b93c1e4a9e2f5681670ed415a2c5782c0bf15c3d > $O/ref_weakening_diff_T.txt 2>&1)
  echo "ref_weakening_diff_T exit $?" >> $O/status.txt ;;
probes)
  MT=$R/tools/gates/mutate_changed.py
  PYTHONDONTWRITEBYTECODE=1 $PY C:/g17/probe/c1_head.py $MT $C/pytest_gate.ini $O/c1_m.json > $O/c1_m.txt 2>&1; echo "c1 exit $?" >> $O/status.txt
  PYTHONDONTWRITEBYTECODE=1 $PY C:/g17/probe/c3_mixed.py $MT $C/pytest_gate.ini $O/c3_m.json > $O/c3_m.txt 2>&1; echo "c3 exit $?" >> $O/status.txt
  PYTHONDONTWRITEBYTECODE=1 $PY C:/g17/probe/c4_clonefail.py $MT $C/pytest_gate.ini $O/c4_m.json > $O/c4_m.txt 2>&1; echo "c4 exit $?" >> $O/status.txt ;;
df36)
  mkdir -p $O/df36tmp
  rm -f $O/df36_v3.jsonl
  s=$(date +%s)
  (cd $R && TEMP=$O/df36tmp TMP=$O/df36tmp TMPDIR=$O/df36tmp PYTHONDONTWRITEBYTECODE=1 $PY $R/tools/gates/mutate_changed.py --root $R --base 070cf6937e2841bdd3b4781eb9b8ba5bba9cc606 --head b29be01 --pytest-ini $C/pytest_gate.ini --gmid-phase=2 --gmid-strict= --out $O/df36_v3.jsonl > $O/df36_v3.txt 2>&1)
  echo "df36 exit $? $(( $(date +%s)-s ))s left=$(ls -A $O/df36tmp | wc -l)" >> $O/status.txt ;;
esac
