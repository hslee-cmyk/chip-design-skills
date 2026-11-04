# -*- coding: utf-8 -*-
"""A3-5 확장(원인 규명, 시뮬레이터 호출 0): OP-1 기준선의 옛 넷리스트(.cir/.loop.cir/.cmloop.cir)마다 같은 폴더 입력을 변환해 새 IR·render 넷리스트를 만들고
소자·수동·원천 줄을 N4-3 과 같은 선언 변환 뒤 줄 집합으로 비교한다. 잔차를 줄 종류별로 센다. 사용: a3_5b.py <iso_v> <out.json>"""
import collections, copy, glob, json, os, re, sys

ISO, OUT = sys.argv[1:3]
O = os.path.join(ISO, "skills/analog-gmid-design/tools/spice_oracle")
FILES = os.path.join(ISO, ".ai/verification/20261016-op1-baseline/baseline/files")
sys.path.insert(0, O)
sys.path.insert(0, os.path.join(ISO, ".ai/verification/20261104-op1b/scripts"))
import op1b_lib as L  # noqa: E402
from adapters.ngspice import dialect  # noqa: E402
from core.build_benches import cm_loop_bench, iso_bench, loop_bench, main_requests  # noqa: E402
from core.build_circuit import circuit_ir  # noqa: E402
from core.descriptor import load_descriptor  # noqa: E402
from core.requests import Condition  # noqa: E402

D = load_descriptor(os.path.join(O, "descriptors/sky130.oracle_descriptor.json"), env=os.environ)
COND = Condition(temp_c=27.0, corner="tt")
TOKN = re.compile(r"[-+]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:e[-+]?[0-9]+)?$", re.I)


def elems(text):
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.lower() == ".control":
            break
        if not s or s[0] in "*.":
            if s.lower().startswith(".nodeset"):
                out.append(" ".join(s.split()))
            continue
        out.append(s)
    return out


def norm(ln, old):
    toks = ln.split()
    if toks[0][0] in "Xx" and len(toks) > 6 and "=" in toks[6]:
        kv = dict(t.split("=", 1) for t in toks[6:])
        pw = {"l": 1, "w": 1, "ad": 2, "as": 2, "pd": 1, "ps": 1}
        if old:
            kv = {k: (float(v) / (1e-6 ** pw[k]) if k in pw else float(v)) for k, v in kv.items()}
            kv["mult"] = kv["m"]
        else:
            kv = {k: float(v) for k, v in kv.items()}
        return " ".join(toks[:6]) + " " + " ".join(f"{k}={kv[k]:.8g}" for k in sorted(kv))
    return " ".join(format(float(t), ".8g") if TOKN.fullmatch(t) else t for t in toks)


cirs = sorted(glob.glob(FILES + "/pytest/tmp/**/*.cir", recursive=True))
res = collections.Counter()
kinds = collections.Counter()
examples = collections.defaultdict(list)
per = []
for c in cirs:
    b = os.path.basename(c)
    if any(x in b for x in (".pz.", ".stab.", ".stabop.", ".mc.", ".noise", ".swing", "openloop")):
        res["skip_other_bench"] += 1
        continue
    m = re.match(r"(.+)\.(free|forced|iso)(\.loop|\.cmloop)?\.cir$", b)
    if not m:
        res["skip_name"] += 1
        continue
    stem, bias, sub = m.group(1), m.group(2), m.group(3)
    d = os.path.dirname(c)
    ips = [p for p in glob.glob(os.path.join(d, "*.json")) if p.endswith("input.json")] + glob.glob(os.path.join(os.path.dirname(d), "*input.json"))
    if not ips:
        res["skip_no_input"] += 1
        continue
    try:
        old = json.load(open(ips[0], encoding="utf-8"))
        meta_p = c + ".meta.json"
        z1 = None
        if os.path.exists(c[:-len(sub or "") - 4] + ".cir.meta.json"):
            mj = json.load(open(c[:-len(sub or "") - 4] + ".cir.meta.json", encoding="utf-8"))
            z1 = mj.get("z1")
        omit, short = (z1 or {}).get("omit") or (), (z1 or {}).get("short") or ()
        old2 = L.rewrite_lut_ref(old, "x")
        new, _ = L.convert_input(old2, lut_files=[{"path": "x", "sha256": "0" * 64, "kinds": {}}], descriptor={"path": "x", "sha256": "0" * 64}, adapter="ngspice", exe="x")
        if bias == "iso":
            circuit, reqs, _ = iso_bench(new, COND, D)
        elif sub == ".loop":
            circuit, reqs, _ = loop_bench(new, bias, COND, omit, short, D)
        elif sub == ".cmloop":
            circuit, reqs, _ = cm_loop_bench(new, bias, COND, omit, short, D)
        else:
            circuit, _ = circuit_ir(new, bias, omit, short, descriptor=D)
            reqs = main_requests(new, bias, circuit, cond=COND)
        text, _ = dialect.render(circuit, reqs, D, COND, (new.get("simulator") or {}).get("options"))
    except L.Op1bStop as e:
        res["skip_convert:" + str(e.reason)] += 1
        continue
    except Exception as e:
        res["exc:" + type(e).__name__] += 1
        examples["exc"].append((os.path.relpath(c, FILES), str(e)[:160]))
        continue
    so = {norm(x, True) for x in elems(open(c, encoding="utf-8", errors="replace").read())}
    sn = {norm(x, False) for x in elems(text)}
    oo, on = sorted(so - sn), sorted(sn - so)
    res["compared"] += 1
    if not oo and not on:
        res["identical"] += 1
        continue
    res["residual"] += 1
    ks = set()
    for side, lst in (("-", oo), ("+", on)):
        for ln in lst:
            head = re.match(r"[A-Za-z]+_?", ln).group(0)
            k = side + head
            ks.add(k)
            kinds[(sub or "main", bias, k)] += 1
            if len(examples[k]) < 3:
                examples[k].append((os.path.relpath(c, FILES).replace("\\", "/"), ln[:120]))
    per.append({"cir": os.path.relpath(c, FILES).replace("\\", "/"), "only_old": oo[:12], "only_new": on[:12]})
out = {"counts": dict(res), "residual_kinds": {str(k): v for k, v in kinds.most_common()}, "examples": {k: v for k, v in examples.items()}, "per_first_60": per[:60], "n_per": len(per)}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ("counts", "residual_kinds")}, ensure_ascii=False, indent=0))
for k, v in examples.items():
    print(k, str(v)[:400])
