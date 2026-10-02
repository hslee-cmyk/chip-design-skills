"""20260930-v3-exempt-binding 순서 7 probe p1~p8 (auditor). 기대값은 spec card 계약 문장과 구성에서 만든다.
사용: python -B probes.py <병합본 mutate_changed.py> <base mutate_changed.py> <pytest_gate.ini> <작업 디렉터리> <출력 json>
묶기 해시 기대값은 auditor 독립 구현(my_bind, 계약 머리 정의)."""
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys

MT, BT, INI, WORK, OUTP = sys.argv[1:6]
PY = sys.executable
A = "skills/analog-gmid-design/assets"
RES = {}


def save():
    with open(OUTP, "w", encoding="utf-8") as f:
        json.dump(RES, f, ensure_ascii=False, indent=1)


def my_bind_node(node):
    return hashlib.sha256(ast.dump(node, annotate_fields=True, include_attributes=False, indent=None,
                                   show_empty=False).encode("utf-8")).hexdigest()


def find_def(src, qualname):
    hits = []
    stack = [(ast.parse(src), "")]
    while stack:
        node, pre = stack.pop()
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = ch.name if not pre else pre + "." + ch.name
                if q == qualname and not isinstance(ch, ast.ClassDef):
                    hits.append(ch)
                stack.append((ch, q))
            else:
                stack.append((ch, pre))
    assert len(hits) == 1, (qualname, len(hits))
    return hits[0]


def my_bind(src, qualname):
    return my_bind_node(find_def(src, qualname))


def git(cwd, *a):
    r = subprocess.run(["git", "-C", cwd, *a], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace"))
    return r.stdout.decode("utf-8").strip()


def mkrepo(name, base, head):
    path = os.path.join(WORK, name)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    git(path, "init", "-q", "-b", "master")
    for k, v in (("user.name", "audit"), ("user.email", "audit@example.invalid"), ("core.autocrlf", "false"),
                 ("commit.gpgsign", "false"), ("core.hooksPath", path + "/.nohooks")):
        git(path, "config", k, v)
    for files, msg in ((base, "base"), (head, "head")):
        for p, data in files.items():
            fp = os.path.join(path, p)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "w", encoding="utf-8", newline="\n") as f:
                f.write(data)
        git(path, "add", "-A")
        git(path, "commit", "-q", "--allow-empty", "-m", msg)
        if msg == "base":
            b = git(path, "rev-parse", "HEAD")
    return path, b, git(path, "rev-parse", "HEAD")


def run(tool, repo, b, h, tag):
    out = os.path.join(WORK, tag + ".jsonl")
    if os.path.exists(out):
        os.remove(out)
    r = subprocess.run([PY, tool, "--root", repo, "--base", b, "--head", h, "--pytest-ini", INI, "--out", out],
                       capture_output=True)
    so = r.stdout.decode("utf-8", "replace")
    lines = [l for l in so.splitlines() if l.strip()]
    raw_out = open(out, encoding="utf-8").read().splitlines() if os.path.exists(out) else []
    return {"exit": r.returncode, "stdout_lines": len(lines), "stdout": lines[0] if lines else None,
            "obj": json.loads(lines[0]) if lines else None, "stderr_tail": r.stderr.decode("utf-8", "replace")[-500:],
            "out_raw": raw_out}


def approval(name, targets):
    return (".ai/approvals/%s.md" % name,
            "---\nid: %s\ndate: 2026-10-02\ntarget_kind: decision\ntarget: %s\nscope: auditor probe\n---\n\n## 사용자 원문\n\n> probe\n" % (name, targets))


TEST_HDR = "import sys\nimport asyncio\nfrom pathlib import Path\n\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"

# ------------------------------------------------------------------ P1: p1·p3·p4·p5·p8
PA_BASE = '''"""pa."""


def deco(f):
    return f


def deco2(n):
    def w(f):
        return f
    return w


def f1(x):
    return x


def f2(x):
    return x


def f3(x):
    return x


def f5(x):
    return x


def dec_fn(x):
    return x


def dec2_fn(x):
    return x


async def af(x):
    return x


class K:
    def meth(self, x):
        return x


def outer(x):
    return x
'''
PA_HEAD = '''"""pa."""


def deco(f):
    return f


def deco2(n):
    def w(f):
        return f
    return w


def f1(x):
    """f1."""
    _ = len("p")
    return abs(x)


def f2(x):
    """f2."""
    _ = len("p")
    return abs(x)


def f3(x):
    """f3."""
    _ = len("p")
    return abs(x)


def f5(x):
    """f5."""
    _a = len("p")
    _b = len("q")
    _c = len("r")
    _d = len("s")
    return abs(x)


@deco
def dec_fn(x):
    """dec."""
    _ = len("p")
    return abs(x)


@deco2(1)
def dec2_fn(x):
    """dec2."""
    _ = len("p")
    return abs(x)


async def af(x):
    """async."""
    _ = len("p")
    return abs(x)


class K:
    def meth(self, x):
        """meth."""
        _ = len("p")
        return abs(x)


def outer(x):
    """outer."""
    def inner(y):
        _ = len("i")
        return abs(y)
    return inner(x)
'''
PB_BASE = '''def g1(x):
    return x
'''
PB_HEAD = '''def g1(x):
    """g1."""
    _ = len("p")
    return abs(x)
'''
T_PA = TEST_HDR + '''from pa import f1, f2, f3, f5, dec_fn, dec2_fn, af, K, outer


def test_pa():
    assert f1(-2) == 2
    assert f2(-2) == 2
    assert f3(-2) == 2
    assert f5(-2) == 2
    assert dec_fn(-2) == 2
    assert dec2_fn(-2) == 2
    assert asyncio.run(af(-2)) == 2
    assert K().meth(-2) == 2
    assert outer(-2) == 2
'''
T_PB = TEST_HDR + '''from pb import g1


def test_pb():
    assert g1(-2) == 2
'''
H_F1 = my_bind(PA_HEAD, "f1")
WRONG0 = "0" * 64
WRONGF = "f" * 64
H_F5 = my_bind(PA_HEAD, "f5")
H_DEC2 = my_bind(PA_HEAD, "dec2_fn")
H_DEC2_ALT = my_bind(PA_HEAD.replace("@deco2(1)", "@deco2(2)"), "dec2_fn")
X1, X2, X3, XG = "pa:f1:stmt_delete:body[1]", "pa:f2:stmt_delete:body[1]", "pa:f3:stmt_delete:body[1]", "pb:g1:stmt_delete:body[1]"
X5 = ["pa:f5:stmt_delete:body[%d]" % i for i in (1, 2, 3, 4)]
XD = "pa:dec2_fn:stmt_delete:body[1]"
rec1 = approval("p-r1", ", ".join([X1, X1 + "@" + WRONG0, X1 + "@" + H_F1,
                                   X2 + "@abc", X2, X2 + "@" + WRONGF,
                                   X3 + "@" + WRONGF,
                                   X5[0] + "@a@b", X5[1] + "@" + H_F5.upper(), X5[2] + "@" + H_F5[:63],
                                   "  " + X5[3] + "@" + H_F5 + "  ",
                                   XD + "@" + H_DEC2_ALT, XG]))
rec2 = approval("p-r2", X3 + "@" + WRONGF)
base1 = {A + "/pa.py": PA_BASE, A + "/pb.py": PB_BASE}
head1 = {A + "/pa.py": PA_HEAD, A + "/pb.py": PB_HEAD, A + "/tests/test_pa.py": T_PA, A + "/tests/test_pb.py": T_PB}
RES["P1_const"] = {"H_f1": H_F1, "H_f5": H_F5, "H_dec2": H_DEC2, "H_dec2_alt(@deco2(2))": H_DEC2_ALT,
                   "dec_arg_changes_hash": H_DEC2 != H_DEC2_ALT}

r, b, h = mkrepo("P1", base1, dict(head1, **dict([rec1, rec2])))
m = run(MT, r, b, h, "P1_m")
RES["P1_m"] = m
save()
r0, b0, h0 = mkrepo("P1n", base1, head1)
mn = run(MT, r0, b0, h0, "P1n_m")
bn = run(BT, r0, b0, h0, "P1n_b")
RES["P8_m"], RES["P8_b"] = mn, bn
save()

# ---- 판정(P1)
o = m["obj"]
outrecs = [json.loads(l) for l in m["out_raw"]]
gen_order = []
for x in [json.loads(l) for l in bn["out_raw"]]:  # base 도구 무기록 실행의 --out 순서 = 생성 순서(독립 기준)
    gen_order.append(x["id"])
srcs = {"pa": PA_HEAD, "pb": PB_HEAD}


def F_of(mid):
    mod, q = mid.split(":")[0], mid.split(":")[1]
    return my_bind(srcs[mod], q)


exp_ign = []
by = {X2: sorted([X2 + "@abc", X2, X2 + "@" + WRONGF])}
def item(el):
    mid = el.split("@")[0]
    if "@" not in el:
        return {"id": mid, "reason": "unbound"}
    p = el.split("@")
    if len(p) == 2 and len(p[1]) == 64 and all(c in "0123456789abcdef" for c in p[1]):
        return {"id": mid, "reason": "hash_mismatch", "approved_hash": p[1], "head_hash": F_of(mid)}
    return {"id": mid, "reason": "malformed", "element": el}


ign_by_id = {X2: [item(e) for e in by[X2]], X3: [item(X3 + "@" + WRONGF)],
             X5[0]: [item(X5[0] + "@a@b")], X5[1]: [item(X5[1] + "@" + H_F5.upper())],
             X5[2]: [item(X5[2] + "@" + H_F5[:63])], XD: [item(XD + "@" + H_DEC2_ALT)], XG: [item(XG)]}
for mid in gen_order:
    exp_ign += ign_by_id.get(mid, [])
exempt_ids = {X1, X5[3]}
exp_surv = [x["id"] for x in [json.loads(l) for l in bn["out_raw"]] if x["result"] == "survived" and x["id"] not in exempt_ids]
chk = {}
chk["exit"] = [m["exit"], 1]
chk["stdout_one_line"] = m["stdout_lines"] == 1
chk["key_order"] = list(o) == ["tool", "verdict", "targets", "mutants", "killed", "survivors", "survivor_bindings", "exempt_ignored"]
chk["exempt_ignored_eq_expected"] = o["exempt_ignored"] == exp_ign
chk["no_X1_in_ignored(p1a)"] = all(e["id"] != X1 for e in o["exempt_ignored"])
chk["X2_three_sorted(p1b)"] = [e for e in o["exempt_ignored"] if e["id"] == X2] == ign_by_id[X2]
chk["X3_once_two_records(p1c)"] = len([e for e in o["exempt_ignored"] if e["id"] == X3]) == 1
chk["survivors_eq_expected"] = o["survivors"] == exp_surv
chk["survivor_bindings"] = o["survivor_bindings"] == ["%s@%s" % (s, F_of(s)) for s in o["survivors"]]
ex = [x for x in outrecs if x.get("result") == "exempt"]
chk["exempt_records"] = ex == [{"id": X1, "result": "exempt", "bind_hash": H_F1},
                               {"id": X5[3], "result": "exempt", "bind_hash": H_F5}] or sorted(map(json.dumps, ex)) == sorted(map(json.dumps, [{"id": X1, "result": "exempt", "bind_hash": H_F1}, {"id": X5[3], "result": "exempt", "bind_hash": H_F5}]))
chk["exempt_record_key_order"] = all(list(x) == ["id", "result", "bind_hash"] for x in ex)
chk["mutants_eq_out_lines_incl_exempt"] = o["mutants"] == len(outrecs) == len(bn["out_raw"])
chk["out_order_eq_generation_order"] = [x["id"] for x in outrecs] == gen_order
# p4: 해시 종류별(생존 바인딩에서) 독립 대조
p4 = {}
for s, bnd in zip(o["survivors"], o["survivor_bindings"]):
    p4[s] = {"tool": bnd.split("@")[1][:16], "auditor": F_of(s)[:16], "eq": bnd.split("@")[1] == F_of(s)}
chk["p4_by_survivor"] = p4
chk["p4_kinds_present"] = {k: any(s.startswith(k) for s in o["survivors"]) for k in
                           ("pa:dec_fn:", "pa:af:", "pa:K.meth:", "pa:outer:stmt_delete:body[1].body[0]", "pa:outer.inner:")}
chk["p4_nested_outer_binding_is_outer"] = all(bnd.endswith(my_bind(PA_HEAD, "outer")) for s, bnd in zip(o["survivors"], o["survivor_bindings"]) if s.startswith("pa:outer:"))
chk["p4_inner_binding_is_inner"] = all(bnd.endswith(my_bind(PA_HEAD, "outer.inner")) for s, bnd in zip(o["survivors"], o["survivor_bindings"]) if s.startswith("pa:outer.inner:"))
chk["p4_decorator_arg_mismatch"] = [e for e in o["exempt_ignored"] if e["id"] == XD] == [{"id": XD, "reason": "hash_mismatch", "approved_hash": H_DEC2_ALT, "head_hash": H_DEC2}]
chk["p5_malformed"] = [e for e in o["exempt_ignored"] if e["id"] in X5[:3]] == [item(X5[0] + "@a@b"), item(X5[1] + "@" + H_F5.upper()), item(X5[2] + "@" + H_F5[:63])]
chk["p5_spaces_exempt"] = X5[3] not in o["survivors"] and any(x["id"] == X5[3] for x in ex)
# p8
ob, om = bn["obj"], mn["obj"]
chk["p8_exit_same"] = [bn["exit"], mn["exit"]]
chk["p8_equal_without_new_keys"] = {k: v for k, v in om.items() if k not in ("survivor_bindings", "exempt_ignored")} == ob
chk["p8_new_keys"] = {"exempt_ignored": om.get("exempt_ignored"), "survivor_bindings_match": om.get("survivor_bindings") == ["%s@%s" % (s, F_of(s)) for s in om["survivors"]]}
chk["p8_out_equal"] = mn["out_raw"] == bn["out_raw"]
RES["P1_checks"] = chk
save()

# ------------------------------------------------------------------ P2: p2·p6·p7 입력
PC_BASE = '''def h0(x):
    return x + 1


def h1(x):
    return x
'''
PC_HEAD = '''def h0(x):
    return x + 1


def h1(x):
    return x * 2
'''
M_BASE = '''def q(x):
    return x + 1
'''
M_HEAD = '''def q(x):
    return x + 2
'''
T_PC = TEST_HDR + '''from pc import h1


def test_h1():
    assert h1(3) == 6
'''
H_Q = my_bind(M_HEAD, "q")
H_H0 = my_bind(PC_HEAD, "h0")
XH1 = "pc:h1:arith:body[0].value"
unrelated = [A + "/tests/test_pc.py::test_h1", A + "/pc.py::h1", "pc:h0:arith:body[0].value",
             "pc:h0:arith:body[0].value@" + H_H0, "U-01", "m:q:const+:body[0].value.right", "m:q:const+:body[0].value.right@" + H_Q]
rec = approval("p-r3", ", ".join(unrelated + [XH1]))
base2 = {A + "/pc.py": PC_BASE, A + "/tests/tools/m.py": M_BASE}
head2 = {A + "/pc.py": PC_HEAD, A + "/tests/tools/m.py": M_HEAD, A + "/tests/test_pc.py": T_PC, rec[0]: rec[1]}
r, b, h = mkrepo("P2", base2, head2)
m2 = run(MT, r, b, h, "P2_m")
b2 = run(BT, r, b, h, "P2_b")
RES["P2_m"], RES["P2_b"] = m2, b2
o2 = m2["obj"]
c2 = {"exit_m": m2["exit"], "exit_b": b2["exit"],
      "targets_m": o2["targets"], "tests_tools_not_target": all("tests/tools" not in t for t in o2["targets"]),
      "exempt_ignored_m": o2["exempt_ignored"],
      "p2_only_own_id": o2["exempt_ignored"] == [{"id": XH1, "reason": "unbound"}],
      "p6_pass_with_nonempty_ignored": m2["exit"] == 0 and o2["verdict"] == "PASS" and len(o2["exempt_ignored"]) > 0,
      "base_obj": b2["obj"], "repo": r, "base": b, "head": h}
RES["P2_checks"] = c2
save()
print(json.dumps({"P1": RES["P1_checks"], "P2": {k: v for k, v in c2.items() if k not in ("base_obj",)}}, ensure_ascii=False, indent=1))
