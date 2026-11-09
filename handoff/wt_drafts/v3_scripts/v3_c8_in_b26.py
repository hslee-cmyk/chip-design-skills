"""C8 면제 문장(load_topology 10, save_instance_json 4)이 B26-1 시뮬레이션 head에서 어떤 id가 되고 정의별 대상인지. 결과: C:/g60/out/v3_c8_in_b26.txt"""
import ast, sys

sys.path.insert(0, "C:/g60/scripts")
import v3_scope_classify as V   # noqa: E402

S, mc, rch = V.S, V.mc, V.rch
OUT = open("C:/g60/out/v3_c8_in_b26.txt", "w", encoding="utf-8")
C8_BASE_PATHS = ["body[11].body[2]", "body[11].body[3]", "body[11].body[4]", "body[11].body[5]", "body[11].body[6]",
                 "body[26].body[1]", "body[26].body[1].body[0]", "body[26].body[2].body[0]", "body[26].body[2].body[1]",
                 "body[26].body[2].body[2]"]
b26, _ = S.build_b26(S.BASEF)
bfn = dict(rch.iter_defs(ast.parse(S.BASEF[S.SD])))["load_topology"]
hfn = dict(rch.iter_defs(ast.parse(b26[S.SD])))["load_topology"]
texts = {ast.unparse(mc._get(bfn, p)).split("\n")[0]: p for p in C8_BASE_PATHS}
rows, info = V.classify(bfn, hfn, b26[S.SD])
hp_text = {p: ast.unparse(n).split("\n")[0] for n, p in mc._path_nodes(hfn) if isinstance(n, ast.stmt)}
for t in rows:
    if t["op"] != "stmt_delete":
        continue
    txt = hp_text.get(t["path"])
    if txt in texts:
        flags = {d: bool(V.DEFS[d](t)) for d in ("N2b", "N2a", "D1b")}
        line = "C8 %s -> B26-1 head %s | %s | %s" % (texts[txt], t["path"], txt[:70], flags)
        print(line)
        OUT.write(line + "\n")
OUT.close()
