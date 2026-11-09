import ast, sys
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\p3kit_f12")
import f12_execstr as xs
def lines(src):
    t = ast.parse(src); h, m, u = xs.exec_strings_ex(t)
    return sorted((n.lineno, n.value) for n in ast.walk(t) if id(n) in h), u
cases = {
 "git -c": ('import subprocess\nsubprocess.run(["git","clone","-c","core.x=1"])\n', []),
 "pytest -c": ('import sys\n[sys.executable,"-P","-m","pytest","-c","a.ini"]\n', []),
 "py -c": ('import sys\n[sys.executable,"-B","-c","import os"]\n', [(2,"import os")]),
 "PY name": ('import sys\nPY=sys.executable\nS="import a"\n[PY,"-c",S]\n', [(3,"import a")]),
 "python lit": ('["C:/Python314/python.exe","-X","utf8","-c","import b"]\n', [(1,"import b")]),
 "emit log": ('def emit(s=""):\n    f.write(s+X)\nemit("  !! no x")\nemit("import z")\n', [(4,"import z")]),
 "format": ('import sys\nSIM="import {mod} as m"\n[sys.executable,"-c",SIM.format(mod="q")]\n', [(2,"import {mod} as m")]),
 "percent": ('import sys\nT="import %s"\n[sys.executable,"-c",T % "q"]\n', [(2,"import %s")]),
 "dedent": ('import textwrap\nS="  import k"\nexec(textwrap.dedent(S))\n', [(2,"  import k")]),
 "fstring": ('import sys\nm="x"\n[sys.executable,"-c",f"import {m}"]\n', []),
 "param fwd": ('import sys\ndef run(s,*a):\n    return [sys.executable,"-c",s,*a]\nrun("import w")\n', [(4,"import w")]),
}
bad = 0
for k, (src, exp) in cases.items():
    got, u = lines(src)
    ok = got == exp
    bad += not ok
    print("OK " if ok else "BAD", k, got, u)
t = ast.parse('import sys\nSIM="import {mod} as m"\n[sys.executable,"-c",SIM.format(mod="q")]\n'); h,m,u = xs.exec_strings_ex(t)
n = [x for x in ast.walk(t) if id(x) in h][0]
print("tmpl parse", ast.dump(xs.parse_exec(n.value, m[id(n)]["tmpl"]))[:120])
print("broken template FAIL", xs.parse_exec("import {", {"format"}))
sys.exit(bad)
