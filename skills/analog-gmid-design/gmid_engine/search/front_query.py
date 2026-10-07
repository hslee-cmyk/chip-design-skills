"""front 점을 가로지르는 노드 조회 (사용자 확정 S3 조회 `node_across_front`, 설계 8절, 확정 사항 3).

진입점: `node_across_front(front, node, archive=None) -> tuple[NodeRow]`.

* `front` 원소 = `FrontPoint`(실행 안 -- 메모리 스냅샷을 읽는다) 또는 `runs.jsonl` 의 front 항목 dict(다른 실행 -- `archive`
  의 `snapshots/<fp>.json.gz` 를 읽는다). 어느 쪽도 재계산(커널 호출)은 0 이다.
* 줄 = (point_id, 상태, 노드 전압(레일이면 `dc_rail_v`, 아니면 `dc_v`), writer 티어, 그 노드에 단자가 닿는 MOS 마다
  (소자, 단자들, (vgs, vds, vsb, current, gm_id, W, L))). 노드가 스냅샷에 없으면 `KeyError`.
"""
from .search_values import FrontPoint, NodeRow

_OP_FIELDS = ("vgs", "vds", "vsb", "current", "gm_id", "W", "L")


def _from_snapshot(point_id, status, snap, node):
    if snap.record("node", node) is None:
        raise KeyError("node_across_front: 노드 " + repr(node) + " 이 스냅샷에 없다")
    rail = snap.field("node", node, "dc_rail_v")
    voltage = rail.value if rail is not None else snap.value("node", node, "dc_v")
    writer = snap.field("node", node, "dc_writer")
    pins = dict(snap.column("device", "pins"))
    devices = []
    for m, op in snap.column("device", "dc_op"):
        terms = tuple(t for t, net in pins[m] if net == node)
        if terms:
            devices.append((m, terms, tuple((f, getattr(op, f)) for f in _OP_FIELDS)))
    return NodeRow(point_id, status, float(voltage), None if writer is None else writer.value.tier, tuple(devices))


def _from_file(entry, archive, node):
    data = archive.read_snapshot(entry["snapshot_ref"])
    records = {(r["kind"], r["key"]): r["fields"] for r in data["records"]}
    fields = records.get(("node", node))
    if fields is None:
        raise KeyError("node_across_front: 노드 " + repr(node) + " 이 스냅샷 파일에 없다")
    voltage = fields["dc_rail_v"]["value"] if "dc_rail_v" in fields else fields["dc_v"]["value"]
    tier = fields["dc_writer"]["value"]["tier"] if "dc_writer" in fields else None
    devices = []
    for (kind, key), dev in sorted(records.items()):
        if kind != "device" or "dc_op" not in dev:
            continue
        terms = tuple(t for t, net in dev["pins"]["value"] if net == node)
        if terms:
            op = dev["dc_op"]["value"]
            devices.append((key, terms, tuple((f, op[f]) for f in _OP_FIELDS)))
    return NodeRow(entry["point_id"], entry["status"], float(voltage), tier, tuple(devices))


def node_across_front(front, node, archive=None):
    rows = []
    for point in front:
        if isinstance(point, FrontPoint):
            rows.append(_from_snapshot(point.point_id, point.result.status, point.result.evaluation.snapshot, node))
        else:
            if archive is None:
                raise ValueError("node_across_front: 파일 front 항목은 archive 가 있어야 읽는다")
            rows.append(_from_file(point, archive, node))
    return tuple(rows)
