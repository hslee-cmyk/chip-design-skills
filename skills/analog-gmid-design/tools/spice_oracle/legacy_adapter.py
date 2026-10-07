# -*- coding: utf-8 -*-
"""legacy_adapter.py -- 옛 gm/ID 엔진(skills/analog-gmid-design/legacy/) 출력 -> SPICE 오라클 입력 JSON.

새 엔진이 생기기 전 대조 기준선(baseline)을 만드는 용도. 오라클 본체(oracle_*.py)는 어떤 엔진도 import 하지
않는다 -- 엔진별 해석은 전부 이 어댑터에 있다.

진입점(단독 실행):
    python legacy_adapter.py <circuit_key> <out_dir> [--from-dump <legacy_dump.json>]
                             [--instance <instance.json>] [--topology <topology.json>]
                             [--w-source layout|sizing] [--isrc topology|engine] [--testbench <json>]

  --from-dump 없음 : 옛 엔진을 정본 spec(legacy/workspaces/run_harness.SPECS)으로 1회 돌려
                     <out_dir>/<key>.legacy_dump.json, <key>.instance.json 을 쓰고(엔진 함수 호출 결과만 담음),
                     이어서 변환한다. 옛 엔진 실행은 회로에 따라 수 분 걸린다.
  --from-dump 있음 : 이미 있는 dump(시제품 engine_dump.py 산출물과 같은 형식)를 변환만 한다.
  출력: <out_dir>/<key>.<w_source>.<isrc>.oracle_input.json

옛 엔진 해석(이 어댑터가 정하는 것, 근거)
  * 예측 노드전압: legacy propagate_node_voltages()(소자 vds 로 복원) + 게이트 전용 넷은 소자 VGS 투표 평균.
  * 예측 VGS: LUT.vgs_for_gm_id(gm_id, L, vds, vsb) -- 엔진이 W 를 정할 때 쓴 바로 그 점.
  * 영역 예측: 전 소자 sat(옛 엔진은 LUT 포화 영역 가정으로 sizing 한다).
  * 레일: topology supply_nets, 전압 = 엔진 예측 노드전압. 0 V 레일이 기준(SPICE 0). 바디: NMOS = 최저 레일,
    PMOS = 최고 레일(옛 엔진 derive_vsb_from_nodes 의 가정).
  * metric -> measure: topology sizing_roles.metrics 의 type/unit 로 정한다(이름이 아니라 선언된 종류).
  * 기하 --w-source layout: instance.json 넷리스트(finger_w, n_fingers 합). sizing: 엔진 sizing W 를
    LUT 특성화 폭(W_ref) bin 에 들도록 n = floor(W/W_ref) 개 finger 로 나눈다(finger_w = W/n).
  * 공정: LUT 생성기(assets/sky130_lut_sweep.py)의 공개 상수(PDK_ROOT, LOD_SPICE, NGSPICE_EXE)와 소스의
    include/DUT/probe 줄에서 모델 include 규칙, subckt, 확산 면적 규칙, W_ref 를 읽는다. 코너 자리는 '{corner}'.
    [신규] models[kind].polarity = 생성기 run_device 의 polarity 인자(+1 -> n, -1 -> p) -- 오라클 iso 모드가 쓴다.
  * [신규] topology = {path: 변환에 쓴 topology JSON(저장소 루트 기준 상대 경로), sha256} -- 오라클 C15 연결 동일성 대조용. topology 에 없는
    부하 C(LOAD_<출력>)는 not_in_topology_reason 을 달아 비교에서 뺀다(이유가 비교 결과에 기록됨).
"""
import argparse
import ast
import importlib.util
import json
import math
import os
import re
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(os.path.dirname(HERE))
LEGACY_DIR = os.path.join(SKILL_DIR, "legacy")
ASSETS_DIR = os.path.join(SKILL_DIR, "assets")
LUT_GENERATOR = os.path.join(ASSETS_DIR, "sky130_lut_sweep.py")
DEFAULT_TESTBENCH = os.path.join(HERE, "legacy_testbench.json")
SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "": 1.0}
PORT_ROLES = {"differential_input_p": "input_p", "differential_input_n": "input_n",
              "differential_output_p": "output_p", "differential_output_n": "output_n",
              "single_ended_output": "output", "single_ended_input": "input"}


# --------------------------------------------------------------------------- 옛 엔진 실행(dump)
def jsonable(v):
    if isinstance(v, (str, int, bool)) or v is None:
        return v
    if isinstance(v, float):
        return v if math.isfinite(v) else repr(v)
    if isinstance(v, dict):
        return {str(k): jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    try:
        import numpy as np
        if isinstance(v, np.generic):
            return jsonable(v.item())
        if isinstance(v, np.ndarray):
            return jsonable(v.tolist())
    except ImportError:
        pass
    return None


def run_legacy_dump(key, out_dir):
    """옛 엔진 1회 실행 -> dump dict. 엔진 함수 호출 결과만 담는다(새 계산 없음)."""
    sys.path.insert(0, os.path.join(LEGACY_DIR, "workspaces"))
    sys.path.insert(0, LEGACY_DIR)
    import run_harness as rh
    from sizing_recipe import optimize_full_circuit_budget, propagate_node_voltages
    from stick_diagram import load_topology, save_instance_json
    import numpy as np

    cfg = rh.SPECS[key]
    topo = os.path.join(rh.LIBRARY_DIR, cfg["topology_file"])
    spec = rh.canonical_spec(key)
    spec.setdefault("floorplan_target", {"max_aspect_ratio": rh.FLOORPLAN_MAX_ASPECT_RATIO,
                                         "min_packing_density": rh.FLOORPLAN_MIN_PACKING_DENSITY})
    spec.setdefault("max_layout_retry_rounds", rh.MAX_ITERS)
    luts = spec["lut_by_kind"]
    w_refs = {k: getattr(v, "W_ref", None) for k, v in luts.items()}
    z = np.load(rh.LUTFILE)
    out = {"circuit_key": key, "topology_path": topo, "lut_path": rh.LUTFILE,
           "lut_meta": {"corner": z["corner"].item() if "corner" in z.files else None,
                        "temp_c": float(z["temp_c"]) if "temp_c" in z.files else None,
                        "W_ref_m": next(iter(set(w_refs.values()))) if len(set(w_refs.values())) == 1 else None,
                        "W_ref_by_kind": w_refs},
           "spec_scalars": {k: jsonable(v) for k, v in spec.items()
                            if k not in ("lut", "lut_by_kind", "L_candidates", "VDS_candidates", "gm_id_grid")}}
    t0 = time.time()
    try:
        res = optimize_full_circuit_budget(topo, spec, grid_points_per_theta=cfg["grid_points_per_theta"],
                                           search_method=cfg.get("search_method", "grid"),
                                           slsqp_kwargs=cfg.get("slsqp_kwargs"))
    except Exception as e:  # 엔진 실패는 dump 에 그대로 남긴다(변환 단계가 막힘으로 보고)
        out.update({"engine_ok": False, "engine_error": f"{type(e).__name__}: {e}",
                    "engine_traceback": traceback.format_exc()[-4000:], "engine_seconds": time.time() - t0})
        return out
    out.update({"engine_ok": True, "engine_seconds": time.time() - t0, "theta_star": jsonable(res["theta_star"]),
                "metrics": jsonable(res["metrics"]), "audit_ok": res["audit_ok"], "sizing": jsonable(res["sizing"])})
    sizing = res["sizing"]
    inst_path = os.path.join(out_dir, f"{key}.instance.json")
    out["instance_json"] = None
    if res.get("pipeline_result") is not None:
        save_instance_json(inst_path, topo, sizing, res["pipeline_result"])
        out["instance_json"] = inst_path
    trs, _ = load_topology(topo)
    by_name = {t.name: t for t in trs}
    rep = propagate_node_voltages(by_name, sizing, spec["vdd"])
    nodes = dict(rep.nodes)
    out["node_voltage_report"] = {"unresolved": rep.unresolved, "conflicts": jsonable(rep.conflicts),
                                  "passes": rep.passes}
    dev_pred, votes = {}, {}
    for name in sorted(by_name):
        t, s = by_name[name], sizing.get(name) or {}
        rec = {"kind": t.kind, "gate": t.gate, "source": t.source, "drain": t.drain}
        need = [k for k in ("gm_id", "L", "vds", "vsb") if s.get(k) is None]
        if need:
            rec["vgs"], rec["vgs_missing_fields"] = None, need
        else:
            try:
                rec["vgs"] = float(luts[t.kind].vgs_for_gm_id(s["gm_id"], s["L"], s["vds"], s["vsb"]))
            except Exception as e:  # 보간 범위 밖 등 -- 원인을 남긴다
                rec["vgs"], rec["vgs_error"] = None, f"{type(e).__name__}: {e}"
        vs = nodes.get(t.source)
        if rec.get("vgs") is not None and vs is not None:
            vg = vs + rec["vgs"] if t.kind == "nmos" else vs - rec["vgs"]
            rec["v_gate_pred"] = vg
            votes.setdefault(t.gate, []).append((name, vg))
        dev_pred[name] = rec
    out["device_pred"] = dev_pred
    gate_pred = {}
    for net, vv in sorted(votes.items()):
        vals = [v for _, v in vv]
        gate_pred[net] = {"votes": vv, "mean": sum(vals) / len(vals), "spread": max(vals) - min(vals)}
    out["gate_net_pred"] = gate_pred
    pred_nodes = dict(nodes)
    for net, g in gate_pred.items():
        pred_nodes.setdefault(net, g["mean"])
    out["node_pred"] = pred_nodes
    return out


# --------------------------------------------------------------------------- 공정(LUT 생성기에서 읽기)
def process_from_lut_generator(lut_npz, corner):
    spec = importlib.util.spec_from_file_location("lut_generator", LUT_GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # 생성기는 __main__ 가드 뒤에서만 실행된다(상수 정의만 실행)
    with open(LUT_GENERATOR, encoding="utf-8") as f:
        src = f.read()
    cells, polarity = {}, {}
    for cell, pol in re.findall(r'run_device\("(\w+)",\s*polarity=([+-]?\d)', src):
        kind = "nmos" if int(pol) > 0 else "pmos"
        cells[kind], polarity[kind] = cell, ("n" if int(pol) > 0 else "p")  # 생성기 polarity 인자(+1/-1)
    inc_tpl = [t.replace("\\\\", "\\") for t in re.findall(r'\.include "(\{PDK_ROOT\}[^"]*)"', src)]
    lod = re.search(r'LOD_SPICE if devcell\.startswith\("(\w+)"\)', src)
    dut = re.search(r'xdut \S+ \S+ \S+ \S+ (\S+) l=\{L_um\}u w=([0-9.]+)(\w?) ad=([0-9.]+)(\w?) as=\S+ '
                    r'pd=([0-9.]+)(\w?) ps=\S+', src)
    probe = re.search(r'print (@m\.xdut\.\S+?)\[id\]', src)
    missing = [n for n, v in (("cells", cells), ("include", inc_tpl), ("dut", dut), ("probe", probe)) if not v]
    if missing:
        raise SystemExit(f"LUT 생성기 소스에서 {missing} 을 못 읽었다: {LUT_GENERATOR}")
    w0 = float(dut.group(2)) * SI[dut.group(3)]
    ad0 = float(dut.group(4)) * SI[dut.group(5)]  # SPICE 관례: ad=2.5p 는 2.5e-12 m^2
    pd0 = float(dut.group(6)) * SI[dut.group(7)]
    models = {}
    for kind, cell in cells.items():
        subckt = dut.group(1).replace("{devcell}", cell)
        incs = []
        if lod and cell.startswith(lod.group(1)):
            incs.append(mod.LOD_SPICE)
        for t in inc_tpl:
            p = t.replace("{PDK_ROOT}", mod.PDK_ROOT).replace("{devcell}", cell)
            incs.append(re.sub(rf"__{re.escape(corner)}\.", "__{corner}.", p))
        op_probe = probe.group(1).replace("xdut", "{inst}").replace("{devcell}", cell) + "[{param}]"
        models[kind] = {"subckt": subckt, "includes": incs, "op_probe": op_probe, "polarity": polarity[kind]}
    return {"lut_npz": lut_npz, "ngspice_exe": mod.NGSPICE_EXE, "models": models,
            "diffusion": {"ad_per_w_m": ad0 / w0, "pd_extra_m": pd0 - w0},
            "lut_reference_width_m": w0,
            "provenance": f"LUT 생성기 {os.path.relpath(LUT_GENERATOR, SKILL_DIR)} 공개 상수 + DUT/include/probe 줄"}


def _repo_relative(path):
    """topology 경로 -> 저장소 루트 기준 상대 경로('/' 구분, 오라클 C15 해석 규칙). 루트는 이 파일 폴더에서 위로 처음
    '.git' 이 있는 폴더. 루트 밖 파일이면 절대 경로 그대로(이식성 없음 -- 경고는 오라클 notes 에 경로로 드러남)."""
    d = HERE
    while not os.path.exists(os.path.join(d, ".git")):
        if os.path.dirname(d) == d:
            return os.path.abspath(path)
        d = os.path.dirname(d)
    rel = os.path.relpath(os.path.abspath(path), d) if os.path.splitdrive(path)[0].lower() == os.path.splitdrive(d)[0].lower() else None
    return os.path.abspath(path) if rel is None or rel.startswith("..") else rel.replace(os.sep, "/")


def _sha256_file(path):
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def legacy_constant(module_file, name):
    """legacy 소스의 모듈 수준 상수를 import 없이 읽는다(ast)."""
    with open(module_file, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise SystemExit(f"{module_file} 에 {name} 상수가 없다")


# --------------------------------------------------------------------------- 변환
def _metric_measure(mdecl):
    t, unit = (mdecl or {}).get("type") or "", (mdecl or {}).get("unit") or ""
    if t == "supply_current":
        return "supply_current_A", SI[unit[:-1]] if unit.endswith("A") and unit[:-1] in SI else None
    if t.endswith("pm_deg"):
        return "pm_deg", 1.0
    if unit == "dB" and "gain" in t:
        return "dc_gain_db", 1.0
    return None, None


def convert(dump, w_source, isrc, testbench, topology_path=None, instance_path=None, dump_dir=None):
    warnings, blockers = [], []
    if not dump.get("engine_ok"):
        raise SystemExit(f"옛 엔진이 끝까지 돌지 않은 dump: {str(dump.get('engine_error'))[:400]}")
    key = dump["circuit_key"]

    def find(p, fallback_dir, what):
        cands = [p] if p else []
        if p:
            cands.append(os.path.join(fallback_dir, os.path.basename(p.replace("\\", "/"))))
        for c in cands:
            if c and os.path.exists(c):
                if c != p:
                    warnings.append(f"{what}: dump 경로 {p} 가 없어 {c} 를 썼다")
                return c
        raise SystemExit(f"{what} 파일을 못 찾았다: {cands}")

    topo_p = topology_path or find(dump["topology_path"], os.path.join(ASSETS_DIR, "library"), "topology")
    lut_p = find(dump.get("lut_path"), ASSETS_DIR, "LUT npz")
    with open(topo_p, encoding="utf-8") as f:
        topo = json.load(f)
    spec = dump["spec_scalars"]
    sizing = dump["sizing"]
    node_pred = dump["node_pred"]
    corner = dump["lut_meta"]["corner"]
    process = process_from_lut_generator(lut_p, corner)
    w_ref = dump["lut_meta"].get("W_ref_m")
    if w_ref is not None and abs(w_ref - process["lut_reference_width_m"]) > abs(w_ref) * sys.float_info.epsilon * 16:
        warnings.append(f"dump W_ref {w_ref} 와 LUT 생성기 DUT 폭 {process['lut_reference_width_m']} 이 다르다 -- dump 값 사용")
    w_ref = w_ref if w_ref is not None else process["lut_reference_width_m"]

    # 레일
    rails = []
    for net in topo.get("supply_nets") or []:
        if node_pred.get(net) is None:
            blockers.append(f"supply net {net} 의 엔진 예측 전압 없음")
            continue
        rails.append({"net": net, "voltage": float(node_pred[net])})
    zero = [r for r in rails if r["voltage"] == 0.0]
    if len(zero) != 1:
        raise SystemExit(f"0 V 레일이 정확히 하나가 아니다: {rails}")
    zero[0]["reference"] = True
    lo = min(rails, key=lambda r: r["voltage"])["net"]
    hi = max(rails, key=lambda r: r["voltage"])["net"]
    rail_names = {r["net"] for r in rails}

    # 기하
    seg = {}
    inst = None
    if w_source == "layout":
        ip = instance_path or find(dump.get("instance_json"), dump_dir or ASSETS_DIR, "instance.json")
        with open(ip, encoding="utf-8") as f:
            inst = json.load(f)
        bad_rows = set()
        for e in inst["netlist"]:
            if abs(e["w"] - int(e["n_fingers"]) * e["finger_w"]) > abs(e["w"]) * sys.float_info.epsilon * 16:
                bad_rows.add(e["name"])
            g = seg.setdefault(e["name"], {"w": 0.0, "n": 0, "fw": set(), "l": set()})
            g["w"] += e["w"]
            g["n"] += int(e["n_fingers"])
            g["fw"].add(e["finger_w"])
            g["l"].add(e["l"])
        if bad_rows:
            warnings.append(f"instance.json 행의 w != n_fingers*finger_w: {sorted(bad_rows)} -- 넷리스트는 finger 규칙"
                            f"(finger_w x n_fingers)을 쓰고, 행 w 합은 devices[].W 로 남긴다(오라클 W_rel 로 드러남)")
    devices, pdev = [], {}
    for d in topo["netlist"]:
        n = d["name"]
        s = sizing[n]
        rec = {k: d[k] for k in ("name", "kind", "drain", "gate", "source")}
        rec["bulk"] = lo if d["kind"] == "nmos" else hi
        if w_source == "layout":
            g = seg.get(n)
            if g is None:
                blockers.append(f"instance.json 에 {n} 이 없다")
                continue
            if len(g["fw"]) != 1 or len(g["l"]) != 1:
                blockers.append(f"{n}: instance 행마다 finger_w/l 이 다르다 {sorted(g['fw'])} {sorted(g['l'])}")
                continue
            rec.update({"L": next(iter(g["l"])), "finger_w": next(iter(g["fw"])), "n_fingers": g["n"], "W": g["w"]})
            if abs(g["w"] - s["W"]) > abs(s["W"]) * sys.float_info.epsilon * 16:
                warnings.append(f"{n}: layout W {g['w'] * 1e6:.4g} um != sizing W {s['W'] * 1e6:.4g} um")
        else:
            nfin = max(1, math.floor(round(s["W"] / w_ref, 9)))
            rec.update({"L": s["L"], "finger_w": s["W"] / nfin, "n_fingers": nfin, "W": s["W"]})
        devices.append(rec)
        dp = dump["device_pred"].get(n) or {}
        pdev[n] = {"ID": s.get("ID"), "VGS": dp.get("vgs"), "VDS": s.get("vds"), "VSB": s.get("vsb"),
                   "gm": s.get("gm"), "gds": s.get("gds"), "gm_id": s.get("gm_id"), "region": "sat"}
        if dp.get("vgs") is None:
            warnings.append(f"{n}: 엔진 VGS 예측 없음 ({dp.get('vgs_error') or dp.get('vgs_missing_fields')})")

    # 전원
    sources = []
    for s in topo.get("ideal_sources") or []:
        a, b = s["terminals"]
        if s.get("kind") == "current_source":
            v, basis = s.get("value_amp"), "topology value_amp"
            if isrc == "engine":
                fed = [d for d in topo["netlist"] if d["drain"] in (a, b) and d["drain"] not in rail_names]
                if fed:
                    v_eng = sizing[fed[0]["name"]]["ID"]
                    if v is not None and v_eng != v:
                        warnings.append(f"전류원 {s['name']}: topology {v:g} A 대신 엔진 ID({fed[0]['name']}) {v_eng:g} A")
                    v, basis = v_eng, f"엔진 ID({fed[0]['name']}) (--isrc engine)"
            if v is None:
                v, basis = (dump.get("theta_star") or {}).get(s["name"]), "theta_star"
            if v is None:
                blockers.append(f"전류원 {s['name']} 값 없음")
                continue
            sources.append({"name": s["name"], "kind": "current", "terminals": [a, b], "value": v, "value_basis": basis})
        elif s.get("kind") == "voltage_source" and s.get("value_v") is not None:
            sources.append({"name": s["name"], "kind": "voltage", "terminals": [a, b], "value": s["value_v"],
                            "value_basis": "topology value_v"})
        else:
            blockers.append(f"ideal source {s['name']} 값/종류 해석 불가")

    # 수동소자
    sense_r = legacy_constant(os.path.join(LEGACY_DIR, "sizing_recipe.py"), "_DEFAULT_SENSE_RESISTOR_OHM")
    passives = []
    for p in topo.get("passive_elements") or []:
        a, b = p["terminals"]
        if p.get("kind") == "resistor":
            if p.get("value_ohm") is not None:
                v, basis = p["value_ohm"], "topology value_ohm"
            elif p.get("nulling_reference_device"):
                ref = p["nulling_reference_device"]
                v, basis = 1.0 / sizing[ref]["gm"], f"1/gm({ref}) (옛 엔진 nulling 저항 규칙)"
            else:
                v, basis = sense_r, "옛 엔진 sense 저항 기본값(legacy sizing_recipe 상수)"
            passives.append({"name": p["name"], "kind": "resistor", "terminals": [a, b], "value": v, "value_basis": basis})
        elif p.get("kind") == "capacitor":
            if p.get("value_farad") is not None:
                v, basis = p["value_farad"], "topology value_farad"
            elif p.get("value_from_spec") and spec.get(p["value_from_spec"]) is not None:
                v, basis = spec[p["value_from_spec"]], f"spec['{p['value_from_spec']}'] (엔진 derived 값은 결과에 없어 spec)"
            else:
                blockers.append(f"커패시터 {p['name']} 값 없음")
                continue
            passives.append({"name": p["name"], "kind": "capacitor", "terminals": [a, b], "value": v, "value_basis": basis})
        else:
            blockers.append(f"passive {p['name']} kind={p.get('kind')} 미지원")

    ports = {}
    for net, pd in (topo.get("ports") or {}).items():
        if isinstance(pd, dict) and pd.get("role") in PORT_ROLES:
            ports[PORT_ROLES[pd["role"]]] = net
    outs = [ports[k] for k in ("output", "output_p", "output_n") if k in ports]
    ref_net = zero[0]["net"]
    has_load = any(p["kind"] == "capacitor" and set(p["terminals"]) & set(outs) and ref_net in p["terminals"]
                   for p in passives)
    if not has_load:
        cl, basis = spec.get("CL"), "spec['CL']"
        if cl is None:
            for mname, m in (topo.get("sizing_roles", {}).get("metrics") or {}).items():
                if isinstance(m, dict) and m.get("CL") is not None:
                    cl, basis = m["CL"], f"topology metrics['{mname}'].CL"
                    break
        if cl is None:
            blockers.append("부하 C 근거 없음(spec CL / metrics CL)")
        else:
            for o in outs:
                passives.append({"name": f"LOAD_{o}", "kind": "capacitor", "terminals": [o, ref_net], "value": cl,
                                 "value_basis": basis,
                                 "not_in_topology_reason": f"topology 에 출력 부하 C 가 없어 어댑터가 {basis} 로 넣은 부하"})

    # 예측 metric / 제약
    mdecl = topo.get("sizing_roles", {}).get("metrics") or {}
    metrics, unmapped = [], []
    for name, val in (dump.get("metrics") or {}).items():
        meas, scale = _metric_measure(mdecl.get(name))
        if meas is None or scale is None or not isinstance(val, (int, float)):
            unmapped.append(name)
            continue
        it = {"name": name, "measure": meas, "value": val * scale, "basis": f"옛 엔진 metric {name} (type {mdecl[name].get('type')})"}
        if meas == "supply_current_A":
            it["rail"] = hi
        metrics.append(it)
    if spec.get("GBW") is not None:
        metrics.append({"name": "spec.GBW", "measure": "ugf_hz", "value": spec["GBW"],
                        "basis": "spec GBW(옛 엔진 설계목표, 엔진 자체 예측 아님)"})
    cons, not_meas = [], []
    for c in topo.get("sizing_roles", {}).get("constraints") or []:
        if not isinstance(c, dict):
            continue
        meas, scale = _metric_measure(mdecl.get(c.get("metric")))
        lim = c.get("value")
        if lim is None and c.get("value_from_spec"):
            lim = spec.get(c["value_from_spec"])
        if meas is None or scale is None or lim is None or c.get("op") not in (">=", "<="):
            not_meas.append(c.get("metric"))
            continue
        it = {"name": c["metric"], "measure": meas, "op": c["op"], "limit": lim * scale,
              "basis": f"topology constraint ({c.get('source')})"}
        if meas == "supply_current_A":
            it["rail"] = hi
        cons.append(it)

    conflicts = (dump.get("node_voltage_report") or {}).get("conflicts") or []
    if conflicts:
        warnings.append(f"옛 엔진 노드전압 복원 충돌 {len(conflicts)}건(최대 {max(c[4] for c in conflicts):.4g} V)")
    spreads = {k: v["spread"] for k, v in (dump.get("gate_net_pred") or {}).items() if v.get("spread")}
    if spreads:
        top = sorted(spreads.items(), key=lambda kv: -kv[1])[:6]
        warnings.append("게이트 넷 예측 전압의 소자간 불일치(VGS 투표 폭, V): " + ", ".join(f"{k}={v:.3g}" for k, v in top))

    # β 되먹임망: 입력 포트 넷에 단자가 물린 수동소자(연결성으로 정한다 -- 옛 엔진 metric 은 이를 부하로 쓴다)
    in_nets = {ports[k] for k in ("input_p", "input_n", "input") if k in ports}
    feedback = [p["name"] for p in passives if set(p["terminals"]) & in_nets]
    return {
        "schema": "spice_oracle_input/1",
        "circuit": key,
        "process": process,
        "rails": rails,
        "devices": devices,
        "sources": sources,
        "passives": passives,
        "bias_voltages": [],
        "feedback_passives": feedback,
        "ports": ports,
        "predictions": {"nodes": node_pred, "devices": pdev, "metrics": metrics},
        "acceptance": {"constraints": cons, "not_measurable": not_meas},
        "testbench": testbench,
        "judge": {},
        "topology": {"path": _repo_relative(topo_p), "sha256": _sha256_file(topo_p)},
        "provenance": {"adapter": "legacy_adapter.py", "engine": "legacy (skills/analog-gmid-design/legacy)",
                       "w_source": w_source, "isrc": isrc, "topology": topo_p, "lut_npz": lut_p,
                       "metrics_unmapped": unmapped, "warnings": warnings, "blockers": blockers,
                       "engine_metrics_raw": dump.get("metrics"), "theta_star": dump.get("theta_star")},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="옛 엔진 출력 -> SPICE 오라클 입력")
    ap.add_argument("circuit_key")
    ap.add_argument("out_dir")
    ap.add_argument("--from-dump", default=None)
    ap.add_argument("--instance", default=None)
    ap.add_argument("--topology", default=None)
    ap.add_argument("--w-source", choices=("layout", "sizing"), required=True)
    ap.add_argument("--isrc", choices=("topology", "engine"), required=True)
    ap.add_argument("--testbench", default=DEFAULT_TESTBENCH)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    if a.from_dump:
        with open(a.from_dump, encoding="utf-8") as f:
            dump = json.load(f)
        dump_dir = os.path.dirname(os.path.abspath(a.from_dump))
    else:
        dump = run_legacy_dump(a.circuit_key, a.out_dir)
        dump_dir = a.out_dir
        with open(os.path.join(a.out_dir, f"{a.circuit_key}.legacy_dump.json"), "w", encoding="utf-8") as f:
            json.dump(dump, f, ensure_ascii=False, indent=1)
        print(f"legacy engine ok={dump.get('engine_ok')} {dump.get('engine_seconds', 0):.1f}s")
    if dump["circuit_key"] != a.circuit_key:
        raise SystemExit(f"dump circuit_key {dump['circuit_key']} != {a.circuit_key}")
    with open(a.testbench, encoding="utf-8") as f:
        tb = json.load(f)
    tb = {k: v for k, v in tb.items() if not k.startswith("_")}
    inp = convert(dump, a.w_source, a.isrc, tb, a.topology, a.instance, dump_dir)
    outp = os.path.join(a.out_dir, f"{a.circuit_key}.{a.w_source}.{a.isrc}.oracle_input.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(inp, f, ensure_ascii=False, indent=1)
    print("wrote", outp)
    for w in inp["provenance"]["warnings"]:
        print("  WARN:", w)
    for b in inp["provenance"]["blockers"]:
        print("  BLOCKER:", b)
    return 2 if inp["provenance"]["blockers"] else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
