"""
Independent re-derivation of gm/ID sizing for the Xie & Chen (UT Austin)
"A 126uW Current-Reuse Telescopic OTA with Class-AB Output Stage" paper,
re-targeted to sky130 (nfet_01v8/pfet_01v8) using the analog-gmid-design skill's
real characterized LUT (sky130_nfet_pfet_lut_sample.npz, W_ref=5um).

Design targets are taken VERBATIM from the paper (Table I, Section III, Eq 1-6):
  - gm1(stage-1, per leg, PMOS+NMOS combined) = 238uS  -> gmp1=gmn4=119uS (Eq 5)
  - gm2(stage-2 signal path) = 3mS (Eq 6 solved by paper)
  - Cc = 500fF, M6:M7 = 0.7:0.3 tail current split (paper Section III.C, heuristic)

gm/ID operating points are a fresh design choice for sky130 (moderate inversion,
gm/ID=12 S/A for the signal path -- inside the sky130 real-LUT range NMOS<=29.93,
PMOS<=32.20 S/A, comfortably moderate-inversion so W stays reasonable per
sky130-worked-example.md Sec 5's "don't push gm/ID near the LUT ceiling" lesson).
"""
import sys, math, json
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import SemiEmpiricalGmIdLUT, size_transistor, gm_from_fT

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
d = np.load(LUTFILE)
W_REF = 5e-6

# NOTE: d["L"] is ALREADY in meters (e.g. 1.5e-07 == 0.15um) -- do NOT multiply by 1e-6 again
# (that bug was caught here by cross-checking against real ngspice .op runs: forward-sizing with
# the erroneous *1e-6 scaling put every L query far outside the LUT's actual (corrupted) grid range,
# producing wildly wrong extrapolated ID/gm -- SPICE ID_sim/ID_target ratios of 0.03x to 41x with no
# consistent pattern were the symptom that exposed it).
nmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_n"], d["GM_n"], d["GDS_n"], d["CGG_n"], W_ref=W_REF)
pmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_p"], d["GM_p"], d["GDS_p"], d["CGG_p"], W_ref=W_REF)

print("L grid (m):", d["L"], " (== um:", d["L"]*1e6, ")")
print("VDS grid range:", d["VDS"].min(), d["VDS"].max())

def size(name, role, lut, gm, gm_id, L, vds, vs=0.0):
    r = size_transistor(gm, gm_id, L, lut, vds, vs)
    gain = lut.gm_gds_ratio(gm_id, L, vds, vs)
    cgg = lut.cgg_absolute(gm_id, L, vds, vs, r.W)
    out = dict(name=name, role=role, gm_uS=gm*1e6, gm_id=gm_id, L_um=L*1e6, VDS_V=vds,
               ID_uA=r.ID*1e6, W_um=r.W*1e6, gain=gain, Cgg_fF=cgg*1e15)
    print(f"{name:22s} {role:38s} gm={gm*1e6:8.2f}uS gm/ID={gm_id:5.1f} L={L*1e6:.2f}um VDS={vds:.2f}V "
          f"-> ID={r.ID*1e6:8.3f}uA W={r.W*1e6:9.4f}um gain={gain:7.2f} Cgg={cgg*1e15:7.3f}fF")
    return out

results = []

# ---- Stage 1: current-reuse telescopic core (paper Eq 3-5) ----
# gm1_total(leg) = gmn4 + gmp1 = 238uS ; paper assumes gmp1=gmn4 => 119uS each
#
# VDS headroom budget: the branch is a SIX-transistor series stack between VDD and GND
# (M6 -> M1a -> M2a -> M3a -> M4a -> M5), so per-device VDS values must sum to <= VDD=1.8V --
# an early draft of this script used VDS=0.5-0.6V per device (borrowed loosely from the paper's
# per-device numbers without checking the stack sum) which summed to 3.2V, physically impossible
# for a 1.8V supply. Corrected budget (cascodes get thin VDS just above Vdsat, input/tail devices
# get more since they set headroom for input CM range and output-impedance quality):
#   M6=0.30 + M1a=0.40 + M2a=0.20 + M3a=0.20 + M4a=0.40 + M5=0.30 = 1.80V exactly.
VDS_M6, VDS_M1, VDS_M2, VDS_M3, VDS_M4, VDS_M5 = 0.30, 0.40, 0.20, 0.20, 0.40, 0.30
gmp1 = 119e-6
gmn4 = 119e-6
L1 = 0.15e-6   # sky130 nfet_01v8/pfet_01v8 min channel
GM_ID_SIG = 12.0   # moderate inversion signal-path operating point (design choice)

results.append(size("M1a/M1b", "stage-1 PMOS input (current-reuse top half, gate=Vip/Vim)", pmos, gmp1, GM_ID_SIG, L1, VDS_M1))
results.append(size("M4a/M4b", "stage-1 NMOS input (current-reuse bottom half, SAME gate net as M1)", nmos, gmn4, GM_ID_SIG, L1, VDS_M4))
# cascodes: fixed-bias devices, carry same branch current as the input pair they stack with.
# gm target for the cascode itself is a free design choice (governs its own gm/gds contribution to r_out);
# choose to match its adjoining input device's gm so the pair sizes as a matched "row" (see stick diagram section).
results.append(size("M2a/M2b", "stage-1 PMOS cascode (gate=Vbias2 fixed)", pmos, gmp1, GM_ID_SIG, L1, VDS_M2))
results.append(size("M3a/M3b", "stage-1 NMOS cascode (gate=Vbias3 fixed)", nmos, gmn4, GM_ID_SIG, L1, VDS_M3))

# Tail devices: M5 sinks ID(M4a)+ID(M4b) = 2x branch current. Strong-inversion-leaning (matching-critical, SKILL.md sec2).
L_tail = 0.5e-6
ID_branch = gmn4 / GM_ID_SIG   # = gmp1/GM_ID_SIG too since equal
GM_ID_TAIL = 10.0
gm5 = 2*ID_branch*GM_ID_TAIL
results.append(size("M5", "stage-1 tail current sink (sinks 2x branch ID)", nmos, gm5, GM_ID_TAIL, L_tail, VDS_M5))

# M6/M7: tail current SOURCE, split 0.7:0.3 (paper Section III.C heuristic) but total = 2x branch current
L_top = 0.35e-6
GM_ID_TOP = 12.0
gm_top_total = 2*ID_branch*GM_ID_TOP
results.append(size("M6", "top load, Vbias1 (0.7 share, fixed bias)", pmos, 0.7*gm_top_total, GM_ID_TOP, L_top, VDS_M6))
results.append(size("M7", "top load, Vcmfb (0.3 share, CMFB-controlled)", pmos, 0.3*gm_top_total, GM_ID_TOP, L_top, VDS_M6))

# ---- Stage 2: Class-AB output core (paper Eq 6, gm2=3mS) ----
# Paper's own two-step logic (Section III.B, verbatim): (1) size W assuming gm/Id=17uS/uA at the
# "design" current (ID=176uA) that gives gm2=3mS -- this fixes the geometry. (2) the actual
# quiescent bias is then pushed to "barely-on" (much lower ID) by the Class-AB floating-bias loop,
# which -- at the SAME W -- moves the device deeper into moderate/weak inversion (higher gm/ID),
# so gm2 is approximately preserved while ID drops ~8x (paper: 176uA design point -> ~22uA actual
# quiescent). This IS the gm/ID methodology's central claim (gm/ID as universal efficiency axis)
# playing out inside the paper's own class-AB story -- reproduced here with a real reverse LUT lookup
# instead of asserting it.
gm2 = 3.0e-3
L2 = 0.35e-6
GM_ID_S2_NOMINAL = 17.0   # paper's own stated design-point gm/Id (Section III.B)
ID2_nominal = gm2 / GM_ID_S2_NOMINAL   # = 176.47uA, matches paper's stated 176uA exactly

def reverse_lookup_gm_at_id(lut, L, vds, vs, W, ID_target):
    """Given a FIXED W and a target ID, find the VGS/gm/gm_id the device actually delivers there
    -- the inverse of size_transistor() (SKILL.md sec 2.1 rule 1: 'forward sizing gives an
    unrealistic W -> fix W to a realistic value, read back gm/ID as the result')."""
    W_ref = lut._w_ref_effective(L)
    target_raw = ID_target * W_ref / W
    raws = np.array([lut._query(lut.ID, L, vgs, vds, vs) for vgs in lut.VGS_grid])
    order = np.argsort(raws)
    vgs = float(np.interp(target_raw, raws[order], lut.VGS_grid[order]))
    raw_gm = lut._query(lut.GM, L, vgs, vds, vs)
    gm = raw_gm * W / W_ref
    return vgs, gm, gm / ID_target

# Forward-size at gm/ID=17 first to see if W is realistic (mirrors sky130-worked-example.md sec5's
# own PMOS-mobility finding: forward sizing at a paper-quoted gm/ID can blow up in sky130 PMOS).
fwd15 = size_transistor(gm2, GM_ID_S2_NOMINAL, L2, pmos, 0.9)
fwd16 = size_transistor(gm2, GM_ID_S2_NOMINAL, L2, nmos, 0.9)
print(f"\nForward sizing check @ gm/ID=17: M15(PMOS) W={fwd15.W*1e6:.1f}um   M16(NMOS) W={fwd16.W*1e6:.1f}um")

# M15/M25 (PMOS): forward W is unrealistically large (sky130 PMOS low-mobility effect, same
# phenomenon documented in sky130-worked-example.md sec5) -> apply the "flip" rule: cap W to the
# skill's own established realistic ceiling (w_max=200um, same convention used throughout
# sky130-worked-example.md sec9/11/12), then read back the gm/ID this W actually delivers at the
# design current ID2_nominal.
W15_CAP = 200e-6
vgs15n, gm15n, gmid15n = reverse_lookup_gm_at_id(pmos, L2, 0.9, 0.0, W15_CAP, ID2_nominal)
r15 = dict(name="M15/M25", role="stage-2 PMOS output -- STEP1 nominal (W capped 200um, gm/ID flipped -- see note)",
           gm_uS=gm15n*1e6, gm_id=gmid15n, L_um=L2*1e6, VDS_V=0.9, ID_uA=ID2_nominal*1e6, W_um=W15_CAP*1e6,
           gain=pmos.gm_gds_ratio(gmid15n, L2, 0.9, 0.0), Cgg_fF=pmos.cgg_absolute(gmid15n, L2, 0.9, 0.0, W15_CAP)*1e15)
print(f"M15/M25 (flip-sized): W={W15_CAP*1e6:.0f}um(capped) -> gm/ID={gmid15n:.2f} S/A (paper quoted 17, sky130 PMOS "
      f"needs strong inversion at this W to hit gm2/2 with a realistic W) ID={ID2_nominal*1e6:.2f}uA gm={gm15n*1e6:.1f}uS")
results.append(r15)

# M16/M26 (NMOS): forward W is already realistic (<200um) -> keep the direct forward sizing.
r16 = size("M16/M26", "stage-2 NMOS output -- STEP1 nominal W sizing (paper's gm/Id=17 design point, forward-sized OK)",
           nmos, gm2, GM_ID_S2_NOMINAL, L2, 0.9)
results.append(r16)

# STEP2: Class-AB barely-on quiescent bias, SAME W as STEP1, ~1/8 the nominal design current
# (paper: 176uA(design) -> ~22uA(actual) total output-stage quiescent current after class-AB
# barely-on biasing; exact per-device split is a class-AB floating-bias design freedom the paper
# does not itemize per-device, so 1/8 of ID2_nominal per device is presented as a design choice
# sized to land near the paper's reported quiescent magnitude, not a re-derivation of the paper's
# own exact number).
ID15_q = ID2_nominal / 16.0   # paper: "final output stage current is around 22uA" == ID(M15)+ID(M16) combined
ID16_q = ID2_nominal / 16.0
vgs15q, gm15q, gmid15q = reverse_lookup_gm_at_id(pmos, L2, 0.9, 0.0, W15_CAP, ID15_q)
vgs16q, gm16q, gmid16q = reverse_lookup_gm_at_id(nmos, L2, 0.9, 0.0, r16["W_um"]*1e-6, ID16_q)
print(f"\n-- Class-AB STEP2 barely-on quiescent bias (same W as STEP1, reverse LUT lookup) --")
print(f"M15/M25 barely-on: ID_q={ID15_q*1e6:.3f}uA VGS={vgs15q:.4f}V gm={gm15q*1e6:.2f}uS gm/ID={gmid15q:.2f} S/A  "
      f"-> gm retained {100*gm15q/(gm2):.1f}% of design gm2 at {100*ID15_q/ID2_nominal:.1f}% of design ID")
print(f"M16/M26 barely-on: ID_q={ID16_q*1e6:.3f}uA VGS={vgs16q:.4f}V gm={gm16q*1e6:.2f}uS gm/ID={gmid16q:.2f} S/A  "
      f"-> gm retained {100*gm16q/(gm2):.1f}% of design gm2 at {100*ID16_q/ID2_nominal:.1f}% of design ID")
results.append(dict(name="M15/M25 (barely-on Q-point)", role="Class-AB actual quiescent bias (same W, STEP2)",
                     gm_uS=gm15q*1e6, gm_id=gmid15q, L_um=L2*1e6, VDS_V=0.9, ID_uA=ID15_q*1e6, W_um=r15["W_um"],
                     gain=pmos.gm_gds_ratio(gmid15q, L2, 0.9, 0.0), Cgg_fF=r15["Cgg_fF"]))
results.append(dict(name="M16/M26 (barely-on Q-point)", role="Class-AB actual quiescent bias (same W, STEP2)",
                     gm_uS=gm16q*1e6, gm_id=gmid16q, L_um=L2*1e6, VDS_V=0.9, ID_uA=ID16_q*1e6, W_um=r16["W_um"],
                     gain=nmos.gm_gds_ratio(gmid16q, L2, 0.9, 0.0), Cgg_fF=r16["Cgg_fF"]))
ID2 = ID15_q + ID16_q  # actual quiescent current used downstream for the bias-fraction devices

# floating-battery / bias devices of the Class-AB core -- small fraction of ID2 (functional role: bias the AB loop, SKILL.md 1.5)
GM_ID_AB = 12.0
ID_ab_bias = 0.12*ID2
gm_ab_bias = ID_ab_bias*GM_ID_AB
results.append(size("M14a/b (NMOS batt)", "Class-AB floating battery (NMOS diode leg)", nmos, gm_ab_bias, GM_ID_AB, L2, 0.6))
results.append(size("M11a/b (PMOS batt)", "Class-AB floating battery (PMOS diode leg)", pmos, gm_ab_bias, GM_ID_AB, L2, 0.6))
ID_ab_src = 0.24*ID2
gm_ab_src = ID_ab_src*GM_ID_AB
results.append(size("M8/M13 (top src)", "Class-AB top current source (gate=Vbias1)", pmos, gm_ab_src, GM_ID_AB, L2, 0.6))

# ---- Bias generator (Fig.4) + CMFB (Fig.5) -- functional-role-derived local targets (SKILL.md 1.5) ----
Lb = 0.5e-6
GM_ID_B = 12.0
Ibias_ref = 1.2e-6   # reference branch current (design choice: low-power replica-bias branch)
gmb = Ibias_ref*GM_ID_B
results.append(size("M27/M28/M29", "bias-gen PMOS mirror (derives Vbias1 replica of tail-source path)", pmos, gmb, GM_ID_B, Lb, 0.6))
results.append(size("M30-M32/M35", "bias-gen NMOS mirror/cascode (derives Vbias3/Vbias4, replicates Vy)", nmos, gmb, GM_ID_B, Lb, 0.6))
results.append(size("M33/M34", "bias-gen Vx/Vy replica cascode (derives Vbias2)", pmos, gmb, GM_ID_B, Lb, 0.6))

ID_cmfb = 2.0e-6
GM_ID_CMFB = 12.0
gm_cmfb = ID_cmfb*GM_ID_CMFB
results.append(size("M36a/M36b", "CMFB output-stage mirror (gate=Vcmfb, feeds M7)", pmos, gm_cmfb, GM_ID_CMFB, 0.35e-6, 0.6))
ID_cmfb_ip = 1.0e-6
gm_cmfb_ip = ID_cmfb_ip*GM_ID_CMFB
results.append(size("M37a/M37b", "CMFB NMOS diff pair (senses Voc vs Voc_des)", nmos, gm_cmfb_ip, GM_ID_CMFB, 0.35e-6, 0.6))
results.append(size("M38", "CMFB tail", nmos, ID_cmfb*GM_ID_CMFB, GM_ID_CMFB, Lb, 0.3))
results.append(size("M39/M40", "CMFB Voc_des generator (long-L for process-variation immunity)", pmos, ID_cmfb_ip*GM_ID_CMFB, GM_ID_CMFB, 1.0e-6, 0.6))

print()
print("Stage-1 branch current (per leg, a or b):", ID_branch*1e6, "uA")
print("Stage-1 total gm1 (=gmp1+gmn4):", (gmp1+gmn4)*1e6, "uS   (paper target 238uS)")
print("Stage-2 gm2:", gm2*1e3, "mS  (paper target 3mS)")

with open(r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\current-reuse-telescopic-ota-report\sizing_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nWrote sizing_results.json (%d devices)" % len(results))

# ---- VGS lookup for SPICE single-device cross-check ----
spice_check_devices = [
    ("M1a", pmos, GM_ID_SIG, L1, VDS_M1, gmp1),
    ("M4a", nmos, GM_ID_SIG, L1, VDS_M4, gmn4),
    ("M2a", pmos, GM_ID_SIG, L1, VDS_M2, gmp1),
    ("M3a", nmos, GM_ID_SIG, L1, VDS_M3, gmn4),
    ("M5",  nmos, GM_ID_TAIL, L_tail, VDS_M5, gm5),
    ("M6",  pmos, GM_ID_TOP, L_top, VDS_M6, 0.7*gm_top_total),
    ("M7",  pmos, GM_ID_TOP, L_top, VDS_M6, 0.3*gm_top_total),
    ("M16", nmos, GM_ID_S2_NOMINAL, L2, 0.9, gm2),
]
print("\n-- VGS lookup for SPICE cross-check --")
vgs_table = {}
for name, lut, gm_id, L, vds, gm in spice_check_devices:
    vgs = lut._solve_vgs(gm_id, L, vds, 0.0)
    ID_t = gm/gm_id
    vgs_table[name] = dict(vgs=vgs, vds=vds, L_um=L*1e6, ID_target_uA=ID_t*1e6, kind=("pmos" if lut is pmos else "nmos"))
    print(f"{name:5s} kind={vgs_table[name]['kind']:4s} VGS={vgs:.5f}V VDS={vds}V L={L*1e6}um ID_target={ID_t*1e6:.4f}uA")
# M15 barely-on-capped-W special case
vgs_table["M15"] = dict(vgs=vgs15n, vds=0.9, L_um=L2*1e6, ID_target_uA=ID2_nominal*1e6, kind="pmos")
print(f"M15    kind=pmos VGS={vgs15n:.5f}V VDS=0.9V L={L2*1e6}um ID_target={ID2_nominal*1e6:.4f}uA (W-capped)")

Wtable = {r["name"].split("/")[0].replace(" (barely-on Q-point)","").replace(" (flip-sized)",""): r["W_um"] for r in results}
with open(r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\current-reuse-telescopic-ota-report\vgs_table.json", "w") as f:
    json.dump(dict(vgs=vgs_table, W={
        "M1a": r15["W_um"] if False else None,  # placeholder, filled below explicitly
    }), f)
# Explicit W map for spice netlist generator (avoid fragile name parsing)
Wmap = {
    "M1a": [r for r in results if r["name"]=="M1a/M1b"][0]["W_um"],
    "M4a": [r for r in results if r["name"]=="M4a/M4b"][0]["W_um"],
    "M2a": [r for r in results if r["name"]=="M2a/M2b"][0]["W_um"],
    "M3a": [r for r in results if r["name"]=="M3a/M3b"][0]["W_um"],
    "M5":  [r for r in results if r["name"]=="M5"][0]["W_um"],
    "M6":  [r for r in results if r["name"]=="M6"][0]["W_um"],
    "M7":  [r for r in results if r["name"]=="M7"][0]["W_um"],
    "M15": W15_CAP*1e6,
    "M16": [r for r in results if r["name"]=="M16/M26"][0]["W_um"],
}
with open(r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\current-reuse-telescopic-ota-report\vgs_table.json", "w") as f:
    json.dump(dict(vgs=vgs_table, W=Wmap), f, indent=2)
print("\nWrote vgs_table.json")

# ---- Total supply-current bill (bottom-up, multiplicity-aware) ----
VDD = 1.8
bill = [
    ("Stage-1 core (M6+M7 tail source = M5 tail sink, BOTH legs already counted)", ID_branch*2, 1),
    ("Stage-2 output, Vom side (M15+M16 barely-on quiescent)", ID15_q+ID16_q, 1),
    ("Stage-2 output, Vop side (M25+M26 barely-on quiescent, mirror of Vom side)", ID15_q+ID16_q, 1),
    ("Class-AB bias/battery chain, Vom side (M8,M9a/b,M10,M11a/b,M12,M14a/b lumped)", ID_ab_bias+ID_ab_src, 1),
    ("Class-AB bias/battery chain, Vop side (M17,M18a/b,M19,M20a/b,M21,M23a/24b lumped, mirror)", ID_ab_bias+ID_ab_src, 1),
    ("Bias generator (Fig.4, M27-M35 replica branches)", 1.2e-6, 3),
    ("CMFB (Fig.5, M36-M40)", 2.0e-6+2.0e-6+1.0e-6, 1),
]
print("\n-- Total supply-current bill --")
I_total = 0.0
for name, i_each, mult in bill:
    i_tot = i_each*mult
    I_total += i_tot
    print(f"  {name:70s} {i_each*1e6*mult:8.3f}uA  (x{mult})")
print(f"\nI_total = {I_total*1e6:.2f}uA   P_total = {I_total*VDD*1e6:.1f}uW  @ VDD={VDD}V")
print(f"(paper: I_total=70uA, P_total=126uW @ VDD=1.8V -- different process/L grid, order-of-magnitude "
      f"cross-check only, not expected to match exactly)")
with open(r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\current-reuse-telescopic-ota-report\power_bill.json", "w") as f:
    json.dump(dict(bill=[dict(name=n, uA=i*1e6*m) for n,i,m in bill], I_total_uA=I_total*1e6, P_total_uW=I_total*VDD*1e6), f, indent=2)
