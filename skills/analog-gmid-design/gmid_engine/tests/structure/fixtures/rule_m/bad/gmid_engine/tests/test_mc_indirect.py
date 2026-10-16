from gmid_engine import pipeline
from gmid_engine.pipeline import run_stage_a as rsa
from gmid_engine.search import open_run


def test_import_alias_reused():
    d, c = open_run()
    rsa("a", "s", None, output_dir="o", donors=d, counters=c)
    rsa("b", "s", None, output_dir="o", donors=d, counters=c)


def test_name_assigned_entry_param(d, c):
    go = pipeline.run_stage_a
    return go("a", "s", None, output_dir="o", donors=d, counters=c)


def test_getattr_entry_attribute(res):
    getattr(pipeline, "run_stage_a")("a", "s", None, output_dir="o", donors=res.donors, counters=res.counters)


def test_branch_assignment_does_not_dominate(flag):
    if flag:
        d, c = open_run()
    else:
        d, c = open_run()
    return rsa("a", "s", None, output_dir="o", donors=d, counters=c)
