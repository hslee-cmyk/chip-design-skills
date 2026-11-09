"""review3 S1 재현 -- 매개변수 '위치' 정의를 고친 뒤(위치 전용·일반 = 둘을 이은 위치 인자 순번, 키워드 전용 = 그 목록 안 순번)
검토자 구성 `def f(a, /, b)` -> `def f(a, z, /, b)`에서 `b`를 읽는 문장이 대상이 되는지 본다.

비교: new = 고친 scope_proto(kind_index), old = scope_proto.v1(같은 종류 목록 안 순번), flat = 시그니처 전체 순번.
보조 구성: `def f(a, *, k=1)` -> `def f(a, z=0, *, k=1)`(키워드 전용 앞 일반 추가 -- k는 의미 불변이므로 new는 k를 더하지 않아야 한다).
변이 생성은 격리 복제본 도구 mutate_changed.mutants(0f23786 판). 결과: C:/g109/out/probe_s1_posonly.txt
"""
import ast, importlib.util, sys

G = "C:/g109"
KIT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3scope_kit"
sys.path.insert(0, G + "/repo/tools/gates")
import mutate_changed as mc   # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


NEW = load("sp_new", KIT + "/scope_proto.py")
OLD = load("sp_old", KIT + "/scope_proto.v1.py")
FLAT = load("sp_flat", KIT + "/scope_proto.py")
FLAT.PARAM_POS = "flat_index"

BODY = "    x = a + 1\n    if b > 2:\n        x = x * 2\n    return x\n"
CASES = (
    ("S1 posonly", "def f(a, /, b):\n" + BODY, "def f(a, z, /, b):\n" + BODY, "b"),
    ("kwonly 앞 일반 추가", "def f(a, *, k=1):\n    y = a\n    if k > 2:\n        y = y * 2\n    return y\n",
     "def f(a, z=0, *, k=1):\n    y = a\n    if k > 2:\n        y = y * 2\n    return y\n", "k"),
)
OUT = G + "/out/probe_s1_posonly.txt"
lines = []
for label, bsrc, hsrc, nm in CASES:
    bfn = ast.parse(bsrc).body[0]
    hfn = ast.parse(hsrc).body[0]
    ms = mc.mutants(hfn, hsrc)
    lines.append("== %s  (변이 %d)" % (label, len(ms)))
    for vn, mod in (("new", NEW), ("old", OLD), ("flat", FLAT)):
        sel = mod.select(bfn, hfn, ms, "N2w")
        cps = sorted(mod.changed_params(bfn, hfn))
        reads_nm = [p for (o, p, _), s in zip(ms, sel) if s and p.startswith("body[1]")]
        lines.append("   %-4s changed_params=%s 대상 %d / %d | '%s'를 읽는 `if`(body[1]) 몫 대상 %d"
                     % (vn, cps, sum(sel), len(ms), nm, len(reads_nm)))
        for (o, p, _), s in zip(ms, sel):
            lines.append("      %s %s:%s" % ("T" if s else "-", o, p))
open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
