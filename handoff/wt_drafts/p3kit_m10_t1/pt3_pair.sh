#!/usr/bin/env bash
# measure only: PT3 (design 30 §10) at labelled revs in worktree C:/g323/pt. args: <label>=<rev> ...
R=C:/g323/r; PT=C:/g323/pt; GC=C:/g323/cache/tools/gates; O=C:/g323/out
[ -d $PT ] || git -C $R worktree add -q --detach $PT HEAD
for lr in "$@"; do
  L=${lr%%=*}; V=${lr#*=}
  git -C $PT checkout -q --detach "$V"; git -C $PT clean -qfdx
  bash C:/g323/kit/pt3.sh $PT "$L" $GC $O
  echo "$L $V $(tail -2 $O/$L.pt3.txt | tr '\n' ' ')" >> $O/pt3_pair.txt
done
echo finished >> $O/pt3_pair.txt
