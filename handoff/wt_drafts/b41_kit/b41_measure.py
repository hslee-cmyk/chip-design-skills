"""B41 측정: save_instance_json의 묶기 해시·변이 목록·4개 변이의 실제 문장·indent 등가 여부.

사용: python -B -P b41_measure.py <격리 복제본 루트> <rev> [<rev> ...] --out <결과 json>
  * 각 rev의 stick_diagram.py에서 save_instance_json 노드를 찾아 merged 도구(<root>/tools/gates/mutate_changed.py, 복제본 체크아웃판)의
    bind_hash·def_hash·mutants로 계산한다(도구를 다시 쓰지 않는다).
  * 마지막 rev 체크아웃(복제본 작업 트리)에서 indent 변이 2개와 원본으로 같은 입력을 실제로 저장해 파싱 결과·바이트를 비교한다.
결과는 --out에 rev마다 append(중간 실패에도 남도록)하고 마지막에 요약 한 줄을 출력한다.
"""
import argparse, ast, copy, hashlib, importlib.util, json, os, subprocess, sys, tempfile

ap = argparse.ArgumentParser()
ap.add_argument("root")
ap.add_argument("revs", nargs="+")
ap.add_argument("--out", required=True)
ns = ap.parse_args()
root = os.path.abspath(ns.root)
SD = "skills/analog-gmid-design/assets/stick_diagram.py"
B41_IDS = [
    "stick_diagram:save_instance_json:stmt_delete:body[2]",
    "stick_diagram:save_instance_json:stmt_delete:body[2].body[0]",
    "stick_diagram:save_instance_json:const+:body[6].body[0].value.keywords[0].value",
    "stick_diagram:save_instance_json:const-:body[6].body[0].value.keywords[0].value",
]
sys.path.insert(0, os.path.join(root, "tools", "gates"))
spec = importlib.util.spec_from_file_location("mc", os.path.join(root, "tools", "gates", "mutate_changed.py"))
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)
tool_sha = hashlib.sha256(open(os.path.join(root, "tools", "gates", "mutate_changed.py"), "rb").read()).hexdigest()


def append(rec):
    with open(ns.out, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def find_def(src):
    for q, n in mc.rch.iter_defs(ast.parse(src)):
        if q == "save_instance_json":
            return n
    raise SystemExit("save_instance_json 없음")


last = None
for rev in ns.revs:
    src = subprocess.run(["git", "-C", root, "show", "%s:%s" % (rev, SD)], capture_output=True, check=True).stdout.decode("utf-8")
    fn = find_def(src)
    muts = mc.mutants(fn, src)
    ids = ["stick_diagram:save_instance_json:%s:%s" % (op, p) for op, p, _ in muts]
    detail = {}
    for op, p, mfn in muts:
        mid = "stick_diagram:save_instance_json:%s:%s" % (op, p)
        if mid in B41_IDS:
            orig = ast.unparse(mc._get(fn, p))
            new = ast.unparse(mc._get(mfn, p))
            detail[mid] = {"orig": orig, "mutated": new}
    rec = {"rev": rev, "tool_sha256": tool_sha, "lineno": fn.lineno, "end_lineno": fn.end_lineno,
           "bind_hash": mc.bind_hash(fn), "def_hash": mc.def_hash(fn), "n_mutants": len(muts),
           "b41_present": {m: (m in ids) for m in B41_IDS}, "b41_detail": detail,
           "bound_elements": ["%s@%s" % (m, mc.bind_hash(fn)) for m in B41_IDS]}
    append(rec)
    last = (rev, src, fn, muts)

# ---- indent 등가: 마지막 rev = 작업 트리 체크아웃이어야 한다(호출 스크립트가 보장)
rev, src, fn, muts = last
work_src = open(os.path.join(root, *SD.split("/")), encoding="utf-8").read()
assert work_src.replace("\r\n", "\n") == src.replace("\r\n", "\n"), "작업 트리가 마지막 rev와 다르다"
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, A)
import stick_diagram as sd  # noqa: E402

lib = sorted(p for p in os.listdir(os.path.join(A, "library")) if p.endswith(".topology.json") and not p.startswith("_"))
res = {"rev": rev, "indent_equivalence": {}}
tmp = tempfile.mkdtemp(prefix="b41eq-")
for name in lib:
    topo = os.path.join(A, "library", name)
    names = [e["name"] for e in json.load(open(topo, encoding="utf-8"))["netlist"]]
    ov = {n: {"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": "stack_%s" % n} for n in names}
    pr = sd.run_topology_pipeline(topo, ov)
    sizing = {n: {k: 1.0 for k in ("W", "L", "ID", "gm", "gm_id")} for n in names}
    pr2 = dict(pr, scope_note="b41 측정 scope_note")
    outs = {}
    for tag, mfn in [("orig", fn)] + [(op, m) for op, p, m in muts if p == "body[6].body[0].value.keywords[0].value"]:
        code = compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(mfn)], type_ignores=[])), "<b41>", "exec")
        g = dict(sd.__dict__)
        exec(code, g)
        path = os.path.join(tmp, "%s_%s.json" % (name, tag.replace("+", "p").replace("-", "m")))
        g["save_instance_json"](path, topo, copy.deepcopy(sizing), copy.deepcopy(pr2))
        raw = open(path, "rb").read()
        outs[tag] = {"bytes_sha256": hashlib.sha256(raw).hexdigest(), "len": len(raw),
                     "parsed_sha256": hashlib.sha256(json.dumps(json.loads(raw.decode("utf-8")), sort_keys=True,
                                                                ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()}
    res["indent_equivalence"][name] = outs
append(res)
eq = all(o[t]["parsed_sha256"] == o["orig"]["parsed_sha256"] for o in res["indent_equivalence"].values() for t in o)
bd = all(o[t]["bytes_sha256"] != o["orig"]["bytes_sha256"] for o in res["indent_equivalence"].values() for t in o if t != "orig")
print(json.dumps({"revs": ns.revs, "bind_hash_last": mc.bind_hash(fn), "parsed_equal_all": eq, "bytes_differ_all": bd,
                  "circuits": lib}, ensure_ascii=False))
