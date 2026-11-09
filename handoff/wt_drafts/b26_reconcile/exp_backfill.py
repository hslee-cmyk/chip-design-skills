"""run_matching_safety_with_finger_growth의 _backfill_interdig_ok 삭제 변이(루프 안 SR 11800 = head 11809, 루프 뒤 SR 11879 = head 11888)
구별 입력 탐색 -- b1 원본과 변이 2종을 같은 무작위 합성 입력으로 돌려 반환값(relaxed_pairs·unresolved·행·audit)을 비교한다.
출력: C:/g103/out/exp_backfill.txt (요약 + 처음 찾은 구별 입력)
사용: python -B exp_backfill.py <N> <seed>
"""
import importlib.util, json, random, sys, traceback

B1 = "C:/g103/b1/skills/analog-gmid-design/assets/"
sys.path.insert(0, B1)
import sizing_recipe as sr0  # noqa: E402

src = open(B1 + "sizing_recipe.py", encoding="utf-8").read()
IN_LOOP = "        _backfill_interdig_ok(result)\n        if result.ok:\n"
AFTER = "    _backfill_interdig_ok(result)\n    current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)\n    return {\"rows\": current_rows, \"audit\": result, \"ctx\": cur_ctx, \"growth_rounds\": growth_rounds,\n"
assert src.count(IN_LOOP) == 1 and src.count(AFTER) == 1
VAR = {"loop_del": src.replace(IN_LOOP, "        pass\n        if result.ok:\n"),
       "after_del": src.replace(AFTER, AFTER.replace("    _backfill_interdig_ok(result)\n", "    pass\n", 1))}


def load(tag, s):
    spec = importlib.util.spec_from_loader("sr_" + tag, loader=None)
    m = importlib.util.module_from_spec(spec)
    m.__file__ = B1 + "sizing_recipe.py"
    sys.modules[spec.name] = m
    exec(compile(s, B1 + "sizing_recipe.py", "exec"), m.__dict__)
    return m


MODS = {"orig": sr0}
MODS.update({k: load(k, v) for k, v in VAR.items()})
LUT = sr0.build_toy_lut()
T = sr0.Transistor


def summary(res):
    if isinstance(res, Exception):
        return "EXC " + type(res).__name__
    rows = {k: [(t.name, t.n_fingers) for t in v] for k, v in res["rows"].items()}
    return json.dumps(dict(rp=[(list(e["pair"]), e["reason"], e["interdig_ok"]) for e in res["relaxed_pairs"]],
                           up=res["unresolved_pair"], ur=res["unresolved_reason"], rows=rows,
                           audit=[(c.name, c.ok) for c in res["audit"].checks],
                           gr=[(g["round"], list(g["names"])) for g in res["growth_rounds"]]), sort_keys=True, default=str)


def case(rng):
    r = sr0.size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=LUT, vds=0.6)
    W0 = r.W
    S = {"ID": r.ID, "W": W0, "L": 0.5e-6, "gm": r.gm, "gm_id": 12.0,
         "gds": r.gm / LUT.gm_gds_ratio(12.0, 0.5e-6, 0.6, 0.0), "kind": "nmos", "vds": 0.6, "vsb": 0.0}
    nets = ["vtail", "n1", "n2", "n3", "n4", "gnd"]
    npairs = rng.choice([1, 2, 2, 3])
    devs, pairs, sens = [], [], {}
    for p in range(npairs):
        a, b = "Ma%d" % p, "Mb%d" % p
        src_ = rng.choice(["vtail", "n1"])
        devs.append((a, src_, "da%d" % p, "ga%d" % p))
        devs.append((b, src_, "db%d" % p, "gb%d" % p))
        pairs.append((a, b))
        sens[(a, b)] = rng.choice(["offset", "offset", "ratio"])
    for k in range(rng.choice([0, 1, 2, 3])):
        devs.append(("Mx%d" % k, rng.choice(nets), rng.choice(nets + ["da0", "db0"]), "gx%d" % k))
    nrows = rng.choice([1, 1, 2])
    rows = {}
    for (n, s, d, g) in devs:
        rn = "row%d" % rng.randrange(nrows)
        nf = rng.choice([1, 1, 2])
        rows.setdefault(rn, []).append(T(n, "nmos", source=s, drain=d, gate=g, n_fingers=nf, finger_w=W0 / nf, stack_id=rn))
    names = [d[0] for d in devs]
    sized = {n: dict(S) for n in names}
    for p in range(npairs):   # 쌍마다 다른 gm/ID -- 한 쌍만 gm/ID 위반(완화)되고 다른 쌍은 성장하는 경우를 만든다
        g = rng.choice([6.0, 9.0, 12.0])
        rp = sr0.size_transistor(gm=200e-6, gm_id=g, L=0.5e-6, lut=LUT, vds=0.6)
        e = {"ID": rp.ID, "W": rp.W, "L": 0.5e-6, "gm": rp.gm, "gm_id": g,
             "gds": rp.gm / LUT.gm_gds_ratio(g, 0.5e-6, 0.6, 0.0), "kind": "nmos", "vds": 0.6, "vsb": 0.0}
        sized["Ma%d" % p] = dict(e)
        sized["Mb%d" % p] = dict(e)
    ctx = sr0.SizingContext(sized=sized, topology_path=None)
    hi = rng.choice([13.0, 14.0, 16.0, 20.0, 28.0])
    mx = rng.choice([0, 1, 2, 3, 5])
    metrics = {"area": {"type": "sum_area", "devices": names}}
    cons = [{"metric": "area", "op": "<=", "value": len(names) * W0 * 0.5e-6 * rng.choice([1.5, 3.0, 10.0])}]
    return rows, pairs, sens, ctx, metrics, cons, hi, mx


def run(m, args):
    rows, pairs, sens, ctx, metrics, cons, hi, mx = args
    try:
        return m.run_matching_safety_with_finger_growth(
            {k: list(v) for k, v in rows.items()}, pairs, sens, ctx, {"nmos": LUT}, metrics, cons,
            gm_id_bounds=(2.0, hi), max_rounds=mx)
    except Exception as e:  # noqa: BLE001 -- 예외도 비교 대상
        return e


def main(n, seed):
    rng = random.Random(seed)
    out = open("C:/g103/out/exp_backfill_%d.txt" % seed, "w", encoding="utf-8")
    stats = {"cases": 0, "exc": 0, "relaxed": 0, "diff_loop_del": 0, "diff_after_del": 0}
    for i in range(n):
        args = case(rng)
        base = summary(run(MODS["orig"], args))
        stats["cases"] += 1
        stats["exc"] += base.startswith("EXC")
        stats["relaxed"] += ('"rp": [[' in base)
        if '"rp": [[' in base:
            b = json.loads(base)
            rr = [g[0] for g in b["gr"]]
            # 완화 뒤에도 다른 쌍의 성장 라운드가 이어진 경우(루프 안 backfill과 최종 backfill 사이에 행이 바뀔 수 있는 경우)
            stats["relaxed_then_more_growth"] = stats.get("relaxed_then_more_growth", 0) + (len(set(rr)) >= 2)
            # 최종 행에 euler 정리(분할) 흔적이 있는 경우
            stats["relaxed_with_fixup"] = stats.get("relaxed_with_fixup", 0) + any(("_seg" in k or "_comp" in k) for k in b["rows"])
            stats["relaxed_interdig_false"] = stats.get("relaxed_interdig_false", 0) + any(e[2] is False for e in b["rp"])
        for k in VAR:
            s = summary(run(MODS[k], args))
            if s != base:
                stats["diff_" + k] += 1
                if stats["diff_" + k] <= 3:
                    rows, pairs, sens, ctx, metrics, cons, hi, mx = args
                    out.write("DIFF %s case %d\n rows=%s\n pairs=%s sens=%s hi=%s max_rounds=%s\n orig=%s\n mut =%s\n" % (
                        k, i, {r: [(t.name, t.source, t.drain, t.n_fingers) for t in v] for r, v in rows.items()},
                        pairs, sens, hi, mx, base, s))
                    out.flush()
    out.write("STATS %s\n" % json.dumps(stats))
    out.close()
    print(stats)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
