"""판정자 계획 JSON 생성. 모든 값은 PDK 파일·LUT meta·위치 선언에서 읽는다. 근거는 plan_basis.json에 함께 적는다.
입력 근거:
 - tlef, lut_grid_um: r2 meta `tlef`, `manufacturing_grid_um`
 - model_records: 슬라이스 32 + 위치 선언 4 세트 meta `model_files_sha256` 전부, 경로 = meta `pdk_root` + 키
 - set_versions: 각 세트 meta `ngspice`
 - bins: 그 kind의 tt.pm3 `.model` 카드의 lmin lmax wmin wmax (생성기 model_file와 같은 파일)
 - includes: 생성기 model_includes(devcell)와 같은 줄 (pfet만 lod), PDK 경로 = meta pdk_root
 - l_axes: 위치 선언 파일 + 그 kind 슬라이스 npz `L`
 - widths_m: manifest 슬라이스 W(meta w_m), w_ref_m: r2 npz meta
 - source.probes: kind마다 bin 표의 L 경계 전부(lmax = 이웃 lmin) 중 측정 L 축에 있는 것.
   슬라이스 = source_point. 칸 = VGS·VDS 절댓값 최대, VS 첫 index. 극성 = sign_convention(pfet driven negative, 본체 +VS/-VS, VS=0이면 0).
"""
import json, os, sys
import numpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ISO = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/op7a-iso"
sys.path.insert(0, ISO + "/.ai/verification/20261104-op7a/scripts")
import bin_rule_lib as B
from bins import bins_of

R = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2"
MD = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/work/meta_dump"
OUT = sys.argv[1]
man = json.load(open(R + "/manifest.json", encoding="utf-8"))
loc = json.load(open(ISO + "/skills/analog-gmid-design/assets/lut_v2_location.json", encoding="utf-8"))
def meta(f):
    return json.load(open(f"{MD}/{f}.json", encoding="utf-8"))["meta_json"]
loc_files = [v["path"] for k, v in loc["files"].items() if k != "manifest"]
r2 = meta(loc["files"]["cap_npz"]["path"])
grid_um = r2["manufacturing_grid_um"]
g = grid_um * 1e-6
pdk = r2["pdk_root"]
assert man["pdk_root"] == pdk

records, versions = [], {}
for f in [s["file"] for s in man["slices"]] + loc_files:
    m = meta(f)
    versions[f] = m.get("ngspice")
    mf = m["model_files_sha256"]
    items = []
    if all(isinstance(v, dict) for v in mf.values()):
        for dv in mf.values():
            items += list(dv.items())
    else:
        items = list(mf.items())
    for rel, sha in items:
        records.append([os.path.join(m["pdk_root"], rel.replace("/", "\\")), sha])
records = sorted({tuple(r) for r in records})

kinds, probes = [], []
for dev in ("nfet_01v8", "pfet_01v8"):
    sub = f"sky130_fd_pr__{dev}"
    pm3 = f"{pdk}\\cells\\{dev}\\{sub}__tt.pm3.spice"
    corner = f"{pdk}\\cells\\{dev}\\{sub}__mismatch.corner.spice"
    inc = []
    if dev.startswith("pfet"):
        inc.append(f'.include "{os.path.join(pdk, "models", "parameters", "lod.spice")}"')
    inc += [f'.include "{pm3}"', f'.include "{corner}"']
    bins = bins_of(pm3)
    slices = [s for s in man["slices"] if s["device"] == dev]
    widths = [meta(s["file"])["w_m"] for s in slices]
    axes = [{"npz": f"{R}/{p}", "scale_to_m": 1.0} for p in loc_files] + \
           [{"npz": f"{R}/{s['file']}", "scale_to_m": 1.0} for s in slices]
    kinds.append({"name": dev, "subckt": sub, "includes": inc, "bins": bins, "l_axes": axes,
                  "widths_m": widths, "w_ref_m": r2["w_ref_m"]})
    # L 축 합집합
    ls = []
    for a in axes:
        with numpy.load(a["npz"]) as z:
            ls.append([float(v) for v in z["L"]])
    anchors = B.anchor_set(ls, g)
    lmaxs = {B.grid_index(b["lmax"], g) for b in bins} & {B.grid_index(b["lmin"], g) for b in bins}
    pol = -1 if dev.startswith("pfet") else 1
    for l in anchors:
        if B.grid_index(l, g) not in lmaxs:
            continue
        w = B.source_point(l, widths, bins, g)
        s = next(s for s, ww in zip(slices, widths) if ww == w)
        m = meta(s["file"])
        layout = m["array_layout"]
        assert layout == "[L, VGS, VDS, VS]"
        axL = m["axes"]["L_m"]
        il = [i for i, x in enumerate(axL) if B.grid_index(x, g) == B.grid_index(l, g)]
        if len(il) != 1:
            raise SystemExit(f"L {l} not in slice axis {s['file']}")
        vgs = m["axes"]["VGS_V"]; vds = m["axes"]["VDS_V"]; vs = m["axes"]["VS_V"]
        ig = max(range(len(vgs)), key=lambda i: abs(vgs[i]))
        idd = max(range(len(vds)), key=lambda i: abs(vds[i]))
        assert "not normalized" in m["units"]["ID"] and m["units"]["ID"].startswith("A ")
        assert m["m"] == 1 and m["nf"] == 1
        rec = [[k, v] for k, v in m["model_files_sha256"].items()]
        probes.append({"kind": dev, "l_m": l, "widths_m": widths,
                       "lut": {"npz": f"{R}/{s['file']}", "member": "ID", "index": [il[0], ig, idd, 0], "scale_to_A": 1.0},
                       "sim": {"vgs": pol * vgs[ig], "vds": pol * vds[idd], "vs": 0.0,
                               "vb": 0.0 if vs[0] == 0.0 else (pol * -1) * vs[0] * 1.0,
                               "temp_c": m["temp_c_from_log"], "mult": m["m"], "include_records": rec},
                       "_slice": s["file"], "_geometry": m["geometry"], "_w_m": w})

plan = {"ngspice_exe": r2["ngspice_exe"], "date": "2026-11-04", "tlef": r2["tlef"], "lut_grid_um": grid_um,
        "model_records": [list(r) for r in records], "set_versions": versions, "kinds": kinds,
        "source": {"declared": "default", "probes": probes}}
json.dump(plan, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("records", len(records), "sets", len(versions), "probes", len(probes),
      "kinds", [(k["name"], len(k["bins"]), len(k["widths_m"]), k["w_ref_m"]) for k in kinds])
