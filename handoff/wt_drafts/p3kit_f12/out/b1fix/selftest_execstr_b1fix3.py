"""f12_execstr b1fix3 selftest -- review_p3_f1_b1fix2 m1~m4 적대 입력(1.3 표의 kit '놓침'·'기록 없음'·'안 걸림' 행 + m3·m4 예).

    python -B selftest_execstr_b1fix3.py [<새 kit .py> [<옛 kit .py>]]

ADV 경우: 새 kit은 모두 통과, 옛 kit(.pre-b1fix3.bak = b1fix2 판)은 모두 실패해야 한다(실패를 '실제로 잡는다'의 증거).
REG 경우: 새 kit이 통과해야 하는 회귀(옛 b1fix2 selftest 11경우 + 순환 가드·동적 import 유지·자리 단위).
exit 0 = (새 kit ADV·REG 전부 통과) 그리고 (옛 kit ADV 전부 실패). 결과는 같은 디렉터리 selftest_execstr_b1fix3.out.json에도 쓴다.
"""
import ast
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, "..", ".."))
NEW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(KIT, "f12_execstr.py")
OLD = sys.argv[2] if len(sys.argv) > 2 else os.path.join(KIT, "f12_execstr.py.pre-b1fix3.bak")
SD, ACF = "stick_diagram", "audit_current_forced"
DROP = {SD: {"find_idiom_matches"}, ACF: {"_theta_evidence_for_pair"}}


def load(path, name):
    spec = importlib.util.spec_from_loader(name, loader=None)
    mod = importlib.util.module_from_spec(spec)
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"), mod.__dict__)
    return mod


def scan_new(xs, src):
    return xs.scan_tree(ast.parse(src), DROP)


def scan_old(xs, src):
    """옛 kit(b1fix2)에는 scan_tree가 없다 -- 옛 main의 파일 단위 처리(그 판 344~392행)를 그대로 옮긴 어댑터."""
    tree = ast.parse(src)
    res = {"exec": [], "parse_fail": [], "unresolved_sink": [], "stop_fstring": []}
    docs = xs.docstring_ids(tree)
    hit, meta, unres = xs.exec_strings_ex(tree)
    for u in unres:
        res["unresolved_sink"].append({"line": u[0], "sink": u[1], "expr": u[2], "kind": u[3] if len(u) > 3 else None})
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)) or id(n) in docs or id(n) not in hit:
            continue
        tm = meta[id(n)]["tmpl"]
        sub = xs.parse_exec(n.value, tm)
        ent = {"line": n.lineno, "base": sorted(meta[id(n)]["base"]), "tmpl": sorted(t for t in tm if t), "parses": sub is not None}
        if sub is None:
            res["parse_fail"].append({"line": n.lineno})
        else:
            ent["e3"] = xs.e3_hits(sub)
            ent["sd_drop_reads"] = sorted({nm for _l, nm in xs.file_reads(sub) if nm in DROP[SD]})
            ent["acf_drop_reads"] = []   # 옛 file_reads는 SD 고정
            dyn = xs.dynamic_import_slots(sub)
            if dyn:
                ent["dynamic_import"] = dyn
        res["exec"].append(ent)
    return res


def L(src, marker):
    return next(i for i, s in enumerate(src.split("\n"), 1) if marker in s)


def ex(r, line):
    return [e for e in r["exec"] if e["line"] == line]


SHADOW = '''import sys
exe = sys.executable


def run(code):
    return [exe, "-c", code]


class K:
    def run(self, code):
        exec(code)  # M-METHOD


def wrap2(c):
    return run(c)


def kwo(*, code):
    exec(code)  # M-KWO


f = lambda c: exec(c)  # M-LAMBDA
run("x = (")  # M-PF
wrap2("import design_report")  # M-2HOP
run(code="import sizing_recipe")  # M-KWARG
K().run("import os")
'''
FSTR = 'import sys\nm = "x"\nr = [sys.executable, "-c", f"import {m}"]  # M-F\n'
ACFS = 'exec("import audit_current_forced as a\\na._theta_evidence_for_pair()")  # M-ACF\n'
DED = 'import textwrap\nX = textwrap.dedent("""\n    import stick_diagram\n    stick_diagram.find_idiom_matches()\n""")\nexec(X)\n'
PCTA = 'tag = "t"\ncode = "import sizing_recipe  # %s" % tag  # M-PCTA\nexec(code)\n'
FMT4 = 'T = "import {mod} as m\\nm.find_idiom_matches()"  # M-FMT4\nexec(T.format(mod="stick_diagram"))\n'
PCT4 = 'exec("import %s as m\\nm.find_idiom_matches()" % "stick_diagram")  # M-PCT4\n'
FROM4 = 'exec("from {pkg} import find_idiom_matches".format(pkg="stick_diagram"))  # M-FROM4\n'

ADV = {
    # review 1.3 '놓침': 같은 파일 메서드 K.run(self, code)가 이름 dict를 덮어 ③ 위치가 어긋남 -> 파싱 실패(멈춤)를 놓침
    "m1 shadow: parse fail via ③": (SHADOW, lambda r: any(p["line"] == L(SHADOW, "M-PF") for p in r["parse_fail"])),
    # review 1.3 '놓침': wrap2(c) -> run(c) 2단 ③
    "m1 shadow: 2-hop ③ + E3": (SHADOW, lambda r: any(e.get("e3") for e in ex(r, L(SHADOW, "M-2HOP")))),
    # review 1.3: run(code=...)의 자리 종류는 (s2) -- 옛 kit은 메서드 쪽 매칭으로 (s1)
    "m1 shadow: kw arg base s2": (SHADOW, lambda r: [e["base"] for e in ex(r, L(SHADOW, "M-KWARG"))] == [["s2"]]),
    # review 1.3 '기록 없음': 메서드·kw-only·lambda 경유
    "m1 method recorded": (SHADOW, lambda r: any(u["line"] == L(SHADOW, "M-METHOD") and u["kind"] == "method" for u in r["unresolved_sink"])),
    "m1 kwonly recorded": (SHADOW, lambda r: any(u["line"] == L(SHADOW, "M-KWO") and u["kind"] == "kwonly" for u in r["unresolved_sink"])),
    "m1 lambda recorded": (SHADOW, lambda r: any(u["line"] == L(SHADOW, "M-LAMBDA") and u["kind"] == "lambda" for u in r["unresolved_sink"])),
    # review 1.3: f-string 잎 -> 멈춤 표지
    "m1 f-string stop": (FSTR, lambda r: [s["line"] for s in r["stop_fstring"]] == [L(FSTR, "M-F")]),
    # review 1.3 '안 걸림': ACF 삭제 집합 읽기
    "m1 ACF file_reads": (ACFS, lambda r: [e["acf_drop_reads"] for e in ex(r, 1)] == [["_theta_evidence_for_pair"]]),
    # m3: 대입값이 감싼 식
    "m3 X = dedent(...)": (DED, lambda r: [e.get("sd_drop_reads") for e in ex(r, L(DED, "dedent("))] == [["find_idiom_matches"]]),
    "m3 code = '...' % x": (PCTA, lambda r: [(e["tmpl"], bool(e.get("e3"))) for e in ex(r, L(PCTA, "M-PCTA"))] == [(["percent"], True)]),
    # m4: import 모듈 자리 자리표시자 + 상수 인자
    "m4 format const": (FMT4, lambda r: [(e.get("sd_drop_reads"), e.get("dynamic_import")) for e in ex(r, 1)] == [(["find_idiom_matches"], None)]),
    "m4 percent const": (PCT4, lambda r: [e.get("sd_drop_reads") for e in ex(r, 1)] == [["find_idiom_matches"]]),
    "m4 from-import const": (FROM4, lambda r: [e.get("sd_drop_reads") for e in ex(r, 1)] == [["find_idiom_matches"]]),
}

OLD_ST = {   # 옛 selftest_execstr_b1fix2.py 11경우(실행 문자열 (줄, 값) 집합)
    "git -c": ('import subprocess\nsubprocess.run(["git","clone","-c","core.x=1"])\n', []),
    "pytest -c": ('import sys\n[sys.executable,"-P","-m","pytest","-c","a.ini"]\n', []),
    "py -c": ('import sys\n[sys.executable,"-B","-c","import os"]\n', [2]),
    "PY name": ('import sys\nPY=sys.executable\nS="import a"\n[PY,"-c",S]\n', [3]),
    "python lit": ('["C:/Python314/python.exe","-X","utf8","-c","import b"]\n', [1]),
    "emit log": ('def emit(s=""):\n    f.write(s+X)\nemit("  !! no x")\nemit("import z")\n', [4]),
    "format": ('import sys\nSIM="import {mod} as m"\n[sys.executable,"-c",SIM.format(mod="q")]\n', [2]),
    "percent": ('import sys\nT="import %s"\n[sys.executable,"-c",T % "q"]\n', [2]),
    "dedent": ('import textwrap\nS="  import k"\nexec(textwrap.dedent(S))\n', [2]),
    "fstring": ('import sys\nm="x"\n[sys.executable,"-c",f"import {m}"]\n', []),
    "param fwd": ('import sys\ndef run(s,*a):\n    return [sys.executable,"-c",s,*a]\nrun("import w")\n', [4]),
}
REG = {"b1fix2 " + k: (src, (lambda exp: lambda r: sorted(e["line"] for e in r["exec"]) == exp)(exp)) for k, (src, exp) in OLD_ST.items()}
CYC = 'src = "import topology_library"\nsrc = src.replace("a", "a")\nexec(src)\n'
CYC2 = 'def f(s):\n    s = s.strip()\n    exec(s)\nf("import design_report")\n'
DYN = 'T = "import {mod} as m"\nexec(T.format(mod=name))\n'
BAD4 = 'exec("import {m}".format(m="a b"))\n'
SITE = 'p = "x.py"\nexec(compile(open(p).read(), p, "exec"))\n'
TWO = ('import sys\ndef a():\n    def run(code):\n        return [sys.executable, "-c", code]\n    return run\n'
       'def b():\n    def run(x, code):\n        exec(code)\n    run(1, "import sizing_recipe")\nrun("import design_report")\n')
REG.update({
    "m3 cycle guard (replace)": (CYC, lambda r: [bool(e.get("e3")) for e in r["exec"]] == [True]),
    "m3 cycle guard (param reassigned)": (CYC2, lambda r: [(e["line"], bool(e.get("e3"))) for e in r["exec"]] == [(4, True)]),
    "m4 non-const arg stays dynamic": (DYN, lambda r: [bool(e.get("dynamic_import")) for e in r["exec"]] == [True]),
    "m4 non-name value -> parse fail": (BAD4, lambda r: [p["line"] for p in r["parse_fail"]] == [1]),
    "m2 site unit (2 leaves -> 1 site record)": (SITE, lambda r: [(u["line"], u["kind"]) for u in r["unresolved_sink"]] == [(2, "outside")]),
    "m1 same-named plain defs union": (TWO, lambda r: sorted(e["line"] for e in r["exec"]) == [9, 10]),
})


def run_all(xs, scan, cases):
    out = {}
    for k, (src, chk) in cases.items():
        try:
            out[k] = bool(chk(scan(xs, src)))
        except Exception as e:   # 옛 kit에서 키·모양이 없어 깨지는 것도 '실패'로 적는다(이유와 함께)
            out[k] = "error: %s: %s" % (type(e).__name__, e)
    return out


new, old = load(NEW, "xs_new"), load(OLD, "xs_old")
res = {"new_kit": NEW, "old_kit": OLD,
       "new_adv": run_all(new, scan_new, ADV), "new_reg": run_all(new, scan_new, REG),
       "old_adv": run_all(old, scan_old, ADV), "old_reg": run_all(old, scan_old, REG)}
ok_new = all(v is True for v in list(res["new_adv"].values()) + list(res["new_reg"].values()))
ok_old = all(v is not True for v in res["old_adv"].values())
res["verdict"] = {"new_all_pass": ok_new, "old_all_adv_fail": ok_old}
for grp in ("new_adv", "new_reg", "old_adv", "old_reg"):
    for k, v in res[grp].items():
        print("%-8s %-5s %s" % (grp, "PASS" if v is True else "FAIL", k + ("" if v in (True, False) else "  [" + v + "]")))
print(json.dumps(res["verdict"]))
with open(os.path.join(HERE, "selftest_execstr_b1fix3.out.json"), "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
sys.exit(0 if ok_new and ok_old else 1)
