# gen_gds_fc.py -- deterministic GDS generator for row-based analog layout (KLayout Python), folded_cascode pass.
# Copied from la1s_tso_hand/layout/gen_gds.py and extended (original kept):
#   - a row may hold several Euler segments separated by "GAP" slots (diffusion break, difftap_space apart);
#   - dummy fingers are ordinary design devices (gate and outer S/D on the row's rail) placed by the design;
#   - optional guard rings (-rd ring=1): p-tap ring around the nmos rows, n-tap ring inside nwell around the pmos rows.
#
# Run:  klayout_app.exe -b -r gen_gds_fc.py -rd design=<json> -rd rules=<json> -rd out=<gds> -rd top=<cell>
#                       -rd pins=<net,...> -rd ptap=<net> -rd ntap=<net> [-rd ring=1]
# No PDK number is written here; every dimension is a role name looked up in rules["um"].
import json
import pya

R = json.load(open(rules, encoding="utf-8"))
D = json.load(open(design, encoding="utf-8"))
U = {k: v[0] for k, v in R["um"].items()}
G = R["grid_um"]
PINS = [p for p in pins.split(",") if p]
RING = globals().get("ring", "0") == "1"


def g(v):
    return round(round(v / G) * G, 6)


ly = pya.Layout()
ly.dbu = R["dbu_um"]
cell = ly.create_cell(top)
LY = {k: ly.layer(v[0], v[1]) for k, v in R["layers"].items()}


def box(layer, x1, y1, x2, y2):
    cell.shapes(LY[layer]).insert(pya.DBox(g(min(x1, x2)), g(min(y1, y2)), g(max(x1, x2)), g(max(y1, y2))))


def label(text, x, y):
    cell.shapes(LY["met1_label"]).insert(pya.DText(text, pya.DTrans(pya.DVector(g(x), g(y)))))


SD = U["licon"] + 2 * U["licon_to_gate"]
SD_END = max(U["diff_ext_beyond_poly"], U["licon"] + U["licon_to_gate"] + U["diff_encl_licon"])
STRAP_W = U["via"] + 2 * U["m1_encl_via"]
BUS_H = U["via"] + 2 * U["m2_encl_via"]
BUS_PITCH = BUS_H + U["m2_space"]
LV_PITCH = max(U["li_width"] + U["li_space"], U["licon"] + U["licon_space"])
PL_GAP = max(U["polylicon_to_diff"], U["implant_encl_diff"] + U["polylicon_to_psdm"])
RISER_PITCH = STRAP_W + U["m1_space"]
MCON_PITCH = U["mcon"] + U["mcon_space"]
LICON_PITCH = U["licon"] + U["licon_space"]
TAP_H = U["licon"] + 2 * U["tap_encl_licon_adj"]
GAP_W = U["difftap_space"]


def chain(slots, dev):
    """Euler walk along one segment: node nets (len n+1)."""
    for first in ("d", "s"):
        nodes, ok = [], True
        left = dev[slots[0]][first]
        nodes.append(left)
        for name in slots:
            t = dev[name]
            if left == t["d"]:
                right = t["s"]
            elif left == t["s"]:
                right = t["d"]
            else:
                ok = False
                break
            nodes.append(right)
            left = right
        if ok:
            return nodes
    raise RuntimeError("segment is not one Euler path: %s" % slots)


def segments(slots):
    segs, cur = [], []
    for s in slots:
        if s == "GAP":
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append(s)
    if cur:
        segs.append(cur)
    return segs


dev = D["devices"]
rows = {r["name"]: r for r in D["rows"]}
order = D["stack"]

layout_rows = []
for rn in order:
    r = rows[rn]
    kind = r["kind"]
    segs = segments(r["slots"])
    w = dev[segs[0][0]]["w_s"] * 1e6
    x = 0.0
    sd = []        # (x0, x1, net, role) role: 'end_l', 'end_r', 'mid'
    gates = []     # (x0, x1, net)
    diff_x = []    # (x0, x1) per segment
    for si, seg in enumerate(segs):
        if si:
            x += GAP_W
        nodes = chain(seg, dev)
        sx0 = x
        sd.append((x, x + SD_END, nodes[0], "end_l"))
        x += SD_END
        for i, name in enumerate(seg):
            Lg = dev[name]["L"] * 1e6
            gates.append((x, x + Lg, dev[name]["g"]))
            x += Lg
            last = i == len(seg) - 1
            wsd = SD_END if last else SD
            sd.append((x, x + wsd, nodes[i + 1], "end_r" if last else "mid"))
            x += wsd
        diff_x.append((sx0, x))
    gate_nets, sd_nets = [], []
    for _, _, n in gates:
        if n not in gate_nets:
            gate_nets.append(n)
    for _, _, n, _ in sd:
        if n not in sd_nets:
            sd_nets.append(n)
    layout_rows.append(dict(name=rn, kind=kind, w=w, sd=sd, gates=gates, diff_x=diff_x,
                            gate_nets=gate_nets, sd_nets=sd_nets, length=x))

width = max(r["length"] for r in layout_rows)
for r in layout_rows:
    r["x0"] = g((width - r["length"]) / 2)
row_x_lo = min(r["x0"] for r in layout_rows)
row_x_hi = max(r["x0"] + r["length"] for r in layout_rows)

# ---- vertical stacking (bottom -> top) ----
y = 0.0
ptap_y = (y, y + TAP_H)
y += TAP_H
ring_strips = []      # (y0, y1, kind) inner horizontal ring strips (tap, no contacts)
n_rows = [r for r in layout_rows if r["kind"] == "nmos"]
p_rows = [r for r in layout_rows if r["kind"] == "pmos"]
nwell_lo = None
for idx, r in enumerate(layout_rows):
    if RING and r["kind"] == "pmos" and nwell_lo is None and n_rows:
        # close the p-ring above the nmos rows, then open the n-ring inside the nwell
        pt0 = g(y + U["difftap_space"])
        ring_strips.append((pt0, pt0 + TAP_H, "ptap"))
        nwell_lo = g(pt0 + TAP_H + U["ptap_to_nwell"])
        nt0 = g(nwell_lo + U["nwell_encl_ntap"])
        ring_strips.append((nt0, nt0 + TAP_H, "ntap"))
        y = nt0 + TAP_H
    nlev = len(r["gate_nets"])
    gap_below = U["poly_field_to_tap"] + U["li_space"]
    r["y0"] = g(y + gap_below + nlev * LV_PITCH + PL_GAP + U["poly_encl_polylicon_adj"])
    r["y1"] = g(r["y0"] + r["w"])
    y = r["y1"] + U["poly_endcap"] + U["m2_space"] + len(r["sd_nets"]) * BUS_PITCH
ntap_y = (g(y + U["difftap_space"]), g(y + U["difftap_space"] + TAP_H))

# ring x extents (side stripes)
if RING:
    ring_xi_lo = g(row_x_lo - U["difftap_space"] - TAP_H)
    ring_xi_hi = g(row_x_hi + U["difftap_space"] + TAP_H)
    tap_x_lo, tap_x_hi = ring_xi_lo, ring_xi_hi
else:
    tap_x_lo, tap_x_hi = row_x_lo, row_x_hi

# ---- risers ----
need = {}
both = set()   # a net that is a gate net and an S/D net of the same row (diode) must join its li level and met2 bus
for r in layout_rows:
    for n in r["gate_nets"] + r["sd_nets"]:
        need.setdefault(n, set()).add(r["name"])
    both |= set(r["gate_nets"]) & set(r["sd_nets"])
LOCAL = globals().get("local", "0") == "1"
# diode net used by one row only: with -rd local=1 it is joined by a short met1 jumper just left of its own row
# instead of a column at the far left edge (shorter li level and met2 bus -> less wiring capacitance)
local_nets = {n for n in both if len(need[n]) == 1 and n not in PINS and n not in (ptap, ntap)} if LOCAL else set()
riser_nets = [n for n in sorted(need) if (len(need[n]) > 1 or n in PINS or n in (ptap, ntap) or n in both) and n not in local_nets]
for n in PINS:
    if n not in riser_nets and n in need:
        riser_nets.append(n)
xmin_edge = (tap_x_lo - U["nwell_encl_ntap"] - U["m1_space"]) if RING else (row_x_lo - U["difftap_space"])
riser_x = {}
for i, n in enumerate(riser_nets):
    x1 = g(xmin_edge - 1.0 * U["m1_space"] - i * RISER_PITCH)
    riser_x[n] = (x1 - STRAP_W, x1)
for r in layout_rows:
    first_strap = r["x0"] + SD_END - U["licon_to_gate"] - U["licon"] - (STRAP_W - U["licon"]) / 2
    for k, n in enumerate(sorted(local_nets & set(r["gate_nets"]))):
        x1 = g(first_strap - U["m1_space"] - k * RISER_PITCH)
        riser_x[n] = (x1 - STRAP_W, x1)
riser_nets = riser_nets + sorted(local_nets)
riser_conn = {n: [] for n in riser_nets}
LABELLED = set()


def licon_ys(y0, h, encl):
    n = max(1, int((h - 2 * encl + U["licon_space"]) // LICON_PITCH))
    span = n * U["licon"] + (n - 1) * U["licon_space"]
    s0 = g(y0 + (h - span) / 2)
    return [g(s0 + k * LICON_PITCH) for k in range(n)]


for r in layout_rows:
    x0, y0, y1, w = r["x0"], r["y0"], r["y1"], r["w"]
    kind = r["kind"]
    for a, b in r["diff_x"]:
        box("diff", x0 + a, y0, x0 + b, y1)
    imp = "nsdm" if kind == "nmos" else "psdm"
    box(imp, x0 - U["implant_encl_diff"], y0 - U["implant_encl_diff"],
        x0 + r["length"] + U["implant_encl_diff"], y1 + U["implant_encl_diff"])
    lev_y = {}
    for j, n in enumerate(r["gate_nets"]):
        top_l = g(y0 - PL_GAP - j * LV_PITCH)
        lev_y[n] = (top_l - U["licon"], top_l)
    npc_lo = min(v[0] for v in lev_y.values()) - U["npc_encl_polylicon"]
    npc_hi = max(v[1] for v in lev_y.values()) + U["npc_encl_polylicon"]
    gx_lo = min(a for a, _, _ in r["gates"])
    gx_hi = max(b for _, b, _ in r["gates"])
    box("npc", x0 + gx_lo - U["npc_encl_polylicon"], npc_lo, x0 + gx_hi + U["npc_encl_polylicon"], npc_hi)
    bus_ext = {n: [None, None] for n in r["gate_nets"]}
    for a, b, n in r["gates"]:
        ly0, ly1 = lev_y[n]
        box("poly", x0 + a, ly0 - U["poly_encl_polylicon_adj"], x0 + b, y1 + U["poly_endcap"])
        cx0 = g(x0 + a + ((b - a) - U["licon"]) / 2)
        box("licon", cx0, ly0, cx0 + U["licon"], ly1)
        e = bus_ext[n]
        e[0] = cx0 if e[0] is None else min(e[0], cx0)
        e[1] = cx0 + U["licon"] if e[1] is None else max(e[1], cx0 + U["licon"])
    for n, (ea, eb) in bus_ext.items():
        ly0, ly1 = lev_y[n]
        left = riser_x[n][0] if n in riser_x else ea - U["li_encl_licon_adj"]
        box("li", left, ly0, eb + U["li_encl_licon_adj"], ly1)
        if n in riser_x:
            rx0, rx1 = riser_x[n]
            mx0 = g(rx0 + (STRAP_W - U["mcon"]) / 2)
            box("mcon", mx0, ly0, mx0 + U["mcon"], ly1)
            riser_conn[n].append((ly0 - U["m1_encl_mcon_adj"], ly1 + U["m1_encl_mcon_adj"]))
    bus_y = {}
    base = y1 + U["poly_endcap"] + U["m2_space"]
    for k, n in enumerate(r["sd_nets"]):
        b0 = g(base + k * BUS_PITCH)
        bus_y[n] = (b0, b0 + BUS_H)
    lys = licon_ys(y0, w, U["diff_encl_licon_adj"])
    bus_x = {n: [None, None] for n in r["sd_nets"]}
    for a, b, n, role in r["sd"]:
        if role == "end_l":
            lx0 = x0 + b - U["licon_to_gate"] - U["licon"]
        else:
            lx0 = x0 + a + U["licon_to_gate"]
        lx0 = g(lx0)
        for yl in lys:
            box("licon", lx0, yl, lx0 + U["licon"], yl + U["licon"])
        li0 = lys[0] - U["li_encl_licon_adj"]
        li1 = lys[-1] + U["licon"] + U["li_encl_licon_adj"]
        box("li", lx0, li0, lx0 + U["licon"], li1)
        my = []
        t = g(li1 - U["mcon"])
        while t >= li0 - 1e-9:
            my.append(t)
            t = g(t - MCON_PITCH)
        for m in my:
            box("mcon", lx0, m, lx0 + U["mcon"], m + U["mcon"])
        sx0 = g(lx0 - (STRAP_W - U["licon"]) / 2)
        b0, b1 = bus_y[n]
        vy0 = g(b0 + (BUS_H - U["via"]) / 2)
        strap_top = vy0 + U["via"] + U["m1_encl_via_adj"]
        strap_bot = min(my) - U["m1_encl_mcon_adj"]
        box("met1", sx0, strap_bot, sx0 + STRAP_W, strap_top)
        if n not in LABELLED and n not in PINS and n not in (ptap, ntap):
            # internal net name on its first met1 strap (same names as the schematic) -- lets parasitic and LVS
            # reports name every net
            label(n, sx0 + STRAP_W / 2, (strap_bot + strap_top) / 2)
            LABELLED.add(n)
        vx0 = g(sx0 + U["m1_encl_via"])
        box("via", vx0, vy0, vx0 + U["via"], vy0 + U["via"])
        e = bus_x[n]
        e[0] = vx0 if e[0] is None else min(e[0], vx0)
        e[1] = vx0 + U["via"] if e[1] is None else max(e[1], vx0 + U["via"])
    for n, (ea, eb) in bus_x.items():
        b0, b1 = bus_y[n]
        if n in riser_x:
            left = riser_x[n][0] + U["m1_encl_via"] - U["m2_encl_via_adj"]
        else:
            left = ea - U["m2_encl_via_adj"]
        box("met2", left, b0, eb + U["m2_encl_via_adj"], b1)
        if n in riser_x:
            rx0, rx1 = riser_x[n]
            vy0 = g(b0 + (BUS_H - U["via"]) / 2)
            vx0 = g(rx0 + U["m1_encl_via"])
            box("via", vx0, vy0, vx0 + U["via"], vy0 + U["via"])
            riser_conn[n].append((vy0 - U["m1_encl_via_adj"], vy0 + U["via"] + U["m1_encl_via_adj"]))


def tap_strip(ty, net, implant):
    t0, t1 = ty
    box("tap", tap_x_lo, t0, tap_x_hi, t1)
    box(implant, tap_x_lo - U["implant_encl_tap"], t0 - U["implant_encl_tap"],
        tap_x_hi + U["implant_encl_tap"], t1 + U["implant_encl_tap"])
    ly0 = g(t0 + (TAP_H - U["licon"]) / 2)
    x = g(tap_x_lo + U["tap_encl_licon_adj"])
    lx = []
    while x + U["licon"] <= tap_x_hi - U["tap_encl_licon_adj"] + 1e-9:
        box("licon", x, ly0, x + U["licon"], ly0 + U["licon"])
        lx.append(x)
        x = g(x + LICON_PITCH)
    rx0, rx1 = riser_x[net]
    box("li", rx0, ly0, lx[-1] + U["licon"] + U["li_encl_licon_adj"], ly0 + U["licon"])
    mx0 = g(rx0 + (STRAP_W - U["mcon"]) / 2)
    box("mcon", mx0, ly0, mx0 + U["mcon"], ly0 + U["licon"])
    riser_conn[net].append((ly0 - U["m1_encl_mcon_adj"], ly0 + U["licon"] + U["m1_encl_mcon_adj"]))


tap_strip(ptap_y, ptap, "psdm")
tap_strip(ntap_y, ntap, "nsdm")

if RING:
    # inner horizontal strips + side stripes; tap diffusion is continuous with the contacted outer strips
    p_top = [s for s in ring_strips if s[2] == "ptap"]
    n_bot = [s for s in ring_strips if s[2] == "ntap"]
    py1 = p_top[0][1] if p_top else ntap_y[1]
    for (a, b, k) in ring_strips:
        box("tap", tap_x_lo, a, tap_x_hi, b)
        imp = "psdm" if k == "ptap" else "nsdm"
        box(imp, tap_x_lo - U["implant_encl_tap"], a - U["implant_encl_tap"], tap_x_hi + U["implant_encl_tap"], b + U["implant_encl_tap"])
    if n_rows:
        for xa, xb in ((tap_x_lo, tap_x_lo + TAP_H), (tap_x_hi - TAP_H, tap_x_hi)):
            box("tap", xa, ptap_y[0], xb, py1)
            box("psdm", xa - U["implant_encl_tap"], ptap_y[0] - U["implant_encl_tap"], xb + U["implant_encl_tap"], py1 + U["implant_encl_tap"])
    if p_rows:
        ny0 = n_bot[0][0] if n_bot else ntap_y[0]
        for xa, xb in ((tap_x_lo, tap_x_lo + TAP_H), (tap_x_hi - TAP_H, tap_x_hi)):
            box("tap", xa, ny0, xb, ntap_y[1])
            box("nsdm", xa - U["implant_encl_tap"], ny0 - U["implant_encl_tap"], xb + U["implant_encl_tap"], ntap_y[1] + U["implant_encl_tap"])

if p_rows:
    wy0 = nwell_lo if (RING and nwell_lo is not None) else min(r["y0"] for r in p_rows) - U["nwell_encl_pdiff"]
    wy1 = ntap_y[1] + U["nwell_encl_ntap"]
    box("nwell", tap_x_lo - U["nwell_encl_ntap"], wy0, tap_x_hi + U["nwell_encl_ntap"], wy1)

for n in riser_nets:
    rx0, rx1 = riser_x[n]
    spans = riser_conn[n]
    lo = min(a for a, _ in spans)
    hi = max(b for _, b in spans)
    min_h = U["m1_area"] / STRAP_W
    if hi - lo < min_h:
        hi = lo + min_h + G
    box("met1", rx0, lo, rx1, hi)
    if n in PINS or n in (ptap, ntap):
        label(n, (rx0 + rx1) / 2, (lo + hi) / 2)

opt = pya.SaveLayoutOptions()
opt.gds2_write_timestamps = False
ly.write(out, opt)
bb = cell.dbbox()
print("GDS written:", out, "bbox_um", round(bb.width(), 3), "x", round(bb.height(), 3),
      "rows", [(r["name"], round(r["length"], 3), r["y0"]) for r in layout_rows], "risers", riser_nets)
