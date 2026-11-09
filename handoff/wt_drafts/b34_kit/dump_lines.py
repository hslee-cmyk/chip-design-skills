import sys
R = "C:/g123/repo/"
SD = R + "skills/analog-gmid-design/assets/stick_diagram.py"
SR = R + "skills/analog-gmid-design/assets/sizing_recipe.py"
def L(p): return open(p, encoding="utf-8").read().split("\n")
sd, sr = L(SD), L(SR)
groups = {
 "site": [(1057,1058),(1046,1048),(1073,1074),(1089,1090),(3370,3371),(3376,3377),(3373,3373),(3381,3381)],
 "handoff": [(1313,1314),(1445,1446),(1714,1715),(1894,1895),(2259,2260),(2400,2401),(2410,2411),(2494,2496),(2523,2524),(2440,2441),(3518,3520),(3522,3524),(3527,3529),(4060,4062),(4076,4077),(4098,4102),(3955,3959)],
 "remain": [(1076,1077),(1092,1093),(1316,1317),(1448,1449),(1717,1718),(2262,2263),(3373,3374),(1543,1543),(2092,2092),(2165,2165),(2169,2169),(2420,2420),(3285,3285),(3104,3104)],
 "doc": [(1025,1031),(1304,1304),(1384,1384),(1533,1533),(1676,1676),(1891,1892),(2070,2070),(2152,2152),(2241,2241),(2349,2349),(3074,3074),(3271,3271),(3356,3356),(3363,3364),(3515,3516),(3921,3922)],
 "callers": [(x,x) for x in (1072,1088,1312,1444,1713,1893,2258,2399,2494,3369,3517,4059)],
 "misc": [(3391,3391),(3330,3330),(3834,3834),(8539,8539)],
}
out = open("C:/g123/out/sd_lines.txt", "w", encoding="utf-8")
for g, rs in groups.items():
    out.write("### %s\n" % g)
    for a, b in rs:
        for i in range(a, b + 1):
            out.write("SD %5d| %s\n" % (i, sd[i-1][:160]))
        out.write("\n")
out.write("### SR\n")
for a, b in ((7952,7952),(6509,6512)):
    for i in range(a, b+1):
        out.write("SR %5d| %s\n" % (i, sr[i-1][:200]))
for f, rs in (("install.py", [(27,29)]), ("skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py", [(2714,2717)]),
              ("skills/analog-gmid-design/references/analog-grammar-integration.md", [(95,97),(107,107),(111,111),(118,121),(187,188),(198,198),(202,202),(440,443)]),
              ("docs/03-analysis/gain-budget-gmid-sizing.function-registry.md", [(360,360)]),
              ("docs/02-design/specs/20260930-p9-kcl-edges.spec.md", [(58,58)]),
              ("docs/02-design/specs/20260930-p9-kcl-edges.interface.md", [(60,60)]),
              (".ai/verification/20260930-p9-kcl-edges/scripts/diff_dup.py", [(17,20)])):
    t = L(R + f)
    out.write("### %s\n" % f)
    for a, b in rs:
        for i in range(a, b+1):
            out.write("%5d| %s\n" % (i, t[i-1][:220]))
out.close()
