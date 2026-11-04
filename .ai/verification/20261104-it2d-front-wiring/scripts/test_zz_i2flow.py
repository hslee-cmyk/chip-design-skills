"""IT-2d·2e 판정 탐침(복제본 전용): 실회로 탐색에서 graph.icm_config·node.dc_window_cfg 실제 소비, 세 metric = V_cm 칸 손 식, 부분 스냅샷 지문·범위."""
import json
import os
import shutil
import sys
import tempfile

import pytest

from gmid_engine.lut import LutMemo
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import build_search_context, find_front, open_run
from gmid_engine.sizing import METRICS_KEY, build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
import gmid_engine.metrics  # noqa: F401
import gmid_engine.search.kernel as kernel_mod

from test_g10_no_recompute_9circuits import LIBRARY, _settings, env  # noqa: F401

aux_mod = sys.modules["gmid_engine.metrics.metrics_aux"]
OUT = os.environ["PROBE_OUT"]
FLOW = os.environ["PROBE_FLOW"].split(",")


def rec(case, **kw):
    with open(OUT, "ab") as f:
        f.write((json.dumps({"case": case, **kw}, ensure_ascii=False, default=str) + "\n").encode("utf-8"))


@pytest.mark.parametrize("circuit", FLOW)
def test_flow(env, circuit, tmp_path, monkeypatch):  # noqa: F811
    donors, counters = open_run()
    out = tmp_path / "o"
    a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), env.lut, output_dir=out, donors=donors, counters=counters)
    memo = LutMemo(env.lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, memo, env.pdk, output_dir=out, diagnostic=True, settings=_settings())
    if (a.status, b.status) != ("ok", "ok"):
        rec("status", circuit=circuit, a=a.status, b=b.status)
        return
    calls = {"icm": 0, "ports": 0, "bad": 0, "eval": 0, "with_metric": 0, "icm_undefined": 0}
    real_icm, real_ports = aux_mod.icm_window_metrics, aux_mod._icm_ports

    def spy_icm(config, ports, input_dc):
        got = real_icm(config, ports, input_dc)
        calls["icm"] += 1
        if config.config is not None and got.icmr_v is not None:
            ok = got.icmr_v == config.vcm_hi - config.vcm_lo and got.icm_margin_v == min(config.vcm0 - config.vcm_lo, config.vcm_hi - config.vcm0)
            calls["bad"] += not ok
        else:
            calls["icm_undefined"] += 1
        return got

    def spy_ports(projection):
        calls["ports"] += 1
        return real_ports(projection)
    monkeypatch.setattr(aux_mod, "icm_window_metrics", spy_icm)
    monkeypatch.setattr(aux_mod, "_icm_ports", spy_ports)
    real = kernel_mod.ss_evaluate
    sample = []

    def spy(sealed, ctx, theta, *args, **kw):
        ev = real(sealed, ctx, theta, *args, **kw)
        calls["eval"] += 1
        if len(sample) < 3:
            ic = ev.snapshot.value("graph", METRICS_KEY, "icm_config")
            names = {r.metric: (res.value, [u.code for u in res.undefined]) for r, res in ev.ss.entries if r.metric in ("icmr_v", "icm_margin_v", "swing_out_v")}
            rep = dict(ev.ss.reports).get("swing_icmr")
            sample.append({"config": ic.config, "vcm": (ic.vcm0, ic.vcm_lo, ic.vcm_hi), "metrics": names, "report_keys": None if rep is None else [k for k, _v in rep], "report_window": None if rep is None else dict(rep)["window"]})
        return ev
    monkeypatch.setattr(kernel_mod, "ss_evaluate", spy)
    root = tempfile.mkdtemp(prefix="pi", dir=os.environ.get("TEMP") or None)
    try:
        kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
        sctx = build_search_context(kctx, a.spec, _settings(), root, env.pdk, env.rule, code_fp=a.code_fp)
        fr = find_front(sctx, [])
        perf = dict(fr.perf)
        rows = [dict(r) for r in perf["blocks"]]
        recompute = sum(r["recomputes_same_input"] for r in rows)
        rec("flow", circuit=circuit, calls=calls, recompute=recompute, sample=sample, spec_metrics=sorted({str(c.metric) for c in a.spec.constraints}))
    finally:
        shutil.rmtree(root, ignore_errors=True)
