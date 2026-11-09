"""2단 Miller toy(CL 200 fF, Cc 60 fF)에서 oracle PM이 I2로 어디까지 오르는지(도달 가능성) -- e0 정지가 실제 도달 불가인지 확인.
I1 = 손계산 GBW 100 MHz 점(gm/ID 14), Rz = 1/gm6(손계산). 결과 append(miller_pm_curve.jsonl)."""
import json
import math
import os

import numpy as np

import z1_multi as M

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "miller_pm_curve.jsonl")
base = {"L1": 5e-7, "L3": 5e-7, "L6": 5e-7, "L7": 5e-7, "gmid1": 14.0, "gmid3": 10.0, "gmid6": 10.0, "gmid7": 10.0,
        "CL": 2e-13, "Cc": 6e-14}
toy = M.ToyB(base, {})
I1 = 100e6 * 2 * math.pi * base["Cc"] * 2 / 14.0
for i, I2 in enumerate(np.geomspace(20e-6, 2e-3, 9)):
    th = dict(base, I1=I1, I2=float(I2), Rz=1 / (base["gmid6"] * float(I2)))
    h = toy.hand(th)
    o = toy.oracle(th, f"millerpm_{i}")
    rec = {"I2": float(I2), "hand_PM": h["PM"], "oracle_PM": o["PM"], "hand_GBW": h["GBW"], "oracle_GBW": o["GBW"],
           "oracle_A0": o["A0"]}
    with open(OUT, "a", encoding="utf-8") as fo:
        fo.write(json.dumps(rec) + "\n")
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rec.items()})
