#!/usr/bin/env bash
# 측정 전용: F1 판정기 r2 자기 점검 커밋(스크래치 C:/g250/a에서만).
set -eu
export TMP=C:/g250/tmp TEMP=C:/g250/tmp
R=/c/g250/a
if [ ! -d "$R/.git" ]; then
  git -c core.autocrlf=false clone -q --no-local /c/g250/c/r "$R"
  git -C "$R" remote remove origin
  git -C "$R" config core.hooksPath C:/g250/nohooks
fi
K=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_f12/out/att_r1
IDX=/c/g250/tmp/idx.mkatt
mk() { # parent path file msg
  rm -f "$IDX"
  GIT_INDEX_FILE="$IDX" git -C "$R" read-tree "$1"
  blob=$(git -C "$R" hash-object -w "$3")
  GIT_INDEX_FILE="$IDX" git -C "$R" update-index --add --cacheinfo "100644,$blob,$2"
  tree=$(GIT_INDEX_FILE="$IDX" git -C "$R" write-tree)
  rm -f "$IDX"
  git -C "$R" -c user.name=sim -c user.email=sim@x commit-tree "$tree" -p "$1" -m "$4"
}
A=skills/analog-gmid-design/assets/tests
OUT=/c/g250/revs.txt
: > "$OUT"
P0=$A/probes/zz_attack.py
echo "H BASE $(mk 0a82920 $P0 $K/base2.py hbase)" >> "$OUT"
for k in good h1 h2 h2b h3 h4 h5; do echo "H $k $(mk c10ee5f $P0 $K/$k.py h$k)" >> "$OUT"; done
for P in $A/probes/zz_rev.py $A/contracts/test_zz_rev.py; do
  tag=$(basename $P .py)
  echo "$tag BASE $(mk 0a82920 $P /c/g250/att/base_rev.py rbase)" >> "$OUT"
  for k in good_rev A1b A2 A10 A3; do echo "$tag $k $(mk c10ee5f $P /c/g250/att/$k.py r$k)" >> "$OUT"; done
done
cat "$OUT"
