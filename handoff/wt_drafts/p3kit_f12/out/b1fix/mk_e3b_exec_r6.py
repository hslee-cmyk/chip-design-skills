"""design 30 §10 E3B_AST(22fd126 판)를 그대로 잘라 e3b_ast.py로 쓰고, F2 계약 4(r6) 판 = 같은 블록 + 실행 문자열 내장 파일 읽기를 e3b_exec.py로 쓴다.
확장은 두 곳만 바꾼다(앵커가 정확히 한 번씩 있어야 한다): reads()의 파일 읽기에 내장 파일 읽기를 더함, 기록 줄 하나."""
import sys

s = open(r"C:\g409\out\design30.md", encoding="utf-8").read()
key = "E3B_AST=$(cat <<'PYEOF'\n"
i = s.index(key) + len(key)
j = s.index("PYEOF\n)", i)
base = s[i:j]
open(r"C:\g409\out\e3b_ast.py", "w", encoding="utf-8", newline="\n").write(base)

EXT = '''
sys.path.insert(0, r"C:\\Users\\HSLEE\\Documents\\Todoc\\fpga\\wt\\_drafts\\p3kit_f12")
import f12_execstr as xs   # F1 계약 1 (e) 실행 문자열 정의의 측정 구현(b1fix4)
EXEC_N = [0]

def exec_reads(tree):   # F2 계약 4 r6: 실행 문자열 내장 파일(채운 판마다)에 위 file_reads를 그대로 -- 자리 줄 = 문자열 상수 줄
    hit, meta, unres = xs.exec_strings_ex(tree)
    docs = xs.docstring_ids(tree)
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) in hit and id(n) not in docs:
            EXEC_N[0] += 1
            for _txt, sub in xs.exec_texts(n.value, meta[id(n)]):
                out |= {(n.lineno, "<EXEC-PARSE-ERROR>")} if sub is None else {(n.lineno, nm) for _l, nm in file_reads(sub)}
    out |= {(ln, "<EXEC-FSTRING>") for ln, _r, _s, kind in unres if kind == "stop_fstring"}
    return out

def reads(rev):'''
a1 = "\ndef reads(rev):"
a2 = "            res[p] = file_reads(ast.parse(src))\n"
a3 = 'print("E3b LIVE moved_out='
for a in (a1, a2, a3):
    assert base.count(a) == 1, a
ext = base.replace(a1, EXT, 1)
ext = ext.replace(a2, "            _t = ast.parse(src)\n            res[p] = file_reads(_t) | exec_reads(_t)\n", 1)
ext = ext.replace(a3, 'print("E3b EXEC strings_scanned=%d (B0+head)" % EXEC_N[0])\n' + a3, 1)
open(r"C:\g409\out\e3b_exec.py", "w", encoding="utf-8", newline="\n").write(ext)
print("e3b_ast", base.count("\n"), "lines; e3b_exec", ext.count("\n"), "lines")
