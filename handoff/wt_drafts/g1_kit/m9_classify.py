"""모의 M card 쌍(p3v6_order_shim_sim.py 상태)의 G1 시제품 거부를 원인별로 나눈다(측정 전용, 읽기 전용).

    python -B m9_classify.py <원본 복제본(C:/g143/b)> <시제품 복제본(C:/g143/p)> <order sim WORK> <출력 json>

원인: future(원본·목적 __future__ 집합 다름), multi(목적 파일이 같은 이름을 두 번 이상 묶음 -- 모의 생성기가 원본 파일들의 import 줄을 그대로 모아서 생김),
      cascade(함께 옮긴 단위가 거부돼 그것에 기대던 단위도 M-4), other.
두 판으로 잰다: raw = 모의 상태 그대로, dedup = 목적(MOD) 파일의 `from M import …` 줄에서 이미 묶인 이름을 빼고(이름마다 import 한 번 -- D0a 생성기가 지킬 수 있는 제약)
같은 쌍을 다시 잰다. future 차이는 손대지 않는다(원본 파일의 future가 다르면 고칠 수 없는 조합).
"""
import ast
import json
import os
import sys

BASE_CLONE, PROTO_CLONE, SIMW, OUT = sys.argv[1:5]
AS = "skills/analog-gmid-design/assets/"
sys.path.insert(0, os.path.join(PROTO_CLONE, "tools", "gates"))
import reachability as g1  # noqa: E402  (시제품)

base0 = {k: v for k, v in g1.read_tree(BASE_CLONE, "HEAD", g1.SOURCE_GLOBS).items() if g1._is_source(k)}
MODS = set()


def state(d):
    cur = dict(base0)
    for f in os.listdir(d):
        if f.endswith(".py"):
            with open(os.path.join(d, f), encoding="utf-8", newline="") as fh:
                cur[AS + f] = fh.read().replace("\r\n", "\n")
            if f not in {p[len(AS):] for p in base0}:
                MODS.add(AS + f)
    return cur


def dedup(files):
    out = dict(files)
    for p in MODS:
        if p not in out:
            continue
        lines = out[p].split("\n")
        tree = ast.parse(out[p])
        seen = set()
        drop, repl = set(), {}
        for n in tree.body:
            if isinstance(n, ast.ImportFrom) and n.module != "__future__":
                keep = [a for a in n.names if (a.asname or a.name) not in seen]
                seen |= {a.asname or a.name for a in n.names}
                if len(keep) != len(n.names):
                    for ln in range(n.lineno, n.end_lineno + 1):
                        drop.add(ln)
                    if keep:
                        repl[n.lineno] = "from %s%s import %s" % ("." * n.level, n.module or "",
                                                                  ", ".join(a.name + (" as " + a.asname if a.asname else "") for a in keep))
            elif isinstance(n, ast.Import):
                seen |= {a.asname or a.name.split(".")[0] for a in n.names}
        new = []
        for i, ln in enumerate(lines, 1):
            if i in repl:
                new.append(repl[i])
            elif i not in drop:
                new.append(ln)
        out[p] = "\n".join(new)
    return out


def classify(mv):
    c = {"future": 0, "multi": 0, "cascade": 0, "other": 0}
    ex = {}
    for k, v in mv["rejected"].items():
        d = v["detail"]
        if v["rule"] == "M-4" and d and d[0] == "__future__":
            kind = "future"
        elif any("'multi'" in x for x in d):
            kind = "multi"
        elif v["rule"] == "M-4" and len(d) == 3 and d[1].startswith("('def'") and d[2].startswith("('def'"):
            kind = "cascade"
        else:
            kind = "other"
        c[kind] += 1
        ex.setdefault(kind, []).append([k.split("/")[-1], v["rule"]] + [x[:120] for x in d])
    return c, {k: v[:50] for k, v in ex.items()}


states = sorted((d for d in os.listdir(SIMW) if d.startswith("state_M")), key=lambda d: int(d[7:]))
res = []
prev = base0
prev_d = base0
for d in states:
    cur = state(os.path.join(SIMW, d))
    rec = {"card": d}
    for lab, (b, h) in (("raw", (prev, cur)), ("dedup", (prev_d, dedup(cur)))):
        mv = g1.moved_defs(b, h)
        c, ex = classify(mv)
        rec[lab] = {"units": len(mv["units"]), "defs": len(mv["defs"]), "rejected": len(mv["rejected"]), "by_cause": c, "examples": ex}
    res.append(rec)
    print(json.dumps({"card": d, "raw": {k: rec["raw"][k] for k in ("units", "defs", "rejected", "by_cause")},
                      "dedup": {k: rec["dedup"][k] for k in ("units", "defs", "rejected", "by_cause")}}, ensure_ascii=False), flush=True)
    prev, prev_d = cur, dedup(cur)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
