# V3~V7 base 판 도구(캐시), --root = 격리 복제본 C:/g394/iso(HEAD M), --base/--head 40자리
set -uo pipefail
C=C:/g394/gmid-gate-cache/863a037cc0d774bb984006ea39966c5e4dd741ab
B=863a037cc0d774bb984006ea39966c5e4dd741ab
T=3004096c81b839998518c14c16d3cd2d6ec6c9bf
M=0bb22782775fd759f9478aeae16e8202095d09a9
I=C:/g394/iso
O=C:/g394/out
mkdir -p C:/g394/tmp/tools
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g394/tmp/tools TEMP=C:/g394/tmp/tools TMPDIR=C:/g394/tmp/tools PYTHONPYCACHEPREFIX=C:/g394/pyc/tools
P=C:/Python314/python.exe
env -C $I $P -B $C/test_lint.py --root $I --interface-card $I/docs/02-design/specs/20261001-b26-backfill-interdig-final-audit.interface.md --base $B --head $T > $O/v4_test_lint.json 2> $O/v4_test_lint.err; echo "V4 rc=$?" > $O/tools_rc.txt
env -C $I $P -B $C/weakening_diff.py --root $I --base $B --head $T > $O/v5_wd_T.json 2> $O/v5_wd_T.err; echo "V5T rc=$?" >> $O/tools_rc.txt
env -C $I $P -B $C/weakening_diff.py --root $I --base $B --head $M > $O/v5_wd_M.json 2> $O/v5_wd_M.err; echo "V5M rc=$?" >> $O/tools_rc.txt
env -C $I $P -B $C/source_lint.py --root $I --base $B --head $M > $O/v6_source_lint.json 2> $O/v6_source_lint.err; echo "V6 rc=$?" >> $O/tools_rc.txt
env -C $I $P -B $C/reachability.py --root $I --base $B --head $M > $O/v7_reach.json 2> $O/v7_reach.err; echo "V7 rc=$?" >> $O/tools_rc.txt
env -C $I $P -B $C/mutate_changed.py --root $I --base $B --head $M --pytest-ini $C/pytest_gate.ini --python $P --gmid-phase=3 --gmid-strict= --out $O/v3.jsonl > $O/v3_stdout.txt 2> $O/v3_stderr.txt; echo "V3 rc=$?" >> $O/tools_rc.txt
cat $O/tools_rc.txt
echo "iso status: [$(git -C $I status --porcelain | tr '\n' ';')] HEAD $(git -C $I rev-parse HEAD)"
