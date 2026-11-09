set -euo pipefail
R=/c/g136/repo
git -C $R checkout -q -f sim-b34
git -C $R reset -q --hard 16b94f1
cp /c/g136/proto/test_b34_grammar_explicit.py $R/skills/analog-gmid-design/assets/tests/contracts/
git -C $R add skills/analog-gmid-design/assets/tests/contracts/test_b34_grammar_explicit.py
git -C $R -c user.name=sim -c user.email=sim@x commit -q -m "sim: proto test T"
git -C $R branch -f sim-T HEAD
PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -B /c/g136/mk_head.py
git -C $R add -A skills
git -C $R -c user.name=sim -c user.email=sim@x commit -q -m "sim: head K"
git -C $R branch -f sim-K HEAD
git -C $R log --oneline -3
