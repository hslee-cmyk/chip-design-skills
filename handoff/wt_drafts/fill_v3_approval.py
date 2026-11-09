"""승인 기록 초안의 `<rev-parse>` 세 자리(target, diff_base, diff_head)를 채워 `.ai/approvals/<id>.md`를 쓴다.

    C:/Python314/python.exe -B fill_v3_approval.py --root <저장소 루트> --draft <초안 .md> --base <diff_base 커밋> --head <diff_head 커밋> [--check]

* diff_base·diff_head는 `git rev-parse`로 40자리로 바꾼다.
* target = `weakening_diff.diff_hash(root, base, head, diff_path 목록)`(00-common §8.2 blob 식, root의 tools/gates를 읽기 전용 import),
  같은 값을 `merge_gate.compute_diff_hash`(바뀌지 않은 경로·양쪽 없음 거부)로 다시 계산해 대조한다 -- 다르거나 거부면 쓰지 않는다.
* 초안 끝의 `<!-- 오케스트레이터: … -->` 주석 블록은 지운다(선례 `20260930-phase2-e4-phase`처럼 기록에는 남기지 않는다).
* 쓴 뒤 `merge_gate.parse_approval_header`로 머리를 파싱한다. 대상 파일이 이미 있고 내용이 다르면 거부(같으면 멱등 0).
* 줄 끝은 LF, BOM 없음(파서 요구). exit 0 성공 / 2 거부.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--draft", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--check", action="store_true")
    ns = ap.parse_args(argv)
    root = os.path.abspath(ns.root)
    sys.path.insert(0, os.path.join(root, "tools", "gates"))
    import merge_gate as mg
    import weakening_diff as wd

    def rev(r):
        out = subprocess.run(["git", "-C", root, "rev-parse", "--verify", "--quiet", r + "^{commit}"],
                             capture_output=True)
        if out.returncode != 0:
            raise SystemExit(fail("커밋이 아니다: %s" % r))
        return out.stdout.decode().strip()

    base, head = rev(ns.base), rev(ns.head)
    with open(ns.draft, "rb") as fh:
        text = fh.read().decode("utf-8")
    text = text.replace("\r\n", "\n")
    if text.count("<rev-parse>") != 3:
        return fail("초안의 `<rev-parse>` 자리가 3개가 아니다: %d" % text.count("<rev-parse>"))
    paths = re.findall(r"^diff_path: (.+)$", text.split("\n---\n", 1)[0], flags=re.M)
    rid = re.search(r"^id: (.+)$", text, flags=re.M).group(1).strip()
    h1 = wd.diff_hash(root, base, head, paths)
    try:
        h2 = mg.compute_diff_hash(mg.TreeView(["-C", root], base), mg.TreeView(["-C", root], head), paths)
    except mg.GateError as e:
        return fail("compute_diff_hash 거부: %s" % e)
    if h1 != h2:
        return fail("두 해시 식이 다르다: %s != %s" % (h1, h2))
    filled = text.replace("target: <rev-parse>", "target: " + h1, 1)
    filled = filled.replace("diff_base: <rev-parse>", "diff_base: " + base, 1)
    filled = filled.replace("diff_head: <rev-parse>", "diff_head: " + head, 1)
    if "<rev-parse>" in filled:
        return fail("자리 순서가 target/diff_base/diff_head 형식이 아니다")
    filled = re.sub(r"\n*<!-- 오케스트레이터:.*?-->\n*\Z", "\n", filled, flags=re.S)
    if "<!--" in filled:
        return fail("남은 HTML 주석이 있다")
    data = filled.encode("utf-8")
    rec = mg.parse_approval_header(data, rid + ".md")
    if rec["target"] != h1 or rec["diff_path"] != paths:
        return fail("파싱 결과가 채운 값과 다르다")
    dest = os.path.join(root, ".ai", "approvals", rid + ".md")
    res = {"id": rid, "target": h1, "diff_base": base, "diff_head": head, "diff_path": paths, "dest": dest}
    if os.path.exists(dest):
        with open(dest, "rb") as fh:
            cur = fh.read()
        if cur.replace(b"\r\n", b"\n") == data:
            res["result"] = "already-present(같은 내용)"
            return done(res)
        return fail("대상 파일이 이미 있고 내용이 다르다: %s" % dest)
    if ns.check:
        res["result"] = "ok(--check, 쓰지 않음)"
        return done(res)
    with open(dest, "wb") as fh:
        fh.write(data)
    res["result"] = "written"
    return done(res)


def done(res):
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


def fail(msg):
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"result": "REFUSED", "error": msg}, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
