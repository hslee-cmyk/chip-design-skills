"""auditor 격리 사전 검사 플러그인(복원 card 순서 3). `-p iso_probe`로 붙인다(판정 명령과 별도 실행).
(1) 실패 보고마다 예외가 AttributeError이고 obj가 모듈이면 그 모듈 __file__을 기록
(2) 세션 끝에 sys.modules 중 파일이 있는 모듈 전부를 분류: 복제본 루트 안 / 메인 저장소 안 / 그 밖
결과 JSON은 환경 변수 ISO_PROBE_OUT, 복제본 루트는 ISO_PROBE_ROOT, 메인 저장소 루트는 ISO_PROBE_MAIN."""
import json
import os
import sys
import types

_ROOT = os.path.normcase(os.path.abspath(os.environ["ISO_PROBE_ROOT"]))
_MAIN = os.path.normcase(os.path.abspath(os.environ["ISO_PROBE_MAIN"]))
_fail = []


def _where(f):
    f = os.path.normcase(os.path.abspath(f))
    if f.startswith(_ROOT + os.sep):
        return "clone"
    if f.startswith(_MAIN + os.sep):
        return "MAIN"
    return "other"


def pytest_runtest_makereport(item, call):
    if call.excinfo is None:
        return
    e = call.excinfo.value
    ent = {"nodeid": item.nodeid, "exc": type(e).__name__}
    obj = getattr(e, "obj", None) if isinstance(e, AttributeError) else None
    if isinstance(obj, types.ModuleType):
        f = getattr(obj, "__file__", None)
        ent["obj_module"] = obj.__name__
        ent["obj_file"] = f
        ent["obj_where"] = _where(f) if f else None
    _fail.append(ent)


def pytest_sessionfinish(session, exitstatus):
    mods = {}
    for name, m in list(sys.modules.items()):
        f = getattr(m, "__file__", None)
        if not f:
            continue
        w = _where(f)
        if w != "other":
            mods[name] = {"file": f, "where": w}
    out = {"root": _ROOT, "main": _MAIN, "exitstatus": int(exitstatus),
           "n_clone": sum(1 for v in mods.values() if v["where"] == "clone"),
           "main_modules": {k: v for k, v in sorted(mods.items()) if v["where"] == "MAIN"},
           "key_modules": {k: mods.get(k) for k in ("sizing_recipe", "run_harness", "stick_diagram", "design_report",
                                                    "conftest", "merge_gate", "role_paths")},
           "failures": _fail}
    with open(os.environ["ISO_PROBE_OUT"], "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
