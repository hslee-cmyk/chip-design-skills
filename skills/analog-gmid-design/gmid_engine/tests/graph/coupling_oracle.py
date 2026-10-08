"""GB3 결합 변수 y·기둥↔블록 매핑표의 독립 oracle (b) -- 피검 함수(`coupling_vars`·`column_block_map`) 미사용, 그 소스 미열람.

근거(정본 순서):
- 설계 `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` §3.3 본문과 'U10 as-built 보완'(master 6707424):
  (i) 바이어스 기둥 = K1·K2·K4 판정의 의사 블록 `bias:<기둥>` (ii) K3 구조 정의 (iii) K7 은 MOS 만
  (iv) 레코드 `nets`·매핑표 `basis` (v) `column_unassigned` 범위 = DC 가지에 든 원소.
- 계획 DEC-71 (2)(기둥↔블록 매핑표, 바이어스 기둥, 귀속 안 된 소자 정지)·(7)(K1·K2·K3·K8 경계 관계).
- interface = graph CONTRACT 11절(값 형식, 매핑표 규칙 11.2, 결합 종류 표 11.3, 횡단 정의 '한 뷰 안에서 소자들의 블록 키
  합집합 != 교집합, 블록이 있는 소자가 둘 이상').

입력은 S1(`graph.branches`·`graph.columns`·`graph.matching_groups`·`graph.rel_equal_vgs`·`device.{dc_role, element_class, pins}`)과
S1v(`views[*].blocks/cells`, `l_classes`) 공개 필드뿐이다. 이 파일은 설계 문장을 다른 표현(집합 연산)으로 다시 세운 것이고
엔진 출력과는 test 쪽에서 비교한다.

의사 블록 표현: 엔진의 `BlockRef` 표현이 아직 없다(57e81fb 미구현). oracle 은 의사 블록을 문자열 키 `"bias:<기둥 id>"` 로
내부에서만 쓰고, 엔진 비교는 (kind, members, domain, nets) 키로 한다(blocks 는 실제 블록 부분만 비교).
"""
from __future__ import annotations

from gmid_engine.graph import GRAPH_KEY

LOAD_ROLES = frozenset({"load", "mirror", "diode_load"})   # CONTRACT 11.3 K1 '부하 역할'
MOS = "mos"


def _g(s1, field):
    return s1.value("graph", GRAPH_KEY, field)


def pseudo(col):
    return "bias:%s" % (col,)


class CouplingOracle:
    def __init__(self, s1, s1v):
        self.s1, self.s1v = s1, s1v
        self.branches = {b.id: b for b in _g(s1, "branches")}
        self.columns = {c.id: c for c in _g(s1, "columns")}
        self.ecls = dict(s1.column("device", "element_class"))
        self.pins = {d: dict(p) for d, p in s1.column("device", "pins")}
        self.dc_role = {d: r.role for d, r in s1.column("device", "dc_role")}
        self.views = {v.id: v for v in s1v.views}
        # 가지 원소
        self.branch_devs = {bid: tuple(sorted({e for s in b.segments for e in s.elements})) for bid, b in self.branches.items()}
        self.col_devs = {cid: frozenset(e for bid in c.branch_order for e in self.branch_devs[bid])
                         for cid, c in self.columns.items()}
        self.in_branch = frozenset(e for devs in self.branch_devs.values() for e in devs)
        # 실제 블록 멤버십: 뷰 -> 소자 -> 블록 키 집합, (뷰, 키) -> roles
        self.member = {}
        self.roles = {}
        for v in s1v.views:
            m = {}
            for b in v.blocks:
                self.roles[(v.id, b.key)] = dict(b.roles)
                for d, _r in b.roles:
                    m.setdefault(d, set()).add(b.key)
            self.member[v.id] = m
        self.block_devs = frozenset(d for m in self.member.values() for d in m)
        self._map()

    # ------------------------------------------------------------ 매핑표 (DEC-71 (2), CONTRACT 11.2, 설계 as-built (v))
    def _map(self):
        rows = set()
        bias_cols = []
        unassigned = []
        dev_cols = {}
        for cid, devs in self.col_devs.items():
            for d in devs:
                dev_cols.setdefault(d, set()).add(cid)
        for cid in sorted(self.col_devs):
            devs = self.col_devs[cid]
            col_blocks = {(vid, k) for vid, m in self.member.items() for d in devs for k in m.get(d, ())}
            if not col_blocks:
                bias_cols.append(cid)
            for d in devs:
                mine = {(vid, k) for vid, m in self.member.items() for k in m.get(d, ())}
                if mine:
                    for ref in mine:
                        rows.add((cid, ref, d, "block_member"))
                elif col_blocks:
                    for ref in col_blocks:
                        rows.add((cid, ref, d, "column_mate"))
                else:
                    rows.add((cid, None, d, "bias_column"))
        for vid, m in self.member.items():
            for d, ks in m.items():
                if d not in dev_cols:
                    for k in ks:
                        rows.add((None, (vid, k), d, "block_member"))
        for d in sorted(self.in_branch):
            if d not in dev_cols and d not in self.block_devs:
                unassigned.append(d)
        self.map_rows = frozenset(rows)
        self.bias_columns = tuple(bias_cols)
        self.unassigned = tuple(unassigned)
        self.dev_cols = dev_cols
        # 뷰별 귀속 블록(블록 멤버 + 기둥 이웃) -- 횡단 판정의 '블록이 있는 소자'
        att = {}
        for col, ref, d, _basis in rows:
            if ref is not None:
                att.setdefault(ref[0], {}).setdefault(d, set()).add(ref[1])
        self.attributed = att
        self.dev_pseudo = {}
        for cid in bias_cols:
            for d in self.col_devs[cid]:
                self.dev_pseudo.setdefault(d, set()).add(pseudo(cid))

    def keys(self, vid, d, with_pseudo):
        ks = set(self.attributed.get(vid, {}).get(d, ()))
        if with_pseudo:
            ks |= self.dev_pseudo.get(d, set())
        return ks

    def crossing(self, members, with_pseudo):
        """{뷰: 횡단 블록 키 집합} -- 한 뷰 안에서 블록이 있는 소자 둘 이상, 키 합집합 != 교집합."""
        out = {}
        for vid in self.views:
            ks = [self.keys(vid, d, with_pseudo) for d in members]
            ks = [k for k in ks if k]
            if len(ks) < 2:
                continue
            union = set().union(*ks)
            inter = set.intersection(*map(set, ks))
            if union != inter:
                out[vid] = union
        return out

    # ------------------------------------------------------------ 결합 종류 (CONTRACT 11.3 + 설계 as-built)
    def records(self):
        recs = set()
        # K1: mirror matching 그룹(dc) / L 동치류(geom). 부하 역할 멤버가 횡단 실제 블록에 있어야 한다.
        sources = [(tuple(g.members), "dc") for g in _g(self.s1, "matching_groups") if g.kind == "mirror"]
        sources += [(tuple(c.members), "geom") for c in self.s1v.l_classes]
        for members, dom in sources:
            cr = self.crossing(members, True)
            ok = any(self.roles.get((vid, k), {}).get(d) in LOAD_ROLES
                     for vid, ks in cr.items() for k in ks if not isinstance(k, str) for d in members)
            if cr and ok:
                recs.add(("K1", tuple(sorted(members)), dom, ()))
        # K2: equal_vgs 엣지 횡단, nets = evidence nets
        for e in _g(self.s1, "rel_equal_vgs"):
            if self.crossing(e.members, True):
                recs.add(("K2", tuple(sorted(e.members)), "dc", tuple(e.evidence.nets)))
        # K3: 비레일 넷에서 MOS e 의 drain 과 MOS d 의 source 가 만나고 둘의 블록이 다르다(실제 블록 멤버십, 한 뷰)
        rails = {n for n, r in self.s1.column("node", "is_rail") if r}
        mos = [d for d, c in self.ecls.items() if c == MOS]
        for e in mos:
            for d in mos:
                n = self.pins[e]["d"]
                if e == d or n in rails or self.pins[d]["s"] != n:
                    continue
                for vid, m in self.member.items():
                    a, b = m.get(e, set()), m.get(d, set())
                    if a and b and (a | b) != (a & b):
                        recs.add(("K3", (e, d), "dc", (n,)))
        # K4: 가지를 지나는 모든 기둥의 소자가 횡단 -> members = 가지 원소, nets = 가지 양 끝
        for bid, b in self.branches.items():
            cols = [cid for cid, c in self.columns.items() if bid in c.branch_order]
            if not cols:
                continue
            devs = sorted(set().union(*(self.col_devs[c] for c in cols)))
            if self.crossing(devs, True):
                recs.add(("K4", self.branch_devs[bid], "dc", tuple(sorted(b.ends))))
        # K7: 둘 이상 뷰의 블록 멤버인 MOS
        for d in sorted(self.block_devs):
            if self.ecls.get(d) == MOS and sum(1 for m in self.member.values() if d in m) >= 2:
                recs.add(("K7", (d,), "dc", ()))
        # K8: 측면 주입
        for vid, v in self.views.items():
            cells = {c.dev: c for c in v.cells}
            cd_edges = {}
            for c in v.cells:
                if c.kind == "cd":
                    cd_edges.setdefault(self.pins[c.dev]["g"], set()).add(c.out)
            gain_outs = {o for b in v.blocks if b.kind == "gain" for o in b.outputs}
            for c, ci in cells.items():
                if ci.kind != "cs" or self.dc_role.get(c) != "bias_current_source":
                    continue
                n = self.pins[c]["d"]
                if n in gain_outs:
                    continue
                inj = []
                for x, xi in cells.items():
                    if xi.kind != "cd" or xi.out != n:
                        continue
                    seen, todo = set(), [self.pins[x]["g"]]
                    while todo:
                        t = todo.pop()
                        if t in seen:
                            continue
                        seen.add(t)
                        todo.extend(cd_edges.get(t, ()))
                    if self.pins[c]["g"] not in seen:
                        inj.append(x)
                if inj:
                    recs.add(("K8", tuple(sorted([c] + inj)), "dc", (n,)))
        return recs

    def real_blocks(self, members, with_pseudo):
        return {(vid, k) for vid, ks in self.crossing(members, with_pseudo).items() for k in ks if not isinstance(k, str)}


def engine_records(coupling):
    """엔진 결과를 oracle 과 같은 키(kind, 정렬 members, domain, nets)로. K3·K4·K8 의 nets 순서는 집합으로 비교하려고 정렬."""
    out = set()
    for v in coupling.vars:
        nets = tuple(v.nets)
        if v.kind in ("K4",):
            nets = tuple(sorted(nets))
        members = tuple(v.members) if v.kind == "K3" else tuple(sorted(v.members))
        out.add((v.kind, members, v.domain, nets))
    return out


def engine_map_rows(cbm):
    return frozenset((r.column, None if r.block is None else (r.block.view, tuple(r.block.key)), r.device, r.basis)
                     for r in cbm.rows)
