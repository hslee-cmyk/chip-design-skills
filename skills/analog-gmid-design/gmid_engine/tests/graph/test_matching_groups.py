"""graph/matching_groups.py -- `s1_matching_groups`: 레이아웃 matching 분류(계약 4.5a, 4.5 표 matching_offset 행, 9절 18번).

근거는 계약 문장뿐이다(graph 소스 미열람). 기대값 두 갈래:
- 손으로 만든 작은 topology 마다 계약 정의를 손으로 따라가 적은 **명시 기대값**(아래 각 test 주석에 유도).
- 이 파일의 `MatchOracle`(topology JSON 만 읽는 test 쪽 재구현, U2~U3 는 `graph_u2_oracle.U2Oracle`)과의 대조.

9회로: 계약 4.5a 는 회로별 수치를 '기대값이 아니라 작성자 실행값'(J-U4 대조표 / J14 사용자 확인 전)이라 했으므로 회로별
분류 수·멤버를 기대값으로 고정하지 않는다. 9회로에는 정의 적합성(oracle 대조)·불변량(권한·status·결정론·치환·복제)만 건다.
"""
from __future__ import annotations

import collections
import copy
import json
import os
import random
import subprocess
import sys

import pytest

from gmid_engine.core import ComputeBlock, GraphSnapshot
from gmid_engine.graph import (
    DISPOSITION_BIAS_DISTRIBUTION,
    DISPOSITION_BIAS_SIBLING,
    DISPOSITION_FEEDBACK_SHARED,
    DOMAIN_DC_TO_SS,
    GRAPH_KEY,
    J_BRANCH_SYMMETRIC,
    J_DIFF_PAIR,
    J_MATCH_CLASS,
    MATCH_BRANCH_SYMMETRIC,
    MATCH_DIFF_PAIR,
    MATCH_MIRROR,
    MIRROR_RULE_CONSUMER_BLOCK,
    MIRROR_RULE_DIODE_BLOCK,
    MIRROR_RULE_SIGNAL_CROSS_BLOCK,
    MIRROR_RULE_WHOLE,
    REL_MATCHING_OFFSET,
    S1_MATCHING_GROUPS_WRITER,
    S1_REL_MATCHING_WRITER,
    S1_WRITERS,
    SIBLING_RULE_GROUND_GATE,
    SIBLING_RULE_OWN_BRANCH_GATE,
    SIBLING_RULE_ROLE,
    STATUS_DERIVED,
    STATUS_PROPOSED,
    STATUS_REVIEW_NEEDED,
    MatchingDisposition,
    MatchingGroup,
    RelEdge,
    build_s1,
    s1_matching_groups,
    s1_rel_matching,
)
from graph_u2_oracle import U2Oracle

NINE = tuple(sorted((
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff", "pushpull_follower_buffer",
    "sf_pushpull_output_opamp", "two_stage_ota_sf", "folded_cascode", "nmcnr_amplifier", "two_stage_ota",
)))
FIELDS = ("rel_matching_offset", "matching_groups", "matching_dispositions")
JB, JD, JC = "J-U4-b", "J-U4-d", "J-U4-c"
D, P, R = "derived", "proposed", "review_needed"


# ---------------------------------------------------------------- 입력 생성 (test 쪽)
def topo(netlist, inputs, outputs, passives=(), rails=("vdd", "gnd"), name="syn"):
    """netlist = ((이름, kind, drain, gate, source), ...), passives = ((이름, kind, t0, t1), ...)."""
    ports = {n: {"direction": "input", "role": "signal"} for n in inputs}
    ports.update({n: {"direction": "output", "role": "signal"} for n in outputs})
    return {
        "schema_version": "2.0",
        "topology_name": name,
        "supply_nets": list(rails),
        "netlist": [{"name": n, "kind": k, "drain": d, "gate": g, "source": s} for n, k, d, g, s in netlist],
        "passive_elements": [{"name": n, "kind": k, "terminals": [a, b]} for n, k, a, b in passives],
        "ports": ports,
    }


def build(gh, tmp_path, raw, supplies=None, stem="syn"):
    return build_s1(gh.load_raw(tmp_path, raw, stem), supplies)


def plain_group(g):
    return (g.kind, g.members, g.status, (g.evidence.rule, g.evidence.nets, g.evidence.group, g.evidence.basis))


def plain_fields(gh, s1):
    off = tuple(gh.rel_plain(r) for r in gh.gval(s1, "rel_matching_offset"))
    grp = tuple(plain_group(g) for g in gh.gval(s1, "matching_groups"))
    dis = tuple(plain_group(g) for g in gh.gval(s1, "matching_dispositions"))
    return off, grp, dis


def rename_all(raw, netmap, elmap):
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
    for k in list(d):
        if k in ("device_roles", "symmetry", "sizing_roles", "compensation"):
            del d[k]                                   # 태그는 소자 이름을 담아 치환 대상이 아니다(엔진은 읽지 않음)
    return d


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


def canon(fields, netmap=None, elmap=None):
    """순서·이름 tie-break 를 지운 정준형: 필드별 다중집합, 원소는 (kind, 멤버 집합, status, rule, 넷 집합, 그룹 집합, basis)."""
    nm = (lambda n: netmap.get(n, n)) if netmap else (lambda n: n)
    em = (lambda n: elmap.get(n, n)) if elmap else (lambda n: n)
    out = []
    for i, recs in enumerate(fields):
        c = collections.Counter()
        for r in recs:
            if i == 0:
                kind, members, status, ev = r[0], r[2], r[3], r[4]
            else:
                kind, members, status, ev = r
            c[(kind, frozenset(map(em, members)), status, ev[0], frozenset(map(nm, ev[1])),
               frozenset(map(em, ev[2])), ev[3])] += 1
        out.append(c)
    return out


# ---------------------------------------------------------------- 계약 4.5a 독립 재구현
class MatchOracle:
    """계약 4.5a 표·문장을 그대로 다시 구현(엔진 미사용). 값은 plain tuple(엔진 출력의 plain_fields 와 같은 모양)."""

    def __init__(self, raw):
        o = U2Oracle(raw)
        self.o = o
        mos, rails, G = o.mos, o.rails, o.ground
        diodes = set(o.diodes)
        inputs = o.input_ports
        # 가지 넷·소자의 가지
        self.bnets = {}
        dev_branch = {}
        for bid, ends, segs, _src in o.branches:
            self.bnets[bid] = frozenset(ends) | {n for nets, _els in segs for n in nets}
            for _nets, els in segs:
                for el in els:
                    dev_branch[el] = bid
        self.dev_branch = dev_branch
        # 블록: 레일이 아닌 가지 끝 넷을 공유하는 가지끼리 연결 성분
        parent = {bid: bid for bid in self.bnets}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        by_end = collections.defaultdict(list)
        for bid, ends, _segs, _src in o.branches:
            for n in ends:
                if n not in rails:
                    by_end[n].append(bid)
        for bids in by_end.values():
            for b in bids[1:]:
                parent[find(b)] = find(bids[0])
        self.block_of_branch = {bid: find(bid) for bid in self.bnets}
        blocks = collections.defaultdict(set)
        for bid, blk in self.block_of_branch.items():
            blocks[blk] |= self.bnets[bid]
        self.block_nets = {k: frozenset(v) for k, v in blocks.items()}
        blk_of = lambda m: self.block_of_branch[dev_branch[m]]  # noqa: E731
        self.blk_of = blk_of
        block_mos = collections.defaultdict(list)
        for m in mos:
            block_mos[blk_of(m)].append(m)
        # 바이어스 블록: 최대 고정점
        alive = set(self.block_nets)
        while True:
            bias_nets = set().union(*(self.block_nets[b] for b in alive)) if alive else set()
            drop = {b for b in alive
                    if self.block_nets[b] & inputs
                    or any(mos[m]["gate"] not in G and mos[m]["gate"] not in bias_nets
                           for m in block_mos[b] if m not in diodes)}
            if not drop:
                break
            alive -= drop
        self.bias_blocks = alive
        self.B = frozenset().union(*(self.block_nets[b] for b in alive)) if alive else frozenset()
        # 영향 그래프 + 루프 신호 넷 L
        edges, mos_edges = set(), set()

        def add(a, b, is_mos):
            if a != b and a not in G and b not in G:
                edges.add((a, b))
                if is_mos:
                    mos_edges.add((a, b))

        for e in mos.values():
            add(e["gate"], e["drain"], True)
            add(e["gate"], e["source"], True)
            add(e["source"], e["drain"], True)
        for e in o.passives.values():
            if e["kind"] == "resistor":
                a, b = e["terminals"]
                add(a, b, False)
                add(b, a, False)
        nodes = {n for ed in edges for n in ed}
        succ = collections.defaultdict(set)
        for a, b in edges:
            succ[a].add(b)

        def reach(x):
            seen, stack = {x}, [x]
            while stack:
                for y in succ[stack.pop()]:
                    if y not in seen:
                        seen.add(y)
                        stack.append(y)
            return seen

        R_ = {n: reach(n) for n in nodes}
        sccs = {frozenset(m for m in R_[n] if n in R_[m]) for n in nodes}
        L = set()
        for C in sccs:
            if len(C) < 2:
                continue
            if not any(a in C and b in C for a, b in mos_edges):
                continue
            if any(C <= bn for bn in self.bnets.values()):
                continue
            L |= C
        self.L = frozenset(L)
        # 차동쌍 후보·바이어스 형제
        cand = collections.defaultdict(list)
        for m in sorted(mos):
            if mos[m]["source"] not in rails:
                cand[(mos[m]["kind"], mos[m]["source"])].append(m)
        offset, siblings = [], []
        for key in sorted(cand):
            members = cand[key]
            if len({mos[m]["gate"] for m in members}) < 2:
                continue
            src = key[1]
            sib, rest = [], []
            for m in members:
                g = mos[m]["gate"]
                if o.dc_roles[m][0] in ("diode_reference", "bias_current_source"):
                    sib.append((m, "bias_sibling_dc_role"))
                elif g in G:
                    sib.append((m, "bias_sibling_ground_gate"))
                elif g in self.bnets[dev_branch[m]]:
                    sib.append((m, "bias_sibling_own_branch_gate"))
                else:
                    rest.append(m)
            for m, rule in sib:
                siblings.append(("bias_sibling", (m,), P, (rule, (src, mos[m]["gate"]), tuple(rest), (JB, JD))))
            gates = sorted({mos[m]["gate"] for m in rest})
            if len(gates) >= 2:
                offset.append(("matching_offset", "dc_to_ss", tuple(rest), D if len(rest) == 2 else R,
                               ("matching_offset", (src,) + tuple(gates), (), (JB,))))
        self.offset = tuple(offset)
        # mirror·disposition
        groups, disp = [], []
        for _kind, g, s, members in o.gs_groups:
            if g in rails:
                continue
            dm = tuple(m for m in members if m in diodes)
            dblocks = {blk_of(m) for m in dm}
            consumers = tuple(m for m in members if m not in diodes and blk_of(m) not in dblocks) if dm else ()
            if not consumers:
                groups.append(("mirror", members, D, ("mirror_whole", (g, s), dm, ())))
            elif g not in self.B and g not in self.L:
                groups.append(("mirror", members, D, ("mirror_signal_cross_block", (g, s), dm, (JD,))))
            else:
                side = tuple(m for m in members if m not in consumers)
                if len(side) >= 2:
                    groups.append(("mirror", side, D, ("mirror_diode_block", (g, s), dm, (JD,))))
                per = collections.defaultdict(list)
                for m in consumers:
                    per[blk_of(m)].append(m)
                for ms in sorted(tuple(v) for v in per.values() if len(v) >= 2):
                    groups.append(("mirror", ms, D, ("mirror_consumer_block", (g, s), dm, (JD,))))
                kind = "bias_distribution" if g in self.B else "feedback_shared"
                disp.append((kind, consumers, P, (kind, (g, s), dm, (JD,))))
        for r in self.offset:
            groups.append(("diff_pair", r[2], r[3], ("diff_pair", r[4][1], (), (JB,))))
        # branch_symmetric 전파
        queue = [x for x in groups if x[2] == D]
        seen = {frozenset(x[1]) for x in groups}
        i = 0
        while i < len(queue):
            S = queue[i]
            i += 1
            upper = set()
            for m in S[1]:
                dn = mos[m]["drain"]
                if dn in rails:
                    continue
                upper |= {x for x in mos if mos[x]["kind"] == mos[m]["kind"] and mos[x]["source"] == dn
                          and x not in S[1]}
            bygate = collections.defaultdict(list)
            for x in upper:
                bygate[mos[x]["gate"]].append(x)
            for g in sorted(bygate):
                xs = tuple(sorted(bygate[g]))
                srcs = tuple(sorted({mos[x]["source"] for x in xs}))
                if len(srcs) >= 2 and frozenset(xs) not in seen:
                    new = ("branch_symmetric", xs, D, ("branch_symmetric", (g,) + srcs, S[1], (JC,)))
                    seen.add(frozenset(xs))
                    groups.append(new)
                    queue.append(new)
        self.groups = tuple(groups)
        self.dispositions = tuple(siblings) + tuple(disp)

    def fields(self):
        return self.offset, self.groups, self.dispositions


# ---------------------------------------------------------------- 손 topology
# 5T OTA: M1/M2 차동쌍(CS), M3 diode + M4 PMOS 미러, M5 꼬리(gate vb = gate 전용 -> G)
OTA5 = (
    ("M1", "nmos", "D3", "inp", "CS"),
    ("M2", "nmos", "O1", "inn", "CS"),
    ("M3", "pmos", "D3", "D3", "vdd"),
    ("M4", "pmos", "O1", "D3", "vdd"),
    ("M5", "nmos", "CS", "vb", "gnd"),
)


def ota5(extra=(), drop=(), replace=None, passives=(), inputs=("inp", "inn"), outputs=("O1",)):
    rows = [r for r in OTA5 if r[0] not in drop]
    if replace:
        rows = [replace.get(r[0], r) for r in rows]
    return topo(rows + list(extra), inputs, outputs, passives)


MIRROR_M3M4 = ("mirror", ("M3", "M4"), D, ("mirror_whole", ("D3", "vdd"), ("M3",), ()))
OFF_M1M2 = ("matching_offset", "dc_to_ss", ("M1", "M2"), D, ("matching_offset", ("CS", "inn", "inp"), (), (JB,)))
DIFF_M1M2 = ("diff_pair", ("M1", "M2"), D, ("diff_pair", ("CS", "inn", "inp"), (), (JB,)))

CASES = {}

# A. 기본 5T: 한 블록(CS 공유) -> 소비 소자 없음 -> mirror_whole. 차동쌍 M1/M2 derived. 위 소자 없음.
CASES["ota5"] = (ota5(), ((OFF_M1M2,), (MIRROR_M3M4, DIFF_M1M2), ()))

# B. 2단 NMOS 캐스코드: diff seed -> {M1c, M2c}(gate vc1, source X1/X2) -> 다시 seed -> {M1d, M2d}(gate vc2).
CASES["cascode2"] = (
    ota5(replace={"M1": ("M1", "nmos", "X1", "inp", "CS"), "M2": ("M2", "nmos", "X2", "inn", "CS")},
         extra=(("M1c", "nmos", "Y1", "vc1", "X1"), ("M2c", "nmos", "Y2", "vc1", "X2"),
                ("M1d", "nmos", "D3", "vc2", "Y1"), ("M2d", "nmos", "O1", "vc2", "Y2"))),
    ((OFF_M1M2,),
     (MIRROR_M3M4, DIFF_M1M2,
      ("branch_symmetric", ("M1c", "M2c"), D, ("branch_symmetric", ("vc1", "X1", "X2"), ("M1", "M2"), (JC,))),
      ("branch_symmetric", ("M1d", "M2d"), D, ("branch_symmetric", ("vc2", "Y1", "Y2"), ("M1c", "M2c"), (JC,)))),
     ()))

# C. 바이어스 형제 셋(같은 source CS): Md diode(dc_role) / Mg gate vb(G) / Mo gate P(자기 가지 vdd-Rq-P-Mq-Q-Mo-CS 안).
#    후보 (nmos, CS) 멤버 이름순 M1, M2, Md, Mg, Mo -> 형제 Md, Mg, Mo 빼고 {M1, M2} derived.
CASES["siblings3"] = (
    ota5(extra=(("Md", "nmos", "Yd", "Yd", "CS"), ("Mg", "nmos", "Z", "vb", "CS"),
                ("Mq", "nmos", "P", "P", "Q"), ("Mo", "nmos", "Q", "P", "CS")),
         passives=(("Ryd", "resistor", "vdd", "Yd"), ("Rz", "resistor", "vdd", "Z"), ("Rq", "resistor", "vdd", "P"))),
    ((OFF_M1M2,), (MIRROR_M3M4, DIFF_M1M2),
     (("bias_sibling", ("Md",), P, ("bias_sibling_dc_role", ("CS", "Yd"), ("M1", "M2"), (JB, JD))),
      ("bias_sibling", ("Mg",), P, ("bias_sibling_ground_gate", ("CS", "vb"), ("M1", "M2"), (JB, JD))),
      ("bias_sibling", ("Mo",), P, ("bias_sibling_own_branch_gate", ("CS", "P"), ("M1", "M2"), (JB, JD))))))

# C2. 검사 순서: gate 가 G(vb) 이고 같은 gs 묶음(nmos, vb, CS)인 Mg/Mh 는 dc_role(2)=bias 라 rule 은 dc_role(ground_gate 아님).
CASES["sibling_order"] = (
    ota5(extra=(("Mg", "nmos", "Z", "vb", "CS"), ("Mh", "nmos", "Z2", "vb", "CS")),
         passives=(("Rz", "resistor", "vdd", "Z"), ("Rz2", "resistor", "vdd", "Z2"))),
    ((OFF_M1M2,),
     (("mirror", ("Mg", "Mh"), D, ("mirror_whole", ("vb", "CS"), (), ())),   # gs 묶음 순: (nmos, vb, CS) 먼저
      MIRROR_M3M4,
      DIFF_M1M2),
     (("bias_sibling", ("Mg",), P, ("bias_sibling_dc_role", ("CS", "vb"), ("M1", "M2"), (JB, JD))),
      ("bias_sibling", ("Mh",), P, ("bias_sibling_dc_role", ("CS", "vb"), ("M1", "M2"), (JB, JD))))))

# C3. 형제를 빼면 gate 넷 하나만 남음 -> RelEdge 없음, 형제 기록은 남음(group = 남은 멤버 (M1,)).
CASES["sibling_leaves_one"] = (
    topo((("M1", "nmos", "D3", "inp", "CS"), ("M3", "pmos", "D3", "D3", "vdd"),
          ("Mg", "nmos", "Z", "vb", "CS"), ("M5", "nmos", "CS", "vb", "gnd")),
         ("inp",), ("D3",), (("Rz", "resistor", "vdd", "Z"),)),
    ((), (), (("bias_sibling", ("Mg",), P, ("bias_sibling_ground_gate", ("CS", "vb"), ("M1",), (JB, JD))),)))

# C4. 남은 멤버 3(gate 셋 다름) -> review_needed. review_needed diff_pair 는 seed 가 아니라 그 위 캐스코드쌍도 안 생긴다.
CASES["offset3_review"] = (
    topo((("M1", "nmos", "X1", "inp", "CS"), ("M2", "nmos", "X2", "inn", "CS"), ("Mx", "nmos", "O2", "inx", "CS"),
          ("M1c", "nmos", "D3", "vc", "X1"), ("M2c", "nmos", "O1", "vc", "X2"),
          ("M3", "pmos", "D3", "D3", "vdd"), ("M4", "pmos", "O1", "D3", "vdd"), ("M6", "pmos", "O2", "D3", "vdd"),
          ("M5", "nmos", "CS", "vb", "gnd")),
         ("inp", "inn", "inx"), ("O1",)),
    ((("matching_offset", "dc_to_ss", ("M1", "M2", "Mx"), R,
       ("matching_offset", ("CS", "inn", "inp", "inx"), (), (JB,))),),
     (("mirror", ("M3", "M4", "M6"), D, ("mirror_whole", ("D3", "vdd"), ("M3",), ())),
      ("diff_pair", ("M1", "M2", "Mx"), R, ("diff_pair", ("CS", "inn", "inp", "inx"), (), (JB,)))),
     ()))

# D. bias_distribution: 바이어스 블록 vdd-Rb-NB-(Mb∥Mb2)-gnd(입력·비diode MOS 없음 -> B 에 NB).
#    gs (nmos, NB, gnd) = M5, M7, M8, Mb, Mb2; diode Mb/Mb2 -> 소비 = M5(주 블록), M7/M8(2단 블록).
#    gate ∈ B -> diode 쪽 {Mb, Mb2} mirror_diode_block, 2단 블록 {M7, M8} mirror_consumer_block, disposition {M5, M7, M8}.
CASES["bias_distribution"] = (
    ota5(replace={"M5": ("M5", "nmos", "CS", "NB", "gnd")},
         extra=(("Mb", "nmos", "NB", "NB", "gnd"), ("Mb2", "nmos", "NB", "NB", "gnd"),
                ("M6", "pmos", "OUT", "O1", "vdd"), ("M7", "nmos", "OUT", "NB", "gnd"), ("M8", "nmos", "OUT", "NB", "gnd")),
         passives=(("Rb", "resistor", "vdd", "NB"),), outputs=("OUT",)),
    ((OFF_M1M2,),
     (("mirror", ("Mb", "Mb2"), D, ("mirror_diode_block", ("NB", "gnd"), ("Mb", "Mb2"), (JD,))),
      ("mirror", ("M7", "M8"), D, ("mirror_consumer_block", ("NB", "gnd"), ("Mb", "Mb2"), (JD,))),
      MIRROR_M3M4, DIFF_M1M2),
     (("bias_distribution", ("M5", "M7", "M8"), P, ("bias_distribution", ("NB", "gnd"), ("Mb", "Mb2"), (JD,))),)))

# E. feedback_shared: 블록 A vdd-Md(diode FB)-FB-Ms(gate OUT)-gnd, 블록 B vdd-Mc(gate FB)-OUT-Mn(gate inp)-gnd.
#    영향 FB->OUT(Mc g->d), OUT->FB(Ms g->d) -> SCC {FB, OUT}(두 가지에 걸침) = L. 바이어스 블록 없음(B 비어 있음).
FB_LOOP = (("Md", "pmos", "FB", "FB", "vdd"), ("Ms", "nmos", "FB", "OUT", "gnd"),
           ("Mc", "pmos", "OUT", "FB", "vdd"), ("Mn", "nmos", "OUT", "inp", "gnd"))
CASES["feedback_shared"] = (
    topo(FB_LOOP, ("inp",), ("OUT",)),
    ((), (), (("feedback_shared", ("Mc",), P, ("feedback_shared", ("FB", "vdd"), ("Md",), (JD,))),)))

# E2. 고리 끊기(Ms gate = 입력 inp2): L 비어 있음, B 비어 있음 -> mirror_signal_cross_block(묶음 전부).
CROSS = ((), (("mirror", ("Mc", "Md"), D, ("mirror_signal_cross_block", ("FB", "vdd"), ("Md",), (JD,))),), ())
FB_OPEN = tuple(r if r[0] != "Ms" else ("Ms", "nmos", "FB", "inp2", "gnd") for r in FB_LOOP)
CASES["signal_cross_block"] = (topo(FB_OPEN, ("inp", "inp2"), ("OUT",)), CROSS)

# E3. 커패시터로만 닫히는 고리(Cc: OUT-FB): 커패시터는 영향 엣지가 아니라 L 아님 -> E2 와 같다.
CASES["capacitor_only_loop"] = (topo(FB_OPEN, ("inp", "inp2"), ("OUT",), (("Cc", "capacitor", "OUT", "FB"),)), CROSS)

# F. 자기 바이어스 고리: 블록 A(Ma1 diode PA, Ma2 gate NB2), 블록 B(Mb1 gate PA, Mb2 diode NB2) -- 서로 gate 를 대서
#    최대 고정점에 남는다(B = {vdd, PA, NB2, gnd}). 주 블록 꼬리 Mt gate NB2. {PA, NB2} 는 L 이기도 하지만 B 먼저.
SELF_BIAS = (("Ma1", "pmos", "PA", "PA", "vdd"), ("Ma2", "nmos", "PA", "NB2", "gnd"),
             ("Mb1", "pmos", "NB2", "PA", "vdd"), ("Mb2", "nmos", "NB2", "NB2", "gnd"))
CASES["self_bias_loop"] = (
    ota5(drop=("M5",), extra=SELF_BIAS + (("Mt", "nmos", "CS", "NB2", "gnd"),)),
    ((OFF_M1M2,), (MIRROR_M3M4, DIFF_M1M2),
     (("bias_distribution", ("Ma2", "Mt"), P, ("bias_distribution", ("NB2", "gnd"), ("Mb2",), (JD,))),
      ("bias_distribution", ("Mb1",), P, ("bias_distribution", ("PA", "vdd"), ("Ma1",), (JD,))))))

# F2. 같은 회로에서 Ma2 gate 를 입력 inp3 로: 블록 A 탈락 -> 블록 B(Mb1 gate PA) 도 탈락 -> B 비어 있음, L 비어 있음.
#     (nmos, NB2, gnd) = {Mb2, Mt}, (pmos, PA, vdd) = {Ma1, Mb1} 모두 mirror_signal_cross_block.
CASES["self_bias_broken"] = (
    ota5(drop=("M5",), inputs=("inp", "inn", "inp3"),
         extra=tuple(r if r[0] != "Ma2" else ("Ma2", "nmos", "PA", "inp3", "gnd") for r in SELF_BIAS)
         + (("Mt", "nmos", "CS", "NB2", "gnd"),)),
    ((OFF_M1M2,),
     (("mirror", ("Mb2", "Mt"), D, ("mirror_signal_cross_block", ("NB2", "gnd"), ("Mb2",), (JD,))),
      MIRROR_M3M4,
      ("mirror", ("Ma1", "Mb1"), D, ("mirror_signal_cross_block", ("PA", "vdd"), ("Ma1",), (JD,))),
      DIFF_M1M2),
     ()))

# G. 한 가지 안에서 닫히는 국소 고리(diode Ma(W->X) 위·아래 Mb gate W): SCC {W, X} 는 가지 W-Ma-X-Mb-gnd 안 -> L 아님.
#    (nmos, W, gnd) = {Mb, Mc, Md}, diode Md, Mb 는 같은 블록, Mc 는 다른 블록(소비). B·L 비어 있음 -> signal_cross_block.
CASES["local_loop_excluded"] = (
    topo((("Mp", "pmos", "W", "inp", "vdd"), ("Ma", "nmos", "W", "W", "X"), ("Mb", "nmos", "X", "W", "gnd"),
          ("Md", "nmos", "W", "W", "gnd"), ("Mc", "nmos", "OUT2", "W", "gnd"), ("Mq", "pmos", "OUT2", "inp2", "vdd")),
         ("inp", "inp2"), ("OUT2",)),
    ((), (("mirror", ("Mb", "Mc", "Md"), D, ("mirror_signal_cross_block", ("W", "gnd"), ("Md",), (JD,))),), ()))

# H1. kind 가 다른 위 소자(PMOS source = NMOS 차동쌍 drain): branch_symmetric 없음.
CASES["kind_filter"] = (
    ota5(replace={"M1": ("M1", "nmos", "X1", "inp", "CS"), "M2": ("M2", "nmos", "X2", "inn", "CS")},
         extra=(("Mk1", "pmos", "D3", "vk", "X1"), ("Mk2", "pmos", "O1", "vk", "X2"))),
    ((OFF_M1M2,), (MIRROR_M3M4, DIFF_M1M2), ()))

# H2. 위 소자 source 넷이 하나뿐({Mu1, Mu2} 모두 X1 위): branch_symmetric 없음. {Mu1, Mu2} 자체는 gs 묶음 mirror.
CASES["single_source_upper"] = (
    ota5(replace={"M1": ("M1", "nmos", "X1", "inp", "CS")},
         extra=(("Mu1", "nmos", "D3", "vc", "X1"), ("Mu2", "nmos", "D3", "vc", "X1"))),
    ((OFF_M1M2,),
     (("mirror", ("Mu1", "Mu2"), D, ("mirror_whole", ("vc", "X1"), (), ())), MIRROR_M3M4, DIFF_M1M2),
     ()))

# H3. 같은 위 집합을 두 seed 가 찾음: mirror {M5, Mt1, Mt2}(먼저) 와 diff {M1, M2} 가 모두 {M1c, M2c} -> 하나만,
#     group = 먼저 찾은 mirror. mirror seed 의 M5 drain CS 위 M1/M2 는 gate 가 달라 gate 별로 source 하나 -> 무.
CASES["dedup_seed"] = (
    ota5(replace={"M1": ("M1", "nmos", "X1", "inp", "CS"), "M2": ("M2", "nmos", "X2", "inn", "CS"),
                  "M5": ("M5", "nmos", "CS", "nb", "gnd")},
         extra=(("M1c", "nmos", "D3", "vc", "X1"), ("M2c", "nmos", "O1", "vc", "X2"),
                ("Mt1", "nmos", "X1", "nb", "gnd"), ("Mt2", "nmos", "X2", "nb", "gnd"))),
    ((OFF_M1M2,),
     (("mirror", ("M5", "Mt1", "Mt2"), D, ("mirror_whole", ("nb", "gnd"), (), ())), MIRROR_M3M4, DIFF_M1M2,
      ("branch_symmetric", ("M1c", "M2c"), D, ("branch_symmetric", ("vc", "X1", "X2"), ("M5", "Mt1", "Mt2"), (JC,)))),
     ()))

# N. 음성: 레일 gate 묶음(Mr1/Mr2 gate vdd)은 mirror 아님, source 가 레일인 묶음은 차동쌍 후보 아님, gate 가 같은
#    (kind, 비레일 source) 묶음은 후보 아님(gs 묶음 -> mirror_whole). 차동쌍·형제·disposition 0.
CASES["negatives"] = (
    topo((("Mr1", "nmos", "A", "vdd", "gnd"), ("Mr2", "nmos", "B", "vdd", "gnd"),
          ("Ms1", "nmos", "A", "inp", "gnd"), ("Ms2", "nmos", "B", "inn", "gnd"),
          ("Mp1", "pmos", "A", "vb", "vdd"), ("Mp2", "pmos", "B", "vb", "vdd"),
          ("Mf1", "nmos", "E", "inp", "T"), ("Mf2", "nmos", "F", "inp", "T"), ("Mt", "nmos", "T", "vb2", "gnd"),
          ("Mf3", "pmos", "E", "vb", "vdd"), ("Mf4", "pmos", "F", "vb", "vdd")),
         ("inp", "inn"), ("A",)),
    ((),
     (("mirror", ("Mf1", "Mf2"), D, ("mirror_whole", ("inp", "T"), (), ())),
      ("mirror", ("Mf3", "Mf4", "Mp1", "Mp2"), D, ("mirror_whole", ("vb", "vdd"), (), ()))),
     ()))


@pytest.fixture(params=sorted(CASES))
def case(request):
    return request.param


# ---------------------------------------------------------------- 상수·권한·선언
def test_vocabulary_constants():
    assert (MATCH_MIRROR, MATCH_DIFF_PAIR, MATCH_BRANCH_SYMMETRIC) == ("mirror", "diff_pair", "branch_symmetric")
    assert (MIRROR_RULE_WHOLE, MIRROR_RULE_SIGNAL_CROSS_BLOCK, MIRROR_RULE_DIODE_BLOCK, MIRROR_RULE_CONSUMER_BLOCK) == (
        "mirror_whole", "mirror_signal_cross_block", "mirror_diode_block", "mirror_consumer_block")
    assert (SIBLING_RULE_ROLE, SIBLING_RULE_GROUND_GATE, SIBLING_RULE_OWN_BRANCH_GATE) == (
        "bias_sibling_dc_role", "bias_sibling_ground_gate", "bias_sibling_own_branch_gate")
    assert (DISPOSITION_BIAS_SIBLING, DISPOSITION_BIAS_DISTRIBUTION, DISPOSITION_FEEDBACK_SHARED) == (
        "bias_sibling", "bias_distribution", "feedback_shared")
    assert (J_DIFF_PAIR, J_BRANCH_SYMMETRIC, J_MATCH_CLASS) == (JB, JC, JD)
    assert REL_MATCHING_OFFSET == "matching_offset" and DOMAIN_DC_TO_SS == "dc_to_ss"
    assert (STATUS_DERIVED, STATUS_PROPOSED, STATUS_REVIEW_NEEDED) == (D, P, R)


def test_writer_table_assigns_three_fields_to_this_block():
    owners = dict(S1_WRITERS.entries)
    for f in FIELDS:
        assert owners[("graph", f)] == S1_MATCHING_GROUPS_WRITER == "s1_matching_groups"
    assert set(S1_WRITERS.fields_of(S1_MATCHING_GROUPS_WRITER)) == {("graph", f) for f in FIELDS}
    # 9절 18 (a): writer 를 s1_rel_matching 에서 옮겼다
    assert ("graph", "rel_matching_offset") not in set(S1_WRITERS.fields_of(S1_REL_MATCHING_WRITER))
    assert ("graph", "rel_matching_offset") not in set(s1_rel_matching.writes)


def test_block_declaration():
    assert isinstance(s1_matching_groups, ComputeBlock)
    assert s1_matching_groups.name == S1_MATCHING_GROUPS_WRITER
    assert set(s1_matching_groups.reads) == {
        ("graph", "branches"), ("graph", "gs_groups"),
        ("device", "dc_nets"), ("device", "dc_role"), ("device", "element_class"), ("device", "is_diode"),
        ("device", "kind"), ("device", "pins"),
        ("node", "ac_ground_class"), ("node", "is_rail"), ("node", "port_direction"),
    }
    assert set(s1_matching_groups.writes) == {("graph", f) for f in FIELDS}
    # 바이어스 형제 제외·블록 정의는 bulk·supplies 와 무관
    assert not any(f in ("bulk",) for _k, f in s1_matching_groups.reads)


def test_standalone_without_predecessors_is_keyerror():
    with pytest.raises(KeyError):
        s1_matching_groups(GraphSnapshot.empty(S1_WRITERS))


@pytest.mark.parametrize("name", NINE)
def test_fields_written_by_this_block(gh, name):
    s1 = build_s1(gh.load_lib(name), gh.supplies_for(name))
    for f in FIELDS:
        fv = s1.snapshot.field("graph", GRAPH_KEY, f)
        assert fv is not None and fv.writer == S1_MATCHING_GROUPS_WRITER
        assert isinstance(fv.value, tuple)
    assert all(isinstance(r, RelEdge) for r in gh.gval(s1, "rel_matching_offset"))
    assert all(isinstance(g, MatchingGroup) for g in gh.gval(s1, "matching_groups"))
    assert all(isinstance(g, MatchingDisposition) for g in gh.gval(s1, "matching_dispositions"))


# ---------------------------------------------------------------- 손 topology: 명시 기대값 + oracle
def test_case_explicit_expected(gh, tmp_path, case):
    raw, expected = CASES[case]
    s1 = build(gh, tmp_path, raw)
    got = plain_fields(gh, s1)
    assert got[0] == expected[0], "rel_matching_offset"
    assert got[1] == expected[1], "matching_groups"
    assert got[2] == expected[2], "matching_dispositions"


def test_case_oracle_agrees_with_explicit(case):
    # test 쪽 두 기대값(손 유도와 oracle 재구현)이 서로 맞는지 -- 기대값 자체의 자기 점검
    raw, expected = CASES[case]
    assert MatchOracle(raw).fields() == expected


def test_oracle_intermediates_on_hand_cases():
    # 정의 중간값(B·L)을 손 유도로 확인
    o = MatchOracle(CASES["bias_distribution"][0])
    assert o.B - o.o.rails == {"NB"} and o.L == frozenset()
    o = MatchOracle(CASES["feedback_shared"][0])
    assert o.B - o.o.rails == frozenset() and o.L == {"FB", "OUT"}
    o = MatchOracle(CASES["self_bias_loop"][0])
    assert o.B - o.o.rails == {"PA", "NB2"} and o.L == {"PA", "NB2"}
    o = MatchOracle(CASES["self_bias_broken"][0])
    assert o.B - o.o.rails == frozenset()
    for c in ("capacitor_only_loop", "local_loop_excluded", "signal_cross_block", "ota5", "cascode2"):
        assert MatchOracle(CASES[c][0]).L == frozenset(), c


# ---------------------------------------------------------------- status·불변량
def _status_invariants(gh, s1):
    off = gh.gval(s1, "rel_matching_offset")
    for r in off:
        assert r.type == "matching_offset" and r.domain == "dc_to_ss"
        assert r.status == (D if len(r.members) == 2 else R) and len(r.members) >= 2
        assert r.members == tuple(sorted(r.members))
        assert r.evidence.rule == "matching_offset" and r.evidence.group == () and r.evidence.basis == (JB,)
    groups = gh.gval(s1, "matching_groups")
    for g in groups:
        assert g.kind in ("mirror", "diff_pair", "branch_symmetric")
        if g.kind == "diff_pair":
            assert g.status in (D, R)
        else:
            assert g.status == D
        assert len(g.members) >= 2 and len(set(g.members)) == len(g.members)
    diffs = [g for g in groups if g.kind == "diff_pair"]
    assert [(g.members, g.status, g.evidence.nets) for g in diffs] == [(r.members, r.status, r.evidence.nets) for r in off]
    # 순서: mirror 전부 -> diff_pair 전부 -> branch_symmetric 전부
    order = {"mirror": 0, "diff_pair": 1, "branch_symmetric": 2}
    ks = [order[g.kind] for g in groups]
    assert ks == sorted(ks)
    # 같은 멤버 집합의 그룹은 둘 이상 없다(branch_symmetric 은 기존 그룹과 다를 때만 생긴다)
    bs = [frozenset(g.members) for g in groups if g.kind == "branch_symmetric"]
    others = {frozenset(g.members) for g in groups if g.kind != "branch_symmetric"}
    assert len(bs) == len(set(bs)) and not (set(bs) & others)
    disp = gh.gval(s1, "matching_dispositions")
    assert all(x.status == P for x in disp)
    kinds = [x.kind for x in disp]
    nsib = kinds.count("bias_sibling")
    assert kinds[:nsib] == ["bias_sibling"] * nsib
    assert set(kinds[nsib:]) <= {"bias_distribution", "feedback_shared"}
    for x in disp[:nsib]:
        assert len(x.members) == 1 and x.evidence.basis == (JB, JD)
    # 형제는 어느 차동쌍 후보 RelEdge 의 멤버도 아니다
    sib = {x.members[0] for x in disp[:nsib]}
    assert not (sib & {m for r in off for m in r.members})


@pytest.mark.parametrize("name", NINE)
def test_library_status_and_structure_invariants(gh, name):
    _status_invariants(gh, build_s1(gh.load_lib(name), gh.supplies_for(name)))


def test_hand_cases_status_invariants(gh, tmp_path, case):
    _status_invariants(gh, build(gh, tmp_path, CASES[case][0]))


# ---------------------------------------------------------------- 9회로: 정의 적합성(회로별 수치는 고정하지 않음)
@pytest.mark.parametrize("name", NINE)
def test_library_matches_definition_oracle(gh, name):
    # 계약 4.5a 정의를 test 쪽에서 재구현한 값과 같다. 회로 해석(J-U4/J14) 확인 전이라 수치를 따로 적지 않는다.
    raw = gh.raw(name)
    s1 = build_s1(gh.load_lib(name), gh.supplies_for(name))
    got = plain_fields(gh, s1)
    exp = MatchOracle(raw).fields()
    assert got[0] == exp[0], "rel_matching_offset"
    assert got[1] == exp[1], "matching_groups"
    assert got[2] == exp[2], "matching_dispositions"


@pytest.mark.parametrize("name", NINE)
def test_library_no_stop_and_supplies_independent(gh, name):
    # 정지 분기 없음(4.6) + reads 에 bulk 가 없으니 supplies 유무와 무관하게 같은 값
    doc = gh.load_lib(name)
    a = plain_fields(gh, build_s1(doc, gh.supplies_for(name)))
    b = plain_fields(gh, build_s1(doc, None))
    assert a == b


# ---------------------------------------------------------------- 메타모픽: 이름 치환·순서 섞기·극성 뒤집기·복제
def _maps(raw, seed):
    rng = random.Random(seed)
    nets = sorted(all_nets(raw))
    els = sorted(all_elements(raw))
    pn = nets[:]
    rng.shuffle(pn)
    pe = els[:]
    rng.shuffle(pe)
    # 새 이름 = 섞인 순번(원 이름과 겹치지 않는 접두) -> 이름순 tie-break 가 바뀐다
    netmap = {n: "q%03d" % pn.index(n) for n in nets}
    elmap = {n: "E%03d" % pe.index(n) for n in els}
    return netmap, elmap


def _check_rename(gh, tmp_path, raw, sv, seed):
    netmap, elmap = _maps(raw, seed)
    base = plain_fields(gh, build(gh, tmp_path, raw, sv, "base"))
    sv2 = None if sv is None else {netmap[k]: v for k, v in sv.items()}
    ren = plain_fields(gh, build(gh, tmp_path, rename_all(raw, netmap, elmap), sv2, "ren"))
    assert canon(ren) == canon(base, netmap, elmap)


@pytest.mark.parametrize("seed", (1, 2, 3))
def test_rename_invariance_hand_cases(gh, tmp_path, case, seed):
    _check_rename(gh, tmp_path, CASES[case][0], None, seed)


@pytest.mark.parametrize("name", NINE)
def test_rename_invariance_library(gh, tmp_path, name):
    _check_rename(gh, tmp_path, gh.raw(name), gh.supplies_for(name), 7)


@pytest.mark.parametrize("name", NINE)
def test_netlist_order_invariance_library(gh, tmp_path, name):
    raw = gh.raw(name)
    sv = gh.supplies_for(name)
    base = plain_fields(gh, build(gh, tmp_path, raw, sv, "base"))
    for seed in (11, 12, 13):
        r = copy.deepcopy(raw)
        random.Random(seed).shuffle(r["netlist"])
        random.Random(seed).shuffle(r["passive_elements"])
        assert plain_fields(gh, build(gh, tmp_path, r, sv, "shuf%d" % seed)) == base


def test_netlist_order_invariance_hand_cases(gh, tmp_path, case):
    raw = CASES[case][0]
    base = plain_fields(gh, build(gh, tmp_path, raw, None, "base"))
    r = copy.deepcopy(raw)
    r["netlist"].reverse()
    assert plain_fields(gh, build(gh, tmp_path, r, None, "rev")) == base


def _flip(raw, lo, hi):
    d = copy.deepcopy(raw)
    for e in d["netlist"]:
        e["kind"] = {"nmos": "pmos", "pmos": "nmos"}.get(e["kind"], e["kind"])
    return rename_all(d, {lo: hi, hi: lo}, {})


def test_polarity_flip_hand_cases(gh, tmp_path, case):
    raw = CASES[case][0]
    base = plain_fields(gh, build(gh, tmp_path, raw, None, "base"))
    flip = plain_fields(gh, build(gh, tmp_path, _flip(raw, "gnd", "vdd"), None, "flip"))
    assert canon(flip) == canon(base, {"vdd": "gnd", "gnd": "vdd"})


@pytest.mark.parametrize("name", NINE)
def test_polarity_flip_library(gh, tmp_path, name):
    raw = gh.raw(name)
    sv = gh.supplies_for(name)
    lo, hi = min(sv, key=sv.get), max(sv, key=sv.get)
    base = plain_fields(gh, build(gh, tmp_path, raw, None, "base"))
    flip = plain_fields(gh, build(gh, tmp_path, _flip(raw, lo, hi), None, "flip"))
    assert canon(flip) == canon(base, {lo: hi, hi: lo})


def _duplicate(raw):
    rails = set(raw["supply_nets"])
    netmap = {n: n + "_dup" for n in all_nets(raw) if n not in rails}
    elmap = {n: n + "_dup" for n in all_elements(raw)}
    a = rename_all(raw, {}, {})
    b = rename_all(raw, netmap, elmap)
    a["netlist"] += b["netlist"]
    a["passive_elements"] = (a.get("passive_elements") or []) + (b.get("passive_elements") or [])
    if a.get("ideal_sources") or b.get("ideal_sources"):
        a["ideal_sources"] = (a.get("ideal_sources") or []) + (b.get("ideal_sources") or [])
    a["ports"].update({k: v for k, v in b["ports"].items() if not k.startswith("_")})
    return a


def _kind_counts(fields):
    c = collections.Counter()
    for i, recs in enumerate(fields):
        for r in recs:
            c[(i, r[0], r[3] if i == 0 else r[2], r[4][0] if i == 0 else r[3][0])] += 1
    return c


def test_duplication_doubles_every_kind_hand_cases(gh, tmp_path, case):
    raw = CASES[case][0]
    one = _kind_counts(plain_fields(gh, build(gh, tmp_path, raw, None, "one")))
    two = _kind_counts(plain_fields(gh, build(gh, tmp_path, _duplicate(raw), None, "two")))
    assert two == collections.Counter({k: 2 * v for k, v in one.items()})


@pytest.mark.parametrize("name", NINE)
def test_duplication_doubles_every_kind_library(gh, tmp_path, name):
    raw = gh.raw(name)
    one = _kind_counts(plain_fields(gh, build(gh, tmp_path, raw, None, "one")))
    two = _kind_counts(plain_fields(gh, build(gh, tmp_path, _duplicate(raw), None, "two")))
    assert two == collections.Counter({k: 2 * v for k, v in one.items()})


# ---------------------------------------------------------------- 결정론: 프로세스·PYTHONHASHSEED
_DET = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from gmid_engine.authoring import load_topology
from gmid_engine.graph import GRAPH_KEY, build_s1
out = {}
for p in sys.argv[2:]:
    s1 = build_s1(load_topology(p), None)
    out[p] = [repr(s1.value("graph", GRAPH_KEY, f)) for f in ("rel_matching_offset", "matching_groups", "matching_dispositions")]
print(json.dumps(out, sort_keys=True))
"""


def test_deterministic_across_hash_seeds(gh, tmp_path):
    paths = [str(gh.LIBRARY / (n + ".topology.json")) for n in NINE]
    paths += [gh.write(tmp_path, CASES[c][0], "det_" + c) for c in sorted(CASES)]
    res = []
    for seed in ("0", "1", "4242"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run([sys.executable, "-c", _DET, str(gh.SKILL_DIR)] + paths,
                           capture_output=True, text=True, env=env, check=True)
        res.append(json.loads(r.stdout))
    assert res[0] == res[1] == res[2]
