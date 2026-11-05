"""IT-2a 재측정 변화표(v2 하네스): BASE2 대 HEAD2(새 병합본), HEAD2 대 옛 HEAD(5517c8b4, 공통 칸), two_stage_ota_sf HEAD2 대 HEAD2_rep2,
그리고 평가마다 지문 칸(eval_fps) 대조 -- snapshot_fp·dc_seal_report 값 지문·봉인 4 새 detail 키(foreign_writers·base_call_overlap)를 뺀 값 지문.

usage: python -I compare_it2a_v2.py <run2_dir> <run_dir(옛)> <out_json>
제외 칸(감사 소유): 시간 칸(wall_s·tag·repo·side·eval_time_median_s·m_i2.t), block_counters(따로 분석), eval_fps(따로 분석).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compare_it2a import LIB, TIME_PATHS, counter_changes, load, rows  # noqa: E402


def diff(a, b, path=()):
    if path in TIME_PATHS or path[:1] in (("block_counters",), ("eval_fps",)):
        return []
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            p = path + (k,)
            if p in TIME_PATHS or p[:1] in (("block_counters",), ("eval_fps",)):
                continue
            if k not in a or k not in b:
                out.append(("/".join(map(str, p)), "missing_in_" + ("a" if k not in a else "b")))
                continue
            out += diff(a[k], b[k], p)
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [("/".join(map(str, path)), "len %d != %d" % (len(a), len(b)))]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, path + (i,))
        return out
    return [] if a == b else [("/".join(map(str, path)), "%r != %r" % (str(a)[:120], str(b)[:120]))]


def fps_compare(a, b):
    ra, rb = ((a or {}).get("eval_fps") or {}).get("rows"), ((b or {}).get("eval_fps") or {}).get("rows")
    if ra is None or rb is None:
        return {"present": [ra is not None, rb is not None]}
    out = {"n": [len(ra), len(rb)], "status_theta_equal": [(x["status"], x["theta_hex"]) for x in ra] == [(y["status"], y["theta_hex"]) for y in rb]}
    for kind in ("evaluation", "partial"):
        for f in ("snapshot_fp", "report_value_fp", "report_fp_without_new_keys"):
            pairs = [(x[kind] or {}).get(f) for x in ra], [(y[kind] or {}).get(f) for y in rb]
            n_def = sum(1 for p, q in zip(*pairs) if p is not None or q is not None)
            n_eq = sum(1 for p, q in zip(*pairs) if (p is not None or q is not None) and p == q)
            out[kind + "." + f] = {"compared": n_def, "equal": n_eq}
    return out


def main():
    run2, run1, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    res = {}
    for c in LIB:
        b2, h2, r2 = (load(run2 / "BASE" / (c + ".json")), load(run2 / "HEAD" / (c + ".json")), load(run2 / "HEAD_rep2" / (c + ".json")))
        h1 = load(run1 / "HEAD" / (c + ".json"))
        row = {"present": {"BASE2": b2 is not None, "HEAD2": h2 is not None, "HEAD2_rep2": r2 is not None, "HEAD_old": h1 is not None},
               "eval_fps_column_present": {"BASE2": bool(b2 and "eval_fps" in b2), "HEAD2": bool(h2 and "eval_fps" in h2)},
               "base2_vs_head2_diffs": diff(b2, h2) if b2 and h2 else ["record missing"],
               "head2_vs_head_old_diffs": diff(h1, h2) if h1 and h2 else ["record missing"],
               "head2_vs_head_old_counters_equal": rows(h1) == rows(h2) if h1 and h2 else None,
               "counter_changes_base2_head2": counter_changes(rows(b2), rows(h2)),
               "head2_recomputes_same_input": sum(r["recomputes_same_input"] for r in rows(h2).values()),
               "fps_base2_vs_head2": fps_compare(b2, h2),
               }
        if r2 is not None:
            row["head2_vs_rep2_diffs"] = diff(h2, r2)
            row["head2_vs_rep2_counters_equal"] = rows(h2) == rows(r2)
            row["fps_head2_vs_rep2"] = fps_compare(h2, r2)
        row["n_unexplained"] = len(row["base2_vs_head2_diffs"]) + len(row["head2_vs_head_old_diffs"] if h1 else []) \
            + sum(1 for x in row["counter_changes_base2_head2"] if x["cause"].startswith("UNEXPLAINED")) + len(row.get("head2_vs_rep2_diffs", []))
        res[c] = row
    allr = {"circuits": res, "total_unexplained": sum(r["n_unexplained"] for r in res.values()),
            "g10_head2_total": sum(r["head2_recomputes_same_input"] for r in res.values())}
    out.write_text(json.dumps(allr, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    for c, r in res.items():
        print(c, r["present"], "b2/h2", len(r["base2_vs_head2_diffs"]), "h2/old", len(r["head2_vs_head_old_diffs"]), "ctr_old_eq", r["head2_vs_head_old_counters_equal"],
              "ctr_changes", len(r["counter_changes_base2_head2"]), "G10", r["head2_recomputes_same_input"], "rep2", len(r.get("head2_vs_rep2_diffs", [])) if "head2_vs_rep2_diffs" in r else "-",
              "unexpl", r["n_unexplained"])
        print("   fps", json.dumps(r["fps_base2_vs_head2"]))
        if "fps_head2_vs_rep2" in r:
            print("   fps rep2", json.dumps(r["fps_head2_vs_rep2"]))
    print("TOTAL_UNEXPLAINED", allr["total_unexplained"], "G10", allr["g10_head2_total"])


if __name__ == "__main__":
    main()
