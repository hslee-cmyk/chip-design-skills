"""봉인 6 벌크 역바이어스 계산 블록 (계획 N3.6 항목 6, DEC-61, 설계 3.6; EO-1 범위 4 -- 경계 0 V, O-210 RR-7).

진입점: `dc_seal_bulk_reverse`(`@compute_block`) -- `dc_seal_bulk_reverse(snapshot)`.

MOS 마다 source–bulk·drain–bulk 접합이 역바이어스인지 노드전압 차로 본다(LUT 부호 규약 크기: vsb = s·(V(s) − V(b)), vdb = vds + vsb). 순방향 크기는
`junction_forward(vds, vsb) = max(0, −vsb, −(vds + vsb))`(식 하나, `ss_off_op` 과 공용). **판정 경계는 0 V**다: 순방향 크기 > 0 이면 크기와 무관하게 fail(문턱 없음),
0 이면 pass. `tol_V`(`dc_tol_v`, id_equivalent)는 판정에 쓰지 않는다 -- 띠 기록만: detail `indistinct` = 순방향 0 이고 min(vsb, vds + vsb) < tol_V 인
((소자, min 값), ...) 이름순, `band_undefined` = tol_V 미정 소자(항목을 미정으로 만들지 않는다 -- 미정은 봉인 2 가 낸다).
보고 칸 `magnitude`·`tol`·`margin`(크기/tol_V)·`worst`·`n_checked`·`n_undefined` 는 `judge` 의 보고 형식 그대로이고 status·devices 는 위 경계가 정한다.
"""
import dataclasses

from gmid_engine.core import compute_block

from ._helpers_seal import judge
from .junction_forward import junction_forward
from .s2_values import DC_KEY, DC_SEAL_BULK_WRITER, SEAL_BULK_REVERSE, SEAL_FAIL, SEAL_PASS

READS = (("device", "dc_op"), ("device", "dc_tol_v"))
WRITES = (("graph", "dc_seal_6"),)


@compute_block(DC_SEAL_BULK_WRITER, reads=READS, writes=WRITES)
def dc_seal_bulk_reverse(projection):
    tol_v = dict(projection.column("device", "dc_tol_v"))
    rows, forward_devices, band, band_undefined = [], [], [], []
    for m, op in projection.column("device", "dc_op"):
        forward = junction_forward(op.vds, op.vsb)
        rows.append((m, forward, tol_v[m], (m,), ()))
        if forward > 0:
            forward_devices.append(m)
        if tol_v[m] is None:
            band_undefined.append(m)
        elif forward == 0 and min(op.vsb, op.vds + op.vsb) < tol_v[m]:
            band.append((m, min(op.vsb, op.vds + op.vsb)))
    item = judge(SEAL_BULK_REVERSE, rows)
    detail = dict(item.detail)
    for key, found in (("indistinct", tuple(sorted(band))), ("band_undefined", tuple(sorted(band_undefined)))):
        if found:
            detail[key] = found
    item = dataclasses.replace(item, status=SEAL_FAIL if forward_devices else SEAL_PASS, devices=tuple(sorted(forward_devices)),
                               nodes=(), detail=tuple(sorted(detail.items())))
    return {("graph", "dc_seal_6"): {DC_KEY: item}}
