"""V4 (2) '확실한 복사' 검출기 실측 probe (05 design §10, review30 R-05·R-06, 사용자 결정 (c)).

규칙의 정본은 05 design §10 V4 행이다. 요약: test의 판정 문장에서 피검 함수 호출이 든 쪽(실제값)과
다른 쪽(기대식 X)을 가르고, 양쪽의 지역 대입을 판정 시점 값으로 인라인한다. 피검 함수는 return마다
지역 대입을 인라인하고 호출 인자를 매개변수에 결합(기본값 포함)해 E_i를 만든다. 같은 모듈 함수 호출은
재귀 인라인한다. 정규화(평탄화와 정렬, 정수 거듭제곱 -> 곱, 항등원 제거, 부호를 밖으로, 숫자는 정확한
유리수이고 곱의 숫자 인자는 곱하지 않은 다중집합 + 나눗셈만 역수) 뒤 X와 입력 통과 경로가 아닌 E_i가
같으면 FAIL. 숫자끼리 접지 않는다. FAIL은 확실한 복사이고 PASS는 독립의 증거가 아니다.
자체 대조는 케이스마다 첫 판정 문장의 출력과 기대를 비교한다.

부트스트랩 ①에서 이 파일의 규칙 함수를 tools/gates/test_lint.py V4 (2) 구현으로 옮겼다(규칙 사본 없음).
DESIGN-GAP(05 §10 "probe는 지운다"): 사례 67개의 표와 자체 대조는 공격 23 재생 데이터(검증 agent 소유
`tools/gates/redteam/`)가 이것을 대신할 때까지 남긴다. 지우면 공격 23의 사례 원천이 저장소에서 사라진다.
"""
import ast
import copy
import functools
import json
import subprocess
from fractions import Fraction
import sys
from pathlib import Path

OUT = Path(__file__).with_name("v4.out.txt")


# ---------- 규칙 함수: 부트스트랩 ①에서 tools/gates/test_lint.py로 옮겼다(글자 그대로). 이 probe는 사례 표와
# 자체 대조만 남기고 규칙은 게이트 구현을 부른다 -- 규칙의 사본을 두지 않는다(WP-01).
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools" / "gates"))
from test_lint import judge  # noqa: E402


# ---------- 사례 ----------
def e329283_inputs():
    src = subprocess.run(["git", "show", "e329283:skills/analog-gmid-design/assets/sizing_recipe.py"],
                         capture_output=True, check=True).stdout.decode("utf-8")
    lines = src.splitlines()
    start = next(i for i, l in enumerate(lines) if "[7-4b 확장 estimate_area_budget()" in l) + 1
    end = next(i for i in range(start, len(lines)) if lines[i].strip() == "print()")
    body = [l for l in lines[start:end]]
    indent = min(len(l) - len(l.lstrip()) for l in body if l.strip())
    test = "def test_area_budget():\n" + "\n".join("    " + l[indent:] if l.strip() else "" for l in body) + "\n"
    return src, test


def _swap(test, old, new):
    assert old in test, old
    return test.replace(old, new)


def main():
    OUT.write_text("", encoding="utf-8")
    src, test = e329283_inputs()
    subj = {"estimate_area_budget"}
    X0 = "_area_cold_expected = (1 - 0.65) * _a1d_demo + 0.65 * _a2d_cold_expected"
    cases = [
        ("e329283 실제(§13.3 변환 test)", src, test, subj, "첫 assert FAIL", None),
        ("e329283 교환 재배열", src, _swap(test, X0, "_area_cold_expected = _a1d_demo * (1 - 0.65) + _a2d_cold_expected * 0.65"), subj, "첫 assert FAIL", None),
        ("e329283 1.0* 감싸기", src, _swap(test, X0, "_area_cold_expected = 1.0 * ((1 - 0.65) * _a1d_demo + 0.65 * _a2d_cold_expected)"), subj, "첫 assert FAIL", None),
        ("e329283 손으로 접은 리터럴", src, _swap(test, X0, "_area_cold_expected = 135.0"), subj, "첫 assert PASS", "F1 상수 접기"),
        ("e329283 대수 정리(α 상쇄를 풀어 씀)", src, _swap(test, X0, "_area_cold_expected = (1 - 0.65) * _a1d_demo + _a1d_demo"), subj, "첫 assert PASS", "F2 분배·약분"),
        ("e329283 비교 <=", src, _swap(test, "abs(_area_cold - _area_cold_expected) < 1e-9", "abs(_area_cold - _area_cold_expected) <= 1e-9"), subj, "첫 assert FAIL", None),
        ("e329283 상대 오차", src, _swap(test, "abs(_area_cold - _area_cold_expected) < 1e-9", "abs((_area_cold - _area_cold_expected) / _area_cold_expected) < 1e-9"), subj, "첫 assert FAIL", None),
        ("e329283 approx 왼쪽", src, _swap(test, "abs(_area_cold - _area_cold_expected) < 1e-9", "pytest.approx(_area_cold_expected) == _area_cold"), subj, "첫 assert FAIL", None),
        ("e329283 주석 달린 대입", src, _swap(test, X0, "_area_cold_expected: float = (1 - 0.65) * _a1d_demo + 0.65 * _a2d_cold_expected"), subj, "첫 assert FAIL", None),
        ("e329283 합을 sum()으로", src, _swap(test, X0, "_area_cold_expected = sum([(1 - 0.65) * _a1d_demo, 0.65 * _a2d_cold_expected])"), subj, "첫 assert PASS", "F3 모듈 밖 호출·자료구조"),
    ]
    syn = [
        ("제곱 vov*vov 대 0.2**2", "def ov(vov):\n    return vov * vov\n", "def test_ov():\n    assert ov(0.2) == pytest.approx(0.2 ** 2)\n", {"ov"}, "FAIL", None),
        ("제곱 vov**2 대 0.2*0.2", "def ov(vov):\n    return vov ** 2\n", "def test_ov():\n    assert ov(0.2) == pytest.approx(0.2 * 0.2)\n", {"ov"}, "FAIL", None),
        ("gm*ro 대 2e-3*50e3(재서술)", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    assert gain(2e-3, 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        ("gm*ro 대 리터럴 100.0", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    assert gain(2e-3, 50e3) == pytest.approx(100.0)\n", {"gain"}, "PASS", None),
        ("병렬 r1*r2/(r1+r2) 대 같은 식", "def par(r1, r2):\n    return r1 * r2 / (r1 + r2)\n", "def test_par():\n    assert par(1e3, 2e3) == pytest.approx(1e3 * 2e3 / (1e3 + 2e3))\n", {"par"}, "FAIL", None),
        ("병렬 대 컨덕턴스 합(다른 폐형식)", "def par(r1, r2):\n    return r1 * r2 / (r1 + r2)\n", "def test_par():\n    assert par(1e3, 2e3) == pytest.approx(1 / (1 / 1e3 + 1 / 2e3))\n", {"par"}, "PASS", None),
        ("같은 모듈 보조 함수 인라인", "def a2d(a1d, alpha):\n    return a1d / alpha\n\ndef area(n, alpha=0.65):\n    a = n * 1.0\n    return (1 - alpha) * a + alpha * a2d(a, alpha)\n", "def test_area():\n    assert area(100) == pytest.approx((1 - 0.65) * 100 + 0.65 * (100 / 0.65))\n", {"area"}, "FAIL", None),
        ("KCL 합 i1+i2 대 10e-6+20e-6", "def itot(i1, i2):\n    return i1 + i2\n", "def test_itot():\n    assert itot(10e-6, 20e-6) == pytest.approx(10e-6 + 20e-6)\n", {"itot"}, "FAIL", None),
        # review31 N-04: 부호·나눗셈 표기와 호출 형태
        ("단항 마이너스 -gm*ro 대 -(2e-3*50e3)", "def g(gm, ro):\n    return -gm * ro\n", "def test_g():\n    assert g(2e-3, 50e3) == pytest.approx(-(2e-3 * 50e3))\n", {"g"}, "FAIL", None),
        ("단항 마이너스 -gm*ro 대 2e-3*(-50e3)", "def g(gm, ro):\n    return -gm * ro\n", "def test_g():\n    assert g(2e-3, 50e3) == pytest.approx(2e-3 * (-50e3))\n", {"g"}, "FAIL", None),
        ("a - b*c 대 -b*c + a", "def h(a, b, c):\n    return a - b * c\n", "def test_h():\n    assert h(1.0, 2.0, 3.0) == pytest.approx(-2.0 * 3.0 + 1.0)\n", {"h"}, "FAIL", None),
        ("x/2 대 x*0.5", "def half(x):\n    return x / 2\n", "def test_half():\n    assert half(y) == pytest.approx(y * 0.5)\n", {"half"}, "FAIL", None),
        ("1/x 대 x**-1", "def inv(x):\n    return 1 / x\n", "def test_inv():\n    assert inv(y) == pytest.approx(y ** -1)\n", {"inv"}, "FAIL", None),
        ("키워드 전용 기본값", "def f(a, *, k=2.0):\n    return a * k\n", "def test_f():\n    assert f(y) == pytest.approx(y * 2.0)\n", {"f"}, "FAIL", None),
        ("**kw 호출(판정 없음, 예외 없음)", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    kw = {'gm': 2e-3, 'ro': 50e3}\n    assert gain(**kw) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("assert 뒤 재대입(데이터 흐름)", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    e = gm0 * ro0\n    assert gain(gm0, ro0) == pytest.approx(e)\n    e = 100.0\n", {"gain"}, "FAIL", None),
        ("튜플 반환", "def gp(a, b):\n    return a * b, a + b\n", "def test_gp():\n    p, s = gp(2.0, 3.0)\n    assert p == pytest.approx(2.0 * 3.0)\n", {"gp"}, "UNJUDGED", "F3 튜플 풀기"),
        # review31 N-03: 잎 하나 return 경로의 명세 리터럴
        ("clamp 통과 경로 리터럴", "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x\n", "def test_clamp():\n    assert clamp(5, 0, 10) == 5\n", {"clamp"}, "PASS", None),
        ("clamp 하한 리터럴", "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x\n", "def test_clamp():\n    assert clamp(-3, 0, 10) == 0\n", {"clamp"}, "PASS", None),
        ("area(0) 상수 return", "def area(n):\n    if n == 0:\n        return 0.0\n    return n * 1.5\n", "def test_area():\n    assert area(0) == 0.0\n", {"area"}, "PASS", None),
        ("단위 이득(항등원 뒤 잎 하나)", "def vout(vin, gain=1.0):\n    return vin * gain\n", "def test_vout():\n    assert vout(0.9) == pytest.approx(0.9)\n", {"vout"}, "PASS", None),
        # review32 M-02: 인자가 식인 통과 경로
        ("clamp 통과 경로, 인자가 식(무발동 값)", "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x\n", "def test_clamp():\n    vdd = 1.8\n    vin = 0.5 * vdd\n    assert clamp(vin, 0.0, vdd) == pytest.approx(vin)\n", {"clamp"}, "PASS", None),
        ("단위 이득, 인자가 식", "def vout(vin, gain=1.0):\n    return vin * gain\n", "def test_vout():\n    vin = 0.5 * 1.8\n    assert vout(vin) == pytest.approx(vin)\n", {"vout"}, "PASS", None),
        ("항등 함수, 인자가 식", "def buf(x):\n    return x\n", "def test_buf():\n    assert buf(2.0 * 3.0) == pytest.approx(2.0 * 3.0)\n", {"buf"}, "PASS", None),
        # review32 M-03: 숫자 인자 다중집합
        ("교환 재배열 a*b*c*x 대 x*c*b*a", "def f(x, a, b, c):\n    return a * b * c * x\n", "def test_f():\n    assert f(y, 0.1, 0.2, 0.3) == pytest.approx(y * 0.3 * 0.2 * 0.1)\n", {"f"}, "FAIL", None),
        ("숫자만의 3.0/2 대 3.0*0.5", "def half(x):\n    return x / 2\n", "def test_half():\n    assert half(3.0) == pytest.approx(3.0 * 0.5)\n", {"half"}, "FAIL", None),
        ("손으로 접은 계수 6.0*y", "def f(x, k1=2.0, k2=3.0):\n    return x * k1 * k2\n", "def test_f():\n    assert f(y) == pytest.approx(6.0 * y)\n", {"f"}, "PASS", "F1 손 계산 계수"),
        ("손으로 접은 계수 4e-6*W/L", "def ids(kp, w, l, vov):\n    return 0.5 * kp * (w / l) * vov ** 2\n", "def test_ids():\n    assert ids(200e-6, W, L, 0.2) == pytest.approx(4e-6 * W / L)\n", {"ids"}, "PASS", "F1 손 계산 계수"),
        # review32 M-04와 FN3·FN7·FN8
        ("합 위 단항 마이너스 -(b+c) 대 -p-q", "def n(b, c):\n    return -(b + c)\n", "def test_n():\n    assert n(p, q) == pytest.approx(-p - q)\n", {"n"}, "FAIL", None),
        ("for 안의 재서술", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    for gm in (1e-3, 2e-3):\n        assert gain(gm, 50e3) == pytest.approx(gm * 50e3)\n", {"gain"}, "FAIL", None),
        ("with 안의 재서술", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    with ctx():\n        assert gain(2e-3, 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        ("np.testing.assert_allclose 재서술", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    np.testing.assert_allclose(gain(2e-3, 50e3), 2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        ("test 쪽 누적 대입 e *= 50e3", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    e = 2e-3\n    e *= 50e3\n    assert gain(2e-3, 50e3) == pytest.approx(e)\n", {"gain"}, "FAIL", None),
        ("식 안의 피검 호출", "def gp(a, b):\n    return a * b\n", "def test_gp():\n    assert gp(2.0, 3.0) * 1 == pytest.approx(2.0 * 3.0)\n", {"gp"}, "UNJUDGED", None),
        ("피검 없는 assert", "def gp(a, b):\n    return a * b\n", "def test_gp():\n    assert len([1, 2]) == 2\n", {"gp"}, "NO-SUBJECT", None),
        # review33 M2-03: 블록·루프 대상으로 받은 피검 결과, match·중첩 함수·except*
        ("표 구동 zip 루프", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    rs = [gain(g, 50e3) for g in gms]\n    for r, g in zip(rs, gms):\n        assert r == pytest.approx(g * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("피검 결과 리스트를 도는 루프", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    for r in [gain(2e-3, 50e3)]:\n        assert r == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("if 블록 안에서 받은 결과", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    if flag:\n        r = gain(2e-3, 50e3)\n    assert r == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("with 블록 안에서 받은 결과", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    with warnings.catch_warnings():\n        r = gain(2e-3, 50e3)\n    assert r == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("try 블록 안에서 받은 결과", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    try:\n        r = gain(2e-3, 50e3)\n    except ValueError:\n        r = 0.0\n    assert r == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("match 안의 재서술", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    match mode:\n        case 1:\n            assert gain(2e-3, 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        ("test 안 중첩 함수", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    def check(g):\n        assert gain(g, 50e3) == pytest.approx(g * 50e3)\n    check(2e-3)\n", {"gain"}, "UNJUDGED", None),
        ("except* 안의 재서술", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    try:\n        pass\n    except* ValueError:\n        assert gain(2e-3, 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        # review33 M2-04~M2-06
        ("쌍 없는 피검 없는 assert", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    assert len(xs) > 0\n", {"gain"}, "NO-SUBJECT", None),
        ("쌍 없는 피검 assert", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    assert gain(2e-3, 50e3) > 0\n", {"gain"}, "UNJUDGED", None),
        ("inf 리터럴(예외 없음)", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    assert gain(1e400, 2.0) == pytest.approx(1e400 * 2.0)\n", {"gain"}, "FAIL", None),
        ("async test", "def gain(gm, ro, note=None):\n    return gm * ro\n", "async def test_gain():\n    assert gain(2e-3, 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        ("쓰지 않는 인자로 통과 경로 흉내", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    assert gain(2e-3, 50e3, note=2e-3 * 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        # review34 M3-04·M3-05
        ("첨자로 받은 결과 out[g] = f(g)", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    out = {}\n    for g in gms:\n        out[g] = gain(g, 50e3)\n    for g, r in out.items():\n        assert r == pytest.approx(g * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("속성으로 받은 결과", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    res = Box()\n    res.v = gain(2e-3, 50e3)\n    assert res.v == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("append로 받은 결과", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    rs = []\n    rs.append(gain(2e-3, 50e3))\n    assert rs[0] == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("comprehension 지역 이름이 기대 이름을 가리지 않음", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    e = 2e-3 * 50e3\n    xs = [e for e in range(3)]\n    assert gain(2e-3, 50e3) == pytest.approx(e)\n", {"gain"}, "FAIL", None),
        ("중첩 def 지역 이름이 기대 이름을 가리지 않음", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    e = 2e-3 * 50e3\n    def h():\n        e = 1.0\n        return e\n    assert gain(2e-3, 50e3) == pytest.approx(e)\n", {"gain"}, "FAIL", None),
        ("블록 안에서 만든 기대식", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    if flag:\n        e = 2e-3 * 50e3\n    assert gain(2e-3, 50e3) == pytest.approx(e)\n", {"gain"}, "PASS", "F6 블록 안에서 만든 기대식"),
        # review35 M4-03: 피검이 중첩 def·class를 호출해 돌려준다(예외 없이 판정)
        ("return inner(x) 중첩 함수 호출", "def f(x, k):\n    def inner(y):\n        return y * k\n    return inner(x)\n", "def test_f():\n    assert f(y0, 2.0) == pytest.approx(y0 * 2.0)\n", {"f"}, "PASS", "F3 중첩 함수 경유"),
        ("return R() 중첩 클래스 호출", "def f(x):\n    class R:\n        pass\n    return R()\n", "def test_f():\n    assert f(1.0) == expected_r\n", {"f"}, "PASS", None),
        ("피검 안 중첩 함수 return", "def f(x, k):\n    def inner(y):\n        return y * k\n    return x + 1.0\n", "def test_f():\n    assert f(y0, 2.0) == pytest.approx(y0 * 2.0)\n", {"f"}, "PASS", None),
    ]
    mismatch = 0
    for name, m, t, s, expect, limit in cases + syn:
        r = judge(m, t, s)
        ok = r[0][1] == expect.split()[-1]  # 첫 판정 문장의 출력과 기대(마지막 단어)를 대조
        mismatch += not ok
        line = ("" if ok else "MISMATCH ") + f"{name}: {r} | 기대 {expect}" + (f" | known_limit {limit}" if limit else "")
        with OUT.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(line)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(f"케이스 {len(cases) + len(syn)}개, 기대 불일치 {mismatch}개\n")
    # 누적 회귀 코퍼스: 검증자들(review32~35)이 만든 케이스 전부. 출력은 3bf0100 판(review36 독립 검증에서
    # 회귀 0 확인)으로 고정했다 -- 출력이 바뀌면 그 변경이 의도인지 기록(history)과 함께 다시 고정한다.
    corpus = json.loads(OUT.with_name("regression_cases.json").read_text(encoding="utf-8"))
    changed = 0
    for c in corpus:
        now = [list(x) for x in judge(c["module"], c["test"], set(c["subjects"]))]
        if now != c["output"]:
            changed += 1
            with OUT.open("a", encoding="utf-8") as f:
                f.write(f"REGRESSION {c['source']} {c['name']}: 고정 {c['output']} -> 지금 {now}\n")
    with OUT.open("a", encoding="utf-8") as f:
        f.write(f"회귀 코퍼스 {len(corpus)}개, 출력 변화 {changed}개\n")
    # R-05 네 조합(인라인 여부) -- 실제 e329283
    for it in (False, True):
        for isub in (False, True):
            r = judge(src, test, subj, inline_test=it, inline_subject=isub)
            line = f"e329283 조합 test 인라인={it} 피검 인라인={isub}: {r}"
            with OUT.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
            print(line)


if __name__ == "__main__":
    sys.exit(main())
