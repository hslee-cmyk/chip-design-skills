"""소자별 게이트 환산 mismatch σ 와 그 LUT 허용오차 (설계 41 §6.4-2, lut/CONTRACT 10절 -- `offset_analysis`·`mirror_ratio` 의 입력 만들기).

진입점: `device_sigmas(lut, mismatch, devices) -> ((라벨, σ_VGS V, tol V 또는 None), ...)` 또는 None(mismatch 감도 자료가 없다).

U3 `mismatch_sigma_vgs`(LUT 감도 열 DVGS_k × PDK bin slope 비 × √(W_ref/W))로 σ 를 구하고(복제하지 않는다), 허용오차는 변수 k 의 DVGS_k LOO 오차 `tol_mismatch_table(...).at(L, VDS, k)`
(V, 기준 폭 값)를 그 변수 기여와 같은 비율(기여 / |DVGS_k|)로 환산해 1차 전파한다: tol_σ = Σ_k (기여_k · tol_k·환산_k) / σ. 한 변수라도 tol 이 없으면(기여가 0 이 아닌데)
None. `devices` = ((라벨, kind, w_key, L, W, vgs, vds, vsb, w_f), ...)(MOS 마다, 호출자가 정준 순서로 준다): `W` = 총 폭(`DeviceOp.W` -- 면적 항), `w_f` = 손가락 폭(slope bin 을 고르는
폭, 범위 2b). 총 폭을 모델 bin 최대 폭으로 쪼개는 finger 분할은 없다 -- 손가락 폭은 슬라이스 폭(PDK bin 안)이라 slope bin 은 w_f 가 정하고 면적은 W 가 정한다. 감도 표 없는 kind 가 하나라도 있으면 None 전체.
"""
from gmid_engine.lut import mismatch_dvgs, mismatch_sigma_vgs, tol_mismatch_table


def device_sigmas(lut, mismatch, devices):
    memo = lut.memo
    models = dict(mismatch.models)
    if any(kind not in memo.lut.mismatch or kind not in models for _l, kind, *_rest in devices):
        return None
    rows = []
    for label, kind, w_key, length, width, vgs, vds, vsb, w_f in devices:
        sigma = mismatch_sigma_vgs(memo, models[kind], kind, w_key, length, vgs, vds, vsb, w_f, width)
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
            extra += part * (tol * part / abs(sens.dvgs[param]))
        rows.append((label, sigma.sigma_v, None if extra is None or not sigma.sigma_v > 0 else extra / sigma.sigma_v))
    return tuple(rows)
