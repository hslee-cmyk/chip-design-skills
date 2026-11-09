"""B33 개정 측정 2: 공격 33(attacks/33-v7-registry-edges) 합성 케이스 생성기(측정용 -- test-author 산출물 아님).
    python -B gen_attack33.py <출력 디렉터리>
기대 exit·메시지는 spec card 계약 문장에서 정한 값(피검 도구 출력으로 만들지 않음)."""
import json
import os
import sys

A = "skills/analog-gmid-design/assets/"
ENG = A + "rt_engine.py"
H = "workspaces/run_harness.py"
E0 = '"""redteam 합성 엔진."""\n\n\ndef rt_gain(gm, ro):\n    """소신호 이득."""\n    return gm * ro\n'
H0 = 'from rt_engine import rt_gain\n\n\ndef run(x):\n    return rt_gain(x, 2.0)\n'
BASE = {ENG: {"text": E0}, H: {"text": H0}}


def harness(imports, body):
    return imports + "\n\n\ndef run(x):\n" + "".join("    " + ln + "\n" for ln in body.split("\n"))


def eng(extra, top=""):
    return (top + "\n" if top else "") + E0 + "\n\n" + extra.rstrip("\n") + "\n"


def uwa(*q):
    return '"unreached_without_approval": [' + ", ".join('"%s"' % (x if "/" in x else ENG + "::" + x) for x in q) + "]"


PASS = '"verdict": "PASS"'
cases = []


def step(name, head, exit_, contains, role, base=None, tool="V7", extra=None):
    c = {"step": name, "tool": tool, "kind": "attack", "base": base or BASE, "head": head,
         "expect": {"exit": exit_, "layer": tool, "message_contains": contains, "basis": role}}
    if extra:
        c.update(extra)
    cases.append(c)


# --- R1 도달(계약 1) ---
step("registry-wired", {ENG: {"text": eng('def _f_b(x):\n    return x + 1.0\n\n\n_REG = {"b": _f_b}\n\n\ndef rt_pick(k, x):\n    return _REG[k](x)\n')},
                        H: {"text": harness("from rt_engine import rt_gain, rt_pick", 'return rt_pick("b", rt_gain(x, 2.0))')}},
     0, [PASS], "계약 1 같은 파일 이름")
step("registry-imported", {ENG: {"text": eng('def _f_i(x):\n    return x + 2.0\n\n\n_REG_I = {"i": _f_i}\n')},
                           H: {"text": harness("from rt_engine import rt_gain, _REG_I", 'return _REG_I["i"](rt_gain(x, 2.0))')}},
     0, [PASS], "계약 1 from M import NAME")
step("registry-modattr", {ENG: {"text": eng('def _f_m(x):\n    return x + 3.0\n\n\n_REG_M = {"m": _f_m}\n')},
                          H: {"text": harness("import rt_engine\nfrom rt_engine import rt_gain", 'return rt_engine._REG_M["m"](rt_gain(x, 2.0))')}},
     0, [PASS], "계약 1 모듈 별칭 M.NAME")
step("registry-reexport", {A + "rt_reg.py": {"text": 'def _f_r(x):\n    return x + 4.0\n\n\n_REG_R = {"r": _f_r}\n'},
                           ENG: {"text": eng("", top="from rt_reg import _REG_R")},
                           H: {"text": harness("from rt_engine import rt_gain, _REG_R", 'return _REG_R["r"](rt_gain(x, 2.0))')}},
     0, [PASS], "계약 1 재수출(M 파일의 from X import NAME)")
# --- R1 미도달(계약 2) ---
step("registry-orphan", {ENG: {"text": eng('def _f_c(x):\n    return x + 5.0\n\n\n_ORPHAN = {"c": _f_c}\n')},
                         H: {"text": harness("import rt_engine\nfrom rt_engine import rt_gain", "return rt_gain(x, 2.0)")}},
     1, [uwa("_f_c")], "계약 2 참조 없는 바인딩(import만, R0 배제)")
step("registry-dead-reader", {ENG: {"text": eng('def _f_d(x):\n    return x + 6.0\n\n\n_DEADREG = {"d": _f_d}\n\n\ndef _dead_reader(k):\n    return _DEADREG[k]\n')}},
     1, [uwa("_dead_reader", "_f_d")], "계약 2 도달하지 않는 def만 읽는 바인딩")
# --- R1 음성 형식(계약 1 음성 -- B2·B3·S1·S2·S3) ---
step("registry-external-attr", {ENG: {"text": eng('def _f_p(x):\n    return x + 7.0\n\n\npi = {"p": _f_p}\n')},
                                H: {"text": harness("import math\nfrom rt_engine import rt_gain", "return math.pi * rt_gain(x, 2.0)")}},
     1, [uwa("_f_p")], "계약 1 음성: 그래프 밖 모듈 속성 math.pi")
step("registry-attr-collision", {ENG: {"text": eng('def _f_a(x):\n    return x + 8.0\n\n\ncache = {"a": _f_a}\n')},
                                 H: {"text": harness("from rt_engine import rt_gain", "return rt_gain(x.cache, 2.0)")}},
     1, [uwa("_f_a")], "계약 1 음성: 비모듈 속성 x.cache")
step("registry-str-collision", {ENG: {"text": eng('def _f_s(x):\n    return x + 9.0\n\n\n_STRREG = {"s": _f_s}\n')},
                                H: {"text": harness("from rt_engine import rt_gain", 'return rt_gain({"_STRREG": x}["_STRREG"], 2.0)')}},
     1, [uwa("_f_s")], "계약 1 음성: 문자열 상수 '_STRREG'")
step("registry-name-strings", {ENG: {"text": eng('_DOC_NAMES = ("rt_h2",)\n\n\ndef rt_h2(x):\n    return x * 5.0\n\n\ndef rt_named(n):\n    return n in _DOC_NAMES\n')},
                               H: {"text": harness("from rt_engine import rt_gain, rt_named", 'return rt_named("a") and rt_gain(x, 2.0)')}},
     1, [uwa("rt_h2")], "계약 1 음성: 바인딩 값 안 문자열 상수는 간선 아님")
step("registry-local-shadow", {ENG: {"text": eng('def _f_t(x):\n    return x + 10.0\n\n\n_TABLE = {"t": _f_t}\n\n\ndef rt_lookup(k):\n    _TABLE = {}\n    return _TABLE.get(k)\n')},
                               H: {"text": harness("from rt_engine import rt_gain, rt_lookup", 'return rt_lookup("t") or rt_gain(x, 2.0)')}},
     1, [uwa("_f_t")], "계약 1 음성: 함수 지역 이름은 모듈 바인딩이 아님")
step("registry-reexport-other", {A + "rt_reg.py": {"text": 'def _f_y(x):\n    return x + 11.0\n\n\n_REG_Y = {"y": _f_y}\n'},
                                 A + "rt_other.py": {"text": 'def _f_y2(x):\n    return x + 12.0\n\n\n_REG_Y = {"y": _f_y2}\n'},
                                 ENG: {"text": eng("", top="from rt_reg import _REG_Y")},
                                 H: {"text": harness("from rt_engine import rt_gain, _REG_Y", 'return _REG_Y["y"](rt_gain(x, 2.0))')}},
     1, [uwa(A + "rt_other.py::_f_y2")], "계약 1 음성: 재수출은 M의 import를 따라감(같은 이름 다른 모듈 바인딩 아님)")
# --- R2 도달(계약 3) ---
step("ctor-wired", {ENG: {"text": eng("class RtBox:\n    def __init__(self, v):\n        self.v = v\n")},
                    H: {"text": harness("from rt_engine import rt_gain, RtBox", "return RtBox(rt_gain(x, 2.0)).v")}},
     0, [PASS], "계약 3 Cls(...)")
step("ctor-raise", {ENG: {"text": eng('class RtError(Exception):\n    def __init__(self, m=""):\n        self.m = m\n\n\ndef rt_check(v):\n    if v < 0:\n        raise RtError\n    return v\n')},
                    H: {"text": harness("from rt_engine import rt_gain, rt_check", "return rt_check(rt_gain(x, 2.0))")}},
     0, [PASS], "계약 3 raise Cls")
step("ctor-inherited", {ENG: {"text": eng("class RtBase:\n    def __init__(self, v):\n        self.v = v\n\n\nclass RtSub(RtBase):\n    pass\n")},
                        H: {"text": harness("from rt_engine import rt_gain, RtSub", "return RtSub(rt_gain(x, 2.0)).v")}},
     0, [PASS], "계약 3 기반 클래스 __init__")
step("ctor-dataclass-post-init", {ENG: {"text": eng("@dataclass\nclass RtDev:\n    w: float\n\n    def __post_init__(self):\n        if self.w < 0:\n            self.w = 0.0\n",
                                                    top="from dataclasses import dataclass")},
                                  H: {"text": harness("from rt_engine import rt_gain, RtDev", "return RtDev(rt_gain(x, 2.0)).w")}},
     0, [PASS], "계약 3 dataclass __post_init__")
step("ctor-super-chain", {ENG: {"text": eng("class RtBase2:\n    def __init__(self, v):\n        self.v = v\n\n\nclass RtSub2(RtBase2):\n    def __init__(self, v):\n        super().__init__(v)\n        self.w = v\n")},
                          H: {"text": harness("from rt_engine import rt_gain, RtSub2", "return RtSub2(rt_gain(x, 2.0)).w")}},
     0, [PASS], "계약 3 super().__init__ -> 기반 클래스 __init__")
step("ctor-in-binding", {ENG: {"text": eng('class RtHandler:\n    def __init__(self, fn):\n        self.fn = fn\n\n\n_HANDLERS = {"k": RtHandler(rt_gain)}\n\n\ndef rt_dispatch(k, x):\n    return _HANDLERS[k].fn(x, 2.0)\n')},
                         H: {"text": harness("from rt_engine import rt_dispatch", 'return rt_dispatch("k", x)')}},
     0, [PASS], "계약 3 바인딩 값 안 생성자 호출")
# --- R2 미도달(계약 4) ---
step("ctor-isinstance-only", {ENG: {"text": eng("class RtOnly:\n    def __init__(self, v):\n        self.v = v\n")},
                              H: {"text": harness("from rt_engine import rt_gain, RtOnly",
                                                  "v: RtOnly = None\ntry:\n    y = rt_gain(x, 2.0)\nexcept RtOnly:\n    y = 0.0\nif isinstance(v, RtOnly):\n    y = 1.0\nreturn y")}},
     1, [uwa("RtOnly.__init__")], "계약 4 isinstance·except·주석만(Q1 (a))")
SUPBASE = {ENG: {"text": eng('class RtErr(ValueError):\n    def __init__(self, m):\n        super().__init__(m)\n\n\ndef rt_check2(v):\n    if v < 0:\n        raise RtErr("neg")\n    return v\n')},
           H: {"text": harness("from rt_engine import rt_gain, rt_check2", "return rt_check2(rt_gain(x, 2.0))")}}
step("ctor-super-leak", {ENG: {"text": SUPBASE[ENG]["text"] + "\n\nclass RtNever:\n    def __init__(self, v):\n        self.v = v\n"},
                         H: SUPBASE[H]},
     1, [uwa("RtNever.__init__")], "계약 4 도달 코드의 super().__init__()이 있어도 인스턴스화 0인 클래스 __init__ 미도달", base=SUPBASE)
# --- R3(계약 5·6) ---
step("leak-test-name", {ENG: {"text": eng("def rt_area(a):\n    return a.rt_sz(2.0)\n\n\ndef rt_g(x):\n    return x * 3.0\n")},
                        A + "tests/probes/p_rt.py": {"text": "from rt_engine import rt_g\n\n\ndef rt_sz(v):\n    return rt_g(v)\n"},
                        H: {"text": harness("from rt_engine import rt_gain, rt_area", "return rt_area(rt_gain(x, 2.0))")}},
     1, [uwa("rt_g")], "계약 5 비운영 파일 이름 폴백 누수 차단")
step("leak-test-string", {ENG: {"text": eng("def rt_h(x):\n    return x * 4.0\n")},
                          A + "tests/contracts/test_rt_names.py": {"text": '_RT_NAMES = ("rt_h",)\n\n\ndef _rt_rel(p):\n    return [n for n in _RT_NAMES if n] + [p]\n'},
                          H: {"text": harness("from rt_engine import rt_gain", 'return _rt_rel("a") and rt_gain(x, 2.0)')}},
     1, [uwa("rt_h")], "계약 6 test 파일 상수")
# --- 면제·대조군(계약 7·8) ---
step("approved-still-exempt", {ENG: cases[4]["head"][ENG], H: cases[4]["head"][H],
                               ".ai/approvals/20260930-rt-v7-exempt.md": {"text": "---\nid: 20260930-rt-v7-exempt\ndate: 2026-09-30\ntarget_kind: decision\ntarget: " + ENG + "::_f_c\nscope: redteam V7 면제 대조군\n---\n"}},
     0, [PASS, '"unreached": ["' + ENG + '::_f_c"]'], "계약 8 면제 불변")
step("direct-call-control", {ENG: {"text": eng("def rt_twice(x):\n    return 2.0 * x\n")},
                             H: {"text": harness("from rt_engine import rt_gain, rt_twice", "return rt_twice(rt_gain(x, 2.0))")}},
     0, [PASS], "계약 8 대조군")
step("binding-not-a-def", {ENG: {"text": eng('_RT_UNUSED = {"k": 1}\n')}}, 0, [PASS, '"new_defs": []'], "계약 7 대조군")
# --- V3(계약 10) ---
step("v3-registry-inventory", {ENG: {"text": eng('def _metric_rt_x(v):\n    """2배."""\n    return 2.0 * v\n\n\n_RT_METRICS = {"x": _metric_rt_x}\n\n\ndef rt_compute(kind, v):\n    return _RT_METRICS[kind](v)\n')},
                               A + "tests/test_rt_compute.py": {"text": "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\nfrom rt_engine import rt_compute\n\n\ndef test_rt_compute_x():\n    assert rt_compute(\"x\", 3.0) == 6.0\n"}},
     0, [PASS], "계약 10 V3 같은 그래프", tool="V3", extra={"subjects": ["rt_engine.rt_compute", "rt_engine._metric_rt_x"]})

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "v.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump({"cases": cases}, f, ensure_ascii=False, indent=1)
with open(os.path.join(out, "expect.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump({"layer": "V7", "exit": 1, "message_contains": [], "modes": ["direct"], "phase": "0.5",
               "basis": "spec card 20260930-v7-registry-edges(측정용 초안)", "title": "공격 33 측정용", "steps_from_records": True},
              f, ensure_ascii=False, indent=1)
with open(os.path.join(out, "run.sh"), "w", encoding="utf-8", newline="\n") as f:
    f.write('#!/usr/bin/env bash\nset -e\nrt() { "$PY" -B "$RT" "$@"; }\n\nrt vcase v.json\n')
print(len(cases), "steps")
