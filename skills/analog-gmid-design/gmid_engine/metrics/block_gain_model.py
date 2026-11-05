"""블록 국소 소신호 모델 조립 -- 격자 축·전류 모델·여기·출력 (설계 41 §2.1 블록 국소 모델, §4.2 축 표; GB4 단계 A6 의 입력).

진입점: `block_gain_model_of(local, spec) -> (BlockModel | None, 미상 사유 | None)`  (`local` = `LocalInputs`, `spec` = `BlockSpec`).

**모형**(ω → 0, 커패시터는 열림, 설계 41 §2.5): 미지수 집합 U_b 는 봉인 모드(`block_model.block_local_gain`)와 같은 규칙이다 -- 고정 집합 F = 교류접지(`spec.ground` ∪ 레일) ∪ 여기 넷 ∪ 남의 블록 넷(`spec.others`),
U_b = (블록 노드 ∪ 블록 소자의 d·s·저항 단자 ∪ 저항 폐포) − F, 막다른 가지(저항 단자 하나뿐, 출력 아님, 스탬프 MOS 의 d·s·g·b 가 안 닿는 넷)는 뺀다. 각 MOS 는 `i = gm·(vg−vs) + gds·(vd−vs) +
gmb·(vb−vs)`(드레인에서 소스로, 양/음극 모두 LUT 크기 값을 같은 식에 넣는다), 저항은 컨덕턴스(조립은 `block_gain_rows.block_stamp_matrix` 하나). 여기 = 입력 넷 단위 전압(`excite` 가 가중을 주면 그대로,
차동 입력은 ±½), 출력 = 넷 하나(`+`) 또는 둘(`+`/`−`, 차동 블록). U_b 에 d 또는 s 가 닿는 비멤버 MOS 는 이 모드에 값이 없어(비멤버 동작점·θ 없음) 스탬프하지 않고 `BlockModel.omitted_load` 에 적는다
(그 부하 어드미턴스가 정해지지 않아 행 값은 상한 쪽이다). 스탬프 저항이 U_b 와 입력·남의 블록 넷을 이으면 `decomposed_only`(되먹임 -- 행 값은 상한이 아니다). 스탬프 MOS 의 gate·bulk 가 F·U_b 밖이고 전회로에
DC 전도 단자가 없는 넷(용량 전용 넷)을 읽으면 이 모드는 용량 값(비멤버 동작점)이 없어 모델이 없다(`charge_node_row_mode`).

**축**(설계 표, 등식으로 묶인 것은 축 하나):
* `vgs` -- 같은 VGS 묶음(같은 (gate, source) 넷)과 같은 자기동형 궤도의 MOS 를 한 그룹으로, 그룹마다 LUT VGS 격자 마디(= gm/ID 축; 행마다 `intrinsic_gain_curve` 의 강반전 분지 마디만 유효).
* `L` -- 같은 L 동치류(S1v derived)와 같은 궤도의 MOS 를 한 그룹으로, 그룹마다 LUT L 앵커(같은 bin 이웃 앵커 사이 안쪽 최대는 `block_gain_bound` 가 `row_gains(cont={L 축: L})` 로 찾는다).
* `vds` -- 비 diode MOS 를 같은 궤도끼리 묶어 그룹마다 LUT VDS 격자. diode(gate == drain) MOS 는 VDS = VGS 라 축이 없다(VDS 격자에 VGS 마디 값이 모두 있을 때; 없으면 diode 도 자기 축을 갖는다).
* `vsb` -- 소스 넷이 bulk 넷과 다른 MOS 를 같은 궤도끼리 묶어 그룹마다 LUT VS 격자(K3). 소스 = bulk 면 VSB = 격자 0 마디.
* `current` -- 블록 MOS 전류식(`CurrentBasis` 행)이 읽는 θ 전류 **대표** 원소(`LocalInputs.cur_rep`: 탐색 변수와 같은 자기동형 묶음, 부호 ±1, 구조적 0 은 항을 뺀다)마다 하나,
  격자 = θ 상자 [lo, hi] 위 로그 균등 `len(VGS 격자)`점(LUT 마디 수에서 유도). 블록에 저항(고정값·θ)이나 값 선언 전류원
  항이 하나도 없으면 gain 이 전류 공통 배율에 0차 동차라 **첫 원소를 기준(=1)으로 빼고** 나머지는 기준에 대한 비 [lo_j/hi_0, hi_j/lo_0] 로 센다.
* `resistor` -- DC 에 걸린 값 미선언(θ) 저항마다 컨덕턴스 로그 균등 격자(θ 상자 양끝의 1/R 사이). 값 선언 저항은 고정 컨덕턴스.
`current`·`resistor` 축은 연속량이라 `continuous` 로 표시한다(비단조 축 세분 대상, 41 §4.2).

**설계와 다른 점**(기록): (1) 저항 컨덕턴스 후보에 이웃 소자 gds 값을 더하지 않고 θ 상자 양끝 사이 로그 균등 격자 + 세분만 쓴다(세분이 극값을 찾는다). (2) 기둥 VDS 는 그룹마다 독립 축으로 두어
(KVL 로 묶이는 합을 쓰지 않음) 격자 곱이 설계보다 크다 -- 풀이 공간의 상위 집합이라 상한으로는 안전하고 Π 만 커진다.

미상 사유: 구동 입력 없음·셋 이상, 출력 없음·셋 이상, θ 전류/저항 상자 없음, 용량 전용 넷(`charge_node_row_mode`).
"""
import math

import numpy as np

from gmid_engine.graph import ELEMENT_MOS

from .achievability_types import (
    AXIS_KIND_CURRENT,
    AXIS_KIND_L,
    AXIS_KIND_RESISTOR,
    AXIS_KIND_VDS,
    AXIS_KIND_VGS,
    AXIS_KIND_VSB,
    REASON_CHARGE_NODE_ROW,
    REASON_MULTI_INPUT,
    REASON_NO_CURRENT_BOX,
    REASON_NO_OUTPUT,
    AxisSpec,
    BlockModel,
    MosLocal,
    ResLocal,
)

KIND_RESISTOR = "resistor"
REASON_NO_DRIVE = "block_input_not_driven"
REASON_NO_RESISTOR_BOX = "resistor_box_missing"
PAIR = ("first", "second")


def _find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def _groups(names, links, key):
    """names 를 `links`((a, b) 쌍들)로 합친 그룹 {대표: 멤버 tuple} -- 멤버·그룹 순서는 `key`(구조 색 순위, 이름이 정하지 않는다), 대표 = 멤버 중 key 최소."""
    parent = {n: n for n in names}
    for a, b in links:
        ra, rb = _find(parent, a), _find(parent, b)
        if ra != rb:
            parent[max(ra, rb, key=key)] = min(ra, rb, key=key)
    out = {}
    for n in names:
        out.setdefault(_find(parent, n), []).append(n)
    return {root: tuple(sorted(members, key=key)) for root, members in sorted(out.items(), key=lambda kv: key(kv[0]))}


def _same_key_links(names, key):
    """key(n) 가 같은(None 이 아닌) 원소끼리 잇는 쌍."""
    first = {}
    links = []
    for n in names:
        k = key(n)
        if k is None:
            continue
        if k in first:
            links.append((first[k], n))
        else:
            first[k] = n
    return links


def _patterns(spec, drive):
    weights = dict(spec.excite)
    if all(n in weights for n in drive):
        return (tuple((n, weights[n]) for n in drive),), None
    if len(drive) == 1:
        return (((drive[0], 1),),), None
    if len(drive) == len(PAIR):
        first, second = drive
        return (((first, 1 / 2), (second, -1 / 2)), ((first, 1 / 2), (second, 1 / 2))), None
    return None, REASON_MULTI_INPUT


def _outputs(spec, key):
    ordered = tuple(sorted(spec.outputs, key=key))
    if len(ordered) == 1:
        return ((ordered[0], 1),), None
    if len(ordered) == len(PAIR):
        return ((ordered[0], 1), (ordered[1], -1)), None
    return None, REASON_NO_OUTPUT


def _row_structure(local, spec, fixed, key):
    """행 모드 미지수 집합 U_b 와 스탬프 소자(모듈 문서, 봉인 모드 `block_model._structure` 와 같은 규칙).
    -> (U_b 넷 set, 스탬프 MOS tuple, 스탬프 저항 tuple, 생략 MOS tuple, 되먹임 여부, 용량 전용 넷을 읽는가)."""
    pins = local.pins
    resistors_all = sorted(n for n, k in local.kind.items() if k == KIND_RESISTOR)
    owned = set(spec.nodes)
    for m in spec.members:
        owned |= {pins[m]["d"], pins[m]["s"]}
    for r in spec.passives:
        if local.kind[r] == KIND_RESISTOR:
            owned |= {pins[r]["t0"], pins[r]["t1"]}
    unknown = owned - fixed
    changed = True
    while changed:                                                  # 저항 폐포: U_b 에 닿는 저항의 다른 끝(F 밖)
        changed = False
        for r in resistors_all:
            ends = {pins[r]["t0"], pins[r]["t1"]}
            if ends & unknown and ends - fixed - unknown:
                unknown |= ends - fixed
                changed = True
    outputs = set(spec.outputs)
    dropped = set()
    while True:
        stamped = {m for m in spec.members if pins[m]["d"] in unknown or pins[m]["s"] in unknown}
        touched = {pins[m][t] for m in stamped for t in ("d", "g", "s")} | {local.bulk.get(m) for m in stamped}
        live = {r for r in resistors_all if r not in dropped and (pins[r]["t0"] in unknown or pins[r]["t1"] in unknown)}
        count = {}
        for r in live:
            for t in ("t0", "t1"):
                count[pins[r][t]] = count.get(pins[r][t], 0) + 1
        dead = {n for n in unknown if n not in outputs and n not in touched and count.get(n, 0) == 1}
        if not dead:
            break
        unknown -= dead                                             # 막다른 가지: 넷과 그 저항을 뺀다(되풀이)
        dropped |= {r for r in live if pins[r]["t0"] in dead or pins[r]["t1"] in dead}
    attach = local.attach or {}
    charge = any(net is not None and net not in fixed and net not in unknown and attach.get(net, 0) == 0
                 for m in stamped for net in (pins[m]["g"], local.bulk.get(m)))
    omitted = tuple(sorted((n for n in pins if local.cls.get(n) == ELEMENT_MOS and n not in spec.members
                            and (pins[n]["d"] in unknown or pins[n]["s"] in unknown)), key=key))
    across = set(spec.inputs) | (set(spec.others) - set(spec.nodes))
    decomposed = any((pins[r]["t0"] in across and pins[r]["t1"] in unknown) or (pins[r]["t1"] in across and pins[r]["t0"] in unknown) for r in live)
    return unknown, tuple(sorted(stamped, key=key)), tuple(sorted(live, key=key)), omitted, decomposed, charge


def _log_grid(lo, hi, count):
    return np.exp(np.linspace(math.log(lo), math.log(hi), count))


def block_gain_model_of(local, spec):
    device_colour, node_colour = local.device_colour or {}, local.node_colour or {}

    def dkey(name):
        return device_colour.get(name, -1), name          # 구조 색 순위(이름은 색이 없을 때만 순서를 정한다)

    def nkey(name):
        return node_colour.get(name, -1), name

    ground = frozenset(spec.ground) | local.rails
    drive = tuple(sorted((n for n in (spec.inputs if spec.drive is None else spec.drive) if n not in ground), key=nkey))
    if not drive:
        return None, REASON_NO_DRIVE
    patterns, reason = _patterns(spec, drive)
    if patterns is None:
        return None, reason
    outputs, reason = _outputs(spec, nkey)
    if outputs is None:
        return None, reason
    fixed = set(ground) | set(drive) | (set(spec.others) - set(spec.nodes))
    unknown, mos, resistors, omitted, decomposed, charge = _row_structure(local, spec, fixed, dkey)
    if charge:
        return None, REASON_CHARGE_NODE_ROW
    nodes = tuple(sorted(unknown, key=nkey))
    known = set(nodes) | set(drive)
    if any(net not in known and net not in ground for net, _sign in outputs):
        return None, REASON_NO_OUTPUT
    n_l, n_v, n_d, n_s = (len(g) for g in local.grids)       # (L, VGS, VDS, VS) 격자 길이
    orbit = local.orbit
    diode = {m: local.pins[m]["g"] == local.pins[m]["d"] for m in mos}
    tied_ok = all(any(abs(v - w) <= math.ulp(max(abs(v), abs(w))) for w in local.grids[2]) for v in local.grids[1])
    free_vds = tuple(m for m in mos if not (diode[m] and tied_ok))
    free_vsb = tuple(m for m in mos if local.bulk.get(m) != local.pins[m]["s"])
    g_vgs = _groups(mos, _same_key_links(mos, lambda m: orbit.get(m)) + _same_key_links(mos, lambda m: (local.pins[m]["g"], local.pins[m]["s"])), dkey)
    g_l = _groups(mos, _same_key_links(mos, lambda m: orbit.get(m)) + _same_key_links(mos, lambda m: local.l_label.get(m)), dkey)
    g_vds = _groups(free_vds, _same_key_links(free_vds, lambda m: orbit.get(m)), dkey)
    g_vsb = _groups(free_vsb, _same_key_links(free_vsb, lambda m: orbit.get(m)), dkey)
    in_vds = {m for members in g_vds.values() for m in members}
    in_vsb = {m for members in g_vsb.values() for m in members}
    axes = []
    index = {}

    def add(kind, members, size, values, continuous=False):
        axes.append(AxisSpec(kind, members, size, values, continuous))
        for m in members:
            index[(kind, m)] = len(axes) - 1

    for members in g_vgs.values():
        add(AXIS_KIND_VGS, members, n_v, np.asarray(local.grids[1], dtype=float))
    for members in g_l.values():
        add(AXIS_KIND_L, members, n_l, np.asarray(local.grids[0], dtype=float))
    for members in g_vds.values():
        add(AXIS_KIND_VDS, members, n_d, np.asarray(local.grids[2], dtype=float))
    for members in g_vsb.values():
        add(AXIS_KIND_VSB, members, n_s, np.asarray(local.grids[3], dtype=float))
    # ---- 전류식과 전류 축: 항의 원천을 (대표 원소, 부호)로 바꾼다(자기동형 묶음 = 탐색 변수와 같은 묶음, 구조적 0 은 항을 뺀다)
    def terms_of(m):
        out = []
        for source, coeff in local.basis_rows.get(m, ()):
            if source in local.fixed:
                out.append((source, coeff, True))
                continue
            rep, sign = local.cur_rep.get(source, (source, 1))
            if rep is not None:
                out.append((rep, coeff * sign, False))
        return tuple(out)

    terms = {m: terms_of(m) for m in mos}
    used = sorted({source for m in mos for source, _c, is_fixed in terms[m] if not is_fixed}, key=dkey)
    uses_fixed = any(is_fixed for m in mos for _s, _c, is_fixed in terms[m])
    theta_r = [r for r in resistors if local.element_value.get(r) is None]
    homogeneous = bool(used) and not uses_fixed and not resistors
    if any(source not in local.current_box for source in used):
        return None, REASON_NO_CURRENT_BOX
    reference = used[0] if homogeneous else None
    for source in used:
        if source == reference:
            continue
        lo, hi = local.current_box[source]
        if homogeneous:
            lo, hi = lo / local.current_box[reference][1], hi / local.current_box[reference][0]
        add(AXIS_KIND_CURRENT, (source,), n_v, _log_grid(lo, hi, n_v), True)
    if any(r not in local.resistor_box for r in theta_r):
        return None, REASON_NO_RESISTOR_BOX
    for r in theta_r:
        lo_r, hi_r = local.resistor_box[r]
        add(AXIS_KIND_RESISTOR, (r,), n_v, _log_grid(1 / hi_r, 1 / lo_r, n_v), True)
    mos_local = []
    for m in mos:
        pins = local.pins[m]
        current = []
        for source, coeff, is_fixed in terms[m]:
            if is_fixed:
                current.append((-1, coeff * local.fixed[source]))
            elif source == reference:
                current.append((-1, coeff))                     # 기준 원소 = 단위 1 (비 축의 분모)
            else:
                current.append((index[(AXIS_KIND_CURRENT, source)], coeff))
        mos_local.append(MosLocal(m, local.kind[m], pins["d"], pins["g"], pins["s"], local.bulk.get(m),
                                  index[(AXIS_KIND_VGS, m)], index[(AXIS_KIND_L, m)],
                                  index[(AXIS_KIND_VDS, m)] if m in in_vds else -1,
                                  index[(AXIS_KIND_VSB, m)] if m in in_vsb else -1, tuple(current)))
    res_local = []
    for r in resistors:
        pins = local.pins[r]
        if r in theta_r:
            res_local.append(ResLocal(r, pins["t0"], pins["t1"], index[(AXIS_KIND_RESISTOR, r)], None))
        else:
            res_local.append(ResLocal(r, pins["t0"], pins["t1"], -1, 1 / local.element_value[r]))
    pi = math.prod(a.size for a in axes)
    model = BlockModel(spec.key, spec.role, nodes, drive, patterns, outputs, tuple(mos_local), tuple(res_local), tuple(axes), pi,
                       () if reference is None else (reference,), omitted, decomposed)
    return model, None

