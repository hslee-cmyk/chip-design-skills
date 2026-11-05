# -*- coding: utf-8 -*-
"""core/input_check.py -- 입력 교차 칸 검사(§11.2 1d)와 LUT 파일 읽기(§11.2 2b) (design §3.1, card 20261104-op23).

1d: 스키마로 쓸 수 없는 교차 규칙 -- lut_kind_coverage, reference_rail_voltage, bias_gate_nets_mismatch(게이트 전용 넷 집합 == 선언 넷 집합).
2b: LUT 파일 raw sha256 대조, npz 멤버 `meta_json`·`corner`·`temp_c` 읽기(그 밖 멤버는 읽지 않는다), 모델 기록 모양 대 kinds 선언,
    코너·온도 확정. meta_json 이 없는 파일은 여기서 거부하지 않는다(8단계 lut_model_provenance_missing).
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass

from core.build_circuit import gate_only_nets, protected_nets
from core.results import OracleError


def check_input_cross(inp, circuit) -> list:
    """1d 위반 전부 [{pointer, rule}] (pointer, rule) 사전순."""
    errs = []
    dev_kinds = {d["kind"] for d in inp["devices"]}
    lut_kinds = set()
    for i, f in enumerate(inp["process"]["lut_files"]):
        for k in f["kinds"]:
            lut_kinds.add(k)
            if k not in dev_kinds:
                errs.append({"pointer": f"/process/lut_files/{i}/kinds/{k}", "rule": "lut_kind_coverage"})
    for i, d in enumerate(inp["devices"]):
        if d["kind"] not in lut_kinds:
            errs.append({"pointer": f"/devices/{i}/kind", "rule": "lut_kind_coverage"})
    refs = [(i, r) for i, r in enumerate(inp["rails"]) if r.get("reference")]
    if len(refs) == 1 and refs[0][1]["voltage"] != 0:
        errs.append({"pointer": f"/rails/{refs[0][0]}/voltage", "rule": "reference_rail_voltage"})
    declared = {b["net"] for b in inp.get("bias_voltages") or []}
    if set(gate_only_nets(circuit, protected_nets(inp))) != declared:
        errs.append({"pointer": "/bias_voltages", "rule": "bias_gate_nets_mismatch"})
    return [{"pointer": p, "rule": r} for p, r in sorted({(e["pointer"], e["rule"]) for e in errs})]


@dataclass(frozen=True)
class LutRead:
    corner: str
    temp_c: float
    meta_json: tuple          # 파일마다 meta_json dict (없으면 None)
    files: tuple              # 파일마다 {index, path, kinds, meta, table_key}

    def tables(self, kind):
        """kind 가 쓰는 LUT 파일의 모델 기록 표: [(index, path, 표 | None, generator_sha256 | None)]. 표 None = 기록 없음."""
        out = []
        for f in self.files:
            if kind not in f["kinds"]:
                continue
            meta, key = f["meta"], f["kinds"][kind]
            tbl = None
            if isinstance(meta, dict) and isinstance(meta.get("model_files_sha256"), dict):
                t = meta["model_files_sha256"]
                tbl = t if key is None else t.get(key)
            out.append((f["index"], f["path"], tbl, (meta or {}).get("generator_sha256") if isinstance(meta, dict) else None))
        return out


def _resolve(input_dir, p):
    return os.path.abspath(p if os.path.isabs(p) else os.path.join(str(input_dir), p))


def read_lut_files(inp, input_dir) -> LutRead:
    import numpy as np
    files, metas = [], []
    for i, f in enumerate(inp["process"]["lut_files"]):
        p = _resolve(input_dir, f["path"])
        try:
            with open(p, "rb") as fh:
                raw = fh.read()
        except OSError:
            raw = None
        actual = "missing" if raw is None else hashlib.sha256(raw).hexdigest()
        if actual != f["sha256"]:
            raise OracleError("lut_file_stale", {"index": i, "path": p, "expected_sha256": f["sha256"], "actual_sha256": actual}, "2b")
        meta, corner, temp = None, None, None
        with np.load(p, allow_pickle=False) as z:
            names = set(z.files)
            if "meta_json" in names:
                meta = json.loads(str(z["meta_json"].item()))
            if "corner" in names:
                corner = str(z["corner"].item())
            if "temp_c" in names:
                temp = float(z["temp_c"].item())
        _shape_check(i, p, f["kinds"], meta)
        files.append({"index": i, "path": p, "kinds": dict(f["kinds"]), "meta": meta, "corner": corner, "temp_c": temp})
        metas.append(meta)
    proc = inp["process"]
    cond = {}
    for key in ("corner", "temp_c"):
        if proc.get(key) is not None:
            cond[key] = proc[key]
            continue
        rec = {f["index"]: f[key] for f in files if f[key] is not None}
        if len(set(rec.values())) > 1:
            raise OracleError("lut_condition_conflict", {"key": key, "values": rec}, "2b")
        if not rec:
            raise OracleError("oracle_condition_missing", {"key": key}, "2b")
        cond[key] = next(iter(rec.values()))
    return LutRead(corner=cond["corner"], temp_c=float(cond["temp_c"]), meta_json=tuple(metas), files=tuple(files))


def _shape_check(index, path, kinds, meta):
    """meta `model_files_sha256` 모양(평탄 표 / 중첩 dict)을 입력 kinds 선언과 대조한다. 조용히 평탄화하지 않는다."""
    if not isinstance(meta, dict) or not isinstance(meta.get("model_files_sha256"), dict):
        return

    def bad(why):
        raise OracleError("lut_meta_shape_mismatch", {"index": index, "path": path, "why": why}, "2b")
    t = meta["model_files_sha256"]
    vals = list(t.values())
    flat = all(isinstance(v, str) for v in vals)
    nested = all(isinstance(v, dict) for v in vals)
    if vals and not (flat or nested):
        bad("unknown_shape")
    if flat:
        if len(kinds) > 1:
            bad("flat_multi_kind")
        if any(v is not None for v in kinds.values()):
            bad("meta_key_given_for_flat")
    else:
        for k, key in kinds.items():
            if key is None:
                bad("meta_key_missing_for_nested")
            if key not in t:
                bad("nested_key_absent")
