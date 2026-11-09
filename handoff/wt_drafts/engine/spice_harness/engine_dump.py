# -*- coding: utf-8 -*-
"""engine_dump.py -- gm/ID 엔진을 정본 spec(run_harness.SPECS)으로 한 번 돌리고, SPICE 하네스가
읽을 "엔진 예측" JSON 하나를 쓴다.

사용법:
    python engine_dump.py <repo_root> <circuit_key> <out_dir>

  repo_root   : gmid-light 복제본 루트(예: /c/g452/repo). 엔진 소스는 여기서 import 한다.
  circuit_key : run_harness.SPECS 키(two_stage_ota / current_reuse_telescopic_ota /
                folded_cascode / nmcnr_amplifier)
  out_dir     : 산출물 디렉터리. <key>.engine.json, <key>.instance.json 을 쓴다.

엔진 쪽에서 새로 계산하는 것은 없다. 아래는 전부 엔진의 기존 함수 호출 결과다.
  - optimize_full_circuit_budget()  : theta_star, sizing, metrics, audit_ok, pipeline(finger)
  - save_instance_json()            : instance.json(넷리스트 finger 배정 포함)
  - propagate_node_voltages()       : 소자 vds 로 복원한 노드 DC 전압(엔진 예측)
  - LUT.vgs_for_gm_id()             : 소자별 VGS(엔진이 W 를 계산할 때 쓴 바로 그 gm_id/L/vds/vsb)
게이트 넷 전압 예측 = V(source) +/- VGS (NMOS +, PMOS -).
"""
import json
import math
import os
import sys
import time
import traceback


def _jsonable(v):
    if isinstance(v, (str, int, bool)) or v is None:
        return v
    if isinstance(v, float):
        return v if math.isfinite(v) else repr(v)
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    try:
        import numpy as np
        if isinstance(v, np.generic):
            return _jsonable(v.item())
        if isinstance(v, np.ndarray):
            return _jsonable(v.tolist())
    except Exception:
        pass
    return None  # LUT 객체 등 직렬화 불가 -- spec 에서만 생기며 의도적으로 버린다


def main(repo_root, key, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ws = os.path.join(repo_root, "workspaces")
    sys.path.insert(0, ws)
    import run_harness as rh                       # noqa: E402  (LUT 로드 포함)
    from sizing_recipe import optimize_full_circuit_budget, propagate_node_voltages
    from stick_diagram import load_topology, save_instance_json

    cfg = rh.SPECS[key]
    topo = os.path.join(rh.LIBRARY_DIR, cfg["topology_file"])
    spec = rh.canonical_spec(key)
    # run_harness.run() 과 같은 설정(floorplan 재시도 루프 포함)으로 호출한다.
    spec.setdefault("floorplan_target", {
        "max_aspect_ratio": rh.FLOORPLAN_MAX_ASPECT_RATIO,
        "min_packing_density": rh.FLOORPLAN_MIN_PACKING_DENSITY})
    spec.setdefault("max_layout_retry_rounds", rh.MAX_ITERS)

    out = {"circuit_key": key, "topology_path": topo, "repo_root": repo_root,
           "lut_path": rh.LUTFILE}
    import numpy as np
    meta = np.load(rh.LUTFILE)
    out["lut_meta"] = {"corner": str(meta["corner"]) if "corner" in meta else None,
                       "temp_c": float(meta["temp_c"]) if "temp_c" in meta else None,
                       "W_ref_m": rh._W_REF}
    out["spec_scalars"] = {k: _jsonable(v) for k, v in spec.items()
                           if k not in ("lut", "lut_by_kind", "L_candidates",
                                        "VDS_candidates", "gm_id_grid")}
    t0 = time.time()
    try:
        res = optimize_full_circuit_budget(
            topo, spec, grid_points_per_theta=cfg["grid_points_per_theta"],
            search_method=cfg.get("search_method", "grid"),
            slsqp_kwargs=cfg.get("slsqp_kwargs"))
    except Exception as e:
        out["engine_ok"] = False
        out["engine_error"] = f"{type(e).__name__}: {e}"
        out["engine_traceback"] = traceback.format_exc()[-4000:]
        out["engine_seconds"] = time.time() - t0
        _write(out, out_dir, key)
        print("ENGINE FAIL:", out["engine_error"][:400])
        return 2
    out["engine_ok"] = True
    out["engine_seconds"] = time.time() - t0
    out["theta_star"] = _jsonable(res["theta_star"])
    out["metrics"] = _jsonable(res["metrics"])
    out["audit_ok"] = res["audit_ok"]
    sizing = res["sizing"]
    out["sizing"] = _jsonable(sizing)

    inst_path = os.path.join(out_dir, f"{key}.instance.json")
    if res.get("pipeline_result") is not None:
        save_instance_json(inst_path, topo, sizing, res["pipeline_result"])
        out["instance_json"] = inst_path
    else:
        out["instance_json"] = None

    # ---- 엔진 예측 노드전압 / VGS -------------------------------------------------
    trs, _ = load_topology(topo)
    by_name = {t.name: t for t in trs}
    vdd = spec["vdd"]
    rep = propagate_node_voltages(by_name, sizing, vdd)
    nodes = dict(rep.nodes)
    out["node_voltage_report"] = {"unresolved": rep.unresolved,
                                  "conflicts": _jsonable(rep.conflicts), "passes": rep.passes}
    luts = spec["lut_by_kind"]
    dev_pred, gate_votes = {}, {}
    for name in sorted(by_name):
        t = by_name[name]
        s = sizing.get(name) or {}
        need = [k for k in ("gm_id", "L", "vds", "vsb") if s.get(k) is None]
        rec = {"kind": t.kind, "gate": t.gate, "source": t.source, "drain": t.drain}
        if need:
            rec["vgs"] = None
            rec["vgs_missing_fields"] = need
        else:
            try:
                rec["vgs"] = float(luts[t.kind].vgs_for_gm_id(s["gm_id"], s["L"], s["vds"], s["vsb"]))
            except Exception as e:                       # 보간 범위 밖 등 -- 그대로 남긴다
                rec["vgs"] = None
                rec["vgs_error"] = f"{type(e).__name__}: {e}"
        vs = nodes.get(t.source)
        if rec.get("vgs") is not None and vs is not None:
            vg = vs + rec["vgs"] if t.kind == "nmos" else vs - rec["vgs"]
            rec["v_gate_pred"] = vg
            gate_votes.setdefault(t.gate, []).append((name, vg))
        dev_pred[name] = rec
    out["device_pred"] = dev_pred
    gate_pred = {}
    for net, votes in sorted(gate_votes.items()):
        vals = [v for _, v in votes]
        gate_pred[net] = {"votes": votes, "mean": sum(vals) / len(vals),
                          "spread": max(vals) - min(vals)}
    out["gate_net_pred"] = gate_pred
    # 노드 전압 정본 예측: propagate 결과 + (propagate 가 못 닿은) 게이트 전용 넷은 VGS 평균
    pred_nodes = dict(nodes)
    for net, g in gate_pred.items():
        pred_nodes.setdefault(net, g["mean"])
    out["node_pred"] = pred_nodes
    _write(out, out_dir, key)
    print(f"ENGINE OK {key}: {out['engine_seconds']:.1f}s metrics={out['metrics']}")
    return 0


def _write(out, out_dir, key):
    p = os.path.join(out_dir, f"{key}.engine.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("wrote", p)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
