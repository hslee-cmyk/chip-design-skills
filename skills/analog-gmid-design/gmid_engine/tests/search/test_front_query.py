"""CONTRACT 3.17 `node_across_front(front, node, archive=None)` + I-9(커널 호출 0).

기대값: 각 front 점 스냅샷의 입력 열(dc_v·dc_rail_v·dc_writer·pins·dc_op)을 test 가 직접 읽는다.
파일 front 항목(dict)은 [xrun, 설계 40 v1.10 §2.4.3 'front 조회 전용 읽기 경로', interface card C6] `read_front_entries(archive.dir)` 로 얻는다
(옛: test 가 runs.jsonl 을 직접 읽음). 서명 `node_across_front(front, node, archive=None)` 은 그대로다.
C6 확인 항목 판단: read_front_entries 는 code_fp 로 거르지 않고 한 줄의 front 다음 pending_front 를 내며 항목마다 run_id·code_fp 키를 더한다.
그래서 메모리 front 와 길이·순서를 맞대는 test 는 '이 실행(run_id = fr.run_id) 줄의 front 부분' = 그 줄 항목의 앞 len(fr.front) 개를 쓴다
(계약 순서 '한 줄 안 front 다음 pending_front'로 정해진다). 이 모듈의 S3 폴더는 새 임시 폴더라 실행 줄은 하나다(전제 단언).
"""
import pytest

from gmid_engine.search import NodeRow, find_front, node_across_front, read_front_entries

from .conftest import build_case, circuit_c, col, node_v, theta_r4c

OP_FIELDS = ("vgs", "vds", "vsb", "current", "gm_id", "W", "L")


# [XRUN-F1 card B 규칙 M M-d] case(커널·탐색 컨텍스트 = 실행의 두 객체를 칸으로 쥠)를 돌려주므로 function 범위(test 하나 = 실행 하나)
@pytest.fixture
def run(tmp_path_factory, lut_sealed):
    import os
    import shutil
    import tempfile
    root = tempfile.mkdtemp(prefix="s6q", dir=os.environ.get("TEMP") or None)
    case = build_case(tmp_path_factory.mktemp("fq"), circuit_c(), lut_sealed, eval_budget=40, archive_root=root)
    fr = find_front(case.sctx, [theta_r4c()])
    assert len(fr.front) >= 1
    entries = read_front_entries(case.sctx.archive.dir)
    assert {e["run_id"] for e in entries} == {fr.run_id}                   # 전제: 새 폴더 -> 이 실행 줄 하나
    assert len(entries) == len(fr.front) + len(fr.pending_front)          # C6: 그 줄의 front·pending_front 항목
    own_front = tuple(entries[:len(fr.front)])                            # C6 순서: 한 줄 안 front 다음 pending_front
    assert [e["point_id"] for e in own_front] == [p.point_id for p in fr.front]
    yield case, fr, own_front
    shutil.rmtree(root, ignore_errors=True)


def expect_row(snap, node):
    V = node_v(snap)
    pins = dict(snap.column("device", "pins"))
    ops = col(snap, "device", "dc_op")
    devs = []
    for m in sorted(ops):
        terms = tuple(t for t, n in dict(pins[m]).items() if n == node)
        if terms:
            devs.append((m, tuple(sorted(terms)), tuple((f, getattr(ops[m], f)) for f in OP_FIELDS)))
    return V[node], col(snap, "node", "dc_writer")[node].tier, devs


def _norm(devices):
    out = []
    for m, terms, pairs in devices:
        out.append((m, tuple(sorted(terms)), tuple((k, v) for k, v in pairs)))
    return sorted(out)


@pytest.mark.parametrize("node", ["out", "vdd", "in"])
def test_memory_front_rows(run, node):
    case, fr, _ = run
    before = dict(case.sctx.counters)
    rows = node_across_front(fr.front, node)
    assert dict(case.sctx.counters) == before                              # I-9
    assert len(rows) == len(fr.front)
    for row, p in zip(rows, fr.front):
        assert isinstance(row, NodeRow)
        assert row.point_id == p.point_id and row.status == p.result.status
        v, tier, devs = expect_row(p.result.evaluation.snapshot, node)
        assert row.voltage == v and row.tier == tier
        assert _norm(row.devices) == sorted(devs)


def test_missing_node_key_error(run):
    _, fr, _ = run
    with pytest.raises(KeyError):
        node_across_front(fr.front, "no_such_node")


def test_archive_entries_match_memory(run):
    case, fr, own_front = run
    before = dict(case.sctx.counters)
    mem = node_across_front(fr.front, "out")
    disk = node_across_front(own_front, "out", case.sctx.archive)
    assert dict(case.sctx.counters) == before                              # I-9: 파일 경로도 커널 0
    assert [(r.point_id, r.voltage, r.tier) for r in disk] == [(r.point_id, r.voltage, r.tier) for r in mem]
    assert [_norm(r.devices) for r in disk] == [_norm(r.devices) for r in mem]


def test_archive_entries_need_archive(run):
    _, _, own_front = run
    with pytest.raises(ValueError):
        node_across_front(own_front, "out")
