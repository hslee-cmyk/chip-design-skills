set -euo pipefail
for v in i ii iii fix; do
  for s in 0 1; do
    D=C:/g393/var_$v
    bash C:/g393/s/run.sh $D var_${v}_s$s $s $D/skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py $D/skills/analog-gmid-design/assets/tests/unit/test_selftest_sizing_recipe.py
  done
done
