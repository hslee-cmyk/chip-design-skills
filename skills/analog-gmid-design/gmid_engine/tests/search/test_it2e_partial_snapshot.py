"""[IT-2e 20261104-it2e-partial-snapshot, T-E3 의 S3 줄 절] parent 가 있는 탐색 평가의 실패 줄 `snapshot_fp` = parent 없는 대조 평가의 지문.

oracle (변성): 부분 스냅샷 지문은 (평가 키, 실패 지점)만으로 정해진다 -- 같은 θ·같은 주입을 parent 있는 컨텍스트와 parent 없는 별도 컨텍스트
(별도 S3 root)에서 부르면 실패 줄 `snapshot_fp` 와 `EvalResult.partial.fp` 가 같다. 지문 절대값은 단언하지 않는다.
주입은 test_kernel.py `test_partial_snapshot_seal_stage_block_failure` 와 같은 공개 경로(ComputeBlock.__call__ 감쌈 + 실제 봉인 위반 기록의
SealViolationError.from_record). 사례 유효 조건 (가): 주입 직전 같은 입력으로 대상 블록을 실제로 한 번 돌려 계수 증분이
(calls 1, reuses 0, grafts 0, replays 0, computes 1, 재계산 0)이어야 한다. (나): 대조는 다른 탐색 컨텍스트·다른 S3 root·다른 객체.
"""
import shutil
import tempfile

import pytest

import gmid_engine.sizing as sizing
from gmid_engine.core import ComputeBlock, SealViolationError
from gmid_engine.search import STATUS_FAILED, STATUS_SEALED, evaluate

from .conftest import CELLS_C, build_case, circuit_c, theta_r4c, write_decls
from .conftest import COUNT_FIELDS, block_row, row_delta
from .test_kernel import read_evals, th_sorted

TARGETS = ("dc_seal_kcl", "dc_seal_report")


def _theta_parent():
    return theta_r4c()


def _theta_child():
    """parent 와 y·v1·i2 가 다른 θ(L 은 같아 칸 CELLS_C 그대로)."""
    return theta_r4c(y=0.45, v1=0.62, i2=3e-5)


def _failed(tmp_path, lut, root, record, target, with_parent, monkeypatch, pdk, rule):
    # pdk·rule 은 두 case 가 같은 선언을 쓴다(선언 sha 가 graph/kernel 지문에 들어가므로 case 마다 따로 쓰면 지문이 달라진다; 이 test 는 parent 독립만 본다)
    case = build_case(tmp_path, circuit_c(), lut, archive_root=root, pdk=pdk, rule=rule)
    s = case.sctx
    parent = None
    if with_parent:
        parent = evaluate(s, th_sorted(_theta_parent()), CELLS_C)
        assert parent.status == STATUS_SEALED                                           # 전제: parent 는 봉인된 평가
    seen, probe = [], []
    orig = ComputeBlock.__call__

    def wrapped(self, snapshot, *extras, **kw):
        seen.append(self.name)
        if self.name == target:
            row0 = block_row(s.dc.counters, target)
            orig(self, snapshot, *extras, **kw)
            probe.append(row_delta(block_row(s.dc.counters, target), row0))
            raise SealViolationError.from_record(record)
        return orig(self, snapshot, *extras, **kw)

    with monkeypatch.context() as mp:
        mp.setattr(ComputeBlock, "__call__", wrapped)
        r = evaluate(s, th_sorted(_theta_child()), CELLS_C, parent=parent)
    assert r.status == STATUS_FAILED and r.partial is not None and r.evaluation is None
    assert seen[-1] == target and len(probe) == 1
    assert probe[0] == (1, 0, 0, 0, 1, 0), (target, dict(zip(COUNT_FIELDS, probe[0])))  # 사례 유효 (가)
    (line,) = [x for x in read_evals(root, s.context_fp) if x["seq"] == r.seq]
    return r, line


@pytest.mark.parametrize("target", TARGETS)
def test_it2e_s3_failure_line_fp_parent_independent(tmp_path, lut_sealed, monkeypatch, target):
    """T-E3 (S3 줄): parent 경로의 실패 줄 snapshot_fp == partial.fp == parent 없는 대조 평가의 지문. 부분 스냅샷에 대상 블록과 그 뒤 필드는 없다."""
    src = build_case(tmp_path / "src", circuit_c(), lut_sealed)
    bad = evaluate(src.sctx, th_sorted(theta_r4c(y=0.1, v1=1.5)), CELLS_C)
    assert bad.status == STATUS_FAILED and bad.failure is not None                      # 전제: 실제 봉인 위반 기록
    pdk, rule = write_decls(tmp_path / "decls")
    root_a, root_b = tempfile.mkdtemp(prefix="s6e"), tempfile.mkdtemp(prefix="s6f")
    try:
        ra, la = _failed(tmp_path / "a", lut_sealed, root_a, bad.failure, target, True, monkeypatch, pdk, rule)
        rb, lb = _failed(tmp_path / "b", lut_sealed, root_b, bad.failure, target, False, monkeypatch, pdk, rule)
    finally:
        shutil.rmtree(root_a, ignore_errors=True)
        shutil.rmtree(root_b, ignore_errors=True)
    assert ra is not rb and ra.partial is not rb.partial                                # (나)
    assert target not in ra.partial.block_versions and target not in rb.partial.block_versions
    later = [getattr(sizing, a).name for a in ("dc_seal_node_conflict", "dc_seal_vgs_match", "dc_seal_kcl", "dc_seal_bulk_reverse",
                                               "dc_seal_saturation", "dc_seal_kvl_branch", "dc_seal_conduction", "dc_seal_report")]
    cut = later.index(target)
    assert all(b not in ra.partial.block_versions for b in later[cut:])
    assert la["snapshot_fp"] == ra.partial.fp and lb["snapshot_fp"] == rb.partial.fp
    assert ra.partial.fp == rb.partial.fp
    assert la["snapshot_fp"] == lb["snapshot_fp"]
