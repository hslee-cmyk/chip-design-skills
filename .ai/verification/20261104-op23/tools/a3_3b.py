# -*- coding: utf-8 -*-
"""A3-3 변형 + 토큰 잠금 + 슬라이스 공칭. 사용: a3_3b.py <iso_v> <work> <exe> <out.json>
변형은 복제본의 기술자·역할 사본과 GMID_PDK_ROOT 뿌리 사본으로만 한다(원본 PDK 수정 없음)."""
import copy, glob, hashlib, json, os, shutil, subprocess, sys

ISO, WORK, EXE, OUT = sys.argv[1:5]
O = os.path.join(ISO, "skills/analog-gmid-design/tools/spice_oracle")
LUT = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2"
PDK = "C:/pdk/sky130_fd_pr"
RUN1 = os.path.join(os.path.dirname(WORK), "run1")
os.makedirs(WORK, exist_ok=True)
home = os.path.join(WORK, "home")
os.makedirs(home, exist_ok=True)
DESC = os.path.join(O, "descriptors/sky130.oracle_descriptor.json")
lf = lambda b: hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()  # noqa: E731
base = json.load(open(os.path.join(RUN1, "R3", "t.input.json"), encoding="utf-8"))
res = {}


def env(root=None):
    e = dict(os.environ)
    e["HOME"] = e["USERPROFILE"] = home
    for k in ("HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR"):
        e.pop(k, None)
    if root:
        e["GMID_PDK_ROOT"] = root
    return e


def run(inp, name, e):
    d = os.path.join(WORK, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    ip = os.path.join(d, "t.input.json")
    json.dump(inp, open(ip, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    r = subprocess.run([sys.executable, "-P", os.path.join(O, "oracle_run.py"), ip, os.path.join(d, "o"), "--bias", "free"], cwd=d, env=e, capture_output=True, text=True, encoding="utf-8", errors="replace")
    files = sorted(os.listdir(os.path.join(d, "o"))) if os.path.isdir(os.path.join(d, "o")) else []
    rej = [f for f in files if f.endswith(".reject.json")]
    out = {"rc": r.returncode, "files": files[:6]}
    if rej:
        j = json.load(open(os.path.join(d, "o", rej[0]), encoding="utf-8"))
        out.update(code=j["code"], stage=j["stage"], detail=str(j["detail"])[:400])
    else:
        out["code"] = None
        cj = glob.glob(os.path.join(d, "o", "*.compare.json"))
        if cj:
            c = json.load(open(cj[0], encoding="utf-8"))
            out["verdict"] = c["summary"]["verdict"]
            out["machine_dependent_refs_n"] = len(c.get("machine_dependent_refs") or [])
            out["machine_dependent_refs"] = sorted(x["ref"] for x in c.get("machine_dependent_refs") or [])
    return out


# 기준: 그대로
res["nominal_with_roles"] = run(base, "nom", env())
# 뿌리 사본(보조 입력 변형)
root = os.path.join(WORK, "root")
shutil.rmtree(root, ignore_errors=True)
for rel in ("cells/nfet_01v8/sky130_fd_pr__nfet_01v8.bins.csv", "cells/pfet_01v8/sky130_fd_pr__pfet_01v8.bins.csv",
            "cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice", "cells/nfet_01v8/sky130_fd_pr__nfet_01v8__mismatch.corner.spice",
            "cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.pm3.spice", "cells/pfet_01v8/sky130_fd_pr__pfet_01v8__mismatch.corner.spice", "models/parameters/lod.spice"):
    os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
    shutil.copyfile(os.path.join(PDK, rel), os.path.join(root, rel))
res["root_copy_unchanged"] = run(base, "rootcopy", env(root))
csv = os.path.join(root, "cells/nfet_01v8/sky130_fd_pr__nfet_01v8.bins.csv")
orig = open(csv, "rb").read()
open(csv, "ab").write(b"# changed\n")
res["aux_content_changed"] = run(base, "auxchg", env(root))
os.remove(csv)
res["aux_file_deleted"] = run(base, "auxdel", env(root))
open(csv, "wb").write(orig)
# 모델 파일 다른 뿌리(기록 뿌리 교차)
mf = os.path.join(root, "cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice")
mo = open(mf, "rb").read()
open(mf, "ab").write(b"* changed\n")
res["record_root_model_changed"] = run(base, "rootmodel", env(root))
open(mf, "wb").write(mo)
# 역할 선언의 보조 입력 sha 를 바꾼 변형 -> 역할 미선언 -> 모델 파일 -> 거부
dd = os.path.join(WORK, "descv")
shutil.rmtree(dd, ignore_errors=True)
shutil.copytree(os.path.join(O, "descriptors"), dd)
# 상대 경로 고정
ddoc = json.load(open(os.path.join(dd, "sky130.oracle_descriptor.json"), encoding="utf-8"))
for k in ("engine_decl",):
    ddoc[k]["path"] = os.path.abspath(os.path.join(O, "descriptors", ddoc[k]["path"])).replace("\\", "/")
for v in ddoc["extra_engine_decls"].values():
    v["path"] = os.path.abspath(os.path.join(O, "descriptors", v["path"])).replace("\\", "/")
ddoc["lut_record_root"]["location_decl"]["path"] = os.path.abspath(os.path.join(O, "descriptors", ddoc["lut_record_root"]["location_decl"]["path"])).replace("\\", "/")
rp = os.path.join(dd, "lut_file_roles", "605846960b6a5afd.lut_file_roles.json")
rd = json.load(open(rp, encoding="utf-8"))
rel0 = "cells/nfet_01v8/sky130_fd_pr__nfet_01v8.bins.csv"
rd["roles"][rel0]["sha256"] = "0" * 64
open(rp, "w", encoding="utf-8", newline="\n").write(json.dumps(rd, ensure_ascii=False, indent=1))
for ent in ddoc["lut_file_roles"]:
    if "605846960b6a5afd" in ent["path"]:
        ent["sha256"] = lf(open(rp, "rb").read())
dp2 = os.path.join(dd, "sky130.oracle_descriptor.json")
open(dp2, "w", encoding="utf-8", newline="\n").write(json.dumps(ddoc, ensure_ascii=False, indent=1))
i2 = copy.deepcopy(base)
i2["process"]["descriptor"] = {"path": dp2.replace("\\", "/"), "sha256": lf(open(dp2, "rb").read())}
res["role_pair_sha_changed"] = run(i2, "rolesha", env())
# 역할 전부 지운 변형(기술자 [])
d3 = copy.deepcopy(ddoc)
d3["lut_file_roles"] = []
dp3 = os.path.join(dd, "noroles.oracle_descriptor.json")
open(dp3, "w", encoding="utf-8", newline="\n").write(json.dumps(d3, ensure_ascii=False, indent=1))
i3 = copy.deepcopy(base)
i3["process"]["descriptor"] = {"path": dp3.replace("\\", "/"), "sha256": lf(open(dp3, "rb").read())}
res["roles_removed"] = run(i3, "noroles", env())
# 폭 슬라이스 공칭: R3 를 nmos/pmos 슬라이스 하나씩으로
nf = sorted(glob.glob(LUT + "/sky130_fd_pr__nfet_01v8__tt__W*_dc.npz"))[0]
pf = sorted(glob.glob(LUT + "/sky130_fd_pr__pfet_01v8__tt__W*_dc.npz"))[0]
i4 = copy.deepcopy(base)
i4["process"]["lut_files"] = [{"path": nf.replace("\\", "/"), "sha256": hashlib.sha256(open(nf, "rb").read()).hexdigest(), "kinds": {"nmos": None}},
                              {"path": pf.replace("\\", "/"), "sha256": hashlib.sha256(open(pf, "rb").read()).hexdigest(), "kinds": {"pmos": None}}]
res["slices_nominal"] = run(i4, "slices", env())
# 전체 슬라이스 32 + 결합 파일: 각 kind 전부
allf = sorted(glob.glob(LUT + "/sky130_fd_pr__*__tt__W*_dc.npz"))
i5 = copy.deepcopy(base)
i5["process"]["lut_files"] = [{"path": f.replace("\\", "/"), "sha256": hashlib.sha256(open(f, "rb").read()).hexdigest(), "kinds": {("nmos" if "nfet" in os.path.basename(f) else "pmos"): None}} for f in allf]
res["slices_all_32"] = run(i5, "slices32", env())
res["slices_all_32"]["n_files"] = len(allf)
# 위치 선언 뿌리와 다른 슬라이스(옆 선언 없는 생성기 sha -> 역할 미선언 -> 거부): 슬라이스 역할 지운 기술자
i6 = copy.deepcopy(i4)
i6["process"]["descriptor"] = i3["process"]["descriptor"]
res["slices_roles_removed"] = run(i6, "slicesnoroles", env())
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=0)[:6000])
# 토큰 잠금
tok = os.path.join(ISO, ".ai/verification/20261016-op1-baseline/op1_measurements/files/g8_dialect_tokens.draft.json")
td = json.load(open(tok, encoding="utf-8"))
print(str(list(td.keys()) if isinstance(td, dict) else type(td))[:300])
