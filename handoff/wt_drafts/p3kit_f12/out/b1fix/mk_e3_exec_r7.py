"""F2 r7 측정 전용: design 30 §10 E3_AST를 그대로 잘라 e3_ast.py로 쓰고, F2 계약 3(r7) 판 = 같은 블록 + 실행 문자열 내장 파일(F1 계약 1 (e))에
같은 E3 식을 적용한 판을 e3_exec.py로 쓴다. 확장은 앵커 두 곳만 바꾼다(각 정확히 1회):
  (1) `iso, rev = sys.argv[1], sys.argv[2]` 뒤에 kit import와 exec_e3() 정의, (2) 파일마다 블록 판정 루프가 끝난 자리에 exec_e3(tree, p) 호출.
내장 파일 적중 = `exec-stmt`·`exec-call`(자리 줄 = 문자열 상수 줄), 파싱 실패 = `EXEC-PARSE-ERROR`, (s1)·(s2) f-string 잎 = `EXEC-FSTRING` --
모두 stdout(셸이 FAIL로 센다 -- 블록의 PARSE-ERROR와 같은 취급, D-9 제외는 블록 그대로). 규칙 밖 자리·스캔 수는 stderr `RECORD`(판정 아님).
    python mk_e3_exec_r7.py <design30.md> <out dir> <kit dir>
"""
import sys

DES, OUT, KIT = sys.argv[1:4]
s = open(DES, encoding="utf-8").read()
key = "E3_AST=$(cat <<'PYEOF'\n"
i = s.index(key) + len(key)
j = s.index("PYEOF\n)", i)
base = s[i:j]
open(OUT + "/e3_ast.py", "w", encoding="utf-8", newline="\n").write(base)

EXT = '''iso, rev = sys.argv[1], sys.argv[2]
sys.path.insert(0, %r)
import f12_execstr as xs   # F1 계약 1 (e) 실행 문자열 정의의 측정 구현(b1fix4)
EXEC_N = [0]

def exec_e3(tree, p):   # F2 계약 3 r7: 실행 문자열 내장 파일(채운 판마다)에 위 E3 식을 그대로 -- 자리 줄 = 문자열 상수 줄
    hit, meta, unres = xs.exec_strings_ex(tree)
    docs = xs.docstring_ids(tree)
    for c in ast.walk(tree):
        if isinstance(c, ast.Constant) and isinstance(c.value, str) and id(c) in hit and id(c) not in docs:
            EXEC_N[0] += 1
            for _txt, sub in xs.exec_texts(c.value, meta[id(c)]):
                if sub is None:
                    print("EXEC-PARSE-ERROR %%s:%%d" %% (p, c.lineno)); continue
                for n in ast.walk(sub):
                    if isinstance(n, ast.Import) and any(a.name.split(".")[0] in mods for a in n.names):
                        print("exec-stmt %%s:%%d" %% (p, c.lineno))
                    elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module and n.module.split(".")[0] in mods:
                        print("exec-stmt %%s:%%d" %% (p, c.lineno))
                    elif isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Constant) \\
                            and isinstance(n.args[0].value, str):
                        f = n.func
                        fn = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
                        if fn in ("import_module", "_import", "__import__") and n.args[0].value.split(".")[0] in mods:
                            print("exec-call %%s:%%d" %% (p, c.lineno))
    for ln, route, shape, kind in unres:
        if kind == "stop_fstring":
            print("EXEC-FSTRING %%s:%%d" %% (p, ln))
        else:
            print("RECORD outside %%s:%%d %%s %%s %%s" %% (p, ln, route, shape, kind), file=sys.stderr)
''' % KIT
a1 = "iso, rev = sys.argv[1], sys.argv[2]\n"
a2 = '                print("call %s:%d" % (p, n.lineno))\nsys.exit(3 if bad else 0)'
a3 = "sys.exit(3 if bad else 0)"
for a in (a1, a2):
    assert base.count(a) == 1, a
assert base.count(a3) == 1
ext = base.replace(a1, EXT, 1)
ext = ext.replace(a2, '                print("call %s:%d" % (p, n.lineno))\n    exec_e3(tree, p)\n'
                  'print("RECORD exec_strings_scanned=%d rev=%s" % (EXEC_N[0], rev), file=sys.stderr)\nsys.exit(3 if bad else 0)', 1)
open(OUT + "/e3_exec.py", "w", encoding="utf-8", newline="\n").write(ext)
print("e3_ast", base.count("\n"), "lines; e3_exec", ext.count("\n"), "lines")
