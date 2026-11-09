"""G1 머리 수치 재측정(측정 전용, 읽기 전용 -- 실제 저장소에 쓰지 않는다).

    python -B m9_measure.py <scratch C:/g<n>> <원본 복제본(base 도구, 예 C:/g143/b)> <시제품 복제본(예 C:/g143/p)> <order sim WORK> <출력 json>

H  (card '의도' 머리 수치, p3v2_g1_measure.py G1·G2와 같은 정의) 엔진 4파일 각각을 새 파일로 볼 때 base V3 대상 def·변이, base V6 새 항목 합,
   HEAD 트리에서 운영 루트 미도달 엔진 def(승인 면제 제외).
W  (G6' -- card '거짓 거부 0') 엔진 4파일을 같은 디렉터리 <m>_mv.py로 통째 옮기고 원본은 명시 재수출만 -- 시제품 moved_defs 단위·def 인정 수, 거부 규칙별 수,
   실제 도구(base / 시제품) V3 대상 def·변이(정적: 도구의 대상 선택 식 그대로), V6·V7 exit·항목 수(실제 CLI 실행).
M  (Phase 3 M card 모의 -- _drafts/p3_scripts/p3v6_order_shim_sim.py가 만든 state_M<k>) 앞 상태 → M<k> 쌍마다 같은 측정. M9가 머리.
케이스마다 <출력>.partial.jsonl에 append(WP-11).
"""
import ast
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time

S, BASE_CLONE, PROTO_CLONE, SIMW, OUT = sys.argv[1:6]
PY = sys.executable
AS = "skills/analog-gmid-design/assets/"
PART = OUT + ".partial.jsonl"
if os.path.exists(PART):
    os.remove(PART)
ENGINE = ("sizing_recipe", "stick_diagram", "topology_library", "design_report")


def log(kind, obj):
    with open(PART, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": kind, "data": obj}, ensure_ascii=False) + "\n")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


BG = os.path.join(BASE_CLONE, "tools", "gates")
PG = os.path.join(PROTO_CLONE, "tools", "gates")
sys.path.insert(0, BG)
import mutate_changed as mc   # noqa: E402  (base 도구 -- changed_defs·mutants)
import reachability as rch    # noqa: E402
import source_lint as sl      # noqa: E402
g1 = load("g1rch", os.path.join(PG, "reachability.py"))


def git(root, *a):
    r = subprocess.run(["git", "-C", root] + list(a), capture_output=True)
    if r.returncode:
        raise RuntimeError("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8", "replace").strip()


res = {"base_clone_head": git(BASE_CLONE, "rev-parse", "HEAD")}

# ------------------------------------------------------------------ H
head = rch.read_tree(BASE_CLONE, "HEAD", rch.GRAPH_PREFIXES)
H = {}
for m in ENGINE:
    src = head[AS + m + ".py"]
    defs = mc.changed_defs(None, src)
    by = {}
    for f in sl.compare(m + ".py", None, src, set()):
        by[f["check"]] = by.get(f["check"], 0) + (f["head"] - f["base"])
    H[m] = {"defs": len(defs), "mutants": sum(1 for _q, fn in defs for _ in mc.mutants(fn, src)), "v6_new_items": by}
cfg = json.loads(git(BASE_CLONE, "show", "HEAD:tools/gates/gate_config.json"))
nodes, edges = rch.build_graph(head)
roots = sorted({r for v in cfg["reachability_roots"].values() for r in v if r.split("::")[0] in head})
seen = rch.reach(edges, roots)
eng = [n for n in nodes if rch._is_source(n.split("::")[0]) and not n.endswith(("::<module>", "::__main__"))
       and n.split("::")[0].rsplit("/", 1)[-1][:-3] in ENGINE]
unr = sorted(n for n in eng if n not in seen)
appr = rch._approved_ids(BASE_CLONE, "HEAD")
res["H"] = {"per_file": H, "defs": sum(v["defs"] for v in H.values()), "mutants": sum(v["mutants"] for v in H.values()),
            "v6_new_items": sum(sum(v["v6_new_items"].values()) for v in H.values()),
            "engine_defs": len(eng), "unreached": len(unr), "unreached_unapproved": len([n for n in unr if n not in appr])}
log("H", res["H"])


# ------------------------------------------------------------------ 측정 저장소(시제품 복제본과 별개의 복제본 -- 상태를 커밋한다)
MR = os.path.join(S, "m")
if not os.path.exists(MR):
    subprocess.run(["git", "clone", "-c", "core.autocrlf=false", "-q", "--no-hardlinks", "--no-local", BASE_CLONE, MR], check=True)
    git(MR, "remote", "remove", "origin")
    git(MR, "config", "user.email", "g1kit@local")
    git(MR, "config", "user.name", "g1kit")
    git(MR, "config", "core.autocrlf", "false")
    git(MR, "config", "core.hooksPath", os.path.join(S, "nohooks"))
CFG = os.path.join(BG, "gate_config.json")


def commit_files(files, msg, drop=()):
    for rel, text in files.items():
        p = os.path.join(MR, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    for rel in drop:
        p = os.path.join(MR, *rel.split("/"))
        if os.path.exists(p):
            os.remove(p)
    git(MR, "add", "-A", "--", "skills", "workspaces")
    git(MR, "commit", "-q", "--allow-empty", "-m", msg)
    return git(MR, "rev-parse", "HEAD")


def tool(gates, script, b, h, extra=()):
    t0 = time.time()
    r = subprocess.run([PY, "-B", os.path.join(gates, script), "--root", MR, "--base", b, "--head", h] + list(extra),
                       capture_output=True, timeout=3600)
    out = r.stdout.decode("utf-8", "replace")
    obj = None
    for line in out.splitlines():
        if line.strip().startswith("{"):
            try:
                obj = json.loads(line)
                break
            except ValueError:
                pass
    return r.returncode, obj, round(time.time() - t0, 1)


def v3_static(bf, hf, moved=None):
    defs = mut = 0
    for p, s in hf.items():
        if not rch._is_source(p) or bf.get(p) == s:
            continue
        for q, fn in mc.changed_defs(bf.get(p), s):
            if moved is not None and g1.g1_excluded(moved, p, q, fn):
                continue
            defs += 1
            mut += sum(1 for _ in mc.mutants(fn, s))
    return {"defs": defs, "mutants": mut}


def measure(label, bf, hf, b, h):
    t0 = time.time()
    g1.G1_STATS.clear()
    mv = g1.moved_defs({k: v for k, v in bf.items() if rch._is_source(k)}, {k: v for k, v in hf.items() if rch._is_source(k)})
    t_mv = round(time.time() - t0, 2)
    rej = {}
    for v in mv["rejected"].values():
        rej[v["rule"]] = rej.get(v["rule"], 0) + 1
    rec = {"label": label, "units_moved": len(mv["units"]), "defs_moved": len(mv["defs"]), "rejected_by_rule": rej,
           "rejected_sample": dict(list(mv["rejected"].items())[:6]), "moved_defs_seconds": t_mv,
           "parse_counts": dict(g1.G1_STATS),
           "v3_base_static": v3_static(bf, hf), "v3_proto_static": v3_static(bf, hf, mv)}
    for name, gates in (("base", BG), ("proto", PG)):
        c6, o6, s6 = tool(gates, "source_lint.py", b, h)
        c7, o7, s7 = tool(gates, "reachability.py", b, h, ["--config", CFG])
        rec[name] = {"V6": {"exit": c6, "findings": len((o6 or {}).get("findings", [])),
                            "new_items": sum(f["head"] - f["base"] for f in (o6 or {}).get("findings", [])), "sec": s6},
                     "V7": {"exit": c7, "new_defs": len((o7 or {}).get("new_defs", [])),
                            "unreached_without_approval": len((o7 or {}).get("unreached_without_approval", [])), "sec": s7,
                            "moved": len((o7 or {}).get("moved", []) or [])}}
    log("pair", rec)
    return rec


B0 = git(MR, "rev-parse", "HEAD")
base_files = rch.read_tree(MR, B0, rch.GRAPH_PREFIXES)

# ------------------------------------------------------------------ W: 엔진 4파일 통째 이동(같은 디렉터리)
hf = dict(base_files)
for m in ENGINE:
    p = AS + m + ".py"
    src = base_files[p]
    tree = ast.parse(src)
    tops = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            tops.add(n.name)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                tops |= {x.id for x in ast.walk(t) if isinstance(x, ast.Name)}
    tops = sorted(x for x in tops if not x.startswith("__"))
    hf[AS + m + "_mv.py"] = src
    hf[p] = "from %s_mv import (%s)  # noqa\n" % (m, ", ".join(tops))
HW = commit_files({k: v for k, v in hf.items() if k not in base_files or base_files[k] != v}, "W rename")
w = measure("W-rename-4", base_files, hf, B0, HW)
w["units_total"] = sum(len(g1.SourceIndex({AS + m + ".py": base_files[AS + m + ".py"]}).units(AS + m + ".py")) for m in ENGINE)
w["defs_total"] = sum(len(rch.iter_defs(ast.parse(base_files[AS + m + ".py"]))) for m in ENGINE)
res["W"] = w
log("W_totals", {"units_total": w["units_total"], "defs_total": w["defs_total"]})
git(MR, "reset", "-q", "--hard", B0)

# ------------------------------------------------------------------ M: order sim 상태
states = sorted((d for d in os.listdir(SIMW) if d.startswith("state_M")), key=lambda d: int(d[7:]))
prev_files, prev_c = base_files, B0
res["M"] = []
for d in states:
    sd = os.path.join(SIMW, d)
    cur = dict(base_files)
    for f in os.listdir(sd):
        if f.endswith(".py"):
            with open(os.path.join(sd, f), encoding="utf-8", newline="") as fh:
                cur[AS + f] = fh.read().replace(chr(13) + chr(10), chr(10))   # 모의가 복사한 원본 파일은 CRLF 체크아웃 사본
    drop = [k for k in prev_files if k.startswith(AS) and k.count("/") == 3 and k not in cur]
    c = commit_files({k: v for k, v in cur.items() if prev_files.get(k) != v}, d, drop)
    cur = rch.read_tree(MR, c, rch.GRAPH_PREFIXES)
    r = measure(d, prev_files, cur, prev_c, c)
    res["M"].append(r)
    prev_files, prev_c = cur, c

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps({"H": res["H"], "W": {k: res["W"][k] for k in ("units_total", "units_moved", "defs_total", "defs_moved", "rejected_by_rule",
                                                                 "v3_base_static", "v3_proto_static", "base", "proto")},
                  "M": [{k: r[k] for k in ("label", "units_moved", "defs_moved", "rejected_by_rule", "v3_base_static", "v3_proto_static", "base", "proto")}
                        for r in res["M"]]}, ensure_ascii=False, indent=1))
