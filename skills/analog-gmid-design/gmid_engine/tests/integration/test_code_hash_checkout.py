"""v1.9.3 결정 10 통합 test -- 다른 checkout(같은 커밋)이 같은 S0 폴더를 읽어도 S0 수준 블록 계산 0, context_fp 같음.

계약 출처(oracle (d), design 원문): 설계 40 v1.9.3 §2.4.3 '블록 코드 해시' 행 (7)·(9) (b), §2.4.9 판정 2(466행 '다른 checkout(같은 커밋)이
같은 S0 폴더를 읽어도 같다: S0 수준 블록의 `computes` = 0이고 `context_fp`가 같다'), 474행('판정 2의 다른 checkout 부분은 결정 10 card의
통합 test가 ② 전에 판정한다').
oracle 종류: (a) 구성 -- 엔진 폴더 `gmid_engine/` 를 바이트 그대로 tmp 두 곳에 복사한 두 checkout 은 구성상 '같은 커밋'이고, 같은 S0 입력
(저장소 library 회로·PDK 선언·LUT 생성 규칙 선언·LUT 데이터 -- 두 실행이 같은 파일을 읽는다)과 같은 `GMID_S0_SNAPSHOT_DIR` 를 쓴다. 기대값은
'두 번째 checkout 의 S0 수준 블록 computes = 0', 'context_fp 가 첫 checkout 과 같다' 라는 관계뿐이고 test 가 지문 값을 만들지 않는다.
S0 수준 블록 = 첫 실행이 쓴 S0 수준 스냅샷 파일(§2.4.3 형식 gzip JSON)의 `block_versions` 에 이름이 있는 블록(test 가 파일을 직접 읽는다).

각 checkout 은 하위 프로세스에서 그 복사본 `gmid_engine` 을 import 해 단계 A -> 단계 B -> 커널 컨텍스트 -> `build_search_context` 를 차례로 돌리고
(호출 형식은 pipeline CONTRACT 1·3·5절, search CONTRACT -- tests/integration/test_s0_layer_9circuits.py 와 같은 입력), 결과를 JSON 파일에 쓴다.
회로는 하나(단계 A·B 가 ok 인 library 회로 -- 무거워서 하나, (9) (b) '1개 이상'). 실 LUT 데이터가 없으면 FAIL(skip 아님).
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[3]
ENGINE = SKILL / "gmid_engine"
CIRCUIT = "common_gate_amplifier"          # 기준선 fixtures/u17_1b_s0_baseline.json 의 status = [ok, ok] 회로 가운데 하나
S0_ENV = "GMID_S0_SNAPSHOT_DIR"
SUFFIX = ".json.gz"

_RUNNER = r'''
import json, sys
from pathlib import Path
ck, skill, circuit, out_dir, out_json = sys.argv[1:6]
sys.path.insert(0, ck)
import gmid_engine
engine_dir = str(Path(gmid_engine.__file__).resolve().parent)
from gmid_engine.core import BoundedLRU, ComputeBlock, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
import os
skill = Path(skill)
lib = skill / "assets" / "library"
pdk_path = skill / "assets" / "sky130_pdk_decl.json"
rule_path = skill / "assets" / "sky130_lut_rule_decl.json"
loc = resolve_lut_location(str(skill / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds_map = {"nfet_01v8": "nmos", "pfet_01v8": "pmos"}
mins = {}
for e in man["slices"]:
    k = kinds_map[e["device"]]
    mins[k] = min(e["w_um"] * 1e-6, mins.get(k, float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(pdk_path), dm)
rule = read_pdk_decl(str(rule_path), dm)
q = dict(pdk.quantities)
spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")),
               (("nmos", "_n"), ("pmos", "_p")), noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
settings = SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "code_hash checkout test"),), (1e-13, 1e-10))
a = run_stage_a(lib / (circuit + ".topology.json"), lib / (circuit + ".sizing_spec.json"), lut, output_dir=Path(out_dir),
                pdk_decl=pdk, lut_rule_decl=rule, pdk_decl_path=str(pdk_path), lut_rule_decl_path=str(rule_path))
memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
b = run_stage_b(a, memo, pdk, output_dir=Path(out_dir), diagnostic=True, settings=settings)
context_fp = None
if (a.status, b.status) == ("ok", "ok"):
    kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo))
    sctx = build_search_context(kctx, a.spec, settings, None, pdk, rule, code_fp=a.code_fp, s0=a.s0)
    context_fp = sctx.context_fp
stats = {}
for name, mod in list(sys.modules.items()):
    if name.startswith("gmid_engine.") and mod is not None:
        for value in list(vars(mod).values()):
            if isinstance(value, ComputeBlock):
                st = value.stats()
                stats[st.name] = {"calls": st.calls, "reuses": st.reuses, "computes": st.computes}
report_a = json.loads(Path(a.report_paths[0]).read_text(encoding="utf-8"))
with open(out_json, "w", encoding="utf-8") as f:
    json.dump({"engine_dir": engine_dir, "status": [a.status, b.status], "s0_snapshot": report_a.get("s0_snapshot"),
               "context_fp": context_fp, "stats": stats}, f)
'''


def _copy_engine(dst_root):
    dst = dst_root / "gmid_engine"
    shutil.copytree(ENGINE, dst, ignore=shutil.ignore_patterns("__pycache__", ".s0_snapshot", ".pytest_cache"))
    return dst_root


def _run_checkout(tmp_path, ck_root, s0_dir, tag):
    script = tmp_path / "runner.py"
    script.write_text(_RUNNER, encoding="utf-8")
    out_dir = tmp_path / ("out_" + tag)
    out_json = tmp_path / ("result_" + tag + ".json")
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env[S0_ENV] = str(s0_dir)
    proc = subprocess.run([sys.executable, str(script), str(ck_root), str(SKILL), CIRCUIT, str(out_dir), str(out_json)],
                          env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3000)
    assert proc.returncode == 0, "checkout %s 실행 실패:\n%s" % (tag, proc.stderr[-4000:])
    return json.loads(out_json.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def two_checkouts(tmp_path_factory):
    root = tmp_path_factory.mktemp("codehash_ck")
    ck1 = _copy_engine(root / "c1")
    ck2 = _copy_engine(root / "second_checkout_longer_path" / "nested")
    s0_dir = root / "s0"
    s0_dir.mkdir()
    first = _run_checkout(root, ck1, s0_dir, "c1")
    files = sorted(s0_dir.glob("*" + SUFFIX))
    docs = [json.loads(gzip.decompress(p.read_bytes()).decode("ascii")) for p in files]
    second = _run_checkout(root, ck2, s0_dir, "c2")
    same = _run_checkout(root, ck1, s0_dir, "c1_again")       # 대조군: 같은 checkout 재실행(경로 차이 없음)
    return {"ck1": ck1, "ck2": ck2, "first": first, "second": second, "same": same, "docs": docs}


def test_checkouts_are_distinct_byte_copies(two_checkouts):
    # 전제: 두 실행은 서로 다른 경로의 엔진 복사본을 import 했고, 첫 실행이 단계 A ok 로 S0 수준 스냅샷 파일 하나를 남겼다.
    first, second = two_checkouts["first"], two_checkouts["second"]
    assert Path(first["engine_dir"]).resolve() == (two_checkouts["ck1"] / "gmid_engine").resolve()
    assert Path(second["engine_dir"]).resolve() == (two_checkouts["ck2"] / "gmid_engine").resolve()
    assert first["engine_dir"] != second["engine_dir"]
    assert first["status"] == ["ok", "ok"] and second["status"] == ["ok", "ok"]
    assert first["s0_snapshot"] == "miss"
    assert len(two_checkouts["docs"]) == 1 and two_checkouts["docs"][0]["block_versions"]


def test_second_checkout_hits_s0_snapshot(two_checkouts):
    assert two_checkouts["second"]["s0_snapshot"] == "hit"


def test_second_checkout_s0_blocks_zero_computes(two_checkouts):
    s0_blocks = sorted(two_checkouts["docs"][0]["block_versions"])
    stats = two_checkouts["second"]["stats"]
    assert s0_blocks
    missing = [n for n in s0_blocks if n not in stats]
    assert not missing, "S0 수준 블록이 두 번째 checkout 엔진에 없다: %r" % missing
    computed = ["%s computes=%d" % (n, stats[n]["computes"]) for n in s0_blocks if stats[n]["computes"] != 0]
    assert not computed, "다른 checkout 에서 S0 수준 블록이 다시 계산됐다(판정 2):\n" + "\n".join(computed)


def test_second_checkout_context_fp_same(two_checkouts):
    first, second = two_checkouts["first"]["context_fp"], two_checkouts["second"]["context_fp"]
    assert isinstance(first, str) and len(first) == 64
    assert second == first


def test_control_same_checkout_rerun_zero_computes(two_checkouts):
    # 대조군: 같은 checkout 을 같은 S0 로 다시 돌리면 S0 수준 블록 계산 0·context_fp 같음(§2.4.9 판정 2 의 같은 checkout 부분).
    # 위 두 test 가 실패한다면 원인이 '다른 checkout 경로' 하나임을 보인다(입력·S0 폴더·실행 절차는 같다).
    same = two_checkouts["same"]
    assert same["s0_snapshot"] == "hit"
    stats = same["stats"]
    s0_blocks = sorted(two_checkouts["docs"][0]["block_versions"])
    assert s0_blocks and all(n in stats for n in s0_blocks)
    assert [n for n in s0_blocks if stats[n]["computes"] != 0] == []
    assert same["context_fp"] == two_checkouts["first"]["context_fp"]
