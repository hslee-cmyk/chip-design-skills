"""LA-1a 선행 card 병합 상태: git 읽기 명령만 쓴다. 결과는 카드마다 n8_predecessors.jsonl에 append."""
import json
import pathlib
import subprocess

R = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
HERE = pathlib.Path(__file__).parent
OUT = HERE / "n8_predecessors.jsonl"
ENGINE = "skills/analog-gmid-design/gmid_engine"
CODE_PATHS = ["skills/analog-gmid-design/gmid_engine", "skills/analog-gmid-design/tools",
              "skills/analog-gmid-design/assets"]
REFS = ["master", "integ/it12"]


def git(*a):
    p = subprocess.run(["git", "-C", R, *a], capture_output=True, text=True, encoding="utf-8")
    return p.stdout


def n_commits(ref, key, paths):
    return len(git("log", ref, "--oneline", f"--grep={key}", "--", *paths).splitlines())


def n_files(ref, sym):
    return len(git("grep", "-l", sym, ref, "--", ENGINE).splitlines())


def n_verif(ref, key):
    names = git("ls-tree", "--name-only", ref, ".ai/verification/").splitlines()
    k = key.replace("-", "").lower()
    return sum(1 for n in names if n.endswith(".json") and k in n.replace("-", "").lower())


CARDS = [
    ("IT-1", "direct", ["input_tie"]), ("IT-2", "direct", []),
    ("WB-1", "direct", ["def dc_solve", "dc_finger"]),
    ("UB-1", "direct", ["block_gain_model_of"]), ("NL-1", "direct", []),
    ("HC-S", "direct", ["sat_threshold"]), ("TB-1", "direct", ["theta_class"]),
    ("HC-1", "direct", ["J_point", "loop_dependents"]), ("GC-8", "direct", ["order_terms"]),
    ("EO-1", "transitive", ["dc_sat_v", "judged_by"]), ("OP-3", "transitive", []),
    ("OP-7", "transitive", []), ("SF-1", "la1_only", []), ("LA-0", "la1_only", []),
    ("LA-1a", "self", []), ("LA-1", "self", []),
]

OUT.write_text("", encoding="utf-8")
for name, kind, syms in CARDS:
    rec = {"card": name, "kind": kind}
    for ref in REFS:
        rec[ref] = {
            "engine_commits": n_commits(ref, name, [ENGINE]),
            "code_commits": n_commits(ref, name, CODE_PATHS),
            "verdict_records": n_verif(ref, name),
            "symbols": {s: n_files(ref, s) for s in syms},
            "symbols_no_tests": {s: len(git("grep", "-l", s, ref, "--", ENGINE, ":!*/tests/*").splitlines()) for s in syms},
        }
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

for b in ["card/it2c", "role/code/it1", "role/code/it2a", "role/code/it2b", "role/code/it2d",
          "role/code/it2e", "design/oracle-eo1"]:
    sha = git("rev-parse", "--verify", "-q", b).strip()
    rec = {"branch": b, "sha": sha[:8]}
    for ref in REFS:
        if sha:
            p = subprocess.run(["git", "-C", R, "merge-base", "--is-ancestor", b, ref])
            rec["in_" + ref] = p.returncode == 0
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

with OUT.open("a", encoding="utf-8") as f:
    f.write(json.dumps({"heads": {r: git("rev-parse", "--short", r).strip() for r in REFS}}) + "\n")
print(OUT.read_text(encoding="utf-8"))
