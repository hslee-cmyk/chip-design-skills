"""기준선 변화 원인 대조: head 트리의 iv_domain 에만 옛 tol 항(옛 `_tol_vdsat_max` 와 같은 계산)을 되돌린다. 나머지는 head 그대로."""
import sys
p = sys.argv[1]
s = open(p, "rb").read()
crlf = b"\r\n" in s
t = s.decode("utf-8").replace("\r\n", "\n")
a = "lowest = _snap_up_vds(ctx, d.kind, float(vdsat.values[j]))"
assert t.count(a) == 1
t = t.replace(a, "lowest = _snap_up_vds(ctx, d.kind, float(vdsat.values[j]) + _old_tol(ctx, d.kind, L, vdsat.vds))")
b = "def domain_bounds(ctx, lengths, vds_budget):"
assert t.count(b) == 1
t = t.replace(b, '''def _old_tol(ctx, kind, L, vds):
    from gmid_engine.lut import tol_vdsat_table
    try:
        table = tol_vdsat_table(ctx.memo, kind, ctx.w_keys[kind])
    except _UNDEFINED:
        return 0.0
    sl = slice_of(ctx, kind)
    anchors = np.asarray([float(a) for a in sl.grids[0]])
    vgrid = np.asarray([float(a) for a in sl.grids[2]])
    i_hi = int(np.searchsorted(anchors, L, side="left"))
    rows = sorted({max(i_hi - 1, 0), min(i_hi, anchors.size - 1)})
    j_hi = int(np.searchsorted(vgrid, vds, side="left"))
    cols = sorted({max(j_hi - 1, 0), min(j_hi, vgrid.size - 1)})
    vals = [float(table.cells[i][k].vdsat_v) for i in rows for k in cols if table.cells[i][k].vdsat_v is not None]
    return max(vals) if vals else 0.0


''' + b)
t = t.replace("\n", "\r\n") if crlf else t
open(p, "wb").write(t.encode("utf-8"))
print("patched")
