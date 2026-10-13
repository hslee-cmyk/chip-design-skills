"""기둥↔블록 매핑표 (설계 40 §3.3, 계획 DEC-71 (2)).

진입점: `column_block_map(s1, views) -> (rows, bias_columns)`  (`views` = `graph/s1v: views` 필드 값, 결과는 `graph/coupling` 의 두 필드 값).

S1 기둥(레일 쌍 노드-단순 경로, `graph.columns`)과 S1v 블록(모든 뷰의 `Block.roles`)을 교차해 행 `ColumnBlockRow(column, block, device, shared, basis)` 를 만든다:

* 소자가 어느 뷰의 블록 멤버이면 그 기둥마다 그 블록(뷰별)과 한 행(`block_member`).
* 어느 블록에도 속하지 않는 소자(어느 뷰에서도)가 든 기둥에 블록 소자가 하나라도 있으면 그 소자를 기둥에 있는 블록들에 귀속시키고 공유 소자로 표시한다(`column_mate`):
  그 기둥의 KVL 을 푸는 주체가 그 블록의 국소 문제이고, 소자의 gds 가 그 블록 AC 이득에 들어가기 때문이다(DEC-71 (2) '블록 소자와 섞여 있으면').
* 기둥의 소자가 모두 블록 밖이면 바이어스 기둥이다: 행의 block 은 None(`bias_column`), 기둥 id 는 `bias_columns` 에 든다.
* 어느 기둥에도 들지 않지만 블록 멤버인 소자(DC 엣지가 없는 커패시터 등)는 column=None 행으로 남는다.
* `shared` = 소자가 둘 이상 기둥에 걸치거나, 한 뷰에서 둘 이상 블록의 멤버이거나, 기둥 이웃으로 귀속된 소자.

**불변식**(DEC-71 (2), N6.2 6a): 어느 블록에도 속하지 않고 어느 기둥(= 바이어스 기둥 포함)에도 들지 않는 소자가 있으면 귀속 규칙이 없어 그 소자가 낀 KVL 을 푸는 주체가 없다 --
`StructureUnresolvedError`(detail reason `column_unassigned`, devices = 그 소자들)로 정지한다. 소자 범위 = 어느 DC 가지(S1 `graph.branches`)에 든 원소(MOS·저항·이상원) --
DC 전류가 없는 원소(커패시터, DEC-70 가지치기로 빠진 저항)는 낀 기둥 KVL 이 없어 이 불변식 대상이 아니다. 블록 멤버면 column=None 행으로만 남는다.
"""
from gmid_engine.core import StructureUnresolvedError

from .coupling_values import (
    BASIS_BIAS_COLUMN,
    BASIS_BLOCK_MEMBER,
    BASIS_COLUMN_MATE,
    REASON_COLUMN_UNASSIGNED,
    BlockRef,
    ColumnBlockRow,
)
from .s1_values import GRAPH_KEY


def _row_key(row):
    return (-1 if row.column is None else row.column, row.block is not None, row.block or BlockRef("", ()), row.device)


def _direct_blocks(views):
    """{소자: {BlockRef}} -- 모든 뷰 블록의 멤버 소자."""
    direct = {}
    for view in views:
        for block in view.blocks:
            ref = BlockRef(view.id, block.key)
            for name, _ in block.roles:
                direct.setdefault(name, set()).add(ref)
    return direct


def _column_devices(branches, s1):
    """{기둥 id: 소자 이름 정렬 tuple} -- 기둥이 지나는 가지의 모든 segment 원소."""
    return {c.id: tuple(sorted({e for bid in c.branch_order for seg in branches[bid].segments for e in seg.elements}))
            for c in s1.value("graph", GRAPH_KEY, "columns")}


def _multi_block_in_view(refs):
    seen = set()
    for ref in refs:
        if ref.view in seen:
            return True
        seen.add(ref.view)
    return False


def column_block_map(s1, views):
    direct = _direct_blocks(views)
    branches = {b.id: b for b in s1.value("graph", GRAPH_KEY, "branches")}
    columns = _column_devices(branches, s1)
    column_count = {}
    for devices in columns.values():
        for name in devices:
            column_count[name] = column_count.get(name, 0) + 1
    on_branch = {e for b in branches.values() for seg in b.segments for e in seg.elements}
    unassigned = tuple(sorted(name for name in on_branch if name not in direct and name not in column_count))
    if unassigned:
        raise StructureUnresolvedError(devices=list(unassigned), detail={
            "reason": REASON_COLUMN_UNASSIGNED,
            "message": "어느 블록에도 어느 기둥에도 속하지 않는 소자(DEC-71 (2), N6.2 6a)",
            "devices": unassigned})
    universe = on_branch | set(direct)
    shared = {name: column_count.get(name, 0) > 1 or _multi_block_in_view(sorted(direct.get(name, ()))) for name in universe}
    rows = []
    bias = []
    for cid, devices in columns.items():
        mates = sorted(set().union(*(direct.get(name, set()) for name in devices)))
        if not mates:
            bias.append(cid)
        for name in devices:
            if name in direct:
                rows.extend(ColumnBlockRow(cid, ref, name, shared[name], BASIS_BLOCK_MEMBER) for ref in sorted(direct[name]))
            elif mates:
                rows.extend(ColumnBlockRow(cid, ref, name, True, BASIS_COLUMN_MATE) for ref in mates)
            else:
                rows.append(ColumnBlockRow(cid, None, name, shared[name], BASIS_BIAS_COLUMN))
    for name in sorted(universe):
        if name in direct and name not in column_count:
            rows.extend(ColumnBlockRow(None, ref, name, shared[name], BASIS_BLOCK_MEMBER) for ref in sorted(direct[name]))
    return tuple(sorted(rows, key=_row_key)), tuple(sorted(bias))
