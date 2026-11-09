"""b26pre -- card '재현할 수치' 표 1·2(markdown) 생성. 입력: kill_v4_N2d.jsonl, proto_card/proto_kill.jsonl, head_v4 소스.
줄 번호는 card base(HEAD a796468) 소스에서 같은 문장 글을 찾아 적는다(SR은 B34 불변, SD는 B34 사이트 밖).
출력: C:/g87/out/b26pre_tables.md"""
import ast, json, re, sys
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26pre_scripts")
import b26v4_kill as K   # noqa: E402
mc = K.mc

HEADF = {"stick_diagram": "C:/g87/head_v4/stick_diagram.py", "sizing_recipe": "C:/g87/head_v4/sizing_recipe.py"}
BASEF = {"stick_diagram": "C:/g87/base/skills/analog-gmid-design/assets/stick_diagram.py",
         "sizing_recipe": "C:/g87/base/skills/analog-gmid-design/assets/sizing_recipe.py"}
hs = {}
for m, f in HEADF.items():
    s = open(f, encoding="utf-8").read()
    hs[m] = dict(K.rch.iter_defs(ast.parse(s)))
bl = {m: open(f, encoding="utf-8").read().split("\n") for m, f in BASEF.items()}
bdefs = {m: dict(K.rch.iter_defs(ast.parse("\n".join(bl[m])))) for m in BASEF}
LM = {m: K.V.line_map("\n".join(bl[m]), open(HEADF[m], encoding="utf-8").read()) for m in BASEF}


def base_line_of_head(mod, h):
    """head 줄 -> base 줄. 같은 줄이면 그대로, 바뀐 줄이면 바로 앞 같은 줄에서 같은 거리."""
    m = LM[mod]
    if h in m:
        return m[h]
    hp = max(k for k in m if k < h)
    return m[hp] + (h - hp)


def head_node(mod, q, op, p):
    fn = hs[mod][q]
    np_ = K.V.node_path(op, p)
    return fn if not np_ else mc._get(fn, np_)


def stmt_of(mod, q, op, p):
    fn = hs[mod][q]
    np_ = K.V.node_path(op, p)
    pre = K.V.stmt_prefixes(np_) if np_ else []
    node = head_node(mod, q, op, p)
    if isinstance(node, ast.stmt):
        return node
    for sp in reversed(pre):
        n = mc._get(fn, sp)
        if isinstance(n, ast.stmt):
            return n
    return fn


def base_line(mod, q, st):
    """base def 안에서 rails 인자를 뺀 같은 문장 첫 줄을 찾는다."""
    if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return bdefs[mod][q].lineno
    first = ast.unparse(st).split("\n")[0]
    first = re.sub(r",\s*rails=rails", "", first).replace("rails.nets", "_RAIL_NETS")
    bfn = bdefs[mod][q]
    for i in range(bfn.lineno - 1, bfn.end_lineno):
        raw = bl[mod][i].strip()
        try:
            cand = ast.unparse(ast.parse(raw if not raw.endswith(":") else raw + " pass")).split("\n")[0]
        except SyntaxError:
            cand = raw
        if cand.rstrip(":").replace(" pass", "") == first.rstrip(":") or cand.startswith(first.rstrip(":")[:40]):
            return i + 1
    return None


def group(q, op, p):
    if q.startswith("optimize_full_circuit_budget"):
        return "E6-a"
    if q == "_fixup_euler_blocked_rows":
        return "E6-b"
    if q == "run_matching_safety_with_finger_growth":
        return "E6-c"
    if q == "run_full_circuit_audit" and "defaults" in p:
        return "E3"
    if q in ("_propose_gm_id_roles", "_propose_L_roles") and p in ("body[2]", "body[4]"):
        return "E4"
    if q in ("_propose_gm_id_roles", "_propose_L_roles") or (q == "propose_device_roles_gap_fill" and p.startswith("body[13]")):
        return "E7-seed"
    if q == "propose_device_roles_gap_fill" and p.startswith(("body[36]", "body[40]", "body[43]")):
        return "E1"
    return "E7"


rows = [json.loads(l) for l in open("C:/g87/out/e67/kill_v4_N2d.jsonl", encoding="utf-8")]
proto = {json.loads(l)["id"]: json.loads(l) for l in open("C:/g87/out/proto_card2/proto_kill.jsonl", encoding="utf-8")}
CONTRACT = {"E6-a": "1", "E6-b": "2", "E6-c": "3"}
t1, t2 = [], []
for r in sorted((r for r in rows if r["result"] == "survived"), key=lambda r: r["id"]):
    mod, q, op, p = r["id"].split(":", 3)
    g = group(q, op, p)
    st = stmt_of(mod, q, op, p)
    txt = ast.unparse(st).split("\n")[0][:70].replace("|", "\\|")
    ln = base_line_of_head(mod, st.lineno)
    defs = "/".join(k for k in ("N2b", "N2w", "N2d") if r[k]) if r["N2b"] else ("N2w" if r["N2w"] else "N2d만")
    pr = proto[r["id"]]
    res = "죽음 (" + ", ".join(sorted({f.split("::")[-1] for f in pr["failed"]})) + ")" if pr["result"] == "killed" else "생존"
    short = "SD" if mod == "stick_diagram" else "SR"
    row = "| %s | `%s` `%s` `%s` | %s %s | `%s` | %s | %s |" % (g, q, op, p, short, ln, txt, defs, res)
    (t1 if g.startswith(("E6", "E7")) else t2).append(row)
hdr = "| 묶음 | 변이(head def·연산자·경로) | base 줄(a796468) | 문장(head) | 정의 | 시제품 판정 |\n|---|---|---|---|---|---|"
out = "표 1\n\n" + hdr + "\n" + "\n".join(t1) + "\n\n표 2\n\n" + hdr + "\n" + "\n".join(t2) + "\n"
open("C:/g87/out/b26pre_tables.md", "w", encoding="utf-8").write(out)
print(len(t1), len(t2), sum("죽음" in x for x in t1), sum("죽음" in x for x in t2))
