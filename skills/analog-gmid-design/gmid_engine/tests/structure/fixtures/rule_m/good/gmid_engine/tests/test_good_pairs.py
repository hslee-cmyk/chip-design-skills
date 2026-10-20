import json

from gmid_engine.graph import build_s1
from gmid_engine.pipeline import run_stage_a
from gmid_engine.search import open_run
from gmid_engine.sizing import build_kernel_context

NAMES = ("a", "b")


def run_one(name):
    donors, counters = open_run()
    return run_stage_a(name, "s", None, output_dir="o", donors=donors, counters=counters)


def test_one_to_one():
    donors, counters = open_run()
    res = run_stage_a("a", "s", None, output_dir="o", donors=donors, counters=counters)
    assert res.donors is donors and res.counters is counters
    other_d, other_c = open_run()
    res2 = run_stage_a("a", "s", None, output_dir="o", donors=other_d, counters=other_c)
    assert res2 is not res


def test_loop_inside():
    out = []
    for name in NAMES:
        d, c = open_run()
        out.append(run_stage_a(name, "s", None, output_dir="o", donors=d, counters=c))
    assert len(out) == 2


def test_unit_one_pair_many_wrapper_calls(pair):
    donors, counters = pair
    s1 = build_s1("doc", donors=donors, counters=counters)
    s1b = build_s1("doc", donors=donors, counters=counters)
    ctx = build_kernel_context(s1, "inputs", "lut", donors=donors, counters=counters)
    assert s1 is s1b and ctx.donors is donors


def test_missing_keyword_type_error():
    donors, counters = open_run()
    run_stage_a("a", "s", None, output_dir="o", donors=donors)
    assert counters is not None


def test_report_counters_snapshot(tmp_path):
    donors, counters = open_run()
    res = run_stage_a("a", "s", None, output_dir="o", donors=donors, counters=counters)
    text = json.dumps([r.block for r in counters.snapshot().blocks])
    (tmp_path / "x.json").write_text(text)
    return res.report, "open_run 은 문자열 안 언급이라 대상이 아니다"


def test_helper_run():
    assert run_one("a") is not run_one("b")


S1_CACHE = {}


def test_snapshot_cache_is_not_a_run(tmp_path):
    donors, counters = open_run()
    res = run_stage_a("a", "s", None, output_dir="o", donors=donors, counters=counters)
    S1_CACHE["a"] = res.s1


def test_same_name_reassigned_per_call():
    # design 40 §2.4.5 (M-c): 대입마다 호출 하나 -- 같은 이름을 새 open_run() 튜플 풀기로 다시 대입하면 허용
    donors, counters = open_run()
    first = run_stage_a("a", "s", None, output_dir="o", donors=donors, counters=counters)
    donors, counters = open_run()
    second = run_stage_a("a", "s", None, output_dir="o2", donors=donors, counters=counters)
    assert first is not second


def test_alias_one_to_one():
    from gmid_engine.pipeline import run_stage_a as rsa
    d, c = open_run()
    return rsa("a", "s", None, output_dir="o", donors=d, counters=c)
