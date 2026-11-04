# -*- coding: utf-8 -*-
"""OP-7b 판정 측정. 사용: a7.py <iso> <exe> <out_dir>
A7-2(R1~R10 입력 LUT 대 선언, 판정자 LF 재측정), A7-3 변형(.spiceinit 격리·모드 표·캐시 적중), 거부 경로(실제 oracle_run), A7-4(R1~R5 7 bias 1회, 7칸 비교는 op23 도구 재사용)."""
import copy, glob, hashlib, json, os, re, shutil, subprocess, sys

ISO, EXE, OUT = sys.argv[1:4]
S = os.path.join(ISO, "skills/analog-gmid-design")
O = os.path.join(S, "tools/spice_oracle")
BL = os.path.join(ISO, ".ai/verification/20261104-op1b")
sys.path.insert(0, O)
sys.path.insert(0, os.path.join(BL, "scripts"))
import numpy as np  # noqa: E402
from adapters.ngspice import Adapter, read as R  # noqa: E402
from core.bin_rule import check_compat  # noqa: E402
from core.descriptor import load_descriptor  # noqa: E402
from core.ir import Circuit, Resistor, VSource  # noqa: E402
from core.requests import Condition, Op, OpOutputs  # noqa: E402
from core.results import OracleError  # noqa: E402

lf = lambda b: hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()  # noqa: E731
DP = os.path.join(O, "descriptors/sky130.oracle_descriptor.json")
PDK = "C:/pdk/sky130_fd_pr"
res = {}
os.makedirs(OUT, exist_ok=True)


def save():
    json.dump(res, open(os.path.join(OUT, "a7.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)


def clean_env(home):
    e = dict(os.environ)
    os.makedirs(home, exist_ok=True)
    e["HOME"] = e["USERPROFILE"] = home
    for k in ("HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR"):
        e.pop(k, None)
    return e


# ---- A7-2 / B-2
decl = json.load(open(os.path.join(S, "assets/lut_v2_bin_rule.json"), encoding="utf-8"))
dset = set(decl["model_files_sha256"])
rows = {}
for i in range(1, 11):
    c = json.load(open(os.path.join(BL, "baseline", f"R{i}.converted.json"), encoding="utf-8"))["input"]
    got = set()
    recs = {}
    for f in c["process"]["lut_files"]:
        with np.load(f["path"], allow_pickle=False) as z:
            m = json.loads(str(z["meta_json"].item()))["model_files_sha256"]
        for k, key in f["kinds"].items():
            t = m if key is None else m[key]
            recs.update(t)
    got = {lf(open(os.path.join(PDK, r), "rb").read()) for r in recs}
    rows[f"R{i}"] = {"records": len(recs), "subset": got <= dset, "direct_record_in_decl": len(set(recs.values()) & dset)}
res["A7-2"] = {"decl_n": len(dset), "rows": rows, "found": sum(v["subset"] for v in rows.values()), "compat": decl["compat"], "simulator": decl["simulator"],
               "compat_sha_ok": hashlib.sha256(decl["compat"]["spiceinit_text"].encode()).hexdigest() == decl["compat"]["spiceinit_sha256"]}
save()

# ---- A7-3 변형: 실행 폴더 파일이 홈을 막는가(홈 파일에 표지 echo 를 넣어 읽힘 자체를 잰다)
D = load_descriptor(DP, env=os.environ)
ad = Adapter(exe=EXE)
modes = ad.capabilities()["compat_modes"]
compat = check_compat(decl, modes)
cir = Circuit(elements=(VSource("V1", "a", "0", 1.0), Resistor("R1", "a", "0", 1000.0)), role={"V1": "testbench", "R1": "circuit"}, meta={})
req = (Op(id="op", cond=Condition(temp_c=27.0, corner="tt"), exc=(), outputs=OpOutputs(devices="all", nodes=("a",), currents=())),)
POISON = "echo HOME_INIT_READ\nset ngbehavior=hsa\n"
home = os.path.join(OUT, "poison_home")
os.makedirs(home, exist_ok=True)
open(os.path.join(home, ".spiceinit"), "w", newline="\n").write(POISON)
saved = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR")}
os.environ["HOME"] = os.environ["USERPROFILE"] = home
for k in ("HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR"):
    os.environ.pop(k, None)
iso = {}


def run_case(name, c, cache=None):
    w = os.path.join(OUT, "iso", name)
    if not cache:
        shutil.rmtree(w, ignore_errors=True)
    try:
        r = ad.run(cir, req, D, w, None, cache, c)
        out = {"state": r.status.cache_state, "error": r.status.error, "V_a": r.by_request["op"].nodes["a"]}
    except OracleError as e:
        out = {"reject": e.code, "detail": e.detail, "stage": e.stage}
    log = open(os.path.join(w, "bench.log"), encoding="utf-8", errors="replace").read() if os.path.exists(os.path.join(w, "bench.log")) else ""
    out.update(spiceinit=open(os.path.join(w, ".spiceinit"), "rb").read().decode(), home_read="HOME_INIT_READ" in log, mode=R.compat_mode_of(log, modes),
               lines=[ln.strip() for ln in log.splitlines() if "ompatib" in ln])
    return out


iso["T7-9a_declared_default_poisoned_home"] = run_case("a", compat)
iso["T7-9b_none_poisoned_home"] = run_case("b", None)
hsa = check_compat({"compat": {"mode": "hsa", "spiceinit_text": modes["hsa"]["spiceinit_text"], "spiceinit_sha256": hashlib.sha256(modes["hsa"]["spiceinit_text"].encode()).hexdigest()}}, modes)
iso["hsa_mode_table"] = run_case("h", hsa)
bad = type(compat)(mode=compat.mode, spiceinit_text=modes["hsa"]["spiceinit_text"], spiceinit_sha256=hsa.spiceinit_sha256, log_line=compat.log_line)
iso["T7-9c_text_hsa_declared_default"] = run_case("c", bad)
os.environ["SPICE_USERINIT_DIR"] = home
iso["userinit_dir_set_declared_default"] = run_case("u", compat)
os.environ.pop("SPICE_USERINIT_DIR")
# 격리 없는 대조(판정자 직접 호출): 실행 폴더 파일이 없으면 홈이 먹는지
d = os.path.join(OUT, "iso", "ctl")
shutil.rmtree(d, ignore_errors=True)
os.makedirs(d)
open(os.path.join(d, "t.cir"), "w").write("* t\nV1 a 0 1\nR1 a 0 1k\n.control\nop\nquit\n.endc\n.end\n")
r = subprocess.run([EXE, "-b", "t.cir"], cwd=d, capture_output=True, text=True, errors="replace")
iso["control_no_run_folder_file"] = {"home_read": "HOME_INIT_READ" in r.stdout + r.stderr, "lines": [ln.strip() for ln in (r.stdout + r.stderr).splitlines() if "ompatib" in ln]}
# 캐시 적중: 슬롯 로그를 다른 모드로 변조해도 적중에서 대조하는가
cache = os.path.join(OUT, "iso", "cache")
shutil.rmtree(cache, ignore_errors=True)
c1 = run_case("k", compat, cache)
c2 = run_case("k", compat, cache)
slot = glob.glob(os.path.join(cache, "*"))[0]
t = open(os.path.join(slot, "bench.log"), encoding="utf-8", errors="replace").read()
open(os.path.join(slot, "bench.log"), "w", encoding="utf-8").write(t.replace("No compatibility mode selected!", "Compatibility modes selected: hs a"))
c3 = run_case("k", compat, cache)
iso["cache"] = {"first": c1, "hit": c2, "hit_with_tampered_log": c3, "keys_differ_by_mode_slots": None}
c4 = run_case("k2", hsa, cache)
iso["cache"]["hsa_same_bench_state"] = c4["state"]
iso["cache"]["slots"] = len(glob.glob(os.path.join(cache, "*")))
for k, v in saved.items():
    if v is None:
        os.environ.pop(k, None)
    else:
        os.environ[k] = v
res["A7-3"] = iso
save()

# ---- 거부 경로(실제 oracle_run, R1 입력)
base = json.load(open(os.path.join(BL, "baseline/R1.converted.json"), encoding="utf-8"))["input"]
root = os.path.join(OUT, "rej")
shutil.rmtree(root, ignore_errors=True)
os.makedirs(root)
ddoc = json.load(open(DP, encoding="utf-8"))
D_DIR = os.path.dirname(DP)
for k in ("engine_decl",):
    ddoc[k]["path"] = os.path.abspath(os.path.join(D_DIR, ddoc[k]["path"])).replace("\\", "/")
for v in ddoc["extra_engine_decls"].values():
    v["path"] = os.path.abspath(os.path.join(D_DIR, v["path"])).replace("\\", "/")
ddoc["lut_record_root"]["location_decl"]["path"] = os.path.abspath(os.path.join(D_DIR, ddoc["lut_record_root"]["location_decl"]["path"])).replace("\\", "/")
for ent in ddoc["lut_file_roles"]:
    ent["path"] = os.path.abspath(os.path.join(D_DIR, ent["path"])).replace("\\", "/")


def variant(name, decl_doc, desc_patch=None, raw_decl=None):
    d = os.path.join(root, name)
    os.makedirs(d)
    dd = copy.deepcopy(ddoc)
    if decl_doc is not None or raw_decl is not None:
        p = os.path.join(d, "decl.json")
        b = raw_decl if raw_decl is not None else json.dumps(decl_doc, ensure_ascii=False, indent=1).encode("utf-8")
        open(p, "wb").write(b)
        dd["bin_rule_decl"] = {"path": p.replace("\\", "/"), "sha256": lf(b)}
    else:
        dd["bin_rule_decl"]["path"] = os.path.abspath(os.path.join(D_DIR, dd["bin_rule_decl"]["path"])).replace("\\", "/")
    if desc_patch:
        desc_patch(dd)
    dp = os.path.join(d, "desc.json")
    b = json.dumps(dd, ensure_ascii=False, indent=1).encode("utf-8")
    open(dp, "wb").write(b)
    i = copy.deepcopy(base)
    i["process"]["descriptor"] = {"path": dp.replace("\\", "/"), "sha256": lf(b)}
    ip = os.path.join(d, "t.input.json")
    json.dump(i, open(ip, "w", encoding="utf-8"), ensure_ascii=False)
    r = subprocess.run([sys.executable, "-P", os.path.join(O, "oracle_run.py"), ip, os.path.join(d, "o"), "--bias", "free"], cwd=d, env=clean_env(os.path.join(d, "home")), capture_output=True, text=True, encoding="utf-8", errors="replace")
    files = sorted(os.listdir(os.path.join(d, "o"))) if os.path.isdir(os.path.join(d, "o")) else []
    rej = [f for f in files if f.endswith(".reject.json")]
    out = {"rc": r.returncode, "files": files[:5], "stderr": r.stderr[-200:]}
    if rej:
        j = json.load(open(os.path.join(d, "o", rej[0]), encoding="utf-8"))
        out.update(code=j["code"], stage=j["stage"], detail=str(j["detail"])[:220])
    return out


def mod(**kw):
    x = copy.deepcopy(decl)
    for k, v in kw.items():
        x[k] = v
    return x


rj = {}
rj["control_real_decl"] = variant("ok", None)
rj["mode_unknown"] = variant("mode_x", mod(compat={"mode": "nosuch", "spiceinit_text": "", "spiceinit_sha256": decl["compat"]["spiceinit_sha256"]}))
hs_text = modes["hsa"]["spiceinit_text"]
rj["mode_name_default_text_hsa"] = variant("mode_txt", mod(compat={"mode": "default", "spiceinit_text": hs_text, "spiceinit_sha256": hashlib.sha256(hs_text.encode()).hexdigest()}))
rj["sha_self_mismatch"] = variant("sha", mod(compat={"mode": "default", "spiceinit_text": "", "spiceinit_sha256": "0" * 64}))
rj["simulator_version"] = variant("ver", mod(simulator={"name": "ngspice", "version": "45"}))
rj["model_set_one_removed"] = variant("set", mod(model_files_sha256=decl["model_files_sha256"][1:]))
rj["model_empty"] = variant("empty_list", mod(model_files_sha256=[]))
rj["decl_file_empty_object"] = variant("empty_obj", {})
rj["decl_file_not_json"] = variant("notjson", None, raw_decl=b"not json")
rj["no_decl_field"] = variant("nofield", None, desc_patch=lambda d: d.pop("bin_rule_decl"))
rj["descriptor_field_empty_object"] = variant("field_empty", None, desc_patch=lambda d: d.__setitem__("bin_rule_decl", {}))
rj["descriptor_sha_wrong"] = variant("field_sha", None, desc_patch=lambda d: d["bin_rule_decl"].__setitem__("sha256", "0" * 64))
rj["hsa_decl_consistent_runs_in_hsa"] = variant("hsa_ok", mod(compat={"mode": "hsa", "spiceinit_text": hs_text, "spiceinit_sha256": hashlib.sha256(hs_text.encode()).hexdigest()}))
res["reject_paths"] = rj
save()
print(json.dumps(res, ensure_ascii=False, indent=0, default=str))
