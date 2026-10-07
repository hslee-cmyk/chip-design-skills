"""폭 키 판정 공용 helper -- 슬라이스 폭(`provenance`)·기준 LUT 폭·검증 중점 파일 폭(`lut_set`)이 같은 규칙을 쓰게 한 곳에 둔다.

규칙(lut/CONTRACT.md 1.3, r3): 폭 키 = round(W / grid). |W/grid − 키| ≤ 2·ulp(W/grid) 이면 그 키(위·아래 대칭), 넘으면
제조 격자 위의 폭이 아니다. 2 ulp = float 반올림 3회(µm × 1e-6 곱·격자·나눗셈)의 상계.
"""
import math


def width_key(w_m, grid_m):
    """`(키, 격자 위 여부)`: 키 = round(w_m / grid_m), 격자 위 = 몫과 키의 차가 2·ulp(몫) 이내."""
    quotient = w_m / grid_m
    key = round(quotient)
    return key, abs(quotient - key) <= 2 * math.ulp(quotient)
