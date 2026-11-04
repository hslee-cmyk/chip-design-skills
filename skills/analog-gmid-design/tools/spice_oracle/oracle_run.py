# -*- coding: utf-8 -*-
"""oracle_run.py -- SPICE 오라클 진입점(CLI) (design §3.1·§11.7, card 20261104-op23).

    python oracle_run.py <oracle_input.json> <out_dir> --bias free [forced] [iso]
                         [--simulator 이름] [--sim-exe 경로] [--judge judge.json] [--sat-margin-v V] [--timeout-s S] [--tag TAG]
                         [--topology T] [--require-topology] [--omit N ...] [--short N ...] [--cache-dir D]

흐름: 입력 검사(1a~1e) -> 기술자 읽기(2) -> LUT 파일 읽기(2b) -> bias 마다 IR·요청 만들기 -> 실행 전 검사(3~9) -> 어댑터 실행 -> 코어 측정 조립 ->
판정(core.compare) -> 출력. 반환 코드: 0 = 모든 bias 판정 PASS/INCOMPLETE, 1 = FAIL, 2 = BLOCKED 또는 거부. 거부(§7 코드)면 `<circuit>.reject.json`
하나만 쓴다(§11.7). 엔진을 import하지 않는다. 시뮬레이터 이름·방언은 어댑터 패키지만 안다(`--simulator` 가 고른다).

기간 동작(D-1): noise·swing_icmr 입력은 adapter_capability_missing, offset_mc 입력은 mc_method_unsupported(side = descriptor)로 거부하고,
PM 은 stability_unverified 로 둔다(OP-4·OP-5 가 오기 전까지).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import compare as cmp                                              # noqa: E402
from core.build_benches import cm_loop_bench, iso_bench, loop_bench, main_requests    # noqa: E402
from core.build_circuit import BIASES, circuit_ir, fold_collisions           # noqa: E402
from core.bundle import check_bundle, check_provenance, check_record_root    # noqa: E402
from core.descriptor import load_descriptor                                  # noqa: E402
from core.identity import topology_identity                                  # noqa: E402
from core.input_check import check_input_cross, read_lut_files               # noqa: E402
from core.ir import Circuit                                                  # noqa: E402
from core.measures_ac import build_sim                                       # noqa: E402
from core.requests import Condition                                          # noqa: E402
from core.results import OracleError, canonical_sha256                       # noqa: E402

OLD_PROCESS_MARKERS = ("models", "ngspice_exe", "lut_npz", "diffusion")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oracle_input.schema.json")
CIRCUIT_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")
VERDICT_RC = {"PASS": 0, "INCOMPLETE": 0, "FAIL": 1, "BLOCKED": 2}


# ---------------------------------------------------------------- 입력 검사 1a~1c
def _json_default(o):
    import numpy as np
    if isinstance(o, np.generic):
        return o.item()
    raise TypeError(f"JSON 으로 쓸 수 없는 값: {type(o).__name__}")


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1, default=_json_default)


def schema_errors(inp) -> list:
    """JSON Schema(Draft 2020-12) 위반 전부 [{pointer, rule}] -- pointer 는 문제 키 자체, 정렬 (pointer, rule), 중복 하나."""
    import jsonschema
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    out = set()
    for e in jsonschema.Draft202012Validator(schema).iter_errors(inp):
        base = "".join("/" + str(x) for x in e.absolute_path)
        if e.validator == "required":
            for k in e.validator_value:
                if k not in e.instance:
                    out.add((f"{base}/{k}", "required"))
        elif e.validator == "additionalProperties":
            props = set((e.schema.get("properties") or {}))
            for k in e.instance:
                if k not in props:
                    out.add((f"{base}/{k}", "additionalProperties"))
        else:
            out.add((base, e.validator))
    return [{"pointer": p, "rule": r} for p, r in sorted(out)]


def old_markers(inp) -> list:
    m = ["schema"] if inp.get("schema") == "spice_oracle_input/1" else []
    proc, tb = inp.get("process"), inp.get("testbench")
    if isinstance(proc, dict):
        m += [f"process.{x}" for x in OLD_PROCESS_MARKERS if x in proc]
    if isinstance(tb, dict) and "options" in tb:
        m.append("testbench.options")
    return m


# ---------------------------------------------------------------- 거부 기록
def write_reject(out_dir, circuit, err, input_path, raw) -> int:
    name = circuit if isinstance(circuit, str) and CIRCUIT_RE.match(circuit) else "circuit"
    os.makedirs(out_dir, exist_ok=True)
    rec = {"schema": "oracle_reject/1", "code": err.code, "detail": err.detail, "stage": err.stage,
           "input_path": os.path.abspath(input_path), "input_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None}
    with open(os.path.join(out_dir, f"{name}.reject.json"), "w", encoding="utf-8") as f:
        f.write(dumps(rec))
    print(f"REJECT {err.code} (stage {err.stage})")
    return 2


# ---------------------------------------------------------------- topology 경로(옛 규칙 그대로: 저장소 루트 기준)
def repo_root(start):
    d = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up


def resolve_topology_path(inp, input_path=None, override=None):
    if override:
        return os.path.abspath(override)
    p = (inp.get("topology") or {}).get("path")
    if not p:
        return None
    if os.path.isabs(p):
        return os.path.abspath(p)
    root = (repo_root(os.path.dirname(os.path.abspath(input_path))) if input_path else None) \
        or repo_root(os.path.dirname(os.path.abspath(__file__)))
    return None if root is None else os.path.abspath(os.path.join(root, *p.split("/")))


def topology_check(circuit, inp, path, required):
    """C15: topology JSON 읽기(파일 sha256 기록) + core.identity 대조. mismatch 이거나 (미검증 + required)이면 막힘 문장을 함께 돌려준다."""
    res = {"status": "unverified", "topology_path": path, "sha256_actual": None, "sha256_declared": (inp.get("topology") or {}).get("sha256"),
           "diffs": [], "compared": 0, "excluded_testbench": [], "declared_not_in_topology": {}, "bulk_compared": [], "notes": [],
           "required": bool(required)}
    blockers = []
    if not path:
        res["notes"].append("topology 미지정(입력 topology.path 도 --topology 도 없음) -- 연결 동일성 미검증")
    elif not os.path.exists(path):
        res["notes"].append(f"topology 파일 없음: {path} -- 연결 동일성 미검증")
    else:
        with open(path, "rb") as f:
            raw = f.read()
        res["sha256_actual"] = hashlib.sha256(raw).hexdigest()
        if res["sha256_declared"] and res["sha256_declared"] != res["sha256_actual"]:
            res["notes"].append(f"topology 파일 sha256 이 입력 선언값과 다르다(입력 변환 뒤 파일이 바뀜): "
                                f"선언 {res['sha256_declared'][:12]}.. 실제 {res['sha256_actual'][:12]}..")
        try:
            topo = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            res["status"] = "mismatch"
            res["diffs"].append(f"topology JSON 을 읽을 수 없다: {e}")
        else:
            res.update(topology_identity(circuit, topo))
    if res["status"] == "mismatch":
        blockers.append(f"C15 topology 연결 동일성 불일치 {len(res['diffs'])}건: " + "; ".join(res["diffs"][:8]))
    elif res["status"] == "unverified" and required:
        blockers.append("C15 topology 연결 동일성 미검증(--require-topology): " + "; ".join(res["notes"]))
    return res, blockers


# ---------------------------------------------------------------- 어댑터 선택(1e)
def pick_adapter(inp, a, adapters):
    name = a.simulator or inp["simulator"]["adapter"]
    known = sorted(set(adapters or {}) | {"ngspice"})
    if name not in known:
        raise OracleError("adapter_unknown", {"name": name, "known": known}, "1e")
    exe = a.sim_exe or inp["simulator"].get("exe")
    if not exe or not os.path.isfile(exe):
        raise OracleError("simulator_exe_missing", {"exe": exe}, "1e")
    if adapters and name in adapters:
        return adapters[name]
    from adapters.ngspice import Adapter
    return Adapter(exe=exe, options=inp["simulator"].get("options"))


# ---------------------------------------------------------------- 실행 전 검사(3~9)
def used_kinds(inp):
    return sorted({d["kind"] for d in inp["devices"]})


def _read(p):
    try:
        with open(p, "rb") as f:
            return f.read()
    except OSError:
        return None


def check_descriptor_use(inp, desc, adapter):
    """§7.2 3~6단계: 기하 선언, 기술자 mc 방법, 어댑터 능력, 보정값·허용오차. 처음 걸린 하나만 낸다."""
    kinds = used_kinds(inp)
    for k in kinds:
        kd = desc.doc["kinds"][k]
        missing = [n for n in ("geometry_unit", "parallel_multiplier") if n not in kd]
        if missing:
            raise OracleError("descriptor_geometry_undeclared", {"kind": k, "missing": missing}, "3")
    if inp.get("offset_mc") is not None:        # 기술자에 mc 칸이 없다(OP-5 가 더한다) -- 기간 동작 D-1
        raise OracleError("mc_method_unsupported", {"side": "descriptor", "block": "offset_mc"}, "4")
    caps = adapter.capabilities()
    for block, cap in (("noise", "noise"), ("swing_icmr", "op_sweep")):
        if inp.get(block) is not None and not caps.get(cap):
            raise OracleError("adapter_capability_missing", cap, "5")
    for cap in ("op", "ac"):
        if not caps.get(cap):
            raise OracleError("adapter_capability_missing", cap, "5")
    if desc.doc["model_family"] not in (caps.get("model_families") or []):
        raise OracleError("adapter_capability_missing", "model_families", "5")
    cal = adapter.calibration()
    if any(desc.doc["kinds"][k]["geometry_unit"] != "si" for k in kinds):
        if "global_directive" not in (caps.get("geometry_unit_application") or []):
            raise OracleError("adapter_capability_missing", "geometry_unit_application", "5")
        g = cal.get("global_geometry_directive")
        if not g or not g.get("affects") or not g.get("power") or not g.get("source"):
            raise OracleError("adapter_calibration_missing", "global_geometry_directive", "6")
    declared = cal.get("default_tolerances") or {}
    opts = inp["simulator"].get("options") or {}
    need = [k for k in ("reltol", "vntol", "abstol") if k not in opts and not (declared.get(k) or {}).get("source")]
    if need or not (cal.get("data_digits") or {}).get("source"):
        raise OracleError("dc_tolerance_undeclared", {"missing": need or ["data_digits"]}, "6")


def check_bundles(inp, desc, adapter, lut, circuit, cond):
    """§7.2 8단계: LUT 기록 빈 표 -> 기록 뿌리 교차 -> 역할 적용 -> 규칙 (i)(ii) -> (iii). 반환 = 기계 의존 항목 목록."""
    kinds = used_kinds(inp)
    tables = {k: lut.tables(k) for k in kinds}
    for k in kinds:
        check_provenance(k, [(i, p, t) for i, p, t, _ in tables[k]])
    all_recs = {}
    for k in kinds:
        for _, _, t, _ in tables[k]:
            all_recs.update(t)
    mdep = list(check_record_root(all_recs, desc.engine_source_files(), lambda rel: _read(os.path.join(desc.record_root, rel))))
    for k in kinds:
        recs, roles = {}, {}
        for idx, _, t, gen in tables[k]:
            for rel, sha in t.items():
                recs[rel if recs.get(rel, sha) == sha else f"{rel}@{idx}"] = sha
            for rd in desc.roles_docs:
                if gen is not None and rd["generator_sha256"] == gen:
                    roles.update(rd["roles"])
        sub = Circuit(tuple(e for e in circuit.elements if type(e).__name__ == "Mos" and e.kind == k), {}, {})
        bundle = adapter.model_bundle(sub, desc, cond)
        texts = {p: (_read(p) or b"").decode("utf-8", errors="replace") for p in bundle}
        mdep += check_bundle(k, recs, roles, bundle, texts, desc.text(desc.doc["kinds"][k]["name"]),
                             lambda rel: _read(os.path.join(desc.record_root, rel)))
    return mdep


# ---------------------------------------------------------------- 한 bias 준비 / 실행
class Plan:
    def __init__(self, bias, stem, circuit, requests, blockers, loop=None, cm=None, ti=None):
        self.bias, self.stem, self.circuit, self.requests, self.blockers = bias, stem, circuit, requests, blockers
        self.loop, self.cm, self.ti = loop, cm, ti


def prepare(inp, bias, a, input_path, desc, cond):
    stem = f"{inp['circuit']}{('.' + a.tag) if a.tag else ''}.{bias}"
    if bias == "iso":
        circuit, reqs, bl = iso_bench(inp, cond, desc)
        ti = {"status": "not_applicable", "topology_path": None, "diffs": [], "required": bool(a.require_topology),
              "notes": ["iso 는 회로 연결이 없는 단독 소자 회로 -- C15 대상 아님"]}
        return Plan(bias, stem, circuit, reqs, list(bl), ti=ti)
    circuit, bl = circuit_ir(inp, bias, a.omit, a.short, descriptor=desc)
    reqs = main_requests(inp, bias, circuit, cond=cond)
    blockers = list(bl)
    loop = cm = None
    if inp.get("feedback_passives"):
        loop = loop_bench(inp, bias, cond, a.omit, a.short, desc)
        blockers += [b for b in loop[2] if b not in blockers]
    if inp.get("cm_output_loop"):
        cm = cm_loop_bench(inp, bias, cond, a.omit, a.short, desc)
        blockers += [b for b in cm[2] if b not in blockers]
    base = circuit if not (a.omit or a.short) else circuit_ir(inp, bias, descriptor=desc)[0]
    ti, tb = topology_check(base, inp, resolve_topology_path(inp, input_path, a.topology), a.require_topology)
    if circuit.meta.get("z1"):
        ti["notes"].append("Z1 변경 전 회로로 비교했다(제거·단락은 진단용 의도된 변경)")
    return Plan(bias, stem, circuit, reqs, blockers + tb, loop, cm, ti)


def blocked_sim(blockers):
    return {"skipped": "회로 막힘: " + " | ".join(blockers), "status": None, "method": None, "cache": {"main": None, "loop": None},
            "log_errors": [], "devices": {}, "nodes": {}, "rail_current_A": {}, "hold_current_A": {}, "op_ok": False, "ac": None,
            "loop": None, "cm_loop": None, "ratio": [], "rout": []}


def execute(plan, desc, adapter, out_dir, a):
    """어댑터로 벤치를 순차 실행해 (sim, 작업 폴더 이름 목록)을 돌려준다. 막힘이면 벤치를 실행하지 않는다."""
    if plan.blockers:
        return blocked_sim(plan.blockers), []
    names = [plan.stem]

    def go(name, circuit, reqs):
        return adapter.run(circuit, reqs, desc, os.path.join(out_dir, name), a.timeout_s, a.cache_dir, None)
    main = go(plan.stem, plan.circuit, plan.requests)
    loop = cm = None
    if plan.loop:
        names.append(plan.stem + ".loop")
        loop = go(names[-1], plan.loop[0], plan.loop[1])
    if plan.cm:
        names.append(plan.stem + ".cmloop")
        cm = go(names[-1], plan.cm[0], plan.cm[1])
    sim = build_sim(plan.circuit, main, loop, cm, plan.loop[0] if plan.loop else None, plan.cm[0] if plan.cm else None)
    for blk, b, name in ((sim, main, names[0]), (sim.get("loop"), loop, plan.stem + ".loop"), (sim.get("cm_loop"), cm, plan.stem + ".cmloop")):
        if blk and b is not None and (blk.get("status") or {}).get("log_path"):   # 출력 폴더 기준 상대 경로(출력 폴더 경로는 결과에 넣지 않는다)
            blk["status"]["log_path"] = f"{name}/{b.status.log_path}"
    return sim, names


def compare_meta(plan, lut):
    m = plan.circuit.meta
    meta = {"bias": plan.bias, "lut_meta": {"corner": lut.corner, "temp_c": lut.temp_c}, "geometry": m["geometry"], "nets": m["nets"],
            "held": m["held"], "gate_bias": m["gate_bias"], "inputs": m["inputs"], "notes": m["notes"], "blockers": list(plan.blockers),
            "z1": m.get("z1"), "topology_identity": plan.ti}
    if plan.bias == "iso":
        meta["iso_applied"], meta["iso_skipped"] = m["iso_applied"], m["iso_skipped"]
    return meta


# ---------------------------------------------------------------- main
def main(argv=None, *, adapters=None) -> int:
    ap = argparse.ArgumentParser(description="SPICE 오라클: IR -> 어댑터 -> 비교표")
    ap.add_argument("oracle_input")
    ap.add_argument("out_dir")
    ap.add_argument("--bias", nargs="+", choices=BIASES, required=True)
    ap.add_argument("--judge", default=None)
    ap.add_argument("--sat-margin-v", type=float, default=None)
    ap.add_argument("--simulator", default=None, help="어댑터 이름(입력 simulator.adapter 보다 우선)")
    ap.add_argument("--sim-exe", default=None, help="시뮬레이터 실행 파일(입력 simulator.exe 보다 우선)")
    ap.add_argument("--timeout-s", type=float, default=None)
    ap.add_argument("--tag", default="")
    ap.add_argument("--topology", default=None, help="C15 대조용 topology JSON(입력 topology.path 보다 우선)")
    ap.add_argument("--require-topology", action="store_true")
    ap.add_argument("--omit", nargs="+", default=[], help="Z1 제거법: 뺄 원소 이름")
    ap.add_argument("--short", nargs="+", default=[], help="Z1 제거법: 0 V 로 단락할 수동소자 이름")
    ap.add_argument("--cache-dir", default=None)
    a = ap.parse_args(argv)
    raw = _read(a.oracle_input)
    inp = None
    try:
        if a.tag and not CIRCUIT_RE.match(a.tag):
            raise OracleError("oracle_input_schema_invalid", [{"pointer": "", "rule": "tag_pattern"}], "1c")
        try:
            inp = json.loads(raw.decode("utf-8")) if raw is not None else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            inp = None
        if not isinstance(inp, dict):
            inp = None
            raise OracleError("oracle_input_schema_invalid", [{"pointer": "", "rule": "json_parse"}], "1a")
        mk = old_markers(inp)
        if mk:
            raise OracleError("oracle_input_format_old", {"markers": mk}, "1b")
        errs = schema_errors(inp)
        if errs:
            raise OracleError("oracle_input_schema_invalid", errs, "1c")
        errs = check_input_cross(inp, circuit_ir(inp, "free")[0])
        if errs:
            raise OracleError("oracle_input_schema_invalid", errs, "1d")
        input_dir = os.path.dirname(os.path.abspath(a.oracle_input))
        adapter = pick_adapter(inp, a, adapters)
        fp = adapter.fingerprint()
        dpath = inp["process"]["descriptor"]["path"]
        dpath = dpath if os.path.isabs(dpath) else os.path.join(input_dir, dpath)
        desc = load_descriptor(dpath, env=os.environ, expected_lf_sha256=inp["process"]["descriptor"]["sha256"])
        bad = sorted({d["kind"] for d in inp["devices"]} - set(desc.doc["kinds"]))
        if bad:
            raise OracleError("descriptor_kind_undeclared",
                              {"kind": bad[0], "devices": [d["name"] for d in inp["devices"] if d["kind"] == bad[0]]}, "2")
        lut = read_lut_files(inp, input_dir)
        cond = Condition(temp_c=lut.temp_c, corner=lut.corner)
        plans = [prepare(inp, b, a, a.oracle_input, desc, cond) for b in a.bias]
        mdep = list(desc.machine_dependent_refs)
        check_descriptor_use(inp, desc, adapter)
        for pl in plans:
            mdep += check_bundles(inp, desc, adapter, lut, pl.circuit, cond)
            if adapter.capabilities().get("case_insensitive_names"):
                for c in [pl.circuit] + [x[0] for x in (pl.loop, pl.cm) if x]:
                    col = fold_collisions(c)
                    if col:
                        raise OracleError("ir_name_collision", col, "9")
        # 실행·판정
        os.makedirs(a.out_dir, exist_ok=True)
        file_judge = None
        if a.judge:
            with open(a.judge, encoding="utf-8") as f:
                file_judge = json.load(f)
        judge = cmp.merge_judge(inp.get("judge"), file_judge, a.sat_margin_v)
        results = {}
        for pl in plans:
            sim, names = execute(pl, desc, adapter, a.out_dir, a)
            res = cmp.compare(inp, compare_meta(pl, lut), sim, judge)
            res["stem"] = pl.stem
            res["netlist"] = next((f"{n}/bench.cir" for n in names if n == pl.stem and os.path.exists(os.path.join(a.out_dir, n, "bench.cir"))), None)
            results[pl.bias] = (res, sim, pl)
    except OracleError as e:
        return write_reject(a.out_dir, inp.get("circuit") if isinstance(inp, dict) else None, e, a.oracle_input, raw)
    if "free" in results:
        fr = results["free"][0]
        fr["diagnosis_free"] = cmp.diagnose(fr, (results.get("forced") or (None,))[0])
    dedup = {r["ref"]: r for r in mdep}
    fpr = {"adapter_fp": canonical_sha256(dict(fp)), "descriptor_fp": desc.fp, "capability_record_id": None, "compat_sha256": None}
    in_sha = hashlib.sha256(raw).hexdigest()
    worst = 0
    for bias, (res, sim, pl) in results.items():
        sim_text = dumps(sim)
        with open(os.path.join(a.out_dir, pl.stem + ".sim.json"), "w", encoding="utf-8") as f:
            f.write(sim_text)
        res["sim_ref"] = {"sha256": canonical_sha256(json.loads(sim_text))}
        res["fingerprints"] = fpr
        res["machine_dependent_refs"] = list(dedup.values())
        res["input_sha256"] = in_sha
        res["record_id"] = canonical_sha256(json.loads(dumps({k: v for k, v in res.items() if k not in ("record_id", "netlist")})))
        with open(os.path.join(a.out_dir, pl.stem + ".compare.json"), "w", encoding="utf-8") as f:
            f.write(dumps(res))
        with open(os.path.join(a.out_dir, pl.stem + ".compare.md"), "w", encoding="utf-8") as f:
            f.write(cmp.to_markdown(res))
        s = res["summary"]
        ac = s.get("spice_ac") or {}
        print(f"[{bias}] verdict={s['verdict']} ({s['verdict_reason']}) gain_db={ac.get('dc_gain_db')} ugf_hz={ac.get('ugf_hz')} "
              f"pm_deg={ac.get('pm_deg')}({ac.get('pm_definition')}) rail_I={s.get('rail_current_A')} topology={s['topology_identity']['status']}")
        for w in s.get("warnings") or []:
            print("  WARNING:", w)
        for b in res["blockers"]:
            print("  BLOCKER:", b)
        worst = max(worst, VERDICT_RC[s["verdict"]])
    return worst


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
