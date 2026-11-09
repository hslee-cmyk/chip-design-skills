# 2차 단순화 커밋 4 -- 구현 끝난 card 절(40 §2.4.3 card 1 삭제 목록, §2.4.13 NFR-4 측정·card 수행 목록, §2.4.14 XRUN-F1 card A·B 행, 41 §5.10-1) → design 이력
import re
D = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md"
T = open(D, encoding="utf-8").read()
H = "design 이력 "


def between(a, b):
    i = T.index(a)
    j = T.index(b, i)
    return T[i:j]


old669 = between("실측(2026-10-15, Windows `EnumProcessModules`", "Linux는 `/proc/self/maps`")
old672 = between("| 비용 | 측정 3(9회로", "\n").rstrip("\r")
old699 = between("실측(2026-10-15): 측정 3과 이 설계 측정의 실행 191개", "비교기 첫 실행이 이것을 판정하고")
CARD_AB = {"A", "B", "A·B"}


def cells(s):
    out, cur, tick, i = [], "", False, 0
    while i < len(s):
        ch = s[i]
        if ch == "`":
            tick = not tick
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur += "|"; i += 2; continue
        if ch == "|" and not tick:
            out.append(cur); cur = ""
        else:
            cur += ch
        i += 1
    out.append(cur)
    return out[1:-1]


def card_ab(line):
    s = line.rstrip("\r")
    if not s.startswith("| ") or s.startswith("|---"):
        return False
    c = cells(s)
    return len(c) >= 2 and c[1].strip() in CARD_AB


JOBS = [
 dict(id="H40-02", file="40", title="§2.4.3 삭제·변경 목록(card 1 실행 사이 재사용 제거 -- 병합 f23aec8로 끝남)", mode="lines",
      start="**삭제·변경 목록**(2026-10-15 grep, 34932a9", end="**front 조회 전용 읽기 경로**",
      new="**삭제·변경 목록**: card 1(실행 사이 재사용 제거, 병합 f23aec8)이 끝냈다 -- 이름별 grep 범위·as-built 위치·처리 표 = " + H + "H40-02.\n"),
 dict(id="H40-03", file="40", title="§2.4.3 test 삭제·변경 목록(card 1)", mode="lines",
      start="**test 삭제·변경 목록**(2026-10-15 grep", end=None,
      new="**test 삭제·변경 목록**: card 1로 끝남 -- 목록 = " + H + "H40-03."),
 dict(id="H40-04", file="40", title="§2.4.3 실행 시간 영향(측정)", mode="lines",
      start="**실행 시간 영향**(측정·정적 판단", end=None,
      new="**실행 시간 영향**(측정) = " + H + "H40-04."),
 dict(id="H40-05", file="40", title="§2.4.13 (1) BLAS 라이브러리 찾기 행의 열거 실측 문장", mode="sub",
      old=old669, new="(열거 실측 = " + H + "H40-05.) "),
 dict(id="H40-06", file="40", title="§2.4.13 (1) 비용 행(측정 3)", mode="sub",
      old=old672, new="| 비용 | 고정 비용은 잡음 수준이다(측정 3 -- " + H + "H40-06) |"),
 dict(id="H40-07", file="40", title="§2.4.13 (1) 고정 방법 실측 표(pin_probe)", mode="lines",
      start="고정 방법 실측(2026-10-15", end="**(2) 검증 기준 (③)**",
      new="고정 방법 실측(환경 변수만으로는 numpy가 먼저 import된 프로세스를 고정하지 못해 설정 API가 필요하다는 근거) = " + H + "H40-07.\n"),
 dict(id="H40-08", file="40", title="§2.4.13 (2) 1차 검사 전제 뒤 실측 문장(측정 3, 실행 191개)", mode="sub",
      old=old699, new="(측정 = " + H + "H40-08.) "),
 dict(id="H40-09", file="40", title="§2.4.13 (4) 분해능을 넘는 필드 측정·선형 추정 문단", mode="lines",
      start="출처가 있어도 측정 차이가 분해능을 넘는 필드가 있다.", end=None,
      new="출처가 있어도 측정 차이가 선언 분해능을 넘는 필드(매크로 풀이 하류 -- 매크로 해는 \\|ln \\|H\\|\\| ≤ √tol 안에서 같은 해로 받아들여진다; 예 nmcnr `start.row` `w_m`·`area_est_m2`, 측정·선형 추정 = " + H + "H40-09)의 비교 폭은 max(선언 분해능, 위 감도 전파값)이다(Q-N4 확정, 사용자 결정 2026-10-15 \"기본안대로 진행해\", U-80). 감도 전파값을 만들 수 없으면 그 칸은 판정 불능이다."),
 dict(id="H40-10", file="40", title="§2.4.13 (5) 이 card의 완료 조건(card NFR-4 -- 병합으로 끝남)", mode="lines",
      start="- **이 card의 완료 조건**(v1.10 정정)", end=None,
      new="- **이 card의 완료 조건**: card NFR-4 병합으로 끝남 -- (i)~(iv) 원문 = " + H + "H40-10. 매크로 해 주입 진입(NFR4-F2)은 완료에 필요하지 않았다(같은 환경 1차 검사는 비트 비교)."),
 dict(id="H40-11", file="40", title="§2.4.13 (5) 기준선 변화 판정 규칙·기준선별 처리(card NFR-4 판정에서 적용 끝남)", mode="lines",
      start="- **기준선 변화 판정 규칙**(사용자 결정 N-1", end="- **작성 주체**",
      new="- **기준선 변화 판정 규칙**(사용자 결정 N-1·N-3): card NFR-4 판정에서 적용 끝남 -- 사전 승인 범위·기준선별 처리(B-1~B-3) 원문 = " + H + "H40-11."),
 dict(id="H40-12", file="40", title="§2.4.13 (7) 영향(card NFR-4 수행 목록)", mode="lines",
      start="- **S0 스냅샷**(v1.10): 디스크 S0 스냅샷이 없어졌다", end="**(8) 결정 Q-N1~Q-N10**",
      new="- card NFR-4 병합으로 끝남 -- 기준선 재측정·다시 쓸 test·새 test·XRUN-F1 card A·C 경계·바꿀 코드 위치 원문 = " + H + "H40-12. XRUN-F1 card C의 기준선 재측정은 §2.4.14 (6).\n"),
 dict(id="H40-13", file="40", title="§2.4.13 (8) 결정 Q-N1~Q-N10 질문·근거 표", mode="lines",
      start="**(8) 결정 Q-N1~Q-N10**", end="**후속 card NFR4-F1",
      new="**(8) 결정 Q-N1~Q-N10**(사용자 결정 2026-10-15 \"기본안대로 진행해\", 계획 N7.2 U-77~U-86 닫힘): 결과는 위 (2)~(5)에 반영됐다 -- Q-N2 K 부류는 보고만, Q-N3 선언 분해능 없는 칸 = 상류 허용오차 섭동의 감도 전파값·노드 전압 tol_V = 그 노드에 채널이 닿는 MOS `dc_tol_v` 최솟값, Q-N4 max(선언 분해능, 감도 전파값), Q-N6 LUT 파생표 디스크 캐시 키 불변(`E/lut/`은 BLAS를 부르지 않는다), Q-N7 pushpull 다른 환경 FAIL = 알려진 결함(42 D-ND4, NFR4-F1), Q-N9 층 0 끌어올림 s = max(0, 식의 값), Q-N10 계획 IC2 = 비트 동일; Q-N1·Q-N5·Q-N8은 대상 소멸(사용자 결정 2026-10-15 \"나로 해\"). 질문·근거 표 = " + H + "H40-13.\n"),
 dict(id="H40-14", file="40", title="§2.4.14 (3) 재작성 범위 표의 card A·B 행(병합 b0077a83·138a6db3으로 끝남)", mode="filter",
      start="| 파일(`E/`) | card | 범위 | 근거 |", end="**(4) 삭제·변경 목록**", pred=card_ab,
      note="(card A·B 행은 병합(b0077a83·138a6db3)으로 끝나 " + H + "H40-14로 옮겼다. 남은 행 = card C와 card B·IT-2e 공동 행.)"),
 dict(id="H40-15", file="40", title="§2.4.14 (4) 삭제·변경 목록의 card A·B 행", mode="filter",
      start="| 이름 | card | grep 범위(이 안에서 0) | 범위 밖에 남는 쓰임 |", end="**(5) card 분할**", pred=card_ab,
      note="(card A·B 행은 병합으로 끝나 " + H + "H40-15로 옮겼다.)"),
 dict(id="H40-16", file="40", title="§2.4.14 (5) card 분할 표의 card A·B 행", mode="filter",
      start="| card | 범위 | 선행 | 완료 조건 |", end="배선(사용자 원칙",
      pred=lambda l: l.startswith("| **A** RT + W") or l.startswith("| **B** 색인"),
      note="(card A·B 행(범위·완료 조건·test 초안·판정 측정)은 병합으로 끝나 " + H + "H40-16으로 옮겼다.)"),
 dict(id="H41-18", file="41", title="§5.10-1 v1.5 as-built 항목의 처리 표", mode="lines",
      start="**1. v1.5 §5.10 as-built 항목의 처리**", end="**2. 구현 변경 목록**",
      new="**1. v1.5 §5.10 as-built 항목의 처리** = " + H + "H41-18(폐기·유지 판정 기록 -- 현행 규칙은 각 절).\n"),
]
