"""블록 국소 봉인 -- 덮는 기둥만 판정하는 평가 커널 (설계 41 §5.3 '국소 봉인 인터페이스', 40 §3.7, 확인 행 D-LS).

진입점: `size_and_seal_local(ctx, theta_block, fixed, columns) -> LocalSeal`.

층 0 블록 국소 후보(41 §5.3)가 부른다 -- 후보 하나의 봉인 판정에 전회로 실패가 섞이지 않게, 판정 대상을 `columns` 가 덮는 소자·노드로
좁힌 커널 호출이다.

* 인자:
  - `theta_block` = {"종류:키": 값} -- 이 블록이 정하는 θ 성분. `fixed` = 같은 형식 -- 블록 밖 성분(블록을 가로지르는 L 동치류 L, 이웃 블록의
    y·전류 등. 첫 회차는 41 §6 출발값, 이후 회차는 직전 조립점 값 -- 값을 고르는 일은 부르는 쪽 몫). 둘의 합집합이 `ctx.schema.components` 와
    정확히 같아야 한다(겹침·빠짐·모르는 키 -> `ValueError`, 호출 계약 위반). 키 문자열 = `theta_name(종류, 키)`.
  - `columns` = {str(기둥 id)} -- S1 `graph.columns` 의 기둥 id(`Column.id`). 덮는 소자 = 그 기둥 경로 가지의 segment 원소 전부, 덮는 넷 =
    그 가지의 끝·segment 넷 중 레일이 아닌 것. 비었거나 모르는 id 면 `ValueError`.
* 계산: 평가 커널(`size_and_seal` 과 같은 ②~⑤ 블록 -- `run_kernel`)을 `raise_on_violation=False` 로 돌려 봉인 항목별 위반 대상을 그대로 읽고,
  **봉인 1·2·6·7 과 덮는 기둥의 KCL(3)·KVL(8)** 위반만 남긴다(설계 문구). 위반 대상(소자 또는 넷)이 덮는 집합과 겹치는 항목만 실패이고, 실패
  레코드의 소자는 덮는 소자만이다. 봉인 4·5(메타데이터)와 9(전도 여유, 41 §5.3 은 전류 하한으로 후보를 만들 때 따로 쓴다)는 국소 판정이 아니다.
  `②~⑤` 계산 중 후보 실패(`SealViolationError`·`NonconvergentError`: 창이 비거나 SCC 수렴 실패 -- 블록 경계를 알 수 없는 전회로 실패)는 덮는
  소자와 무관하게 실패로 낸다(국소 해를 만들 수 없다).
* 반환 `LocalSeal`: `ok`, `failures`(FailureRecord, 항목 순), `snapshot_fragment`(덮는 소자의 `DeviceOp`·덮는 넷의 전압 -- 실패하면 비어 있다),
  `gain_db`(**None**: 블록 국소 gain 모델 `metrics.block_local_gain`(41 §2, U7)이 병합되기 전 자리), `power_w` = 덮는 소자가 레일에서 끌어오는
  Σ V·I(레일에 닿는 덮는 소자의 채널·저항 전류 × 레일 전압, 부호 있는 합 -- 전회로 `power_dc_w` 와 같은 정의의 부분합), `area_m2` = 덮는 MOS 의
  Σ W·L(전회로 게이트 면적 축의 부분합). 실패 점은 power·area 가 None.
* 캐시: 필드 캐시(`compute_block` 입력 버전)는 커널 안에서 그대로 동작한다. (블록 키, θ_block, fixed 지문) 키의 결과 캐시는 블록 몫 평가 예산
  N_T,i(41 §5.8, U13 `eval_budget`)로 상한을 정해야 해서 호출하는 U15 `local_candidates` 가 갖는다(여기에 상수 상한을 두지 않는다).
"""
import math

from gmid_engine.core import NonconvergentError, SealViolationError
from gmid_engine.graph import ELEMENT_MOS, GRAPH_KEY

from .s2_values import (
    SEAL_BULK_REVERSE,
    SEAL_FAIL,
    SEAL_KCL,
    SEAL_KVL_BRANCH,
    SEAL_NODE_CONFLICT,
    SEAL_SATURATION,
    SEAL_VGS_MATCH,
    DC_KEY,
    KernelContext,
)
from .kernel_run import run_kernel
from .local_values import LocalSeal, SnapshotFragment

_LOCAL_ITEMS = (SEAL_NODE_CONFLICT, SEAL_VGS_MATCH, SEAL_KCL, SEAL_BULK_REVERSE, SEAL_SATURATION, SEAL_KVL_BRANCH)
_SEP = ":"


def theta_name(kind, key):
    """θ 성분 (kind, key) 의 국소 봉인 키 문자열 `종류:키`."""
    return kind + _SEP + key


def _merge_theta(ctx, theta_block, fixed):
    names = {theta_name(kind, key): (kind, key) for kind, key in ctx.schema.components}
    overlap = sorted(set(theta_block) & set(fixed))
    unknown = sorted((set(theta_block) | set(fixed)) - set(names))
    missing = sorted(set(names) - set(theta_block) - set(fixed))
    if overlap or unknown or missing:
        raise ValueError("size_and_seal_local: θ 키가 스키마와 다르다 -- 겹침 " + repr(overlap) + ", 모르는 키 " + repr(unknown)
                         + ", 빠짐 " + repr(missing))
    return {names[name]: value for source in (theta_block, fixed) for name, value in source.items()}


def covered_sets(ctx, columns):
    """(덮는 원소 frozenset(MOS·저항), 덮는 넷 frozenset(레일 제외), 덮는 MOS frozenset). `columns` = 기둥 id 문자열 모음."""
    if isinstance(columns, str) or not columns:
        raise ValueError("size_and_seal_local: columns 는 기둥 id 문자열의 비어 있지 않은 모음이어야 한다")
    base = ctx.base
    by_id = {str(c.id): c for c in base.value("graph", GRAPH_KEY, "columns")}
    unknown = sorted(set(columns) - set(by_id))
    if unknown:
        raise ValueError("size_and_seal_local: 모르는 기둥 id " + repr(unknown))
    branches = {b.id: b for b in base.value("graph", GRAPH_KEY, "branches")}
    rails = {net for net, is_rail in base.column("node", "is_rail") if is_rail}
    mos = {name for name, cls in base.column("device", "element_class") if cls == ELEMENT_MOS}
    devices, nets = set(), set()
    for token in columns:
        for bid in by_id[token].branch_order:
            branch = branches[bid]
            nets.update(branch.ends)
            for segment in branch.segments:
                nets.update(segment.nets)
                devices.update(segment.elements)
    return frozenset(devices), frozenset(nets - rails), frozenset(devices & mos)


def _failures(report, devices, nets):
    out = []
    for item in report.items:
        if item.item not in _LOCAL_ITEMS or item.status != SEAL_FAIL:
            continue
        hit_devices = set(item.devices) & devices
        if not hit_devices and not set(item.nodes) & nets:
            continue
        detail = {"item": item.item, "nodes": tuple(sorted(set(item.nodes) & nets)), "item_detail": item.detail}
        out.append(SealViolationError(devices=tuple(sorted(hit_devices)), margin=item.margin, detail=detail).record)
    return tuple(out)


def _power(snapshot, devices):
    """덮는 소자가 레일에서 끌어오는 Σ V·I -- 채널·저항 전류(전도 방향 a -> b)가 레일 a 에서 나가면 +, 레일 b 로 들어가면 −."""
    rails = dict(snapshot.column("node", "dc_rail_v"))
    currents = dict(snapshot.column("device", "dc_current"))
    total = 0.0
    for name, a, b in snapshot.value("graph", DC_KEY, "dc_current_basis").ends:
        if name in devices:
            total += currents[name] * (rails.get(a, 0.0) - rails.get(b, 0.0))
    return total


def size_and_seal_local(ctx, theta_block, fixed, columns):
    if not isinstance(ctx, KernelContext):
        raise TypeError("size_and_seal_local: ctx 는 build_kernel_context 결과여야 한다")
    theta = _merge_theta(ctx, theta_block, fixed)
    elements, nets, mos = covered_sets(ctx, columns)
    try:
        evaluation = run_kernel(ctx, theta, None, (), False)
    except (SealViolationError, NonconvergentError) as exc:
        return LocalSeal(False, (exc.record,), SnapshotFragment())
    failures = _failures(evaluation.report, elements, nets)
    if failures:
        return LocalSeal(False, failures, SnapshotFragment())
    snapshot = evaluation.snapshot
    ops = dict(snapshot.column("device", "dc_op"))
    volts = dict(snapshot.column("node", "dc_v"))
    fragment = SnapshotFragment(tuple((m, ops[m]) for m in sorted(mos)), tuple((n, volts[n]) for n in sorted(nets) if n in volts))
    area = math.fsum(ops[m].W * ops[m].L for m in sorted(mos))
    return LocalSeal(True, (), fragment, None, _power(snapshot, elements), area)
