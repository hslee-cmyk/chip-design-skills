"""backfill card -- library 회로에서 수정 후보가 `interdig_ok`를 바꾸는지(DEC-40 입력) 계측.

사본 하나(<root> = git archive 트리)에서 실행한다. sizing_recipe.run_matching_safety_with_finger_growth를 감싸
호출마다 다음을 기록한다(엔진 동작은 바꾸지 않는다 -- 반환값을 읽기만 한다):
  * relaxed_pairs 항목마다 (pair, 반환 interdig_ok, 같은 반환 audit의 `3b.…[a/b]` 체크 ok 목록)
  * mismatch = 반환 interdig_ok가 반환 audit 3b와 다른 항목 수(base 사본에서 이 수 = 수정이 값을 바꾸는 항목 수)
  * core_sha = 반환에서 interdig_ok만 뺀 핵심(rows 키·소자 이름·n_fingers·stack_id, audit 체크 이름·ok,
    unresolved_pair·reason, growth_rounds 길이, relaxed_pairs의 pair·reason·trim_recommended) sha256 -- 계약 2 대조용
모드:
  einst <circuit>  : workspaces/run_harness.py를 exec하고 run(<circuit>) (E-INST와 같은 진입, 산출 instance.json sha256 기록)
  elib             : library/*.topology.json(_TEMPLATE 제외) 9회로 -- load_topology 성공 여부와 run_harness.SPECS 등록 여부.
                     이 함수의 엔진 안 유일한 호출부는 optimize_full_circuit_budget(spec 필요)이라 SPECS에 없는 회로는
                     호출 경로가 없다(정적 사실 -- 동적 계측은 einst 모드가 SPECS 회로마다 한다).
사용: python -B lib_measure.py <root> einst <circuit> <out.json> | <root> elib <out.json>"""
import contextlib, glob, hashlib, json, os, sys, time, types

root = os.path.abspath(sys.argv[1])
mode = sys.argv[2]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, A)
sys.path.insert(0, os.path.join(root, "workspaces"))
import sizing_recipe as sr  # noqa: E402
import stick_diagram as sd  # noqa: E402
for m in (sr, sd):
    assert os.path.normcase(os.path.abspath(m.__file__)).startswith(os.path.normcase(A)), m.__file__

CALLS = []
_orig = sr.run_matching_safety_with_finger_growth


def _h(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=repr).encode("utf-8")).hexdigest()


def _wrap(*a, **k):
    res = _orig(*a, **k)
    checks = list(res["audit"].checks)
    ents = []
    mism = 0
    for e in res["relaxed_pairs"]:
        x, y = e["pair"]
        c3b = [c.ok for c in checks if c.name.startswith("3b.") and f"[{x}/{y}]" in c.name]
        bad = not (len(c3b) == 1 and e["interdig_ok"] is c3b[0])
        mism += bad
        ents.append({"pair": list(e["pair"]), "interdig_ok": e["interdig_ok"], "audit_3b": c3b, "mismatch": bad})
    core = {"rows": {k2: [[t.name, t.n_fingers, t.stack_id] for t in v] for k2, v in res["rows"].items()},
            "audit": [[c.name, c.ok] for c in checks], "audit_ok": res["audit"].ok,
            "unresolved_pair": res["unresolved_pair"], "unresolved_reason": res["unresolved_reason"],
            "growth_rounds": len(res["growth_rounds"]),
            "relaxed": [[list(e["pair"]), e["reason"], e["trim_recommended"]] for e in res["relaxed_pairs"]]}
    CALLS.append({"relaxed": ents, "mismatch": mism, "unresolved_reason": res["unresolved_reason"], "core_sha": _h(core)})
    return res


sr.run_matching_safety_with_finger_growth = _wrap


def summary():
    return {"calls": len(CALLS), "calls_with_relaxed": sum(1 for c in CALLS if c["relaxed"]),
            "relaxed_entries": sum(len(c["relaxed"]) for c in CALLS),
            "mismatch_entries": sum(c["mismatch"] for c in CALLS),
            "interdig_values": sorted({repr(e["interdig_ok"]) for c in CALLS for e in c["relaxed"]}),
            "core_seq_sha": _h([c["core_sha"] for c in CALLS]),
            "relaxed_detail": [c for c in CALLS if c["relaxed"]][:50]}


if mode == "einst":
    circuit, out = sys.argv[3], sys.argv[4]
    H = os.path.join(root, "workspaces", "run_harness.py")
    src = open(H, encoding="utf-8").read()
    mod = types.ModuleType("run_harness_bf")
    mod.__file__ = H
    t0 = time.time()
    with open(out + ".stdout.txt", "w", encoding="utf-8") as buf, contextlib.redirect_stdout(buf):
        exec(compile(src, H, "exec"), mod.__dict__)
        assert sys.modules["sizing_recipe"] is sr
        cfg = mod.SPECS[circuit]
        inst = os.path.join(mod.WORKSPACES_DIR, cfg["report_dir"], cfg["topology_file"].removesuffix(".topology.json") + ".instance.json")
        if os.path.exists(inst):
            os.remove(inst)
        mod.run(circuit)
    res = {"mode": mode, "circuit": circuit, "elapsed_s": round(time.time() - t0, 1), "instance_exists": os.path.exists(inst)}
    if res["instance_exists"]:
        obj = json.load(open(inst, encoding="utf-8"))
        res["instance_sha256"] = _h(obj)
        res["instance_has_interdig_ok"] = "interdig_ok" in open(inst, encoding="utf-8").read()
    res.update(summary())
else:
    out = sys.argv[3]
    sys.path.insert(0, os.path.join(root, "workspaces"))
    import run_harness as RH  # noqa: E402
    spec_files = {cfg["topology_file"] for cfg in RH.SPECS.values()}
    circ = {}
    for p in sorted(glob.glob(os.path.join(A, "library", "*.topology.json"))):
        name = os.path.basename(p)[:-len(".topology.json")]
        if name.startswith("_"):
            continue
        n0 = len(CALLS)
        ent = {"has_harness_spec": os.path.basename(p) in spec_files}
        try:
            trs, meta = sd.load_topology(p)
            ent["load"] = "ok"
        except Exception as e:  # 관찰 기록용
            ent["load"] = "%s" % type(e).__name__
        ent["calls_during"] = len(CALLS) - n0
        circ[name] = ent
    res = {"mode": mode, "circuits": circ}
    res.update(summary())
with open(out, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "relaxed_detail"}, ensure_ascii=False))
