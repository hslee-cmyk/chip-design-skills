"""measure-only prototype (NOT a role artifact): synthetic-return scenarios for the M10 entry branch contract (design 30 §2.3 (iii)).
Each scenario patches the names the moved code reads as module globals (optimize_full_circuit_budget, run_full_circuit_audit_from_topology,
save_instance_json, assemble_report_data, save_html_report, diagnose_sizing_roles_gap) on a target module, records calls, and returns
stdout + calls with output paths normalised to <OUT>."""
import contextlib
import io
import types

NAMES = ("optimize_full_circuit_budget", "run_full_circuit_audit_from_topology", "save_instance_json",
         "assemble_report_data", "save_html_report", "diagnose_sizing_roles_gap")


def _fp(ar, pd):
    return types.SimpleNamespace(aspect_ratio=ar, packing_density=pd)


def _bs():
    return types.SimpleNamespace(ok=True, rectangular=False, width_ratio=1.25, approx=True, row_widths=[1, 2], row_heights=[3])


def _pr(ar=1.2, pd=0.7, rounds=True):
    return {"layout_retry_rounds": ([{"target": "M1", "row_split": {"M1": 2}, "score_before": 1.5, "score_after": 1.25, "accepted": True},
                                     {"target": "M2", "row_split": {"M2": 3}, "score_before": 1.25, "score_after": 1.5, "accepted": False}]
                                    if rounds else []),
            "floorplan": _fp(ar, pd), "row_split": {"M1": 2}, "box_shape": _bs(),
            "coverage": types.SimpleNamespace(ok=False, missing=["M9"])}


def _res(pr, audit_ok=True):
    return {"pipeline_result": pr, "theta_star": {"Ibg": 1e-5}, "audit_ok": audit_ok, "metrics": {"gain_db": 70.0}, "sizing": {"M1": {"W": 1e-6}}}


def _audit(ok):
    return types.SimpleNamespace(ok=ok, checks=[types.SimpleNamespace(name="c1", ok=True, detail="d1"),
                                                types.SimpleNamespace(name="c2", ok=ok, detail="d2")])


SCEN = {
    "pr_none_audit_skip": dict(opt=lambda: _res(None), audit=ValueError("no sections")),
    "full_ok": dict(opt=lambda: _res(_pr()), audit=_audit(True)),
    "notes_all": dict(opt=lambda: _res(_pr(ar=2.0, pd=0.3), audit_ok=False), audit=_audit(False)),
    "density_only_bad": dict(opt=lambda: _res(_pr(ar=1.0, pd=0.4, rounds=False)), audit=_audit(True)),
    "aspect_only_bad": dict(opt=lambda: _res(_pr(ar=1.6, pd=0.9, rounds=False)), audit=_audit(True)),
    "boundary_eq": dict(opt=lambda: _res(_pr(ar=1.5, pd=0.5, rounds=False)), audit=_audit(True)),
    "audit_skip_with_pr": dict(opt=lambda: _res(_pr()), audit=ValueError("no sections")),
    "opt_valueerror_diag": dict(opt=ValueError("infeasible"), audit=_audit(True), diag="GAP-REPORT"),
    "opt_valueerror_diag_fails": dict(opt=ValueError("infeasible"), audit=_audit(True), diag=KeyError("x")),
    "opt_runtimeerror": dict(opt=RuntimeError("boom"), audit=_audit(True), diag="GAP-REPORT"),
}


def run_scenario(mod, name, call, out_dir, root):
    """mod = module whose globals the moved code reads; call() runs the code under test. Returns {stdout, calls}."""
    sc = SCEN[name]
    calls = []
    mods = mod if isinstance(mod, (list, tuple)) else [mod]
    owner = {n: next(m for m in mods if hasattr(m, n)) for n in NAMES}
    saved = {n: getattr(owner[n], n) for n in NAMES}

    def rec(nm, ret):
        def f(*a, **k):
            calls.append([nm, list(a), dict(sorted(k.items()))])
            if isinstance(ret, BaseException):
                raise ret
            return ret() if callable(ret) else ret
        return f
    try:
        setattr(owner["optimize_full_circuit_budget"], "optimize_full_circuit_budget", rec("optimize_full_circuit_budget", sc["opt"]))
        setattr(owner["run_full_circuit_audit_from_topology"], "run_full_circuit_audit_from_topology", rec("run_full_circuit_audit_from_topology", sc["audit"]))
        setattr(owner["save_instance_json"], "save_instance_json", rec("save_instance_json", None))
        setattr(owner["assemble_report_data"], "assemble_report_data", rec("assemble_report_data", {"report": 1}))
        setattr(owner["save_html_report"], "save_html_report", rec("save_html_report", None))
        setattr(owner["diagnose_sizing_roles_gap"], "diagnose_sizing_roles_gap", rec("diagnose_sizing_roles_gap", sc.get("diag", "D")))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            call()
    finally:
        for n, v in saved.items():
            setattr(owner[n], n, v)
    return {"stdout": _s(buf.getvalue(), out_dir, root), "calls": _norm(calls, (out_dir, root))}


def _s(x, out_dir, root):
    for a, t in ((out_dir, "<OUT>"), (root, "<ROOT>")):
        x = x.replace(a, t).replace(a.replace("\\", "/"), t)
    return x


def _norm(x, od):
    out_dir = od
    if isinstance(x, str):
        return _s(x, od[0], od[1])
    if isinstance(x, dict):
        return {str(k): _norm(v, out_dir) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [_norm(v, out_dir) for v in x]
    if isinstance(x, (int, float, bool)) or x is None:
        return x
    return type(x).__name__
