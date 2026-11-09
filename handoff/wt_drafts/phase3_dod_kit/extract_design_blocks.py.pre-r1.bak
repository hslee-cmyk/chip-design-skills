"""Phase 3 DoD -- design 30 §10 bash 블록에서 판정 코드를 **그대로** 뽑는다(사본을 손으로 만들지 않는다).

    python -B extract_design_blocks.py <iso> <rev> <out_dir>

design 30 §10은 "명령은 아래 bash 블록이 정본"이라 적는다. 이 도구는 <rev> 판 design 30에서
  blk_e3_ast.py   = `E3_AST=$(cat <<'PYEOF'` .. `PYEOF`
  blk_e3b_ast.py  = `E3B_AST=$(cat <<'PYEOF'` .. `PYEOF`
  blk_e5_judge.py = `$PY - "$O" "$ISO" "$P2D" <<'PYEOF'` .. `PYEOF`
  blk_import_any.sh = `import_any() {` .. 첫 `}` 줄
  blk_vars.sh     = `EXCL='...'` 줄 + `MP_ARGS=(` .. `')` 줄
을 바이트 그대로 쓰고 sha256을 blk_sha256.txt에 적는다. 표지가 정확히 한 번씩 나오지 않으면 exit 1(INVALID).
읽기 전용: git show만 쓴다.
"""
import hashlib
import os
import re
import subprocess
import sys

D30 = "docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md"


def main(iso, rev, out):
    p = subprocess.run(["git", "-C", iso, "show", "%s:%s" % (rev, D30)], capture_output=True)
    if p.returncode != 0:
        sys.exit("git show 실패: " + p.stderr.decode("utf-8", "replace"))
    lines = p.stdout.decode("utf-8").replace("\r\n", "\n").split("\n")
    sec = [i for i, ln in enumerate(lines) if ln.startswith("## 10. ")]
    nxt = [i for i, ln in enumerate(lines) if ln.startswith("## 11. ")]
    if len(sec) != 1 or len(nxt) != 1 or nxt[0] < sec[0]:
        sys.exit("INVALID: §10/§11 머리를 정확히 한 번씩 찾지 못함")
    lo, hi = sec[0], nxt[0]   # 표지는 §10 안에서만 찾는다(§6.3에도 MP_ARGS 예시가 있다)

    def one(pred, what):
        idx = [i for i, ln in enumerate(lines) if lo < i < hi and pred(ln)]
        if len(idx) != 1:
            sys.exit("INVALID: 표지 %s 가 %d번 나온다" % (what, len(idx)))
        return idx[0]

    def heredoc(start_pred, what):
        s = one(start_pred, what)
        e = next((j for j in range(s + 1, len(lines)) if lines[j] == "PYEOF"), None)
        if e is None:
            sys.exit("INVALID: %s 끝 PYEOF 없음" % what)
        return s + 1, e

    blocks = {}
    a, b = heredoc(lambda ln: ln == "E3_AST=$(cat <<'PYEOF'", "E3_AST")
    blocks["blk_e3_ast.py"] = (a, b)
    a, b = heredoc(lambda ln: ln == "E3B_AST=$(cat <<'PYEOF'", "E3B_AST")
    blocks["blk_e3b_ast.py"] = (a, b)
    a, b = heredoc(lambda ln: ln == '$PY - "$O" "$ISO" "$P2D" <<\'PYEOF\'', "E5 판정 python")
    blocks["blk_e5_judge.py"] = (a, b)
    s = one(lambda ln: ln.startswith("import_any() {"), "import_any")
    e = next((j for j in range(s + 1, len(lines)) if lines[j] == "}"), None)
    if e is None:
        sys.exit("INVALID: import_any 끝 } 없음")
    blocks["blk_import_any.sh"] = (s, e + 1)
    ex = one(lambda ln: ln.startswith("EXCL='"), "EXCL")
    ms = one(lambda ln: ln.startswith("MP_ARGS=("), "MP_ARGS")
    me = next((j for j in range(ms, len(lines)) if re.search(r"'\)\s*(#.*)?$", lines[j])), None)
    if me is None:
        sys.exit("INVALID: MP_ARGS 끝 줄 없음")
    os.makedirs(out, exist_ok=True)
    sums = []
    for name, (a, b) in blocks.items():
        body = "\n".join(lines[a:b]) + "\n"
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        sums.append("%s  %s  design 줄 %d-%d" % (hashlib.sha256(body.encode("utf-8")).hexdigest(), name, a + 1, b))
    body = lines[ex] + "\n" + "\n".join(lines[ms:me + 1]) + "\n"
    with open(os.path.join(out, "blk_vars.sh"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    sums.append("%s  blk_vars.sh  design 줄 %d, %d-%d" % (hashlib.sha256(body.encode("utf-8")).hexdigest(), ex + 1, ms + 1, me + 1))
    with open(os.path.join(out, "blk_sha256.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("rev %s\n" % rev + "\n".join(sums) + "\n")
    print("\n".join(sums))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    main(*sys.argv[1:4])
