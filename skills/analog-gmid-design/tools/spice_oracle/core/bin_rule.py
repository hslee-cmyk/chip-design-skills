# -*- coding: utf-8 -*-
"""core/bin_rule.py -- 구간(bin) 규칙 선언 `lut_bin_rule/1` 찾기와 호환 모드 대조 (design §16, §7.2 8b, card 20261104-op7b).

LUT 로 잡은 동작점을 다른 호환 모드로 재면 bin 경계 소속이 뒤집혀 다른 모델 조각을 잰다. 이 모듈은 실행 전에
  (1) 입력 LUT 의 모델 기록 파일을 뿌리 아래에서 다시 재서 LF 집합을 만들고(`recorded_lf_set`; 기록 sha 값은 읽지 않는다),
  (2) 선언 파일의 형식·모델 포함·판을 검사하고(`find_decl`),
  (3) 선언 모드가 어댑터가 낼 수 있는 모드이고 글이 같은지 대조한다(`check_compat`).
처음 걸린 하나만 `OracleError`(stage "8b")로 거부한다. 값 문턱은 없고 모든 대조는 해시 일치다. 시뮬레이터 호출 0, 어댑터·엔진 import 0.
선언 정본은 선언 파일 하나이고(기술자는 경로·sha 만 가리킨다) 여기에는 PDK 값·시뮬레이터 이름이 없다.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable, Mapping

from core.results import OracleError, lf_sha256

STAGE = "8b"
SCHEMA = "lut_bin_rule/1"


def _undeclared(detail):
    return OracleError("bin_rule_undeclared", detail, STAGE)


def _mismatch(declared, actual):
    return OracleError("bin_rule_compat_mismatch", {"declared": declared, "actual": actual}, STAGE)


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CompatDecl:
    """`Adapter.run(..., compat)` 의 인자: 선언 모드와 그 설정 글(선언 정본)·글 sha·실행 뒤 대조에 쓰는 로그 줄 정규식(어댑터 표)."""
    mode: str
    spiceinit_text: str
    spiceinit_sha256: str
    log_line: str


def recorded_lf_set(lut_records: Mapping, read_under_root: Callable) -> set:
    """기록 경로마다 `read_under_root(rel)` 바이트의 LF sha256 집합. 기록된 sha 값은 읽지 않는다. 파일을 못 읽으면 거부(why = model_set)."""
    out = set()
    for rel in lut_records:
        try:
            b = read_under_root(rel)
        except OSError:
            b = None
        if b is None:
            raise _undeclared({"why": "model_set", "path": rel})
        out.add(lf_sha256(b))
    return out


def _is_nonempty_str(v) -> bool:
    return isinstance(v, str) and bool(v)


def _form_error(doc):
    """선언 형식 오류 한 항목(없으면 None). 뒤 검사가 읽는 칸이 있고 형이 맞는지만 본다."""
    if not isinstance(doc, dict):
        return "type"
    if doc.get("schema") != SCHEMA:
        return "schema"
    files = doc.get("model_files_sha256")
    if not isinstance(files, list) or not files or not all(_is_nonempty_str(x) for x in files):
        return "model_files_sha256"
    sim = doc.get("simulator")
    if not isinstance(sim, dict) or not _is_nonempty_str(sim.get("name")) or not _is_nonempty_str(sim.get("version")):
        return "simulator"
    comp = doc.get("compat")
    if not isinstance(comp, dict) or not _is_nonempty_str(comp.get("mode")) or not isinstance(comp.get("spiceinit_text"), str) \
            or not _is_nonempty_str(comp.get("spiceinit_sha256")):
        return "compat"
    return None


def find_decl(doc, lf_set: set, fingerprint: Mapping) -> dict:
    """형식 -> 모델 포함(lf_set 이 선언 집합의 부분집합) -> 판(`<name>-<version>` 이 어댑터 sim_version). 맞으면 doc 을 돌려준다."""
    if doc is None:
        raise _undeclared({"why": "no_decl_ref"})
    bad = _form_error(doc)
    if bad is not None:
        raise _undeclared({"why": "decl_invalid", "item": bad})
    missing = sorted(set(lf_set) - set(doc["model_files_sha256"]))
    if missing:
        raise _undeclared({"why": "model_set", "missing": missing})
    declared = f"{doc['simulator']['name']}-{doc['simulator']['version']}"
    actual = fingerprint.get("sim_version")
    if declared != actual:
        raise _undeclared({"why": "simulator", "declared": declared, "actual": actual})
    return doc


def check_compat(decl: dict, compat_modes: Mapping) -> CompatDecl:
    """선언 글 sha 자기 일치 -> 선언 모드가 어댑터 표에 있음 -> 표의 글 sha = 선언 sha."""
    comp = decl["compat"]
    declared = comp["spiceinit_sha256"]
    own = _sha_text(comp["spiceinit_text"])
    if own != declared:
        raise _mismatch(declared, own)
    ent = compat_modes.get(comp["mode"])
    if ent is None:
        raise _mismatch(declared, None)
    table = _sha_text(ent["spiceinit_text"])
    if table != declared:
        raise _mismatch(declared, table)
    return CompatDecl(mode=comp["mode"], spiceinit_text=comp["spiceinit_text"], spiceinit_sha256=declared, log_line=ent["log_line"])
