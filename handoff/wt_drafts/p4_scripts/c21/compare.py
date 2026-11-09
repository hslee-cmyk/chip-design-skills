"""c21 비교: E-LIB(e_lib_p3.py 출력)와 E-INST(e_inst_p3 출력) -- 결과를 out/compare.txt에 쓴다.
판정기 두 모양을 같은 입력에 돌린다:
  J-hash   : '#21 card base(= B26-1 뒤) 대 병합본: e_lib_p3.py MASK 없음 hash 같음(meta["rails"] 포함 9/9)'
  J-mask   : Phase 3 v8.2 E5 모양 -- MASK=("rails",) hash 같음 + masked.rails가 __dc__ RailDeclaration·nets = supply_nets
             (필드 집합은 보지 않음 -- p3v82_e5_judge.py 그대로의 조건)
  J-mask+  : J-mask + masked.rails의 필드 집합이 base와 같음"""
import glob, hashlib, json, os, re
X = os.path.dirname(os.path.abspath(__file__)); O = os.path.join(X, "out")
LIB = r"C:/g148/base/skills/analog-gmid-design/assets/library"
lines = []
def p(*a):
    lines.append(" ".join(str(x) for x in a))
ld = lambda n: json.load(open(os.path.join(O, n), encoding="utf-8"))
E = {}
for v in ("base", "p1", "p20", "p21", "x1", "x2", "x4"):
    for m in ("nomask", "mask"):
        E[v, m] = ld("elib_%s_%s.json" % (v, m))
p("== E-LIB hash (e_lib_p3.py; nomask = e_lib.py와 같은 hash, mask = meta['rails'] 뺌)")
for v in ("base", "p1", "p20", "p21", "x1", "x2", "x4"):
    nl = [n for n, c in E[v, "nomask"]["circuits"].items() if not c["ok"].get("load")]
    p("  %-4s nomask %s  mask %s  load 실패 %d %s" % (v, E[v, "nomask"]["hash"][:16], E[v, "mask"]["hash"][:16], len(nl), nl[:3]))
G = {v: ld("gate_%s.json" % v) for v in ("base", "p1", "p20", "p21", "x1", "x2", "x4")}
def keys(v, n):
    c = G[v]["library"][n]
    if not c["ok"]:
        return "EXC " + c["exc"]
    return c["value"]["meta_keys"]
p("== meta 키 집합(회로별) -- base 대비 더해진 키")
for v in ("p1", "p20", "p21", "x1", "x2", "x4"):
    add = {}
    for n in E["base", "nomask"]["circuits"]:
        kb, kv = keys("base", n), keys(v, n)
        if isinstance(kv, str):
            add[n] = kv; continue
        d = sorted(set(kv) - set(kb)), sorted(set(kb) - set(kv))
        add[n] = d
    uniq = {json.dumps(x) for x in add.values()}
    p("  %-4s (더한 키, 빠진 키) 9회로 값 종류: %s" % (v, sorted(uniq)))
def judge(base, head):
    sup = {}
    for f in glob.glob(os.path.join(LIB, "*.topology.json")):
        n = os.path.basename(f)[:-len(".topology.json")]
        if not n.startswith("_"):
            sup[n] = json.load(open(f, encoding="utf-8")).get("supply_nets")
    jh = E[base, "nomask"]["hash"] == E[head, "nomask"]["hash"] and all(c["ok"].get("load") for c in E[head, "nomask"]["circuits"].values())
    jm, jmp = E[base, "mask"]["hash"] == E[head, "mask"]["hash"], None
    jmp = jm
    bad = []
    for n, nets in sup.items():
        hv = E[head, "mask"]["circuits"][n]["masked"].get("rails")
        bv = E[base, "mask"]["circuits"][n]["masked"].get("rails")
        want = {"__set__": sorted(nets, key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False))}
        ok = isinstance(hv, dict) and hv.get("__dc__") == "RailDeclaration" and hv.get("nets") == want
        if not ok:
            jm = jmp = False; bad.append(n)
        elif isinstance(bv, dict) and sorted(bv) != sorted(hv):
            jmp = False; bad.append(n + "(필드 " + ",".join(sorted(set(hv) - set(bv))) + ")")
    return jh, jm, jmp, bad
p("== #21 판정기 대조 (base = B26-1 뒤 판 p20 -- #21 card base 대용; head = 각 판)")
for head in ("p21", "x1", "x2", "x4"):
    jh, jm, jmp, bad = judge("p20", head)
    p("  head %-4s  J-hash %s  J-mask %s  J-mask+ %s  %s" % (head, "PASS" if jh else "FAIL", "PASS" if jm else "FAIL", "PASS" if jmp else "FAIL", bad[:4]))
p("== 참고: B26-1 시제품 자체(Phase 3 E5 모양) base -> p1")
jh, jm, jmp, bad = judge("base", "p1") if False else (None, None, None, None)
bm = E["base", "mask"]["hash"] == E["p1", "mask"]["hash"]
p("  base mask hash == p1 mask hash: %s ; base nomask == p1 nomask: %s" % (bm, E["base", "nomask"]["hash"] == E["p1", "nomask"]["hash"]))
p("  p1 nomask == p20 nomask (CC-5 최소 시제품 무동작): %s" % (E["p1", "nomask"]["hash"] == E["p20", "nomask"]["hash"]))
p("  p20 nomask == p21 nomask (#21 시제품, rails 포함 전체): %s" % (E["p20", "nomask"]["hash"] == E["p21", "nomask"]["hash"]))
p("  p21 masked.rails (9회로) == p20 masked.rails: %s" % all(E["p21", "mask"]["circuits"][n]["masked"] == E["p20", "mask"]["circuits"][n]["masked"] for n in E["p20", "mask"]["circuits"]))
p("== E-INST (e_inst_p3.py; p1 = B26-1 시제품, p21 = #21 시제품)")
fh = lambda n: hashlib.sha256(re.sub(rb"C:[\\/]g148[\\/](p1|p21)", b"<ROOT>", re.sub(rb"elapsed=[0-9.]+s", b"elapsed=<T>s", open(os.path.join(O, n), "rb").read()))).hexdigest() if os.path.exists(os.path.join(O, n)) else None  # 경과 시간과 트리 루트 이름만 가림
for c in ("folded_cascode", "current_reuse_telescopic_ota"):
    a, b = "einst_p1_%s.json" % c, "einst_p21_%s.json" % c
    if not (os.path.exists(os.path.join(O, a)) and os.path.exists(os.path.join(O, b))):
        p("  %s: 출력 없음" % c); continue
    A, B = ld(a), ld(b)
    rv = ld(b + ".rv_calls.json")
    diffk = sorted(k for k in set(A["field_sha256"]) | set(B["field_sha256"]) if A["field_sha256"].get(k) != B["field_sha256"].get(k))
    p("  %s: exists %s/%s fail_in_stdout %s/%s raw %s/%s 같음=%s file_bytes 같음=%s 다른 최상위 키=%s top_keys=%s" % (
        c, A["exists"], B["exists"], A["fail_in_stdout"], B["fail_in_stdout"], A["raw_sha256"][:12], B["raw_sha256"][:12],
        A["raw_sha256"] == B["raw_sha256"], A["file_bytes_sha256"] == B["file_bytes_sha256"], diffk, B["top_keys_in_file_order"]))
    p("     stdout(경과 시간 가림) 같음=%s ; p21 RailVoltages 읽기 계수 %s (rc %s)" % (fh(a + ".stdout.txt") == fh(b + ".stdout.txt"), rv["rv_calls"], rv["rc"]))
open(os.path.join(O, "compare.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
