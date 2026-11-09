# fc_pex.py -- KLayout Python: per-net wiring geometry (area, perimeter, length along the long axis) of the
# conductive routing layers, for the O-255 (5) parasitic approximation. No RC numbers here; the caller multiplies by
# the PDK extraction coefficients (magic sky130.tech extract style, read separately with line numbers).
# Run: klayout_app.exe -b -r fc_pex.py -rd gds=<gds> -rd rules=<rules.json> -rd outjson=<json>
import json
import pya

R = json.load(open(rules, encoding="utf-8"))
ly = pya.Layout()
ly.read(gds)
top = ly.top_cell()
idx = {k: ly.layer(v[0], v[1]) for k, v in R["layers"].items()}
l2n = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, top, []))
L = {k: l2n.make_layer(idx[k], k) for k in ("diff", "tap", "poly", "licon", "li", "mcon", "met1", "via", "met2")}
lab = l2n.make_text_layer(idx["met1_label"], "lab")
gate = L["poly"] & L["diff"]
poly_f = L["poly"] - L["diff"]
sd = L["diff"] - L["poly"]
l2n.register(gate, "gate")
l2n.register(poly_f, "poly_f")
l2n.register(sd, "sd")
for a in (poly_f, sd, L["tap"], L["licon"], L["li"], L["mcon"], L["met1"], L["via"], L["met2"]):
    l2n.connect(a)
for a, b in ((poly_f, L["licon"]), (sd, L["licon"]), (L["tap"], L["licon"]), (L["licon"], L["li"]), (L["li"], L["mcon"]),
             (L["mcon"], L["met1"]), (L["met1"], L["via"]), (L["via"], L["met2"]), (L["met1"], lab)):
    l2n.connect(a, b)
l2n.connect(gate)
l2n.connect(poly_f, gate)
l2n.extract_netlist()
nl = l2n.netlist()
dbu = ly.dbu
res = {}
for c in nl.each_circuit():
    for net in c.each_net():
        name = net.expanded_name()
        rec = {}
        for k, reg in (("li", L["li"]), ("met1", L["met1"]), ("met2", L["met2"]), ("poly_f", poly_f), ("gate", gate)):
            s = l2n.shapes_of_net(net, reg, True)
            a = s.area() * dbu * dbu
            p = s.perimeter() * dbu
            # longest single shape (bus) length / width for a sheet-resistance estimate
            longest = None
            for poly in s.each():
                bb = poly.bbox()
                w, h = bb.width() * dbu, bb.height() * dbu
                ln, wd = max(w, h), min(w, h)
                if longest is None or ln > longest[0]:
                    longest = (ln, wd)
            rec[k] = {"area_um2": a, "perim_um": p, "longest": longest}
        res[name] = rec
json.dump(res, open(outjson, "w"), indent=1)
print("nets", len(res))
