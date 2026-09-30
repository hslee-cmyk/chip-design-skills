"""V3 보강: A/tests/tools/reg_check.py(도구 대상 밖)에 변이를 하나씩 넣고 test_reg_check.py를 V1 형태로 실행. 끝나면 원본 복원.
사용: mut_regcheck.py <복제본> <캐시> <out.jsonl>"""
import json, os, subprocess, sys
root, cache, out = sys.argv[1:4]
T = os.path.join(root, "skills/analog-gmid-design/assets/tests/tools/reg_check.py")
TEST = root + "/skills/analog-gmid-design/assets/tests/contracts/test_reg_check.py"
orig = open(T, "rb").read()
src = orig.decode("utf-8")
M = [
    ("control", None, None),
    ("stale_off", "if name and name not in engine_names:", "if False and name not in engine_names:"),
    ("disp_col_off", "            if disp_idx is None:", "            if False:"),
    ("disp_regex_loose", r'_DISP_RE = re.compile(r"^보류\(Phase [0-9]+[a-z]?\)")', r'_DISP_RE = re.compile(r"^보류")'),
    ("heading_count_off", "if heading_n is not None and heading_n != n_rows:", "if False:"),
    ("s1_count_off", "if not re.fullmatch(r\"\\d+\", d_txt) or int(d_txt) != n_rows:", "if False:"),
    ("s1_missing_off", "        if fname not in s1_d:", "        if False:"),
    ("methods_off", "names.add(node.name + \".\" + sub.name)", "pass"),
    ("harness_off", "if harness.is_file():", "if False:"),
    ("exit1_to_0", "    return 1" + chr(13), "    return 0" + chr(13)),
    ("no_sec7_ok", 'raise ValueError("레지스트리에 \'## 7.\' 절이 없다")', "return []"),
    ("orphan_s1_off", "if fname not in seen_files and d_txt != \"0\":", "if False:"),
]
env = dict(os.environ, PYTHONPATH=cache, PYTHONDONTWRITEBYTECODE="1", APPDATA="C:/Users/HSLEE/AppData/Roaming")
with open(out, "w", encoding="utf-8") as fo:
    for tag, a, b in M:
        if a is not None:
            if src.count(a) != 1:
                fo.write(json.dumps({"mutant": tag, "error": f"pattern count {src.count(a)}"}, ensure_ascii=False) + "\n"); fo.flush()
                continue
            open(T, "wb").write(src.replace(a, b).encode("utf-8"))
        try:
            p = subprocess.run(["C:/Python314/python.exe", "-P", "-m", "pytest", "-c", cache + "/pytest_gate.ini",
                                f"--rootdir={root}", f"--confcutdir={root}", "--gmid-phase=2", "--gmid-strict=", TEST,
                                "-q", "-p", "no:cacheprovider"], capture_output=True, env=env)
            last = p.stdout.decode("utf-8", "replace").strip().splitlines()[-1:]
            fo.write(json.dumps({"mutant": tag, "exit": p.returncode, "killed": p.returncode != 0 if a else None, "summary": last}, ensure_ascii=False) + "\n"); fo.flush()
        finally:
            open(T, "wb").write(orig)
print(open(out, encoding="utf-8").read())
