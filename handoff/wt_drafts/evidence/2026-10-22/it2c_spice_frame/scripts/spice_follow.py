"""IT-2c SPICE 틀 판정 -- SPICE 쪽.

엔진 봉인점 값(out/<회로>.engine.json, eng_seal.py)을 오라클의 기존 경로로 넷리스트로 만든다:
  legacy_adapter.convert(dump, w_source="layout", isrc="topology")  -> oracle_input (스키마 검증)
  oracle_netlist.write_netlists(inp, "free", ...)                    -> free 본 넷리스트(.cir + .meta.json)
dump 는 convert 가 읽는 칸만 엔진 봉인점 값으로 채운다(새 넷리스트 생성기 없음). 기하 = 엔진 W 를 엔진 DC 폭 슬라이스(w_key)
이상 finger 로 나눈 instance 행(layout 모드 입력 형식).

follower 측정: free 넷리스트는 반전 입력 = V(out) − Vofs (Efb_·Vofs_·Lfb_ servo), 비반전 입력 = Vdc_ 이다. 본문(.control 앞)을
그대로 두고 control 만 바꿔
  B (봉인점 유지 follower): Vofs = 넷리스트 값(V_out,pred − V_inn,pred) -- 증분 u = V_out, 엔진 선형 틀과 같은 동작점 가족
  A (순수 follower)        : Vofs = 0 -- 반전 입력 = 출력(계획 측정 구성 그대로)
에서 `dc Vdc_<비반전> x0→레일` 두 방향(0.5 mV)을 돌고 모든 넷 전압·모든 MOS 의 id·vds·vdsat·vgs 를 wrdata 로 쓴다.
"""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

SRC_ORACLE = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_it2c\src\skills\analog-gmid-design\tools\spice_oracle")
LIB = SRC_ORACLE.parent.parent / "assets" / "library"
sys.path.insert(0, str(SRC_ORACLE))
import legacy_adapter  # noqa: E402
import oracle_netlist  # noqa: E402

ROOT = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_it2c_spice")
OUT = ROOT / "out"
SP = ROOT / "spice"
NGSPICE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
LUT_NPZ = r"C:\Users\HSLEE\Documents\Todoc\fpga\lut_data\sky130_lut_v2\sky130_nfet_pfet_lut_v2_r2.npz"
STEP = 0.5e-3
PARAMS = ("id", "vds", "vdsat", "vgs")


def build_input(name, eng):
    ops = eng["device_cols"]["dc_op"]
    ss = eng["device_cols"]["ss_dev"]
    kinds = eng["device_cols"]["kind"]
    sizing, dpred, inst = {}, {}, []
    for m, op in ops.items():
        W, wk = op["W"], op["w_key"] * 1e-9
        n = max(1, math.floor(W / wk))
        inst.append({"name": m, "w": W, "n_fingers": n, "finger_w": W / n, "l": op["L"]})
        sizing[m] = {"W": W, "L": op["L"], "ID": op["current"], "vds": op["vds"], "vsb": op["vsb"],
                     "gm": ss[m]["gm"], "gds": ss[m]["gds"], "gm_id": op["gm_id"]}
        dpred[m] = {"vgs": op["vgs"]}
    theta_star = {k: v for k, v in eng["device_cols"]["dc_current"].items() if kinds.get(k) == "current_source"}
    pv = eng["device_cols"]["passive_value"]
    dump = {"circuit_key": name, "engine_ok": True, "topology_path": str(LIB / (name + ".topology.json")), "lut_path": LUT_NPZ,
            "spec_scalars": {"CL": pv.get("CL")}, "sizing": sizing, "node_pred": eng["values"],
            "lut_meta": {"corner": "tt", "W_ref_m": None}, "device_pred": dpred, "metrics": {}, "theta_star": theta_star}
    ipath = SP / (name + ".instance.json")
    ipath.write_text(json.dumps({"netlist": inst}, indent=1), encoding="utf-8")
    tb = json.loads((SRC_ORACLE / "legacy_testbench.json").read_text(encoding="utf-8"))
    tb = {k: v for k, v in tb.items() if not k.startswith("_")}
    topo_for_convert = LIB / (name + ".topology.json")
    t0 = json.loads(topo_for_convert.read_text(encoding="utf-8"))
    sizing_roles_null = t0.get("sizing_roles", {}) is None
    if sizing_roles_null:   # convert 는 sizing_roles 가 null 이면 AttributeError -- metric·제약 전용 칸이라 {} 로 바꾼 사본만 convert 에 준다(연결 불변, C15 는 원본으로)
        t0["sizing_roles"] = {}
        topo_for_convert = SP / (name + ".topology.convert_copy.json")
        topo_for_convert.write_text(json.dumps(t0, ensure_ascii=False, indent=1), encoding="utf-8")
    dump["topology_path"] = str(topo_for_convert)
    inp = legacy_adapter.convert(dump, "layout", "topology", tb, str(topo_for_convert), str(ipath), str(SP))
    inp["provenance"]["it2c_sizing_roles_null_copy"] = sizing_roles_null
    # 수동소자 값: convert 는 topology 값만 읽는다 -- 엔진 봉인점 값(device.passive_value)으로 맞춘다(DC 에서 용량은 열림, 직렬 Rz 는 DC 전류 0)
    fixed = []
    names = {p["name"] for p in inp["passives"]}
    for p in inp["passives"]:
        if p["name"] in pv and pv[p["name"]] is not None and p["value"] != pv[p["name"]]:
            fixed.append((p["name"], p["value"], pv[p["name"]]))
            p["value"], p["value_basis"] = pv[p["name"]], "엔진 봉인점 device.passive_value"
    topo = json.loads((LIB / (name + ".topology.json")).read_text(encoding="utf-8"))
    for p in topo.get("passive_elements") or []:
        if p["name"] not in names and pv.get(p["name"]) is not None:
            inp["passives"].append({"name": p["name"], "kind": p["kind"], "terminals": p["terminals"], "value": pv[p["name"]],
                                    "value_basis": "엔진 봉인점 device.passive_value"})
            fixed.append((p["name"], None, pv[p["name"]]))
    inp["provenance"]["it2c_passive_fix"] = fixed
    # bulk 대조: convert 규칙(NMOS 최저 레일, PMOS 최고 레일) vs 엔진 device.bulk
    eb = {k: v["net"] for k, v in eng["device_cols"]["bulk"].items()}
    inp["provenance"]["it2c_bulk_mismatch"] = [(d["name"], d["bulk"], eb.get(d["name"])) for d in inp["devices"] if eb.get(d["name"]) != d["bulk"]]
    return inp


def sweep_netlist(cir_text, meta, inp, cfg, x0, lo, hi, tag):
    body = []
    for raw in cir_text.splitlines():
        if raw.strip().lower().startswith(".control"):
            break
        body.append(raw)
    ports = inp["ports"]
    non, inv = ports["input_p"], ports["input_n"]
    nets = [n for n in meta["nets"]]
    vecs = [f"v({meta['spice_node'][n]})" for n in nets if meta["spice_node"][n] != "0"]
    for d in inp["devices"]:
        vecs += [meta["probes"][d["name"]][p] for p in PARAMS]
    for i in range(0, len(vecs), 6):
        body.append(".save " + " ".join(vecs[i:i + 6]))
    c = [".control", "set noaskquit", "set wr_singlescale", "set wr_vecnames", "option numdgt=12"]
    if cfg == "A":
        c.append(f"alter vofs_{inv.lower()} dc = 0")
    up = SP / f"{tag}.up.txt"
    dn = SP / f"{tag}.dn.txt"
    c.append(f"dc vdc_{non.lower()} {x0:.9g} {hi:.9g} {STEP:.9g}")
    c.append(f"wrdata {up.name} " + " ".join(vecs))
    c.append("reset")
    if cfg == "A":
        c.append(f"alter vofs_{inv.lower()} dc = 0")
    c.append(f"dc vdc_{non.lower()} {x0:.9g} {lo:.9g} {-STEP:.9g}")
    c.append(f"wrdata {dn.name} " + " ".join(vecs))
    c += ["quit", ".endc", ".end"]
    return "\n".join(body + c) + "\n", vecs, up, dn


def read_wrdata(path):
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    head = lines[0].split()
    rows = [[float(t) for t in ln.split()] for ln in lines[1:] if ln.strip()]
    return {"cols": head, "rows": rows}


def main(name):
    eng = json.loads((OUT / (name + ".engine.json")).read_text(encoding="utf-8"))
    inp = build_input(name, eng)
    errs = oracle_netlist.validate_input(inp)
    ip = SP / (name + ".oracle_input.json")
    ip.write_text(json.dumps(inp, ensure_ascii=False, indent=1), encoding="utf-8")
    cir = SP / (name + ".free.cir")
    meta = oracle_netlist.write_netlists(inp, "free", str(cir), str(LIB / (name + ".topology.json")), False)
    info = {"circuit": name, "schema_errors": [str(e) for e in errs], "netlist_blockers": meta["blockers"],
            "topology_identity": meta["topology_identity"]["status"], "adapter_warnings": inp["provenance"]["warnings"],
            "adapter_blockers": inp["provenance"]["blockers"], "passive_fix": inp["provenance"]["it2c_passive_fix"],
            "bulk_mismatch": inp["provenance"]["it2c_bulk_mismatch"], "sizing_roles_null_copy": inp["provenance"]["it2c_sizing_roles_null_copy"], "ports": inp["ports"],
            "bias_voltages": inp["bias_voltages"], "sources": inp["sources"], "notes": meta["notes"]}
    if inp["ports"].get("input_n") != eng["inv"] or inp["ports"].get("input_p") != eng["non"]:
        info["stop"] = f"port role 과 엔진 반전 입력 식별이 다르다: ports {inp['ports']} engine inv {eng['inv']}"
        (OUT / (name + ".spice_info.json")).write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
        return
    rails = [float(r["voltage"]) for r in inp["rails"]]
    lo, hi = min(rails), max(rails)
    x0 = eng["values"][eng["non"]]
    text = cir.read_text(encoding="utf-8")
    info["runs"] = {}
    for cfg in ("B", "A"):
        tag = f"{name}.{cfg}"
        net, vecs, up, dn = sweep_netlist(text, meta, inp, cfg, x0, lo, hi, tag)
        p = SP / (tag + ".dc.cir")
        p.write_text(net, encoding="utf-8")
        for f in (up, dn):
            if f.exists():
                f.unlink()
        r = subprocess.run([NGSPICE, "-b", p.name], cwd=str(SP), capture_output=True, text=True, errors="replace", timeout=3600)
        (SP / (tag + ".dc.log")).write_text(r.stdout + "\n--- stderr ---\n" + r.stderr, encoding="utf-8")
        info["runs"][cfg] = {"rc": r.returncode, "up_rows": None, "dn_rows": None}
        for key, f in (("up", up), ("dn", dn)):
            d = read_wrdata(f)
            info["runs"][cfg][key + "_rows"] = None if d is None else len(d["rows"])
            if d is not None:
                (OUT / f"{tag}.{key}.json").write_text(json.dumps(d), encoding="utf-8")
    info["vecs"] = vecs
    info["probes"] = meta["probes"]
    info["spice_node"] = meta["spice_node"]
    (OUT / (name + ".spice_info.json")).write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(name, json.dumps(info["runs"]), flush=True)


if __name__ == "__main__":
    for nm in sys.argv[1:]:
        main(nm)
