set -euo pipefail
C=C:/g393/gmid-gate-cache/863a037cc0d774bb984006ea39966c5e4dd741ab
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g393/tmp TEMP=C:/g393/tmp TMPDIR=C:/g393/tmp PYTHONPYCACHEPREFIX=C:/g393/pyc_v3
set +e
C:/Python314/python.exe $C/mutate_changed.py --root C:/g393/iso --base 863a037cc0d774bb984006ea39966c5e4dd741ab --head 3004096c81b839998518c14c16d3cd2d6ec6c9bf --pytest-ini $C/pytest_gate.ini --python C:/Python314/python.exe --gmid-phase 3 --gmid-strict= --out C:/g393/out/v3_base_T.json > C:/g393/out/v3_base_T.txt 2>&1
echo "rc=$?" >> C:/g393/out/v3_base_T.txt
set -e
cat C:/g393/out/v3_base_T.txt
echo ---
cat C:/g393/out/v3_base_T.json 2>/dev/null || true
git -C C:/g393/iso status --porcelain
git -C C:/g393/iso rev-parse HEAD
