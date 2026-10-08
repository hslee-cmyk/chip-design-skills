"""graph/matching_groups.py -- `s1_matching_groups`: 레이아웃 matching 분류(계약 4.5a, 4.5 표 matching_offset 행, 9절 18번).

근거는 계약 문장뿐이다(graph 소스 미열람). 기대값 두 갈래:
- 손으로 만든 작은 topology 마다 계약 정의를 손으로 따라가 적은 **명시 기대값**(아래 각 test 주석에 유도).
- 이 파일의 `MatchOracle`(topology JSON 만 읽는 test 쪽 재구현, U2~U3 는 `graph_u2_oracle.U2Oracle`)과의 대조.

9회로: 계약 4.5a 는 회로별 수치를 '기대값이 아니라 작성자 실행값'(J-U4 대조표 / J14 사용자 확인 전)이라 했으므로 회로별
분류 수·멤버를 기대값으로 고정하지 않는다. 9회로에는 정의 적합성(oracle 대조)·불변량(권한·status·결정론·치환·복제)만 건다.
예외: 사용자가 2026-10-08 ratify 한 행(J14 파일럿 분리·판단 7·M7 꼬리·ngcc {M8, M14})은 oracle (d) 로 `RATIFIED` 에 고정한다.
`MatchOracle(split=True)` 는 2026-10-08 '소비 소자 세분'(꼬리·diode 공급·대칭쌍, 대응 넷 사상)까지 담은 현재 정의,
`split=False` 는 그 이전 정의(세분이 걸리지 않는 회로의 무동작 대조용)다.
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
def topo(netlist, inputs, outputs, passives=(), rails=("vdd", "gnd"), name="syn", bias=()):
    """netlist = ((이름, kind, drain, gate, source), ...), passives = ((이름, kind, t0, t1), ...).
    bias = authoring CONTRACT 9절 `bias_inputs`(gate 전용 넷) -- 회로마다 손으로 정한 리터럴(입력 선언), 비면 키 없음."""
    ports = {n: {"direction": "input", "role": "signal"} for n in inputs}
    ports.update({n: {"direction": "output", "role": "signal"} for n in outputs})
    d = {
        "schema_version": "2.0",
        "topology_name": name,
        "supply_nets": list(rails),
        "netlist": [{"name": n, "kind": k, "drain": d, "gate": g, "source": s} for n, k, d, g, s in netlist],
        "passive_elements": [{"name": n, "kind": k, "terminals": [a, b]} for n, k, a, b in passives],
        "ports": ports,
    }
    if bias:
        d["bias_inputs"] = list(bias)
    return d


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
    if "bias_inputs" in d:                                   # authoring 9절 선언도 같은 넷 치환(이름 치환의 일부)
        d["bias_inputs"] = [f(n) for n in d["bias_inputs"]]
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

    def __init__(self, raw, split=True):
        # split=False: 2026-10-08 세분(꼬리·diode 공급·대칭쌍) 이전 정의 -- '세분이 걸리지 않는 회로는 불변' 대조용
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
        # 꼬리 넷(derived 차동쌍 공통 source)·diode 넷·대응 넷 사상 (계약 4.5a 용어표)
        self.tail_nets = frozenset(r[4][1][0] for r in self.offset if r[3] == D)
        self.diode_nets = frozenset(mos[m]["gate"] for m in diodes)
        self.partner = self._corresponding_nets() if split else {}
        partner = self.partner
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
                # 꼬리: drain ∈ 꼬리 넷인 소비 소자(블록 크기 무관, 묶음 전체)
                tails = tuple(m for m in consumers if split and mos[m]["drain"] in self.tail_nets)
                per = collections.defaultdict(list)
                for m in consumers:
                    per[blk_of(m)].append(m)
                for ms in sorted(tuple(v) for v in per.values() if len(v) >= 2):
                    if not split:
                        groups.append(("mirror", ms, D, ("mirror_consumer_block", (g, s), dm, (JD,))))
                        continue
                    btails = [m for m in ms if m in tails]
                    rest = [m for m in ms if m not in tails]
                    supply = [m for m in rest if mos[m]["drain"] in self.diode_nets]
                    opened = [m for m in rest if m not in supply]
                    by_drain = collections.defaultdict(list)
                    for m in opened:
                        by_drain[mos[m]["drain"]].append(m)
                    sym = []
                    for a in sorted(by_drain):
                        b = partner.get(a)
                        if b is None or not a < b or b not in by_drain:
                            continue
                        if len(by_drain[a]) == 1 and len(by_drain[b]) == 1:
                            sym.append(("mirror", tuple(sorted((by_drain[a][0], by_drain[b][0]))), D,
                                        ("mirror_consumer_symmetric", (g, s, a, b), dm, (JD,))))
                    sym.sort(key=lambda x: x[1])
                    groups.extend(sym)
                    in_sym = {m for x in sym for m in x[1]}
                    left = tuple(m for m in opened if m not in in_sym)
                    if not (btails or supply or sym):
                        groups.append(("mirror", ms, D, ("mirror_consumer_block", (g, s), dm, (JD,))))
                    elif len(left) >= 2:
                        groups.append(("mirror", left, D, ("mirror_consumer_block", (g, s), dm, (JD,))))
                if tails:
                    groups.append(("mirror", tuple(sorted(dm + tails)), D, ("mirror_tail_ratio", (g, s), dm, (JD,))))
                kept = tuple(m for m in consumers if m not in tails)
                if kept:
                    kind = "bias_distribution" if g in self.B else "feedback_shared"
                    disp.append((kind, kept, P, (kind, (g, s), dm, (JD,))))
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

    def _corresponding_nets(self):
        """계약 4.5a '대응 넷 사상' 문장 그대로: seed -> 같은 서명 열 쌍 확장(고정점), 레일 제외, 충돌 넷 제거."""
        o, mos, rails = self.o, self.o.mos, self.o.rails

        def esig(el):
            # segment 서명 원소 = (element_class, kind). test 쪽은 분류를 (MOS/수동/이상원) 범주로 대신한다 -- 서명은
            # 같음 비교에만 쓰이므로 범주·kind 가 같으면 같은 값이면 충분하다.
            if el in mos:
                return ("mos", mos[el]["kind"])
            if el in o.passives:
                return ("passive", o.passives[el]["kind"])
            return ("source", o.sources[el]["kind"])

        seqs = []
        for bid, ends, segs, _src in o.branches:
            cur, nets, sig = ends[0], [ends[0]], []
            for (a, b), els in segs:
                cur = b if a == cur else a
                nets.append(cur)
                sig.append(tuple(sorted(esig(el) for el in els)))
            assert cur == ends[1]
            seqs.append((bid, tuple(nets), tuple(sig)))
            seqs.append((bid, tuple(reversed(nets)), tuple(reversed(sig))))
        partner, conflict = {}, set()

        def add(a, b):
            pa, pb = partner.get(a), partner.get(b)
            if (pa is not None and pa != b) or (pb is not None and pb != a):
                bad = {a, b} | ({pa, pb} - {None})
                conflict.update(bad)
                for n in bad:
                    partner.pop(n, None)
                return
            if a not in conflict and b not in conflict:
                partner[a], partner[b] = b, a

        for r in self.offset:
            if r[3] == D and len(r[2]) == 2:
                a, b = (mos[m]["drain"] for m in r[2])
                if a != b and a not in rails and b not in rails:
                    add(a, b)
        changed = True
        while changed:
            changed = False
            for i, (bi, ni, si) in enumerate(seqs):
                for bj, nj, sj in seqs[i + 1:]:
                    if bi == bj or si != sj:
                        continue
                    last, ok, anchored, new = len(ni) - 1, True, False, []
                    for p, (x, y) in enumerate(zip(ni, nj)):
                        if x == y:
                            if p not in (0, last):
                                ok = False
                                break
                            continue
                        if x in rails or y in rails or x in conflict or y in conflict:
                            ok = False
                            break
                        px, py = partner.get(x), partner.get(y)
                        if (px is not None and px != y) or (py is not None and py != x):
                            ok = False
                            break
                        if px == y:
                            anchored = True
                        else:
                            new.append((x, y))
                    if ok and anchored and new:
                        for x, y in new:
                            add(x, y)
                        changed = True
        return {a: b for a, b in partner.items() if a not in conflict and b not in conflict}


# ---------------------------------------------------------------- 손 topology
# 5T OTA: M1/M2 차동쌍(CS), M3 diode + M4 PMOS 미러, M5 꼬리(gate vb = gate 전용 -> G)
OTA5 = (
    ("M1", "nmos", "D3", "inp", "CS"),
    ("M2", "nmos", "O1", "inn", "CS"),
    ("M3", "pmos", "D3", "D3", "vdd"),
    ("M4", "pmos", "O1", "D3", "vdd"),
    ("M5", "nmos", "CS", "vb", "gnd"),
)


def ota5(extra=(), drop=(), replace=None, passives=(), inputs=("inp", "inn"), outputs=("O1",), bias=()):
    """bias: 케이스마다 손으로 정한 gate 전용 넷(authoring 9절) -- 기본 몸통만이면 vb(M5 gate)."""
    rows = [r for r in OTA5 if r[0] not in drop]
    if replace:
        rows = [replace.get(r[0], r) for r in rows]
    return topo(rows + list(extra), inputs, outputs, passives, bias=bias)


MIRROR_M3M4 = ("mirror", ("M3", "M4"), D, ("mirror_whole", ("D3", "vdd"), ("M3",), ()))
OFF_M1M2 = ("matching_offset", "dc_to_ss", ("M1", "M2"), D, ("matching_offset", ("CS", "inn", "inp"), (), (JB,)))
DIFF_M1M2 = ("diff_pair", ("M1", "M2"), D, ("diff_pair", ("CS", "inn", "inp"), (), (JB,)))

CASES = {}

# A. 기본 5T: 한 블록(CS 공유) -> 소비 소자 없음 -> mirror_whole. 차동쌍 M1/M2 derived. 위 소자 없음.
CASES["ota5"] = (ota5(bias=["vb"]), ((OFF_M1M2,), (MIRROR_M3M4, DIFF_M1M2), ()))      # vb: M5 gate

# B. 2단 NMOS 캐스코드: diff seed -> {M1c, M2c}(gate vc1, source X1/X2) -> 다시 seed -> {M1d, M2d}(gate vc2).
CASES["cascode2"] = (
    ota5(replace={"M1": ("M1", "nmos", "X1", "inp", "CS"), "M2": ("M2", "nmos", "X2", "inn", "CS")},
         extra=(("M1c", "nmos", "Y1", "vc1", "X1"), ("M2c", "nmos", "Y2", "vc1", "X2"),
                ("M1d", "nmos", "D3", "vc2", "Y1"), ("M2d", "nmos", "O1", "vc2", "Y2")),
         bias=["vb", "vc1", "vc2"]),                                       # vb: M5, vc1: M1c·M2c, vc2: M1d·M2d gate
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
         passives=(("Ryd", "resistor", "vdd", "Yd"), ("Rz", "resistor", "vdd", "Z"), ("Rq", "resistor", "vdd", "P")),
         bias=["vb"]),                                                     # vb: M5·Mg gate (P 는 Mq drain·Rq 단자)
    ((OFF_M1M2,), (MIRROR_M3M4, DIFF_M1M2),
     (("bias_sibling", ("Md",), P, ("bias_sibling_dc_role", ("CS", "Yd"), ("M1", "M2"), (JB, JD))),
      ("bias_sibling", ("Mg",), P, ("bias_sibling_ground_gate", ("CS", "vb"), ("M1", "M2"), (JB, JD))),
      ("bias_sibling", ("Mo",), P, ("bias_sibling_own_branch_gate", ("CS", "P"), ("M1", "M2"), (JB, JD))))))

# C2. 검사 순서: gate 가 G(vb) 이고 같은 gs 묶음(nmos, vb, CS)인 Mg/Mh 는 dc_role(2)=bias 라 rule 은 dc_role(ground_gate 아님).
CASES["sibling_order"] = (
    ota5(extra=(("Mg", "nmos", "Z", "vb", "CS"), ("Mh", "nmos", "Z2", "vb", "CS")),
         passives=(("Rz", "resistor", "vdd", "Z"), ("Rz2", "resistor", "vdd", "Z2")), bias=["vb"]),   # vb: M5·Mg·Mh gate
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
         ("inp",), ("D3",), (("Rz", "resistor", "vdd", "Z"),), bias=["vb"]),                      # vb: Mg·M5 gate
    ((), (), (("bias_sibling", ("Mg",), P, ("bias_sibling_ground_gate", ("CS", "vb"), ("M1",), (JB, JD))),)))

# C4. 남은 멤버 3(gate 셋 다름) -> review_needed. review_needed diff_pair 는 seed 가 아니라 그 위 캐스코드쌍도 안 생긴다.
CASES["offset3_review"] = (
    topo((("M1", "nmos", "X1", "inp", "CS"), ("M2", "nmos", "X2", "inn", "CS"), ("Mx", "nmos", "O2", "inx", "CS"),
          ("M1c", "nmos", "D3", "vc", "X1"), ("M2c", "nmos", "O1", "vc", "X2"),
          ("M3", "pmos", "D3", "D3", "vdd"), ("M4", "pmos", "O1", "D3", "vdd"), ("M6", "pmos", "O2", "D3", "vdd"),
          ("M5", "nmos", "CS", "vb", "gnd")),
         ("inp", "inn", "inx"), ("O1",), bias=["vb", "vc"]),                                     # vc: M1c·M2c, vb: M5 gate
    ((("matching_offset", "dc_to_ss", ("M1", "M2", "Mx"), R,
       ("matching_offset", ("CS", "inn", "inp", "inx"), (), (JB,))),),
     (("mirror", ("M3", "M4", "M6"), D, ("mirror_whole", ("D3", "vdd"), ("M3",), ())),
      ("diff_pair", ("M1", "M2", "Mx"), R, ("diff_pair", ("CS", "inn", "inp", "inx"), (), (JB,)))),
     ()))

# D. bias_distribution: 바이어스 블록 vdd-Rb-NB-(Mb∥Mb2)-gnd(입력·비diode MOS 없음 -> B 에 NB).
#    gs (nmos, NB, gnd) = M5, M7, M8, Mb, Mb2; diode Mb/Mb2 -> 소비 = M5(주 블록), M7/M8(2단 블록).
#    gate ∈ B -> diode 쪽 {Mb, Mb2} mirror_diode_block. 소비 세분(2026-10-08): M5 drain CS = derived 차동쌍 {M1, M2} 의
#    공통 source(꼬리 넷) -> 꼬리(주 블록에 혼자여도, 판단 7) -> mirror_tail_ratio {M5, Mb, Mb2}(diode + 꼬리, 이름순), 묶음 끝.
#    2단 블록 {M7, M8}: 꼬리·diode 공급(drain OUT 은 diode 넷 아님)·대칭쌍(OUT 은 짝 없음) 모두 없음 -> 옛 규칙 consumer_block.
#    disposition = 소비 - 꼬리 = {M7, M8}.  [oracle (a): 계약 4.5a 정의를 손으로 적용한 구성 입력]
CASES["bias_distribution"] = (
    ota5(replace={"M5": ("M5", "nmos", "CS", "NB", "gnd")},
         extra=(("Mb", "nmos", "NB", "NB", "gnd"), ("Mb2", "nmos", "NB", "NB", "gnd"),
                ("M6", "pmos", "OUT", "O1", "vdd"), ("M7", "nmos", "OUT", "NB", "gnd"), ("M8", "nmos", "OUT", "NB", "gnd")),
         passives=(("Rb", "resistor", "vdd", "NB"),), outputs=("OUT",)),
    ((OFF_M1M2,),
     (("mirror", ("Mb", "Mb2"), D, ("mirror_diode_block", ("NB", "gnd"), ("Mb", "Mb2"), (JD,))),
      ("mirror", ("M7", "M8"), D, ("mirror_consumer_block", ("NB", "gnd"), ("Mb", "Mb2"), (JD,))),
      ("mirror", ("M5", "Mb", "Mb2"), D, ("mirror_tail_ratio", ("NB", "gnd"), ("Mb", "Mb2"), (JD,))),
      MIRROR_M3M4, DIFF_M1M2),
     (("bias_distribution", ("M7", "M8"), P, ("bias_distribution", ("NB", "gnd"), ("Mb", "Mb2"), (JD,))),)))

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
#    세분(2026-10-08): (nmos, NB2, gnd) = {Ma2, Mb2, Mt}, diode Mb2. Mt drain CS = 꼬리 넷 -> mirror_tail_ratio {Mb2, Mt};
#    Ma2 는 블록 A 에 혼자(꼬리 아님) -> bias_distribution (Ma2,). (pmos, PA, vdd) 의 Mb1(drain NB2, 꼬리 아님) -> (Mb1,).
#    [oracle (a): 계약 4.5a 정의를 손으로 적용]
SELF_BIAS = (("Ma1", "pmos", "PA", "PA", "vdd"), ("Ma2", "nmos", "PA", "NB2", "gnd"),
             ("Mb1", "pmos", "NB2", "PA", "vdd"), ("Mb2", "nmos", "NB2", "NB2", "gnd"))
CASES["self_bias_loop"] = (
    ota5(drop=("M5",), extra=SELF_BIAS + (("Mt", "nmos", "CS", "NB2", "gnd"),)),
    ((OFF_M1M2,),
     (("mirror", ("Mb2", "Mt"), D, ("mirror_tail_ratio", ("NB2", "gnd"), ("Mb2",), (JD,))),   # gs 묶음 (nmos, NB2, gnd) 먼저
      MIRROR_M3M4, DIFF_M1M2),
     (("bias_distribution", ("Ma2",), P, ("bias_distribution", ("NB2", "gnd"), ("Mb2",), (JD,))),
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
         extra=(("Mk1", "pmos", "D3", "vk", "X1"), ("Mk2", "pmos", "O1", "vk", "X2")), bias=["vb", "vk"]),  # vb: M5, vk: Mk1·Mk2
    ((OFF_M1M2,), (MIRROR_M3M4, DIFF_M1M2), ()))

# H2. 위 소자 source 넷이 하나뿐({Mu1, Mu2} 모두 X1 위): branch_symmetric 없음. {Mu1, Mu2} 자체는 gs 묶음 mirror.
CASES["single_source_upper"] = (
    ota5(replace={"M1": ("M1", "nmos", "X1", "inp", "CS")},
         extra=(("Mu1", "nmos", "D3", "vc", "X1"), ("Mu2", "nmos", "D3", "vc", "X1")), bias=["vb", "vc"]),  # vb: M5, vc: Mu1·Mu2
    ((OFF_M1M2,),
     (("mirror", ("Mu1", "Mu2"), D, ("mirror_whole", ("vc", "X1"), (), ())), MIRROR_M3M4, DIFF_M1M2),
     ()))

# H3. 같은 위 집합을 두 seed 가 찾음: mirror {M5, Mt1, Mt2}(먼저) 와 diff {M1, M2} 가 모두 {M1c, M2c} -> 하나만,
#     group = 먼저 찾은 mirror. mirror seed 의 M5 drain CS 위 M1/M2 는 gate 가 달라 gate 별로 source 하나 -> 무.
CASES["dedup_seed"] = (
    ota5(replace={"M1": ("M1", "nmos", "X1", "inp", "CS"), "M2": ("M2", "nmos", "X2", "inn", "CS"),
                  "M5": ("M5", "nmos", "CS", "nb", "gnd")},
         extra=(("M1c", "nmos", "D3", "vc", "X1"), ("M2c", "nmos", "O1", "vc", "X2"),
                ("Mt1", "nmos", "X1", "nb", "gnd"), ("Mt2", "nmos", "X2", "nb", "gnd")),
         bias=["nb", "vc"]),                                               # nb: M5·Mt1·Mt2, vc: M1c·M2c gate
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
         ("inp", "inn"), ("A",), bias=["vb", "vb2"]),                       # vb: Mp1·Mp2·Mf3·Mf4, vb2: Mt gate
    ((),
     (("mirror", ("Mf1", "Mf2"), D, ("mirror_whole", ("inp", "T"), (), ())),
      ("mirror", ("Mf3", "Mf4", "Mp1", "Mp2"), D, ("mirror_whole", ("vb", "vdd"), (), ()))),
     ()))


# ---- 소비 소자 세분(계약 4.5a '소비 소자 세분', 사용자 ratify 2026-10-08 J14 1번·판단 7·M7 결정) 손 topology.
#      기대값은 모두 oracle (a): 계약 정의를 손으로 적용한 구성 입력. 각 주석이 유도다.
TAIL = "mirror_tail_ratio"
SYM = "mirror_consumer_symmetric"

# S1. 루프 신호 gate 로 구동되는 꼬리(M7 결정): 5T 의 꼬리 M5 gate = FB, FB 블록 vdd-Mfp(gate O1)-FB-Md(diode)-gnd.
#     영향 고리 CS->D3(M1 s->d)->O1(M4 g->d)->FB(Mfp g->d)->CS(M5 g->d) = SCC {CS, D3, O1, FB}, 두 블록에 걸침 -> L.
#     B: FB 블록의 Mfp gate O1 은 주 블록(입력 포함, 탈락) 넷이라 둘째 반복에서 탈락 -> B = 레일뿐. 따라서 (nmos, FB, gnd)
#     묶음은 옛 규칙이면 feedback_shared (M5,). 새 규칙: M5 drain CS = derived 차동쌍 {M1, M2} 꼬리 넷 -> mirror_tail_ratio
#     {M5, Md}, disposition 에서 빠져 기록 없음(빈 기록 금지).
CASES["tail_loop_gate"] = (
    ota5(replace={"M5": ("M5", "nmos", "CS", "FB", "gnd")},
         extra=(("Md", "nmos", "FB", "FB", "gnd"), ("Mfp", "pmos", "FB", "O1", "vdd"))),
    ((OFF_M1M2,),
     (("mirror", ("M5", "Md"), D, (TAIL, ("FB", "gnd"), ("Md",), (JD,))), MIRROR_M3M4, DIFF_M1M2),
     ()))

# S2. 세분 전부: NMOS 차동쌍 M1/M2(drain X1/X2) -> 대응 넷 seed X1<->X2. 바이어스 블록 vdd-Rnr-NB-Nr(diode)-gnd,
#     vdd-Pr(diode)-PB-Rpr-gnd (입력·비diode MOS 없음 -> B = {NB, PB} + 레일).
#     (nmos, NB, gnd) = {Nr, Ye}: Ye drain CS = 꼬리 넷 -> tail_ratio {Nr, Ye}(주 블록에 혼자), 남는 소비 소자 없음 -> 기록 없음.
#     (pmos, PB, vdd) = {Pa, Pb, Pe, Pf, Pg, Pr}: 소비 Pa·Pb(주 블록), Pe·Pf·Pg(2단 블록: Rl 이 OUT-DN 을 이어 한 블록).
#       주 블록: Pa(X1)·Pb(X2) 열린 소자, drain 이 짝 (X1, X2)이고 각 drain 에 하나씩 -> consumer_symmetric (PB, vdd, X1, X2).
#       2단 블록: Pe drain DN = diode Mn 의 넷 -> diode 공급(그룹 없음). Pf·Pg 열린 소자 drain 모두 OUT(짝 없음) ->
#       세분 요소(diode 공급)가 있으므로 남은 열린 소자 2개 -> consumer_block {Pf, Pg}.
#       블록 순서 = 소비 멤버 순(주 (Pa, Pb) < 2단 (Pe, Pf, Pg)). 꼬리 없음. disposition = 소비 전부 {Pa, Pb, Pe, Pf, Pg}.
#     L: {OUT, DN} 고리는 저항 Rl 뿐(MOS 엣지 없음) -> L = 빈 집합. 2단 블록은 Mo gate X1(주 블록)라 바이어스 아님.
SPLIT = (
    ("M1", "nmos", "X1", "inp", "CS"), ("M2", "nmos", "X2", "inn", "CS"),
    ("Ye", "nmos", "CS", "NB", "gnd"), ("Nr", "nmos", "NB", "NB", "gnd"),
    ("Pr", "pmos", "PB", "PB", "vdd"), ("Pa", "pmos", "X1", "PB", "vdd"), ("Pb", "pmos", "X2", "PB", "vdd"),
)
SPLIT_R = (("Rnr", "resistor", "vdd", "NB"), ("Rpr", "resistor", "PB", "gnd"))
OFF_SPLIT = ("matching_offset", "dc_to_ss", ("M1", "M2"), D, ("matching_offset", ("CS", "inn", "inp"), (), (JB,)))
DIFF_SPLIT = ("diff_pair", ("M1", "M2"), D, ("diff_pair", ("CS", "inn", "inp"), (), (JB,)))
TAIL_YE = ("mirror", ("Nr", "Ye"), D, (TAIL, ("NB", "gnd"), ("Nr",), (JD,)))
CASES["split_block"] = (
    topo(SPLIT + (("Pe", "pmos", "DN", "PB", "vdd"), ("Mn", "nmos", "DN", "DN", "gnd"),
                  ("Pf", "pmos", "OUT", "PB", "vdd"), ("Pg", "pmos", "OUT", "PB", "vdd"), ("Mo", "nmos", "OUT", "X1", "gnd")),
         ("inp", "inn"), ("OUT",), SPLIT_R + (("Rl", "resistor", "OUT", "DN"),)),
    ((OFF_SPLIT,),
     (TAIL_YE,
      ("mirror", ("Pa", "Pb"), D, (SYM, ("PB", "vdd", "X1", "X2"), ("Pr",), (JD,))),
      ("mirror", ("Pf", "Pg"), D, ("mirror_consumer_block", ("PB", "vdd"), ("Pr",), (JD,))),
      DIFF_SPLIT),
     (("bias_distribution", ("Pa", "Pb", "Pe", "Pf", "Pg"), P, ("bias_distribution", ("PB", "vdd"), ("Pr",), (JD,))),)))

# N1 (음성). 대칭쌍은 '각 drain 에 열린 소비 소자가 정확히 하나'일 때만: Pa·Pa2 둘 다 X1 -> 대칭쌍 없음. 그 블록에 꼬리
#     (Ye 는 다른 묶음)·diode 공급도 없음 -> 옛 규칙 그대로 블록 전체 consumer_block {Pa, Pa2, Pb}.
CASES["symmetric_needs_one_per_drain"] = (
    topo(SPLIT + (("Pa2", "pmos", "X1", "PB", "vdd"),), ("inp", "inn"), ("X2",), SPLIT_R),
    ((OFF_SPLIT,),
     (TAIL_YE,
      ("mirror", ("Pa", "Pa2", "Pb"), D, ("mirror_consumer_block", ("PB", "vdd"), ("Pr",), (JD,))),
      DIFF_SPLIT),
     (("bias_distribution", ("Pa", "Pa2", "Pb"), P, ("bias_distribution", ("PB", "vdd"), ("Pr",), (JD,))),)))

# N2 (음성). 꼬리 넷은 status derived 차동쌍만: 3멤버 review_needed 후보(C4 와 같은 몸통)의 공통 source CS 를 바이어스
#     블록 gate NB 로 받는 M5 는 꼬리가 아니다 -> 혼자인 소비 소자 = bias_distribution (M5,)만, 그룹 없음.
#     review_needed 는 대응 넷 seed 도 아니다(seed = derived 2멤버).
CASES["tail_needs_derived_pair"] = (
    topo((("M1", "nmos", "X1", "inp", "CS"), ("M2", "nmos", "X2", "inn", "CS"), ("Mx", "nmos", "O2", "inx", "CS"),
          ("M1c", "nmos", "D3", "vc", "X1"), ("M2c", "nmos", "O1", "vc", "X2"),
          ("M3", "pmos", "D3", "D3", "vdd"), ("M4", "pmos", "O1", "D3", "vdd"), ("M6", "pmos", "O2", "D3", "vdd"),
          ("M5", "nmos", "CS", "NB", "gnd"), ("Mb", "nmos", "NB", "NB", "gnd")),
         ("inp", "inn", "inx"), ("O1",), (("Rb", "resistor", "vdd", "NB"),), bias=["vc"]),       # vc: M1c·M2c gate
    ((("matching_offset", "dc_to_ss", ("M1", "M2", "Mx"), R,
       ("matching_offset", ("CS", "inn", "inp", "inx"), (), (JB,))),),
     (("mirror", ("M3", "M4", "M6"), D, ("mirror_whole", ("D3", "vdd"), ("M3",), ())),
      ("diff_pair", ("M1", "M2", "Mx"), R, ("diff_pair", ("CS", "inn", "inp", "inx"), (), (JB,)))),
     (("bias_distribution", ("M5",), P, ("bias_distribution", ("NB", "gnd"), ("Mb",), (JD,))),)))

# N3 (음성). 충돌 넷은 사상에서 빠진다: 두 derived 차동쌍 {M1, M2}(X1, X2)·{M1b, M3b}(X1, X3)가 X1 을 함께 쓴다 ->
#     seed X1<->X2 뒤 X1<->X3 -> X1·X2·X3 충돌 -> 사상 비어 있음 -> Pa·Pb·Pc 대칭쌍 없음 -> consumer_block {Pa, Pb, Pc}.
#     (nmos, NB, gnd) = {Nr, Ye, Yf}: Ye(CS)·Yf(CS2) 모두 꼬리 -> tail_ratio {Nr, Ye, Yf}, 남은 소비 없음 -> 기록 없음.
#     branch_symmetric: tail 그룹 seed 의 Ye·Yf drain 위 nmos = M1, M2(CS 위)·M1b, M3b(CS2 위) -> gate inp 에 {M1, M1b}
#     (source CS, CS2 둘) / gate inn 에 {M2, M3b} -> 새 그룹 둘(gate 넷 순: inn < inp).
CASES["conflicting_pairs_dropped"] = (
    topo((("M1", "nmos", "X1", "inp", "CS"), ("M2", "nmos", "X2", "inn", "CS"),
          ("M1b", "nmos", "X1", "inp", "CS2"), ("M3b", "nmos", "X3", "inn", "CS2"),
          ("Ye", "nmos", "CS", "NB", "gnd"), ("Yf", "nmos", "CS2", "NB", "gnd"), ("Nr", "nmos", "NB", "NB", "gnd"),
          ("Pr", "pmos", "PB", "PB", "vdd"), ("Pa", "pmos", "X1", "PB", "vdd"), ("Pb", "pmos", "X2", "PB", "vdd"),
          ("Pc", "pmos", "X3", "PB", "vdd")),
         ("inp", "inn"), ("X2",), SPLIT_R),
    ((OFF_SPLIT,
      ("matching_offset", "dc_to_ss", ("M1b", "M3b"), D, ("matching_offset", ("CS2", "inn", "inp"), (), (JB,)))),
     (("mirror", ("Nr", "Ye", "Yf"), D, (TAIL, ("NB", "gnd"), ("Nr",), (JD,))),
      ("mirror", ("Pa", "Pb", "Pc"), D, ("mirror_consumer_block", ("PB", "vdd"), ("Pr",), (JD,))),
      DIFF_SPLIT,
      ("diff_pair", ("M1b", "M3b"), D, ("diff_pair", ("CS2", "inn", "inp"), (), (JB,))),
      ("branch_symmetric", ("M2", "M3b"), D, ("branch_symmetric", ("inn", "CS", "CS2"), ("Nr", "Ye", "Yf"), (JC,))),
      ("branch_symmetric", ("M1", "M1b"), D, ("branch_symmetric", ("inp", "CS", "CS2"), ("Nr", "Ye", "Yf"), (JC,)))),
     (("bias_distribution", ("Pa", "Pb", "Pc"), P, ("bias_distribution", ("PB", "vdd"), ("Pr",), (JD,))),)))


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


# ---------------------------------------------------------------- 소비 소자 세분 (2026-10-08): 중간값·불변량·ratified 값
def test_split_intermediates_on_hand_cases():
    # 대응 넷 사상·꼬리 넷을 손 유도로 확인 (oracle (a): 각 CASES 주석의 유도)
    o = MatchOracle(CASES["split_block"][0])
    assert o.partner == {"X1": "X2", "X2": "X1"} and o.tail_nets == {"CS"} and o.L == frozenset()
    assert o.B - o.o.rails == {"NB", "PB"}
    o = MatchOracle(CASES["conflicting_pairs_dropped"][0])
    assert o.partner == {} and o.tail_nets == {"CS", "CS2"}
    o = MatchOracle(CASES["tail_needs_derived_pair"][0])
    assert o.partner == {} and o.tail_nets == frozenset()
    o = MatchOracle(CASES["tail_loop_gate"][0])
    assert o.B - o.o.rails == frozenset() and o.L == {"CS", "D3", "O1", "FB"} and o.tail_nets == {"CS"}
    # 레일은 짝이 되지 않는다: 5T 의 seed D3<->O1 뿐, 레일 vdd/gnd 는 사상에 없다
    o = MatchOracle(CASES["ota5"][0])
    assert o.partner == {"D3": "O1", "O1": "D3"}


def test_split_changes_only_split_kinds_on_hand_cases():
    # 세분이 걸리지 않는 손 회로(꼬리·대칭쌍 조건 없음)는 옛 정의와 결과가 같다(무동작)
    for c in ("ota5", "cascode2", "siblings3", "sibling_order", "sibling_leaves_one", "offset3_review", "feedback_shared",
              "signal_cross_block", "capacitor_only_loop", "self_bias_broken", "local_loop_excluded", "kind_filter",
              "single_source_upper", "dedup_seed", "negatives", "tail_needs_derived_pair"):
        assert MatchOracle(CASES[c][0]).fields() == MatchOracle(CASES[c][0], split=False).fields(), c
    # 걸리는 회로는 옛 정의와 다르다(세분이 실제로 동작함을 확인 -- 테스트가 공허하지 않음)
    for c in ("bias_distribution", "self_bias_loop", "tail_loop_gate", "split_block", "symmetric_needs_one_per_drain",
              "conflicting_pairs_dropped"):
        assert MatchOracle(CASES[c][0]).fields() != MatchOracle(CASES[c][0], split=False).fields(), c


def _split_invariants(gh, s1, raw):
    """세분 불변량(계약 4.5a 문장). drain·diode 는 topology JSON 에서 직접 읽는다."""
    mos = {e["name"]: e for e in raw["netlist"]}
    diode_nets = {e["gate"] for e in mos.values() if e["gate"] == e["drain"]}
    off = gh.gval(s1, "rel_matching_offset")
    tail_nets = {r.evidence.nets[0] for r in off if r.status == D}
    groups = gh.gval(s1, "matching_groups")
    disp = gh.gval(s1, "matching_dispositions")
    tails = set()
    for g in groups:
        if g.evidence.rule == TAIL:
            dm = g.evidence.group
            rest = [m for m in g.members if m not in dm]
            assert g.members == tuple(sorted(g.members)) and dm and set(dm) <= set(g.members)
            assert all(mos[m]["gate"] == mos[m]["drain"] for m in dm)
            assert rest and all(mos[m]["drain"] in tail_nets for m in rest)      # 꼬리 = drain ∈ 꼬리 넷
            assert all(mos[m]["gate"] == g.evidence.nets[0] and mos[m]["source"] == g.evidence.nets[1] for m in g.members)
            tails |= set(rest)
        if g.evidence.rule == SYM:
            gate, src, a, b = g.evidence.nets
            assert a < b and len(g.members) == 2
            assert {mos[m]["drain"] for m in g.members} == {a, b}
            assert all(mos[m]["gate"] == gate and mos[m]["source"] == src for m in g.members)
            assert not ({a, b} & diode_nets) and not ({a, b} & tail_nets)
    for x in disp:
        assert x.members, "빈 disposition 기록 금지"
        if x.kind in ("bias_distribution", "feedback_shared"):
            assert not (set(x.members) & tails), "꼬리는 disposition 에서 빠진다"
    # 한 gs 묶음 안 순서: diode_block -> (symmetric·consumer_block) -> tail_ratio
    rank = {"mirror_diode_block": 0, SYM: 1, "mirror_consumer_block": 1, TAIL: 2}
    by_bundle = collections.defaultdict(list)
    for g in groups:
        if g.evidence.rule in rank:
            by_bundle[g.evidence.nets[:2]].append(rank[g.evidence.rule])
    for ks in by_bundle.values():
        assert ks == sorted(ks)


def test_split_invariants_hand_cases(gh, tmp_path, case):
    _split_invariants(gh, build(gh, tmp_path, CASES[case][0]), CASES[case][0])


@pytest.mark.parametrize("name", NINE)
def test_split_invariants_library(gh, name):
    _split_invariants(gh, build_s1(gh.load_lib(name), gh.supplies_for(name)), gh.raw(name))


def _rule_members(gh, s1):
    return collections.Counter((g.kind, g.evidence.rule, frozenset(g.members)) for g in gh.gval(s1, "matching_groups"))


# oracle (d): 사용자 ratify 2026-10-08 (user_decisions "2번도 네 판단에 동의해"(J14 파일럿 분리), "A는 나도 동의해"(판단 7),
# "꼬리 비율 미러 {M36a, M7}로 분류", "3번도 네 의견에 동의해"(ngcc {M8, M14} mirror whole 유지)) + J-U4 대조표 [ratified] 행.
# 손 대조(파일럿 JSON): Vbias4 묶음 = M10(Vop1) M12(N11b) M19(Vom1) M21(N20b) M38(Ncmfb_tail) M5(Vy) M66(diode) M68(Vbias2 = M57
# diode 넷); Vbias1 묶음 = M6(Vx) M8(Vg15) M13 M17(Vg25) M22 M60(Vbias4 = M66 diode 넷) M61(Vbias3 = M64 diode 넷) M18_bg(diode);
# Vcmfb 묶음 = M36a(diode) M7(Vx). 꼬리 넷 Vx({M1a, M1b})·Vy({M4a, M4b})·Ncmfb_tail({M37a, M37b}).
RATIFIED = {
    "current_reuse_telescopic_ota": (
        (SYM, ("M10", "M19")), (SYM, ("M17", "M8")),
        (TAIL, ("M38", "M5", "M66")), (TAIL, ("M18_bg", "M6")), (TAIL, ("M36a", "M7"))),
    "folded_cascode": ((TAIL, ("M11", "MN")),),
    "sf_pushpull_output_opamp": ((TAIL, ("M3", "M4")),),
    "ngcc_3stage_ff": (("mirror_whole", ("M14", "M8")),),
}
RATIFIED_DISP = {
    "current_reuse_telescopic_ota": (
        ("bias_distribution", ("M10", "M12", "M19", "M21", "M68"), ("Vbias4", "gnd")),
        ("bias_distribution", ("M13", "M17", "M22", "M60", "M61", "M8"), ("Vbias1", "vdd"))),
}


@pytest.mark.parametrize("name", sorted(RATIFIED))
def test_library_ratified_matching_values(gh, name):
    s1 = build_s1(gh.load_lib(name), gh.supplies_for(name))
    got = _rule_members(gh, s1)
    for rule, members in RATIFIED[name]:
        assert got[("mirror", rule, frozenset(members))] == 1, (rule, members)
        # 그 멤버는 다른 mirror 그룹(어느 rule 이든)에 같은 집합으로 다시 나오지 않는다
        assert sum(v for (k, _r, m), v in got.items() if k == "mirror" and m == frozenset(members)) == 1
    disp = [(x.kind, x.members, x.evidence.nets) for x in gh.gval(s1, "matching_dispositions")
            if x.kind in ("bias_distribution", "feedback_shared")]
    if name in RATIFIED_DISP:
        assert disp == list(RATIFIED_DISP[name])
    if name == "current_reuse_telescopic_ota":
        # M7 결정: Vcmfb 묶음의 유일한 소비 소자 M7 이 꼬리 -> feedback_shared 기록 없음
        assert not [d for d in disp if d[0] == "feedback_shared"]


@pytest.mark.parametrize("name", sorted(set(NINE) - {"current_reuse_telescopic_ota", "folded_cascode",
                                                       "sf_pushpull_output_opamp"}))
def test_library_split_is_noop_elsewhere(gh, name):
    # 세분(꼬리·diode 공급·대칭쌍)이 걸리는 묶음이 없는 6회로는 2026-10-08 이전 정의 결과 그대로(무동작).
    # 기대값 = test 쪽 옛 정의 재구현(MatchOracle split=False), 엔진 미사용.
    raw = gh.raw(name)
    got = plain_fields(gh, build_s1(gh.load_lib(name), gh.supplies_for(name)))
    assert got == MatchOracle(raw, split=False).fields()


# 합성 회로(tests/generality/topogen, 엔진 미사용 dict 생성기). oracle (a): 각 구조를 손으로 따라간 값.
#   syn_cs_load: (pmos, cs_pb, qp_hi) = {Xload, Xref}, Xref diode(전류원 Ics 블록 = 바이어스), Xload 는 주 블록에 혼자,
#     차동쌍 없음 -> 꼬리 없음 -> bias_distribution (Xload,) 만, 그룹 없음.
#   syn_follower: (nmos, sf_bn, qp_lo) = {Zb, Zc} 같은 구조 -> bias_distribution (Zb,).
#   syn_diffpair5: Ye drain dp_t = derived 차동쌍 {Ya, Yb} 공통 source -> tail_ratio {Ye, Yf}(판단 7), 기록 없음.
def _topogen():
    import importlib.util
    d = HERE_TESTS / "generality" / "topogen"
    name = "_matching_topogen"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, d / "__init__.py", submodule_search_locations=[str(d)])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name].synthetic_topologies()


HERE_TESTS = __import__("pathlib").Path(__file__).resolve().parents[1]
SYN_EXPECTED = {
    "syn_cs_load": ((), (), (("bias_distribution", ("Xload",), P,
                              ("bias_distribution", ("cs_pb", "qp_hi"), ("Xref",), (JD,))),)),
    "syn_follower": ((), (), (("bias_distribution", ("Zb",), P,
                               ("bias_distribution", ("sf_bn", "qp_lo"), ("Zc",), (JD,))),)),
    "syn_diffpair5": (
        (("matching_offset", "dc_to_ss", ("Ya", "Yb"), D, ("matching_offset", ("dp_t", "dp_im", "dp_ip"), (), (JB,))),),
        (("mirror", ("Ye", "Yf"), D, (TAIL, ("dp_bn", "qp_lo"), ("Yf",), (JD,))),
         ("mirror", ("Yc", "Yd"), D, ("mirror_whole", ("dp_x", "qp_hi"), ("Yc",), ())),
         ("diff_pair", ("Ya", "Yb"), D, ("diff_pair", ("dp_t", "dp_im", "dp_ip"), (), (JB,)))),
        ()),
}


@pytest.mark.parametrize("name", sorted(SYN_EXPECTED))
def test_synthetic_split_explicit(gh, tmp_path, name):
    raw = _topogen()[name]
    got = plain_fields(gh, build(gh, tmp_path, raw))
    assert got == SYN_EXPECTED[name]
    assert MatchOracle(raw).fields() == SYN_EXPECTED[name]


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
    if a.get("bias_inputs") or b.get("bias_inputs"):        # 복제본의 gate 전용 넷도 선언(authoring 9절)
        a["bias_inputs"] = (a.get("bias_inputs") or []) + (b.get("bias_inputs") or [])
    a.pop("source_manifest", None)                           # 복제 문서는 출처 그림이 아니다(10절: 키 없으면 검사 안 함)
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
