# -*- coding: utf-8 -*-
"""A3-5 N4-3: 기준선 넷리스트 + 선언 변환 -> 정규화 -> 새 넷리스트와 줄 집합 차이. 변환 값은 기술자 선언(u, parallel_multiplier.to)과
calibration.json affects/power 에서만 읽는다(어댑터 산출 넷리스트에서 베끼지 않는다). 형태 선택(지시 줄 직접)만 어댑터 산출물에서 읽는다.
정규화 규칙(선언과 무관한 표기만): (N1) 머리 주석 줄 제거 (N2) 줄 순서 무시(집합) (N3) 공백 하나로 (N4) 숫자 토큰 = float 재표기 .10g (N5) 소문자 안 접음.
.control 은 분석 순서 상태 기계로 비교한다: (op, 인쇄 집합) / (ac 인자, 분석 시점 acmag 상태, 출력식).
사용: a3_n43.py <iso_root> <baseline_files> <run_dir> <out.json>
"""
import glob, json, os, re, sys

ISO, BL, RUN, OUT = sys.argv[1:5]
O = os.path.join(ISO, "skills/analog-gmid-design/tools/spice_oracle")
sys.path.insert(0, O)
os.environ.setdefault("X", "1")
from core.descriptor import load_descriptor  # noqa: E402  (u 와 to 를 원본에서 풀 때만 쓴다: 값은 엔진 선언)

D = load_descriptor(os.path.join(O, "descriptors/sky130.oracle_descriptor.json"), env=os.environ)
CAL = json.load(open(os.path.join(O, "adapters/ngspice/calibration.json"), encoding="utf-8"))["global_geometry_directive"]
PW = {"l": CAL["power"]["Mos.L"], "w": CAL["power"]["Mos.finger_w"], "ad": CAL["power"]["Mos.diffusion.ad"], "as": CAL["power"]["Mos.diffusion.as_"],
      "pd": CAL["power"]["Mos.diffusion.pd"], "ps": CAL["power"]["Mos.diffusion.ps"]}
U = {k: D.quantity(v["geometry_unit"]["source"]) for k, v in D.doc["kinds"].items()}
TO = {}
NAME = {}
for k, v in D.doc["kinds"].items():
    NAME[D.text(v["name"])] = k
    TO[k] = [t.get("name", {}).get("value") if t["target"] == "model_param" else None for t in v["parallel_multiplier"]["to"]]


def num(t):
    try:
        return format(float(t), ".10g")
    except ValueError:
        return t


def norm_tok(ln):
    out = []
    for t in ln.split():
        if "=" in t and not t.startswith(".") and not t.startswith("@"):
            k, v = t.split("=", 1)
            out.append(f"{k}={num(v)}")
        else:
            out.append(num(t))
    return " ".join(out)


def transform(ln):
    toks = ln.split()
    if toks[0][0] in "Xx" and len(toks) > 5 and toks[5] in NAME:
        kind = NAME[toks[5]]
        out = toks[:6]
        kv = dict(t.split("=", 1) for t in toks[6:])
        m = kv.pop("m")
        u = U[kind]
        for k in ("l", "w"):
            out.append(f"{k}={float(kv.pop(k)) / (u ** PW[k]):.10g}")
        for tn in TO[kind]:
            out.append(f"m={m}" if tn is None else f"{tn}={m}")
        for k in ("ad", "as", "pd", "ps"):
            if k in kv:
                out.append(f"{k}={float(kv.pop(k)) / (u ** PW[k]):.10g}")
        assert not kv, kv
        return " ".join(out)
    return ln


def split(path):
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    head, ctrl, in_c = [], [], False
    for ln in lines[1:]:
        if ln.strip().lower() == ".control":
            in_c = True
            continue
        if ln.strip().lower() in (".endc", ".end"):
            in_c = False
            continue
        (ctrl if in_c else head).append(ln)
    return head, ctrl


def ctrl_seq(ctrl, source_acmag):
    """분석 순서 -> [('op', 인쇄 집합)] / [('ac', 인자, acmag 상태, 출력식 목록)]"""
    state = dict(source_acmag)
    lets, seq, cur = {}, [], None
    for ln in ctrl:
        s = ln.strip()
        if s.startswith("op"):
            cur = ("op", set())
            seq.append(cur)
        elif s.startswith("print ") and cur and cur[0] == "op":
            cur[1].add(s[6:])
        elif s.startswith("alter "):
            m = re.match(r"alter @(\S+)\[acmag\] = (\S+)", s)
            state[m.group(1)] = float(m.group(2))
        elif s.startswith("ac "):
            seq.append(("ac", norm_tok(s), {k: v for k, v in sorted(state.items()) if v != 0.0}, []))
            cur = seq[-1]
        elif s.startswith("let "):
            m = re.match(r"let (\S+) = (.*)", s)
            if cur and cur[0] == "ac":
                cur[3].append(m.group(2).replace(" ", ""))
    return seq


def acmag_of(head):
    st = {}
    for ln in head:
        t = ln.split()
        if t and t[0][0] in "VIvi":
            st[t[0].lower()] = float(t[t.index("AC") + 1]) if "AC" in t else 0.0
    return st


res = {"normalization_rules": ["N1 머리 주석 줄 제거", "N2 줄 순서 무시(집합)", "N3 공백 하나로", "N4 숫자 토큰 .10g 재표기", ".control = 분석 순서 상태 기계(op 인쇄 집합 포함 관계, ac 인자·acmag 상태·출력식 같음)"],
       "form_choice_from_adapter": "전역 지시를 넷리스트 직접 줄로 씀(include 아님)", "pairs": {}}
for rid in ("R1", "R2", "R3", "R4", "R5"):
    for old in sorted(glob.glob(os.path.join(BL, rid, "o", "*.cir"))):
        b = os.path.basename(old)
        if any(x in b for x in (".pz.", ".stab.", ".stabop.")):
            continue
        stem = b[:-4]
        new = os.path.join(RUN, rid, "o", stem, "bench.cir")
        ho, co = split(old)
        hn, cn = split(new)
        u = next(iter(U.values()))
        conv = [transform(x) for x in ho] + [f".option scale={u:.10g}"]
        so, sn = {norm_tok(x) for x in conv}, {norm_tok(x) for x in hn}
        sqo, sqn = ctrl_seq(co, acmag_of(ho)), ctrl_seq(cn, acmag_of(hn))
        ctrl_diff = []
        if [x[0] for x in sqo] != [x[0] for x in sqn]:
            ctrl_diff.append({"order": [[x[0] for x in sqo], [x[0] for x in sqn]]})
        for i, (a, c) in enumerate(zip(sqo, sqn)):
            if a[0] == "op":
                if not a[1] <= c[1]:
                    ctrl_diff.append({"i": i, "missing_prints": sorted(a[1] - c[1])})
            elif a[1:] != c[1:]:
                ctrl_diff.append({"i": i, "old": [a[1], a[2], a[3]], "new": [c[1], c[2], c[3]]})
        res["pairs"][f"{rid}/{stem}"] = {"only_old": sorted(so - sn), "only_new": sorted(sn - so), "control_diffs": ctrl_diff,
                                         "n_old": len(so), "n_new": len(sn), "analyses": len(sqo),
                                         "extra_prints": sorted(sqn[0][1] - sqo[0][1]) if sqo and sqo[0][0] == "op" and sqn and sqn[0][0] == "op" else []}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1, default=str)
for k, v in res["pairs"].items():
    print(k, "n", v["n_old"], v["n_new"], "analyses", v["analyses"], "ctrl", len(v["control_diffs"]))
    for x in v["only_old"]:
        print("   -", x)
    for x in v["only_new"]:
        print("   +", x)
    for x in v["control_diffs"]:
        print("   c", str(x)[:400])
