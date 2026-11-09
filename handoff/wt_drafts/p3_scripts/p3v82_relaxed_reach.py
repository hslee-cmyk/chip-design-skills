"""v8.2 실측(판정 아님): backfill card가 바꾸는 `relaxed_pairs[i]["interdig_ok"]`가 E-INST·보고 산출물에 닿는가.
사용: python -B -P p3v82_relaxed_reach.py <root> <circuit> <out.json>
하네스를 e_inst_p3.py와 같은 방식(모듈 run_harness_df36으로 exec)으로 돌리되, exec 전에
  (1) sizing_recipe.run_matching_safety_with_finger_growth를 감싸 반환 relaxed_pairs(쌍, interdig_ok)를 기록하고
  (2) stick_diagram.save_instance_json을 감싸 넘겨받은 pipeline_result에 relaxed_pairs 키가 있는지·값을 기록한다
      (하네스가 `from stick_diagram import save_instance_json`로 가져가므로 exec 전에 바꾼다).
실행 뒤 instance.json·report.html·stdout 사본에서 문자열 'relaxed'·'interdig'를 센다. 결과는 회로마다 파일로 쓴다."""
import contextlib, json, os, sys, traceback, types
root, circuit, out = sys.argv[1:4]
root = os.path.abspath(root)
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
H = os.path.join(root, "workspaces", "run_harness.py")
sys.path.insert(0, A)
import sizing_recipe as sr, stick_diagram as sd
rec = {"circuit": circuit, "calls": [], "save_calls": []}
_orig = sr.run_matching_safety_with_finger_growth
def _wrap(*a, **k):
    r = _orig(*a, **k)
    rec["calls"].append([{"pair": list(e.get("pair", ())), "interdig_ok": e.get("interdig_ok")} for e in r.get("relaxed_pairs", [])])
    return r
sr.run_matching_safety_with_finger_growth = _wrap
_osave = sd.save_instance_json
def _swrap(path, topo, sizing, pr):
    rec["save_calls"].append({"pipeline_result_has_relaxed_pairs": "relaxed_pairs" in pr,
                              "relaxed_pairs": [{"pair": list(e.get("pair", ())), "interdig_ok": e.get("interdig_ok")} for e in pr.get("relaxed_pairs", [])],
                              "pipeline_result_keys": sorted(pr)})
    return _osave(path, topo, sizing, pr)
sd.save_instance_json = _swrap
src = open(H, encoding="utf-8").read()
mod = types.ModuleType("run_harness_df36"); mod.__file__ = H
buf = open(out + ".stdout.txt", "w", encoding="utf-8")
try:
    with contextlib.redirect_stdout(buf):
        exec(compile(src, H, "exec"), mod.__dict__)
        cfg = mod.SPECS[circuit]
        stem = cfg["topology_file"].removesuffix(".topology.json")
        rd = os.path.join(mod.WORKSPACES_DIR, cfg["report_dir"])
        inst, rep = os.path.join(rd, stem + ".instance.json"), os.path.join(rd, stem + ".report.html")
        for f in (inst, rep):
            if os.path.exists(f):
                os.remove(f)
        mod.run(circuit)
    rec["exc"] = None
except BaseException as e:
    rec["exc"] = "%s: %s" % (type(e).__name__, str(e)[:300])
    rec["tb_tail"] = traceback.format_exc()[-600:]
buf.close()
def count(path):
    if not os.path.exists(path):
        return None
    t = open(path, encoding="utf-8", errors="replace").read()
    return {"relaxed": t.count("relaxed"), "interdig": t.count("interdig"), "bytes": len(t)}
rec["instance_json"] = count(inst) if "inst" in dir() else None
rec["report_html"] = count(rep) if "rep" in dir() else None
rec["stdout"] = count(out + ".stdout.txt")
if rec["instance_json"] is not None:
    rec["instance_top_keys"] = list(json.load(open(inst, encoding="utf-8")))
json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: rec.get(k) for k in ("circuit", "exc", "instance_json", "report_html", "stdout")}, ensure_ascii=False))
print("calls", rec["calls"]); print("save", [{k: v for k, v in s.items() if k != "pipeline_result_keys"} for s in rec["save_calls"]])
