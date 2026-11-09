# F-22: ngspice 실행 cwd .spiceinit / HOME .spiceinit 읽기 순서. 결과 m1.jsonl. 넷리스트 없는 저항 하나, PDK 안 씀.
import json, os, shutil, subprocess, tempfile
EXE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m1.jsonl")
NET = "* t\nR1 a 0 1k\nV1 a 0 1\n.control\nop\nprint v(a)\necho NGBEH $ngbehavior\necho MARK $mark\nquit\n.endc\n.end\n"
HSA = "set ngbehavior=hsa\nset mark=from_%s\n"


def case(name, cwd_init, home_init, drop=()):
    r = tempfile.mkdtemp(prefix="op75_m1_")
    cwd = os.path.join(r, "cwd"); home = os.path.join(r, "home")
    os.makedirs(cwd); os.makedirs(home)
    if cwd_init is not None:
        open(os.path.join(cwd, ".spiceinit"), "w", newline="\n").write(cwd_init)
    if home_init is not None:
        open(os.path.join(home, ".spiceinit"), "w", newline="\n").write(home_init)
    open(os.path.join(cwd, "b.cir"), "w", newline="\n").write(NET)
    env = dict(os.environ)
    env.update(HOME=home, USERPROFILE=home)
    env.pop("SPICE_USERINIT_DIR", None)
    for d in drop:
        env.pop(d, None)
    p = subprocess.run([EXE, "-b", "b.cir"], cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
    txt = p.stdout + p.stderr
    rec = {"case": name, "rc": p.returncode,
           "lines": [l.strip() for l in txt.splitlines() if any(k in l for k in ("ompat", "NGBEH", "MARK", "v(a)"))]}
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    shutil.rmtree(r, ignore_errors=True)


open(OUT, "w").close()
case("none", None, None)
case("home_hsa_only", None, HSA % "home")
case("cwd_hsa_only", HSA % "cwd", None)
case("cwd_empty_home_hsa", "", HSA % "home")
case("cwd_hsa_home_other", HSA % "cwd", "set mark=from_home\n")
case("home_hsa_USERPROFILE_only", None, HSA % "home", drop=("HOME",))
case("home_hsa_HOME_only", None, HSA % "home", drop=("USERPROFILE",))


def case_dir(name, cwd_init):
    # SPICE_USERINIT_DIR 가 가리키는 폴더의 .spiceinit 과 cwd .spiceinit 의 순서
    r = tempfile.mkdtemp(prefix="op75_m1_")
    cwd = os.path.join(r, "cwd"); ud = os.path.join(r, "ud"); home = os.path.join(r, "home")
    os.makedirs(cwd); os.makedirs(ud); os.makedirs(home)
    open(os.path.join(ud, ".spiceinit"), "w", newline="\n").write(HSA % "userinit_dir")
    if cwd_init is not None:
        open(os.path.join(cwd, ".spiceinit"), "w", newline="\n").write(cwd_init)
    open(os.path.join(cwd, "b.cir"), "w", newline="\n").write(NET)
    env = dict(os.environ)
    env.update(HOME=home, USERPROFILE=home, SPICE_USERINIT_DIR=ud)
    p = subprocess.run([EXE, "-b", "b.cir"], cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
    txt = p.stdout + p.stderr
    rec = {"case": name, "rc": p.returncode,
           "lines": [l.strip() for l in txt.splitlines() if any(k in l for k in ("ompat", "NGBEH", "MARK"))]}
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    shutil.rmtree(r, ignore_errors=True)


case_dir("userinit_dir_only", None)
case_dir("cwd_empty_userinit_dir", "")
