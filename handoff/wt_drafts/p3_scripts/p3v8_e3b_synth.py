"""Phase 3 design v8 -- 5차 검토 B2(E3b `pre_existing`이 표지 이름을 면제)·S2(판정 기록 스크립트 중 실제로 깨지는 것)·S1(E-LIB·E-INST가 F1·F2 뒤 도는가) 확인용 합성 커밋.

읽기 전용 측정의 보조 스크립트(초안 측정 -- 구현·test 기대값의 근거가 아니다, 작성자 != 검증자).
**스크래치 복제본 전용**: REPO가 C:/g113 아래가 아니면 멈춘다(실제 저장소에 커밋하지 않는다).
입력: REPO(0f23786 복제본, 깨끗한 작업 트리), SIM(p3v6_order_shim_sim.py `bottom7 pull`의 state_M9), OUT(JSON).
만드는 브랜치:
  syn/m9      : A/*.py = 모의 M9 병합본(SD가 나간 이름을 전부 재수출 -- F2 전). base = REPO HEAD.            E3b PASS 기대
  syn/f2drop  : syn/m9에서 SD가 스스로 읽지 않는 재수출을 지운 커밋(F1 없는 F2).                               E3b FAIL 기대
  syn/f1h     : syn/f2drop + 하네스 `run_harness.py`의 엔진 import만 모의 트리의 정의 파일로 바꾼 커밋(하네스 한 파일의 F1 모의)
  syn/b2base  : REPO HEAD + workspaces/zz/{star_reader,dyn_reader,parse_err}.py (5차 검토 B2의 B0')
  syn/b2head  : syn/b2base + SD에서 find_structural_symmetry_candidates def를 A/zz_moved_sym.py로 옮김(재수출 없음)
                + structural_symmetry_probe.py:10만 새 모듈로 갱신 (5차 검토 B2의 H)                        v7 E3b PASS(결함) / v8 E3b FAIL 기대
결과(브랜치별 커밋 id 등)는 OUT에 쓴다.
"""
import ast
import json
import os
import shutil
import subprocess
import symtable
import sys

REPO, SIM, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
real = os.path.realpath(REPO).replace("\\", "/").lower()
if not real.startswith("c:/g113/"):
    sys.exit("REPO가 C:/g113 밖이다: " + real)
A = os.path.join(REPO, "skills", "analog-gmid-design", "assets")
SDP = os.path.join(A, "stick_diagram.py")


def git(*a, check=True):
    r = subprocess.run(["git", "-c", "core.quotepath=off", "-C", REPO] + list(a), capture_output=True)
    if check and r.returncode != 0:
        sys.exit("git %s 실패: %s" % (" ".join(a), r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8", "replace").strip()


top = git("rev-parse", "--show-toplevel")
if os.path.realpath(top).replace("\\", "/").lower() != real:
    sys.exit("toplevel 불일치: " + top)
if git("status", "--porcelain"):
    sys.exit("작업 트리가 깨끗하지 않다")
BASE = git("rev-parse", "HEAD")
res = {"base": BASE}


def commit(branch, msg):
    git("add", "-A")
    git("-c", "user.name=scratch", "-c", "user.email=scratch@invalid", "commit", "-q", "-m", msg)
    res[branch] = git("rev-parse", "HEAD")
    git("branch", "-f", branch, "HEAD")


# ---- syn/m9 (p3v7_e3b_synth.py와 같은 절차)
git("checkout", "-q", "--detach", BASE)
for p in os.listdir(A):
    if p.endswith(".py"):
        os.remove(os.path.join(A, p))
for p in os.listdir(SIM):
    if p.endswith(".py"):
        shutil.copy2(os.path.join(SIM, p), A)
commit("syn/m9", "scratch: 모의 M9 병합본")
sd_src = open(SDP, encoding="utf-8").read()
tab = symtable.symtable(sd_src, "stick_diagram.py", "exec")
# v8 정정: SD가 '읽는' 이름 = 모든 유효 범위에서 모듈 전역으로 해석되는 참조 + 주석(문자열 주석 포함)의 이름.
# p3v7_e3b_synth.py는 모듈 최상위 표의 is_referenced()만 봐서 함수 몸체에서만 읽는 이름(load_topology·Transistor 등 19개)을
# '읽지 않음'으로 셌다 -- 그 모의 F2(syn/f2drop)는 실제 F2가 남길 import까지 지운 과대 삭제였다.
reads = set()


def _walk(tb, top):
    for s in tb.get_symbols():
        if s.is_referenced() and (top or s.is_global() or s.is_declared_global()):
            reads.add(s.get_name())
    for c in tb.get_children():
        _walk(c, False)


_walk(tab, True)
tree = ast.parse(sd_src)
for n in ast.walk(tree):
    anns = []
    if isinstance(n, (ast.arg, ast.AnnAssign)) and n.annotation is not None:
        anns.append(n.annotation)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.returns is not None:
        anns.append(n.returns)
    for a in anns:
        for m in ast.walk(a):
            if isinstance(m, ast.Name):
                reads.add(m.id)
            elif isinstance(m, ast.Constant) and isinstance(m.value, str):
                try:
                    reads |= {k.id for k in ast.walk(ast.parse(m.value, mode="eval")) if isinstance(k, ast.Name)}
                except SyntaxError:
                    pass
unread = {s.get_name() for s in tab.get_symbols() if s.is_imported()} - reads
v7_unread = {s.get_name() for s in tab.get_symbols() if s.is_imported() and not s.is_referenced()}
TREE_STEMS = {p[:-3] for p in os.listdir(A) if p.endswith(".py")}
reexp = []
for n in tree.body:
    if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module in TREE_STEMS:
        reexp.append((n.lineno, n.end_lineno, n.module, [a.name for a in n.names if a.asname is None]))
drop = unread & {x for r in reexp for x in r[3]}
res["sd_unread_reexported_n"] = len(drop)
res["sd_unread_reexported"] = sorted(drop)
res["v7_overdropped_reexports"] = sorted((v7_unread - unread) & {x for r in reexp for x in r[3]})
lines = sd_src.splitlines(keepends=True)
out, i, spans = [], 0, {r[0]: r for r in reexp}
while i < len(lines):
    ln = i + 1
    if ln in spans:
        a, b, mod, names = spans[ln]
        keep = [x for x in names if x not in drop]
        if keep:
            out.append("from %s import %s\n" % (mod, ", ".join(keep)))
        i = b
        continue
    out.append(lines[i])
    i += 1
open(SDP, "w", encoding="utf-8", newline="").write("".join(out))
commit("syn/f2drop", "scratch: F2만(SD가 읽지 않는 재수출 삭제, F1 없음)")

# ---- syn/f1h: 하네스의 엔진 import를 모의 트리의 정의 파일로(하네스 한 파일의 F1 모의)
def top_defs(path):
    t = ast.parse(open(path, encoding="utf-8").read())
    d = set()
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            d.add(n.name)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            for tg in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                if isinstance(tg, ast.Name):
                    d.add(tg.id)
    return d


owner = {}
for p in sorted(os.listdir(A)):
    if p.endswith(".py"):
        for nm in top_defs(os.path.join(A, p)):
            owner.setdefault(nm, []).append(p[:-3])
H = os.path.join(REPO, "workspaces", "run_harness.py")
hsrc = open(H, encoding="utf-8").read()
ht = ast.parse(hsrc)
hl = hsrc.splitlines(keepends=True)
ENG = {"sizing_recipe", "stick_diagram", "design_report", "topology_library"}
repl, f1h_map = {}, {}
for n in ht.body:
    if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module in ENG:
        by_mod = {}
        for a in n.names:
            ow = owner.get(a.name, [])
            if len(ow) != 1:
                sys.exit("하네스 이름 %s의 정의 파일이 하나가 아니다: %s" % (a.name, ow))
            by_mod.setdefault(ow[0], []).append(a.name)
            f1h_map[a.name] = ow[0]
        repl[n.lineno] = (n.end_lineno, "".join("from %s import %s\n" % (m, ", ".join(v)) for m, v in sorted(by_mod.items())))
out, i = [], 0
while i < len(hl):
    if i + 1 in repl:
        e, txt = repl[i + 1]
        out.append(txt)
        i = e
        continue
    out.append(hl[i])
    i += 1
open(H, "w", encoding="utf-8", newline="").write("".join(out))
res["f1h_map"] = f1h_map
commit("syn/f1h", "scratch: 하네스 import만 F1 모의")

# ---- syn/b2base·syn/b2head (5차 검토 B2 재현)
git("checkout", "-q", "--detach", BASE)
zz = os.path.join(REPO, "workspaces", "zz")
os.makedirs(zz, exist_ok=True)
open(os.path.join(zz, "star_reader.py"), "w", encoding="utf-8").write(
    "from stick_diagram import *\nv = find_structural_symmetry_candidates\n")
open(os.path.join(zz, "dyn_reader.py"), "w", encoding="utf-8").write(
    "import stick_diagram as sd\nname = 'find_structural_symmetry_candidates'\nv = getattr(sd, name)\n")
open(os.path.join(zz, "parse_err.py"), "w", encoding="utf-8").write(
    "import stick_diagram as sd\nv = sd.find_structural_symmetry_candidates(\n")
commit("syn/b2base", "scratch: star·동적 이름·파싱 오류 reader(B0')")
SDB = os.path.join(A, "stick_diagram.py")
src = open(SDB, encoding="utf-8").read()
t = ast.parse(src)
fn = [n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == "find_structural_symmetry_candidates"]
if len(fn) != 1:
    sys.exit("SD에 그 def가 하나가 아니다")
fn = fn[0]
start = (fn.decorator_list[0].lineno if fn.decorator_list else fn.lineno) - 1
L = src.splitlines(keepends=True)
open(os.path.join(A, "zz_moved_sym.py"), "w", encoding="utf-8", newline="").write("".join(L[start:fn.end_lineno]))
open(SDB, "w", encoding="utf-8", newline="").write("".join(L[:start] + L[fn.end_lineno:]))
P = os.path.join(REPO, "workspaces", "current-reuse-telescopic-ota-report", "structural_symmetry_probe.py")
ps = open(P, encoding="utf-8").read()
old = "from stick_diagram import load_topology, find_structural_symmetry_candidates\n"
if old not in ps:
    sys.exit("probe 10행 모양이 다르다")
open(P, "w", encoding="utf-8", newline="").write(ps.replace(
    old, "from stick_diagram import load_topology\nfrom zz_moved_sym import find_structural_symmetry_candidates\n"))
commit("syn/b2head", "scratch: def 이동(재수출 없음) + probe 갱신(H)")
git("checkout", "-q", "--detach", BASE)
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("sd_unread_reexported",)}, ensure_ascii=False))
