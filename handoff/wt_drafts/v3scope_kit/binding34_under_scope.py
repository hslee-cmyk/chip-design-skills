"""묶기 card(34) 검증된 구성 예(v3_binding_briefs.md §1.3)가 범위 card(35) 계약 1 아래에서도 '모든 변이가 대상'인지 -- 범위 card 계약 7 확인.
도구 mutants(복제본 0f23786 판)로 변이를 만들고 scope_proto.select(N2w)로 대상 여부를 본다. 결과: <KIT>/out/binding34_under_scope.txt"""
import ast, sys

KIT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3scope_kit"
sys.path.insert(0, KIT)
sys.path.insert(0, "C:/g109/repo/tools/gates")
import mutate_changed as mc   # noqa: E402
import reachability as rch     # noqa: E402
import scope_proto as SP       # noqa: E402

BASE = '"""rt."""\n\n\ndef rt_gain(gm, ro):\n    """이득."""\n    return gm * ro\n\n\ndef rt_scale(x):\n    """배율."""\n    return 2.0 * x\n'
HEAD_ABCDF = '"""rt."""\n\n\ndef rt_gain(gm, ro):\n    """이득."""\n    return gm * ro\n\n\ndef rt_scale(x):\n    """배율."""\n    _ = len("rt")\n    return 3.0 * abs(x)\n'
HEAD_E = '"""rt."""\n\n\ndef rt_gain(gm, ro):\n    """이득."""\n    return gm * ro\n\n\ndef rt_scale(x):\n    """배율."""\n    _ = len("rt")\n    x = abs(x)\n    return 3.0 * x\n'

lines = []
for label, head in (("(a)(b)(c)(d)(f) head", HEAD_ABCDF), ("(e) head = Dk + docstring", HEAD_E)):
    bdefs = dict(rch.iter_defs(ast.parse(BASE)))
    for q, hfn in mc.changed_defs(BASE, head):
        ms = mc.mutants(hfn, head)
        sel = SP.select(bdefs[q], hfn, ms, "N2w") if q in bdefs else [True] * len(ms)
        lines.append("%s  %s: 변이 %d, 대상 %d, 대상 밖 %s" % (label, q, len(ms), sum(sel),
                     [("%s:%s" % (o, p)) for (o, p, _), s in zip(ms, sel) if not s]))
        lines += ["    %s:%s -> %s" % (o, p, "대상" if s else "대상 밖") for (o, p, _), s in zip(ms, sel)]
open(KIT + "/out/binding34_under_scope.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
