"""backfill 결함 card(20261001-b26-backfill-interdig-final-audit) 착수 키트 -- V3 측정용 모의 커밋 사슬.

격리 복제본 C:/g128/sim/r(origin 없음, 빈 hooksPath)에 다음 커밋을 만든다(저장소는 읽기만):
  P0 = a796468 (gate master 0f23786과 tools/·skills/·workspaces/ 차이 0)
  B1 = P0 + B34 코드 변경(stick_diagram 4 def, _drafts/b26pre_v2_scripts/mk_g106.py와 같은 def_replace 치환)
  BP = B1 + b26pre 시제품 test(_drafts/b26pre_v2_scripts/proto_v2_test_b26pre.py → A/tests/contracts/test_b26pre_existing_paths.py)
  H  = BP + 수정 후보(run_matching_safety_with_finger_growth의 사전 backfill 두 줄 삭제)
          + 이 card 시제품 test(proto_bf_test.py → A/tests/contracts/test_b26_backfill_interdig.py)
  HF = BP + 수정 후보만(test 없음 -- red 확인용)
결과: C:/g128/out/setup_v3.json (커밋 해시), stdout.
사용: python -B setup_v3.py <원본 저장소>"""
import ast, json, os, subprocess, sys

SRC = sys.argv[1]
G = "C:/g128"
CL = G + "/sim/r"
DR = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts"
A = "skills/analog-gmid-design/assets/"
SD, SR = A + "stick_diagram.py", A + "sizing_recipe.py"
T_PRE = A + "tests/contracts/test_b26pre_existing_paths.py"
T_BF = A + "tests/contracts/test_b26_backfill_interdig.py"


def git(*a, cwd=CL):
    r = subprocess.run(["git", "-C", cwd] + list(a), capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8", "replace")


def defs(tree, prefix=""):
    for n in ast.iter_child_nodes(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            q = prefix + n.name
            yield q, n
            yield from defs(n, q + ".")


def def_replace(src, qual, old, new):
    fn = dict(defs(ast.parse(src)))[qual]
    lines = src.split("\n")
    seg = "\n".join(lines[fn.lineno - 1:fn.end_lineno])
    assert seg.count(old) == 1, (qual, seg.count(old))
    return "\n".join(lines[:fn.lineno - 1] + seg.replace(old, new).split("\n") + lines[fn.end_lineno:])


def b34(src):
    src = def_replace(src, "_import_analog_grammar", "    except ImportError:\n        return tuple(None for _ in module_names)",
                      "    except ImportError as e:\n        raise ImportError(\"analog-grammar skill을 import할 수 없다(탐색 경로 %s)\" % _ag_path) from e")
    src = def_replace(src, "find_idiom_matches", "    if netclass is None:\n        return None\n", "")
    src = def_replace(src, "find_stack_edges", "    if netclass is None:\n        return None\n", "")
    src = def_replace(src, "audit_theta_root_direction", "    if netclass_mod is None or idioms_mod is None:\n        return []\n", "")
    src = def_replace(src, "audit_theta_root_direction", "    if matches is None:\n        return []\n", "")
    ast.parse(src)
    return src


def fix(src):
    """수정 후보: 루프 안·루프 뒤 `_backfill_interdig_ok(result)` 두 줄 삭제(정리 함수 안 호출은 남김)."""
    fn = dict(defs(ast.parse(src)))["run_matching_safety_with_finger_growth"]
    lines = src.split("\n")
    hit = [i for i in range(fn.lineno - 1, fn.end_lineno) if lines[i].strip() == "_backfill_interdig_ok(result)"]
    assert len(hit) == 2, hit
    keep = [i for i in range(fn.lineno - 1, fn.end_lineno) if lines[i].strip() == "_backfill_interdig_ok(fixed_audit)"]
    assert len(keep) == 1, keep
    for i in reversed(hit):
        del lines[i]
    out = "\n".join(lines)
    ast.parse(out)
    return out, [i + 1 for i in hit]


def commit(parent, files, msg, branch):
    git("checkout", "--quiet", "-B", branch, parent)
    for rel, txt in files.items():
        p = os.path.join(CL, *rel.split("/"))
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(txt)
        git("add", "--", rel)
    git("commit", "--quiet", "-m", msg)
    return git("rev-parse", "HEAD").strip()


def show(rev, path):
    return git("show", "%s:%s" % (rev, path))


if __name__ == "__main__":
    os.makedirs(G + "/out", exist_ok=True)
    if not os.path.exists(CL):
        os.makedirs(G + "/sim/nohooks", exist_ok=True)
        subprocess.run(["git", "clone", "-c", "core.autocrlf=false", "-q", "--no-hardlinks", "--no-local", "--no-checkout", SRC, CL], check=True)
        git("remote", "remove", "origin")
        git("config", "core.longpaths", "true")
        git("config", "core.hooksPath", G + "/sim/nohooks")
        git("config", "core.autocrlf", "false")
    P0 = git("rev-parse", "a796468").strip()
    GM = git("rev-parse", "0f23786").strip()
    same = subprocess.run(["git", "-C", CL, "diff", "--quiet", P0, GM, "--", "tools", "skills", "workspaces"]).returncode == 0
    B1 = commit(P0, {SD: b34(show(P0, SD))}, "sim: B34 code", "sim-b1")
    pre = open(DR + "/b26pre_v2_scripts/proto_v2_test_b26pre.py", encoding="utf-8").read()
    BP = commit(B1, {T_PRE: pre}, "sim: b26pre proto test", "sim-bp")
    fsrc, deleted = fix(show(BP, SR))
    bf = open(DR + "/b26pre_v2_scripts/proto_bf_test.py", encoding="utf-8").read()
    H = commit(BP, {SR: fsrc, T_BF: bf}, "sim: backfill fix + proto test", "sim-h")
    HT = commit(BP, {T_BF: bf}, "sim: backfill proto test only (T)", "sim-t")
    git("checkout", "--quiet", "--detach", H)
    res = {"P0": P0, "GM": GM, "P0_GM_same_tools_skills_workspaces": same, "B1": B1, "BP": BP, "H": H, "T": HT,
           "deleted_lines_in_BP": deleted}
    with open(G + "/out/setup_v3.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))
