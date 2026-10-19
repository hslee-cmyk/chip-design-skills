from gmid_engine.pipeline import run_stage_a
from gmid_engine.search import open_run


def test_loop_outside():
    d, c = open_run()
    for name in ("a", "b"):
        run_stage_a(name, "s", None, output_dir="o", donors=d, counters=c)


def test_comprehension():
    d, c = open_run()
    return [run_stage_a(n, "s", None, output_dir="o", donors=d, counters=c) for n in ("a", "b")]


def test_same_name_twice():
    d, c = open_run()
    run_stage_a("a", "s", None, output_dir="o", donors=d, counters=c)
    run_stage_a("b", "s", None, output_dir="o", donors=d, counters=c)


def test_free_variable():
    d, c = open_run()

    def inner():
        return run_stage_a("a", "s", None, output_dir="o", donors=d, counters=c)

    lam = lambda: run_stage_a("b", "s", None, output_dir="o", donors=d, counters=c)
    return inner(), lam()


def test_packed():
    d, c = open_run()
    kw = dict(donors=d, counters=c)
    run_stage_a("a", "s", None, output_dir="o", **kw)
    args = ("a", "s", None)
    run_stage_a(*args, output_dir="o", donors=d, counters=c)


def test_loop_outer_body_inner_call():
    for name in ("a", "b"):
        d, c = open_run()
        for _k in (1,):
            run_stage_a(name, "s", None, output_dir="o", donors=d, counters=c)
