#!/usr/bin/bash
# 순서 3 준비: 실제 저장소 상태 기록, 격리 복제본 2개(T1, B1), base 판 게이트 코드 캐시 추출·대조, freeze 확인
set -euo pipefail
A=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-rail-accessor-set-audit
R=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
GATE=C:/Users/HSLEE/Documents/Todoc/fpga/gmid-gate.git
B1=6df4bd7fd9920e752da4b16bff9b0513caf78362
T1=c247a7697fad8f4695a89d6c9fd0683b900e86fd
O=$A/.ai/verification/20260930-b26-rail-accessor-set/out
S=C:/g412
mkdir -p $O
state() {
  echo "HEAD $(git -C $R rev-parse HEAD)"
  echo "status_md5 $(git -C $R status --porcelain | md5sum | cut -d' ' -f1)"
  echo "reflog_lines $(git -C $R reflog | wc -l)"
  echo "refs_md5 $(git -C $R for-each-ref | md5sum | cut -d' ' -f1)"
}
state > $O/repo_state_start.txt
echo "gate_master $(git -C $GATE rev-parse refs/heads/master)" > $O/gate_master.txt
test "$(git -C $GATE rev-parse refs/heads/master)" = "$B1"
test ! -e $S/iso
mkdir -p $S/tmp $S/pycache $S/gmid-gate-cache/$B1
git clone --no-hardlinks --no-local -c core.autocrlf=false -c core.longpaths=true --no-checkout $A $S/iso
git -C $S/iso remote remove origin
test -z "$(git -C $S/iso remote)"
git -C $S/iso checkout --detach $T1
git clone --no-hardlinks --no-local -c core.autocrlf=false -c core.longpaths=true --no-checkout $A $S/isob
git -C $S/isob remote remove origin
test -z "$(git -C $S/isob remote)"
git -C $S/isob checkout --detach $B1
# base 판 게이트 코드 추출 + 오케스트레이터 캐시와 대조
OC=$(git -C $A rev-parse --git-common-dir)/gmid-gate-cache/$B1
: > $O/cache_cmp.txt
for f in $(git -C $A ls-tree --name-only $B1 tools/gates/); do
  t=$(git -C $A cat-file -t $B1:$f)
  [ "$t" = blob ] || continue
  b=$(basename $f)
  git -C $A cat-file blob $B1:$f > $S/gmid-gate-cache/$B1/$b
  if [ -e $OC/$b ]; then
    if cmp -s $S/gmid-gate-cache/$B1/$b $OC/$b; then echo "same $b" >> $O/cache_cmp.txt; else echo "DIFF $b" >> $O/cache_cmp.txt; fi
  else echo "absent_in_orch_cache $b" >> $O/cache_cmp.txt; fi
done
ls $OC >> $O/cache_cmp.txt 2>&1 || true
# freeze
{
  echo "audit_wt_HEAD $(git -C $A rev-parse HEAD)"
  echo "role_test_tip $(git -C $A rev-parse refs/heads/role/test/20260930-b26-rail-accessor-set)"
  echo "iso_HEAD $(git -C $S/iso rev-parse HEAD)"
  echo "-- log B1..T1 (%H %P)"
  git -C $S/iso log --format='%H %P' $B1..$T1
  echo "-- first-parent chain"
  git -C $S/iso rev-list --first-parent $B1..$T1
  echo "-- merges"
  git -C $S/iso rev-list --merges $B1..$T1 | wc -l
  echo "-- is B1 ancestor"
  git -C $S/iso merge-base --is-ancestor $B1 $T1 && echo yes
  for c in $(git -C $S/iso rev-list --reverse $B1..$T1); do
    echo "== trailers $c"
    git -C $S/iso log -1 --format=%B $c | git -C $S/iso interpret-trailers --parse
  done
  echo "-- diff --name-only B1 T1"
  git -C $S/iso diff --name-only $B1 $T1
  echo "-- diff --raw B1 T1"
  git -C $S/iso diff --raw --no-abbrev $B1 $T1
} > $O/freeze.txt
echo done
