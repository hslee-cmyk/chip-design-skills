"""V3 보강(auditor): 게이트 도구 mutate_changed.py는 .git 없는 사본에서 돌아 git을 읽는 test(test_ts6_probe_relocate
test_base_blob_reader_reads_the_base_tree)가 기준 실행에서 실패해 변이를 하나도 실행하지 못했다. 같은 V1 명령을 git이 있는
격리 복제본(<mut>)에서 변이마다 -x로 돌린다. 변이: 새 함수 본문 5개 + 18 호출 사이트마다 결과 2배 1개. 끝나면 원본 복원.
사용: python -P mut_sites.py <mut 복제본> <캐시> <wcmp_m.json> <out.jsonl> [<시작 번호>]"""
import json, os, subprocess, sys, time
mut, cache, wcmp, out = sys.argv[1:5]
start = int(sys.argv[5]) if len(sys.argv) > 5 else 0
F = os.path.join(mut, "skills", "analog-gmid-design", "assets", "sizing_recipe.py")
orig = open(F, "rb").read()
text = orig.decode("utf-8")
lines = text.split("\n")
NEWFN_RET = "    return L * ID / IDu"
ret_idx = [i for i, l in enumerate(lines) if l.rstrip("\r") == NEWFN_RET]
assert len(ret_idx) == 1, ret_idx
cr = "\r" if lines[ret_idx[0]].endswith("\r") else ""
muts = []
for tag, body in [("N1_return_None", "    return None"), ("N2_mul_IDu", "    return L * ID * IDu"),
                  ("N3_add", "    return L + ID / IDu"), ("N4_reassoc_L*(ID/IDu)", "    return L * (ID / IDu)"),
                  ("N5_abs", "    return abs(L * ID / IDu)")]:
    muts.append((tag, ret_idx[0], body + cr))
rows = json.load(open(wcmp, encoding="utf-8"))["rows"]
for r in sorted(rows, key=lambda r: r["merged_line"]):
    i = r["merged_line"] - 1
    l = lines[i]
    assert l.count("width_from_id_density(") == 1, (r, l)
    # 호출 전체를 괄호로 싸서 2배: 호출의 닫는 괄호는 균형으로 찾는다
    s = l.index("width_from_id_density(")
    d = 0
    for j in range(s, len(l)):
        if l[j] == "(":
            d += 1
        elif l[j] == ")":
            d -= 1
            if d == 0:
                break
    new = l[:s] + "(2.0 * " + l[s:j + 1] + ")" + l[j + 1:]
    muts.append(("S%d_%s_x2" % (r["base_line"], r["function"]), i, new))
env = dict(os.environ, PYTHONPATH=cache, PYTHONDONTWRITEBYTECODE="1")
for k, (tag, i, new) in enumerate(muts):
    if k < start:
        continue
    ls = list(lines)
    ls[i] = new
    open(F, "wb").write("\n".join(ls).encode("utf-8"))
    pyc = os.path.join(os.path.dirname(out), "pyc_mut_%d" % k)
    env["PYTHONPYCACHEPREFIX"] = pyc
    cmd = ["C:/Python314/python.exe", "-P", "-m", "pytest", "-c", cache + "/pytest_gate.ini", "--rootdir=" + mut,
           "--confcutdir=" + mut, "--gmid-phase=2", "--gmid-strict=", mut + "/skills/analog-gmid-design/assets/tests",
           "-x", "-q", "-p", "no:cacheprovider"]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, env=env, timeout=900)
        rc = p.returncode
        tail = p.stdout.decode("utf-8", "replace").strip().splitlines()
        failed = [x for x in tail if x.startswith("FAILED") or x.startswith("ERROR")]
        summ = tail[-1] if tail else ""
    except subprocess.TimeoutExpired:
        rc, failed, summ = "timeout", [], ""
    open(F, "wb").write(orig)
    rec = {"k": k, "mutant": tag, "line": i + 1, "rc": rc, "killed": rc != 0, "first_failed": failed[:1],
           "summary": summ, "elapsed_s": round(time.time() - t0, 1)}
    with open(out, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False), flush=True)
open(F, "wb").write(orig)
print("restored", open(F, "rb").read() == orig)
