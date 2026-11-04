# -*- coding: utf-8 -*-
"""core/bundle.py -- 모델 묶음 비교 규칙과 LUT 기록 뿌리 교차 검사 (design §12.5·§7, card 20261104-op23).

LUT 기록(엔진 소유 raw sha256)과 어댑터가 모은 모델 묶음(경로 -> {lf, raw})을 실행마다 대조한다. '같다' = 계획 N3.4 규칙 (ii):
기록값이 파일 LF 값과 같으면 일치, raw 값과만 같으면 기계 의존 일치(반환 목록에 적는다), 둘 다 아니면 위반.
역할은 선언으로만 정한다(`roles`): 선언된 (경로, sha256) 쌍이 기록과 정확히 같을 때만 쓰고, 아니면 역할 미선언 = 모델 파일(조용한 면제 없음).
위반은 OracleError(stage "8"). 대조 불가를 통과로 세지 않는다.
"""
from __future__ import annotations

import re

from core.descriptor import lf_sha256, match_recorded, raw_sha256
from core.results import OracleError

STAGE = "8"


def check_provenance(kind, tables, where=None):
    """LUT 슬라이스 모델 기록 표가 비었는지: tables = [(index, path, 표 | None)]. None -> meta_absent, {} -> empty."""
    for idx, path, table in tables:
        if table is None or table == {}:
            raise OracleError("lut_model_provenance_missing",
                              {"index": idx, "path": path, "why": "meta_absent" if table is None else "empty", "kind": kind}, STAGE)


def check_bundle(kind, lut_records, roles, bundle, texts, model_name, read_aux, where=None):
    """kind 하나의 규칙 (i)(ii)(iii). lut_records = {기록 상대 경로: 기록 sha256}(None = 기록 없음), roles = {상대 경로: {sha256, role}},
    bundle = {경로: {lf, raw}}, texts = {경로: 파일 글}, read_aux(상대 경로) -> bytes | None. 반환 = 기계 의존 항목 목록."""
    where = dict(where or {})
    if lut_records is None:
        raise OracleError("lut_model_provenance_missing", {**where, "why": "meta_absent", "kind": kind}, STAGE)
    if not lut_records:
        raise OracleError("lut_model_provenance_missing", {**where, "why": "empty", "kind": kind}, STAGE)
    mdep: dict = {}
    model_recs, aux_recs = {}, {}
    for rel, sha in lut_records.items():
        r = (roles or {}).get(rel)
        if r and r.get("sha256") == sha and r.get("role") == "generation_aux_input":
            aux_recs[rel] = sha
        else:
            model_recs[rel] = sha
    undeclared = sorted(rel for rel in model_recs if not ((roles or {}).get(rel) and roles[rel].get("sha256") == model_recs[rel]))
    # (i) 모델 파일 기록 ⊆ 묶음
    missing = []
    for rel, sha in sorted(model_recs.items()):
        hit = None
        for path, h in bundle.items():
            if h["lf"] == sha:
                hit = "lf"
                break
            if h["raw"] == sha:
                hit = "raw"
        if hit is None:
            missing.append({"sha256": sha, "path": rel})
        elif hit == "raw":
            ref = f"lut_model_file:{kind}:{rel}"
            mdep[ref] = {"ref": ref, "path": rel, "recorded_sha256": sha, "matched": "raw"}
    if missing:
        raise OracleError("model_bundle_mismatch", {"rule": "i", "kind": kind, "missing": missing,
                                                    "undeclared_role_paths": undeclared}, STAGE)
    # (ii) 호출 모델을 정의한 파일의 sha256 ∈ 모델 파일 기록
    pat = re.compile(rf"^\s*\.(?:subckt|model)\s+{re.escape(model_name)}(?=\s|$)", re.I | re.M)
    defining = [p for p in bundle if pat.search(texts.get(p) or "")]
    rec_shas = set(model_recs.values())
    ok_ii = False
    for p in defining:
        h = bundle[p]
        if h["lf"] in rec_shas:
            ok_ii = True
        elif h["raw"] in rec_shas:
            ok_ii = True
            rel = next(r for r, s in model_recs.items() if s == h["raw"])
            ref = f"lut_model_file:{kind}:{rel}"
            mdep.setdefault(ref, {"ref": ref, "path": rel, "recorded_sha256": h["raw"], "matched": "raw"})
    if not ok_ii:
        raise OracleError("model_bundle_mismatch", {"rule": "ii", "kind": kind, "model_name": model_name,
                                                    "defining_files": sorted(defining)}, STAGE)
    # (iii) 보조 입력 기록 sha256 = 기록 뿌리 아래 같은 상대 경로 파일의 지금 sha256
    for rel, sha in sorted(aux_recs.items()):
        data = read_aux(rel)
        if data is None:
            raise OracleError("lut_aux_input_mismatch", {"path": rel, "recorded_sha256": sha, "actual_sha256": "missing"}, STAGE)
        got = match_recorded(sha, data)
        if got is None:
            raise OracleError("lut_aux_input_mismatch", {"path": rel, "recorded_sha256": sha,
                                                         "actual_sha256": {"lf": lf_sha256(data), "raw": raw_sha256(data)}}, STAGE)
        if got == "raw":
            ref = f"lut_aux_input:{kind}:{rel}"
            mdep[ref] = {"ref": ref, "path": rel, "recorded_sha256": sha, "matched": "raw"}
    return list(mdep.values())


def check_record_root(lut_records, engine_files, read_under_root):
    """기록 뿌리 교차 검사(design §7 `lut_record_root_mismatch`): (1) 짝 = LUT 기록값이 어떤 엔진 원본 파일의 LF 값 또는 raw 값과 같은
    (상대 경로, 엔진 원본 키) (2) 짝마다 뿌리 아래 그 상대 경로 파일의 LF 값 == 엔진 원본 파일의 LF 값(둘 다 바이트 재측정)
    (3) 짝이 0개면 거부. engine_files = {원본 키: (상대 경로, 바이트)}. 반환 = 기계 의존 항목 목록."""
    mdep, pairs = [], []
    for rel, sha in sorted((lut_records or {}).items()):
        for key, (_, data) in sorted(engine_files.items()):
            m = match_recorded(sha, data)
            if m is not None:
                pairs.append((rel, key, data, m, sha))
    if not pairs:
        raise OracleError("lut_record_root_mismatch", {"why": "no_pairs"}, STAGE)
    for rel, key, data, m, sha in pairs:
        elf = lf_sha256(data)
        root_bytes = read_under_root(rel)
        rlf = "missing" if root_bytes is None else lf_sha256(root_bytes)
        if rlf != elf:
            raise OracleError("lut_record_root_mismatch", {"path": rel, "engine_source_key": key,
                                                           "root_file_lf_sha256": rlf, "engine_file_lf_sha256": elf}, STAGE)
        if m == "raw":
            mdep.append({"ref": f"lut_record_root:{key}", "path": rel, "recorded_sha256": sha, "matched": "raw"})
    return mdep
