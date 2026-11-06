"""LM-1d S3 관문 G-a~G-h + 출처 기록 (card 20261106-lm1d interface 4절). ngspice 0.

값은 모두 plan.json·생성 파일·진행 로그·compare.json에서 읽는다(손 값 0). n = N일 때만 출처 기록을 쓴다.
어긋나면 <plan 폴더>/record_stop.json 에 어긋난 항목을 쓰고 끝(출처 기록 파일 0).

실행: python -P record_midpoints.py --plan <V>/plan.json --data <D> --compare <V>/compare.json --out A/lut_v2_midpoints_w.provenance.json
"""
import argparse
import json
import math
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import plan_midpoints as pm                      # 같은 card 폴더 (공용 함수)

SHOWMOD_REL_TOL = 1e-12        # 생성기 showmod 대조와 같은 꼴 (생성기 :129)
BOUND_KEYS = ("lmin", "lmax", "wmin", "wmax")
META_SAME_KEYS = ("model_files_sha256", "ngspice", "temp_c_from_log", "corner", "nf", "m", "geometry")
TIME_LINE = re.compile(r"^(\S+) W=(\S+) L=(\S+) ([0-9.]+)s elapsed=\d+s$")
DONE_LINE = re.compile(r"^# done total ([0-9.]+)s$")


def close(x, y):
    return math.isclose(x, y, rel_tol=SHOWMOD_REL_TOL, abs_tol=0.0)


def key_of(um):
    return "%g" % round(um, 6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--compare", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    plan_path = os.path.abspath(a.plan)
    vdir = os.path.dirname(plan_path)
    with open(plan_path, encoding="utf-8") as fh:
        plan = json.load(fh)
    stop_path = os.path.join(vdir, "record_stop.json")
    if plan["mode"] != "generate":
        with open(stop_path, "w", encoding="utf-8") as fh:
            json.dump({"reason": "plan_mode_not_generate", "mode": plan["mode"]}, fh, indent=1)
        print("STOP plan_mode_not_generate")
        sys.exit(2)

    data = os.path.abspath(a.data)
    grid = plan["manufacturing_grid_m"]
    idx = pm.index_new_files(data, grid)
    failures = []

    def fail(gate, where, msg):
        failures.append({"gate": gate, "where": where, "msg": msg})

    combos = plan["combos"]
    n_total = plan["n_expected"]
    mids_m = np.asarray(sorted(plan["mids_um"])) * 1e-6
    gen_sha = plan["s0"]["generator"]["manifest_generator_sha256"]
    if len(idx) != len(combos):
        fail("G-f", "data", "file count %d != slices %d" % (len(idx), len(combos)))
    n_pass, files, models_by_device, versions = 0, [], {}, set()
    for c in combos:
        where = "%s w_key=%d" % (c["kind"], c["w_key"])
        path = idx.get((c["slice_device_meta"], c["w_key"]))
        if path is None:
            fail("G-b", where, "no data file")
            continue
        slice_bad = len(failures)
        with np.load(path) as zn, np.load(c["slice_file"]) as zs:
            mn, ms = json.loads(str(zn["meta_json"])), json.loads(str(zs["meta_json"]))
            for ax in ("VGS", "VDS", "VS"):
                if not np.array_equal(zn[ax], zs[ax]):
                    fail("G-b", where, "axis %s != slice" % ax)
            if not np.array_equal(zn["L"], mids_m):
                fail("G-b", where, "L axis != approved midpoints")
            if not np.array_equal(zn["W"], zs["W"]):
                fail("G-b", where, "W != slice")
            for k in META_SAME_KEYS:
                if mn.get(k) != ms.get(k):
                    fail("G-c", where, "meta %s != slice" % k)
            if mn.get("generator_sha256") != gen_sha:
                fail("G-e", where, "generator_sha256 != manifest")
            if mn.get("ref_npz_sha256") != plan["stub_sha256"]:
                fail("G-e", where, "ref_npz_sha256 != stub sha256")
            slice_ok = len(failures) == slice_bad
            for bn in c["bins"]:
                j = int(np.argmin(np.abs(mids_m - bn["L_mid"] * 1e-6)))
                bwhere = "%s L_mid=%g" % (where, bn["L_mid"])
                bad = len(failures)
                if round(bn["L_mid"] / (grid * 1e6), 6) != bn["L_mid_grid_int"] or \
                        bn["L_mid_grid_int"] != int(bn["L_mid_grid_int"]):
                    fail("G-b", bwhere, "L_mid not grid integer")
                if not np.isclose(mids_m[j], bn["L_mid"] * 1e-6, rtol=0, atol=0):
                    fail("G-b", bwhere, "L axis index mismatch")
                nb = mn["model_bin_bounds_per_L"].get(key_of(bn["L_mid"]))
                if nb is None:
                    fail("G-a", bwhere, "no model_bin_bounds_per_L entry")
                else:
                    for anchor in bn["anchors"]:
                        sb = ms["model_bin_bounds_per_L"][key_of(anchor)]
                        if not all(close(nb[k], sb[k]) for k in BOUND_KEYS):
                            fail("G-a", bwhere, "bounds != slice anchor %g bin" % anchor)
                        if mn["model_bin_per_L"].get(key_of(bn["L_mid"])) != ms["model_bin_per_L"][key_of(anchor)]:
                            fail("G-a", bwhere, "model name != slice anchor %g bin" % anchor)
                    if not all(close(nb[k], bn[k]) for k in BOUND_KEYS):
                        fail("G-a", bwhere, "bounds != plan bin")
                for col in ("ID", "GM", "VDSAT"):
                    if not np.isfinite(zn[col][j]).all():
                        fail("G-d", bwhere, "non-finite %s" % col)
                if slice_ok and len(failures) == bad:
                    n_pass += 1
        models_by_device[c["slice_device_meta"]] = mn["model_files_sha256"]
        versions.add(mn["ngspice"])
        files.append({"kind": c["kind"], "device": c["device"], "w_key": c["w_key"], "w_um": c["w_um"],
                      "path_rel_root": pm.DATA_SUBDIR + "/" + os.path.basename(path),
                      "bytes": os.path.getsize(path), "sha256": pm.sha_raw(path),
                      "L_mid_um": [bn["L_mid"] for bn in c["bins"]], "bins": c["bins"]})
    if len(versions) != 1:
        fail("G-c", "run", "ngspice versions %r" % sorted(versions))

    # ---- G-h 진행 로그
    log_path = os.path.join(data, "generation_progress.log")
    times, cached, total_s = [], 0, 0.0
    with open(log_path, encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            if " cached " in line:
                cached += 1
            m = TIME_LINE.match(line)
            if m:
                times.append({"device": m.group(1), "w_um": round(float(m.group(2)), 6),
                              "L_um": round(float(m.group(3)), 6), "s": float(m.group(4))})
            d = DONE_LINE.match(line)
            if d:
                total_s += float(d.group(1))
    want = sorted((c["device"], c["w_um"], round(bn["L_mid"], 6)) for c in combos for bn in c["bins"])
    got = sorted((t["device"], t["w_um"], t["L_um"]) for t in times)
    if cached:
        fail("G-h", "log", "cached lines %d" % cached)
    if len(times) != n_total:
        fail("G-h", "log", "time lines %d != N %d" % (len(times), n_total))
    if got != want:
        fail("G-h", "log", "(device, W, L) pairs differ from plan")

    # ---- G-g compare
    with open(a.compare, encoding="utf-8") as fh:
        compare = json.load(fh)
    if compare.get("stop") is not None:
        fail("G-g", "compare", "stop: %s" % compare["stop"].get("reason"))

    # ---- G-f <root> 전후
    root = plan["root"]
    with open(os.path.join(vdir, "preexisting_files.json"), encoding="utf-8") as fh:
        pre = json.load(fh)
    now = pm.list_root(root)
    allowed = [os.path.relpath(p, root).replace(os.sep, "/") + "/" for p in (plan["record_dir"], plan["data_dir"])]
    for rel, sha in pre.items():
        if now.get(rel) != sha:
            fail("G-f", rel, "preexisting file changed or missing")
    for rel in now:
        if rel not in pre and not any(rel.startswith(p) for p in allowed):
            fail("G-f", rel, "new file outside <V>/<D>")

    if n_pass != n_total or failures:
        with open(stop_path, "w", encoding="utf-8") as fh:
            json.dump({"reason": "gates", "n": n_pass, "N": n_total, "failures": failures[:200],
                       "n_failures": len(failures)}, fh, indent=1, ensure_ascii=False)
        print("STOP gates n=%d N=%d failures=%d" % (n_pass, n_total, len(failures)))
        sys.exit(2)

    with np.load(os.path.join(vdir, "axis_stub.npz")) as z:
        stub_meta = json.loads(str(z["meta_json"]))
    repo = plan["repo"]
    jobs = plan["s2_commands"][0][plan["s2_commands"][0].index("--jobs") + 1]
    s0 = plan["s0"]
    record = {
        "schema": "lut_midpoints_record/1",
        "card": "20261106-lm1d", "decision": "O-242", "plan": "gain-budget v6.38.22 N6.40 LM-1d",
        "base_commit": plan["base_commit"],
        "n": n_pass, "N": n_total,
        "expect": plan["expect"],
        "plan_command": plan["command"],
        "generator": {"path_rel_root": s0["generator"]["path_rel_root"], "sha256": s0["generator"]["sha256"],
                      "sha256_lf": s0["generator"]["sha256_lf"], "in_repo": False},
        "commands": plan["s2_commands"],
        "simulator": {"exe": s0["ngspice"]["exe"], "exe_sha256": s0["ngspice"]["exe_sha256"],
                      "version": sorted(versions)[0]},
        "pdk": {"root": plan["pdk_root"], "model_files_sha256": dict(sorted(models_by_device.items()))},
        "inputs": {"axis_stub": {"sha256": plan["stub_sha256"], "L_source": stub_meta["L_source"],
                                 "axes_source": stub_meta["axes_source"]},
                   "pdk_decl": {"path": os.path.relpath(plan["pdk_decl"], repo).replace(os.sep, "/"),
                                "sha256": plan["pdk_decl_sha256"], "min_finger_w_m": plan["min_finger_w_m"],
                                "manufacturing_grid_m": plan["manufacturing_grid_m"]},
                   "lut_manifest_sha256": plan["lut_manifest_sha256"],
                   "device_kinds_source": "E/tests/lut/conftest.py:47-48"},
        "runtime": {"python": sys.version, "numpy": np.__version__, "jobs": int(jobs), "per_combo_s": times,
                    "total_s": total_s, "cached_lines": cached},
        "files": sorted(files, key=lambda f: (f["kind"], f["w_key"])),
        "compare": compare,
        "notes": {"location_declaration": "unchanged (WB-1 + LM-1e 통합 병합 안, 표 #24)",
                  "old_midpoints_file": "unchanged",
                  "sha256_rule": "files[].sha256 = raw = 위치 선언 files 항목에 쓸 값 (data_location.py:32-34·:50-58)"},
    }
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(record, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("OK record n=%d N=%d files=%d" % (n_pass, n_total, len(files)))


if __name__ == "__main__":
    main()
