"""pytest 플러그인: 세션 전체에서 SD·SR의 실행된 줄(합집합)을 sys.monitoring LINE으로 기록한다.
위치마다 첫 실행 뒤 DISABLE을 돌려 부하를 줄인다(합집합만 필요). 결과: 환경변수 COVPLUG_OUT(JSON)."""
import json, os, sys

_TOOL = 3
_WANT = ("stick_diagram.py", "sizing_recipe.py")
_HIT = {}


def _line(code, line):
    fn = code.co_filename
    if fn.endswith(_WANT):
        _HIT.setdefault(os.path.basename(fn), set()).add(line)
    return sys.monitoring.DISABLE


def pytest_configure(config):
    sys.monitoring.use_tool_id(_TOOL, "covplug")
    sys.monitoring.register_callback(_TOOL, sys.monitoring.events.LINE, _line)
    sys.monitoring.set_events(_TOOL, sys.monitoring.events.LINE)


def pytest_unconfigure(config):
    sys.monitoring.set_events(_TOOL, 0)
    with open(os.environ["COVPLUG_OUT"], "w", encoding="utf-8") as fh:
        json.dump({k: sorted(v) for k, v in _HIT.items()}, fh)
