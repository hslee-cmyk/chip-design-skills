"""IT-2b 감사(test 여덟째 db216ef7): k_max test 상태 비교 전제와 L12 (f) 상대 허용오차를 수치로 본다(복제본 m 의 test 파일만 잠시 바꾸고 복원).
NEG_QV 를 바꿔 k_max test·L12 (f) test 결과와 실패 줄, 탐침 값(tol 공개 표·상한 1·2·3·주입 없음 상태·L12 (f) tol_first·tol_last·tol_v)을 적는다.
usage: python -I neg_lut_probe2.py <clone root> <final test file 경로> <out jsonl>
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
SRC = Path(sys.argv[2])
OUT = Path(sys.argv[3])
SKILL = ROOT / "skills" / "analog-gmid-design"
TF = SKILL / "gmid_engine" / "tests" / "sizing" / "test_block_columns.py"
TESTS = {"kmax": "test_it2b_l12a_k_max_exhausted_root_window_is_unsettled_and_y_range_kept",
         "L12f": "test_it2b_l12a_window_tol_v_is_the_tolerance_of_the_last_measured_solution",
         "Pa": "test_it2b_pa_negative_sensitivity_port_window_is_min_max_of_the_two_end_voltages"}
PROBE = '''

def test_zz_audit_probe2(tmp_path, monkeypatch):
    """감사 탐침(커밋 안 함)."""
    import json as _j
    from gmid_engine.sizing import dc_widths
    out = {}
    def tol_of(acc, ctx, snap):
        ops = dict(dc_widths(snap, ctx.lut, donors=ctx.donors, counters=ctx.counters).column("device", "dc_op"))
        return min(tol_v_table(acc.memo, op.kind, op.w_key).at(op.L, op.vds, "id_equivalent") for op in ops.values())
    for label, cap, y in (("none_y05", None, 0.5), ("none_y03", None, 0.3), ("k1_y03", 1, 0.3), ("k2_y03", 2, 0.3), ("k3_y03", 3, 0.3)):
        (tmp_path / label).mkdir()
        acc, ctx = _neg_ctx(tmp_path / label)
        if cap is not None:
            monkeypatch.setattr("gmid_engine.sizing.block_columns.k_max", (lambda c: (lambda width, tol_: c))(cap))
        else:
            monkeypatch.undo()
        snap = _columns_with_declared(ctx, _neg_theta(ctx, y))
        w = _window_of(snap)["x"]
        out[label] = [w.lo, w.hi, w.input_status, w.tol_v, tol_of(acc, ctx, snap)]
    monkeypatch.undo()
    t, u, d, _ = _neg_solve(0.9)
    (tmp_path / "f").mkdir()
    acc, ctx = _neg_ctx(tmp_path / "f")
    tv = tol_v_table(acc.memo, "nmos", 100)
    tol_first = min(tv.at(1e-6, v, "id_equivalent") for v in (1.8 - t, 1.8 - u, d - u, u))
    snap = _columns_with_declared(ctx, _neg_theta(ctx, 0.5))
    out["L12f"] = {"tol_first": tol_first, "tol_last": tol_of(acc, ctx, snap), "tol_v": _window_of(snap)["x"].tol_v}
    print("AUDITPROBE " + _j.dumps(out))
'''


def main():
    orig = TF.read_bytes()
    final = SRC.read_bytes()
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        for qv in (0.005, 0.05, 0.5):
            raw = final.decode("utf-8")
            crlf = "\r\n" in raw
            t = raw.replace("\r\n", "\n")
            t2 = re.sub(r"^NEG_QV, NEG_VS_KINK = [0-9.]+, 1\.6", "NEG_QV, NEG_VS_KINK = %r, 1.6" % qv, t, count=1, flags=re.M)
            applied = ("NEG_QV, NEG_VS_KINK = %r, 1.6" % qv) in t2
            t2 += PROBE
            TF.write_bytes((t2.replace("\n", "\r\n") if crlf else t2).encode("utf-8"))
            res = {"NEG_QV": qv, "applied": applied}
            for short, name in list(TESTS.items()) + [("probe", "test_zz_audit_probe2")]:
                r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-s", "--tb=short",
                                    "gmid_engine/tests/sizing/test_block_columns.py::" + name], cwd=SKILL, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", env=env)
                res[short] = "pass" if r.returncode == 0 else "FAIL"
                if r.returncode:
                    res[short + "_E"] = [ln for ln in r.stdout.splitlines() if ln.startswith("E ") or ".py:" in ln][:6]
                if short == "probe":
                    m = [ln for ln in r.stdout.splitlines() if "AUDITPROBE" in ln]
                    res["probe_values"] = json.loads(m[0].split("AUDITPROBE ", 1)[1]) if m else None
            print(json.dumps(res, ensure_ascii=False), flush=True)
            with OUT.open("a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
    finally:
        TF.write_bytes(orig)


if __name__ == "__main__":
    main()
