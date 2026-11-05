"""거부 경로 실측: 입력 복제본(작은 npz: L, meta_json만, 또는 plan 사본)을 변형해 measure_bin_rule.py를 그대로 돌린다. 원본 불변.
결과는 케이스마다 rejects.jsonl에 append."""
import copy, json, os, subprocess, sys, shutil
import numpy
T = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit"
W2 = T + "/work2"
S = T + "/op7a-iso2/.ai/verification/20261104-op7a/scripts/measure_bin_rule.py"
OUT = W2 + "/rej"
plan0 = json.load(open(W2 + "/plan2.json", encoding="utf-8"))
ONLY = set(sys.argv[1:])
cells = {}
for ln in open(W2 + "/run1/source_modes.jsonl", encoding="utf-8"):
    r = json.loads(ln)
    if "set" in r:
        cells.setdefault(r["set"], []).append(r)
res_path = W2 + "/rejects.jsonl"

def load(npz):
    with numpy.load(npz) as z:
        return numpy.array(z["L"]), json.loads(str(z["meta_json"]))

def small(name, L, meta):
    os.makedirs(OUT + "/npz", exist_ok=True)
    p = f"{OUT}/npz/{name}.npz"
    numpy.savez(p, L=L, meta_json=numpy.array(json.dumps(meta)))
    return p

def key_of(meta, l_m):
    for k in meta["model_bin_per_L"]:
        if round(float(k) * 1e-6 / 5e-9) == round(l_m / 5e-9):
            return k
    raise SystemExit("no key")

def run(name, plan, expect):
    d = f"{OUT}/{name}"
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    pp = d + "/plan.json"
    json.dump(plan, open(pp, "w", encoding="utf-8"), ensure_ascii=False)
    decl = d + "/decl.json"
    e = dict(os.environ); e["OPENBLAS_NUM_THREADS"] = "1"; e["PYTHONPYCACHEPREFIX"] = T + "/pyc"
    p = subprocess.run([sys.executable, S, "--plan", pp, "--out", d + "/o", "--decl-out", decl], capture_output=True, env=e)
    err = p.stderr.decode("utf-8", errors="replace").strip().splitlines()
    rec = {"case": name, "rc": p.returncode, "stderr_last": (err[-1][:300] if err else ""), "decl_written": os.path.exists(decl), "expect": expect}
    rec["hit"] = expect in rec["stderr_last"] if expect != "ok" else p.returncode == 0
    open(res_path, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
    shutil.rmtree(d + "/o", ignore_errors=True)
    print(rec, flush=True)

def wanted(n):
    return not ONLY or n in ONLY

sl0 = plan0["slices"][0]
L0, m0 = load(sl0["npz"])
c0 = cells[sl0["set"]][0]

if wanted("no_per_l"):
    m = copy.deepcopy(m0); del m["model_bin_per_L"]
    pl = copy.deepcopy(plan0); pl["slices"][0]["npz"] = small("no_per_l", L0, m)
    run("no_per_l", pl, "source_record_missing")
if wanted("cell_key_gone"):
    m = copy.deepcopy(m0); del m["model_bin_per_L"][key_of(m0, c0["l_m"])]
    pl = copy.deepcopy(plan0); pl["slices"][0]["npz"] = small("cell_key_gone", L0, m)
    run("cell_key_gone", pl, "source_record_missing")
if wanted("no_mode"):
    m = copy.deepcopy(m0); m["model_bin_per_L"][key_of(m0, c0["l_m"])] = "bogus"
    pl = copy.deepcopy(plan0); pl["slices"][0]["npz"] = small("no_mode", L0, m)
    run("no_mode", pl, "source_record_no_mode")
if wanted("mixed"):
    m = copy.deepcopy(m0); m["model_bin_per_L"][key_of(m0, c0["l_m"])] = c0["hsa"]
    pl = copy.deepcopy(plan0); pl["slices"][0]["npz"] = small("mixed", L0, m)
    run("mixed", pl, "source_record_mixed")
if wanted("differs"):
    pl = copy.deepcopy(plan0)
    for i, sl in enumerate(pl["slices"]):
        L, m = load(sl["npz"])
        for c in cells[sl["set"]]:
            m["model_bin_per_L"][key_of(m, c["l_m"])] = c["hsa"]
        sl["npz"] = small(f"differs{i}", L, m)
    run("differs", pl, "source_mode_differs")
if wanted("include"):
    m = copy.deepcopy(m0)
    k = next(x for x in m["model_files_sha256"] if x.endswith("tt.pm3.spice"))
    del m["model_files_sha256"][k]
    pl = copy.deepcopy(plan0); pl["slices"][0]["npz"] = small("include", L0, m)
    run("include", pl, "include_not_recorded")
cs0 = plan0["combined_sets"][0]
if wanted("combined_differs") or wanted("combined_gone"):
    Lc, mc = load(cs0["npz"])
    if wanted("combined_differs"):
        m = copy.deepcopy(mc)
        tab = m["model_bin_per_L_at_w_ref"]["nfet_01v8"]
        k = next(iter(tab)); tab[k]["model"] = "bogus"
        pl = copy.deepcopy(plan0); pl["combined_sets"][0]["npz"] = small("combined_differs", Lc, m)
        run("combined_differs", pl, "combined_bin_differs")
    if wanted("combined_gone"):
        m = copy.deepcopy(mc); del m["model_bin_per_L_at_w_ref"]["nfet_01v8"]
        pl = copy.deepcopy(plan0); pl["combined_sets"][0]["npz"] = small("combined_kind_gone", Lc, m)
        run("combined_kind_gone", pl, "combined_bin_missing")
bs0 = plan0["bound_sets"][0]
if wanted("cap_differs") or wanted("cap_gone"):
    Lb, mb = load(bs0["npz"])
    if wanted("cap_differs"):
        m = copy.deepcopy(mb); m["cap_npz_sha256"] = "0" * 64
        pl = copy.deepcopy(plan0); pl["bound_sets"][0]["npz"] = small("cap_differs", Lb, m)
        run("cap_differs", pl, "cap_bind_differs")
    if wanted("cap_gone"):
        m = copy.deepcopy(mb); del m["cap_npz_sha256"]
        pl = copy.deepcopy(plan0); pl["bound_sets"][0]["npz"] = small("cap_gone", Lb, m)
        run("cap_gone", pl, "cap_bind_missing")
if wanted("both_modes"):
    # 두 모드 다 가리킴: 측정 경로에서 칸의 default = hsa를 만들려면 대조가 안 갈려야 한다. 래퍼로 nfet 대조 cwd의 .spiceinit만 지운다.
    os.makedirs(OUT, exist_ok=True)
    wp = OUT + "/wrap.py"
    open(wp, "w", encoding="utf-8").write(
        "import os,subprocess,sys\n"
        "if os.getcwd().replace(chr(92),'/').endswith('cwd_nfet_01v8/cwd') and os.path.exists('.spiceinit'):\n"
        "    os.remove('.spiceinit')\n"
        f"p=subprocess.run([{plan0['ngspice_exe']!r}]+sys.argv[1:])\nsys.exit(p.returncode)\n")
    bat = OUT + "/wrap.bat"
    open(bat, "w").write(f'@"{sys.executable}" "{wp}" %*\r\n')
    pl = copy.deepcopy(plan0); pl["ngspice_exe"] = bat
    run("both_modes", pl, "control_undetermined")
if wanted("empty_lists"):
    pl = copy.deepcopy(plan0); pl["combined_sets"] = []; pl["bound_sets"] = []
    run("empty_lists", pl, "ok")
if wanted("partial_slices"):
    pl = copy.deepcopy(plan0)
    pl["slices"] = [next(s for s in pl["slices"] if s["kind"] == k) for k in ("nfet_01v8", "pfet_01v8")]
    run("partial_slices", pl, "ok")
if wanted("kind_slice_gone"):
    pl = copy.deepcopy(plan0); pl["slices"] = [s for s in pl["slices"] if s["kind"] == "nfet_01v8"]
    run("kind_slice_gone", pl, "source_record_missing")
if wanted("plan_field_gone"):
    pl = copy.deepcopy(plan0); del pl["combined_sets"]
    run("plan_field_gone", pl, "source_condition_unresolved")
print("done")
