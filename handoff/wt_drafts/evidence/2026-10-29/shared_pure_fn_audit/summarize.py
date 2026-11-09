"""Summarize shared callees: kind (function/record class/other class), distinct roots across sites.

Usage: python summarize.py <gmid_engine dir>  -> summary.tsv
"""
import ast
import collections
import os
import sys

ENG = sys.argv[1]
INFRA = ("authoring._rejection", "authoring._spec_fields", "core.", "lut._helpers_fail", "lut.axis_guard",
         "authoring.json_read")

rows = collections.OrderedDict()
for l in open("reach.tsv", encoding="utf-8").read().splitlines()[1:]:
    fn, site, rts = l.split("\t")
    rows.setdefault(fn, []).append((site, set(rts.split(";"))))


def kind_of(fq):
    mod, name = fq.rsplit(".", 1)
    path = os.path.join(ENG, *mod.split(".")) + ".py"
    if not os.path.exists(path):
        path = os.path.join(ENG, *mod.split("."), "__init__.py")
    t = ast.parse(open(path, encoding="utf-8").read())
    for n in t.body:
        if getattr(n, "name", None) == name:
            if isinstance(n, ast.ClassDef):
                decos = [ast.unparse(d) for d in n.decorator_list]
                bases = [ast.unparse(b) for b in n.bases]
                if any("dataclass" in d for d in decos) or any(b in ("NamedTuple", "typing.NamedTuple", "enum.Enum", "Enum") or b.endswith("Error") or b.endswith("Exception") for b in bases):
                    return "record"
                return "class"
            return "function"
    return "?"


with open("summary.tsv", "w", encoding="utf-8") as fh:
    fh.write("fn\tkind\tinfra\tn_sites\tn_roots\troots\n")
    for fn, sites in rows.items():
        allr = set()
        for _, r in sites:
            allr |= r
        infra = any(fn.startswith(p) for p in INFRA)
        fh.write("%s\t%s\t%s\t%d\t%d\t%s\n" % (fn, kind_of(fn), "infra" if infra else "", len(sites), len(allr),
                                                ";".join(sorted(allr))[:400]))
print(len(rows))
