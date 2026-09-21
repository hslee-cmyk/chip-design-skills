"""10-test-separation design 부록 A -- IC5·IC3 설계 입력 실측(분석 부산물, 판정 도구 아님).

(1) IC5: `skills/analog-gmid-design/assets/*.py`와 `workspaces/run_harness.py`에서 이름이 IC5 패턴
    (`check_`/`verify_`/`validate_`/`audit_`/`reject_`/`require_` 접두, `load_*_checked`)인 함수(모든 깊이, `if __name__` 블록 안 제외)와
    docstring에 `검사하지 않는 것:` 줄·`영역:` 줄이 있는지.
(2) IC3: library topology(`_TEMPLATE` 제외)의 이름 충돌 -- 소자 이름 중복, 소자∩수동소자 이름, 소자·수동소자 이름의 대소문자만 다른 쌍.
(3) IC3: 추적되는 `workspaces/*/*.instance.json` 중 library topology를 참조하는 것의 필드 완전성(설계 §5.5 필드 목록).

출력: 같은 디렉터리 ic_inputs.json. 사용: C:/Python314/python.exe measure_ic_inputs.py <저장소 루트>
"""
import ast
import collections
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
PAT = re.compile(r"^(check_|verify_|validate_|audit_|reject_|require_)|^load_.*_checked$")
TOP = ("schema_version", "topology_ref", "sizing", "netlist", "floorplan", "box_shape", "audit_row_split", "coverage")
SZ = ("W", "L", "ID", "gm", "gm_id")


def ic5():
    rows = []
    files = sorted(glob.glob(str(ROOT / "skills/analog-gmid-design/assets/*.py"))) + [str(ROOT / "workspaces/run_harness.py")]
    for f in files:
        t = ast.parse(open(f, encoding="utf-8").read())
        main = [n for n in t.body if isinstance(n, ast.If) and ast.unparse(n.test).replace("'", '"') == '__name__ == "__main__"']
        inside = {id(x) for m in main for x in ast.walk(m)}
        for n in ast.walk(t):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and PAT.search(n.name) and id(n) not in inside:
                d = ast.get_docstring(n) or ""
                rows.append({"file": os.path.basename(f), "name": n.name, "line": n.lineno,
                             "blind_spot_clause": bool(re.search(r"^\s*검사하지 않는 것:", d, re.M)),
                             "domain_line": bool(re.search(r"^\s*영역:", d, re.M))})
    return rows


def ic3_names():
    out = {}
    for f in sorted(glob.glob(str(ROOT / "skills/analog-gmid-design/assets/library/*.topology.json"))):
        if os.path.basename(f).startswith("_"):
            continue
        d = json.load(open(f, encoding="utf-8"))
        names = [e.get("name") for e in d.get("netlist", []) if isinstance(e, dict)]
        pe = d.get("passive_elements", [])
        pnames = [p.get("name") for p in pe] if isinstance(pe, list) else list(pe) if isinstance(pe, dict) else []
        ci = collections.defaultdict(set)
        for n in names + pnames:
            ci[str(n).casefold()].add(n)
        out[os.path.basename(f)] = {
            "devices": len(names), "passives": len(pnames),
            "duplicate_devices": sorted(n for n, c in collections.Counter(names).items() if c > 1),
            "device_passive_overlap": sorted(set(names) & set(pnames)),
            "case_only_collisions": sorted(sorted(v) for v in ci.values() if len(v) > 1)}
    return out


def ic3_instances():
    out = {}
    tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "workspaces/*/*.instance.json"],
                             capture_output=True, text=True).stdout.split()
    for rel in tracked:
        d = json.load(open(ROOT / rel, encoding="utf-8"))
        topo = ROOT / "skills/analog-gmid-design/assets/library" / os.path.basename(d.get("topology_ref", ""))
        if not topo.is_file():
            out[rel] = {"skipped": "topology_ref가 library 파일이 아니다: " + os.path.basename(d.get("topology_ref", ""))}
            continue
        tn = [e["name"] for e in json.load(open(topo, encoding="utf-8"))["netlist"]]
        nn = {e.get("name") for e in d.get("netlist", [])}
        out[rel] = {"missing_top": [k for k in TOP if k not in d],
                    "missing_sizing": [n for n in tn if n not in d.get("sizing", {})],
                    "missing_fields": {n: [k for k in SZ if k not in d["sizing"][n]] for n in tn
                                       if n in d.get("sizing", {}) and any(k not in d["sizing"][n] for k in SZ)},
                    "missing_netlist": [n for n in tn if n not in nn],
                    "coverage_missing": d.get("coverage", {}).get("missing")}
    return out


if __name__ == "__main__":
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    res = {"commit": head, "ic5_gates": ic5(), "ic3_library_names": ic3_names(), "ic3_tracked_instances": ic3_instances()}
    p = Path(__file__).resolve().parent / "ic_inputs.json"
    p.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    g = res["ic5_gates"]
    print(f"written {p}: IC5 gates {len(g)}, clause {sum(r['blind_spot_clause'] for r in g)}, domain {sum(r['domain_line'] for r in g)}; "
          f"library collisions {sum(bool(v['duplicate_devices'] or v['device_passive_overlap'] or v['case_only_collisions']) for v in res['ic3_library_names'].values())}")
