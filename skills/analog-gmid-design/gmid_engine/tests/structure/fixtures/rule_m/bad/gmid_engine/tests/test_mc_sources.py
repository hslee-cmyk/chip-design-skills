from gmid_engine.pipeline import run_stage_a
from gmid_engine.search import open_run


def run_case(donors, counters):
    return run_stage_a("t", "s", None, output_dir="o", donors=donors, counters=counters)


def make_pair():
    return open_run()


def test_result_fields():
    d, c = open_run()
    a = run_stage_a("t", "s", None, output_dir="o", donors=d, counters=c)
    b = run_stage_a("t", "s", None, output_dir="o", donors=a.donors, counters=a.counters)
    assert a is not b


def test_other_call():
    d, c = make_pair()
    run_stage_a("t", "s", None, output_dir="o", donors=d, counters=c)


def test_swapped():
    c, d = open_run()
    run_stage_a("t", "s", None, output_dir="o", donors=d, counters=c)


def test_rebound():
    d, c = open_run()
    d = make_pair()[0]
    run_stage_a("t", "s", None, output_dir="o", donors=d, counters=c)


def test_two_runs():
    d1, c1 = open_run()
    d2, c2 = open_run()
    run_stage_a("t", "s", None, output_dir="o", donors=d1, counters=c2)
