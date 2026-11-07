"""출발 w_f 칸 선택에 쓰는 멤버 출발 W (FS-1, 계획 DEC-108 (3), 설계 40 §3.7-B 3, interface card §3.3).

진입점: `member_start_w(mos, writers, partner, current, length, ln_idu) -> {이름: float | why}`. 출발 블록 안 값이다(필드 아님, 호출자 `start_intervals` 하나).

* `mos` = MOS 이름, `writers` = 출발 단계가 ln IDu 좌표를 두는 멤버 집합, `partner` = {종속 멤버: KVL 짝 쓰기 멤버 또는 None}, `current` = {이름: 1회차 전류(A) 또는 None}(41 §6.1 4 -- 4단계
  `matching_bounds` 첫 호출에 넘기는 것과 같은 dict), `length` = {이름: 5의 L}, `ln_idu` = {쓰기 멤버: 1회차 ln IDu(float) 또는 `reference_slice_undefined`}.
* 쓰기 멤버: 전류가 없으면 `no_member_density`, ln IDu 가 why 문자열이면 그 문자열, 아니면 I·L/exp(ln IDu). 종속 멤버: 짝이 없거나 전류가 없으면 `no_member_density`, 짝의 ln IDu 가 why 문자열이면
  그 문자열, 아니면 I_i·L_i/exp(ln IDu_짝) -- 같은 VGS·VSB·L 이면 단위 폭 전류 밀도가 같다(대체값을 만들지 않는다, 짝 밀도는 차용이 아니라 KVL 등식).
"""
import math

WHY_NO_MEMBER_DENSITY = "no_member_density"


def member_start_w(mos, writers, partner, current, length, ln_idu):
    out = {}
    for name in mos:
        source = name if name in writers else partner.get(name)         # 밀도를 내는 쓰기 멤버(자기 자신 또는 KVL 짝)
        if source is None or current.get(name) is None:
            out[name] = WHY_NO_MEMBER_DENSITY
        elif isinstance(ln_idu[source], str):
            out[name] = ln_idu[source]
        else:
            out[name] = current[name] * length[name] / math.exp(ln_idu[source])
    return out
