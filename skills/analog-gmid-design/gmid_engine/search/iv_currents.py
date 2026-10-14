"""전류 출발값의 선형 구조 -- 블록 gm 에서 소자·θ 전류로 (설계 41 §6.5 '나머지 소자는 미러 비와 KCL 로 전파한다', J 추가 범위 U13 FF 묶음).

진입점: `current_model(ctx, gm_id, lengths) -> CurrentModel`.

**모델**: 블록 b 마다 gm_b(= 그 블록 입력 소자 하나의 gm, S)가 매크로 모델(`macro_poles`)의 미지수다. 입력 소자 d 의 전류는 I_d = gm_b / (gm/ID)_d 이고, KCL 기저
(`CurrentBasis.rows`: MOS 전류 = Σ 계수 · θ 전류 원소)가 이 식을 θ 전류 원소에 관한 선형 방정식으로 바꾼다. 모든 전류를 **아핀 벡터**(길이 n_b + 1: gm_b 계수들과 상수항 --
값 선언 이상 전류원이 상수항으로 들어온다)로 들고, 항이 하나만 미지인 방정식부터 차례로 풀어 θ 전류 원소를 정한다(전파). 그래서

* 같은 가지 직렬 소자(캐스코드)는 같은 행을 읽으므로 같은 전류를 가진다.
* 미러 출력·꼬리 전류는 기저 행의 계수(KCL 비)로 정해진다 -- 계수가 미러 비다.
* feedforward 묶음(41 §1.12.2)의 신호 셀은 방정식 `I_c = G_ff / (gm/ID)_c`, `G_ff = r_ff · gm_in(B_b)`, `r_ff = 1`(영점 상쇄 조건 후보, 41 §6.5)을 더한다. B_b = 묶음이 처음 우회하는
  주경로 블록. 그 묶음 소자의 전류가 FF 경로 미러 비로 전파된다.
* **미러**: 같은 VGS 묶음(쓰기 계획 `parallel_vgs`)의 멤버 전류 = 뿌리 전류(폭 비 1 -- 비를 정할 근거가 없다). 이 규칙이 입력 소자 방정식으로 닿지 않는 바이어스 미러 출력을 정한다.
* 어느 입력 소자 방정식으로도 정해지지 않은 θ 전류 원소(바이어스 가지 등)는 `unassigned` 로 남는다 -- 호출부(`start_intervals`)가 채운다. 조용히 0 으로 두지 않는다.
방정식 순서는 구조 색(`dc_colour`)과 이름 순이 아니라 색 순서만 따른다(이름 전단사에 값이 같다).

**블록 순서와 입력**: 전달 뷰의 이득·버퍼·복합 블록을 (stage, 출력 넷 구조 색) 순으로 둔다. 블록 출력 넷 = 출력노드 중 색이 가장 작은 것, 입력 넷 = 다른 블록의 출력 넷인 블록 입력(가장 앞 stage 의 것),
없으면 포트 구동(None). (버퍼 블록의 stage 는 입력 넷의 거리라 앞 블록과 같을 수 있어 stage 대소로 거르지 않고 자기 출력 넷만 뺀다.) 블록 부호 = 셀 부호의 곱(CS·미러의 CS 읽기 = −1, 그 밖 +1)을 입력 소자 하나·미러 역할 하나만 센 것. 전체 부호는 맞추지 않는다 -- 위상 여유는 T(0) 위상을 기준으로 재므로(metrics `analyze_loop`) 되먹임 부호 관례와 무관하다.
**소자 용량 계수**: (gm/ID, L) 의 W/I = L / IDu 와 기준 (VDS, VSB) 의 `caps` 로, 전류 1 A 당 cgg·cdrain(cdd 가 있으면 cdd, 없으면 cgd)을 `per_amp` 에 둔다 -- 노드 용량이 gm_b 에 선형이 된다.
"""
import dataclasses

import numpy as np

from gmid_engine.core import SchemaRejectedError, SealViolationError
from gmid_engine.lut import caps

from ._helpers_curves import QUANTITY_IDU, QUANTITY_VGS, curve_bundle_of, curve_value


_KIND_BUFFER = "buffer"
_BLOCK_KINDS = ("gain", _KIND_BUFFER, "composite")
_ROLE_INPUT = ("input", "follower")
_ROLE_MIRROR = "mirror"
_CELL_CS = "cs"
_LUT_ERRORS = (SealViolationError, SchemaRejectedError, KeyError, ValueError)


@dataclasses.dataclass(frozen=True)
class BlockInfo:
    """`key` = 블록 키, `out_net`·`in_net` = 매크로 노드 넷(in_net None = 포트 구동), `sign` = 블록 부호(±1), `inputs` = 입력 소자 이름(색 순), `stage` = stage 번호,
    `buffer` = 버퍼 블록(팔로어: 출력 컨덕턴스가 gm 이라 이득 ≈ 1)."""

    key: tuple
    out_net: str
    in_net: object
    sign: int
    inputs: tuple
    stage: int
    buffer: bool = False


@dataclasses.dataclass(frozen=True, eq=False)
class CurrentModel:
    """`blocks` = BlockInfo tuple, `affine` = {θ 전류 원소·이상원: 길이 n_b + 1 벡터}, `mos` = {MOS: 전류 아핀 벡터}(전류를 정하지 못한 MOS 는 없다),
    `unassigned` = 방정식으로 정해지지 않은 θ 전류 원소(색 순), `per_amp` = {MOS: (cgg [F/A], cdrain [F/A], W/I [m/A])}, `ff` = ((탭 넷, 합류 넷, 부호, gm_ff 벡터), ...),
    `lacking_caps` = 용량을 LUT 에서 못 읽은 MOS."""

    blocks: tuple
    affine: object
    mos: object
    unassigned: tuple
    per_amp: object
    ff: tuple
    lacking_caps: tuple

    def current(self, device, gm):
        """MOS `device` 의 전류(A) -- gm = 블록 gm 벡터(S, 길이 n_b). 정해지지 않았으면 None."""
        vec = self.mos.get(device)
        return None if vec is None else float(vec[:-1] @ gm + vec[-1])

    def element(self, name, gm):
        """θ 전류 원소(또는 이상원) 전류(A) -- 정해지지 않았으면 None."""
        vec = self.affine.get(name)
        return None if vec is None else float(vec[:-1] @ gm + vec[-1])


def _blocks(ctx):
    if ctx.transfer is None:
        return ()
    cells = {c.dev: c.kind for c in ctx.transfer.cells}
    colour = ctx.node_colour
    chosen = sorted((b for b in ctx.transfer.blocks if b.kind in _BLOCK_KINDS and b.outputs),
                    key=lambda b: (b.stage, min(colour[n] for n in b.outputs)))
    out_of = {b.key: min(b.outputs, key=lambda n: colour[n]) for b in chosen}
    produced = {out_of[b.key]: b.stage for b in chosen}
    infos = []
    for b in chosen:
        feeding = sorted(((produced[n], colour[n], n) for n in b.inputs if n in produced and n != out_of[b.key]))
        roles = dict(b.roles)
        inputs = tuple(sorted((n for n, r in b.roles if r in _ROLE_INPUT and n in ctx.by_name), key=lambda n: (ctx.by_name[n].colour, n)))
        negative = int(any(cells.get(n) == _CELL_CS for n in inputs[:1])) + int(any(r == _ROLE_MIRROR and cells.get(n) == _CELL_CS for n, r in roles.items()))
        infos.append(BlockInfo(b.key, out_of[b.key], feeding[0][2] if feeding else None, -1 if negative % 2 else 1, inputs, b.stage, b.kind == _KIND_BUFFER))
    return tuple(infos)


def _per_amp(ctx, gm_id, lengths):
    out, lacking = {}, []
    for d in ctx.devices:
        bundle = curve_bundle_of(ctx, d.name, d.kind, lengths[d.name])
        if bundle is None:
            lacking.append(d.name)
            continue
        idu = curve_value(bundle, QUANTITY_IDU, gm_id[d.name])
        w_per_a = lengths[d.name] / idu
        try:
            c = caps(ctx.memo, d.kind, lengths[d.name], curve_value(bundle, QUANTITY_VGS, gm_id[d.name]), bundle[QUANTITY_IDU].vds,
                     bundle[QUANTITY_IDU].vsb, w_per_a)
        except _LUT_ERRORS:
            lacking.append(d.name)
            continue
        out[d.name] = (float(c.cgg), float(c.cdd if c.cdd is not None else c.cgd), float(w_per_a))
    return out, tuple(lacking)


def current_model(ctx, gm_id, lengths):
    blocks = _blocks(ctx)
    size = len(blocks) + 1
    index = {b.key: i for i, b in enumerate(blocks)}
    rows = {name: tuple((t.source, t.num / t.den) for t in terms) for name, terms in ctx.basis.rows}
    known = {}
    for source, amp in ctx.basis.fixed:
        vec = np.zeros(size)
        vec[-1] = float(amp)
        known[source] = vec
    equations = []
    for i, b in enumerate(blocks):
        for name in b.inputs:
            rhs = np.zeros(size)
            rhs[i] = 1.0 / gm_id[name]
            equations.append((ctx.by_name[name].colour, name, rhs))
    ff = []
    for f in (() if ctx.transfer is None else ctx.transfer.feedforward):
        first = next((index[k] for k in f.bypassed_blocks if k in index), None)
        if first is None:
            continue
        gm_ff = np.zeros(size)
        gm_ff[first] = 1.0                              # G_ff = r_ff · gm_in(B_b), r_ff = 1 (41 §6.5)
        ff.append((f.tap, f.merge, f.sign, gm_ff))
        for name in f.cells:
            if name in ctx.by_name:
                equations.append((ctx.by_name[name].colour, name, gm_ff / gm_id[name]))
    equations.sort(key=lambda e: (e[0], e[1]))

    def propagate():
        progress = False
        for _colour, name, rhs in equations:
            terms = rows.get(name, ())
            unknown = [(s, c) for s, c in terms if s not in known]
            if len(unknown) != 1:
                continue
            source, coeff = unknown[0]
            rest = sum((c * known[s] for s, c in terms if s in known), np.zeros(size))
            known[source] = (rhs - rest) / coeff
            progress = True
        return progress

    def mirror():
        """같은 VGS 묶음(`DeviceInfo.group`, 쓰기 계획 `parallel_vgs`)의 멤버는 뿌리와 같은 gm/ID·같은 L 이라 전류 = 폭 비 × 뿌리 전류다 -- 폭 비를 정할 근거가 없으면 1(같은 크기 미러,
        `mirror_ratio` 기본). 뿌리 전류가 정해졌고 멤버 행에 미지 원소가 하나뿐이면 그 원소를 푼다."""
        progress = False
        for d in ctx.devices:
            terms = rows.get(d.name, ())
            unknown = [(s, c) for s, c in terms if s not in known]
            root_terms = rows.get(d.group, ())
            if d.group == d.name or len(unknown) != 1 or not root_terms or any(s not in known for s, _c in root_terms):
                continue
            source, coeff = unknown[0]
            rest = sum((c * known[s] for s, c in terms if s in known), np.zeros(size))
            known[source] = (sum((c * known[s] for s, c in root_terms), np.zeros(size)) - rest) / coeff
            progress = True
        return progress

    while propagate() or mirror():
        pass
    mos = {}
    for d in ctx.devices:
        terms = rows.get(d.name, ())
        if terms and all(s in known for s, _c in terms):
            mos[d.name] = sum((c * known[s] for s, c in terms), np.zeros(size))
    unassigned = tuple(s for s in ctx.basis.free if s not in known)
    per_amp, lacking = _per_amp(ctx, gm_id, lengths)
    return CurrentModel(blocks, known, mos, unassigned, per_amp, tuple(ff), lacking)
