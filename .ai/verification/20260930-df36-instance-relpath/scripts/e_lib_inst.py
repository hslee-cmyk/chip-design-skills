"""E-LIB-INST (auditor 독립 작성, 2026-09-30, DF-36 순서 3): 바뀌는 함수 save_instance_json을 library 전 회로로 직접 부른다.
e_lib.py는 save_instance_json을 부르지 않으므로(load_topology·run_topology_pipeline만) 이 card의 무동작·계약 5를 library 전수로 보강한다.
회로마다 입력 = test_ic3 3절 구성(소자마다 자기 스택 n_fingers=2·finger_w=1.0·w=2.0, sizing 다섯 필드 1.0) -- 판정 대상이 아닌 구성 입력.
topology 경로는 <root>/skills/analog-gmid-design/assets/library/<파일>의 os.path.abspath(역슬래시) 표기, 출력은 <out_dir>/<이름>.instance.json
(저장소 밖). 기록: without_topology_ref_sha256, field_sha256, file_bytes_masked_sha256(topology_ref 값 표기를 "<TOPOLOGY_REF>"로), topology_ref_raw,
기대 계약 1 값(auditor 구성), 경로 문자열 잎. stick_diagram이 <root> 밖이면 중단.
사용: python -P e_lib_inst.py <root> <out_dir> <out.json>"""
import glob, hashlib, json, os, pathlib, sys
root, out_dir, out = sys.argv[1:4]
root = os.path.abspath(root)
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, A)
import stick_diagram as sd
if not os.path.normcase(os.path.abspath(sd.__file__)).startswith(os.path.normcase(A)):
    sys.exit("stick_diagram imported outside root: %s" % sd.__file__)
os.makedirs(out_dir, exist_ok=True)
def h(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
res = {"stick_diagram_file": sd.__file__, "circuits": {}}
for p in sorted(glob.glob(os.path.join(A, "library", "*.topology.json"))):
    fn = os.path.basename(p)
    if fn.startswith("_"):
        continue
    name = fn[:-len(".topology.json")]
    tp = os.path.abspath(p)
    ts, _meta = sd.load_topology(tp)
    ov = {t.name: {"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": f"stack_{t.name}"} for t in ts}
    pr = sd.run_topology_pipeline(tp, ov)
    sizing = {t.name: {k: 1.0 for k in ("W", "L", "ID", "gm", "gm_id")} for t in ts}
    op = os.path.join(out_dir, name + ".instance.json")
    if os.path.exists(op):
        os.remove(op)
    ent = {}
    try:
        sd.save_instance_json(op, tp, sizing, pr)
        ent["ok"] = True
    except Exception as e:
        ent.update(ok=False, exc=type(e).__name__, msg=str(e).replace(root, "<ROOT>")[:300])
    ent["file_exists"] = os.path.exists(op)
    if ent["file_exists"]:
        raw = open(op, "rb").read()
        obj = json.loads(raw.decode("utf-8"))
        tr = obj.get("topology_ref")
        ent["topology_ref_raw"] = tr
        ent["topology_ref_expected_contract1"] = pathlib.Path(tp).resolve().relative_to(pathlib.Path(root).resolve()).as_posix()
        ent["top_keys_in_file_order"] = list(obj)
        ent["without_topology_ref_sha256"] = h({k: v for k, v in obj.items() if k != "topology_ref"})
        ent["field_sha256"] = {k: h(v) for k, v in obj.items()}
        b = json.dumps(tr, ensure_ascii=False).encode("utf-8")
        ent["file_bytes_masked_sha256"] = hashlib.sha256(raw.replace(b, b'"<TOPOLOGY_REF>"')).hexdigest() if raw.count(b) == 1 else None
        low_roots = {root.lower(), root.replace("\\", "/").lower()}
        hits = []
        def walk(x, q):
            if isinstance(x, dict):
                for k, v in x.items():
                    walk(k, q + "/<key>"); walk(v, q + "/" + str(k))
            elif isinstance(x, list):
                for i, v in enumerate(x):
                    walk(v, q + "[%d]" % i)
            elif isinstance(x, str) and any(r in x.lower() for r in low_roots):
                hits.append(q)
        walk(obj, "")
        ent["root_string_hits"] = hits
    res["circuits"][name] = ent
res["combined_without_topology_ref_sha256"] = h({k: v.get("without_topology_ref_sha256") for k, v in res["circuits"].items()})
res["combined_masked_sha256"] = h({k: v.get("file_bytes_masked_sha256") for k, v in res["circuits"].items()})
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
print("E-LIB-INST", res["combined_without_topology_ref_sha256"], res["combined_masked_sha256"])
for k, v in res["circuits"].items():
    print(k, v.get("ok"), v.get("file_exists"), v.get("topology_ref_raw"), v.get("root_string_hits"))
