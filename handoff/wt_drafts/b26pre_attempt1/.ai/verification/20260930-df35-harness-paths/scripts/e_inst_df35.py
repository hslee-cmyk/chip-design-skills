"""E-INST for DF-35 (auditor 독립 작성, 2026-09-30, P6/P8 e_inst.py에서 파생).

목적: 계약 5(메인 체크아웃 경로에서 E-INST가 base와 같다)를 격리 복제본에서 판정할 수 있게 base 기준값을 잰다.
  * mode=base  : <root>/workspaces/run_harness.py 사본에서 메인 체크아웃 절대 경로 리터럴(ASSETS 2곳, WORKSPACES 1곳)을
                 **같은 표기 방식**(r"...", 역슬래시, os.path.abspath 형태)의 <root> 경로로 치환한다. WORKSPACES도 <root>/workspaces로
                 치환한다(병합본이 __file__에서 유도하면 산출이 같은 곳에 쓰이게 -- 옛 e_inst.py는 별도 작업 디렉터리를 썼다).
                 = "base를 이 복제본이 메인 체크아웃 위치에 있을 때 돌린 것"과 같은 문자열 입력.
  * mode=merged: 치환 없이 실행(리터럴 0개 요구). 병합본이 __file__에서 유도한 경로를 그대로 쓴다.
  두 mode 모두 모듈 __file__ = os.path.abspath(<root>/workspaces/run_harness.py)로 exec한다(파일 import와 같은 이름공간).
산출: instance.json(<WORKSPACES_DIR>/<report_dir>/<name>.instance.json)을
  (1) raw_sha256 = 키 정렬 compact JSON(ensure_ascii=False) sha256 (P6/P8과 같은 규칙)
  (2) norm_sha256 = topology_ref를 ASSETS 기준 상대 표기 '<ASSETS>/library/<file>'로 바꾼 뒤 같은 규칙 sha256
  (3) 경로 문자열 전수 스캔: 복제본 루트·메인 체크아웃 루트(어느 표기든)를 담은 문자열 잎의 JSON 경로 목록
  그리고 모듈이 본 경로 상수 원문(ASSETS_DIR·LIBRARY_DIR·WORKSPACES_DIR·LUTFILE), sys.path에 새로 들어간 항목, 엔진 모듈 출처.
엔진 import가 <root> 밖이면 중단. stdout은 <out>.stdout.txt.
사용: python -P e_inst_df35.py <root> <회로> <base|merged> <out.json>"""
import contextlib, hashlib, json, os, sys, types
root, circuit, mode, out = sys.argv[1:5]
root = os.path.abspath(root)
MAIN_ROOT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"   # 비교용 문자열(읽지도 쓰지도 않는다)
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
WS = os.path.join(root, "workspaces")
H = os.path.abspath(os.path.join(WS, "run_harness.py"))
src = open(H, encoding="utf-8").read()
LA = 'r"' + MAIN_ROOT + r'\skills\analog-gmid-design\assets"'
LW = 'r"' + MAIN_ROOT + r'\workspaces"'
na, nw = src.count(LA), src.count(LW)
if mode == "base":
    if (na, nw) != (2, 1):
        sys.exit("literal count mismatch %r" % ((na, nw),))
    src = src.replace(LA, 'r"' + A + '"').replace(LW, 'r"' + WS + '"')
elif mode == "merged":
    if (na, nw) != (0, 0):
        sys.exit("merged still has literals %r" % ((na, nw),))
else:
    sys.exit("mode must be base|merged")
path_before = list(sys.path)
mod = types.ModuleType("run_harness_df35")
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
        os.remove(inst)          # 이 실행이 새로 썼는지 확인하려고 지운다(복제본 안, 추적 파일은 드라이버가 되돌린다)
    mod.run(circuit)
buf.close()
stdout_text = open(out + ".stdout.txt", encoding="utf-8").read()
added = [p for p in sys.path if p not in path_before]
consts = {k: getattr(mod, k) for k in ("ASSETS_DIR", "LIBRARY_DIR", "WORKSPACES_DIR", "LUTFILE")}
res = {"circuit": circuit, "mode": mode, "root": root, "harness_file": H, "literal_counts_before": [na, nw],
       "constants_raw": consts, "sys_path_added": added, "engine_origin": origin,
       "instance_path": inst, "exists": os.path.exists(inst), "fail_in_stdout": "[FAIL]" in stdout_text}
spellings = sorted({root, root.replace("\\", "/"), MAIN_ROOT, MAIN_ROOT.replace("\\", "/")}, key=len, reverse=True)
def h(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
if res["exists"]:
    obj = json.load(open(inst, encoding="utf-8"))
    hits = []
    def walk(x, p):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, p + "/" + str(k))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, p + "[%d]" % i)
        elif isinstance(x, str):
            low = x.lower()
            for s in spellings:
                if s.lower() in low:
                    hits.append({"json_path": p, "value": x, "matched_root": s})
                    break
    walk(obj, "")
    res["path_string_hits"] = hits
    res["raw_sha256"] = h(obj)
    tr = obj.get("topology_ref")
    res["topology_ref_raw"] = tr
    res["topology_ref_is_join_of_ASSETS_DIR"] = tr == os.path.join(consts["ASSETS_DIR"], "library", cfg["topology_file"])
    rel = os.path.relpath(os.path.normcase(os.path.normpath(tr)), os.path.normcase(os.path.normpath(A))).replace("\\", "/")
    res["topology_ref_rel_to_clone_assets"] = rel
    norm = dict(obj)
    norm["topology_ref"] = "<ASSETS>/" + rel
    res["norm_sha256"] = h(norm)
    rest = dict(obj); rest.pop("topology_ref", None)
    res["without_topology_ref_sha256"] = h(rest)
    res["top_keys"] = sorted(obj)
    res["n_sizing"] = len(obj.get("sizing", {}))
    # 메인 체크아웃 투영: base가 메인 체크아웃에서 쓸 raw 해시(topology_ref = 메인 리터럴 + library + 파일). 계약 5 비교용.
    proj = dict(obj)
    proj["topology_ref"] = os.path.join(MAIN_ROOT + r"\skills\analog-gmid-design\assets", "library", cfg["topology_file"])
    res["main_projection_raw_sha256"] = h(proj)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res.get(k) for k in ("circuit", "mode", "exists", "fail_in_stdout", "raw_sha256", "norm_sha256",
                                           "main_projection_raw_sha256", "topology_ref_raw")}, ensure_ascii=False))
if not res["exists"] or res["fail_in_stdout"]:
    sys.exit(1)
