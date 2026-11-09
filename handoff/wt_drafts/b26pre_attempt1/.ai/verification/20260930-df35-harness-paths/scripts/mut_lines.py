"""V3 보강(auditor 작성): mutate_changed.py는 def만 변이하므로(이번 변경은 모듈 머리 문장) 바뀐 네 줄에 손 변이를 넣고
새 test 파일(그리고 살아남으면 전체 스위트)로 죽는지 본다. 복제본 C:/g14/mut에서만 쓰고, 변이마다 git checkout으로 되돌린다.
사용: python -P mut_lines.py <mut 복제본> <캐시> <out.jsonl>"""
import json, os, subprocess, sys
root, cache, out = sys.argv[1:4]
H = os.path.join(root, "workspaces", "run_harness.py")
L1 = "WORKSPACES_DIR = os.path.dirname(os.path.abspath(__file__))\n"
L2 = "_REPO_ROOT = os.path.dirname(WORKSPACES_DIR)\n"
L3 = 'ASSETS_DIR = os.path.join(_REPO_ROOT, "skills", "analog-gmid-design", "assets")\n'
L4 = "sys.path.insert(0, ASSETS_DIR)\n"
MAIN = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
MUTS = [
 ("M1 WORKSPACES_DIR 옛 리터럴", L1, 'WORKSPACES_DIR = r"' + MAIN + r'\workspaces"' + "\n"),
 ("M2 _REPO_ROOT dirname 빠짐", L2, "_REPO_ROOT = WORKSPACES_DIR\n"),
 ("M3 ASSETS_DIR 옛 리터럴", L3, 'ASSETS_DIR = r"' + MAIN + r'\skills\analog-gmid-design\assets"' + "\n"),
 ("M4 sys.path에 옛 리터럴", L4, 'sys.path.insert(0, r"' + MAIN + r'\skills\analog-gmid-design\assets")' + "\n"),
 ("M5 sys.path.insert 삭제", L4, "pass\n"),
 ("M6 WORKSPACES_DIR = getcwd", L1, "WORKSPACES_DIR = os.getcwd()\n"),
 ("M7 abspath 빠짐(__file__ 그대로)", L1, "WORKSPACES_DIR = os.path.dirname(__file__)\n"),
 ("M8 sys.path.append(끝에)", L4, "sys.path.append(ASSETS_DIR)\n"),
 ("M9 _REPO_ROOT 한 단계 더 위", L2, "_REPO_ROOT = os.path.dirname(os.path.dirname(WORKSPACES_DIR))\n"),
]
src0 = open(H, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in src0 else "\n"
def run(target):
    env = dict(os.environ, PYTHONPYCACHEPREFIX=os.path.join(os.path.dirname(out), "pyc_mut"), PYTHONPATH=cache)
    cmd = [sys.executable, "-P", "-m", "pytest", "-c", cache + "/pytest_gate.ini", "--rootdir=" + root, "--confcutdir=" + root,
           "--gmid-phase=2", "--gmid-strict=", target, "-q", "-p", "no:cacheprovider", "-x" if False else "-q"]
    p = subprocess.run(cmd, cwd=root, capture_output=True, timeout=900)
    tail = p.stdout.decode("utf-8", "replace").strip().splitlines()[-1:] 
    return p.returncode, tail
fo = open(out, "w", encoding="utf-8")
T = root + "/skills/analog-gmid-design/assets/tests/contracts/test_df35_harness_paths.py"
FULL = root + "/skills/analog-gmid-design/assets/tests"
for name, old, new in MUTS:
    o, n = old.replace("\n", nl), new.replace("\n", nl)
    assert src0.count(o) == 1, name
    open(H, "w", encoding="utf-8", newline="").write(src0.replace(o, n))
    rc, tail = run(T)
    rec = {"mutant": name, "new_test_rc": rc, "new_test_tail": tail}
    if rc == 0:
        rc2, tail2 = run(FULL)
        rec.update(full_rc=rc2, full_tail=tail2)
    rec["killed"] = rc != 0 or rec.get("full_rc", 0) != 0
    subprocess.run(["git", "-C", root, "checkout", "-q", "--", "workspaces/run_harness.py"], check=True)
    fo.write(json.dumps(rec, ensure_ascii=False) + "\n"); fo.flush()
    print(json.dumps(rec, ensure_ascii=False))
fo.close()
