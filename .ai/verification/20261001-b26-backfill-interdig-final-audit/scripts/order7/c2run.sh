set -euo pipefail
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-audit/.ai/verification/20261001-b26-backfill-interdig-final-audit/scripts/order7
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g394/tmp TEMP=C:/g394/tmp TMPDIR=C:/g394/tmp
for seed in 0 1; do
  for x in isob iso; do
    env -C C:/g394/$x PYTHONHASHSEED=$seed PYTHONPYCACHEPREFIX=C:/g394/pyc/c2_${x}_$seed C:/Python314/python.exe -P $S/contract2.py C:/g394/$x C:/g394/tmp/c2_${x}_$seed C:/g394/out/c2_${x}_s$seed.json > C:/g394/out/c2_${x}_s$seed.txt 2>&1
    echo "== $x seed $seed"; cat C:/g394/out/c2_${x}_s$seed.txt
  done
done
C:/Python314/python.exe -B $S/c2cmp.py C:/g394/out/c2_isob_s0.json C:/g394/out/c2_iso_s0.json C:/g394/out/c2_isob_s1.json C:/g394/out/c2_iso_s1.json > C:/g394/out/c2_cmp.txt 2>&1
cat C:/g394/out/c2_cmp.txt
