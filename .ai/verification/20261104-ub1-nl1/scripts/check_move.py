"""A-105 이동 동작 변경 0: 옛(base3) conductance_matrix·_gamma 소스와 새 소스 AST 비교, 같은 회로 입력 비트 비교(옛 함수는 옛 소스를 exec). pencil 행 교체 등가 비트 비교. 결과 stdout + 파일."""
import ast
import json
import pathlib
import sys

import numpy as np

R = pathlib.Path(sys.argv[1])
head = R / "iso3/skills/analog-gmid-design"
base = R / "base3/skills/analog-gmid-design"
sys.path.insert(0, str(head))
out = {}


def fn(path, name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            for n in ast.walk(node):
                if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                    n.value.value = ""
            return ast.dump(node), node
    raise KeyError(name)


old_p, new_p = base / "gmid_engine/metrics/_helpers_nodal.py", head / "gmid_engine/metrics/ss_nodal.py"
for name in ("conductance_matrix", "_gamma"):
    a, _ = fn(old_p, name)
    b, _ = fn(new_p, name)
    out["ast_same:" + name] = a == b

from gmid_engine.metrics import MosSmallSignal, Resistor, SmallSignalCircuit
from gmid_engine.metrics._helpers_dc import limit_matrix
import importlib
SN = importlib.import_module("gmid_engine.metrics.ss_nodal")
from gmid_engine.metrics.stamp_mos import mos_stamps
from gmid_engine.metrics.stamp_two_terminal import two_terminal_stamps
ns = {"numpy": np, "sys": sys, "mos_stamps": mos_stamps, "two_terminal_stamps": two_terminal_stamps}
src = old_p.read_text(encoding="utf-8")
tree = ast.parse(src)
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in ("conductance_matrix", "_gamma"):
        exec(compile(ast.Module([node], []), "old", "exec"), ns)
rng = np.random.default_rng(1)
same = 0
N = 200
for _ in range(N):
    n = int(rng.integers(3, 9))
    mos = [MosSmallSignal(*(int(x) for x in rng.integers(0, n, 4)), *(float(x) for x in rng.random(3) * 1e-3), label="m%d" % k) for k in range(5)]
    res = [Resistor(int(a), int((a + 1 + rng.integers(0, n - 1)) % n), float(1e3 + rng.random() * 1e4), label="r%d" % k) for k, a in enumerate(rng.integers(0, n, 3))]
    ck = SmallSignalCircuit(mos=tuple(mos), resistors=tuple(res))
    g0, b0 = ns["conductance_matrix"](ck, n, bound=True)
    g1, b1 = SN.conductance_matrix(ck, n, bound=True)
    same += g0.tobytes() == g1.tobytes() and b0.tobytes() == b1.tobytes()
out["conductance_bit_same"] = [same, N]
# pencil 행 교체 등가
same = 0
for _ in range(N):
    n = int(rng.integers(2, 10))
    a0, e0 = rng.random((n, n)), rng.random((n, n))
    charge = sorted(set(int(x) for x in rng.integers(0, n, int(rng.integers(0, n)))))
    a_old, e_old = a0.copy(), e0.copy()
    a_old[charge, :] = e_old[charge, :]
    e_old[charge, :] = 0.0
    a_new, e_new = limit_matrix(a0, e0, charge), limit_matrix(e0, np.zeros_like(e0), charge)
    same += a_old.tobytes() == a_new.tobytes() and e_old.tobytes() == e_new.tobytes()
out["pencil_bit_same"] = [same, N]
# 전하 없는 계 c 무관
HN = importlib.import_module("gmid_engine.metrics._helpers_nodal")
same = 0
for _ in range(N):
    n = 5
    g = rng.random((n, n)) * 1e-3
    c1, c2 = np.zeros((n, n)), rng.random((n, n)) * 1e-12
    f1, f2 = HN.nodal_factor(g, {0}, c=c1), HN.nodal_factor(g, {0}, c=c2)
    v1, r1 = HN.nodal_solve(f1, n, {0: 1.0})
    v2, r2 = HN.nodal_solve(f2, n, {0: 1.0})
    same += v1.tobytes() == v2.tobytes() and f1[1].tobytes() == f2[1].tobytes()
out["no_charge_c_independent"] = [same, N]
txt = json.dumps(out, ensure_ascii=False)
(R / "run3/out/check_move.json").write_text(txt, encoding="utf-8")
print(txt)
