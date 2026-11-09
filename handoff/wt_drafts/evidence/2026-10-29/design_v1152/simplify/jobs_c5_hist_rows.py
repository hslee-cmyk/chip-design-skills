# 2차 단순화 커밋 5 -- 40 §8 R1~R33 이력표, §3.10.8 옛 문언 보존 행, 41 §7.2·§6.4-2 측정 서술 → design 이력
D40 = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md"
D41 = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md"
T40 = open(D40, encoding="utf-8").read()
T41 = open(D41, encoding="utf-8").read()
H = "design 이력 "


def between(T, a, b, inclusive_b=False):
    i = T.index(a)
    j = T.index(b, i)
    return T[i:j + (len(b) if inclusive_b else 0)]


o1435 = between(T40, "옛 문언: spec `search_method`가 정밀 경로", "**결정**(사용자 결정 2026-10-12 \"U-66은 (가)로\"")
o1436 = between(T40, "옛 문언: 사용자 결정 2026-10-12 \"U-51은 (나)로\"", "`perf.compensation_fixed_fallback` 계수", inclusive_b=True)
o1440 = between(T40, "옛 문언: 기본 비활성. spec `optional_stages`(DEC-75)", "(DEC-68 명명, §3.10.9 PN4 결정)", inclusive_b=True)
o1862 = between(T41, "  - 근거(2026-10-08 r1 실측): L = 20 µm·약반전", "(설계와 구현 일치).", inclusive_b=True)

JOBS = [
 dict(id="H40-17", file="40", title="§8 R1~R33 행별 표(축소 내용·출처·계획 근거·결정 전 상태·권고)", mode="lines",
      start="| # | 축소 내용 | 출처 | 계획 근거 | 상태 | 권고 |", end="---",
      new="R1~R33 행별 표(축소 내용·출처·계획 근거·결정 전 상태·권고) = " + H + "H40-17. 현행 처리는 위 결정 표와 각 행이 가리킨 절이 정본이다(R9·R10·R27의 v1.15.0 개정 -- 공급 능력 정의 DEC-65·DEC-104 R9, `driving_spec` 삭제 §3.1-1, 슬루·정착 = oracle `.tran` 판정 §3.8-3·§4-9·§4-10 -- 포함).\n"),
 dict(id="H40-18", file="40", title="§8 머리 '상태 열' 문장", mode="sub",
      old="아래 목록이 정본이다. 표의 '상태' 열은 결정 이전 상태를 남겨 둔 것이다.",
      new="아래 목록이 정본이다(R별 원 표 = " + H + "H40-17)."),
 dict(id="H40-19", file="40", title="§3.10.8 I-A11 옛 엔진 수치", mode="sub",
      old="옛 엔진의 선언식(36.6 MHz) 대 전체 응답(30.50 MHz) 차이다.",
      new="옛 엔진의 선언식 대 전체 응답 크로스오버 차이다(옛 수치 = " + H + "H40-19)."),
 dict(id="H40-20", file="40", title="§3.10.8 정밀 경로 선언 행의 옛 문언", mode="sub",
      old=o1435, new="(옛 문언 = " + H + "H40-20.) "),
 dict(id="H40-21", file="40", title="§3.10.8 보상 단 폴백(U-51) 행의 옛 문언", mode="sub",
      old=o1436, new="옛 문언(U-51 계수 기반 폴백) = " + H + "H40-21"),
 dict(id="H40-22", file="40", title="§3.10.8 N3.13 bisection 켜기 경로 행의 옛 문언", mode="sub",
      old=o1440, new="옛 문언(`optional_stages` 켜기 키) = " + H + "H40-22."),
 dict(id="H41-19", file="41", title="§7.2 분해 규칙의 r1 실측 근거 문장", mode="sub",
      old=o1862, new="  - 근거(r1 실측 -- 피드스루 조건만 쓰면 긴 L·약반전 칸에서 B를 크게 낮게 읽음) = " + H + "H41-19. as-built `E/lut/noise_planes.py`가 이 규칙이다."),
]
