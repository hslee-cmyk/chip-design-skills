"""IT-2b 감사: P(a)·L12 (a) k_max·L12 (f) toy 의 LUT 상수(NEG_QV·NEG_QD)를 바꿔 test 결과와 실패 단언을 본다(복제본 m 의 test 파일만 잠시 바꾸고 복원).
또 k_max test 전제 값(창 차·tol)을 탐침으로 출력한다.
usage: python -I neg_lut_probe.py <clone m root> <out jsonl>
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
SKILL = ROOT / "skills" / "analog-gmid-design"
TF = SKILL / "gmid_engine" / "tests" / "sizing" / "test_block_columns.py"
TESTS = {"Pa": "test_it2b_pa_negative_sensitivity_port_window_is_min_max_of_the_two_end_voltages",
         "kmax": "test_it2b_l12a_k_max_exhausted_root_window_is_unsettled_and_y_range_kept",
         "L12f": "test_it2b_l12a_window_tol_v_is_the_tolerance_of_the_last_measured_solution"}
PROBE = '''

def test_zz_audit_kmax_probe(tmp_path, monkeypatch):
    """감사 탐침(커밋 안 함): k_max test 의 전제 값들을 출력한다."""
    import json as _j
    acc, ctx = _neg_ctx(tmp_path)
    star = _window_of(_columns_with_declared(ctx, _neg_theta(ctx, 0.5)))["x"]
    t_tab = tol_v_table(acc.memo, "nmos", 100).at(1e-6, 0.9, "id_equivalent")
    monkeypatch.setattr("gmid_engine.sizing.block_columns.k_max", lambda width, tol_: 1)
    w = _window_of(_columns_with_declared(ctx, _neg_theta(ctx, 0.3)))["x"]
    print("AUDITPROBE " + _j.dumps({"star": [star.lo, star.hi, star.input_status, star.tol_v], "w": [w.lo, w.hi, w.input_status, w.tol_v],
                                    "tol_table_0p9": t_tab, "dlo": abs(w.lo - star.lo), "dhi": abs(w.hi - star.hi)}))
'''


def main():
    orig = TF.read_bytes()
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        for qv, qd in ((0.05, 20.0), (0.5, 20.0), (0.05, 0.0), (0.5, 0.0)):
            raw = orig.decode("utf-8")
            crlf = "\r\n" in raw
            t = raw.replace("\r\n", "\n")
            t2 = re.sub(r"^NEG_QD = [0-9.]+", "NEG_QD = %r" % qd, t, count=1, flags=re.M)
            t2 = re.sub(r"^NEG_QV, NEG_VS_KINK = [0-9.]+, 1\.6", "NEG_QV, NEG_VS_KINK = %r, 1.6" % qv, t2, count=1, flags=re.M)
            applied = ("NEG_QD = %r" % qd) in t2 and ("NEG_QV, NEG_VS_KINK = %r, 1.6" % qv) in t2
            t2 += PROBE
            TF.write_bytes((t2.replace("\n", "\r\n") if crlf else t2).encode("utf-8"))
            res = {"NEG_QV": qv, "NEG_QD": qd, "applied": applied}
            for short, name in list(TESTS.items()) + [("probe", "test_zz_audit_kmax_probe")]:
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
