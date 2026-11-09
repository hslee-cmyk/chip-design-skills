# A-24 §18.3 '꼬리에서 완만해지지 않음' 검사: data_digits(어댑터 선언 값) 반올림 PSD 에서 엄격 비교와 자릿수 폭 비교의 거짓 거부·진짜 거부. 시뮬레이터 호출 0. 결과 m4.jsonl
# δ = 8u/Δ, u = 0.5·10^(1-d), Δ = 구간 Δln f. 유도: 파일 값이 V/√Hz 이고 상대 반올림 ≤ u -> S = v² 의 ln 오차 ≤ 2u -> 기울기 오차 ≤ 4u/Δ -> 두 기울기 차 오차 ≤ 8u/Δ
import json, os
import numpy as np
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m4.jsonl")
open(OUT, "w").close()


def w(o):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")


def rs(x, d):
    return np.array([float(f"{v:.{d - 1}e}") for v in x])


d = 9  # calibration.json data_digits
u = 0.5 * 10 ** (1 - d)
for name, fn in (("one_pole", lambda f: 1e-14 / (1 + (f / 1e3) ** 2)),
                 ("two_pole", lambda f: 1e-14 / (1 + (f / 1e3) ** 2) / (1 + (f / 1e5) ** 2)),
                 ("flatten_floor", lambda f: 1e-14 / (1 + (f / 1e3) ** 2) + 1e-20),
                 ("flat", lambda f: 1e-14 + 0 * f)):
    for ppd in (10, 20, 80, 320):
        for dec in (1, 2, 3, 4, 5, 6):
            bad_s = bad_t = 0
            for sh in np.linspace(0, 1, 200):
                f = 1e3 * 10 ** dec * 10 ** ((np.arange(-2, 1) + sh) / ppd)
                v = rs(np.sqrt(fn(f)), d)      # 파일 값 = V/√Hz, 9 자리
                s = v * v
                dl = np.diff(np.log(f))
                g = -np.diff(np.log(s)) / dl
                delta = 8 * u / dl[1]
                bad_s += int(not (g[1] >= g[0] and g[1] > 1))
                bad_t += int(not (g[1] >= g[0] - delta and g[1] > 1))
            w({"psd": name, "ppd": ppd, "decades_above_first_pole": dec, "strict_reject": bad_s, "tol_reject": bad_t, "of": 200})
