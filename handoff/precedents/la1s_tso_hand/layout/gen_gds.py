# gen_gds.py -- deterministic GDS generator for a row-based analog layout (KLayout Python).
#
# Run:  klayout_app.exe -b -r gen_gds.py -rd design=<design_for_layout.json> -rd rules=<layout_rules.json>
#                       -rd out=<out.gds> -rd top=<cell> -rd pins=<net,net,...> -rd ptap=<net> -rd ntap=<net>
#
# Inputs only: design (devices kind/d/g/s/L/w_s/m + rows of finger slots + stack order) and the PDK rule
# declaration (layer numbers and every geometric value with its source line). No PDK number is written here;
# every dimension is a role name looked up in rules["um"].
#
# Structure (bottom -> top): p-tap strip | per row: gate li levels (below diff), diffusion, S/D met2 buses
# (above diff) | n-tap strip. nwell covers the pmos rows and the n-tap. Every net that must leave its row
# (pin, cross-row, tap) gets a vertical met1 riser on the left; its li/met2 buses extend to the riser and
# connect there (mcon / via). Crossings of different nets are always on different layers.
import json
import pya

R = json.load(open(rules, encoding="utf-8"))
D = json.load(open(design, encoding="utf-8"))
U = {k: v[0] for k, v in R["um"].items()}
G = R["grid_um"]
PINS = [p for p in pins.split(",") if p]


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


# ---- derived role quantities (all from rules) ----
SD = U["licon"] + 2 * U["licon_to_gate"]                 # S/D region between gates (one licon column)
SD_END = max(U["diff_ext_beyond_poly"], U["licon"] + U["licon_to_gate"] + U["diff_encl_licon"])
STRAP_W = U["via"] + 2 * U["m1_encl_via"]                # met1 strap wide enough to land a via
BUS_H = U["via"] + 2 * U["m2_encl_via"]                  # met2 bus height
BUS_PITCH = BUS_H + U["m2_space"]
LV_PITCH = max(U["li_width"] + U["li_space"], U["licon"] + U["licon_space"])
PL_GAP = max(U["polylicon_to_diff"], U["implant_encl_diff"] + U["polylicon_to_psdm"])
RISER_PITCH = STRAP_W + U["m1_space"]
MCON_PITCH = U["mcon"] + U["mcon_space"]
LICON_PITCH = U["licon"] + U["licon_space"]
TAP_H = U["licon"] + 2 * U["tap_encl_licon_adj"]


def chain(slots, dev):
    """Euler walk along a row: returns node nets (len n+1) and per-finger (left, right)."""
    for first in ("d", "s"):
        nodes, ok = [], True
        a = dev[slots[0]]
        left = a[first]
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
    raise RuntimeError("row is not one Euler path; breaks not supported by this generator")


dev = D["devices"]
rows = {r["name"]: r for r in D["rows"]}
order = D["stack"]

# ---- pass 1: geometry of each row (x), nets per level ----
layout_rows = []
for rn in order:
    r = rows[rn]
    slots = r["slots"]
    kind = r["kind"]
    w = dev[slots[0]]["w_s"] * 1e6
    nodes = chain(slots, dev)
    x = 0.0
    sd_x = []      # (x0, x1) of each S/D region
    gates = []     # (x0, x1, net)
    sd_x.append((x, x + SD_END))
    x += SD_END
    for i, name in enumerate(slots):
        Lg = dev[name]["L"] * 1e6
        gates.append((x, x + Lg, dev[name]["g"]))
        x += Lg
        last = i == len(slots) - 1
        wsd = SD_END if last else SD
        sd_x.append((x, x + wsd))
        x += wsd
    gate_nets = []
    for _, _, n in gates:
        if n not in gate_nets:
            gate_nets.append(n)
    sd_nets = []
    for n in nodes:
        if n not in sd_nets:
            sd_nets.append(n)
    layout_rows.append(dict(name=rn, kind=kind, w=w, nodes=nodes, sd_x=sd_x, gates=gates,
                            gate_nets=gate_nets, sd_nets=sd_nets, length=x))

# centre rows horizontally on the widest row (symmetry axis shared)
width = max(r["length"] for r in layout_rows)
for r in layout_rows:
    r["x0"] = g((width - r["length"]) / 2)

# ---- vertical stacking ----
y = 0.0
ptap_y = (y, y + TAP_H)
y += TAP_H
for r in layout_rows:
    nlev = len(r["gate_nets"])
    # lowest gate level poly bottom must clear the tap below (poly_field_to_tap) -- start gap from previous
    gap_below = U["poly_field_to_tap"] + U["li_space"]
    lev_span = nlev * LV_PITCH
    r["y0"] = g(y + gap_below + lev_span + PL_GAP + U["poly_encl_polylicon_adj"])
    r["y1"] = g(r["y0"] + r["w"])
    y = r["y1"] + U["poly_endcap"] + U["m2_space"] + len(r["sd_nets"]) * BUS_PITCH
ntap_y = (y + U["difftap_space"], y + U["difftap_space"] + TAP_H)

# ---- riser columns on the left (one per net that needs to leave its row) ----
need = {}
for r in layout_rows:
    for n in r["gate_nets"] + r["sd_nets"]:
        need.setdefault(n, set()).add(r["name"])
riser_nets = [n for n in sorted(need) if len(need[n]) > 1 or n in PINS or n in (ptap, ntap)]
xmin_rows = min(r["x0"] for r in layout_rows) - U["difftap_space"]
riser_x = {}
for i, n in enumerate(riser_nets):
    x1 = g(xmin_rows - 1.0 * U["m1_space"] - i * RISER_PITCH)
    riser_x[n] = (x1 - STRAP_W, x1)
riser_conn = {n: [] for n in riser_nets}   # y spans of connections


def licon_ys(y0, h, encl):
    n = max(1, int((h - 2 * encl + U["licon_space"]) // LICON_PITCH))
    span = n * U["licon"] + (n - 1) * U["licon_space"]
    s0 = g(y0 + (h - span) / 2)
    return [g(s0 + k * LICON_PITCH) for k in range(n)]


# ---- draw rows ----
for r in layout_rows:
    x0, y0, y1, w = r["x0"], r["y0"], r["y1"], r["w"]
    kind = r["kind"]
    dx_end = x0 + r["length"]
    box("diff", x0, y0, dx_end, y1)
    imp = "nsdm" if kind == "nmos" else "psdm"
    box(imp, x0 - U["implant_encl_diff"], y0 - U["implant_encl_diff"],
        dx_end + U["implant_encl_diff"], y1 + U["implant_encl_diff"])
    # --- gates: poly + poly licon at the level of its net, li bus per gate net ---
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
    # --- S/D: licons, li stripe, mcons, met1 strap up to the net's met2 bus ---
    bus_y = {}
    base = y1 + U["poly_endcap"] + U["m2_space"]
    for k, n in enumerate(r["sd_nets"]):
        b0 = g(base + k * BUS_PITCH)
        bus_y[n] = (b0, b0 + BUS_H)
    lys = licon_ys(y0, w, U["diff_encl_licon_adj"])
    bus_x = {n: [None, None] for n in r["sd_nets"]}
    for (a, b), n in zip(r["sd_x"], r["nodes"]):
        # licon column placed licon_to_gate away from the inner gate side
        if (a, b) == r["sd_x"][0]:
            lx0 = x0 + b - U["licon_to_gate"] - U["licon"]
        elif (a, b) == r["sd_x"][-1]:
            lx0 = x0 + a + U["licon_to_gate"]
        else:
            lx0 = x0 + a + U["licon_to_gate"]
        lx0 = g(lx0)
        for yl in lys:
            box("licon", lx0, yl, lx0 + U["licon"], yl + U["licon"])
        li0 = lys[0] - U["li_encl_licon_adj"]
        li1 = lys[-1] + U["licon"] + U["li_encl_licon_adj"]
        box("li", lx0, li0, lx0 + U["licon"], li1)
        # mcons from the top down, spaced by mcon pitch, inside the li stripe
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
        vx0 = g(sx0 + U["m1_encl_via"])
        box("via", vx0, vy0, vx0 + U["via"], vy0 + U["via"])
        e = bus_x[n]
        e[0] = vx0 if e[0] is None else min(e[0], vx0)
        e[1] = vx0 + U["via"] if e[1] is None else max(e[1], vx0 + U["via"])
    for n, (ea, eb) in bus_x.items():
        b0, b1 = bus_y[n]
        # at the riser the via sits m1_encl_via inside the riser edge; extend met2 so the via has the
        # adjacent-edge enclosure (m2_encl_via_adj) along the bus direction
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
    r["bus_top"] = max(v[1] for v in bus_y.values())

# ---- taps ----
row_x_lo = min(r["x0"] for r in layout_rows)
row_x_hi = max(r["x0"] + r["length"] for r in layout_rows)


def tap_strip(ty, net, implant):
    t0, t1 = ty
    box("tap", row_x_lo, t0, row_x_hi, t1)
    box(implant, row_x_lo - U["implant_encl_tap"], t0 - U["implant_encl_tap"],
        row_x_hi + U["implant_encl_tap"], t1 + U["implant_encl_tap"])
    ly0 = g(t0 + (TAP_H - U["licon"]) / 2)
    x = g(row_x_lo + U["tap_encl_licon_adj"])
    lx = []
    while x + U["licon"] <= row_x_hi - U["tap_encl_licon_adj"] + 1e-9:
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

# ---- nwell over pmos rows + n-tap ----
p_rows = [r for r in layout_rows if r["kind"] == "pmos"]
if p_rows:
    wy0 = min(r["y0"] for r in p_rows) - U["nwell_encl_pdiff"]
    wy1 = ntap_y[1] + U["nwell_encl_ntap"]
    box("nwell", row_x_lo - U["nwell_encl_ntap"], wy0, row_x_hi + U["nwell_encl_ntap"], wy1)

# ---- risers + labels ----
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
