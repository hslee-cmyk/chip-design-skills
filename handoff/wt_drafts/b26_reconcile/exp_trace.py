"""trace 루프 range(i + 1, …) 변이(const+·arith·const-) 구별 입력 탐색 -- b1(C:/g103/b1)과 그 변이 3종의 출력 비교.
출력: C:/g103/out/exp_trace.txt"""
import ast, importlib.util, sys

B1 = "C:/g103/b1/skills/analog-gmid-design/assets/"
OUT = open("C:/g103/out/exp_trace.txt", "w", encoding="utf-8")
sys.path.insert(0, B1)
import stick_diagram as sd  # noqa: E402

src = open(B1 + "stick_diagram.py", encoding="utf-8").read()
OLD = "for j in range(i + 1, len(chains)):"
_k = src.index("def find_differential_pair_candidates(")
_pos = src.index(OLD, _k)   # find_differential_pair_candidates 안의 첫 출현(줄 1563)
assert _pos < src.index("\ndef ", _k + 10)
VAR = {"orig": OLD, "const+": "for j in range(i + 2, len(chains)):", "arith": "for j in range(i - 1, len(chains)):",
       "const-": "for j in range(i + 0, len(chains)):"}


def load(tag):
    s = src[:_pos] + VAR[tag] + src[_pos + len(OLD):]
    spec = importlib.util.spec_from_loader("sd_" + tag.replace("+", "p").replace("-", "m"), loader=None)
    m = importlib.util.module_from_spec(spec)
    m.__file__ = B1 + "stick_diagram.py"
    sys.modules[spec.name] = m
    exec(compile(s, B1 + "stick_diagram.py", "exec"), m.__dict__)
    return m


T = sd.Transistor


def circ(n):
    ts = [T("Mt", "nmos", source="gnd", drain="ntail", gate="nb")]
    for k in range(1, n + 1):
        ts.append(T("Mi%d" % k, "nmos", source="ntail", drain="no%d" % k, gate="ni%d" % k))
        ts.append(T("Ml%d" % k, "pmos", source="vdd", drain="no%d" % k, gate="nbp"))
    return ts


mods = {t: load(t) for t in VAR}
for n in (2, 3):
    ts = circ(n)
    res = {}
    for t, m in mods.items():
        r = m.find_differential_pair_candidates(ts)
        res[t] = None if r is None else [(c["direction"], c["position"], c["devices"]) for c in r["candidates"]]
    for t in VAR:
        OUT.write("n=%d %-7s same_as_orig=%s %s\n" % (n, t, res[t] == res["orig"], res[t]))
OUT.close()
print(open("C:/g103/out/exp_trace.txt", encoding="utf-8").read())
