# Build per-pfet original operating-point records (read from source figures/tables).
# All numeric values below are transcribed from the cited source pages, or derived by
# the formula written in "derivation". Writes one JSONL per circuit (append per record).
import json, os

LIB = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library"
OUT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-30/m_kv1_name_tiebreak/orig_ops"
os.makedirs(OUT, exist_ok=True)

def topo(c):
    t = json.load(open(f"{LIB}/{c}.topology.json", encoding="utf-8"))
    rails = set(t["supply_nets"])
    return {d["name"]: d for d in t["netlist"]}, rails

def emit(c, recs):
    nl, rails = topo(c)
    path = f"{OUT}/{c}.jsonl"
    if os.path.exists(path):
        os.remove(path)  # this agent owns this file; rebuild from scratch
    pf = [n for n, d in nl.items() if d["kind"] == "pmos"]
    assert set(pf) == set(r["dev"] for r in recs), (c, set(pf) ^ set(r["dev"] for r in recs))
    for r in recs:
        d = nl[r["dev"]]
        src_rail = d["source"] in rails
        row = {
            "circuit": c, "dev": r["dev"], "orig_name": r.get("orig"),
            "W_um": r.get("W"), "L_um": r.get("L"), "m": r.get("m"),
            "I_A": r.get("I"), "VSG_V": r.get("VSG"), "VSD_V": r.get("VSD"),
            "VSB_V": r.get("VSB", 0.0 if src_rail else None),
            "source_is_rail": src_rail, "is_diode": d["gate"] == d["drain"],
            "process": r["process"], "evidence": r["ev"], "status": r["status"],
        }
        for k in ("field_status", "derivation", "note", "nf"):
            if k in r:
                row[k] = r[k]
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(recs)

SRC = LIB + "/sources"
VSB_NOTE = "VSB_V = V(bulk) - V(source) magnitude for pfet (positive = reverse bias), from node voltages printed on the size figure"

# ---------------- current_reuse_telescopic_ota (Xie & Chen 2019) ----------------
CR_PDF = f"{SRC}/current_reuse_telescopic_ota__xie_chen_2019/source.pdf"
P = "0.18 um CMOS, VDD 1.8 V (p.1 abstract)"
f6 = f"PDF p.6 Fig.6 (a) size images/p06_1.png, (b) DC op images/p06_2.png; {CR_PDF}"
f7 = f"PDF p.7 Fig.7 (a) size images/p07_1.png, (b) DC op images/p07_2.png; {CR_PDF}"
f8 = f"PDF p.8 Fig.8 (a) size images/p08_1.png, (b) DC op images/p08_2.png; {CR_PDF}"
f9 = f"PDF p.9 Fig.9 CMFB size+DC images/p09_1.png, p09_2.png (M3/M4), p09_3.png, p09_4.png (M65/M76); {CR_PDF}"
mnote = "m not printed on Cadence instance (null); W is the printed w expression value"
cr = []
def crr(dev, orig, W, L, I, VSG, VSD, VSB, ev, note=""):
    cr.append(dict(dev=dev, orig=orig, W=W, L=L, m=None, I=I, VSG=VSG, VSD=VSD, VSB=VSB,
                   process=P, ev=ev, status="read",
                   note=(mnote + "; " + VSB_NOTE + ("; " + note if note else ""))))
crr("M6", "M8 (Fig.6)", 21.0, 0.36, 7.878e-6, 0.5024, 0.2603, 0.0, f6, "w=3u*10*0.7 -> 21 um; gate 1.298 V = Vbias_p2(Vbias1); bulk label 1.8")
crr("M7", "M43 (Fig.6)", 9.0, 0.36, 5.103e-6, 0.5237, 0.2603, 0.0, f6, "w=3u*10*0.3 -> 9 um, l=180n*2 -> 0.36 um; gate Vcmfb 1.276 V")
crr("M1a", "M0 (Fig.6, gate Vip)", 6.0, 0.18, 5.723e-6, 0.6397, 0.09972, 0.26, f6, "source 1.54 V, bulk 1.8 V")
crr("M1b", "M7 (Fig.6, gate Vim)", 6.0, 0.18, 5.723e-6, 0.6397, 0.09972, 0.26, f6, "source 1.54 V, bulk 1.8 V")
crr("M2a", "M2 (Fig.6)", 6.0, 0.18, 5.723e-6, 0.6486, 0.9648, 0.36, f6, "source 1.44 V, bulk 1.8 V; gate Vbias_p1 791.4 mV")
crr("M2b", "M6 (Fig.6)", 6.0, 0.18, 5.723e-6, 0.6486, 0.9648, 0.36, f6, "source 1.44 V, bulk 1.8 V")
crr("M8", "M41 (Fig.7 Vom side)", 3.0, 0.36, 1.196e-6, 0.5024, 0.487, 0.0, f7, "drain 1.313 V = gate of M53(M15)")
crr("M11a", "M48 (Fig.7 Vom side)", 15.0, 0.18, 2.199e-6, 0.4676, 0.4676, 0.0, f7)
crr("M11b", "M49 (Fig.7 Vom side)", 15.0, 0.18, 2.199e-6, 0.5999, 0.5999, 0.468, f7, "source 1.332 V, bulk 1.8 V")
crr("M15", "M53 (Fig.7 Vom side)", 65.0, 0.36, 20.45e-6, 0.487, 0.9043, 0.0, f7)
crr("M9a", "M46 (Fig.7 Vom side)", 3.0, 0.54, 338.8e-9, 0.5806, 0.8379, 0.487, f7, "source 1.313 V, bulk 1.8 V (Vdd label); vgs -580.6m read as 580.6 mV")
crr("M13", "M42 (Fig.7 Vom side)", 6.0, 0.36, 2.502e-6, 0.5024, 0.7382, 0.0, f7, "drain 1.062 V feeds M51/M52 nmos diode stack")
crr("M17", "M87 (Fig.7 Vop side)", 3.0, 0.36, 1.196e-6, 0.5024, 0.487, 0.0, f7, "drain 1.313 V = gate of M77(M25)")
crr("M20a", "M81 (Fig.7 Vop side)", 15.0, 0.18, 2.199e-6, 0.4676, 0.4676, 0.0, f7)
crr("M20b", "M80 (Fig.7 Vop side)", 15.0, 0.18, 2.199e-6, 0.5999, 0.5999, 0.468, f7, "source 1.332 V, bulk 1.8 V")
crr("M25", "M77 (Fig.7 Vop side)", 65.0, 0.36, 20.45e-6, 0.487, 0.9043, 0.0, f7)
crr("M18a", "M83 (Fig.7 Vop side)", 3.0, 0.54, 338.8e-9, 0.5806, 0.8379, 0.487, f7, "source 1.313 V, bulk 1.8 V")
crr("M22", "M88 (Fig.7 Vop side)", 6.0, 0.36, 2.502e-6, 0.5024, 0.7382, 0.0, f7, "drain 1.062 V feeds M79/M78 nmos diode stack")
crr("M18_bg", "M18 (Fig.8)", 3.0, 0.36, 1.2e-6, 0.5024, 0.5024, 0.0, f8, "Iref idc=1.2u")
crr("M60", "M60 (Fig.8)", 3.0, 0.36, 1.395e-6, 0.5024, 1.33, 0.0, f8, "drain 470.2 mV = Vbias_n2(Vbias4)")
crr("M61", "M61 (Fig.8)", 3.0, 0.36, 1.273e-6, 0.5024, 0.8011, 0.0, f8, "drain 998.9 mV = Vbias_n1(Vbias3)")
crr("M58", "M58 (Fig.8)", 0.75, 1.44, 1.534e-6, 0.7483, 0.1893, -0.02, f8,
    "UNCERTAIN VSB: bulk pin labelled 'vdd' (lowercase, not the 'Vdd' supply pin) and its printed DC value reads '1.52' (glyph run '1.521' overlaps the '\"pch\"' label); source 1.54 V -> V(bulk)-V(source) = -0.02 V (forward); if the bulk were the 1.8 V supply it would be +0.26 V")
crr("M57", "M57 (Fig.8)", 6.0, 1.44, 1.534e-6, 0.559, 0.559, 0.17, f8,
    "UNCERTAIN VSB: same 'vdd' bulk label printed '1.52' V; source 1.35 V -> 0.17 V (would be 0.45 V if bulk = 1.8 V supply)")
crr("M36a", "M3 (Fig.9 CMFB)", 0.52, 0.36, 350.3e-9, 0.5237, 0.5237, 0.0, f9, "gate=drain Vcmfb 1.276 V")
crr("M36b", "M4 (Fig.9 CMFB)", 0.52, 0.36, 384.2e-9, 0.5288, 0.5288, 0.0, f9, "gate=drain 1.271 V")
crr("M39", "M65 (Fig.9 Voc_des divider)", 0.1, 3.0, 260.4e-9, 0.9, 0.9, 0.0, f9, "w=100n l=3u; gate=drain Voc_des 900 mV")
crr("M40", "M76 (Fig.9 Voc_des divider)", 0.1, 3.0, 260.4e-9, 0.9, 0.9, 0.0, f9, "source Voc_des 900 mV, gate=drain=0; bulk wire goes to the source node (label 900m), so VSB=0")

# ---------------- erfc_ota (Wu 2025) ----------------
E_PDF = f"{SRC}/erfc_ota__wu_2025/source.pdf"
EP = "0.18 um CMOS, VDD 1.8 V (p.1 abstract, p.12 sec.4)"
T1 = f"PDF p.9 Table 1 (W/L); {E_PDF}"
F6 = f"PDF p.8 Figure 6 + side table VDD 1.8 V, VCP 1.1 V, VCN 0.7 V, IB 2 uA, IC 0.2 uA; {E_PDF}"
IB = 2e-6; IC = 0.2e-6
em = "m not given (Table 1 lists W/L only; W treated as printed); bulk not drawn in Fig.6 (3-terminal symbols) -- topology bulk=vdd is an O-174 assumption, so VSB for non-rail sources is null"
er = []
def err(dev, W, L, I, deriv, ev, VSG=None, VSD=None, VSB=None, fs=None, note=""):
    r = dict(dev=dev, orig=dev, W=W, L=L, m=None, I=I, VSG=VSG, VSD=VSD, process=EP, ev=ev,
             status="derived", derivation=deriv, note=em + ("; " + note if note else ""))
    if VSB is not None:
        r["VSB"] = VSB
    if fs:
        r["field_status"] = fs
    er.append(r)
txt11 = f"PDF p.11 sec.3.5 'Under static conditions, the currents of M1A,1B and M2A,2B are all equal to 0.5IB'"
for d in ("M1A", "M1B", "M2A", "M2B"):
    err(d, 24.0, 0.6, 0.5 * IB, "I = 0.5*IB (stated) with IB = 2 uA (Fig.6 table)", f"{txt11}; {F6}; {T1}",
        fs={"I_A": "derived(read statement x read IB)", "W_L": "read", "VSG_VSD": "missing (no node voltages; input CM 800 mV p.12 only)"})
for d, n in (("M11", "n_m11d"), ("M12", "n_m12d")):
    err(d, 24.0, 0.6, 0.5 * IB, f"KCL at drain {n}: only the '0.5IB' ideal sink (Fig.6) and the gate of M15/M16 -> I = 0.5*IB = 1 uA", f"{F6}; PDF p.5 Fig.3b text; {T1}")
for d, a in (("M13", "A: M11 + M2A + M2B"), ("M14", "B: M12 + M1A + M1B")):
    err(d, 24.0, 0.3, 1.5 * IB, f"KCL at node {a} = 3 x 0.5*IB = 1.5*IB = 3 uA", f"{F6}; {txt11}; {T1}",
        note="consistency: 2*IC + 2*1.5IB + 2*IB = 0.4 + 6 + 4 = 10.4 uA = quiescent current (p.1, p.12)")
for d in ("M15", "M16"):
    err(d, 1.0, 20.0, IC, "I = IC = 0.2 uA (ideal source IC feeds the M15/M16 source node; M13/M14 gate draws no DC)", f"{F6}; PDF p.7 sec.3.2 (M15,M16 saturation); {T1}")
outd = ("I(M3A) = 0.3*IB (p.11), M3B:M3A = 15:3 (p.6) -> I(M3B) = 1.5*IB; KCL at M5 source: I(M5) = I(M3B) - I(M1A) = 1.5IB - 0.5IB = IB = 2 uA; "
        "series stack M9-M7-M5 (and M10-M8-M6 by the same ratio on the M4 side) -> I = IB")
for d, W in (("M9", 48.0), ("M10", 48.0), ("M7", 24.0), ("M8", 24.0)):
    err(d, W, 0.3, IB, outd, f"{F6} ('IB' arrow on M10/M8 branch); PDF p.6 (15:3:2); PDF p.11 sec.3.5; {T1}",
        note="consistency with 10.4 uA quiescent total (see M13)")
st = "PDF p.7 'In a static state, no current flows through the series RL CBAT, and VC is equal to VE'; PDF p.7 sec.3.2 'M19 to M21 are operated in the deep triode region, functioning as active resistors'"
for d in ("M19", "M20"):
    err(d, 3.0, 1.0, 0.0, "static: drain node only drives the M5/M6 gate and CBAT1 -> DC current 0, VSD 0", f"{st}; {F6}; {T1}",
        VSD=0.0, VSB=0.0, fs={"VSG": "missing (V(Z) not given)"}, note="source=bulk=vcn per topology O-174 (not drawn)")
err("M21", 3.0, 1.0, 0.0, "static: drain node n_m8g only drives M7/M8 gates and CBAT2 -> DC current 0, VSD 0; VSG = VCP - VCN = 1.1 - 0.7 = 0.4 V",
    f"{st}; {F6}; {T1}", VSG=0.4, VSD=0.0, VSB=0.0, note="source=bulk=vcp per topology O-174 (not drawn)")

# ---------------- rfc_ota (Matibag 2024) ----------------
R_PDF = f"{SRC}/rfc_ota__matibag_2024/source.pdf"
RP = "UMC 180 nm, VDD 1.8 V (p.10 abstract, p.11 requirements)"
T2 = f"PDF p.27 Table 2 + p.28 Figure 6 (W/L); {R_PDF}"
F9 = f"PDF p.34 Figure 9 (bias W/L); {R_PDF}"
DES = ("design-intent current from the thesis hand sizing (square law, Vov = 0.15 V for all devices p.17, KP = 63 uA/V^2 p.17, KN = 280 uA/V^2 p.18): "
       "gm1(conv) = 2*pi*CL*GBW = 2*pi*2.25 pF*100 MHz = 1.414 mS (p.16 eq.7), I(M1 conv) = gm1*Vov/2 = 0.5*KP*(W/L)*Vov^2 = 0.5*63u*149.59*0.0225 = 106.0 uA (p.18 eq.10, W/L p.20 Table 1)")
rn = "NOT a simulated DC op (thesis prints no per-device op); simulated amplifier current = 457.2 uA (p.35 Table 4) vs design-intent 424 uA; VSG = |VT| + Vov but VT not given -> null; m not given"
rr = []
def rrr(dev, W, L, I, deriv, ev, VSG=None, VSB=None, status="derived", note=""):
    r = dict(dev=dev, orig=dev, W=W, L=L, m=None, I=I, VSG=VSG, VSD=None, process=RP, ev=ev, status=status,
             derivation=deriv, note=rn + ("; " + note if note else ""))
    if VSB is not None:
        r["VSB"] = VSB
    rr.append(r)
rrr("M0", 161.57, 0.54, 212.1e-6, DES + "; I(M0) = 0.5*KP*299.2*Vov^2 = 212.1 uA = 2*I(M1 conv)", T2)
for d in ("M1a", "M1b", "M2a", "M2b"):
    rrr(d, 40.39, 0.54, 53.0e-6, DES + "; RFC splits each input device in half (p.22, p.25): I = 106.0/2 = 53.0 uA = I(M0)/4", f"{T2}; PDF p.22 sec.3.1")
kc = ("KCL (K = 3, p.22): I(M4b) = I(M12) = I(M1b) = 53 uA, I(M4a) = 3*53 = 159 uA, node Y: I(M6) = I(M4a) - I(M2a) = 106 uA; "
      "series M6-M8-M10 (and M5-M7-M9) -> 106.0 uA = Ib (also 0.5*KP*149.59*Vov^2 = 106.0 uA for M7..M10 W/L 149.59)")
for d, W, L in (("M7", 80.78, 0.54), ("M8", 80.78, 0.54), ("M9", 53.85, 0.36), ("M10", 53.85, 0.36)):
    rrr(d, W, L, 106.0e-6, DES + "; " + kc, f"{T2}; PDF p.22-p.26")
bq = ("bias loop scaled 1:4 vs amplifier (p.33): Q9/Q7 'must drive the same current' as M0 then sizes /4 -> 212.1/4 = 53.0 uA "
      "(also 0.5*KP*(40.4/0.54)*Vov^2 = 53.0 uA; NMOS Q3 0.5*KN*(9.09/0.54)*Vov^2 = 53.0 uA, same)")
rrr("Q9", 40.4, 0.54, 53.0e-6, bq, f"{F9}; PDF p.33 sec.4.2")
rrr("Q7", 40.4, 0.54, 53.0e-6, bq, f"{F9}; PDF p.33 sec.4.2")
rrr("Q11", 40.4, 0.54, 53.0e-6, bq + "; Q11 same W/L and gate VBP1 as Q9 -> mirror 1:1", f"{F9}; PDF p.33")
for d, s in (("Q8", "Q9"), ("Q6", "Q7"), ("Q10", "Q11")):
    rrr(d, 40.4, 0.66, 53.0e-6, bq + f"; series with {s} -> same current", f"{F9}; PDF p.33")
rrr("Q14", 10.1, 0.66, 53.0e-6, bq + "; Q14 diode current = I(Q13) = I(Q12), Q12 same W/L and gate VBN1 as Q3 -> 53.0 uA", f"{F9}; PDF p.32-p.33",
    note="Q14 width printed 'W = 10.1' without unit; p.33 says diode Q5/Q14 are 4x smaller than loop devices (40.4/4 = 10.1 um)")
rr.append(dict(dev="Q18", orig="Q18", W=0.24, L=0.36, m=None, I=None, VSG=1.8, VSD=None, process=RP,
               ev=f"{F9}; PDF p.32-p.34 (start-up, 'smaller size ratio')", status="missing",
               derivation="VSG = VDD - 0 = 1.8 V (source vdd, gate gnd); steady-state current not given (start-up pull-up against Q17)",
               note="start-up device; current unknown"))

# ---------------- cnr_ota (Wulff 2024, sky130 xschem) ----------------
C_SCH = f"{SRC}/cnr_ota__wulff_2024/CNR_OTA.sch"
SIZES = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_heldout/D_cnr/D_cnr.sizes.md (sub-cell cnr_atr_sky130nm .sch, library @2024-03-01; raw D_cnr.flat_lib20240301.json)"
CP = "sky130 (130 nm) sky130_fd_pr pfet_01v8, VDD_1V8 = 1.8 V"
LOADS = f"{SRC}/cnr_ota__wulff_2024/sim/load.spi line 3 'IDC 0 IBPSR dc 2u'"
cn = ("no DC op published (sim/README.md gives only idd 90.682 uA Sch_typ); W/L from sub-cell; currents by 1:1 mirrors of identical cells from IBPSR 2 uA (ignores VDS mismatch); "
      "consistency: sum of VDD branch currents 53 (pfet) + 24 (SF nfets x31/x33/x35) + 11.41 (resistor string x40-x39-x3 157.8 kOhm) = 88.4 uA vs sim idd 90.682 uA (2.5 % low)")
cnl = json.load(open(f"{LIB}/cnr_ota.topology.json", encoding="utf-8"))["netlist"]
cr_ = []
def cell(dev):
    c = [d for d in cnl if d["name"] == dev][0]
    return c["_cell"].split()[0], c["_src"].split(":")[-1]
GEOM = {"CNRATR_PCH_4C4F0": (3.84, 1.26), "CNRATR_PCH_4C1F2": (3.84, 0.252), "CNRATR_PCH_4C8F0": (3.84, 2.7)}
def cnr(dev, I, deriv, status="derived", extra=""):
    cl, line = cell(dev)
    W, L = GEOM[cl]
    cr_.append(dict(dev=dev, orig=dev, W=W, L=L, m=1, nf=2, I=I, VSG=None, VSD=None, process=CP,
                    ev=f"{C_SCH}:{line} ({cl}); W/L/nf {SIZES}; bias {LOADS}", status=status, derivation=deriv,
                    note=cn + "; W is total over nf=2, L = 2024-03-01 library (U6 (a))" + ("; " + extra if extra else "")))
tail = "tail x23[3:0] = 4 x 2 uA = 8 uA (4C8F0 cells mirroring diode x24 fed by IBPSR 2 uA); each input (x2.M1 VIP, x22.M1 VIN) = 4 uA at balance"
cnr("x26.M1", 2e-6, "diode VBP fed by x25.M1 (4C8F0 = x24 cell, gate IBPSR) -> 2 uA")
for i in range(6):
    cnr(f"x28[{i}].M1", 2e-6, "gate VBP, same cell (4C4F0) as diode x26 -> 1:1 mirror 2 uA (6 parallel = 12 uA into diode x30 VCN)")
cnr("x27.M1", 2e-6, "diode VCP fed by x29.M1 (4C8F0 = x24 cell, gate IBPSR) -> 2 uA")
cnr("x7.M1", 4e-6, tail + "; x7-x8 stack carries x2.M1 (VIP) current into VBP2 -> 4 uA")
cnr("x8.M1", 4e-6, tail + "; series with x7 -> 4 uA")
cnr("x11.M1", 4e-6, "gate VBP2, same cell as x7 -> 1:1 mirror 4 uA (into VBN1 diode chain)")
cnr("x12.M1", 4e-6, "series with x11 -> 4 uA")
cnr("x18.M1", 4e-6, tail + "; x18-x19 stack carries x22.M1 (VIN) current into VBP1 -> 4 uA")
cnr("x19.M1", 4e-6, tail + "; series with x18 -> 4 uA")
cnr("x20.M1", 4e-6, "gate VBP1, same cell as x18 -> 1:1 mirror 4 uA (into VBN2 diode chain)")
cnr("x21.M1", 4e-6, "series with x20 -> 4 uA")
cmfb = "CMFB pair x42 (LPCO)/x43 (VCREF) on tail x44 = 2 uA (gate VBP, same cell as x26); ASSUMES settled loop V(LPCO)=V(VCREF) -> 1 uA each (CMFB loop DC gain only 17 dB, sim/README.md, so split may deviate)"
cnr("x44.M1", 2e-6, "gate VBP, same cell (4C4F0) as diode x26 -> 2 uA")
cnr("x42.M1", 1e-6, cmfb)
cnr("x43.M1", 1e-6, cmfb)
cnr("x51.M1", 1e-6, cmfb + "; x42 -> diode x45 (VCBN1) -> mirror x52 (same 4C8F0) -> diode x51 VCBP -> 1 uA")
cnr("x49.M1", 1e-6, cmfb + "; gate VCBP, same cell as diode x51 -> 1 uA into VCONP")
cnr("x50.M1", 1e-6, cmfb + "; gate VCBP, same cell as diode x51 -> 1 uA into VCOPP")
for i in range(2):
    cnr(f"x5[{i}].M1", 4e-6, "gate VBP2, same cell (4C4F0) as x7 -> 1:1 mirror 4 uA each")
    cnr(f"x16[{i}].M1", 4e-6, "gate VBP1, same cell (4C4F0) as x18 -> 1:1 mirror 4 uA each")
    cnr(f"x6[{i}].M1", 4.5e-6, "KCL at VCOPP: x5[1:0] 8 uA + x50 1 uA = 9 uA through x6[1:0] -> 4.5 uA each (check VCOPN: x2[1:0] 2x4 uA + x48 1 uA = 9 uA)",
        extra="depends on CMFB 1 uA assumption")
    cnr(f"x17[{i}].M1", 4.5e-6, "KCL at VCONP: x16[1:0] 8 uA + x49 1 uA = 9 uA through x17[1:0] -> 4.5 uA each (check VCONN: x13[1:0] 2x4 uA + x47 1 uA = 9 uA)",
        extra="depends on CMFB 1 uA assumption")

counts = {}
counts["current_reuse_telescopic_ota"] = emit("current_reuse_telescopic_ota", cr)
counts["erfc_ota"] = emit("erfc_ota", er)
counts["rfc_ota"] = emit("rfc_ota", rr)
counts["cnr_ota"] = emit("cnr_ota", cr_)
print(counts)
