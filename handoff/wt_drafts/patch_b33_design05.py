"""B33 `20260930-v7-registry-edges` 문서 커밋용 design 05 §10 문구 패치(spec card '문구 변경', 계약 13).

    C:/Python314/python.exe -B patch_b33_design05.py <저장소 루트 또는 design 05 파일 경로>

* 바이너리로 읽고 쓴다(UTF-8). 줄 끝은 파일의 것을 그대로 둔다(작업 트리 CRLF(core.autocrlf=true)·blob LF 모두 -- 섞여 있으면 중단).
  새 문구에 줄바꿈 없음.
* 교체마다 '옛 문구+줄 끝'이 정확히 1번이고 '새 문구+줄 끝'이 0번이어야 적용한다. 이미 적용된 상태(옛 0번·새 1번)는 건너뛴다.
  그 밖이면 아무것도 쓰지 않고 exit 1.
* 멱등: 두 교체가 모두 이미 적용돼 있으면 파일을 건드리지 않고 exit 0("already applied").
대상: §10 V7 행(HEAD 2d58fd8 321행)과 같은 절 '거부 증명' 줄 끝(338행).
"""
import os
import sys

REL = "docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md"

OLD_V7 = ("| `reachability.py`(V7) | 배선 | 새 `def`가 `gate_config.json`의 `reachability_roots`에서 정적 호출 그래프(문자열 레지스트리 포함)로 "
          "도달하는지 |")
NEW_V7 = ("| `reachability.py`(V7) | 배선 | 새 `def`가 `gate_config.json`의 `reachability_roots`에서 정적 호출 그래프(문자열 레지스트리 포함)로 "
          "도달하는지. 그래프 간선 = 이름·속성 참조(기존, 단 dunder 속성 `x.__y__`는 같은 이름 전역 폴백 없음). 모듈 최상위 이름 바인딩(dict 레지스트리 등)은 "
          "도달하는 코드가 그 이름을 네 형식(같은 파일 맨 이름 -- 함수 지역 이름 제외, `from M import NAME`, `M.NAME`, M에 없으면 M의 `from X import NAME`을 따른 "
          "재수출 -- M·X는 그래프 안 모듈)으로 참조할 때만 값 식의 이름·속성·생성자 참조(문자열 상수 제외)로 이어진다. 클래스 호출 `Cls(...)`·`raise Cls`(같은 "
          "형식으로 해석)는 그 클래스(없으면 기반 클래스)의 `__init__`·`__new__`·`__post_init__`로, `super().__d__`는 기반 클래스의 `__d__`로. import 문장 자체는 "
          "간선이 아니다. 도달 계산은 소스 분류 파일(`_is_source`, §4.3 소스의 `.py`) 노드 안에서만 따라간다 -- test·probe·workspace 스크립트의 def를 거친 도달은 "
          "세지 않는다. V3 인벤토리는 같은 그래프를 test 노드에서 출발해 쓴다(범위 제한 없음) |")

OLD_RJ = ", V7 → `redteam/v7_unwired`."
NEW_RJ = ", V7 → `redteam/v7_unwired`·공격 33(`attacks/33-v7-registry-edges`)."
RJ_PREFIX = "거부 증명: V3 → `redteam/v3_survivor`"   # 338행 머리 -- 교체가 이 줄에서 일어났는지 확인

PAIRS = [("V7 행", OLD_V7, NEW_V7), ("거부 증명 줄", OLD_RJ, NEW_RJ)]


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    p = argv[1]
    if os.path.isdir(p):
        p = os.path.join(p, *REL.split("/"))
    data = open(p, "rb").read()
    if data.startswith(b"\xef\xbb\xbf"):
        print("BOM 있음 -- 중단")
        return 1
    n_crlf, n_lf = data.count(b"\r\n"), data.count(b"\n")
    if n_crlf not in (0, n_lf):
        print("줄 끝이 섞여 있음(CRLF %d / LF %d) -- 중단" % (n_crlf, n_lf))
        return 1
    eol = b"\r\n" if n_crlf else b"\n"
    out = data
    applied = 0
    for label, old, new in PAIRS:
        # 줄 끝까지 포함해 맞춘다(옛 문구가 새 문구의 앞부분으로 다시 맞는 것을 막는다 -- 멱등)
        ob, nb = old.encode("utf-8") + eol, new.encode("utf-8") + eol
        n_old, n_new = out.count(ob), out.count(nb)
        if n_old == 1 and n_new == 0:
            out = out.replace(ob, nb, 1)
            applied += 1
        elif n_old == 0 and n_new == 1:
            pass  # 이미 적용
        else:
            print("%s: 옛 문구 %d번, 새 문구 %d번 -- 정확히 하나가 아니라 중단(쓰지 않음)" % (label, n_old, n_new))
            return 1
    lines = out.split(b"\n")
    hit = [i for i, ln in enumerate(lines, 1) if NEW_RJ.encode("utf-8") in ln]
    if len(hit) != 1 or not lines[hit[0] - 1].startswith(RJ_PREFIX.encode("utf-8")):
        print("거부 증명 줄 위치 확인 실패: %r" % hit)
        return 1
    if out.count(b"\r\n") != n_crlf or out.count(b"\n") != n_lf:
        print("줄 수·줄 끝이 바뀜 -- 중단")
        return 1
    if applied == 0:
        print("already applied (no change)")
        return 0
    with open(p, "wb") as f:
        f.write(out)
    print("applied %d replacement(s), V7 row line %d, rejection line %d: %s"
          % (applied, [i for i, ln in enumerate(lines, 1) if NEW_V7.encode("utf-8") in ln][0], hit[0], p))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
