"""metamorphic: 레이아웃 행 구성(layout `run_layout`)이 이름·순서 변형을 따라가는가.

oracle 종류 (a) -- 변형 관계(원래 결과에 치환표를 적용한 것 대 치환한 입력의 결과).
- 입력: 레이아웃 입력 계약(layout CONTRACT 4.1)의 생산자(graph·sizing -> MOD7)는 아직 없다(4.16 '다른 패키지 생산자 대기'). 그래서
  test 가 공개 값만으로 `LayoutInput` 을 만든다 -- 소자 = 봉인 스냅샷 `dc_op`(kind·L·gm/ID·VDS·VSB, 보존량 (ID, gm/ID, L) 4.1)와 S1
  `pins`·`bulk`·`is_diode`, matching 그룹 = graph `matching_groups`(status derived 만 -- graph CONTRACT 4.5a '레이아웃 전달 정책') +
  `matching_dispositions` 중 bias_distribution·feedback_shared(2명 이상 -- layout `EXCLUDED_ROLES` 입력), hub = 차동쌍 evidence 첫
  넷(source)·미러 (gate, source) 의 source(4.5a 표), branch_symmetric 은 hub 없음(4.1), 허용 패턴 = `PATTERNS` 전부, 행 그룹 =
  (kind, body) 마다 하나(4.1 '소자 (kind, body) == 행 그룹 (kind, body_net)'). gid·rid 는 내용(규칙·멤버·kind·body)으로 만든
  문자열이라 이름 치환을 같은 표로 따라간다(이름에서 온 순서 말고는 아무 것도 들지 않는다).
- **W 압축**(입력 변환, 회로·이름 무관 단조 함수): 층 0 시작점은 W·면적 상한 미선언(search CONTRACT S-3b)이라 W 가 m~10⁵ m 급이고,
  그대로 넣으면 행 구성이 finger 수백만 개를 만들어 MemoryError 가 난다(작성자 실측 syn_cs_load W 2.6e5 m). 그래서 소자 W 를
  로그 축에서 [1 µm, 50 µm] 로 같은 1차 함수로 옮기고 ID 를 같은 비로 바꾼다(전류 밀도 ID/W·gm/ID·L·VDS·VSB 보존 -> 4.2 의 슬라이스
  역산 점이 같다). 원래·변형 입력에 같은 함수를 쓰므로 변형 관계는 그대로다.
- 불변식(4.13): 9 결정론 -- 같은 입력이면 결과가 같다. 이름 치환은 이름 정렬로 정한 순서(행 그룹 rid 정렬, 행 안 이름 정렬, hub 병합
  '넷 이름 정렬 순', Euler 섬 이름 정렬 -- 4.7·4.8·4.11)만 바꾼다. 사용자 대원칙(topology 무관)에 따라 판정 축 외곽 면적(4.10
  `outline_area_m2`)과 소자별 배치(폭 키·finger 수·실현 W·허용오차·origin)가 치환표를 따라가야 한다. 행 id 는 이름을 담아 소자별
  행 finger 수의 다중집합으로 비교한다.
- 순서 섞기·태그 잡음: 같은 이름이라 결과가 같다(4.13 9).
"""
from __future__ import annotations

import collections
import dataclasses
import math

import pytest

from gmid_engine.graph import GRAPH_KEY
from gmid_engine.layout import LayoutDevice, LayoutInput, LayoutPdk, MatchingGroup, RowGroup, run_layout
from gmid_engine.layout.contract_input import PATTERNS
from gmid_engine.sizing import size_and_seal

from .pipeline import map_theta

LIB = ("two_stage_ota", "folded_cascode", "ngcc_3stage_ff")
SYNTH = ("syn_cs_load", "syn_diffpair5", "syn_follower")
CIRCUITS = LIB + SYNTH
SEEDS = (0, 1)
W_LO, W_HI = 0.5e-6, 5e-6        # 압축 목표 W 범위(test 입력 -- 실 LUT 최소 finger 0.36~0.42 µm 위, 소자당 finger 수 ~10 이하)
EXCLUDED = ("bias_distribution", "feedback_shared")     # graph disposition kind = layout EXCLUDED_ROLES 이름(4.1·4.5a)


def _compress(ws):
    lo, hi = math.log(min(ws)), math.log(max(ws))
    span = hi - lo
    return [math.exp(math.log(W_LO) + (math.log(w) - lo) / span * (math.log(W_HI) - math.log(W_LO))) if span > 0
            else math.sqrt(W_LO * W_HI) for w in ws]


def layout_input(pipe, case, theta):
    ev = size_and_seal(case.ctx, theta)
    assert ev.sealed is not None, ev.report
    snap = ev.sealed.snapshot
    ops = sorted(snap.column("device", "dc_op"), key=lambda kv: (kv[1].W, kv[1].current, kv[1].L))
    new_w = dict(zip([n for n, _ in ops], _compress([op.W for _, op in ops])))
    devs, rows = [], collections.defaultdict(list)
    for name, op in snap.column("device", "dc_op"):
        pins = dict(snap.value("device", name, "pins"))
        body = snap.value("device", name, "bulk").net
        k = new_w[name] / op.W
        devs.append(LayoutDevice(name, op.kind, pins["d"], pins["g"], pins["s"], body, float(new_w[name]), float(op.L),
                                 float(op.current * k), float(op.gm_id), float(op.vds), float(op.vsb),
                                 bool(snap.value("device", name, "is_diode")), True))
        rows[(op.kind, body)].append(name)
    groups = []
    for g in case.s1.value("graph", GRAPH_KEY, "matching_groups"):
        if g.status != "derived":
            continue
        hub = None if g.kind == "branch_symmetric" else (g.evidence.nets[0] if g.kind == "diff_pair" else g.evidence.nets[1])
        groups.append(MatchingGroup("%s|%s" % (g.evidence.rule, "+".join(sorted(g.members))), tuple(sorted(g.members)),
                                    g.kind, hub, tuple(PATTERNS)))
    for g in case.s1.value("graph", GRAPH_KEY, "matching_dispositions"):
        if g.kind in EXCLUDED and len(g.members) >= 2:
            groups.append(MatchingGroup("%s|%s" % (g.kind, "+".join(sorted(g.members))), tuple(sorted(g.members)), g.kind,
                                        None, tuple(PATTERNS)))
    row_groups = tuple(RowGroup("%s|%s" % key, key[0], key[1], tuple(sorted(v))) for key, v in sorted(rows.items()))
    return LayoutInput(tuple(devs), tuple(groups), row_groups, _pdk(pipe))


def _pdk(pipe):
    """정본 생성 경로 `LayoutPdk.from_decl`(4.1) 에서 폭 슬라이스만 kind 마다 셋(최소·가운데·레이아웃 전 폭 -- sizing 1.3)으로 줄인
    입력. 슬라이스마다 tol_V 표 1회 비용(실 LUT ~10 s)이 32장 전부면 test 가 수십 분이 된다(작성자 실측 첫 호출 448~1377 s).
    변형 전후 같은 PDK 입력이면 충분하다."""
    full = LayoutPdk.from_decl(pipe.env.lut, pipe.env.pdk)
    pre = dict(pipe.env.access.w_keys)
    keys = []
    for kind, ks in full.slice_width_keys:
        keep = sorted({ks[0], ks[len(ks) // 2], pre[kind]} & set(ks))
        keys.append((kind, tuple(keep)))
    return dataclasses.replace(full, slice_width_keys=tuple(keys))


def _run(pipe, case, theta):
    return run_layout(layout_input(pipe, case, theta), pipe.env.memo)


def _device_rows(d, nm):
    return (nm(d.name), d.finger_w_m, d.n_fingers, d.W_m, d.W_need_m, d.W_realized_m, d.W_err_rel, d.W_tol_lower,
            d.W_tol_upper, d.W_tol_effective, d.grid_dominated, d.origin, tuple(d.excluded_slices),
            tuple(sorted(n for _, n in d.rows)))


def _theta0(pipe, name):
    theta, res = pipe.theta0(name)
    assert theta is not None, "원래 회로 %s 의 층 0 시작점 없음(stop=%s)" % (name, res.stop)
    return theta[0]


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", CIRCUITS)
def test_floorplan_follows_renaming(pipe, name, seed):
    a, b = pipe.case(name), pipe.case(name, ("ren", seed))
    th = _theta0(pipe, name)
    ra, rb = _run(pipe, a, th), _run(pipe, b, map_theta(th, b))
    assert rb.floorplan.outline_area_m2 == ra.floorplan.outline_area_m2
    assert (rb.floorplan.bbox_width_m, rb.floorplan.bbox_height_m) == (ra.floorplan.bbox_width_m, ra.floorplan.bbox_height_m)
    assert sorted(_device_rows(d, lambda x: x) for d in rb.devices) == sorted(_device_rows(d, b.nm) for d in ra.devices)
    assert len(rb.rows) == len(ra.rows)
    # [U12] `GroupLayout.relaxed` 삭제(LY5 즉시 완화 제거, D-LY2) -> 비교 열에서 빼고 LY4 `l_mismatch` 를 치환표로 따라가게 비교
    def grp(g, nm):
        return (g.role, g.pattern, g.method, g.finger_w_m, g.dx, g.dy, g.ok, g.pending, g.reason,
                tuple(sorted((nm(m), L) for m, L in g.l_mismatch)))
    assert sorted(map(repr, (grp(g, lambda x: x) for g in rb.groups))) == sorted(map(repr, (grp(g, b.nm) for g in ra.groups)))
    assert sorted((b.nm(w.device), w.reason) for w in ra.w_requests) == sorted((w.device, w.reason) for w in rb.w_requests)
    assert (rb.coverage_ok, rb.w_invariant_ok) == (ra.coverage_ok, ra.w_invariant_ok)
    # [U12] 새 판정 축 면적 항목(grid_m, passive_area_m2, included)도 치환표를 따라간다
    assert (rb.floorplan.grid_m, rb.floorplan.passive_area_m2, rb.floorplan.included) == (
        ra.floorplan.grid_m, ra.floorplan.passive_area_m2, ra.floorplan.included)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", CIRCUITS)
def test_diffusion_follows_renaming(pipe, name, seed):
    """[U12] ly.diffusion(LY8, CONTRACT 4.10a) -- 소자별 ad·as·pd·ps·finger 수가 치환표를 따라간다.

    oracle (a) 변형 관계: 확산 기하는 엔진 접합 용량과 오라클 입력이 쓰는 성능 양이다(4.10a). 사용자 대원칙(topology·이름 무관)에서
    이름만 바꾼 회로의 소자별 drain·source 확산이 달라지면 같은 회로가 이름에 따라 다른 C_db·C_sb 를 받는다.
    """
    a, b = pipe.case(name), pipe.case(name, ("ren", seed))
    th = _theta0(pipe, name)
    ra, rb = _run(pipe, a, th), _run(pipe, b, map_theta(th, b))
    dif = lambda d, nm: (nm(d.name), d.finger_w_m, d.n_fingers, d.ad_m2, d.as_m2, d.pd_m, d.ps_m)  # noqa: E731
    assert sorted(dif(d, lambda x: x) for d in rb.diffusion) == sorted(dif(d, b.nm) for d in ra.diffusion)


@pytest.mark.parametrize("name", CIRCUITS)
def test_floorplan_same_after_shuffle_and_tag_noise(pipe, name):
    a, b = pipe.case(name), pipe.case(name, ("shuf", 1))
    th = _theta0(pipe, name)
    ra, rb = _run(pipe, a, th), _run(pipe, b, th)
    assert rb.floorplan == ra.floorplan
    assert rb.devices == ra.devices and rb.groups == ra.groups and rb.rows == ra.rows
    assert rb.diffusion == ra.diffusion                                      # [U12] ly.diffusion 도 같은 입력 = 같은 결과


def test_layout_inputs_are_nontrivial(pipe):
    """공허한 통과 방지: 비교 대상에 matching 그룹(차동쌍·미러·위 소자 대칭)이 실제로 배치된다."""
    roles = collections.Counter()
    for name in CIRCUITS:
        r = _run(pipe, pipe.case(name), _theta0(pipe, name))
        assert r.floorplan.outline_area_m2 > 0
        roles.update(g.role for g in r.groups)
    assert roles["diff_pair"] > 0 and roles["mirror"] > 0 and roles["branch_symmetric"] > 0, roles
