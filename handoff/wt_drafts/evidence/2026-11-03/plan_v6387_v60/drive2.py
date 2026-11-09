"""v60 driver 2: two_stage_ota_sf, base vs ga with --front, then dump M8 block gain table and front-case records to sf_front.txt."""
import subprocess, sys, os, json
D = os.path.dirname(os.path.abspath(__file__))
for m in ("base", "ga"):
    try:
        r = subprocess.run([sys.executable, os.path.join(D, "q8_run.py"), "two_stage_ota_sf", m, "--front"], capture_output=True, timeout=270, cwd=D)
        rc = r.returncode
    except subprocess.TimeoutExpired:
        rc = "timeout"
    with open(os.path.join(D, "drive_out.txt"), "ab") as f:
        f.write(f"two_stage_ota_sf {m} --front rc={rc}\n".encode("utf-8"))
with open(os.path.join(D, "sf_front.txt"), "w", encoding="utf-8") as o:
    for ln in open(os.path.join(D, "q8_engine_gainL.jsonl"), encoding="utf-8"):
        d = json.loads(ln)
        if d.get("circuit") != "two_stage_ota_sf":
            continue
        if d["case"] == "captured":
            for c in d.get("gain_call") or []:
                o.write(f"[{d['mode']}] anchors {c.get('anchors_m')}\n")
                for b in c.get("blocks", []):
                    o.write(f"[{d['mode']}] {b.get('members')} target={b.get('target_db')} table={b.get('gain_db_by_anchor')}\n")
            for f in d.get("fields") or []:
                o.write(f"[{d['mode']}] rung0_L={f.get('rung0_L')} conflicts={f.get('conflicts_L')}\n")
        elif d["case"] not in ("start", "lut", "stage_a", "stage_b"):
            o.write(f"[{d['mode']}] {json.dumps(d, ensure_ascii=False)[:1800]}\n")
print("done")
