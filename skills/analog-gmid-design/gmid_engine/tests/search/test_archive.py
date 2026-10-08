"""CONTRACT 3.18·6절 `S3Archive(root, context_fp, code_fp)` -- `<root>/<context_fp>/` 아래 evals.jsonl·runs.jsonl·
snapshots/<fp>.json.gz 형식, 줄마다 flush(평가 직후 읽힘), 스냅샷 왕복(read_snapshot)."""
import gzip
import json
from pathlib import Path


from gmid_engine.search import S3Archive, evaluate, find_front

from .conftest import CELLS_C, build_case, circuit_c, theta_r4c

RUN_KEYS = ("run_id", "s0", "schema_fp", "settings", "starts", "resolution", "front", "pending_front", "removed",
            "failed_eps", "notes", "perf", "code_fp")
POINT_KEYS = ("point_id", "status", "seq", "theta_hex", "cells", "power_dc_w", "area_search_m2", "gate_area_m2",
              "passives_in_area", "power_resolution_w", "unmeasured", "active", "origin", "snapshot_fp", "snapshot_ref")


def _jsonl(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def test_constructor_and_lazy_layout(tmp_path, short_root):
    a = S3Archive(short_root, "c" * 64, "d" * 64)
    assert isinstance(a, S3Archive)


def test_evals_line_written_per_kernel_call(tmp_path, lut_sealed, short_root):
    case = build_case(tmp_path, circuit_c(), lut_sealed, archive_root=short_root)
    s = case.sctx
    d = Path(short_root) / s.context_fp
    for k in range(3):
        evaluate(s, tuple(sorted(theta_r4c(i2=1e-5 * (1 + 0.1 * k)).items())), CELLS_C)
        assert len(_jsonl(d / "evals.jsonl")) == k + 1                     # flush: 바로 읽힌다
    evaluate(s, tuple(sorted(theta_r4c(i2=1e-5).items())), CELLS_C)        # 캐시 적중 -> 줄 없음
    recs = _jsonl(d / "evals.jsonl")
    assert len(recs) == 3 == dict(s.counters)["kernel_calls"]
    assert [r["seq"] for r in recs] == [1, 2, 3]
    assert all(r["code_fp"] == s.code_fp and r["schema_fp"] == s.schema_fp for r in recs)


def test_runs_and_snapshot_files(tmp_path, lut_sealed, short_root):
    case = build_case(tmp_path, circuit_c(), lut_sealed, archive_root=short_root, eval_budget=40)
    s = case.sctx
    fr = find_front(s, [theta_r4c()])
    d = Path(short_root) / s.context_fp
    (run,) = _jsonl(d / "runs.jsonl")
    for k in RUN_KEYS:
        assert k in run, k
    assert run["run_id"] == fr.run_id and run["code_fp"] == s.code_fp and run["schema_fp"] == s.schema_fp
    assert len(run["front"]) == len(fr.front) >= 1
    for entry, p in zip(run["front"], fr.front):
        for k in POINT_KEYS:
            assert k in entry, k
        assert entry["point_id"] == p.point_id
        # [결정 11] 6절: passives_in_area = sctx.area_decl 이 있으면 True(수동 커패시터 면적이 area_search_m2 에 든다). build_search_context
        # 는 PDK 선언과 spec 으로 늘 area_decl 을 만든다(3.22) -> True. oracle (d) 계약 6절 문장.
        assert s.area_decl is not None
        assert entry["passives_in_area"] is True
        assert entry["power_dc_w"] == p.result.objectives.power_w
        assert entry["area_search_m2"] == p.result.objectives.area_m2
        assert [tuple(k) for k, _ in entry["theta_hex"]] == [k for k, _ in p.result.theta]
        assert [float.fromhex(h) for _, h in entry["theta_hex"]] == [v for _, v in p.result.theta]
        ref = d / entry["snapshot_ref"]
        assert ref.is_file() and ref.name == entry["snapshot_fp"] + ".json.gz"
        with gzip.open(ref, "rt", encoding="utf-8") as fh:
            body = json.load(fh)
        assert body["fp"] == entry["snapshot_fp"]
        assert body["records"] and {"kind", "key", "fields"} <= set(body["records"][0])
        f0 = next(iter(body["records"][0]["fields"].values()))
        assert {"value", "writer", "input_version"} <= set(f0)
        # 왕복: read_snapshot(ref) = 그 파일 내용(6절 형식), 노드전압 = 메모리 스냅샷
        back = s.archive.read_snapshot(entry["snapshot_ref"])
        assert back == body
        mem = p.result.evaluation.snapshot
        dv = {r["key"]: r["fields"]["dc_v"]["value"] for r in back["records"]
              if r["kind"] == "node" and "dc_v" in r["fields"]}
        assert dv == dict(mem.column("node", "dc_v"))
