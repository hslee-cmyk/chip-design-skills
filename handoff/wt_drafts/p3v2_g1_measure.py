"""Phase 3 design v2 부록 A G1~G3 측정(읽기 전용). 결과는 이 파일 옆 p3v2_g1_results.json에 쓴다(WP-11).

G1: 엔진 4파일 각각을 'base에 없는 새 파일'로 볼 때 base V3 대상 def·변이 수, base V6 '새 항목' 수(상한 추정).
G2: HEAD 트리에서 운영 루트로 도달하지 못하는 엔진 def 수(옮기면 base V7이 '새 def 미도달'로 셀 수).
G3: 합성 git 저장소(임시 디렉터리, 끝나면 지움)에서 def 하나를 바이트 그대로 옮긴 커밋에 base V6·V7을 실행.
저장소는 읽기만 한다(게이트 모듈 import는 `python -B`로 바이트코드를 쓰지 않는다).

    C:/Python314/python.exe -B p3v2_g1_measure.py
"""
import json, os, shutil, stat, subprocess, sys, tempfile

R = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
G = os.path.join(R, "tools", "gates")
PY = sys.executable
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "p3v2_g1_results.json")
sys.path.insert(0, G)
import mutate_changed as mc   # noqa: E402
import reachability as rch    # noqa: E402
import source_lint as sl      # noqa: E402

A = os.path.join(R, "skills", "analog-gmid-design", "assets")
ENGINE = ("sizing_recipe", "stick_diagram", "topology_library", "design_report")
res = {"head": subprocess.run(["git", "-C", R, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()}

# ---- G1
g1 = {}
for m in ENGINE:
    src = open(os.path.join(A, m + ".py"), "rb").read().decode("utf-8")
    defs = mc.changed_defs(None, src)
    by = {}
    for f in sl.compare(m + ".py", None, src, set()):
        by[f["check"]] = by.get(f["check"], 0) + (f["head"] - f["base"])
    g1[m] = {"defs": len(defs), "mutants": sum(1 for _q, fn in defs for _ in mc.mutants(fn, src)),
             "v6_new_items": by, "same_path_targets": len(mc.changed_defs(src, src))}
res["G1"] = g1

# ---- G2
cfg = json.loads(rch._git(R, ["show", "HEAD:tools/gates/gate_config.json"]).decode("utf-8"))
head = rch.read_tree(R, "HEAD", rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(head)
roots = sorted({r for v in cfg["reachability_roots"].values() for r in v if r.split("::")[0] in head})
seen = rch.reach(edges, roots)
eng = [n for n in nodes if rch._is_source(n.split("::")[0]) and not n.endswith(("::<module>", "::__main__"))
       and n.split("::")[0].rsplit("/", 1)[-1][:-3] in ENGINE]
unreached = sorted(n for n in eng if n not in seen)
approved = rch._approved_ids(R, "HEAD")
res["G2"] = {"roots": roots, "engine_defs": len(eng), "unreached": len(unreached),
             "unreached_unapproved": len([n for n in unreached if n not in approved]), "sample": unreached[:15]}

# ---- G3
RT = tempfile.mkdtemp(prefix="p3v2-g1-")


def git(*a):
    return subprocess.run(["git", "-C", RT] + list(a), capture_output=True, text=True, check=True).stdout.strip()


def write(rel, text):
    p = os.path.join(RT, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


try:
    git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")
    AS = "skills/analog-gmid-design/assets/"
    F = "def f(x):\n    try:\n        return x / 3.7\n    except Exception:\n        return None\n"
    write(AS + "a.py", "def run():\n    return 1\n\n" + F)
    write("workspaces/run_harness.py", "from a import run\n\ndef run2():\n    return run()\n")
    write("cfg.json", json.dumps({"reachability_roots": {"before_phase3": ["workspaces/run_harness.py::run2"]}}))
    git("add", "-A"); git("commit", "-q", "-m", "base"); base = git("rev-parse", "HEAD")
    write(AS + "b.py", F)
    write(AS + "a.py", "from b import f  # noqa: F401\n\ndef run():\n    return 1\n")
    git("add", "-A"); git("commit", "-q", "-m", "move f"); hd = git("rev-parse", "HEAD")
    g3 = {}
    for tool, extra in (("reachability.py", ["--config", os.path.join(RT, "cfg.json")]), ("source_lint.py", [])):
        p = subprocess.run([PY, "-B", os.path.join(G, tool), "--root", RT, "--base", base, "--head", hd] + extra,
                           capture_output=True, text=True, encoding="utf-8")
        g3[tool] = {"exit": p.returncode, "stdout": p.stdout.strip()}
    res["G3"] = g3
finally:
    def _onerr(func, path, _exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    shutil.rmtree(RT, onexc=_onerr)
    res["G3_tmp_removed"] = not os.path.exists(RT)

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print("wrote", OUT)
