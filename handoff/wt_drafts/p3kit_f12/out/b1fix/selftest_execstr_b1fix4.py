"""b1fix4 selftest(review_p3_f1_b1fix3 minor 1~4 -- 계약 1 (e) b1fix4 문언과 kit `f12_execstr` 대조, 측정 전용).

    python -B selftest_execstr_b1fix4.py [<새 f12_execstr.py> [<옛 f12_execstr.py.pre-b1fix4.bak>]] [--out <json>]

ADV: 새 kit이 통과하고 옛 kit이 실패해야 하는 경우(b1fix4에서 바뀐 동작 -- minor 3 판 순서 = 채움 자리 소스 위치).
DOC: 새 kit이 통과해야 하는 문언 확인(minor 1 대소문자 무시, minor 2 '이 식이 보지 않는 것' -- 기본값·메서드 매개변수 경유 (s3),
     minor 4 이름 충돌 파싱 실패·f-string 멈춤). b1fix3 kit도 같은 동작이었다(문언만 보탬) -- 옛 kit 결과는 기록만.
판 수 다름의 실패 이름(`exec_str_variant_count`, f12_equiv)은 git 커밋 쌍이 필요해 여기서 재지 않는다(F1 card b1fix4 단락의 사슬 실측).
"""
import ast
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] != "--out"]
NEW = args[0] if len(args) > 0 else os.path.join(KIT, "f12_execstr.py")
OLD = args[1] if len(args) > 1 else os.path.join(KIT, "f12_execstr.py.pre-b1fix4.bak")
DROP = {"stick_diagram": {"find_idiom_matches"}}


def load(path, name):
    spec = importlib.util.spec_from_loader(name, loader=None)
    mod = importlib.util.module_from_spec(spec)
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"), mod.__dict__)
    return mod


def variants(xs, src):
    t = ast.parse(src)
    hit, meta, _u = xs.exec_strings_ex(t)
    n = [x for x in ast.walk(t) if isinstance(x, ast.Constant) and id(x) in hit][0]
    return [txt for txt, _tr in xs.exec_texts(n.value, meta[id(n)])]


ORD = 'T = "import {m} as x"\nexec(T.format(m="zzz_mod"))\nexec(T.format(m="aaa_mod"))\n'
ORD_PCT = 'T = "import %s as x"\nexec(T % "zzz_mod")\nexec(T % "aaa_mod")\n'
ADV = {
    "m3 .v<j> order = fill-site source position (format)": lambda xs: variants(xs, ORD) == ["import zzz_mod as x", "import aaa_mod as x"],
    "m3 .v<j> order = fill-site source position (%)": lambda xs: variants(xs, ORD_PCT) == ["import zzz_mod as x", "import aaa_mod as x"],
}


def sc(xs, src):
    return xs.scan_tree(ast.parse(src), DROP)


DOC = {
    "m1 Python.exe (upper) is interpreter": lambda xs: [e["line"] for e in sc(xs, '["C:/Python314/Python.exe", "-c", "import os"]\n')["exec"]] == [1],
    "m1 PYTHON3.EXE (upper) is interpreter": lambda xs: [e["line"] for e in sc(xs, '["C:/PY/PYTHON3.EXE", "-B", "-c", "import os"]\n')["exec"]] == [1],
    "m2 default param: not exec, not outside, content-rule only": lambda xs: (lambda r: r["exec"] == [] and r["unresolved_sink"] == []
        and [e["line"] for e in r["content_only"]] == [1])(sc(xs, 'def run(c="import design_report"):\n    exec(c)\nrun()\n')),
    "m2 (s3) via method param: not exec, not outside, content-rule only": lambda xs: (lambda r: r["exec"] == [] and r["unresolved_sink"] == []
        and [e["line"] for e in r["content_only"]] == [4])(sc(xs, 'class K:\n    def w(self, t):\n        self.fh.write(t)\n'
                                                               'K().w("import stick_diagram\\nstick_diagram.find_idiom_matches()")\n')),
    "m4 name collision parse fail = stop": lambda xs: [e["line"] for e in sc(xs, 'def a():\n    code = "x = ("\ndef b():\n    code = "import os"\n'
                                                                                 '    exec(code)\n')["parse_fail"]] == [2],
    "m4 name collision f-string = stop": lambda xs: len(sc(xs, 'def a(m):\n    code = f"import {m}"\ndef b():\n    code = "import os"\n'
                                                               '    exec(code)\n')["stop_fstring"]) == 1,
}


def run(xs, cases):
    out = {}
    for k, f in cases.items():
        try:
            out[k] = bool(f(xs))
        except Exception as e:
            out[k] = "error: %s: %s" % (type(e).__name__, e)
    return out


new, old = load(NEW, "xs_new"), load(OLD, "xs_old")
res = {"new_kit": NEW, "old_kit": OLD, "new_adv": run(new, ADV), "new_doc": run(new, DOC), "old_adv": run(old, ADV), "old_doc": run(old, DOC)}
ok_new = all(v is True for v in list(res["new_adv"].values()) + list(res["new_doc"].values()))
ok_old = all(v is not True for v in res["old_adv"].values())
res["verdict"] = {"new_all_pass": ok_new, "old_all_adv_fail": ok_old}
for grp in ("new_adv", "new_doc", "old_adv", "old_doc"):
    for k, v in res[grp].items():
        print("%-8s %-5s %s" % (grp, "PASS" if v is True else "FAIL", k + ("" if v in (True, False) else "  [" + v + "]")))
print(json.dumps(res["verdict"]))
if OUT:
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
sys.exit(0 if ok_new and ok_old else 1)
