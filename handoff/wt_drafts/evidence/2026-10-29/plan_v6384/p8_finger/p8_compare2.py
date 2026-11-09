"""P8 비교(완전판): p8_enum.out.jsonl의 슬라이스별 W_s(w_by_slice)에서 자기 정합 해 전부를 다시 세고(bin 소속 = (lo, hi], 첫 bin은 lo 포함 --
as-built '아래 bin 우선' 재현, 엔진 저장 fits 앞 12개와 대조), 고르는 규칙을 옛 반복 규칙과 대조한다.
 (B') w_f ≤ w_hi 가운데 w_f 최대, 같으면 |m·w_f − W_s| 최소   (C) m 최소, 같으면 w_f 최대   (D) 총 폭 m·w_f 최소
 (E) 기제 (ii) 대응: bin 안 슬라이스가 둘 이상이면 IDu를 w에 대해 bin 안 선형 보간(bin 경계 넘는 보간 없음), 선택 = B' 기준
출력 p8_compare2.out.json, p8_interp.out.json"""
import json, collections
G, WMIN = 0.005, 0.42


def bins_of(sl):
    return sorted({tuple(v[1]) for v in sl.values()})


def fits_of(e):
    sl = e["w_by_slice"]; bins = bins_of(sl); first = bins[0]

    def in_bin(w, b):
        lo, hi = b
        return (lo - G / 2 <= w <= hi + G / 2) if b == first else (lo + G / 2 < w <= hi + G / 2)
    out = []
    for k, (ws, b, W) in sl.items():
        b = tuple(b); m = 1
        while True:
            wf = round(W / m / G) * G
            if wf < WMIN - G / 2:
                break
            if in_bin(wf, b):
                cands = sorted((abs(v[0] - wf), v[0], kk) for kk, v in sl.items() if tuple(v[1]) == b and v[0] >= WMIN - G / 2)
                if cands and cands[0][2] == k:
                    out.append((m, round(wf, 4), k, W))
            m += 1
    return out


def fits_interp(e):
    sl = e["w_by_slice"]; bins = bins_of(sl); first = bins[0]; out = []
    for b in bins:
        pts = sorted((v[0], 1.0 / v[2]) for v in sl.values() if tuple(v[1]) == b and v[0] >= WMIN - G / 2)   # (w, 1/W ∝ IDu)
        if not pts:
            continue
        lo = max(b[0], WMIN) if b == first else b[0] + G
        hi = b[1]

        def invW(w):
            if len(pts) == 1 or w <= pts[0][0]:
                return pts[0][1]
            for (w0, y0), (w1, y1) in zip(pts, pts[1:]):
                if w <= w1:
                    return y0 + (y1 - y0) * (w - w0) / (w1 - w0)
            return pts[-1][1]
        n0, n1 = int(round(lo / G)), int(round(hi / G))
        Ws = [1.0 / invW(n * G) for n in range(n0, n1 + 1)]
        for m in range(max(1, int(min(Ws) / hi) - 1), int(max(Ws) / lo) + 2):
            for n in range(n0, n1 + 1):
                w = n * G; W = Ws[n - n0]
                if abs(m * w - W) <= m * G / 2 + 1e-12:
                    out.append((m, round(w, 4), "bin(%.2f,%.2f]" % b, W))
    return out


def pickB(ok):
    return max(ok, key=lambda f: (f[1], -abs(f[0] * f[1] - f[3])))


rows = collections.defaultdict(collections.Counter); detail = []; check = collections.Counter(); interp = collections.Counter(); idet = []
for l in open("p8_enum.out.jsonl", encoding="utf-8"):
    r = json.loads(l)
    for p in r.get("points", []):
        for dev, d in p["devices"].items():
            it, e = d["iter_rule"], d["enum"]
            F = fits_of(e)
            stored = [(f[0], round(f[1], 4), str(f[2])) for f in e["fits"]]
            mine = sorted((f[0], f[1], str(f[2])) for f in F)[:len(stored)]
            check["stored_prefix_match" if mine == stored else "stored_prefix_mismatch"] += 1
            c = rows[r["circuit"]]; c["device_points"] += 1; c["iter_" + it["status"]] += 1
            ok = [f for f in F if f[1] <= e["w_hi_um"] + G / 2]
            FI = fits_interp(e); okI = [f for f in FI if f[1] <= e["w_hi_um"] + G / 2]
            interp[(r["circuit"], it["status"], "E_fit" if okI else "E_none")] += 1
            if it["status"] != "converged":
                idet.append([r["circuit"], p["point"], dev, it["status"], "B'", pickB(ok)[:3] if ok else None, "E", pickB(okI)[:3] if okI else None])
            if not ok:
                c["rule_none"] += 1
                if it["status"] == "converged":
                    detail.append([r["circuit"], p["point"], dev, "converged but no B' fit", len(F)])
                continue
            B = pickB(ok); C = min(ok, key=lambda f: (f[0], -f[1])); D = min(ok, key=lambda f: (f[0] * f[1], f[0]))
            if it["status"] == "converged":
                last = it["seq"][-1]; key_it, m_it, wf_it = str(it["final"]), last[2], last[3]
                for name, pk in (("B", B), ("C", C), ("D", D)):
                    same = pk[2] == key_it and abs(pk[1] - wf_it) <= G
                    c[name + ("_same" if same else "_diff")] += 1
                    if not same and name == "B":
                        detail.append([r["circuit"], p["point"], dev, "converged", "iter(m,w_f,key)", [m_it, wf_it, key_it], "B'", B[:3]])
            else:
                c["iter_fail_but_B_fit"] += 1
json.dump({"check": dict(check), "per_circuit": {k: dict(v) for k, v in rows.items()}, "detail": detail},
          open("p8_compare2.out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"counts": {"|".join(k): v for k, v in interp.items()}, "detail": idet}, open("p8_interp.out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(dict(check))
for k, v in rows.items():
    print(k, dict(v))
for d in detail:
    print(d)
print("INTERP", {"|".join(k): v for k, v in interp.items()})
for d in idet:
    print(d)
