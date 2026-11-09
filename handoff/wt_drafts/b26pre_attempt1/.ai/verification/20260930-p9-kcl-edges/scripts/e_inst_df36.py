"""E-INST for DF-36 (auditor 독립 작성, 2026-09-30, DF-35 e_inst_df35.py merged 모드에서 파생).

base(070cf69, DF-35 병합 뒤)의 run_harness는 경로를 __file__에서 유도하므로 치환 없이 실행한다(메인 리터럴 0개 요구).
모듈 __file__ = os.path.abspath(<root>/workspaces/run_harness.py)로 exec, 산출은 <root>/workspaces/<report_dir>/<name>.instance.json.
계약 5(topology_ref를 뺀 나머지 필드가 base와 바이트 동일, topology_ref는 계약 1 값) 판정용 기록:
  raw_sha256              키 정렬 compact JSON(ensure_ascii=False) sha256 (P6/P8/DF-35와 같은 규칙)
  without_topology_ref_sha256  topology_ref 키를 뺀 객체의 같은 규칙 sha256
  field_sha256            최상위 키마다 값의 같은 규칙 sha256
  file_bytes_sha256       파일 바이트 sha256
  file_bytes_masked_sha256 파일 바이트에서 topology_ref 값의 JSON 문자열 표기(json.dumps(값, ensure_ascii=False)와
                          ensure_ascii=True 두 형태 중 실제로 1회 나오는 것)를 "<TOPOLOGY_REF>"로 바꾼 바이트 sha256 -- 키 순서·서식까지 비교
  topology_ref_raw, topology_ref_expected_contract1 (= 저장소 루트 기준 '/' 상대 경로, test와 같은 방식으로 auditor가 구성)
  path_string_hits        복제본 루트(두 표기, 대소문자 무시)를 담은 문자열 잎
엔진 import가 <root> 밖이면 중단. stdout은 <out>.stdout.txt.
사용: python -P e_inst_df36.py <root> <회로> <out.json>"""
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
buf = open(out + ".stdout.txt", "w", encoding="utf-8")
with contextlib.redirect_stdout(buf):
    exec(compile(src, H, "exec"), mod.__dict__)
    origin = {}
    for m in ("sizing_recipe", "stick_diagram", "design_report"):
        f = os.path.normcase(os.path.abspath(sys.modules[m].__file__))
        origin[m] = sys.modules[m].__file__
        if not f.startswith(os.path.normcase(A)):
            raise SystemExit("engine imported outside root: %s" % f)
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
