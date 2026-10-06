"""계약 9 -- 주표(N2w 20 id)·참고표(N2d만 16) 변이 죽임 측정(auditor 작성, 브리프 2.3 (다)·(라)·(마)).

    python -B kill_b26pre.py map            # 대응만 -> C:/g372/out/kill_map.json
    python -B kill_b26pre.py run [--only i,j]   # 대응 + 실행 -> C:/g372/out/kill_results.jsonl(변이마다 append)

* 도구 = base 판 캐시 mutate_changed.py의 mutants·_replace_def·changed_defs, reachability.iter_defs(실제 도구 함수).
* 대상 id = H4(B26-1 v4 모의 head, C:/g372/r) 기준 주표 20 id(ids_b26v4.json). 대응: H4 문장을 B1(= base) 같은 def에서
  찾는다 -- `rails=` 키워드를 지운 ast.dump 비교, if/while은 test만, for는 iter만, 같은 모양이 둘 이상이면 같은 깊이·가장 가까운 경로.
  대응 뒤 변이 노드(head·base)의 dump가 같은지도 확인한다.
* 참고표 16 = base def 안에서 (def, 문장 글)로 찾는다(유일해야 한다).
* 실행 사본 = C:/g372/kt(T 클론: 엔진 = base, 새 test 포함). 변이마다 모듈 파일을 _replace_def 결과로 쓰고, T의 새 test 파일만
  PYTHONHASHSEED=1, base 판 캐시 ini, --gmid-phase=3 --gmid-strict=, -rA로 실행. 죽음 = exit 1이고 FAILED 1개 이상.
  끝나면 원본 바이트로 되돌리고 git diff --quiet(exit 0) 확인. 기준(변이 없음)·복원(끝) 실행과 def 항등 치환(unparse만) 대조도 한다.
"""
import ast
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import time

BASE = "ae1b5886e6fd4b5b18d6096d8ac6076259719ff3"
T = "e4d5833f89a9a96db7410ce4bfc53703f4f9ef3f"
CACHE = "C:/g372/gmid-gate-cache/" + BASE
R = "C:/g372/r"
KT = "C:/g372/kt"
OUT = "C:/g372/out"
PY = "C:/Python314/python.exe"
AS = "skills/analog-gmid-design/assets/"
MODP = {"sizing_recipe": AS + "sizing_recipe.py", "stick_diagram": AS + "stick_diagram.py"}
TESTF = AS + "tests/contracts/test_b26pre_existing_paths.py"
sys.path.insert(0, CACHE)
import mutate_changed as mc   # noqa: E402
import reachability as rch     # noqa: E402

HEADS = json.load(open(OUT + "/heads.json", encoding="utf-8"))
H4 = HEADS["H4"]
assert HEADS["B1"] == BASE, HEADS


def git(root, *a):
    r = subprocess.run(["git", "-C", root] + list(a), capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r.stdout


SRC = {}


def src(rev, mod):
    k = (rev, mod)
    if k not in SRC:
        SRC[k] = git(R, "show", "%s:%s" % (rev, MODP[mod])).decode("utf-8")
    return SRC[k]


def defs(text):
    return dict(rch.iter_defs(ast.parse(text)))


def strip_rails(n):
    n = copy.deepcopy(n)
    for x in ast.walk(n):
        if isinstance(x, ast.Call):
            x.keywords = [k for k in x.keywords if k.arg != "rails"]
    return n


def key(stmt):
    if isinstance(stmt, (ast.If, ast.While)):
        return (type(stmt).__name__, ast.dump(strip_rails(stmt.test)))
    if isinstance(stmt, (ast.For, ast.AsyncFor)):
        return ("For", ast.dump(strip_rails(stmt.iter)))
    return ("S", ast.dump(strip_rails(stmt)))


def idx(path):
    return [(f, int(i)) for f, i in re.findall(r"([A-Za-z_]+)\[(\d+)\]", path)]


def dist(p, q):
    a, b = idx(p), idx(q)
    return (0 if len(a) == len(b) else 1, 0 if [f for f, _ in a] == [f for f, _ in b] else 1,
            sum(abs(x[1] - y[1]) for x, y in zip(a, b)))


def stmt_prefix(fn, path):
    """path에서 ast.stmt를 가리키는 가장 긴 접두와 나머지."""
    parts = re.findall(r"\.?[A-Za-z_]+(?:\[\d+\])?", path)
    best = None
    acc = ""
    for p in parts:
        acc += p
        a = acc.lstrip(".")
        if isinstance(mc._get(fn, a), ast.stmt):
            best = a
    return best, path[len(best):]


def first_line(text, node):
    return text.split("\n")[node.lineno - 1].strip()


def find_mutant(fn, text, op, path):
    hit = [f for o, p, f in mc.mutants(fn, text) if o == op and p == path]
    assert len(hit) == 1, (op, path, len(hit))
    return hit[0]


def map_main():
    ids = json.load(open(OUT + "/ids_b26v4.json", encoding="utf-8"))
    out = []
    for i, mid in enumerate(ids, 1):
        mod, qual, op, path = mid.split(":", 3)
        htext, btext = src(H4, mod), src(BASE, mod)
        hfn, bfn = defs(htext)[qual], defs(btext)[qual]
        hp, suffix = stmt_prefix(hfn, path) if op != "stmt_delete" else (path, "")
        hs = mc._get(hfn, hp)
        k = key(hs)
        cands = [p for n, p in mc._path_nodes(bfn) if isinstance(n, ast.stmt) and p and key(n) == k]
        assert cands, ("대응 없음", mid)
        cands.sort(key=lambda p: dist(p, hp))
        bp = cands[0]
        bnode = mc._get(bfn, bp + suffix)
        hnode = mc._get(hfn, path)
        same_node = ast.dump(strip_rails(bnode)) == ast.dump(strip_rails(hnode)) if op != "stmt_delete" else \
            key(mc._get(bfn, bp)) == k
        bstmt = mc._get(bfn, bp)
        out.append({"n": i, "table": "main", "head_id": mid, "module": mod, "qual": qual, "op": op,
                    "head_path": path, "base_path": bp + suffix, "n_candidates": len(cands),
                    "base_line": bstmt.lineno, "base_text": first_line(btext, bstmt), "head_line": hs.lineno,
                    "node_equal_mod_rails": same_node})
    return out


REF = [  # (module, qual, op, 문장 글(첫 줄), 그 문장 안의 상대 경로 접미, 몇 번째 자식(None = 그 문장 자체), 기대 base 줄 메모)
    ("sizing_recipe", "run_matching_safety_with_finger_growth", "stmt_delete", "if a not in all_devs or b not in all_devs:", None, "SR 11834"),
    ("sizing_recipe", "run_matching_safety_with_finger_growth", "stmt_delete", "if a not in all_devs or b not in all_devs:", "body[0]", "SR 11835"),
    ("sizing_recipe", "run_matching_safety_with_finger_growth", "stmt_delete", "if a not in all_devs or b not in all_devs:", "body[1]", "SR 11836"),
    ("sizing_recipe", "run_matching_safety_with_finger_growth", "stmt_delete", "if result.ok:", "body[0]", "SR 11801 (card 11802)"),
    ("sizing_recipe", "run_matching_safety_with_finger_growth", "stmt_delete", "if result.ok:", "body[1]", "SR 11802 (card 11803)"),
    ("sizing_recipe", "run_matching_safety_with_finger_growth", "stmt_delete", "@line11827", None, "SR 11827 (card 11828)"),
    ("stick_diagram", "_propose_L_roles", "stmt_delete", "seeds[ga] = gb", None, "SD seed L ga->gb"),
    ("stick_diagram", "_propose_L_roles", "stmt_delete", "seeds[gb] = ga", None, "SD seed L gb->ga"),
    ("stick_diagram", "_propose_gm_id_roles", "stmt_delete", "seeds[ga] = gb", None, "SD seed gm ga->gb"),
    ("stick_diagram", "_propose_gm_id_roles", "stmt_delete", "seeds[gb] = ga", None, "SD seed gm gb->ga"),
    ("stick_diagram", "propose_device_roles_gap_fill", "stmt_delete", "seed_net_pairs[ga] = gb", None, "SD seed gapfill ga->gb"),
    ("stick_diagram", "propose_device_roles_gap_fill", "stmt_delete", "seed_net_pairs[gb] = ga", None, "SD seed gapfill gb->ga"),
    ("stick_diagram", "propose_device_roles_gap_fill", "stmt_delete", "review_needed.append({'case_collisions': disp.case_collisions})", None, "SD case_collisions append"),
    ("stick_diagram", "propose_vertical_stack_id_gap_fill", "cmp_flip", "if relations is not None:", ".test.ops[0]", "SD relations is not None (cmp_flip)"),
    ("stick_diagram", "propose_vertical_stack_id_gap_fill", "stmt_delete", "if relations is not None:", None, "SD relations is not None (delete)"),
    ("stick_diagram", "propose_vertical_stack_id_gap_fill", "stmt_delete", "edges.extend((rel['devices'] for rel in relations['differential']))", None, "SD edges.extend differential"),
]


def map_ref():
    out = []
    for i, (mod, qual, op, txt, sub, memo) in enumerate(REF, 1):
        btext = src(BASE, mod)
        bfn = defs(btext)[qual]
        if txt.startswith("@line"):
            ln = int(txt[5:])
            c = [p for n, p in mc._path_nodes(bfn) if isinstance(n, ast.stmt) and p and n.lineno == ln]
            c = [c[-1]] if c else []
        else:
            c = [p for n, p in mc._path_nodes(bfn) if isinstance(n, ast.stmt) and p
                 and ast.unparse(n).split("\n")[0] == txt]
        assert len(c) == 1, (memo, c)
        sp = c[0]
        if sub and not sub.startswith("."):
            sp = sp + "." + sub
            suffix = ""
        else:
            suffix = sub or ""
        st = mc._get(bfn, sp)
        assert isinstance(st, ast.stmt)
        out.append({"n": i, "table": "ref", "memo": memo, "module": mod, "qual": qual, "op": op,
                    "base_path": sp + suffix, "base_line": st.lineno, "base_text": first_line(btext, st)})
    return out


def extras():
    """(마) 덤: trace 줄 const-(등가 기대), 동점 순서 역전(텍스트 치환, 계약 10 '정확히 하나' 단언은 통과 기대)."""
    return [
        {"n": 1, "table": "extra", "memo": "trace range const- (range(i + 0, ...)) -- 등가 기대",
         "module": "stick_diagram", "qual": "find_differential_pair_candidates", "op": "const-", "base_path": None},
        {"n": 2, "table": "extra", "memo": "동점 순서 역전(이름 역순) -- 계약 10 test는 PASS 기대",
         "module": "stick_diagram", "qual": None, "op": "text",
         "old": "        pending.sort(key=lambda item: (-len(item[1]), item[0].name))\n",
         "new": "        pending.sort(key=lambda item: item[0].name, reverse=True)\n        pending.sort(key=lambda item: -len(item[1]))\n"},
    ]


CONTRACT = {}
for c, names in {
    "1": ["test_b26pre_ofcb_lutless_repair"], "2": ["test_b26pre_euler_fixup_group_split"],
    "3": ["test_b26pre_growth_zero_rounds", "test_b26pre_growth_zero_rounds_euler", "test_b26pre_growth_already_ok",
          "test_b26pre_growth_pair_not_found", "test_b26pre_growth_only_3b_left"],
    "4": ["test_b26pre_full_audit_all_disposed", "test_b26pre_full_audit_mirror_undisposed",
          "test_b26pre_full_audit_diffpair_undisposed", "test_b26pre_full_audit_hub_gnd_undisposed"],
    "5": ["test_b26pre_resolve_stack_candidates"], "6": ["test_b26pre_vsid_gap_fill_no_ports", "test_b26pre_vsid_gap_fill_ports"],
    "7": ["test_b26pre_case_collisions"], "10": ["test_b26pre_seed_tap_p", "test_b26pre_seed_tap_n"],
    "11": ["test_b26pre_trace_two_branches", "test_b26pre_trace_three_branches_order"]}.items():
    for n in names:
        CONTRACT[n] = c

RUN_N = [0]


def pytest_run(tag):
    RUN_N[0] += 1
    pyc = "C:/g372/pyc/kill/%03d" % RUN_N[0]
    os.makedirs(pyc, exist_ok=True)
    env = dict(os.environ, PYTHONHASHSEED="1", PYTHONPYCACHEPREFIX=pyc, PYTHONPATH=CACHE,
               TMP="C:/g372/tmp", TEMP="C:/g372/tmp", TMPDIR="C:/g372/tmp", PYTHONIOENCODING="utf-8")
    cmd = [PY, "-P", "-m", "pytest", "-c", CACHE + "/pytest_gate.ini", "--rootdir=" + KT, "--confcutdir=" + KT,
           KT + "/" + TESTF, "--gmid-phase=3", "--gmid-strict=", "-rA", "-p", "no:cacheprovider"]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, env=env)
    txt = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    os.makedirs(OUT + "/kill_logs", exist_ok=True)
    open(OUT + "/kill_logs/%s.txt" % tag, "w", encoding="utf-8").write(txt)
    failed = sorted({m.split("::")[-1].split(" ")[0] for m in re.findall(r"^FAILED (\S+)", txt, re.M)})
    errors = re.findall(r"^ERROR (\S+)", txt, re.M)
    passed = len(re.findall(r"^PASSED ", txt, re.M))
    summ = (re.findall(r"^=+ (.*) in [0-9.]+s", txt, re.M) or [""])[-1]
    return {"exit": r.returncode, "failed": failed, "n_failed": len(failed), "n_error": len(errors), "n_passed": passed,
            "summary": summ, "sec": round(time.time() - t0, 1),
            "killed": r.returncode == 1 and len(failed) >= 1,
            "killing_contracts": sorted({CONTRACT.get(f, "?") for f in failed}, key=lambda s: (len(s), s))}


ORIG = {}


def orig_bytes(mod):
    if mod not in ORIG:
        ORIG[mod] = open(KT + "/" + MODP[mod], "rb").read()
    return ORIG[mod]


def restore(mod):
    open(KT + "/" + MODP[mod], "wb").write(orig_bytes(mod))
    r = subprocess.run(["git", "-C", KT, "diff", "--quiet"])
    assert r.returncode == 0, "복원 실패 %s" % mod


def apply(rec):
    mod = rec["module"]
    text = orig_bytes(mod).decode("utf-8")
    assert text == src(BASE, mod), "T 트리 엔진이 base와 다르다"
    if rec["op"] == "text":
        assert text.count(rec["old"]) == 1
        new = text.replace(rec["old"], rec["new"])
    elif rec["op"] == "identity":
        fn = defs(text)[rec["qual"]]
        new = mc._replace_def(text, fn, copy.deepcopy(fn))
    else:
        fn = defs(text)[rec["qual"]]
        if rec["base_path"] is None:   # extra const-: trace 줄
            main = [m for m in MAP if m["table"] == "main" and m["op"] == "const+"][0]
            rec["base_path"] = main["base_path"]
        f = find_mutant(fn, text, rec["op"], rec["base_path"])
        new = mc._replace_def(text, fn, f)
    assert new != text
    open(KT + "/" + MODP[mod], "wb").write(new.encode("utf-8"))
    rec["mutated_sha256"] = hashlib.sha256(new.encode("utf-8")).hexdigest()


def log(rec):
    with open(OUT + "/kill_results.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


MAP = []
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    MAP = map_main() + map_ref()
    json.dump(MAP, open(OUT + "/kill_map.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for m in MAP:
        print(m["table"], m["n"], m["op"], m.get("base_line"), "|", m.get("base_text", "")[:70], "|", m.get("n_candidates", ""),
              m.get("node_equal_mod_rails", ""))
    if sys.argv[1] == "map":
        sys.exit(0)
    assert git(KT, "rev-parse", "HEAD").decode().strip() == T
    assert subprocess.run(["git", "-C", KT, "diff", "--quiet"]).returncode == 0
    b = pytest_run("baseline_before")
    log({"table": "baseline", "tag": "before", **b})
    print("baseline", b["summary"], b["exit"])
    assert b["exit"] == 0
    idents = sorted({(m["module"], m["qual"]) for m in MAP if m.get("qual")})
    jobs = [dict(m) for m in MAP] + extras() + [
        {"table": "identity", "n": k, "module": mo, "qual": q, "op": "identity"} for k, (mo, q) in enumerate(idents, 1)]
    for rec in jobs:
        tag = "%s_%02d" % (rec["table"], rec["n"])
        try:
            apply(rec)
            res = pytest_run(tag)
        finally:
            restore(rec["module"])
        rec.update(res)
        rec["tag"] = tag
        log(rec)
        print(tag, rec["op"], rec.get("base_line"), "killed" if res["killed"] else "survived", res["summary"], res["failed"])
    e = pytest_run("baseline_after")
    log({"table": "baseline", "tag": "after", **e})
    print("restore", e["summary"], e["exit"])
