"""[xrun XR-2] 사슬은 S0 파일을 어디에도 쓰지 않는다 -- interface card C2(설계 40 v1.10 §2.4.3 '디스크: S0 수준 층을 디스크에 쓰지도 읽지도
않는다', 'S0 위치 환경 변수·엔진 폴더 아래 기본 S0 폴더 삭제', 사용자 결정 2026-10-15 "나로 해").

격리: 엔진 폴더 `gmid_engine/`(tests 제외)를 tmp 에 바이트 그대로 복사하고, 하위 프로세스가 그 복사본을 import 해 사슬(단계 A -> B -> 커널 컨텍스트
-> 탐색 컨텍스트(archive_root 줌) -> find_front, 선언 평가 예산)을 돈다. 엔진이 자기 폴더에 무엇을 쓰더라도 복사본에만 쓰므로 이 checkout·공용
폴더를 건드리지 않는다. 하위 프로세스 환경은 허용 목록으로 새로 만든 dict 다(바깥 환경 변수 -- 특히 S0 위치 변수 -- 를 물려받지 않는다):
PATH·SYSTEMROOT·APPDATA(파이썬 사용자 site-packages 위치), TEMP/TMP = 이 test 의 빈 tmp 폴더, OPENBLAS_NUM_THREADS=1, GMID_LUT_TABLE_CACHE_DIR(U-87
표 캐시 -- conftest 의 test 캐시 폴더), LUT·PDK 데이터 위치 변수(있으면, 입력), PYTHONDONTWRITEBYTECODE=1·PYTHONIOENCODING·PYTHONUTF8.

oracle (a) 구성(C2 문장 그대로): 실행 전후
- 엔진 복사본 폴더의 파일·폴더 목록(`__pycache__` 제외)이 같다(새 파일·폴더 0 -- 바이트코드 캐시만 예외).
- tmp(TEMP/TMP) 폴더가 비어 있다.
- 작업 폴더에 새로 생긴 것은 output_dir 보고서, `<archive_root>/<context_fp>/` 아래 evals.jsonl·runs.jsonl·snapshots/*.json.gz, 그리고 이 test 가
  만든 실행 스크립트·결과 JSON 뿐이다(표 캐시는 작업 폴더 밖 conftest 폴더).
실 LUT 데이터가 없으면 FAIL(skip 아님).
"""
from __future__ import annotations

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
PASS_THROUGH = ("PATH", "SYSTEMROOT", "APPDATA", "GMID_LUT_TABLE_CACHE_DIR", "GMID_LUT_V2_ROOT", "GMID_PDK_ROOT")

_RUNNER = r'''
import json, os, sys
from pathlib import Path
ck, skill, circuit, out_dir, s3_root, out_json = sys.argv[1:7]
sys.path.insert(0, ck)
import gmid_engine
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, find_front
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
skill = Path(skill)
lib = skill / "assets" / "library"
loc = resolve_lut_location(str(skill / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds_map = {"nfet_01v8": "nmos", "pfet_01v8": "pmos"}
mins = {}
for e in man["slices"]:
    k = kinds_map[e["device"]]
    mins[k] = min(e["w_um"] * 1e-6, mins.get(k, float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(skill / "assets" / "sky130_pdk_decl.json"), dm)
rule = read_pdk_decl(str(skill / "assets" / "sky130_lut_rule_decl.json"), dm)
q = dict(pdk.quantities)
spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")),
               (("nmos", "_n"), ("pmos", "_p")), noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
settings = SearchSettings(600.0, 20, (1e2, 1e5), (("front_budget_s", "xrun XR-2 fixture"),), (1e-13, 1e-10))
a = run_stage_a(lib / (circuit + ".topology.json"), lib / (circuit + ".sizing_spec.json"), lut, output_dir=Path(out_dir))
memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
b = run_stage_b(a, memo, pdk, output_dir=Path(out_dir), diagnostic=True, settings=settings)
assert (a.status, b.status) == ("ok", "ok"), (a.status, b.status)
kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo))
sctx = build_search_context(kctx, a.spec, settings, s3_root, pdk, rule, code_fp=a.code_fp)
fr = find_front(sctx, [])
with open(out_json, "w", encoding="utf-8") as f:
    json.dump({"engine_dir": str(Path(gmid_engine.__file__).resolve().parent), "context_fp": sctx.context_fp,
               "report_paths": [str(p) for p in list(a.report_paths) + list(b.report_paths)], "n_front": len(fr.front)}, f)
'''


def _listing(root):
    """root 아래 상대 경로 집합(파일과 폴더, `__pycache__` 폴더와 그 안 제외)."""
    root = Path(root)
    out = set()
    for p in root.rglob("*"):
        parts = p.relative_to(root).parts
        if "__pycache__" in parts:
            continue
        out.add(("d:" if p.is_dir() else "f:") + "/".join(parts))
    return out


@pytest.fixture(scope="module")
def isolated_run(tmp_path_factory):
    work = tmp_path_factory.mktemp("xr2")
    ck = work / "ck"
    shutil.copytree(ENGINE, ck / "gmid_engine", ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "tests"))
    tmp = work / "t"
    tmp.mkdir()
    runner = work / "runner.py"
    runner.write_text(_RUNNER, encoding="utf-8")
    out_dir, s3_root, out_json = work / "out", work / "s3", work / "result.json"
    s3_root.mkdir()
    engine_before = _listing(ck / "gmid_engine")
    work_before = _listing(work)
    env = {k: os.environ[k] for k in PASS_THROUGH if k in os.environ}
    env.update(TEMP=str(tmp), TMP=str(tmp), OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               PYTHONUTF8="1")
    assert "GMID_LUT_TABLE_CACHE_DIR" in env                       # conftest 가 고정한 test 표 캐시 폴더(U-87)
    proc = subprocess.run([sys.executable, "-P", str(runner), str(ck), str(SKILL), CIRCUIT, str(out_dir), str(s3_root), str(out_json)],
                          env=env, cwd=str(work), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3000)
    return {"work": work, "ck": ck, "tmp": tmp, "proc": proc, "engine_before": engine_before, "work_before": work_before,
            "out_json": out_json}


def test_chain_ran_on_isolated_engine_copy(isolated_run):
    # 전제: 하위 프로세스가 성공했고 복사본 엔진을 import 했다.
    proc = isolated_run["proc"]
    assert proc.returncode == 0, "격리 실행 실패:\n" + proc.stderr[-4000:]
    got = json.loads(isolated_run["out_json"].read_text(encoding="utf-8"))
    assert Path(got["engine_dir"]).resolve() == (isolated_run["ck"] / "gmid_engine").resolve()


def test_no_new_file_in_engine_folder(isolated_run):
    assert isolated_run["proc"].returncode == 0, isolated_run["proc"].stderr[-4000:]
    after = _listing(isolated_run["ck"] / "gmid_engine")
    assert sorted(after - isolated_run["engine_before"]) == [], "엔진 폴더에 새 파일·폴더가 생겼다(C2)"
    assert sorted(isolated_run["engine_before"] - after) == []


def test_tmp_folder_left_empty(isolated_run):
    assert isolated_run["proc"].returncode == 0, isolated_run["proc"].stderr[-4000:]
    assert sorted(_listing(isolated_run["tmp"])) == [], "TEMP/TMP 에 파일·폴더가 생겼다(C2)"


def test_new_files_only_reports_and_s3_output(isolated_run):
    assert isolated_run["proc"].returncode == 0, isolated_run["proc"].stderr[-4000:]
    work = isolated_run["work"]
    got = json.loads(isolated_run["out_json"].read_text(encoding="utf-8"))
    ctx = got["context_fp"]
    reports = {"f:out/" + Path(p).name for p in got["report_paths"]}
    new = _listing(work) - isolated_run["work_before"]
    allowed_fixed = {"d:out", "f:result.json", "d:s3/" + ctx, "f:s3/%s/evals.jsonl" % ctx, "f:s3/%s/runs.jsonl" % ctx,
                     "d:s3/%s/snapshots" % ctx} | reports
    engine_side = {x for x in new if x.split(":", 1)[1].startswith("ck/")}
    snapshots = {x for x in new if x.startswith("f:s3/%s/snapshots/" % ctx) and x.endswith(".json.gz")
                 and x.count("/") == 3}
    other = sorted(new - allowed_fixed - snapshots - engine_side)
    assert other == [], "허용 밖 새 파일·폴더(C2): %r" % other
    assert {"f:s3/%s/evals.jsonl" % ctx, "f:s3/%s/runs.jsonl" % ctx} <= new          # S3 는 출력으로 계속 쓴다(C5)
    assert reports <= new and len(reports) >= 2
