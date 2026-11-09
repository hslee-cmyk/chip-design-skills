"""spec이 oracle 자기부하 점근선(gm/ID 20, CL 30 fF에서 ~970 MHz) 위일 때 닫기 거동(발산·정지 검출). 결과 append(results.jsonl)."""
import z1_toy as z

th = {"L1": 5e-7, "L3": 5e-7, "gmid1": 20.0, "gmid3": 10.0, "I": 50e-6, "CL": 3e-14}
for aim in ("mid", "secant"):
    try:
        z.run_closure("infeasible_cl3e-14_g20_1000M", th, "GBW", 1000e6, 0.01, aim)
    except Exception as e:
        print(aim, "EXC", type(e).__name__, str(e)[:200])
