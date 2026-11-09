"""b26pre -- 생존 변이 목록을 사람용 표로(변이 id, N2b/N2w/N2d, head 줄, b1 줄, 문장 첫 줄, 묶음).
입력: C:/g87/out/e67/kill_v4_N2d.jsonl, (있으면) C:/g87/out/proto_card/proto_kill.jsonl. 출력: C:/g87/out/survivors.txt"""
import ast, json, os, sys
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26pre_scripts")
import b26v4_kill as K   # noqa: E402
mc = K.mc

HEAD = {"stick_diagram": "C:/g87/head_v4/stick_diagram.py", "sizing_recipe": "C:/g87/head_v4/sizing_recipe.py"}
B1 = {"stick_diagram": "C:/g87/b1/skills/analog-gmid-design/assets/stick_diagram.py",
      "sizing_recipe": "C:/g87/b1/skills/analog-gmid-design/assets/sizing_recipe.py"}


def defs(path):
    src = open(path, encoding="utf-8").read()
    return src, dict(K.rch.iter_defs(ast.parse(src)))


def locate(mod, q, op, p, srcs):
    src, d = srcs[mod]
    fn = d[q]
    np_ = K.V.node_path(op, p)
    try:
        node = mc._get(fn, np_) if np_ else fn
    except Exception:
        return None, "?"
    ln = getattr(node, "lineno", None)
    try:
        txt = ast.unparse(node).split("\n")[0][:110]
    except Exception:
        txt = type(node).__name__
    return ln, txt


def group(q, op, p):
    if q.startswith("optimize_full_circuit_budget"):
        return "E6-a"
    if q == "_fixup_euler_blocked_rows":
        return "E6-b"
    if q == "run_matching_safety_with_finger_growth":
        return "E6-c"
    if q in ("_propose_gm_id_roles", "_propose_L_roles") and p in ("body[2]", "body[4]"):
        return "E4(B26-1 계약 14)"
    if q in ("_propose_gm_id_roles", "_propose_L_roles") or (q == "propose_device_roles_gap_fill" and p.startswith("body[13]")):
        return "E7-seed"
    if q == "propose_device_roles_gap_fill" and p.startswith(("body[36]", "body[40]", "body[43]")):
        return "E1(B26-1 계약 7(e))"
    return "E7"


hs = {m: defs(f) for m, f in HEAD.items()}
bs = {m: defs(f) for m, f in B1.items()}
rows = [json.loads(l) for l in open("C:/g87/out/e67/kill_v4_N2d.jsonl", encoding="utf-8")]
proto = {}
if os.path.exists("C:/g87/out/proto_card/proto_kill.jsonl"):
    for l in open("C:/g87/out/proto_card/proto_kill.jsonl", encoding="utf-8"):
        r = json.loads(l)
        proto[r["id"]] = r
out = []
tot = {"killed": 0, "survived": 0}
for r in rows:
    tot[r["result"]] += 1
surv = sorted((r for r in rows if r["result"] == "survived"), key=lambda r: r["id"])
out.append("kill_v4_N2d: %d mutants (%s), survivors %d" % (len(rows), tot, len(surv)))
for r in surv:
    mod, q, op, p = r["id"].split(":", 3)
    hl, ht = locate(mod, q, op, p, hs)
    bop, bp = r["b1"].split(":", 1)
    bl, _bt = locate(mod, q, bop, bp, bs)
    pr = proto.get(r["id"])
    pk = "-" if pr is None else ("KILLED " + ",".join(f.split("::")[-1] for f in pr["failed"])) if pr["result"] == "killed" else "survived"
    out.append("%-20s %-58s N2b=%d N2w=%d N2d=%d head:%s b1:%s | %s | proto: %s" % (
        group(q, op, p), r["id"], r["N2b"], r["N2w"], r["N2d"], hl, bl, ht, pk))
open("C:/g87/out/survivors.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
