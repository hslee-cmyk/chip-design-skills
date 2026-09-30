"""E-INST (auditor 독립 작성, 2026-09-30 P6 순서 3).
<root>/workspaces/run_harness.py 사본에서 저장소 절대 경로 리터럴 2종(ASSETS 2곳, WORKSPACES 1곳)을 <root> 경로·작업 디렉터리로
치환해 모듈로 실행(run(<회로>)), 산출 instance.json을 키 정렬 compact JSON(ensure_ascii=False)으로 sha256.
엔진 import가 <root> 밖이면 중단. stdout은 <out>.stdout.txt.
사용: python -P e_inst.py <root> <회로> <작업 디렉터리> <out.json>"""
import contextlib, hashlib, io, json, os, sys, types
root, circuit, ws, out = sys.argv[1:5]
root = os.path.abspath(root); ws = os.path.abspath(ws)
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
src = open(os.path.join(root, "workspaces", "run_harness.py"), encoding="utf-8").read()
LA = r'r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets"'
LW = r'r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces"'
na, nw = src.count(LA), src.count(LW)
if (na, nw) != (2, 1):
    sys.exit("literal count mismatch %r" % ((na, nw),))
src = src.replace(LA, repr(A)).replace(LW, repr(ws))
os.makedirs(ws, exist_ok=True)
mod = types.ModuleType("run_harness_copy")
mod.__file__ = os.path.join(ws, "run_harness_copy.py")
buf = open(out + ".stdout.txt", "w", encoding="utf-8")   # reconfigure()가 있는 텍스트 파일
with contextlib.redirect_stdout(buf):
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    for m in ("sizing_recipe", "stick_diagram", "design_report"):
        f = os.path.normcase(os.path.abspath(sys.modules[m].__file__))
        if not f.startswith(os.path.normcase(A)):
            raise SystemExit("engine imported outside root: %s" % f)
    _cfg = mod.SPECS[circuit]
    os.makedirs(os.path.join(ws, _cfg["report_dir"]), exist_ok=True)   # 저장소에는 report 폴더가 이미 있다
    mod.run(circuit)
buf.close()
stdout_text = open(out + ".stdout.txt", encoding="utf-8").read()
cfg = mod.SPECS[circuit]
inst = os.path.join(ws, cfg["report_dir"], cfg["topology_file"].removesuffix(".topology.json") + ".instance.json")
res = {"circuit": circuit, "instance_path": inst.replace("\\", "/"), "exists": os.path.exists(inst),
       "fail_in_stdout": "[FAIL]" in stdout_text}
if res["exists"]:
    obj = json.load(open(inst, encoding="utf-8"))
    res["sha256"] = hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    res["top_keys"] = sorted(obj)
    res["n_sizing"] = len(obj.get("sizing", {}))
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
if not res["exists"] or res["fail_in_stdout"]:
    sys.exit(1)
