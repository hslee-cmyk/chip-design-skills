"""GB3(U10) test 공용 손 회로와 helper -- 피검 함수 소스 미열람. 근거는 설계 40 §3.3(+6707424 as-built 보완), 계획 DEC-71 (2)(7),
graph CONTRACT 11절(interface).

손 회로는 구성으로 정답이 정해진 합성 입력(oracle (a))이다. 이 모듈은 입력(topology JSON)과 결과에서 값을 꺼내는 함수만 두고
기대값을 계산하지 않는다(기대값은 각 test 의 리터럴). 회로 이름·소자 이름은 test 데이터일 뿐 엔진 규칙이 아니다.
"""
from __future__ import annotations

import copy
import json
import random
import re

import s1v_hand as H
from types import SimpleNamespace

from gmid_engine.graph import COUPLING_KEY, GRAPH_KEY
from gmid_engine.graph import column_block_map as _column_block_map
from gmid_engine.graph import coupling_vars as _coupling_vars


# ---------------------------------------------------------------- [U17 ①-b] 결합 필드 읽기
# 설계 40 v1.9.1 §2.4.8 D8: 묶음 `Coupling`·`ColumnBlockMap` 은 없고 계산 블록 `coupling_vars`(writer coupling_vars)가 S0 수준 필드
# `graph/coupling: vars·column_block_map(=옛 rows)·bias_columns` 를 쓴다. `column_block_map(s1, views) -> (rows, bias_columns)`.
# 아래 두 helper 는 값을 담지 않고 그 필드(또는 함수 반환)를 옛 test 가 읽던 이름(.vars, .column_block_map.rows/.bias_columns)으로 보여 준다.
def cbm(s1, s1v):
    rows, bias = _column_block_map(s1, s1v.views)
    return SimpleNamespace(rows=rows, bias_columns=bias)


def coupling(s1, s1v):
    """S1v 필드가 있는 스냅샷 위에서 계산 블록 `coupling_vars` 를 부르고 `graph/coupling` 필드를 읽는다. `.fields` = (vars, column_block_map, bias_columns)."""
    snap = _coupling_vars(s1v.graph.snapshot)
    f = lambda n: snap.value("graph", COUPLING_KEY, n)  # noqa: E731
    return SimpleNamespace(vars=f("vars"), column_block_map=SimpleNamespace(rows=f("column_block_map"), bias_columns=f("bias_columns")),
                           fields=(f("vars"), f("column_block_map"), f("bias_columns")), snapshot=snap)

# ---------------------------------------------------------------- 손 회로
# 기둥 이웃(column_mate): CS M1 + PMOS 캐스코드 부하 M2(gate vbc) 위의 PMOS 전류원 M3(gate vbp). M3 는 블록 밖이고 같은 기둥에 블록 소자가 있다.
MATE = H.topo("mate", (("M1", "nmos", "out", "in", "gnd"), ("M2", "pmos", "out", "vbc", "m"), ("M3", "pmos", "m", "vbp", "vdd")),
              {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vbc", "vbp"))
# 바이어스 기둥: CS M1 + PMOS 부하 M2(gate vbp). vbp 는 기준 diode Mr(PMOS) + 전류원 Mi(gate vb) 기둥이 만든다 -- 그 기둥 소자는 블록 밖뿐.
BCS = H.topo("bcs", (("M1", "nmos", "out", "in", "gnd"), ("M2", "pmos", "out", "vbp", "vdd"), ("Mr", "pmos", "vbp", "vbp", "vdd"),
                     ("Mi", "nmos", "vbp", "vb", "gnd")), {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vb",))
# BCS + 바이어스 넷 vbp 의 커패시터 Cb(vbp-gnd) + 잎 저항 Rx(vbp-z, z 에 다른 DC 엣지 없음 -> DEC-70 가지치기).
_BCS_MOS = tuple((e["name"], e["kind"], e["drain"], e["gate"], e["source"]) for e in BCS["netlist"])
CAPOR = H.topo("capor", _BCS_MOS,
               {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vb",),
               passives=(("Cb", "capacitor", ("vbp", "gnd")), ("Rx", "resistor", ("vbp", "z"))))
# 귀속 안 된 소자: BCS + Mx(drain z 막다른 넷, source vbp). z 는 Mx drain 하나뿐 -> 가지 (vbp, z) 는 어느 기둥에도 안 들고 Mx 는 블록 밖.
ORPHAN = H.topo("orphan", _BCS_MOS + (("Mx", "nmos", "z", "vb", "vbp"),), {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vb",))
# 바이어스 기둥 둘이 가지를 공유: Mt(gnd-t) 위로 Ma(t-vdd) 와 Mb-Mc 사슬(t-u-vdd). 신호 CS M1/M2 는 따로.
BIASNET = H.topo("biasnet", (("M1", "nmos", "out", "in", "gnd"), ("M2", "pmos", "out", "vbp", "vdd"), ("Mt", "nmos", "t", "vb", "gnd"),
                             ("Ma", "pmos", "t", "ga", "vdd"), ("Mb", "pmos", "t", "gb", "u"), ("Mc", "pmos", "u", "gc", "vdd")),
                 {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vb", "vbp", "ga", "gb", "gc"))
# K3·K4: PMOS 입력 M1(gate in, drain vdd->a 쪽) 와 NMOS M2(a-s) 가 한 블록, 2단 CS M3(gate a, out-s) + 부하 M4 + s 의 싱크 M5 가 다른 블록.
# M5 drain(s) = M2 source(s), s 는 비레일 -> stacked_vsb. 가지 M5 는 두 블록의 기둥이 공유한다.
STACK = H.topo("stack", (("M1", "pmos", "a", "in", "vdd"), ("M2", "nmos", "a", "vbn", "s"), ("M3", "nmos", "out", "a", "s"),
                         ("M4", "pmos", "out", "vbp", "vdd"), ("M5", "nmos", "s", "vbn2", "gnd")),
               {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vbp", "vbn", "vbn2"))
# K8: 차동쌍 M1/M2 + 자기 바이어스 캐스코드 diode(M5/M6, Ra: q-p) 와 그 미러 M9/M10 -> 이득 블록 y.
# 측면 주입: M6 미러 형제 Mc(PMOS, drain n) 가 레벨 시프트 CD Ms(gate y, source n) 의 source 노드 n 에 전류를 넣고, n 은 출력 CD Mf 로 간다.
SIDE = H.topo("side", (("M1", "nmos", "p", "inp", "tail"), ("M2", "nmos", "y", "inn", "tail"), ("M0", "nmos", "tail", "vb", "gnd"),
                       ("M5", "pmos", "q", "p", "r"), ("M6", "pmos", "r", "q", "vdd"), ("M9", "pmos", "w", "q", "vdd"),
                       ("M10", "pmos", "y", "p", "w"), ("Mc", "pmos", "n", "q", "vdd"), ("Ms", "pmos", "gnd", "y", "n"),
                       ("Mf", "nmos", "vdd", "n", "out"), ("Mk", "nmos", "out", "vb", "gnd")),
              {"inp": H.DIFF_P, "inn": H.DIFF_N, "out": H.SE_OUT}, bias=("vb",), passives=(("Ra", "resistor", ("q", "p")),))
# 꼬리를 바이어스 기둥 기준 diode 에서 미러: 5T OTA 의 꼬리 M5(gate nb) + 바이어스 기둥 {Mr(nb-nb-gnd diode), Mi(PMOS 전류원, gate vbp)}.
TAILREF = H.topo("tailref", (("M1", "nmos", "x", "inp", "tail"), ("M2", "nmos", "out", "inn", "tail"), ("M3", "pmos", "x", "x", "vdd"),
                             ("M4", "pmos", "out", "x", "vdd"), ("M5", "nmos", "tail", "nb", "gnd"), ("Mr", "nmos", "nb", "nb", "gnd"),
                             ("Mi", "pmos", "nb", "vbp", "vdd")),
                 {"inp": H.DIFF_P, "inn": H.DIFF_N, "out": H.SE_OUT}, bias=("vbp",))
# H.CMFB + 출력 사이 커패시터 Cx(om-op): 전달 뷰와 루프 뷰 블록이 함께 갖는 커패시터.
CMFB_C = copy.deepcopy(H.CMFB)
CMFB_C["topology_name"] = "cmfbc"
CMFB_C["passive_elements"].append({"name": "Cx", "kind": "capacitor", "terminals": ["om", "op"]})

NINE = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
        "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf")


# ---------------------------------------------------------------- 값 꺼내기
def gval(s1, field):
    return s1.value("graph", GRAPH_KEY, field)


def column_devices(s1):
    """{기둥 id: 기둥 경로 위 원소 집합} -- S1 공개 필드(branches·columns) 직접 집계."""
    br = {b.id: {e for s in b.segments for e in s.elements} for b in gval(s1, "branches")}
    return {c.id: frozenset(e for bid in c.branch_order for e in br[bid]) for c in gval(s1, "columns")}


def column_id(s1, devices):
    """원소 집합이 정확히 devices 인 기둥 id(하나여야 한다)."""
    hits = [cid for cid, devs in column_devices(s1).items() if devs == frozenset(devices)]
    assert len(hits) == 1, (devices, column_devices(s1))
    return hits[0]


def rows(cbm):
    return [(r.column, None if r.block is None else (r.block.view, tuple(r.block.key)), r.device, r.shared, r.basis)
            for r in cbm.rows]


def rec(v):
    """(kind, members, domain, init_rule, nets) -- K4 nets 는 가지 양 끝이라 순서 대신 집합."""
    nets = frozenset(v.nets) if v.kind == "K4" else tuple(v.nets)
    return (v.kind, tuple(v.members), v.domain, v.init_rule, nets)


def _is_pseudo(b):
    return re.search(r"bias:", repr(b)) is not None


def real_blocks(v):
    """레코드 blocks 중 실제 블록(의사 블록 `bias:<기둥>` 이 아닌 것)만 (view, key)."""
    return {(b.view, tuple(b.key)) for b in v.blocks if not _is_pseudo(b)}


def mentions_bias_column(v, col):
    """레코드 blocks 가 의사 블록 `bias:<기둥>`(설계 40 §3.3 as-built)을 담는가 -- 표현(BlockRef 필드 배치)은 정해지지 않아 repr 로 본다."""
    pat = re.compile(r"bias:%s(?!\d)" % re.escape(str(col)))
    return any(pat.search(repr(b)) for b in v.blocks)


# ---------------------------------------------------------------- 이름 전단사(library 원본 -> 새 이름)
def all_nets(raw):
    s = set(raw["supply_nets"])
    for e in raw["netlist"]:
        s |= {e["drain"], e["gate"], e["source"]} | ({e["bulk"]} if e.get("bulk") else set())
    for key in ("passive_elements", "ideal_sources"):
        for e in raw.get(key) or []:
            s |= set(e["terminals"])
    return s


def all_elements(raw):
    return [e["name"] for key in ("netlist", "passive_elements", "ideal_sources") for e in raw.get(key) or []]


def rename_all(raw, netmap, elmap, seed):
    """원소·넷 이름 전단사 + netlist·수동소자 순서 섞기. 태그 키(소자 이름을 담음, 엔진은 읽지 않음)는 지운다."""
    d = copy.deepcopy(raw)
    f = lambda n: netmap.get(n, n)  # noqa: E731
    for e in d["netlist"]:
        e["name"] = elmap.get(e["name"], e["name"])
        for k in ("drain", "gate", "source", "bulk"):
            if k in e:
                e[k] = f(e[k])
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            e["name"] = elmap.get(e["name"], e["name"])
            e["terminals"] = [f(t) for t in e["terminals"]]
    d["supply_nets"] = [f(n) for n in d["supply_nets"]]
    d["ports"] = {(k if k.startswith("_") else f(k)): v for k, v in d["ports"].items()}
    if "bias_inputs" in d:
        d["bias_inputs"] = [f(n) for n in d["bias_inputs"]]
    for k in ("device_roles", "symmetry", "sizing_roles", "compensation"):
        d.pop(k, None)
    random.Random(seed).shuffle(d["netlist"])
    if d.get("passive_elements"):
        random.Random(seed + 1).shuffle(d["passive_elements"])
    return d


def bijection(raw, seed):
    nets = sorted(all_nets(raw))
    els = sorted(all_elements(raw))
    rn = random.Random(seed)
    new_nets = ["w%03d" % i for i in range(len(nets))]
    new_els = ["E%03d" % i for i in range(len(els))]
    rn.shuffle(new_nets)
    rn.shuffle(new_els)
    return dict(zip(nets, new_nets)), dict(zip(els, new_els))


def lib_raw(name):
    return json.loads((H.LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
