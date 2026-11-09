"""Q1 공통 표: 4회로 SPICE servo 훑기(회로 분석가 기록 재사용, SPICE 재실행 0)에서
영역 행 창과 기능 기준 후보((가) 절대 하한 = spec gain_ss_db, (나) 기준점 대비 상대 저하 X)의
창·묶는 쪽을 같은 규칙으로 다시 잰다.

규칙(계획 N3.8 'ICMR 기능 기준' 꼴): 창 = 기준점 x0에서 양쪽으로 넓히며
  영역 행(전 MOS VDS >= VDSAT) ∧ 기능 기준이 모두 참인 연속 격자점의 끝.
  격자 = 각 분석가 훑기 격자(값은 격자점, 보간 없음 -- 끝 오차 <= 격자 한 칸).
X 값(1·3·6 dB)과 x0 주사는 측정 매개변수(spec 권고 아님). floor 는 spec 파일에서 읽는다(상수 0).
출력: 같은 폴더 q1_unified_windows.jsonl(케이스마다 append), q1_unified_windows.txt.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(os.path.dirname(HERE), "icmr4")
LIB = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library"
OUT_J = os.path.join(HERE, "q1_unified_windows.jsonl")
OUT_T = os.path.join(HERE, "q1_unified_windows.txt")
XS = (1.0, 3.0, 6.0)


def spec_rails(circuit):
    s = json.load(open(os.path.join(LIB, circuit + ".sizing_spec.json"), encoding="utf-8"))
    v = s["human"]["supplies_v"]["values"].values()
    return min(v), max(v)


def spec_floor(circuit):
    s = json.load(open(os.path.join(LIB, circuit + ".sizing_spec.json"), encoding="utf-8"))
    for c in s["human"]["constraints"] if "human" in s else s["constraints"]:
        if c.get("metric") == "gain_ss_db" and c.get("op") == ">=":
            return float(c["value"])
    return None


def load_nmcnr():
    rows = [json.loads(l) for l in open(os.path.join(EV, "nmcnr_amplifier_files", "spice_ref.jsonl"), encoding="utf-8")]
    designs = {r["tag"]: r for r in rows if r.get("case") == "design"}
    out = {}
    for tag, d in designs.items():
        pts = [r for r in rows if r.get("case") == "point" and r.get("tag") == tag]
        seq = sorted((float(p["x"]), float(p["gain_db"]), p["sat_fail"] in ([], "[]")) for p in pts)
        out[tag] = (seq, float(d["X0"]))
    return out


def load_ngcc():
    out = {}
    for name in ("icmr_hs_vref0p9", "icmr_hs_L1u_vref0p9", "icmr_hs_L1u_vref0p5"):
        seq = []
        with open(os.path.join(EV, "ngcc_3stage_ff_files", name + ".csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["ok"] != "1":
                    continue
                seq.append((float(r["vcm"]), float(r["A_db"]), float(r["worst_sat"]) >= 0.0))
        out[name] = (sorted(seq), None)
    return out


def load_cr():
    rows = [json.loads(l) for l in open(os.path.join(EV, "current_reuse_telescopic_ota_files", "icmr_servo_sweep_alldev_s5.jsonl"), encoding="utf-8")]
    seq = []
    for r in rows:
        if r.get("case") != "point" or not r.get("servo_ok"):
            continue
        ok = all(v["m"] >= 0.0 for v in r["sat"].values())
        seq.append((float(r["vcm"]), float(r["adm_db"]), ok))
    return {"rep_s5": (sorted(seq), 0.9)}


def load_sf():
    rows = [json.loads(l) for l in open(os.path.join(EV, "sf_pushpull_output_opamp_files", "spice_icmr.jsonl"), encoding="utf-8")]
    seq = []
    for r in rows:
        if r.get("case") == "v2" and r.get("step") == "icmr":
            seq.append((float(r["x"]), float(r["A_db"]), r["neg_sat"] in ([], "[]")))
    return {"v2": (sorted(seq), 0.9)}


def window(seq, i0, pred):
    """x0 격자 index i0 에서 양쪽으로 pred 가 참인 동안 넓힘. 반환 (lo, hi, lo_stop, hi_stop)."""
    if not pred(seq[i0]):
        return None
    lo = i0
    while lo - 1 >= 0 and pred(seq[lo - 1]):
        lo -= 1
    hi = i0
    while hi + 1 < len(seq) and pred(seq[hi + 1]):
        hi += 1
    lo_stop = "sweep_edge" if lo == 0 else "rule"
    hi_stop = "sweep_edge" if hi == len(seq) - 1 else "rule"
    return seq[lo][0], seq[hi][0], lo_stop, hi_stop


def binding(seq, i0, a0, func):
    """영역 ∧ 기능 창과, 각 끝을 어느 행이 묶는지."""
    reg = lambda p: p[2]
    both = lambda p: p[2] and func(p, a0)
    w_reg = window(seq, i0, reg)
    w_both = window(seq, i0, both)
    if w_both is None:
        return {"window": None, "lo_bind": "x0_fails", "hi_bind": "x0_fails"}
    lo, hi, ls, hs = w_both
    def side(edge, stop, reg_edge):
        if stop == "sweep_edge":
            return "sweep_edge(rail_or_scan)"
        return "region" if abs(edge - reg_edge) < 1e-12 else "function"
    return {"window": [lo, hi], "lo_bind": side(lo, ls, w_reg[0]), "hi_bind": side(hi, hs, w_reg[1])}


def main():
    open(OUT_J, "w", encoding="utf-8").close()
    lines = []
    sets = [
        ("nmcnr_amplifier", load_nmcnr()),
        ("ngcc_3stage_ff", load_ngcc()),
        ("current_reuse_telescopic_ota", load_cr()),
        ("sf_pushpull_output_opamp", load_sf()),
    ]
    for circuit, data in sets:
        floor = spec_floor(circuit)
        r_lo, r_hi = spec_rails(circuit)
        for case, (seq, x0) in data.items():
            # 레일 자름(계획 N3.8 '레일 자름'): 입력이 레일 밖인 격자점은 범위 밖 -- 영역 행 거짓으로 둠
            seq = [(x, a, ok and (r_lo <= x <= r_hi)) for (x, a, ok) in seq]
            reg_idx = [i for i, p in enumerate(seq) if p[2]]
            if not reg_idx:
                rec = {"circuit": circuit, "case": case, "note": "no region-ok point"}
                with open(OUT_J, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                lines.append(json.dumps(rec, ensure_ascii=False))
                continue
            # x0 후보: 분석가 x0(있으면) + 영역 창 안 모든 격자점 주사
            x0_list = []
            if x0 is not None:
                x0_list.append(("analyst_x0", min(range(len(seq)), key=lambda i: abs(seq[i][0] - x0))))
            for i in reg_idx:
                x0_list.append(("scan", i))
            rows = []
            for kind, i0 in x0_list:
                a0 = seq[i0][1]
                r = {"x0": seq[i0][0], "A_x0_db": round(a0, 3), "region_ok_x0": seq[i0][2]}
                r["region_only"] = window(seq, i0, lambda p: p[2])
                if floor is not None:
                    r["abs_floor"] = binding(seq, i0, a0, lambda p, a: p[1] >= floor)
                    r["abs_equiv_X_db"] = round(a0 - floor, 3)
                for X in XS:
                    r["rel_%gdB" % X] = binding(seq, i0, a0, lambda p, a, X=X: a - p[1] <= X)
                r["kind"] = kind
                rows.append(r)
            reg_w = window(seq, reg_idx[0], lambda p: p[2])
            ins = [p[1] for p in seq if reg_w[0] <= p[0] <= reg_w[1]]
            summary = {
                "circuit": circuit, "case": case, "grid_step_v": round(seq[1][0] - seq[0][0], 6),
                "scan_range": [seq[0][0], seq[-1][0]], "floor_db_from_spec": floor,
                "region_window_first": reg_w, "A_in_region_min_max_db": [round(min(ins), 3), round(max(ins), 3)],
                "analyst_x0_row": rows[0] if rows[0]["kind"] == "analyst_x0" else None,
            }
            # 주사 요약: 상대 X 가 한 끝이라도 묶는 x0 비율, 절대 하한이 묶는 x0 비율
            scan = [r for r in rows if r["kind"] == "scan"]
            for key in ["abs_floor"] + ["rel_%gdB" % X for X in XS]:
                if key not in scan[0]:
                    continue
                n_func = sum(1 for r in scan if "function" in (r[key]["lo_bind"], r[key]["hi_bind"]))
                n_fail = sum(1 for r in scan if r[key]["window"] is None)
                summary["scan_%s" % key] = {"n_x0": len(scan), "function_binds": n_func, "x0_fails": n_fail}
            with open(OUT_J, "a", encoding="utf-8") as f:
                f.write(json.dumps(summary, ensure_ascii=False) + "\n")
            lines.append(json.dumps(summary, ensure_ascii=False))
    with open(OUT_T, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
