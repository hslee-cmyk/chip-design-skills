# usage: bash einst.sh <label> <commit>   -- 전용 격리 복제본 C:/g394/einst_<label>에서 E-INST 두 회로
set -euo pipefail
LABEL=$1; REV=$2
W=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-audit
S=$W/.ai/verification/20261001-b26-backfill-interdig-final-audit/scripts/order7
D=C:/g394/einst_$LABEL
git clone -q --no-hardlinks --no-local -c core.autocrlf=false -c core.longpaths=true --no-checkout $W $D
git -C $D remote remove origin
test -z "$(git -C $D remote)"
git -C $D -c advice.detachedHead=false checkout -q --detach $REV
mkdir -p C:/g394/tmp/einst_$LABEL
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g394/tmp/einst_$LABEL TEMP=C:/g394/tmp/einst_$LABEL TMPDIR=C:/g394/tmp/einst_$LABEL
for k in current_reuse_telescopic_ota folded_cascode; do
  env -C $D PYTHONHASHSEED=0 PYTHONPYCACHEPREFIX=C:/g394/pyc/einst_$LABEL C:/Python314/python.exe -P $S/einst.py $D $k C:/g394/out/einst_${LABEL}_$k.json > C:/g394/out/einst_${LABEL}_$k.txt 2>&1 || echo "rc=$?" >> C:/g394/out/einst_${LABEL}_$k.txt
  cat C:/g394/out/einst_${LABEL}_$k.txt
done
echo "HEAD $(git -C $D rev-parse HEAD) status: $(git -C $D status --porcelain | tr '\n' ';')"
