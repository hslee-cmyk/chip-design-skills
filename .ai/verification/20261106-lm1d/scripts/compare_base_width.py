"""LM-1d 기준 폭 대조 (card 20261106-lm1d interface 5절, spec 완료 조건 3). ngspice 0.

같은 셀에서 옛 기준 폭 중점(LutSet A)과 새 기준 폭 중점(LutSet B)이 낸 bin L 방향 값(id_equivalent_v, V)의 차를 새 tol_V와 비교한다.
식은 엔진 정의 함수(`midpoint_l_bin_checks`, `tol_v_table`)가 낸 값 그대로이고, 이 파일의 식은 |new - old|, 비율, 짝짓기, 부호 셈뿐이다.
A·B는 순서대로 적재한다(동시에 두 LutSet을 메모리에 두지 않는다 -- 서로 다른 입력 버전의 별개 LutSet이라는 점은 그대로).

실행: python -P compare_base_width.py --location L --pdk-decl P --plan <V>/plan.json --data <D> --tmp <T> --cache <T>/table_cache --out <V>/compare.json
"""
import argparse
import gc
import json
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import plan_midpoints as pm                      # 같은 card 폴더 (공용 적재 함수)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--location", required=True)
    ap.add_argument("--pdk-decl", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--tmp", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    # 공용 표 캐시에 쓰지 않는다: 엔진이 읽는 환경 변수(GMID_LUT_TABLE_CACHE_DIR)를 빈 임시 폴더로 (메모 만들기 전에)
    cache = os.path.abspath(a.cache)
    if os.path.exists(cache) and os.listdir(cache):
        raise SystemExit("cache folder not empty: %s" % cache)
    os.environ["GMID_LUT_TABLE_CACHE_DIR"] = cache
    from gmid_engine.lut import LutMemo, midpoint_l_bin_checks, resolve_lut_location, tol_v_table

    tmp = os.path.abspath(a.tmp)
    os.makedirs(tmp, exist_ok=True)
    with open(a.plan, encoding="utf-8") as fh:
        plan = json.load(fh)
    loc = resolve_lut_location(os.path.abspath(a.location), os.environ)
    spec, grid, _w_min = pm.build_spec(os.path.abspath(a.pdk_decl))
    kinds = sorted({c["kind"] for c in plan["combos"]})
    suffix = dict(spec.cap_column_suffix)
    result = {"base_commit": plan["base_commit"], "kinds": {}, "stop": None}
    stops = []

    def new_memo(lut):
        return LutMemo(lut, point=256, curve=256, root=256)

    def bin_pairs(lut, kind, w_key):
        """앵커 2개 bin: [(model, 앵커 index 쌍)]"""
        sl = lut.slice_map[(kind, w_key)]
        out = []
        for b, lb in enumerate(sl.l_bins.bins):
            members = tuple(i for i, ab in enumerate(sl.l_bins.anchor_bin) if ab == b)
            if len(members) == pm.ANCHORS_PER_BIN:
                out.append((lb.model, members))
        return out

    # ---- 옛 값 (LutSet A)
    lut = pm.load_lut(loc, spec, loc.midpoints_path)
    memo = new_memo(lut)
    base = {k: lut.cap_map[k].w_key for k in kinds}
    old_rows, pairs, vds_of, anchor_l, old_sha = {}, {}, {}, {}, lut.provenance.midpoints_sha256
    for kind in kinds:
        b = base[kind]
        if lut.midpoints[kind].w_key != b:
            raise SystemExit("old midpoints w_key != cap w_key (%s)" % kind)
        chk = midpoint_l_bin_checks(memo, kind, b)
        pairs[kind] = bin_pairs(lut, kind, b)
        if chk.skipped or len(chk.rows) != len(pairs[kind]):
            raise SystemExit("old rows/skipped unexpected (%s): rows=%d skipped=%r" % (kind, len(chk.rows), chk.skipped))
        old_rows[kind] = {r.model: r.id_equivalent_v for r in chk.rows}
        sl = lut.slice_map[(kind, b)]
        vds_of[kind], anchor_l[kind] = sl.grids[2], sl.grids[0]
    del memo, lut
    gc.collect()

    # ---- 새 기준 폭 파일 -> 옛 중점 파일 꼴로 다시 담기 (열 이름만 바꿈, 값 변환 0)
    idx = pm.index_new_files(os.path.abspath(a.data), grid)
    stub_path = os.path.join(os.path.dirname(os.path.abspath(a.plan)), "axis_stub.npz")
    if pm.sha_raw(stub_path) != plan["stub_sha256"]:
        raise SystemExit("stub sha256 != plan.stub_sha256")
    with np.load(stub_path) as z:
        l_source = json.loads(str(z["meta_json"]))["L_source"]
    repack, axes0, meta0 = {}, None, None
    for kind in kinds:
        combo = next(c for c in plan["combos"] if c["kind"] == kind and c["w_key"] == base[kind])
        with np.load(idx[(combo["slice_device_meta"], base[kind])]) as z:
            meta = json.loads(str(z["meta_json"]))
            axes = {k: np.asarray(z[k]) for k in ("L", "VGS", "VDS", "VS")}
            w = np.asarray(z["W"])
            if axes0 is None:
                axes0, w0, meta0 = axes, w, meta
                repack.update(axes)
                repack.update({"w_ref_m": np.float64(w), "corner": np.str_(meta["corner"]),
                               "temp_c": np.float64(meta["temp_c_from_log"])})
            elif not (all(np.array_equal(axes0[k], axes[k]) for k in axes0) and np.array_equal(w0, w)
                      and meta["corner"] == meta0["corner"] and meta["temp_c_from_log"] == meta0["temp_c_from_log"]):
                raise SystemExit("base-width new files differ in axes/W/conditions between kinds")
            for name in ("ID", "GM", "VDSAT"):
                repack[name + suffix[kind]] = np.asarray(z[name])
    repack["meta_json"] = np.str_(json.dumps({"L_source": l_source}))
    repack_path = os.path.join(tmp, "repack_base.npz")
    np.savez(repack_path, **repack)
    repack_sha = pm.sha_raw(repack_path)

    # ---- 새 값 (LutSet B) + 새 tol_V
    lut = pm.load_lut(loc, spec, repack_path)
    memo = new_memo(lut)
    for kind in kinds:
        b = base[kind]
        chk = midpoint_l_bin_checks(memo, kind, b)
        if chk.skipped or len(chk.rows) != len(pairs[kind]) or bin_pairs(lut, kind, b) != pairs[kind]:
            raise SystemExit("new rows/skipped unexpected (%s)" % kind)
        new_rows = {r.model: r.id_equivalent_v for r in chk.rows}
        if set(new_rows) != set(old_rows[kind]) or set(new_rows) != {m for m, _ in pairs[kind]}:
            raise SystemExit("old/new bin models differ (%s)" % kind)
        tol = tol_v_table(memo, kind, b)
        cells = []
        for model, members in pairs[kind]:
            for i in members:
                for k, vds_v in enumerate(vds_of[kind]):
                    old, new = old_rows[kind][model][k], new_rows[model][k]
                    t = tol.cells[i][k].id_equivalent_v
                    cell = {"anchor_L_m": anchor_l[kind][i], "vds_k": k, "vds_v": vds_v, "model": model,
                            "old_v": old, "new_v": new, "diff_v": None, "tol_new_v": t, "ratio": None}
                    if old is not None and new is not None:
                        cell["diff_v"] = abs(new - old)
                        if t is not None:
                            cell["ratio"] = cell["diff_v"] / t if t else (0.0 if cell["diff_v"] == 0 else float("inf"))
                    cells.append(cell)
        defined = [c for c in cells if c["diff_v"] is not None]
        for c in cells:
            if (c["old_v"] is None) != (c["new_v"] is None):
                stops.append(("one_side_undefined", kind, c))
            elif c["diff_v"] is not None and c["tol_new_v"] is None:
                stops.append(("tol_undefined", kind, c))
            elif c["diff_v"] is not None and c["diff_v"] > c["tol_new_v"]:
                stops.append(("diff_exceeds_tol", kind, c))
        ratios = [c["ratio"] for c in defined if c["ratio"] is not None]
        result["kinds"][kind] = {
            "base_w_key": b, "old_midpoints_sha256": old_sha, "repack_sha256": repack_sha, "cells": cells,
            "n_cells": len(cells),
            "n_both_undefined": sum(1 for c in cells if c["old_v"] is None and c["new_v"] is None),
            "n_new_gt_old": sum(1 for c in defined if c["new_v"] > c["old_v"]),
            "n_new_lt_old": sum(1 for c in defined if c["new_v"] < c["old_v"]),
            "n_equal": sum(1 for c in defined if c["new_v"] == c["old_v"]),
            "max_diff_v": max((c["diff_v"] for c in defined), default=None),
            "max_ratio": max(ratios, default=None)}
    n_cells = sum(v["n_cells"] for v in result["kinds"].values())
    if n_cells != plan["n_cells_expected"]:
        stops.append(("cell_count_mismatch", None, {"got": n_cells, "expected": plan["n_cells_expected"]}))
    if stops:
        order = ("cell_count_mismatch", "one_side_undefined", "tol_undefined", "diff_exceeds_tol")
        reason = next(r for r in order if any(s[0] == r for s in stops))
        result["stop"] = {"reason": reason,
                          "counts": {r: sum(1 for s in stops if s[0] == r) for r in order if any(s[0] == r for s in stops)},
                          "cells": [dict(c, kind=kind, reason=r) for r, kind, c in stops]}
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, ensure_ascii=False)
    os.remove(repack_path)
    shutil.rmtree(cache, ignore_errors=True)
    print("compare: n_cells=%d stop=%s" % (n_cells, result["stop"] and result["stop"]["reason"]))
    for kind, v in result["kinds"].items():
        print(kind, {k: v[k] for k in ("n_cells", "n_both_undefined", "n_new_gt_old", "n_new_lt_old", "n_equal",
                                       "max_diff_v", "max_ratio")})


if __name__ == "__main__":
    main()
