"""graph/s1_key.py -- `s1_key(doc, supplies) -> S1Key(topology_fp, rule_fp, supplies_v_fp)` (계약 3절, 1절 재사용 불변식).

rule_fp 기대값은 test 가 graph 디렉터리의 S1_RULE_FILES 바이트를 직접 sha256(CRLF -> LF) 해서 만든다(내용은 해석하지
않는다). 소스 변경 감지는 패키지 사본(tmp)에서 확인한다 -- 작업 트리의 엔진 파일은 건드리지 않는다.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import gmid_engine.graph as graph_pkg
from gmid_engine.core import fp_of
from gmid_engine.graph import NO_SUPPLIES_FP, S1_RULE_FILES, S1Key, build_s1, s1_key, supplies_declaration

GRAPH_DIR = Path(graph_pkg.__file__).resolve().parent
ENGINE_DIR = GRAPH_DIR.parent
SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)

# 9회로 전부(2026-10-07 topology 정정 b9c7042 뒤 모두 load 통과) -- JSON 직접 집계 대조용
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))


def _expected_rule_fp(graph_dir: Path) -> str:
    pairs = []
    for base in sorted(S1_RULE_FILES):
        data = (graph_dir / base).read_bytes().replace(b"\r\n", b"\n")
        pairs.append((base, hashlib.sha256(data).hexdigest()))
    return fp_of(tuple(pairs))


@pytest.mark.parametrize("name", NINE)
def test_key_parts(gh, name):
    doc = gh.load_lib(name)
    sv = gh.supplies_for(name)
    sup = supplies_declaration(sv, doc.rails)
    key = s1_key(doc, sup)
    assert isinstance(key, S1Key)
    assert key.topology_fp == doc.connectivity_fp
    assert key.rule_fp == _expected_rule_fp(GRAPH_DIR)
    if sv is None:
        assert key.supplies_v_fp == NO_SUPPLIES_FP
    else:
        assert key.supplies_v_fp == fp_of(tuple(sorted((k, float(v)) for k, v in sv.items())))
    assert build_s1(doc, sv).key == key


def test_supplies_fp_hand_built(gh):
    doc = gh.load_lib("common_gate_amplifier")
    key = s1_key(doc, (("gnd", 0.0), ("vdd", 1.8)))
    assert key.supplies_v_fp == fp_of((("gnd", 0.0), ("vdd", 1.8)))
    assert s1_key(doc, None).supplies_v_fp == "none"


def test_int_and_float_supplies_same_key(gh):
    doc = gh.load_lib("common_gate_amplifier")
    assert build_s1(doc, {"vdd": 2, "gnd": 0}).key == build_s1(doc, {"vdd": 2.0, "gnd": 0.0}).key


@pytest.mark.parametrize("delta", [1e-12, 0.1, -0.5])   # agnd 를 vss·vdd 사이에 둔다(정지 조건 회피)
def test_any_potential_change_changes_only_supplies_part(gh, delta):
    doc = gh.load_lib("sf_pushpull_output_opamp")
    sv = gh.supplies_for("sf_pushpull_output_opamp")
    sv2 = dict(sv, agnd=sv["agnd"] + delta)
    a, b = build_s1(doc, sv).key, build_s1(doc, sv2).key
    assert a != b
    assert (a.topology_fp, a.rule_fp) == (b.topology_fp, b.rule_fp)
    assert a.supplies_v_fp != b.supplies_v_fp


def test_none_vs_supplies_differ(gh):
    doc = gh.load_lib("two_stage_ota_sf")
    assert build_s1(doc, None).key != build_s1(doc, {"vdd": 1.8, "gnd": 0.0}).key


# ------------------------------------------------------------------ 주석·태그는 불변, 연결은 변경 (계약 1절 마지막 항목)


def _annotate(raw: dict, tags) -> dict:
    raw = json.loads(json.dumps(raw))
    raw["_note"] = "changed annotation " + "x" * 17
    raw["_extra_comment"] = {"a": [1, 2, 3]}
    for e in raw["netlist"]:
        e["_comment"] = "per-element note"
    for k in tags:
        raw.pop(k, None)
    rng = random.Random(7)
    rng.shuffle(raw["netlist"])
    if raw.get("passive_elements"):
        rng.shuffle(raw["passive_elements"])
    raw["ports"]["_comment"] = "ports note changed"
    return raw


@pytest.mark.parametrize("name", NINE)
def test_annotation_tags_order_do_not_change_key(gh, tmp_path, name):
    raw = gh.raw(name)
    sv = gh.supplies_for(name, raw)
    a = build_s1(gh.load_lib(name), sv)
    b = build_s1(gh.load_raw(tmp_path, _annotate(raw, gh.TAG_KEYS)), sv)
    assert a.key == b.key
    assert a.snapshot.fp == b.snapshot.fp


def _first_mos(raw, kind=None):
    return next(e for e in raw["netlist"] if kind is None or e["kind"] == kind)


CONNECTION_EDITS = {
    "gate_net": lambda r: _first_mos(r).__setitem__("gate", "NEW_GATE_NET"),
    "kind_flip": lambda r: _first_mos(r, "nmos").__setitem__("kind", "pmos"),
    "declared_bulk": lambda r: _first_mos(r, "nmos").__setitem__("bulk", sorted(r["supply_nets"])[0]),
    "port_role": lambda r: next(v for k, v in r["ports"].items() if not k.startswith("_")).__setitem__("role", "other_role"),
    "passive_terminal_swap": lambda r: r["passive_elements"][0].__setitem__(
        "terminals", list(reversed(r["passive_elements"][0]["terminals"]))),
}


@pytest.mark.parametrize("edit", sorted(CONNECTION_EDITS))
def test_connection_change_changes_key(gh, tmp_path, edit):
    name = "ngcc_3stage_ff"
    raw = gh.raw(name)
    sv = gh.supplies_for(name, raw)
    raw2 = json.loads(json.dumps(raw))
    CONNECTION_EDITS[edit](raw2)
    assert raw2 != raw
    a = build_s1(gh.load_lib(name), sv)
    b = build_s1(gh.load_raw(tmp_path, raw2), sv)
    assert a.key != b.key
    assert a.key.topology_fp != b.key.topology_fp
    assert (a.key.rule_fp, a.key.supplies_v_fp) == (b.key.rule_fp, b.key.supplies_v_fp)


# ------------------------------------------------------------------ rule_fp: 프로세스·해시시드 무관, 소스 바이트 의존


_RULE_FP_SCRIPT = (
    "import sys; sys.path.insert(0, sys.argv[1]);"
    "from gmid_engine.authoring import load_topology;"
    "from gmid_engine.graph import s1_key;"
    "print(s1_key(load_topology(sys.argv[2]), None).rule_fp)"
)


def _rule_fp_in(pkg_parent: Path, topo: Path, seed: str) -> str:
    env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
    out = subprocess.run([sys.executable, "-c", _RULE_FP_SCRIPT, str(pkg_parent), str(topo)],
                         capture_output=True, text=True, env=env, check=True)
    return out.stdout.strip()


def test_rule_fp_independent_of_hash_seed(gh):
    topo = gh.LIBRARY / "common_gate_amplifier.topology.json"
    vals = {_rule_fp_in(ENGINE_DIR.parent, topo, seed) for seed in ("0", "1", "4242", "random")}
    assert vals == {_expected_rule_fp(GRAPH_DIR)}


def _copy_engine(tmp_path: Path) -> Path:
    dst = tmp_path / "pkgcopy"
    shutil.copytree(ENGINE_DIR, dst / "gmid_engine",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", "*.pyc"))
    return dst


def test_rule_fp_tracks_source_bytes_crlf_normalized(gh, tmp_path):
    topo = gh.LIBRARY / "common_gate_amplifier.topology.json"
    copy_root = _copy_engine(tmp_path)
    gdir = copy_root / "gmid_engine" / "graph"
    base = _rule_fp_in(copy_root, topo, "0")
    assert base == _expected_rule_fp(GRAPH_DIR)
    # CRLF 로 바꾼 사본: 같은 rule_fp
    for f in S1_RULE_FILES:
        p = gdir / f
        data = p.read_bytes().replace(b"\r\n", b"\n")
        p.write_bytes(data.replace(b"\n", b"\r\n"))
    assert _rule_fp_in(copy_root, topo, "0") == base
    # 규칙 파일 하나에 주석 한 줄 추가: 다른 rule_fp (기대값도 test 가 직접 계산)
    target = gdir / "supplies.py"
    target.write_bytes(target.read_bytes() + b"# rule change marker\r\n")
    changed = _rule_fp_in(copy_root, topo, "0")
    assert changed != base
    assert changed == _expected_rule_fp(gdir)
    # S1_RULE_FILES 밖(graph/s1_key.py)의 바이트 변경은 rule_fp 에 들어가지 않는다
    other = gdir / "s1_key.py"
    other.write_bytes(other.read_bytes() + b"# not a rule file\n")
    assert _rule_fp_in(copy_root, topo, "0") == changed
