set -euo pipefail
W=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-audit
B=863a037cc0d774bb984006ea39966c5e4dd741ab
C=C:/g393/gmid-gate-cache/$B
OC=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/.git/gmid-gate-cache/$B
mkdir -p $C
for f in $(git -C $W ls-tree --name-only $B tools/gates/ | grep -E '\.(py|ini|json|txt)$'); do
  n=$(basename $f)
  git -C $W cat-file blob $B:$f > $C/$n
  if [ -e $OC/$n ]; then cmp $C/$n $OC/$n && echo "same $n"; else echo "missing-in-orch $n"; fi
done
echo "--- orch cache listing"
ls $OC
