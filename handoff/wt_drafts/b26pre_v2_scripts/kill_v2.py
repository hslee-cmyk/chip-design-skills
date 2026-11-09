"""b26pre v2 -- 표 1의 base 문장 32개(stmt_delete 31 + SD 3285 cmp_flip)를 변이해 시제품 v3(card v2, 17 test)만 실행한다.
변이 위치: base(a796468) 줄 번호 -> (최상위 def, 문장 첫 줄 글, def 안 순번)으로 바꿔 각 사본(base, b34)에서 다시 찾는다.
stmt_delete = 그 문장 노드 전체(복합문이면 몸통 포함)를 같은 들여쓰기의 `pass`로. cmp_flip = `is not` -> `is`.
사용: python -B kill_v2.py <copy> <NW>   결과: C:/g106/out/kill_<copy>.jsonl (변이마다 append)."""
import ast, json, os, shutil, sys, threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_proto as RP  # noqa: E402

A = "skills/analog-gmid-design/assets/"
SR, SD = A + "sizing_recipe.py", A + "stick_diagram.py"
MUTS = [(SR, l, "del") for l in (11696, 11698, 11700, 9404, 9406, 6573, 11835, 11836, 11837, 11800, 11801, 11802,
                                  11803, 11828, 11877, 11879, 11880, 11881)] + \
       [(SD, l, "del") for l in (2176, 2177, 2100, 2101, 3985, 3986, 4529, 4530, 3282, 3285, 3286, 6892, 6894)] + \
       [(SD, 3285, "flip")]


def read(root, f):
    with open(os.path.join(root, f), encoding="utf-8") as fh:
        return fh.read()


def top_defs(tree):
    return [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]


def stmts_in(node):
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.stmt) and n is not node:
            out.append(n)
    return sorted(out, key=lambda n: (n.lineno, n.col_offset))


def key_of(src, line):
    lines = src.split("\n")
    tree = ast.parse(src)
    for d in top_defs(tree):
        if d.lineno <= line <= d.end_lineno:
            cands = [n for n in stmts_in(d) if n.lineno == line]
            n = cands[0]  # 가장 바깥(같은 줄 시작 문장 중 첫째)
            text = lines[line - 1].strip()
            same = [m for m in stmts_in(d) if lines[m.lineno - 1].strip() == text]
            return d.name, text, same.index(n)
    raise KeyError(line)


def locate(src, key):
    name, text, idx = key
    lines = src.split("\n")
    d = [x for x in top_defs(ast.parse(src)) if x.name == name][0]
    same = [m for m in stmts_in(d) if lines[m.lineno - 1].strip() == text]
    return same[idx]


def mutate(src, node, op):
    lines = src.split("\n")
    i = node.lineno - 1
    ind = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
    if op == "del":
        new = lines[:i] + [ind + "pass"] + lines[node.end_lineno:]
    else:
        assert " is not None" in lines[i]
        new = list(lines)
        new[i] = lines[i].replace(" is not None", " is None", 1)
    out = "\n".join(new)
    ast.parse(out)
    return out


def main(copy, nw):
    base_src = {f: read("C:/g106/base", f) for f in (SR, SD)}
    root0 = "C:/g106/" + copy
    jobs = []
    for f, line, op in MUTS:
        key = key_of(base_src[f], line)
        src = read(root0, f)
        node = locate(src, key)
        jobs.append(dict(id="%s %s %d %s" % ("SR" if f == SR else "SD", op, line, key[0]), file=f,
                         line_in_copy=node.lineno, text=key[1][:70], src=mutate(src, node, op)))
    res_path = "C:/g106/out/kill_%s.jsonl" % copy
    done = set()
    if os.path.exists(res_path):
        done = {json.loads(l)["id"] for l in open(res_path, encoding="utf-8")}
    pool = []
    for k in range(nw):
        w = "C:/g106/w_%s%d" % (copy, k)
        if not os.path.exists(w):
            shutil.copytree(root0, w)
        RP.place(w)
        pool.append(w)
    lock = threading.Lock()

    def one(j):
        if j["id"] in done:
            return
        with lock:
            w = pool.pop()
        fp = os.path.join(w, j["file"])
        orig = open(fp, "rb").read()
        try:
            with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(j["src"])
            rc, dt, txt = RP.run(w, "1")
        finally:
            with open(fp, "wb") as fh:
                fh.write(orig)
            with lock:
                pool.append(w)
        failed = [l.split(" ", 1)[1].split(" - ")[0].split("::")[-1] for l in txt.splitlines() if l.startswith("FAILED ")]
        rec = dict(id=j["id"], line_in_copy=j["line_in_copy"], text=j["text"],
                   result="survived" if rc == 0 else "killed", exit=rc, s=round(dt, 1), failed=failed)
        with lock:
            with open(res_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(rec["result"], rec["id"], failed, flush=True)

    with ThreadPoolExecutor(nw) as ex:
        list(ex.map(one, jobs))
    print("DONE", copy, flush=True)


if __name__ == "__main__":
    os.makedirs("C:/g106/out", exist_ok=True)
    main(sys.argv[1], int(sys.argv[2]))
