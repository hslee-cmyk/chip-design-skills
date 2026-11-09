"""measure only: M1-2 amendment variants on the scratch clone.
  qtok   -- N3.10 MOD1 '대표 대상' gets token `_QUERY_CACHE_MAX` (after `_multilinear_interp_point_multi`)
  regfix -- registry row whose function cell is `_QUERY_CACHE_MAX` (4D 배열 적재 ...) gets function cell
            `SemiEmpiricalGmIdLUT.__init__` (audit source agent1_sizing_1_3021.md:22 '`_QUERY_CACHE_MAX`(301) + `SemiEmpiricalGmIdLUT.__init__`(318-416)')
Exact-match anchors, exactly one occurrence each, else exit 1 without writing."""
import sys

ROOT, VAR = sys.argv[1:3]
if VAR == "qtok":
    p = ROOT + "/docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
    old = "| MOD1 | `gmid_lut.py` | LUT 인터페이스·보간·역산·곡선 검사·보간 오차 | `GmIdLUT`, `SemiEmpiricalGmIdLUT`, `_multilinear_interp`, `_multilinear_interp_point_multi`, "
    new = "| MOD1 | `gmid_lut.py` | LUT 인터페이스·보간·역산·곡선 검사·보간 오차 | `GmIdLUT`, `SemiEmpiricalGmIdLUT`, `_multilinear_interp`, `_multilinear_interp_point_multi`, `_QUERY_CACHE_MAX`, "
elif VAR == "regfix":
    p = ROOT + "/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md"
    old = "| `_QUERY_CACHE_MAX` | 4D 배열 적재, shape 검증,"
    new = "| `SemiEmpiricalGmIdLUT.__init__` | 4D 배열 적재, shape 검증,"
else:
    sys.exit("unknown variant")
raw = open(p, encoding="utf-8", newline="").read()
if raw.count(old) != 1:
    sys.exit("anchor count %d" % raw.count(old))
open(p, "w", encoding="utf-8", newline="").write(raw.replace(old, new))
print("variant", VAR, "applied")
