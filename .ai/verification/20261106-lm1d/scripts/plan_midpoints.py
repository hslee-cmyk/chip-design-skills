"""LM-1d S0·S1 -- 슬라이스별 앵커 2개 bin 중점 조합 계획·축 stub (card 20261106-lm1d interface 2절). ngspice 0.

엔진 식 재구현 0(엔진 `widths`·`load_lut_set`·`read_pdk_decl`·`core.file_sha256`을 부른다), 숫자 리터럴 0(기대 수는 `--expect`,
폭·L·격자·하한은 파일/선언에서), card 폴더 밖 import 0(엔진 공개 이름만). 이 파일은 compare_base_width.py·record_midpoints.py가
공용 함수(`sha_raw`, `build_spec`, `load_lut`, `list_root`, `index_new_files`)를 가져다 쓴다(같은 card 폴더 안).

실행: python -P plan_midpoints.py --location A/lut_v2_location.json --pdk-decl A/sky130_pdk_decl.json --l-grid A/sky130_lut_L_grid.json
        --work <T>/work --out <V> --expect nmos=18,pmos=12,N=120 [--verify]
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

import numpy as np

from gmid_engine.core import BoundedLRU, file_sha256, read_pdk_decl
from gmid_engine.lut import LutSpec, load_lut_set, resolve_lut_location, widths

# 장치 <-> kind, kind -> 기준 LUT 열 접미사: E/tests/lut/conftest.py:47-48 (REAL_DEVICE_KINDS, REAL_CAP_SUFFIX) 값을 그대로 인용.
# 셋째 사본이다(card spec '출처 기록 자리' 끝 문단) -- 두 원 자리가 pytest·패키지 상대 import를 요구해 직접 못 부른다. 정리는 LA-1 재점검 입력.
REAL_DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
REAL_CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))

DATA_SUBDIR = "verify_midpoints_w"                  # <D> (card 출처 기록 자리 표)
RECORD_SUBDIR = "verification/midpoints_w"          # <V>
GENERATOR_REL = "verification/slices_vdsat/sky130_dc_width_slices.py"
MIDPOINT_KEY = "verification_midpoints_um"          # 사용자 승인 목록 키 (A/sky130_lut_L_grid.json)
ANCHORS_PER_BIN = 2                                 # "앵커 2개 bin" 정의 (엔진 midpoint_checks._PAIR 와 같은 정의)


def sha_raw(path):
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def build_spec(pdk_decl_path):
    """PDK 선언(역할 이름)에서 격자·최소 finger 폭을 읽어 LutSpec. 선언에 없으면 read_pdk_decl이 거부(fail-closed)."""
    decl = read_pdk_decl(pdk_decl_path, BoundedLRU(16))
    grid = decl.value("manufacturing_grid_m")
    w_min = decl.value("min_finger_w_m")
    mins = tuple(sorted((kind, w_min) for _, kind in REAL_DEVICE_KINDS))
    return LutSpec(grid, mins, REAL_DEVICE_KINDS, REAL_CAP_SUFFIX), grid, w_min


def load_lut(loc, spec, verify_midpoints):
    return load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, bin_rule=loc.bin_rule_path, pdk_root=loc.pdk_root,
                        verify_midpoints=verify_midpoints)


def list_root(root):
    """<root> 아래 모든 파일 {상대 경로(/): raw sha256}."""
    out = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            p = os.path.join(dirpath, name)
            out[os.path.relpath(p, root).replace(os.sep, "/")] = sha_raw(p)
    return dict(sorted(out.items()))


def index_new_files(data_dir, grid):
    """<D>의 npz -> {(meta device, 폭 키): 경로}. 같은 키 둘이면 거부."""
    out = {}
    for name in sorted(os.listdir(data_dir)):
        if not name.endswith(".npz"):
            continue
        p = os.path.join(data_dir, name)
        with np.load(p) as z:
            device = json.loads(str(z["meta_json"]))["device"]
            w = float(z["W"])
        key = (device, round(w / grid))
        if key in out:
            raise RuntimeError("data dir: duplicate (device, w_key) %r" % (key,))
        out[key] = p
    return out


def parse_expect(text):
    pairs = dict(item.split("=") for item in text.split(","))
    return {k: int(v) for k, v in pairs.items()}


def generator_default(gen_path, option):
    """생성기 argparse 기본값(소스에서 읽음 -- 명령줄에 박지 않는다)."""
    src = open(gen_path, encoding="utf-8").read()
    m = re.search(r'add_argument\("%s",[^)]*?default=(?:r)?["\']?([^"\',)]+)["\']?' % re.escape(option), src)
    if not m:
        raise RuntimeError("generator default not found: %s" % option)
    return m.group(1)


class Stop(Exception):
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--location", required=True)
    ap.add_argument("--pdk-decl", required=True)
    ap.add_argument("--l-grid", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect", required=True)
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    mode = "verify" if a.verify else "generate"
    out = os.path.abspath(a.out)
    work = os.path.abspath(a.work)
    plan = {"mode": mode, "command": " ".join([sys.executable, "-P", os.path.abspath(__file__)] + sys.argv[1:])}
    try:
        build(a, mode, out, work, plan)
    except Stop as e:
        plan["stop"] = {"reason": str(e.args[0]), "detail": e.args[1:] and e.args[1] or None}
        if not os.path.exists(out) or not os.listdir(out):
            os.makedirs(out, exist_ok=True)
            with open(os.path.join(out, "plan.json"), "w", encoding="utf-8") as fh:
                json.dump(plan, fh, indent=1, ensure_ascii=False)
        print("STOP", json.dumps(plan["stop"], ensure_ascii=False, default=str))
        sys.exit(2)
    print("OK plan: N=%d cells=%d mode=%s" % (plan["n_expected"], plan["n_cells_expected"], mode))


def nonempty(path):
    return os.path.exists(path) and (not os.path.isdir(path) or bool(os.listdir(path)))


def build(a, mode, out, work, plan):
    expect = parse_expect(a.expect)
    plan["expect"] = {"values": a.expect, "source": "spec 20261106-lm1d '작성 전 실측' 표"}
    loc = resolve_lut_location(os.path.abspath(a.location), os.environ)
    root = loc.root
    repo = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(a.location)), "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True).stdout.strip()
    plan["base_commit"] = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True,
                                         check=True).stdout.strip()
    data_dir = os.path.join(root, DATA_SUBDIR)
    rec_dir = os.path.join(root, RECORD_SUBDIR)
    s0 = {}
    plan["s0"] = s0
    plan["root"], plan["data_dir"], plan["record_dir"], plan["pdk_root"] = root, data_dir, rec_dir, loc.pdk_root

    # ---- S0-1 생성기 sha
    gen = os.path.normpath(os.path.join(root, GENERATOR_REL))
    if not os.path.isfile(gen):
        raise Stop("S0-1 generator missing", gen)
    with open(loc.manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    s0["generator"] = {"path_rel_root": GENERATOR_REL, "sha256": sha_raw(gen), "sha256_lf": file_sha256(gen),
                       "manifest_generator_sha256": manifest["generator_sha256"]}
    if not (s0["generator"]["sha256"] == s0["generator"]["sha256_lf"] == manifest["generator_sha256"]):
        raise Stop("S0-1 generator sha mismatch", s0["generator"])
    # ---- S0-2 <root> 기존 파일 (생성 모드: <V>·<D> 가 이미 있고 비어 있지 않으면 멈춤) -- <V> 를 만들기 전에 센다
    if mode == "generate":
        if out != os.path.abspath(rec_dir):
            raise Stop("S0-2 --out is not <V>", [out, rec_dir])
        for p in (rec_dir, data_dir):
            if nonempty(p):
                raise Stop("S0-2 folder not empty", p)
        # ---- S0-5
        if nonempty(work):
            raise Stop("S0-5 work not empty", work)
    elif nonempty(out):
        raise Stop("verify --out not empty", out)
    pre = list_root(root)
    s0["preexisting_n"] = len(pre)
    # ---- S0-3 ngspice
    ng = generator_default(gen, "--ngspice")
    if not os.path.isfile(ng):
        raise Stop("S0-3 ngspice missing", ng)
    s0["ngspice"] = {"exe": ng, "exe_sha256": sha_raw(ng)}
    # ---- S0-4 pdk
    if not (loc.pdk_root and os.path.isdir(loc.pdk_root)):
        raise Stop("S0-4 pdk root missing", loc.pdk_root)
    # ---- S0-6 L 격자 파일 raw sha = cap L_source.sha256
    l_grid = os.path.abspath(a.l_grid)
    with np.load(loc.cap_npz_path) as z:
        cap_l_source = json.loads(str(z["meta_json"]))["L_source"]
    s0["l_grid"] = {"path": l_grid, "sha256": sha_raw(l_grid), "sha256_lf": file_sha256(l_grid), "key": MIDPOINT_KEY,
                    "cap_L_source_sha256": cap_l_source["sha256"]}
    if s0["l_grid"]["sha256"] != cap_l_source["sha256"]:
        raise Stop("S0-6 L grid raw sha != cap L_source sha", s0["l_grid"])

    # ---- S1 조합 계획
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "preexisting_files.json"), "w", encoding="utf-8") as fh:
        json.dump(pre, fh, indent=1)
    pdk_decl = os.path.abspath(a.pdk_decl)
    spec, grid, w_min = build_spec(pdk_decl)
    lut = load_lut(loc, spec, loc.midpoints_path)
    with open(l_grid, encoding="utf-8") as fh:
        mids_um = [float(x) for x in json.load(fh)[MIDPOINT_KEY]]
    device_of = {kind: dev for dev, kind in spec.device_kinds}
    src_of = {(s.kind, s.w_key): s for s in lut.provenance.slices}
    kinds = sorted(device_of)
    combos, n_cells_expected = [], 0
    per_kind_count = {}
    for kind in kinds:
        keys = widths(lut, kind)
        per_kind_count[kind] = len(keys)
        if len(keys) != expect[kind]:
            raise Stop("S1 widths count != expect", {"kind": kind, "got": len(keys), "expect": expect[kind]})
        for w_key in keys:
            sl = lut.slice_map[(kind, w_key)]
            src = src_of[(kind, w_key)]
            with np.load(src.path) as z:
                slice_meta = json.loads(str(z["meta_json"]))
            l_grid_m = sl.grids[0]
            bins = []
            for b, lb in enumerate(sl.l_bins.bins):
                members = [i for i, ab in enumerate(sl.l_bins.anchor_bin) if ab == b]
                if len(members) != ANCHORS_PER_BIN:
                    continue
                a0, a1 = l_grid_m[members[0]], l_grid_m[members[1]]
                inside = [u for u in mids_um if a0 < u * 1e-6 < a1]
                if len(inside) != 1:
                    raise Stop("S1 approved midpoint count in bin != 1",
                               {"kind": kind, "w_key": w_key, "model": lb.model, "inside": inside})
                u = inside[0]
                q = round(u / (grid * 1e6), 6)
                if q != int(q):
                    raise Stop("S1 midpoint not on manufacturing grid", {"u_um": u, "q": q})
                bins.append({"model": lb.model, "lmin": lb.lmin, "lmax": lb.lmax,
                             "wmin": sl.l_bins.w_bin[0], "wmax": sl.l_bins.w_bin[1],
                             "anchors": [round(a0 * 1e6, 6), round(a1 * 1e6, 6)],
                             "anchor_idx": members, "L_mid": u, "L_mid_grid_int": int(q)})
            combos.append({"kind": kind, "device": device_of[kind], "slice_device_meta": slice_meta["device"],
                           "w_key": w_key, "w_um": round(w_key * grid * 1e6, 6), "slice_file": src.path,
                           "slice_sha256": src.sha256, "bins": bins})
    n_expected = sum(len(c["bins"]) for c in combos)
    if n_expected != expect["N"]:
        raise Stop("S1 N != expect", {"got": n_expected, "expect": expect["N"]})
    for kind in kinds:
        b = lut.cap_map[kind].w_key
        sl = lut.slice_map[(kind, b)]
        n_bins = sum(1 for bi in range(len(sl.l_bins.bins))
                     if sum(1 for ab in sl.l_bins.anchor_bin if ab == bi) == ANCHORS_PER_BIN)
        n_cells_expected += n_bins * ANCHORS_PER_BIN * len(sl.grids[2])
    # ---- 축: 모든 슬라이스 VGS·VDS·VS array_equal
    axes0 = None
    for c in combos:
        with np.load(c["slice_file"]) as z:
            axes = tuple(np.asarray(z[k], dtype=float) for k in ("VGS", "VDS", "VS"))
        if axes0 is None:
            axes0, axes_file = axes, c["slice_file"]
        elif not all(np.array_equal(x, y) for x, y in zip(axes0, axes)):
            raise Stop("S1 axes differ between slices", c["slice_file"])
    # ---- 생성기 VS 확장식과 stub VS 비교 (생성기 :263-267 같은 식)
    vgs, vds, vs = axes0
    vs_step = float(np.round(np.diff(vs).mean(), 9))
    nvs = int(round((float(vgs.max()) - vs[0]) / vs_step)) + 1
    vs_gen = np.round(vs[0] + vs_step * np.arange(nvs), 9)
    if not np.array_equal(vs_gen, vs):
        raise Stop("S1 generator VS expansion != stub VS", [vs_gen.tolist(), vs.tolist()])
    l_used_um = sorted({bn["L_mid"] for c in combos for bn in c["bins"]})
    stub = os.path.join(out, "axis_stub.npz")
    stub_meta = {"stub": "axes only",
                 "L_source": {"path": l_grid, "sha256": s0["l_grid"]["sha256"], "sha256_lf": s0["l_grid"]["sha256_lf"],
                              "key": MIDPOINT_KEY},
                 "axes_source": {"file": axes_file, "sha256": sha_raw(axes_file)}}
    np.savez(stub, L=np.asarray(l_used_um) * 1e-6, VGS=vgs, VDS=vds, VS=vs, meta_json=json.dumps(stub_meta))
    # ---- 폭 목록 + S2 명령
    jobs = generator_default(gen, "--jobs")
    cmds = []
    for dev in [d for d, _k in spec.device_kinds]:
        ws = sorted({c["w_um"] for c in combos if c["device"] == dev})
        text = ",".join(repr(w) for w in ws)
        with open(os.path.join(out, "widths_%s.txt" % dev), "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        cmds.append([sys.executable, "-P", gen, "--ref-npz", stub, "--out", data_dir, "--work", work, "--jobs", jobs,
                     "--devices", dev, "--widths", text])
    plan.update({"n_expected": n_expected, "n_cells_expected": n_cells_expected, "per_kind_widths": per_kind_count,
                 "mids_um": mids_um, "units": {"L_mid": "um", "lmin/lmax/wmin/wmax": "m", "anchors": "um"},
                 "combos": combos, "stub_sha256": sha_raw(stub), "pdk_decl": pdk_decl,
                 "pdk_decl_sha256": sha_raw(pdk_decl), "min_finger_w_m": w_min, "manufacturing_grid_m": grid,
                 "lut_manifest_sha256": sha_raw(loc.manifest_path), "repo": repo, "s2_commands": cmds})
    with open(os.path.join(out, "plan.json"), "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
