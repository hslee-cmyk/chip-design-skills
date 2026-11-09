"""head 사본을 복사하고 변이 하나를 넣은 사본을 만든다(기존 test 전체로 죽는지 보려고).
사용: python -B mkmut.py <base 사본> <head 사본> <dst> <파일 rel> <def> <op> <path>"""
import ast, os, shutil, sys

BASE, HEAD, DST, REL, Q, OP, PATH = sys.argv[1:8]
sys.path.insert(0, BASE + "/tools/gates")
import mutate_changed as mc  # noqa: E402
import reachability as rch  # noqa: E402

if os.path.exists(DST):
    shutil.rmtree(DST)
shutil.copytree(HEAD, DST)
p = os.path.join(DST, REL)
raw = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in raw
src = raw.replace("\r\n", "\n")
fn = dict(rch.iter_defs(ast.parse(src)))[Q]
m = {(o, pp): f for o, pp, f in mc.mutants(fn, src)}
new = mc._replace_def(src, fn, m[(OP, PATH)])
assert new != src
if crlf:
    new = new.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(new)
print("mutant copy", DST, Q, OP, PATH)
