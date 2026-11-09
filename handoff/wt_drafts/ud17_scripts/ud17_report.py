"""UD-17 결정 자료 요약: C:/g67/out/eval.jsonl을 읽어 (1) conflicts 경로 (2) clamp vs extrap 소자·metric 차이 (3) 전체 실행 비교를
C:/g67/out/report.txt에 쓴다(사람이 읽는 표 재료). 사용: python -B ud17_report.py
"""
import json

R = {}
for line in open("C:/g67/out/eval.jsonl", encoding="utf-8"):
    r = json.loads(line)
    R[r["label"]] = r
out = open("C:/g67/out/report.txt", "w", encoding="utf-8")


def p(*a):
    print(*a, file=out)


for lab in ("F_theta_clamp", "C_theta_clamp"):
    r = R.get(lab)
    if not r or r["outcome"] != "ok":
        p(lab, "N/A", r and r.get("exc_msg"))
        continue
    p("=" * 20, lab, "trace_matches_engine", r["trace_matches_engine"], "axis_out", r["axis_out_count"])
    for c in r["conflicts"]:
        p(f"conflict {c['device']} @ {c['net']}: existing {c['existing']:.6f} vs via_this {c['via_this']:.6f} diff {c['diff']:.6f}")
        p("   existing path:", " | ".join(c["path_existing"]))
        p("   this path    :", " | ".join(c["path_this"]))
    p("devices (kind src drn gate | vds vsb L gm_id W ID _vsb_source _gm_id_source):")
    for d, t in r["devices"].items():
        e = r["sized"].get(d, {})
        p(f"  {d:6s} {t['kind']} {t['source']}->{t['drain']} g={t['gate']} | vds={e.get('vds')} vsb={e.get('vsb')} L={e.get('L')} "
          f"gm_id={e.get('gm_id')} W={e.get('W')} ID={e.get('ID')} {e.get('_vsb_source')} {e.get('_gm_id_source')}")
    p("metrics", r["metrics"])

for a, b in (("F_theta_clamp", "F_theta_extrap"), ("C_theta_clamp", "C_theta_extrap"),
             ("F_full_clamp", "F_full_extrap"), ("C_full_clamp", "C_full_extrap")):
    ra, rb = R.get(a), R.get(b)
    p("=" * 20, a, "vs", b)
    if not ra or not rb or ra["outcome"] != "ok" or rb["outcome"] != "ok":
        p("  N/A", ra and ra["outcome"], rb and rb["outcome"], rb and rb.get("exc_msg"))
        continue
    if "theta_star" in ra:
        p("  theta_star same:", ra["theta_star"] == rb["theta_star"], ra["theta_star"], rb["theta_star"])
    for k in sorted(set(ra["metrics"]) | set(rb["metrics"])):
        va, vb = ra["metrics"].get(k), rb["metrics"].get(k)
        if va != vb:
            rel = (vb - va) / abs(va) * 100 if (va not in (None, 0) and vb is not None) else None
            p(f"  metric {k}: {va} -> {vb}  ({rel:+.3f}%)" if rel is not None else f"  metric {k}: {va} -> {vb}")
    for d in sorted(set(ra["sized"]) | set(rb["sized"])):
        ea, eb = ra["sized"].get(d, {}), rb["sized"].get(d, {})
        diffs = []
        for k in ("gm_id", "W", "gm", "gds", "vsb", "vds", "L", "ID"):
            va, vb = ea.get(k), eb.get(k)
            if isinstance(va, float) and isinstance(vb, float) and va != vb:
                rel = (vb - va) / abs(va) * 100 if va else float("inf")
                diffs.append(f"{k} {va:.5g}->{vb:.5g} ({rel:+.2f}%)")
        if diffs:
            p(f"  {d}: " + ", ".join(diffs))
out.close()
print(open("C:/g67/out/report.txt", encoding="utf-8").read())
