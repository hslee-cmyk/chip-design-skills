#!/usr/bin/env bash
# 측정 전용: 판정기 r2(f12_equiv.py)·r1(f12_equiv.pre-r2.bak)로 공격 커밋 판정, 결과를 파일마다 쓴다.
set -u
export TMP=C:/g250/tmp TEMP=C:/g250/tmp PYTHONIOENCODING=utf-8
K=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_f12
R=C:/g250/a
A=skills/analog-gmid-design/assets/tests
mkdir -p /c/g250/attout
job() { # judge tag k base head path
  local j=$1 tag=$2 k=$3 b=$4 h=$5 p=$6 f
  if [ "$j" = r2 ]; then f=$K/f12_equiv.py; else f=$K/f12_equiv.pre-r2.bak; fi
  C:/Python314/python.exe -B "$f" $R "$b" "$h" C:/g250/attout/$j.$tag.$k.json --only "$p" > /c/g250/attout/$j.$tag.$k.txt 2>&1
}
export -f job
export K R A
{
while read -r tag k rev; do
  case $tag in
    H) p=$A/probes/zz_attack.py ;;
    zz_rev) p=$A/probes/zz_rev.py ;;
    test_zz_rev) p=$A/contracts/test_zz_rev.py ;;
  esac
  [ "$k" = BASE ] && { eval "B_$tag=$rev"; continue; }
  eval "b=\$B_$tag"
  echo "r2 $tag $k $b $rev $p"
  [ "$tag" != H ] && echo "r1 $tag $k $b $rev $p"
done < /c/g250/revs.txt
} | xargs -P 4 -L 1 bash -c 'job "$@"' _
echo DONE > /c/g250/attout/DONE
