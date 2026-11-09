# S1v 구조 분류(AC cell 종류·블록 역할)만 읽는다 -- 엔진 build_s1v 를 구조 사실 추출 도구로만 사용(판정 근거 아님).
import sys, json, pathlib, traceback
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG)); sys.path.insert(0, str(ENG / "gmid_engine/tests/graph"))
import s1v_hand as H
_orig = H.lib_supplies
def _sup(name):
    try: return _orig(name)
    except KeyError:
        sp = json.load(open(ENG/"assets/library"/(name+".sizing_spec.json"), encoding="utf-8"))
        return {k: v for k, v in sp["human"]["supplies_v"]["values"].items()}
H.lib_supplies = _sup
OUT = pathlib.Path(__file__).with_name("s1v_roles.jsonl")
names = sorted(p.name.replace(".topology.json", "") for p in (ENG / "assets/library").glob("*.topology.json") if not p.name.startswith("_"))
if OUT.exists(): OUT.unlink()
for n in names:
    try:
        s1, s1v = H.build_lib(n)
        rec = dict(circuit=n, views=[])
        for v in s1v.views:
            rec["views"].append(dict(id=v.id, excite=[list(x) for x in v.excite] if getattr(v, "excite", None) else None,
                sense=list(v.sense) if getattr(v, "sense", None) else None,
                cells={c.dev: c.kind for c in v.cells},
                blocks=[dict(key=list(b.key), kind=b.kind, stage=b.stage, inputs=list(b.inputs), members=list(getattr(b, "members", [])) if not isinstance(getattr(b,"members",None), dict) else list(b.members), roles=[list(x) for x in (getattr(b, "roles", None) or [])]) for b in v.blocks]))
        rec["findings"] = [f.code for f in s1v.all_findings]
    except BaseException as e:
        rec = dict(circuit=n, error=repr(e)[:400], tb=traceback.format_exc()[-800:])
    with open(OUT, "a", encoding="utf-8") as fh: fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    print(n, "error" in rec and rec["error"][:100] or "ok")
