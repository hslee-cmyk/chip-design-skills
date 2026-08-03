# -*- coding: utf-8 -*-
"""corrected Fig.5 CMFB amp: exact symbolic solve vs. my hand closed form."""
import sympy as sp

gm36a, gd36a, gm36b, gd36b = sp.symbols('gm36a gd36a gm36b gd36b', positive=True)
gm37a, gd37a, gm37b, gd37b = sp.symbols('gm37a gd37a gm37b gd37b', positive=True)
gm39, gd39, gm40, gd40, gd38 = sp.symbols('gm39 gd39 gm40 gd40 gd38', positive=True)
voc = sp.symbols('voc')
vc, vb, vt, vd = sp.symbols('vc vb vt vd')          # Vcmfb, N36b, Ncmfb_tail, Voc_des


def ids(gm, gds, vg, vd_, vs):
    """current flowing drain-node -> source-node through the device."""
    return gm * (vg - vs) + gds * (vd_ - vs)


# --- KCL: sum of currents LEAVING each node == 0 -------------------------------
# Vcmfb: M36a (drain node = vc, source = vdd = 0, gate = vc) + M37a (drain = vc)
eq_c = ids(gm36a, gd36a, vc, vc, 0) + ids(gm37a, gd37a, voc, vc, vt)
# N36b: M36b diode + M37b drain
eq_b = ids(gm36b, gd36b, vb, vb, 0) + ids(gm37b, gd37b, vd, vb, vt)
# Ncmfb_tail: M38 (drain = vt, source = 0) leaves; M37a/M37b sources feed in
eq_t = ids(0, gd38, 0, vt, 0) - ids(gm37a, gd37a, voc, vc, vt) - ids(gm37b, gd37b, vd, vb, vt)
# Voc_des: M39 (pmos diode, drain=vd, source=vdd=0, gate=vd)
#          M40 (pmos, SOURCE = vd, drain = gnd = 0, gate = gnd = 0)  -> current leaving node vd
eq_d = ids(gm39, gd39, vd, vd, 0) - ids(gm40, gd40, 0, 0, vd)

sol = sp.solve([eq_c, eq_b, eq_t, eq_d], [vc, vb, vt, vd], dict=True)[0]
print("v(Voc_des) exact =", sp.simplify(sol[vd]))
Ac_exact = sp.simplify(sol[vc] / voc)
print()

# --- my hand closed form -------------------------------------------------------
a = gm36a + gd36a
b = gm36b + gd36b
A1 = a * (gm37a + gd37a) / (a + gd37a)
A0 = a * gm37a / (a + gd37a)
B1 = b * (gm37b + gd37b) / (b + gd37b)
vt_h = A0 / (A1 + B1 + gd38)
Ac_hand = ((gm37a + gd37a) * vt_h - gm37a) / (a + gd37a)

print("hand == sympy ?", sp.simplify(Ac_exact - Ac_hand) == 0)

# --- leading order -------------------------------------------------------------
lead = sp.limit(sp.limit(sp.limit(sp.limit(sp.limit(
    Ac_hand, gd36a, 0), gd36b, 0), gd37a, 0), gd37b, 0), gd38, 0)
print("leading order (all gds->0):", sp.simplify(lead))

# --- numeric spot check --------------------------------------------------------
sub = {gm36a: 80e-6, gd36a: 0.8e-6, gm36b: 84e-6, gd36b: 0.9e-6,
       gm37a: 100e-6, gd37a: 1.0e-6, gm37b: 105e-6, gd37b: 1.1e-6,
       gm39: 85e-6, gd39: 0.7e-6, gm40: 88e-6, gd40: 0.6e-6, gd38: 1.2e-6}
print("A_c numeric  =", float(Ac_hand.subs(sub)))
print("A_c leading  =", float(lead.subs(sub)))
