"""벌크 접합 순방향 크기 -- 식 하나 (EO-1 범위 4, 설계 41 §4.8-10, 계획 N3.6 표 6행, O-210 RR-7).

진입점: `junction_forward(vds, vsb) -> float` = max(0, −vsb, −(vds + vsb)). LUT 부호 규약 크기(nmos 그대로, pmos 부호 반전)의 vds, vsb 를 받아
source–bulk(−vsb)·drain–bulk(−vdb, vdb = vds + vsb) 접합의 순방향 크기를 낸다. 0 이면 역바이어스(경계 0 V 정확히도 순방향 아님), > 0 이면 순방향이다.
문턱·tol 입력이 없다. 순수 함수이고 값을 저장하지 않는다. 호출 자리 = 봉인 6(`dc_seal_bulk_reverse`, 봉인점 `dc_op`)과 `ss_off_op`(off 소자 동작점) 둘.
"""


def junction_forward(vds, vsb):
    return max(0.0, -vsb, -(vds + vsb))
