# -*- coding: utf-8 -*-
"""red 수집(판정자 플러그인): interface 에 '## 신규 시그니처' 절이 없어(§3·§5 표로 대신) merge_gate 플러그인이 읽지 못한다. 해시 정의는 00-common §8.1 그대로.
수집 오류 = __cause__ 타입, 실행 실패 = excinfo 타입. 결과 = RED_OUT jsonl."""
import hashlib, json, os


def h(test_id, t):
    return hashlib.sha256(f"{test_id}\n{t.__module__}.{t.__qualname__}".encode("utf-8")).hexdigest()


rows = []


def pytest_exception_interact(node, call, report):
    if report.__class__.__name__ == "CollectReport":
        v = call.excinfo.value
        cause = v.__cause__ if getattr(v, "__cause__", None) is not None else v
        t = type(cause)
        rows.append({"test_id": node.nodeid, "exc": f"{t.__module__}.{t.__qualname__}", "msg": str(cause)[:120], "failure_hash": h(node.nodeid, t)})


def pytest_runtest_makereport(item, call):
    if call.when in ("setup", "call") and call.excinfo is not None:
        t = call.excinfo.type
        rows.append({"test_id": item.nodeid, "exc": f"{t.__module__}.{t.__qualname__}", "msg": str(call.excinfo.value)[:120], "failure_hash": h(item.nodeid, t)})


def pytest_sessionfinish(session):
    with open(os.environ["RED_OUT"], "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
