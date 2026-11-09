"""v60: summarize q8_engine_gainL.jsonl (this folder): per circuit stage status, found_db, g1, per-block lower bound vs rung0 L, conflicts, undefined reasons."""
import json, collections
D = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/plan_v6387_v60/"
recs = collections.defaultdict(list)
for ln in open(D + "q8_engine_gainL.jsonl", encoding="utf-8"):
    d = json.loads(ln); recs[d["circuit"]].append(d)
o = open(D + "sum_q8.txt", "w", encoding="utf-8")
for c, rs in recs.items():
    o.write(f"=== {c}: cases {[r['case'] for r in rs]}\n")
    for r in rs:
        if r["case"] in ("stage_a", "stage_b"):
            o.write(f"  {r['case']} status={r.get('status')} stop={str(r.get('stop'))[:300]} target={r.get('target_db')}\n")
            for b in r.get("gain_blocks") or []:
                o.write(f"    block {b.get('key')} found_db={b.get('found_db')} reason={b.get('reason')} members={b.get('members')}\n")
        elif r["case"] == "captured":
            for g in r.get("gain_inputs") or []:
                o.write(f"  gain_input {json.dumps({k: g.get(k) for k in ('case','G_db','g1','reason')}, ensure_ascii=False)[:300]}\n")
            for call in r.get("gain_call") or []:
                for b in call.get("blocks", []):
                    o.write(f"  call block members={b.get('members')} target={b.get('target_db')} model_reason={b.get('model_reason')} evaluated={sum(x is not None for x in (b.get('gain_db_by_anchor') or []))}/{len(b.get('gain_db_by_anchor') or [])}\n")
            for f in r.get("fields") or []:
                o.write(f"  n_rungs={f.get('n_rungs')} rung0_L={f.get('rung0_L')}\n  inactive={[x for x in (f.get('inactive') or []) if 'gain' in x.lower()]}\n  conflicts_L={str(f.get('conflicts_L'))[:500]}\n")
        elif r["case"] not in ("start", "lut"):
            o.write(f"  {r['case']}: {json.dumps(r, ensure_ascii=False)[:500]}\n")
o.close(); print("ok")
