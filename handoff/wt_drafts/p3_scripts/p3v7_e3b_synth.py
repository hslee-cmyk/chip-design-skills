"""Phase 3 design v7 -- E3(S1)·E3b(N1) 검증용 합성 커밋 생성(4차 검토 반영). 읽기 전용 측정의 보조 스크립트.

**스크래치 복제본 전용**: REPO가 C:/g95b 아래가 아니면 멈춘다(실제 저장소에 커밋하지 않는다 -- 메모리 '검증 agent의 git 실측은 격리 경로').
입력: REPO(a796468 복제본, 깨끗한 작업 트리), SIM(p3v6_order_shim_sim.py `bottom7 pull`이 만든 state_M9 디렉터리), OUT(JSON).
만드는 브랜치(모두 base = REPO의 HEAD):
  syn/m9       : A/*.py를 모의 M9 병합본으로 바꾼 커밋(SD가 나간 이름을 전부 재수출 -- F2 전 상태). E3b PASS 기대.
  syn/f2drop   : syn/m9에서 SD가 스스로 읽지 않는 재수출 이름을 지운 커밋(F1 없이 F2만 -- N1의 결함 상태). E3b FAIL 기대.
  syn/dropone  : syn/m9에서 재수출 이름 하나(SD가 읽지 않고, 추적 파일이 SD에서 읽는 것)만 지운 커밋. E3b FAIL 기대(그 이름만).
  syn/e3bnonascii: syn/dropone + 비ASCII 경로 파일 `workspaces/k/sd_전압.py`(`import stick_diagram as sd; sd.<그 이름>`). E3b FAIL 기대(두 파일).
  syn/e3clean  : base에서 sizing_recipe·topology_library·design_report와 E3가 찾는 제외 집합 밖 파일을 모두 지운 커밋. E3 PASS 기대.
  syn/e3nonascii: syn/e3clean + 비ASCII 경로 파일 `workspaces/k/probe_전압.py`(`import sizing_recipe`). E3 FAIL 기대(v6 E3는 PASS -- S1 재현).
결과(브랜치별 커밋 id, 지운 이름)는 OUT에 쓴다.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import symtable
import sys

REPO, SIM, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
real = os.path.realpath(REPO).replace("\\", "/").lower()
if not real.startswith("c:/g95b/"):
    sys.exit("REPO가 C:/g95b 밖이다: " + real)
A = os.path.join(REPO, "skills", "analog-gmid-design", "assets")
EXCL = re.compile(r"^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)")


def git(*a, check=True):
    r = subprocess.run(["git", "-c", "core.quotepath=off", "-C", REPO] + list(a), capture_output=True)
    if check and r.returncode != 0:
        sys.exit("git %s 실패: %s" % (" ".join(a), r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8", "replace").strip()


top = git("rev-parse", "--show-toplevel").replace("\\", "/").lower()
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


# ---- syn/m9
git("checkout", "-q", "--detach", BASE)
for p in os.listdir(A):
    if p.endswith(".py"):
        os.remove(os.path.join(A, p))
for p in os.listdir(SIM):
    if p.endswith(".py"):
        shutil.copy2(os.path.join(SIM, p), A)
commit("syn/m9", "scratch: 모의 M9 병합본")
SD = os.path.join(A, "stick_diagram.py")
sd_src = open(SD, encoding="utf-8").read()
tab = symtable.symtable(sd_src, "stick_diagram.py", "exec")
unread = {s.get_name() for s in tab.get_symbols() if s.is_imported() and not s.is_referenced()}
tree = ast.parse(sd_src)
TREE_STEMS = {p[:-3] for p in os.listdir(A) if p.endswith(".py")}
reexp = []  # (lineno, end_lineno, module, [names])
for n in tree.body:
    if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module in TREE_STEMS:
        reexp.append((n.lineno, n.end_lineno, n.module, [a.name for a in n.names if a.asname is None]))
res["sd_reexport_lines"] = len(reexp)
res["sd_unread_reexported"] = sorted(unread & {x for r in reexp for x in r[3]})


def rewrite(drop):
    lines = sd_src.splitlines(keepends=True)
    out, i = [], 0
    spans = {r[0]: r for r in reexp}
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
    return "".join(out)


# ---- syn/f2drop
open(SD, "w", encoding="utf-8", newline="").write(rewrite(set(res["sd_unread_reexported"])))
commit("syn/f2drop", "scratch: F2만(SD가 읽지 않는 재수출 삭제, F1 없음)")

# ---- syn/dropone: 추적 파일이 SD에서 `from stick_diagram import` 로 읽는 이름 중 SD가 읽지 않는 재수출 하나
git("checkout", "-q", "--detach", res["syn/m9"])
cand = None
grep = git("grep", "-l", "-F", "find_structural_symmetry_candidates", "--", "*.py", check=False).splitlines()
if "find_structural_symmetry_candidates" in res["sd_unread_reexported"]:
    cand = "find_structural_symmetry_candidates"
else:
    cand = res["sd_unread_reexported"][0]
res["dropone_name"] = cand
open(SD, "w", encoding="utf-8", newline="").write(rewrite({cand}))
commit("syn/dropone", "scratch: 재수출 하나(%s) 삭제" % cand)
# ---- syn/e3bnonascii: syn/dropone + 비ASCII 경로 파일이 SD에서 그 이름을 읽는다(E3b의 경로 처리 확인)
os.makedirs(os.path.join(REPO, "workspaces", "k"), exist_ok=True)
open(os.path.join(REPO, "workspaces", "k", "sd_전압.py"), "w", encoding="utf-8").write(
    "import stick_diagram as sd\nx = sd.%s\n" % cand)
commit("syn/e3bnonascii", "scratch: 비ASCII 경로 SD 이름 reader 하나")

# ---- syn/e3clean·syn/e3nonascii
git("checkout", "-q", "--detach", BASE)
mods = ("sizing_recipe", "topology_library", "design_report")
files = git("grep", "-l", "-E", "|".join(mods), "--", "*.py", check=False).splitlines()
rm = []
for p in files:
    if EXCL.search(p):
        continue
    src = open(os.path.join(REPO, p), "rb").read()
    try:
        t = ast.parse(src)
    except SyntaxError:
        rm.append(p)
        continue
    hit = False
    for n in ast.walk(t):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] in mods for a in n.names):
            hit = True
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module and n.module.split(".")[0] in mods:
            hit = True
        elif isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
            f = n.func
            fn = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if fn in ("import_module", "_import", "__import__") and n.args[0].value.split(".")[0] in mods:
                hit = True
    if hit:
        rm.append(p)
for m in mods:
    rm.append("skills/analog-gmid-design/assets/%s.py" % m)
rm = sorted(set(rm))
git("rm", "-q", "--", *rm)
res["e3clean_removed"] = len(rm)
commit("syn/e3clean", "scratch: shim 3파일과 importer 삭제")
os.makedirs(os.path.join(REPO, "workspaces", "k"), exist_ok=True)
open(os.path.join(REPO, "workspaces", "k", "probe_전압.py"), "w", encoding="utf-8").write("import sizing_recipe\n")
commit("syn/e3nonascii", "scratch: 비ASCII 경로 importer 하나")
git("checkout", "-q", "--detach", BASE)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "sd_unread_reexported"}, ensure_ascii=False))
print("unread re-exported:", len(res["sd_unread_reexported"]))
