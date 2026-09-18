import ast
def match(subj, exp):
    a, b = ast.parse(subj, mode="eval").body, ast.parse(exp, mode="eval").body
    fwd, rev, leaves = {}, {}, []
    def leaf_key(n):
        return ("N", n.id) if isinstance(n, ast.Name) else ("C", repr(n.value))
    def walk(x, y):
        if isinstance(x, (ast.Name, ast.Constant)) and isinstance(y, (ast.Name, ast.Constant)):
            kx, ky = leaf_key(x), leaf_key(y); leaves.append(kx)
            if fwd.setdefault(kx, ky) != ky or rev.setdefault(ky, kx) != kx: return False
            return True
        if type(x) is not type(y): return False
        if isinstance(x, ast.BinOp): return type(x.op) is type(y.op) and walk(x.left, y.left) and walk(x.right, y.right)
        if isinstance(x, ast.UnaryOp): return type(x.op) is type(y.op) and walk(x.operand, y.operand)
        if isinstance(x, ast.Call):
            return ast.dump(x.func) == ast.dump(y.func) and len(x.args) == len(y.args) and all(walk(p, q) for p, q in zip(x.args, y.args))
        return False
    iso = walk(a, b)
    repeated = len(leaves) != len(set(leaves))
    return iso and repeated, iso, repeated
cases = [("e329283 (참 양성 기대)", "(1 - cold_start_alpha) * a_1d + cold_start_alpha * a_2d_cold", "(1 - 0.65) * _a1d_demo + 0.65 * _a2d_cold_expected"),
         ("gm*ro 독립 oracle (통과 기대)", "gm * ro", "2e-3 * 50e3"),
         ("KCL 합 (통과 기대)", "i1 + i2", "10e-6 + 20e-6"),
         ("다른 구조 (통과 기대)", "a * b + c", "0.13"),
         ("잎 대응 불일치 (통과 기대)", "a * a + b", "2.0 * 3.0 + 1.0")]
with open(__file__.replace("v4.py", "v4.out.txt"), "a", encoding="utf-8") as f:
    for name, s_, e in cases:
        r = match(s_, e); f.write(f"{name}: FAIL={r[0]} (동형={r[1]}, 반복 잎={r[2]})\n"); print(name, r)
