"""card 20261104-op7a 측정 스크립트 (spec C-2~C-10). 판정자가 ngspice로 돌린다. toy 대상 아님.

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
 "source": {"declared": "default",
            "probes": [{"kind","l_m","widths_m"(슬라이스 폭 목록),
                        "lut": {"npz","member","index":[...],"scale_to_A"},
                        "sim": {"vgs","vds","vb","vs","temp_c","mult","include_records":[[경로,sha],...]}}]}
}
칸이 없거나 뜻을 못 정하면 BinRuleStop으로 멈춘다(값을 짓지 않음). 선언 파일은 --decl-out이 주어지고
모든 관문이 ok이며 validate_decl이 []일 때만 쓴다.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bin_rule_lib as B  # noqa: E402
from bin_rule_lib import BinRuleStop  # noqa: E402

HSA_TEXT = "set ngbehavior=hsa\n"


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


def check_includes(sim, includes):
    rec = {r[1] for r in _need(sim, "include_records", "sim")}
    files = []
    for ln in includes:
        m = re.search(r'"(.*)"', ln)
        if m:
            _included(m.group(1).replace("\\\\", "\\"), set(), files)
    import hashlib
    for f in files:
        b = open(f, "rb").read()
        if not ({hashlib.sha256(b).hexdigest(), hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()} & rec):
            raise BinRuleStop("source_condition_unresolved", f)
    return files


def source_modes(plan, g, base, kinds):
    src = _need(plan, "source", "plan")
    declared = _need(src, "declared", "source")
    import numpy
    rows, modes = [], []
    for k, pr in enumerate(_need(src, "probes", "source")):
        kind = kinds[pr["kind"]]
        w = B.source_point(pr["l_m"], pr["widths_m"], kind["bins"], g)
        lut, sim = _need(pr, "lut", "probe"), _need(pr, "sim", "probe")
        with numpy.load(lut["npz"], mmap_mode="r") as z:
            lut_id = float(z[lut["member"]][tuple(lut["index"])]) * lut["scale_to_A"]
        check_includes(sim, kind["includes"])
        vals = []
        for mname, init, mk in (("default", "", None), ("hsa", HSA_TEXT, "cwd")):
            cwd, env = _modes(base, f"src{k}_{mname}", init, mk)
            m = _need(sim, "mult", "sim")
            lines = [f"* source {k}", *kind["includes"], f".temp {_need(sim, 'temp_c', 'sim')}",
                     f"vgs g 0 dc {_need(sim, 'vgs', 'sim')}", f"vds d 0 dc {_need(sim, 'vds', 'sim')}",
                     f"vsrc s 0 dc {_need(sim, 'vs', 'sim')}", f"vb b 0 dc {_need(sim, 'vb', 'sim')}",
                     f"xp d g s b {kind['subckt']} l={pr['l_m'] * 1e6:g}u w={w * 1e6:g}u m={m:g}",
                     ".control", "op", "print i(vds)", "quit", ".endc", ".end"]
            log = run_ngspice(plan["ngspice_exe"], lines, cwd, env, "src")
            mm = re.search(r"i\(vds\)\s*=\s*([0-9.eE+-]+)", log)
            if not mm:
                raise BinRuleStop("source_condition_unresolved", "i(vds) 출력 없음")
            vals.append(float(mm.group(1)))
        mode = B.identify_mode(lut_id, vals[0], vals[1])
        modes.append(mode)
        rows.append({"probe": k, "kind": pr["kind"], "l_m": pr["l_m"], "w_m": w, "lut_id": lut_id,
                     "default_id": vals[0], "hsa_id": vals[1], "mode": mode})
    return B.judge_source_modes(modes, declared), rows


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
    ver_res = B.set_versions(plan["set_versions"])
    controls["simulator"], controls["unrecorded_sets"] = ver_res[0], list(ver_res[1])
    json.dump(controls, open(os.path.join(a.out, "controls.json"), "w"), indent=1, sort_keys=True)
    if controls["unrecorded_sets"]:
        raise BinRuleStop("simulator_version_unrecorded", controls["unrecorded_sets"])
    if verdict_c[0] != "ok":
        raise BinRuleStop(verdict_c[1])
    if verdict_e[0] != "ok":
        raise BinRuleStop(verdict_e[1])
    rule, why = rules["default"]
    if rule is None:
        raise BinRuleStop(why)
    (sv, srows) = source_modes(plan, g, a.out, kinds)
    with open(os.path.join(a.out, "source_modes.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in srows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    if sv[0] != "ok":
        raise BinRuleStop(sv[1])
    lf, md = B.union_model_sha([tuple(r) for r in plan["model_records"]], lambda p: open(p, "rb").read())
    decl = B.build_decl(lf, ver_res[0], "default", "", rule, ev_all, plan["date"])
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
