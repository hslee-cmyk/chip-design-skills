"""B1 모양 F1(실행 문자열만 고치지 않은 F1 모의): F1 모의 트리의 B34 test에서 실행 문자열 상수 원문을 F1 base(M9 정정) 원문으로 되돌린다.
바깥 줄은 F1 모의 그대로(옛 판 d37ffc5 모양). 작업 트리 = 체크아웃된 F1 모의."""
import ast
import subprocess
import sys

R, BASE = sys.argv[1:3]
P = "skills/analog-gmid-design/assets/tests/contracts/test_b34_grammar_explicit.py"
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\p3kit_f12")
import f12_execstr as xs  # noqa: E402


def strs(src):
    t = ast.parse(src)
    hit, _m, _u = xs.exec_strings_ex(t)
    docs = xs.docstring_ids(t)
    return [n for n in ast.walk(t) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) in hit and id(n) not in docs]


bsrc = subprocess.run(["git", "-C", R, "show", BASE + ":" + P], capture_output=True, check=True).stdout.decode("utf-8")
path = R + "/" + P
hsrc = open(path, encoding="utf-8", newline="").read()
bs, hs = strs(bsrc), strs(hsrc)
assert len(bs) == len(hs) == 2, (len(bs), len(hs))
changed = [(b, h) for b, h in zip(bs, hs) if b.value != h.value]
assert len(changed) == 1, len(changed)
b, h = changed[0]
seg_b = ast.get_source_segment(bsrc, b)
seg_h = ast.get_source_segment(hsrc, h)
assert hsrc.count(seg_h) == 1
open(path, "w", encoding="utf-8", newline="").write(hsrc.replace(seg_h, seg_b, 1))
print("reverted exec string at head line", h.lineno, "(base line", b.lineno, ")")
