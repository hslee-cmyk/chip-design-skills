"""p9: 병합본 redteam lib/rt.py 오류 경로(계약 9) -- 함수 수준. 사용: python -B p9_rt_errors.py <lib 디렉터리> <작업 디렉터리> <출력 json>"""
import json
import os
import sys
from pathlib import Path

lib, work, outp = sys.argv[1:4]
os.environ["WORK"] = work
sys.path.insert(0, lib)
import rt  # noqa: E402

ENG = "skills/analog-gmid-design/assets/rt_engine.py"
SRC = {"text": "def f(x):\n    return x\n"}


def case(head):
    return {"base": {ENG: SRC}, "head": head}


tests = {
    "path_missing(head ref, file only in base)": case({"a.md": {"text": "t: @bindhash(head:%s:f)" % ENG}}),
    "qualname_missing": case({ENG: SRC, "a.md": {"text": "t: @bindhash(head:%s:g)" % ENG}}),
    "self_reference": case({ENG: {"text": "def f(x):\n    return x\n# @bindhash(head:%s:f)\n" % ENG}}),
    "ref_file_has_placeholder(cycle)": case({ENG: {"text": "def f(x):\n    return x\n# @bindhash(base:%s:f)\n" % ENG},
                                             "a.md": {"text": "t: @bindhash(head:%s:f)" % ENG}}),
    "duplicate_qualname": case({ENG: {"text": "def f(x):\n    return x\n\n\ndef f(x):\n    return 1\n"},
                                "a.md": {"text": "t: @bindhash(head:%s:f)" % ENG}}),
    "bad_side": case({ENG: SRC, "a.md": {"text": "t: @bindhash(mid:%s:f)" % ENG}}),
    "None_spec_ref": {"base": {ENG: SRC}, "head": {ENG: None, "a.md": {"text": "t: @bindhash(head:%s:f)" % ENG}}},
}
res = {}
for name, c in tests.items():
    try:
        rt._vrepo_contents(None, c)
        res[name] = {"raised": None}
    except RuntimeError as e:
        res[name] = {"raised": "RuntimeError", "msg": str(e)}
    except Exception as e:  # 다른 예외도 기록(조용한 통과만 아니면 됨)
        res[name] = {"raised": type(e).__name__, "msg": str(e)}
# 정상 경로 + 자리표시자 없는 파일 바이트 불변
c = case({ENG: SRC, "a.md": {"text": "t: @bindhash(base:%s:f)" % ENG}})
out = rt._vrepo_contents(None, c)
res["normal"] = {"a.md": out["head"]["a.md"].decode(), "eng_bytes_same": out["head"][ENG] == SRC["text"].encode()}
# out_jsonl 관찰
d = Path(work)
d.mkdir(parents=True, exist_ok=True)
for name, content in {"array_line": '{"id": "a", "result": "killed"}\n[1, 2]\n', "not_json": "garbage\n",
                      "ok": '{"id": "b", "result": "exempt", "bind_hash": "h"}\n{"id": "a", "result": "killed"}\n{"id": "c", "result": "not_targeted"}\n{"id": "a2", "result": "exempt"}\n'}.items():
    p = d / (name + ".jsonl")
    p.write_text(content, encoding="utf-8")
    try:
        res["out_jsonl_" + name] = {"observed": rt._out_jsonl_observed(p)}
    except RuntimeError as e:
        res["out_jsonl_" + name] = {"raised": "RuntimeError", "msg": str(e)}
res["out_jsonl_missing_file"] = {"observed": rt._out_jsonl_observed(d / "nope.jsonl")}
with open(outp, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
