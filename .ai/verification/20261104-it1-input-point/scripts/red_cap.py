"""판정용 pytest 플러그인: 실패 test 의 (nodeid, 예외 모듈.이름) 를 파일에 append. 수집 오류도 적는다."""
import json
import os

OUT = os.environ["RED_CAP_OUT"]


def _w(rec):
    with open(OUT, "ab") as f:
        f.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))


def pytest_runtest_makereport(item, call):
    if call.excinfo is None:
        if call.when == "call":
            _w({"id": item.nodeid, "outcome": "passed"})
        return
    t = call.excinfo.type
    _w({"id": item.nodeid, "when": call.when, "outcome": "failed", "exc": "%s.%s" % (t.__module__, t.__qualname__), "msg": str(call.excinfo.value)[:200]})


def pytest_collectreport(report):
    if report.failed:
        _w({"id": report.nodeid, "outcome": "collect_error", "msg": str(report.longrepr)[:300]})
