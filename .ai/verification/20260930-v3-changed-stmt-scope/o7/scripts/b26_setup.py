"""auditor p8 준비(20260930-v3-changed-stmt-scope 순서 7): 키트 setup_g109.py + mk_b1.py + measure_b26.py의 모의 커밋 부분을
scratch C:/g259/b26 에 다시 만든다. 저장소 쓰기 없음(audit worktree는 clone 원본으로 읽기만).

  C:/g259/b26/b1      = REV(0f23786) archive -> B34 코드 변경(build_b34)을 SD에 쓴다
  C:/g259/b26/sim     = audit worktree 격리 복제(--no-hardlinks --no-local, origin 제거, 빈 hooksPath)
  C:/g259/b26/scripts = _drafts/b26_scripts 사본(경로 C:/g83 -> C:/g259/b26, REPO -> sim 복제본)
모의 커밋(sim 복제본): B1 = REV + B34 코드, H4 = B1 + B26-1 card v4 head(b26v4_head.build_head("v4")). 결과 해시를 out/b26_mock.json에.
"""
import io, json, os, subprocess, sys, tarfile

SRC = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v3-changed-stmt-scope-audit"
DR = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts"
G = "C:/g259/b26"
CL = G + "/sim"
REV = "0f23786"


def git(*a):
    r = subprocess.run(["git"] + list(a), capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r.stdout


assert not os.path.exists(G), G
for d in ("b1", "scripts", "out", "emptyhooks"):
    os.makedirs(os.path.join(G, d))
git("clone", "--quiet", "--no-hardlinks", "--no-local", "-c", "core.longpaths=true", "-c", "core.autocrlf=false", SRC, CL)
git("-C", CL, "remote", "remove", "origin")
git("-C", CL, "config", "core.hooksPath", G + "/emptyhooks")
git("-C", CL, "config", "core.autocrlf", "false")
git("-C", CL, "config", "user.name", "sim")
git("-C", CL, "config", "user.email", "sim@example.invalid")
git("-C", CL, "checkout", "--quiet", "-B", "sim", REV)
tarfile.open(fileobj=io.BytesIO(git("-C", CL, "archive", REV))).extractall(G + "/b1", filter="data")
for f in ("sim_head.py", "v3_scope_classify.py", "mk_b1.py", "b26v4_head.py"):
    t = open(DR + "/b26_scripts/" + f, encoding="utf-8").read()
    t = t.replace(DR + "/b26_scripts", G + "/scripts").replace("C:/g83", G)
    t = t.replace('REPO = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"', 'REPO = "%s"' % CL)
    assert '"C:/g8' not in t and '"C:/g6' not in t and "chip-design-skills" not in t, f
    open(G + "/scripts/" + f, "w", encoding="utf-8", newline="\n").write(t)
for f in ("executed_lines.json", "junit_base.xml"):
    open(G + "/out/" + f, "wb").write(open(DR + "/v3_scripts/out/" + f, "rb").read())
print("setup ok", git("-C", CL, "rev-parse", "HEAD").decode().strip(), flush=True)
# mk_b1: b1의 SD를 B34판으로
r = subprocess.run([sys.executable, "-B", G + "/scripts/mk_b1.py"], capture_output=True)
print("mk_b1", r.returncode, r.stdout.decode("utf-8", "replace").strip(), r.stderr.decode("utf-8", "replace")[-500:], flush=True)
assert r.returncode == 0
sys.path.insert(0, G + "/scripts")
import b26v4_head as H  # noqa: E402  (sim_head BASE = C:/g259/b26/b1)
S = H.S


def commit_files(parent, files, msg, branch):
    git("-C", CL, "checkout", "--quiet", "-B", branch, parent)
    for rel, txt in files.items():
        p = os.path.join(CL, *rel.split("/"))
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(txt)
        git("-C", CL, "add", "--", rel)
    git("-C", CL, "commit", "--quiet", "-m", msg)
    return git("-C", CL, "rev-parse", "HEAD").decode().strip()


P0 = git("-C", CL, "rev-parse", REV).decode().strip()
B1 = commit_files(P0, {S.SD: S.BASEF[S.SD]}, "sim: B34 code (b1)", "sim-b1")
head4, _ = H.build_head("v4")
H4 = commit_files(B1, {p: t for p, t in head4.items() if t != S.BASEF.get(p)}, "sim: B26-1 v4 head", "sim-h4")
git("-C", CL, "checkout", "--quiet", "sim")
names = git("-C", CL, "diff", "--name-only", B1, H4).decode().split()
out = {"P0": P0, "B1": B1, "H4": H4, "B1_H4_paths": names,
       "P0_B1_paths": git("-C", CL, "diff", "--name-only", P0, B1).decode().split()}
json.dump(out, open("C:/g259/out/b26_mock.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(out), flush=True)
