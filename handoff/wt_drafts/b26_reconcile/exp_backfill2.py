"""backfill 삭제 변이 표적 입력: 완화 쌍(gm/ID 위반)의 행에 euler 막힘 소자(별 모양)를 함께 둔다 -- 수리 결과의 3b가
'sequence 없음'(False)이고 _finalize의 euler 정리 뒤 3b가 True가 되면 두 변이가 갈린다.
출력: C:/g103/out/exp_backfill2.txt"""
import sys
sys.argv = ["x"]
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile")
import exp_backfill as E  # noqa: E402

sr0, LUT, T = E.sr0, E.LUT, E.T
out = open("C:/g103/out/exp_backfill2.txt", "w", encoding="utf-8")
r = sr0.size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=LUT, vds=0.6)
W0 = r.W
S = {"ID": r.ID, "W": W0, "L": 0.5e-6, "gm": r.gm, "gm_id": 12.0,
     "gds": r.gm / LUT.gm_gds_ratio(12.0, 0.5e-6, 0.6, 0.0), "kind": "nmos", "vds": 0.6, "vsb": 0.0}


def build(variant):
    tail = "nx" if variant in ("share", "share2") else "vtail"
    P = [T("Ma", "nmos", source=tail, drain="nda", gate="ga", n_fingers=1, finger_w=W0, stack_id="row"),
         T("Mb", "nmos", source=tail, drain="ndb", gate="gb", n_fingers=1, finger_w=W0, stack_id="row")]
    X = [T("M1", "nmos", source="na", drain="nx", gate="g1", n_fingers=1, finger_w=W0, stack_id="row"),
         T("M2", "nmos", source="nx", drain="nb", gate="g2", n_fingers=1, finger_w=W0, stack_id="row"),
         T("M3", "nmos", source="nx", drain="nc", gate="g3", n_fingers=1, finger_w=W0, stack_id="row")]
    if variant == "share2":
        X.append(T("M4", "nmos", source="nda", drain="ne", gate="g4", n_fingers=1, finger_w=W0, stack_id="row"))
    rows = {"row": P + X}
    names = [t.name for t in P + X]
    ctx = sr0.SizingContext(sized={n: dict(S) for n in names}, topology_path=None)
    metrics = {"area": {"type": "sum_area", "devices": names}}
    cons = [{"metric": "area", "op": "<=", "value": 10 * len(names) * W0 * 0.5e-6}]
    return rows, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, ctx, metrics, cons


for variant in ("sep", "share", "share2"):
    for mx in (1, 2, 3):
        rows, pairs, sens, ctx, metrics, cons = build(variant)
        args = (rows, pairs, sens, ctx, metrics, cons, 13.0, mx)
        res = {k: E.summary(E.run(m, args)) for k, m in E.MODS.items()}
        out.write("%s max_rounds=%d same(loop_del)=%s same(after_del)=%s\n  orig=%s\n" % (
            variant, mx, res["loop_del"] == res["orig"], res["after_del"] == res["orig"], res["orig"][:900]))
        if res["loop_del"] != res["orig"]:
            out.write("  loop_del=%s\n" % res["loop_del"][:900])
        if res["after_del"] != res["orig"]:
            out.write("  after_del=%s\n" % res["after_del"][:900])
out.close()
print(open("C:/g103/out/exp_backfill2.txt", encoding="utf-8").read())
