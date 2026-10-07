set -euo pipefail
export PYTHONPYCACHEPREFIX=C:/g393/pyc_mk
T=3004096c81b839998518c14c16d3cd2d6ec6c9bf
W=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-audit
SR=skills/analog-gmid-design/assets/sizing_recipe.py
mk() {  # name lines
  D=C:/g393/var_$1
  git clone -q --no-hardlinks --no-local -c core.autocrlf=false -c core.longpaths=true --no-checkout $W $D
  git -C $D remote remove origin
  test -z "$(git -C $D remote)"
  git -C $D checkout -q --detach $T
  C:/Python314/python.exe C:/g393/s/mkvar.py $D/$SR $2
  git -C $D diff --stat
}
mk i 11799
mk ii 11878
mk iii 11792,11799,11878
