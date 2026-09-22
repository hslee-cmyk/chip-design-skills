"""C9(ts2-pytest-split) 섹션 -> test 매핑표 생성기 (design 10-test-separation v1.2 §6.8).

입력(둘 다 git 객체로 읽는다 -- 작업 트리와 무관):
  * 번호 기준: C2 병합 커밋 6abe0fc의 이관본(§6.8-1 '섹션 번호는 C2 병합 커밋의 이관본').
  * 변환 대상: --head 커밋의 이관본(C4 뒤 범주, §6.8-2 '범주(C4 뒤)').
섹션 경계는 C12(20260922-sections-major-merge)로 고친 `tools/migrate/extract_selftest.py sections`의 출력이다.
C4가 지운 섹션은 번호를 비워 둔다. HEAD 섹션은 표지 원문(title)으로 C2 섹션에 순서대로 대응시키고, 대응이 하나라도
안 되면 멈춘다(추측 금지).

실행: python build_c9_mapping.py --repo <저장소 루트> --head <커밋> --out <json>
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile

MODULES = ("sizing_recipe", "stick_diagram", "design_report", "topology_library")
C2_MERGE = "6abe0fc"
LEGACY = "skills/analog-gmid-design/assets/tests/legacy/selftest_%s.py"
TOOL = "tools/migrate/extract_selftest.py"
SLUG_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?=\()")


def git_show(repo, rev, path):
    return subprocess.run(["git", "-C", repo, "show", "%s:%s" % (rev, path)], capture_output=True, check=True).stdout


def sections(repo, head, src_bytes, tmp, name):
    p = os.path.join(tmp, name + ".py")
    with open(p, "wb") as f:
        f.write(src_bytes)
    tool = os.path.join(tmp, "extract_selftest.py")
    if not os.path.exists(tool):
        with open(tool, "wb") as f:
            f.write(git_show(repo, head, TOOL))
    o = p + ".json"
    subprocess.run([sys.executable, tool, "sections", "--source", p, "--out", o], check=True)
    with open(o, encoding="utf-8") as f:
        d = json.load(f)
    return d if isinstance(d, list) else d["sections"]


def marker_text(title):
    """표지 print의 첫 인자 정적 텍스트(design §5.1)."""
    try:
        call = ast.parse(title.strip()).body[0].value
        a = call.args[0]
    except (SyntaxError, IndexError, AttributeError):
        return ""
    if isinstance(a, ast.Constant) and isinstance(a.value, str):
        return a.value
    if isinstance(a, ast.JoinedStr):
        return "".join(v.value for v in a.values if isinstance(v, ast.Constant))
    return ""


def is_raise_ae(n):
    return isinstance(n, ast.Raise) and n.exc is not None and "AssertionError" in ast.unparse(n.exc)


def is_reject_try(n):
    """거부 try(§6.8-4): try 본문에 `raise AssertionError` 또는 `assert False`가 있고 except가 있는 것."""
    if not (isinstance(n, ast.Try) and n.handlers):
        return False
    for b in n.body:
        for x in ast.walk(b):
            if is_raise_ae(x):
                return True
            if isinstance(x, ast.Assert) and isinstance(x.test, ast.Constant) and x.test.value is False:
                return True
    return False


def judgements(block, s):
    """섹션 판정 분석 -> (거부 try 밖 판정의 'if·try 아래' 여부 목록, 거부 try 수).

    거부 try 안의 `assert False`/`raise AssertionError`는 §6.8-4에서 `pytest.raises` 하나가 되므로 따로 세지 않는다
    (C4가 `raise AssertionError`를 `assert False`로 바꿔 design §7 M2 식의 asserts가 그것을 포함하게 됐다)."""
    js = []
    rejects = [0]

    def walk(n, anc, inrej):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            return
        if (isinstance(n, ast.Assert) or is_raise_ae(n)) and not inrej:
            js.append(any(isinstance(a, (ast.If, ast.Try)) for a in anc))
        rej = is_reject_try(n)
        if rej and not inrej:
            rejects[0] += 1
        for c in ast.iter_child_nodes(n):
            walk(c, anc + [n], inrej or rej)

    for st in block.body:
        if s["start"] <= st.lineno <= s["end"]:
            walk(st, [], False)
    return js, rejects[0]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--known-limitation", action="append", default=[],
                    help="<모듈>:<C2 번호> -- 사용자 결정으로 test 2개(xfail + 현재 동작)로 나눌 섹션")
    ns = ap.parse_args(argv)
    head = subprocess.run(["git", "-C", ns.repo, "rev-parse", ns.head], capture_output=True, check=True,
                          text=True).stdout.strip()
    kl = set(ns.known_limitation)
    out = {"c2_merge": C2_MERGE, "head": head, "tool": TOOL, "modules": {}}
    with tempfile.TemporaryDirectory() as tmp:
        for m in MODULES:
            c2_src = git_show(ns.repo, C2_MERGE, LEGACY % m)
            head_src = git_show(ns.repo, head, LEGACY % m)
            c2 = sections(ns.repo, head, c2_src, tmp, m + ".c2")
            hs = sections(ns.repo, head, head_src, tmp, m + ".head")
            tree = ast.parse(head_src.decode("utf-8"))
            block = [n for n in tree.body if isinstance(n, ast.If)][-1]
            j = 0
            rows = []
            for s in hs:
                k = j
                while k < len(c2) and c2[k]["title"] != s["title"]:
                    k += 1
                if k == len(c2):
                    sys.exit("대응 실패: %s HEAD 섹션 %d %r" % (m, s["index"], s["title"][:80]))
                j = k + 1
                num = c2[k]["index"]
                row = {"head_index": s["index"], "number": num, "kind": s["kind"], "category": s["category"],
                       "start": s["start"], "end": s["end"], "title": s["title"],
                       "asserts": s["asserts"], "raise_assertion": s["raise_assertion"],
                       "reject_try": s["reject_try"],
                       "deps": [{"name": d["name"], "number": hs[d["section"]]["index"]} for d in s["deps"]]}
                rows.append(row)
            hidx2num = {r["head_index"]: r["number"] for r in rows}
            for r in rows:
                r["deps"] = [{"name": d["name"], "number": hidx2num[d["number"]]} for d in r["deps"]]
            readers = {d["number"] for r in rows for d in r["deps"]}
            for i, r in enumerate(rows):
                cat = r["category"]
                if cat == "P":
                    r["target"] = "header"
                elif cat == "D":
                    nxt = rows[i + 1]["number"] if i + 1 < len(rows) else None
                    r["target"] = "docstring_of"
                    r["docstring_of"] = nxt
                elif cat in ("A", "B"):
                    slug_m = SLUG_RE.search(marker_text(r["title"]))
                    slug = slug_m.group(0) if slug_m else "section"
                    tid = "test_s%03d_%s" % (r["number"], slug)
                    r["target"] = "test"
                    r["test_ids"] = [tid]
                    js, nrej = judgements(block, r)
                    r["judgements_outside_reject_try"] = len(js)
                    r["reject_try_ast"] = nrej
                    r["m2_min"] = len(js) + nrej
                    r["guarded_only"] = bool(js) and all(js)
                    if "%s:%d" % (m, r["number"]) in kl:
                        r["known_limitation"] = "I-C11"
                        r["test_ids"] = [tid, tid + "_known_limitation"]
                elif cat == "C":
                    r["target"] = "fixture" if r["number"] in readers else "none"
                rows[i] = r
            out["modules"][m] = {"c2_sections": len(c2), "head_sections": len(hs),
                                 "c2_numbers_removed_by_c4": sorted(set(x["index"] for x in c2) -
                                                                    set(r["number"] for r in rows)),
                                 "sections": rows}
    with open(ns.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    for m, d in out["modules"].items():
        tests = [t for r in d["sections"] for t in r.get("test_ids", [])]
        print(m, "sections", d["head_sections"], "tests", len(tests),
              "guarded_only", ["S%03d" % r["number"] for r in d["sections"] if r.get("guarded_only")],
              "fixtures", ["S%03d" % r["number"] for r in d["sections"] if r.get("target") == "fixture"])


if __name__ == "__main__":
    main(sys.argv[1:])
