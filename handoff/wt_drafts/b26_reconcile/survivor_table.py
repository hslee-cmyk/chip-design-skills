"""통합 생존 표(v4 head, N2w, b1 = HEAD + B34): 기존 test에서 사는 변이마다 줄 번호·문장·세 시제품 판정.
입력: C:/g103/out/{proto.jsonl, existing.jsonl, trace_v4.jsonl, plan_A_proto.jsonl}, _drafts/b26_reconcile/out/consolidated.json
출력: _drafts/b26_reconcile/out/survivor_table.md
"""
import ast, json, os, sys

R = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile/"
G = "C:/g103/out/"
sys.path.insert(0, R)
import b26v4_classify as C   # noqa: E402
V, S, mc, rch = C.V, C.S, C.mc, C.rch


def jl(p):
    return {json.loads(l)["id"]: json.loads(l) for l in open(p, encoding="utf-8")} if os.path.exists(p) else {}


head = {}
for f in ("stick_diagram.py", "sizing_recipe.py"):
    head[f] = open("C:/g103/head_v4/" + f, encoding="utf-8").read()
defs = {f: dict(rch.iter_defs(ast.parse(s))) for f, s in head.items()}
bdefs = {f.split("/")[-1]: dict(rch.iter_defs(ast.parse(s))) for f, s in S.BASEF.items() if f.endswith(("stick_diagram.py", "sizing_recipe.py"))}


def lineno(fn, op, path):
    if op == "early_return":
        return fn.body[0].lineno if fn.body else fn.lineno
    np_ = V.node_path(op, path)
    try:
        n = mc._get(fn, np_)
        return getattr(n, "lineno", None) or fn.lineno
    except Exception:
        return None


rows = json.load(open(R + "out/consolidated.json", encoding="utf-8"))
proto = jl(G + "proto.jsonl")
tr = jl(G + "trace_v4.jsonl")
pa = jl(G + "plan_A_proto.jsonl")
EQ = {"stick_diagram:_propose_L_roles:stmt_delete:body[2]": "등가(중복 가드)",
      "stick_diagram:_propose_L_roles:stmt_delete:body[4]": "등가(중복 가드)",
      "stick_diagram:propose_device_roles_gap_fill:const-:body[40].body[8].value.slice": "등가(len==1 뒤 [0]→[-1])",
      "stick_diagram:find_differential_pair_candidates:const-:body[8].body[3].body[1].body[0].iter.args[0].right": "등가(j==i 짝은 전 위치 a==b로 건너뜀)"}
out = ["| # | 변이 id(head def·연산자·경로) | head 줄 | b1 줄 | 문장(head) | 분석 | 기존 test | B26-1 계약 근사 | b26pre v1 시제품 | b26pre v2 시제품(시나리오 A) | trace 보강 | 판정 |",
       "|---|---|---|---|---|---|---|---|---|---|---|---|"]
k = 0
for r in sorted(rows, key=lambda r: r["id"]):
    if r["existing"].startswith("killed"):
        continue
    k += 1
    mod, q, op, path = r["id"].split(":", 3)
    f = mod + ".py"
    fn = defs[f][q]
    hl = lineno(fn, op, path)
    b1p = proto[r["id"]]["b1"]
    bop, bpath = b1p.split(":", 1)
    bpath = ast.literal_eval(bpath)[1] if bpath.startswith("(") else bpath
    bl = lineno(bdefs[f][q], bop, bpath)
    txt = head[f].split("\n")[hl - 1].strip()[:70].replace("|", "\\|") if hl else ""
    if op == "early_return":
        txt = "(def 첫머리 return None 삽입)"
    an = []
    if r["con"] == "killed" or q in ("_propose_gm_id_roles",):
        pass
    con = "죽음(%s)" % ",".join(r["con_failed"]) if r["con"] == "killed" else "생존"
    pre = "죽음(%s)" % ",".join(r["pre_failed"]) if r["pre"] == "killed" else "생존"
    # 시나리오 A의 base는 backfill 두 줄을 지운 baseF라 이 def의 AST 경로가 밀린다 -- id로 대조하지 않는다
    p2 = None if q == "run_matching_safety_with_finger_growth" else pa.get(r["id"])
    pre2 = ("죽음(%s)" % ",".join(p2["pre_failed"]) if p2["pre"] == "killed" else "생존") if p2 else ("—(A base에서 경로 이동, v2 문장 대조 = b26pre_v2_kill_map: 11800·11879 생존, 나머지 죽음)" if q == "run_matching_safety_with_finger_growth" else "—")
    t = tr.get(r["id"])
    trs = ("죽음" if t["result"] == "killed" else "생존") if t else "—"
    if r["id"] in EQ:
        verdict = EQ[r["id"]]
    elif "_backfill" in txt:
        verdict = "등가 아님(결함, U-BF) -- backfill card가 문장 삭제"
    elif r["con"] == "killed":
        verdict = "B26-1 자기 계약"
    elif r["pre"] == "killed" or (p2 and p2["pre"] == "killed"):
        verdict = "b26pre card"
    elif t and t["result"] == "killed":
        verdict = "b26pre 보강(trace)"
    else:
        verdict = "남음"
    out.append("| %d | `%s` | %s | %s | `%s` | %s | %s | %s | %s | %s | %s | %s |" % (
        k, r["id"], hl, bl, txt, "B26-1·b26pre" if q in ("optimize_full_circuit_budget", "optimize_full_circuit_budget._evaluate_row_split",
                                                               "_fixup_euler_blocked_rows", "run_matching_safety_with_finger_growth",
                                                               "run_full_circuit_audit", "resolve_stack_layout",
                                                               "propose_vertical_stack_id_gap_fill") or "case_collisions" in txt else "B26-1",
        r["existing"], con, pre, pre2, trs, verdict))
os.makedirs(R + "out", exist_ok=True)
open(R + "out/survivor_table.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
print(k, "rows")
