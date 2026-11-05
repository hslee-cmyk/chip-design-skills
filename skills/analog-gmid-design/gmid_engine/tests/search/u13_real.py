"""U13 실경로 test 공용 -- 실 LUT v2(데이터 위치 선언 `assets/lut_v2_location.json`, lut CONTRACT 1.8 의 정본 호출: noise·mismatch 파일까지
`load_lut_set(..., noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)`)와 sky130 PDK·LUT 규칙 선언, library 회로 -> 단계 A(s1v) -> 단계 B(ach)
-> `build_search_context` 공개 진입점 묶음([U17 ①-b] S1v·GB4·출발 구간은 S0 수준 필드 -- u13_hand `S1vRead`·`StartRead` 로 읽는다). 기대값을 만들지 않는다(입력 생성).

측정 harness tests/generality/pipeline.py 도 noise·mismatch npz 를 싣는다(search CONTRACT 11절 시작 검사); tests/pipeline/conftest.py 는 싣지 않는다
-- 여기서는 명시적으로 싣는다.
데이터가 없으면 FAIL 이다(skip 아님 -- tests/pipeline conftest 와 같은 정책).
프로세스당 LUT 한 번(메모리 한계): `real_env()` 는 모듈 전역 한 칸 캐시, `real_case()` 는 (회로, 추가 제약) 키의 작은 캐시(상한 `_CASE_CAP`).
"""
from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

SKILL = Path(__file__).resolve().parents[3]
LIBRARY = SKILL / "assets" / "library"
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
SRC = {"kind": "user_spec", "record": "U13 independent test fixture (constraint added to library spec)", "decided": "2026-10-09"}
RBOX = (1e2, 1e5)                 # search CONTRACT 10절 시연 상자(generality pipeline 과 같은 입력)
CBOX = (1e-13, 1e-10)
EVAL_BUDGET = 40
_ENV = []
_CASES = {}
_CASE_CAP = 6


def real_env():
    if _ENV:
        return _ENV[0]
    from gmid_engine.core import BoundedLRU, read_pdk_decl
    from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(DEVICE_KINDS)
    from pdk_min_w import min_finger_w_m
    mins = min_finger_w_m(kinds.values())      # PDK 선언 양(card 20261104-wb1)
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)          # EF = PDK 선언 noise_ef_* (lut CONTRACT 9 '부르는 쪽이 PDK 선언에서 채운다')
    spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                   noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    assert loc.noise_path and loc.mismatch_path, "데이터 위치 선언에 noise·mismatch 항목이 있어야 한다(lut CONTRACT 1.8)"
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path, bin_rule=loc.bin_rule_path)
    env = SimpleNamespace(lut=lut, memo=LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16), pdk=pdk,
                          rule=read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm),
                          root=Path(tempfile.mkdtemp(prefix="u13r", dir=os.environ.get("TEMP") or None)))
    _ENV.append(env)
    return env


def library_spec(name, extra=()):
    """library spec dict + 추가 판정 제약 extra = ((metric, op, value), ...) (같은 (metric, op) 가 있으면 값을 바꾼다)."""
    spec = json.loads((LIBRARY / (name + ".sizing_spec.json")).read_text(encoding="utf-8"))
    spec = copy.deepcopy(spec)
    cons = spec["human"]["constraints"]
    for metric, op, value in extra:
        hit = [c for c in cons if c.get("metric") == metric and c.get("op") == op]
        if hit:
            hit[0]["value"] = value
        else:
            cons.append({"metric": metric, "op": op, "value": value, "source": dict(SRC)})
    return spec


def real_case(name, extra=()):
    """library 회로 + 추가 제약 -> SimpleNamespace(s1v, ach, spec, kctx, sctx, start, topology, settings, pdk, rule)(처음 부를 때는 a·b 도).
    단계 A·B 는 같은 키에 한 번만 돈다. [XRUN-F1 card B 규칙 M M-d] 프로세스 캐시(_CASES)는 실행과 무관한 입력(S0 수준 S1Graph·spec·code_fp 등)
    뿐이고, 커널·탐색 컨텍스트는 부를 때마다 새 실행(새 open_run() 쌍)으로 만든다 -- 실행의 두 객체를 test 사이에 보관하지 않는다."""
    key = (name, tuple(extra))
    if key in _CASES:
        return _contexts(_CASES[key], None)
    from gmid_engine.pipeline import run_stage_a, run_stage_b
    from gmid_engine.search import SearchSettings, open_run
    env = real_env()
    d = env.root / ("c%02d" % (len(_CASES) + len(os.listdir(env.root))))
    d.mkdir(parents=True, exist_ok=True)
    tp = d / (name + ".topology.json")
    tp.write_text((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"), encoding="utf-8")
    sp = d / (name + ".sizing_spec.json")
    sp.write_text(json.dumps(library_spec(name, extra), indent=1, ensure_ascii=False), encoding="utf-8")
    donors, counters = open_run()      # [card B 규칙 M M-c] 단계 A 와 1:1
    a = run_stage_a(tp, sp, env.lut, output_dir=d / "out", donors=donors, counters=counters)      # [xrun J-1] 선언·경로 인자 없음
    assert a.s1 is not None and a.s1.snapshot.record("graph", "s1v") is not None and a.status == "ok", (a.status, a.report.get("stop_reasons"))
    # [U17 ①-b 2차, 사용자 결정 4] run_stage_b(settings=) 필수 -- build_search_context 와 같은 값(한 실행 = 한 설정, pipeline CONTRACT 5절)
    settings = SearchSettings(600.0, EVAL_BUDGET, RBOX, (("front_budget_s", "u13 test fixture"),), CBOX)
    b = run_stage_b(a, env.memo, env.pdk, output_dir=d / "out", settings=settings)
    assert b.status == "ok", (b.status, b.report.get("stop_reasons"))
    recipe = _recipe(a, b, json.loads(tp.read_text(encoding="utf-8")), settings)
    if len(_CASES) >= _CASE_CAP:
        _CASES.pop(next(iter(_CASES)))
    _CASES[key] = recipe
    case = _contexts(recipe, dict(donors=a.donors, counters=a.counters))   # 처음 부른 test 는 단계 A 의 실행 그대로
    case.a, case.b = a, b
    return case


def _recipe(a, b, topology, settings):
    """실행과 무관한 입력 묶음 -- S0 수준 S1Graph(b.s1)·spec·DcInputs·code_fp·topology·settings(두 객체를 담지 않는다)."""
    from gmid_engine.sizing import dc_inputs_from_spec
    return SimpleNamespace(s0=b.s1, spec=a.spec, inputs=dc_inputs_from_spec(a.spec), code_fp=a.code_fp, topology=topology,
                           settings=settings)


def _contexts(recipe, kernel):
    """recipe -> 커널·탐색 컨텍스트 묶음. kernel = 실행 두 객체 키워드(dict), None 이면 새 실행 하나(새 open_run() 쌍 -- card B C0)."""
    from gmid_engine.search import build_search_context, open_run
    from gmid_engine.sizing import build_kernel_context, LutAccess
    from .u13_hand import read_s1v, start_of
    env = real_env()
    if kernel is None:
        donors, counters = open_run()
        kernel = dict(donors=donors, counters=counters)
    kctx = build_kernel_context(recipe.s0, recipe.inputs, LutAccess(env.memo), **kernel)
    sctx = build_search_context(kctx, recipe.spec, recipe.settings, None, env.pdk, env.rule, code_fp=recipe.code_fp)
    return SimpleNamespace(s1v=read_s1v(recipe.s0), ach=recipe.s0, spec=recipe.spec, kctx=kctx, sctx=sctx, start=start_of(sctx),
                           topology=recipe.topology, settings=recipe.settings, pdk=env.pdk, rule=env.rule)


def input_gate_devices(topology):
    """구조 사실(oracle (a)): gate 가 입력 포트 넷에 닿는 MOS 이름 집합 -- 입력 셀 소자."""
    ins = {n for n, p in topology["ports"].items() if not n.startswith("_") and p["direction"] == "input"}
    return {d["name"] for d in topology["netlist"] if d.get("gate") in ins}
