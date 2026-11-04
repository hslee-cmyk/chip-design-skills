"""A8 판정 측정(복제본 전용): 같은 toy·같은 θ 의 graph.metrics_ss·metrics_aux value_fp 와 DC 지문, 보고 값을 base·head 양쪽에서 기록."""
import json
import os

from gmid_engine.core import PdkMismatchBlock, PdkMismatchModel, fp_of
from gmid_engine.metrics import MismatchSource, ss_evaluate
from gmid_engine.sizing import METRICS_KEY

from . import u7_hand as H
from .test_metrics_aux import _struct, case, theta  # noqa: F401

OUT = os.environ["PROBE_OUT"]


def test_a8(case):  # noqa: F811
    spec, ctx, sealed, js = case
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js, structure=H.MetricStructure_of(_struct()))
    snap = res.snapshot
    row = {"dc_v": fp_of(tuple(sorted(snap.column("node", "dc_v")))), "ss_dev": fp_of(tuple(sorted(snap.column("device", "ss_dev"), key=lambda kv: kv[0])))}
    for f in ("metrics_ss", "metrics_aux", "metrics_dc"):
        got = snap.field("graph", METRICS_KEY, f)
        row[f] = None if got is None else got.value_fp
    aux = snap.value("graph", METRICS_KEY, "metrics_aux")
    row["aux_entries"] = [(r.metric, repr(v.value)[:120], [(u.code) for u in v.undefined]) for r, v in aux.entries]
    row["reports"] = [(n, repr(v)[:400]) for n, v in aux.reports]
    with open(OUT, "ab") as f:
        f.write((json.dumps(row, ensure_ascii=False, default=str) + "\n").encode("utf-8"))
