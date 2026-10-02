"""E-INST for Phase 3 (design 30-module-split §10 E5, 2026-10-01 초안 v8 -- 5차 검토 S1).

e_inst_df36.py(.ai/verification/20260930-df36-instance-relpath/scripts/, design 20 §10 E4 정본)와 **한 곳만** 다르다:
엔진 출처 확인(df36 32~37행)이 고정 모듈 이름 셋(sizing_recipe·stick_diagram·design_report)의 sys.modules 항목을 읽는 대신,
하네스 실행 뒤 sys.modules에 있는 모듈 중 __file__이 어느 루트의 `skills/analog-gmid-design/assets` 바로 아래에 있는 것을 전부 모아
(1) 하나 이상이고 (2) 전부 <root>의 assets 아래인지 본다. 이유: F1이 하네스 import를 N3.10 모듈로 바꾸면 sizing_recipe·design_report가
sys.modules에 없어 df36이 KeyError로 끝난다(df36은 D-9 제외 집합이라 고치지 않는다). 모듈 이름을 적지 않으므로 Phase 3 어느 판에서나 같은 사본이 돈다.
나머지(하네스 exec 방식, 모듈 이름 run_harness_df36, 산출 경로, 해시 정의, 출력 키·순서)는 df36과 같다 -- 그래서 F1 전 트리에서는
`engine_origin` 키 값 하나만 다르고(더 많은 모듈을 담는다) 나머지 출력·stdout 사본이 df36과 같아야 한다(E5 '동등 확인').
사용: python -B -P e_inst_p3.py <root> <회로> <out.json>"""
import contextlib, hashlib, json, os, pathlib, sys, types
root, circuit, out = sys.argv[1:4]
root = os.path.abspath(root)
MAIN_ROOT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
H = os.path.abspath(os.path.join(root, "workspaces", "run_harness.py"))
src = open(H, encoding="utf-8").read()
na = src.count(MAIN_ROOT)
if na != 0:
    sys.exit("run_harness still has main-checkout literals: %d" % na)
path_before = list(sys.path)
mod = types.ModuleType("run_harness_df36")
mod.__file__ = H
TAIL = os.path.normcase(os.path.join("skills", "analog-gmid-design", "assets"))
buf = open(out + ".stdout.txt", "w", encoding="utf-8")
with contextlib.redirect_stdout(buf):
    exec(compile(src, H, "exec"), mod.__dict__)
    origin = {}
    for m, mo in sorted(sys.modules.items()):
        f = getattr(mo, "__file__", None)
        if not isinstance(f, str):
            continue
        d = os.path.normcase(os.path.dirname(os.path.abspath(f)))
        if d.endswith(TAIL):
            origin[m] = f
            if d != os.path.normcase(A):
                raise SystemExit("engine imported outside root: %s" % f)
    if not origin:
        raise SystemExit("no engine module loaded from any assets directory")
    cfg = mod.SPECS[circuit]
    inst = os.path.join(mod.WORKSPACES_DIR, cfg["report_dir"],
                        cfg["topology_file"].removesuffix(".topology.json") + ".instance.json")
    if os.path.exists(inst):
        os.remove(inst)
    mod.run(circuit)
buf.close()
stdout_text = open(out + ".stdout.txt", encoding="utf-8").read()
consts = {k: getattr(mod, k) for k in ("ASSETS_DIR", "LIBRARY_DIR", "WORKSPACES_DIR", "LUTFILE")}
res = {"circuit": circuit, "root": root, "harness_file": H, "constants_raw": consts,
       "sys_path_added": [p for p in sys.path if p not in path_before], "engine_origin": origin,
       "instance_path": inst, "exists": os.path.exists(inst), "fail_in_stdout": "[FAIL]" in stdout_text}
def h(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
if res["exists"]:
    raw = open(inst, "rb").read()
    obj = json.loads(raw.decode("utf-8"))
    tr = obj.get("topology_ref")
    res["top_keys_in_file_order"] = list(obj)
    res["raw_sha256"] = h(obj)
    rest = {k: v for k, v in obj.items() if k != "topology_ref"}
    res["without_topology_ref_sha256"] = h(rest)
    res["field_sha256"] = {k: h(v) for k, v in obj.items()}
    res["file_bytes_sha256"] = hashlib.sha256(raw).hexdigest()
    masked = None
    for form in (json.dumps(tr, ensure_ascii=False), json.dumps(tr, ensure_ascii=True)):
        b = form.encode("utf-8")
        if raw.count(b) == 1:
            masked = raw.replace(b, b'"<TOPOLOGY_REF>"')
            res["mask_form"] = "ensure_ascii=False" if form == json.dumps(tr, ensure_ascii=False) else "ensure_ascii=True"
            break
    res["file_bytes_masked_sha256"] = hashlib.sha256(masked).hexdigest() if masked is not None else None
    res["file_len"] = len(raw)
    res["topology_ref_raw"] = tr
    topo_file = pathlib.Path(A) / "library" / cfg["topology_file"]
    res["topology_ref_expected_contract1"] = topo_file.resolve().relative_to(pathlib.Path(root).resolve()).as_posix()
    res["topology_ref_equals_expected_contract1"] = tr == res["topology_ref_expected_contract1"]
    spellings = sorted({root, root.replace("\\", "/"), MAIN_ROOT, MAIN_ROOT.replace("\\", "/")}, key=len, reverse=True)
    hits = []
    def walk(x, p):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(k, p + "/<key>")
                walk(v, p + "/" + str(k))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, p + "[%d]" % i)
        elif isinstance(x, str):
            low = x.lower()
            for s in spellings:
                if s.lower() in low:
                    hits.append({"json_path": p, "value": x})
                    break
    walk(obj, "")
    res["path_string_hits"] = hits
    res["n_sizing"] = len(obj.get("sizing", {}))
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res.get(k) for k in ("circuit", "exists", "fail_in_stdout", "raw_sha256", "without_topology_ref_sha256",
                                           "file_bytes_masked_sha256", "topology_ref_raw")}, ensure_ascii=False))
if not res["exists"] or res["fail_in_stdout"]:
    sys.exit(1)
