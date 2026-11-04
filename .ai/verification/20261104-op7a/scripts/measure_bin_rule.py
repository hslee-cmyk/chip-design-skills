"""card 20261104-op7a 측정 스크립트 (spec C-2~C-14). 판정자가 ngspice로 돌린다. toy 대상 아님.

입력 = 계획 파일(JSON, --plan). 이 스크립트는 PDK 값·경로·bin 표를 코드에 두지 않고 계획 파일에서 읽는다:
{
 "ngspice_exe": "...", "date": "YYYY-MM-DD",
 "tlef": "<tech LEF 경로>", "lut_grid_um": <LUT meta manufacturing_grid_um>,
 "model_records": [["<경로>", "<LUT 기록 sha256>"], ...],
 "set_versions": {"<세트>": "ngspice-46" | null, ...},
 "kinds": [{"name": "...", "subckt": "...", "includes": ['.include "..."'],
            "bins": [{"model","lmin","lmax","wmin","wmax"}],   # m
            "l_axes": [{"npz": "...", "scale_to_m": <float>}] | [[<m>...]],
            "widths_m": [...], "w_ref_m": <m>}],
 "slices": [{"set","kind","npz","scale_to_m"}],          # C-10·C-13: 폭 슬라이스(npz `L`·`meta_json`만 읽음)
 "combined_sets": [{"set","npz"}],                       # C-11: cap_npz·verify_midpoints
 "bound_sets": [{"set","npz"}],                          # C-12: noise·mismatch
 "location": "<lut_v2_location.json 경로>"               # C-12: files.cap_npz.sha256
}
kinds[*]에 "meta_key"(결합 세트 meta의 kind 키)가 더 필요하다.
출처 모드는 생성기 기록 bin 이름 대조이고(C-10) 값 시뮬레이션은 없다. 선언 `evidence.source_basis` = generator_record(C-14).
칸이 없거나 뜻을 못 정하면 BinRuleStop으로 멈춘다(값을 짓지 않음). 선언 파일은 --decl-out이 주어지고
모든 관문이 ok이며 validate_decl이 []일 때만 쓴다.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bin_rule_lib as B  # noqa: E402
from bin_rule_lib import BinRuleStop  # noqa: E402

HSA_TEXT = "set ngbehavior=hsa\n"
MODE = "default"  # 본 측정 모드(C-5 1), 선언 compat.mode


def _need(d, key, where):
    if not isinstance(d, dict) or key not in d:
        raise BinRuleStop("source_condition_unresolved", f"{where}.{key}")
    return d[key]


def grid_from_tlef(path, lut_grid_um):
    txt = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"MANUFACTURINGGRID\s+([0-9.eE+-]+)\s*;", txt)
    if not m:
        raise BinRuleStop("grid_unresolved", path)
    g_um = float(m.group(1))
    if abs(g_um - lut_grid_um) > 1e-12:
        raise BinRuleStop("grid_mismatch", (g_um, lut_grid_um))
    return g_um * 1e-6


def l_axes_m(kind):
    out = []
    for ax in kind["l_axes"]:
        if isinstance(ax, dict):
            import numpy  # npz `L` 멤버만 읽는다
            with numpy.load(ax["npz"]) as z:
                out.append([float(v) * ax["scale_to_m"] for v in z["L"]])
        else:
            out.append([float(v) for v in ax])
    return out


def run_ngspice(exe, lines, workdir, env, tag):
    os.makedirs(workdir, exist_ok=True)
    cir = os.path.join(workdir, tag + ".cir")
    with open(cir, "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    p = subprocess.run([exe, "-b", cir], cwd=workdir, env=env, capture_output=True, timeout=600)
    if p.returncode != 0:
        raise BinRuleStop("ngspice_failed", (tag, p.returncode))
    return p.stdout.decode("utf-8", errors="replace")


def _modes(base, name, init_text, make_file):
    """실행 폴더(cwd)와 HOME 폴더를 만든다. make_file in (None, "cwd", "home")."""
    cwd, home = os.path.join(base, name, "cwd"), os.path.join(base, name, "home")
    os.makedirs(cwd, exist_ok=True)
    os.makedirs(home, exist_ok=True)
    if make_file == "cwd":
        open(os.path.join(cwd, ".spiceinit"), "w", newline="").write(init_text)
    elif make_file == "home":
        open(os.path.join(home, ".spiceinit"), "w", newline="").write(init_text)
    return cwd, B.isolated_env(os.environ, home)


def measure_kind(plan, kind, g, base, name, init_text, make_file, points_m):
    """points_m = [(L_m, W_m)] -> {point key: bin model}."""
    cwd, env = _modes(base, name + "_" + kind["name"], init_text, make_file)
    pts_um = [(l * 1e6, w * 1e6) for l, w in points_m]
    lines = B.netlist_lines(kind["subckt"], kind["includes"], pts_um)
    log = run_ngspice(plan["ngspice_exe"], lines, cwd, env, "probe")
    got = B.parse_probe_log(log, kind["bins"], g)
    missing = [f"p{i}" for i in range(len(points_m)) if f"p{i}" not in got]
    if missing:
        raise BinRuleStop("showmod_incomplete", missing)
    return {f"p{i}": got[f"p{i}"] for i in range(len(points_m))}


def kind_points(kind, g):
    ls = B.anchor_set(l_axes_m(kind), g)
    ws = list(kind["widths_m"]) + [kind["w_ref_m"]]
    pts = [(l, w) for l in ls for w in ws]
    for p in B.w_boundary_points(kind["bins"], g):
        if p not in pts:
            pts.append(p)
    return pts


def rule_of(kind, pts, bins_by_tag, g):
    dirs, ev = [], []
    by = {b["model"]: b for b in kind["bins"]}
    for i, (l, w) in enumerate(pts):
        chosen = by[bins_by_tag[f"p{i}"]]
        d = B.point_direction(l, w, chosen, kind["bins"], g)
        dirs.append(d)
        if d:
            ev.append((l, w, chosen["model"]))
    return dirs, ev


def read_real_home_spiceinit():
    p = os.path.join(os.path.expanduser("~"), ".spiceinit")
    if not os.path.exists(p):
        return {"exists": False}
    return {"exists": True, "text": open(p, encoding="utf-8", errors="replace").read()}


def _included(path, seen, out):
    if path in seen:
        return
    seen.add(path)
    out.append(path)
    for ln in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r'\s*\.(?:include|lib)\s+"?([^"\s]+)"?', ln, re.I)
        if m:
            sub = m.group(1)
            if not os.path.isabs(sub):
                sub = os.path.join(os.path.dirname(path), sub)
            if os.path.exists(sub):
                _included(sub, seen, out)


def _num(v, where):
    try:
        return float(v)
    except (TypeError, ValueError):
        raise BinRuleStop("source_record_missing", where)


def read_meta(npz_path):
    import numpy  # npz `meta_json` 멤버만 읽는다
    with numpy.load(npz_path) as z:
        return json.loads(str(z["meta_json"]))


def read_l_axis_m(npz_path, scale_to_m):
    import numpy  # npz `L` 멤버만 읽는다
    with numpy.load(npz_path) as z:
        return [float(v) * scale_to_m for v in z["L"]]


def reached_files(kind):
    """kind의 include 줄에서 재귀로 닿는 파일 -> (LF sha256, raw sha256)."""
    files = []
    for ln in kind["includes"]:
        m = re.search(r'"(.*)"', ln)
        if m:
            _included(m.group(1).replace("\\\\", "\\"), set(), files)
    out = {}
    for f in files:
        b = open(f, "rb").read()
        out[f] = (hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest(), hashlib.sha256(b).hexdigest())
    return out


def source_gate(plan, g, kinds, pts_of, runs, out_dir):
    """C-10 + C-13: 슬라이스 기록 bin 이름 대조와 기록 전용 파일. source_modes.jsonl을 쓴다."""
    reached = {n: reached_files(k) for n, k in kinds.items()}
    cells_all, ro, seen = [], {}, set()
    with open(os.path.join(out_dir, "source_modes.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for sl in _need(plan, "slices", "plan"):
            name = _need(sl, "kind", "slice")
            kind = kinds[name]
            meta = read_meta(_need(sl, "npz", "slice"))
            l_axis = read_l_axis_m(sl["npz"], _need(sl, "scale_to_m", "slice"))
            w = _num(_need(meta, "w_m", "meta"), "w_m")
            measured = {}
            for i, (l, wp) in enumerate(pts_of[name]):
                measured[(B.grid_index(l, g), B.grid_index(wp, g))] = (runs["default"][name][f"p{i}"],
                                                                        runs["cwd"][name][f"p{i}"])
            cells = B.slice_tie_cells(l_axis, w, meta.get("model_bin_per_L"), measured, kind["bins"], g)
            for c in cells:
                f.write(json.dumps({"set": sl["set"], "kind": name, **c}, sort_keys=True) + "\n")
            cells_all += cells
            only = B.record_only_files(reached[name], meta.get("model_files_sha256"))
            ro.setdefault(name, set()).update(only)
            seen.add(name)
        for name in kinds:
            if name not in seen:
                raise BinRuleStop("source_record_missing", name)
            f.write(json.dumps({"kind": name, "record_only_files": sorted(ro[name])}, sort_keys=True) + "\n")
        return B.record_source_mode(cells_all, MODE), {n: sorted(v) for n, v in ro.items()}


def combined_gate(plan, g, kinds, pts_of, runs):
    """C-11: 결합 세트 meta의 (kind, L)별 model을 본 측정 (L, w_ref_m) bin과 대조."""
    res = {}
    for cs in _need(plan, "combined_sets", "plan"):
        meta = read_meta(_need(cs, "npz", "combined_set"))
        wi = B.grid_index(_num(_need(meta, "w_ref_m", "meta"), "w_ref_m"), g)
        rec_all = _need(meta, "model_bin_per_L_at_w_ref", "meta")
        for name, kind in kinds.items():
            rec = rec_all.get(_need(kind, "meta_key", "kind")) if isinstance(rec_all, dict) else None
            measured = {}
            for k in (rec if isinstance(rec, dict) else {}):
                try:
                    li = B.grid_index(float(k) * 1e-6, g)
                except ValueError:
                    continue
                for i, (l, w) in enumerate(pts_of[name]):
                    if B.grid_index(l, g) == li and B.grid_index(w, g) == wi:
                        measured[k] = runs["default"][name][f"p{i}"]
            B.combined_bin_check(rec if isinstance(rec, dict) else None, measured)
            res[f"{cs['set']}:{name}"] = "ok"
    return res


def cap_bind_gate(plan):
    """C-12: noise·mismatch meta `cap_npz_sha256`을 위치 선언 `files.cap_npz.sha256`과 대조."""
    loc = json.load(open(_need(plan, "location", "plan"), encoding="utf-8"))
    pinned = _need(_need(_need(loc, "files", "location"), "cap_npz", "files"), "sha256", "cap_npz")
    res = {}
    for bs in _need(plan, "bound_sets", "plan"):
        B.cap_bind_check(read_meta(_need(bs, "npz", "bound_set")).get("cap_npz_sha256"), pinned)
        res[bs["set"]] = "ok"
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True, help="산출물 폴더(저장소 밖)")
    ap.add_argument("--decl-out", help="선언 파일 경로(관문 전부 ok일 때만 씀)")
    ap.add_argument("--smoke", action="store_true", help="kind마다 동률 점 하나만 재서 bin 이름을 찍는다")
    a = ap.parse_args(argv)
    plan = json.load(open(a.plan, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    g = grid_from_tlef(plan["tlef"], plan["lut_grid_um"])
    kinds = {k["name"]: k for k in plan["kinds"]}

    if a.smoke:
        for k in kinds.values():
            tie = [p for p in kind_points(k, g) if B.tie_axes(p[0], p[1], k["bins"], g)]
            if not tie:
                raise BinRuleStop("no_tie_point", k["name"])
            got = measure_kind(plan, k, g, a.out, "smoke", "", None, tie[:1])
            print(k["name"], tie[0], got["p0"])
        return 0

    runs = {n: {} for n in ("default", "cwd", "home", "empty")}
    spec = {"default": ("", None), "cwd": (HSA_TEXT, "cwd"), "home": (HSA_TEXT, "home"), "empty": ("", "cwd")}
    pts_of, ev_all = {}, []
    with open(os.path.join(a.out, "points.jsonl"), "w", encoding="utf-8", newline="\n") as fp:
        for k in kinds.values():
            pts_of[k["name"]] = kind_points(k, g)
            for n, (txt, mk) in spec.items():
                runs[n][k["name"]] = measure_kind(plan, k, g, a.out, n, txt, mk, pts_of[k["name"]])
            for i, (l, w) in enumerate(pts_of[k["name"]]):
                fp.write(json.dumps({"kind": k["name"], "L": l, "W": w,
                                     **{n: runs[n][k["name"]][f"p{i}"] for n in runs}}, sort_keys=True) + "\n")
    rules = {}
    for n in runs:
        dirs = []
        for k in kinds.values():
            d, ev = rule_of(k, pts_of[k["name"]], runs[n][k["name"]], g)
            dirs += d
            if n == "default":
                ev_all += ev
        rules[n] = B.derive_rule(dirs)
    flat = {n: {f"{kn}:{t}": m for kn, bt in runs[n].items() for t, m in bt.items()} for n in runs}
    verdict_c = B.judge_controls(rules["default"][0], rules["cwd"][0], rules["home"][0])
    verdict_e = B.judge_empty_init(flat["default"], flat["empty"])
    controls = {"rules": {n: rules[n] for n in rules}, "controls": verdict_c, "empty_init": verdict_e,
                "real_home_spiceinit": read_real_home_spiceinit()}
    def dump_controls():
        with open(os.path.join(a.out, "controls.json"), "w", encoding="utf-8", newline="\n") as cf:
            json.dump(controls, cf, indent=1, sort_keys=True, default=str)

    ver_res = B.set_versions(plan["set_versions"])
    controls["simulator"], controls["unrecorded_sets"] = ver_res[0], list(ver_res[1])
    dump_controls()
    if controls["unrecorded_sets"]:
        raise BinRuleStop("simulator_version_unrecorded", controls["unrecorded_sets"])
    if verdict_c[0] != "ok":
        raise BinRuleStop(verdict_c[1])
    if verdict_e[0] != "ok":
        raise BinRuleStop(verdict_e[1])
    rule, why = rules["default"]
    if rule is None:
        raise BinRuleStop(why)
    try:
        controls["source_mode"], controls["record_only_files"] = source_gate(plan, g, kinds, pts_of, runs, a.out)
        controls["combined_bins"] = combined_gate(plan, g, kinds, pts_of, runs)
        controls["cap_bind"] = cap_bind_gate(plan)
    except BinRuleStop as e:
        controls["stop"] = {"reason": e.reason, "detail": e.detail}
        dump_controls()
        raise
    dump_controls()
    lf, md = B.union_model_sha([tuple(r) for r in plan["model_records"]], lambda p: open(p, "rb").read())
    decl = B.build_decl(lf, ver_res[0], MODE, "", rule, ev_all, plan["date"])
    bad = B.validate_decl(decl)
    if bad:
        raise BinRuleStop("decl_invalid", bad)
    if a.decl_out:
        json.dump(decl, open(a.decl_out, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("ok", rule, "machine_dependent:", md)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BinRuleStop as e:
        print("STOP", e.reason, e.detail, file=sys.stderr)
        sys.exit(2)
