import hashlib, itertools, subprocess, re
R = "C:/g374/f/r"; BASE = "da9de15"; HEAD = "99082e6"
A = "skills/analog-gmid-design/assets/tests/contracts/"
L = sorted(A + f for f in ["test_b34_grammar_explicit.py", "test_d_delete_dead.py", "test_d_delete_telescopic.py", "test_dup_kcl_edges.py", "test_dup_w_calc.py", "test_ts6_dead_probes.py"])
def blob(rev, p):
    return subprocess.run(["git", "-C", R, "rev-parse", rev + ":" + p], capture_output=True, text=True, check=True).stdout.strip()
B = {p: blob(BASE, p) for p in L}; H = {p: blob(HEAD, p) for p in L}
def dh(h):
    return hashlib.sha256("".join("%s\t%s\t%s\n" % (p, B[p], h[p]) for p in L).encode()).hexdigest()
print("honest", dh(H))
K = A + "test_dup_kcl_edges.py"
src = subprocess.run(["git", "-C", R, "show", HEAD + ":" + K], capture_output=True, check=True).stdout
mods = ("gmid_lut", "topology_authoring", "circuit_state_graph", "gmid_sizing_engine", "circuit_metrics", "theta_search", "stick_diagram", "sizing_layout_convergence", "instance_report_builder")
old = ("(" + ", ".join('"%s"' % m for m in mods) + ")").encode()
assert src.count(old) == 1
def gitblob(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()
for perm in itertools.permutations(mods):
    if perm == mods: continue
    nb = src.replace(old, ("(" + ", ".join('"%s"' % m for m in perm) + ")").encode())
    h = dict(H); h[K] = gitblob(nb)
    v = dh(h)
    if v.startswith("05b8eec4"):
        print("FOUND", perm, v); break
else:
    print("no permutation matches")
