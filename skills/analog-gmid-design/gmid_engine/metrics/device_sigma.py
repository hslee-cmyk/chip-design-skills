"""소자별 게이트 환산 mismatch σ 와 그 LUT 허용오차 (설계 41 §6.4-2, lut/CONTRACT 10절 -- `offset_analysis`·`mirror_ratio` 의 입력 만들기).

진입점: `device_sigmas(lut, mismatch, devices) -> ((라벨, σ_VGS V, tol V 또는 None), ...)` 또는 None(mismatch 감도 자료가 없다).

U3 `mismatch_sigma_vgs`(LUT 감도 열 DVGS_k × PDK bin slope 비 × √(W_ref/W))로 σ 를 구하고(복제하지 않는다), 허용오차는 변수 k 의 DVGS_k LOO 오차 `tol_mismatch_table(...).at(L, VDS, k)`
(V, 기준 폭 값)를 그 변수 기여와 같은 비율(기여 / |DVGS_k|)로 환산해 1차 전파한다: tol_σ = Σ_k (기여_k · tol_k·환산_k) / σ. 한 변수라도 tol 이 없으면(기여가 0 이 아닌데)
None. 폭이 PDK bin 최대 폭을 넘으면 finger 로 나눠 σ/√n (`_sigma`). `devices` = ((라벨, kind, w_key, L, W, vgs, vds, vsb), ...)(MOS 마다, 호출자가 정준 순서로 준다). 감도 표 없는 kind 가 하나라도 있으면 None 전체.
"""
import math

from gmid_engine.core import SealViolationError
from gmid_engine.lut import MismatchSigma, mismatch_dvgs, mismatch_sigma_vgs, tol_mismatch_table

REASON_NO_BLOCK = "lut_mismatch_no_block"                           # lut mismatch_sigma_vgs: 소자 (W, L) 을 품는 모델 bin 이 없다


def _sigma(memo, model, kind, w_key, length, vgs, vds, vsb, width):
    """(MismatchSigma, 병렬 finger 수). 소자 폭 W 가 PDK 모델 bin 의 최대 폭을 넘으면(sky130 은 W ≤ 100 µm 로 bin 되어 있다) 같은 L 의 최대 bin 폭 이하의 finger n = ceil(W / w_top)개로
    나눠 finger 폭 W/n 의 σ 를 구하고 독립 n 개의 합 σ/√n 으로 환산한다(모델 카드 slope 식의 1/√(l·w·mult) 과 같은 면적 환산 -- 레이아웃 전 가정 `ss_dev` 접합 기하의
    finger 분할과 같은 방향). bin 이 L 로도 없으면 원래 실패를 그대로 올린다."""
    try:
        return mismatch_sigma_vgs(memo, model, kind, w_key, length, vgs, vds, vsb, width), 1
    except SealViolationError as exc:
        covering = [b.wmax_m for b in model.blocks if b.lmin_m <= length <= b.lmax_m]
        if dict(exc.record.detail).get("reason") != REASON_NO_BLOCK or not covering or not width > max(covering):
            raise
    fingers = math.ceil(width / max(covering))
    base = mismatch_sigma_vgs(memo, model, kind, w_key, length, vgs, vds, vsb, width / fingers)
    root = math.sqrt(fingers)
    return MismatchSigma(base.sigma_v / root, tuple((p, v / root) for p, v in base.parts), base.model), fingers


def device_sigmas(lut, mismatch, devices):
    memo = lut.memo
    models = dict(mismatch.models)
    if any(kind not in memo.lut.mismatch or kind not in models for _l, kind, *_rest in devices):
        return None
    rows = []
    for label, kind, w_key, length, width, vgs, vds, vsb in devices:
        sigma, fingers = _sigma(memo, models[kind], kind, w_key, length, vgs, vds, vsb, width)
        sens = mismatch_dvgs(memo, kind, w_key, length, vgs, vds, vsb)
        table = tol_mismatch_table(memo, kind)
        extra = 0.0
        for param, part in sigma.parts:
            if part == 0.0:
                continue
            tol = table.at(length, vds, param)
            if tol is None:
                extra = None
                break
            extra += part * (tol * part / abs(sens.dvgs[param]) / math.sqrt(fingers))             # 같은 finger 환산을 허용오차에도
        rows.append((label, sigma.sigma_v, None if extra is None or not sigma.sigma_v > 0 else extra / sigma.sigma_v))
    return tuple(rows)
