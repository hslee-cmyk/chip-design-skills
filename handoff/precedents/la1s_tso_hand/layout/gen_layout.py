"""레이아웃 생성 스크립트(결정적, 숫자 없음) -- two_stage_ota 손설계용 후보(저장소에 둘 후보 산출물).

입력
  design.json : 소자(kind, d, g, s, L, w_s, m) + 행 의도(intent): 행마다 kind·손가락 열(slot)·대칭 짝.
  PDK 역할 양 : pdklib.quantities() -- finger_pitch_overhead_m, dummy_w_m, tap_w_m, well_spacing_m, row_gap_m,
                manufacturing_grid_m (값은 PDK 선언이 가리키는 원본 파일에서; 이 파일에 PDK 숫자 없음, O-197).
출력
  geometry.json : 손가락별 x 위치·방향·좌우 확산 넷, 소자별 ad/as/pd/ps(손가락별), 행 길이, box, 빈 면적,
                  대칭·Euler 판정.
  layout.svg    : 행·손가락·넷 라벨 그림.

기하 모형(규칙 수준, 의도 문서 §기하 모형):
  - 손가락 x 간격 = L + overhead. 이웃 손가락이 같은 넷을 공유하면 확산 한 칸(폭 overhead)을 반씩 나눈다.
  - 공유가 안 되면(확산 끊김) 끊김 자리에 더미 손가락 하나(간격 L_row + overhead)를 넣는다.
  - 행 양 끝에 더미 폭 dummy_w_m, 확산 끝 칸(폭 overhead)은 한 손가락이 혼자 쓴다.
  - 행 높이 = w_s. NMOS 행 아래 기판 tap(tap_w_m), PMOS 행 위 nwell tap(tap_w_m), P·N 행 사이 well_spacing_m,
    같은 kind 행 사이 row_gap_m.
"""
import json, math, sys

sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/scripts")
import pdklib

Q = pdklib.quantities(["finger_pitch_overhead_m", "dummy_w_m", "tap_w_m", "well_spacing_m", "row_gap_m",
                       "manufacturing_grid_m"])
OV = Q["finger_pitch_overhead_m"]
GRID = Q["manufacturing_grid_m"]


def snap(x):
    return round(x / GRID) * GRID


def orient_row(slots, dev):
    """손가락 열에 방향을 붙인다: 왼쪽 넷이 앞 손가락의 오른쪽 넷과 같도록(확산 공유) 탐욕 + 첫 손가락 두 방향 시도."""
    best = None
    for first in (0, 1):
        seq, breaks = [], 0
        prev_r = None
        for i, name in enumerate(slots):
            d, s = dev[name]["d"], dev[name]["s"]
            opts = [(s, d), (d, s)]
            if i == 0:
                l, r = opts[first]
            else:
                cand = [o for o in opts if o[0] == prev_r]
                if cand:
                    # 다음 손가락과도 이어지는 쪽을 고른다(한 칸 앞보기)
                    if len(cand) == 2 and i + 1 < len(slots):
                        nd = dev[slots[i + 1]]
                        nxt = {nd["d"], nd["s"]}
                        cand.sort(key=lambda o: 0 if o[1] in nxt else 1)
                    l, r = cand[0]
                else:
                    breaks += 1
                    nd = dev[slots[i + 1]] if i + 1 < len(slots) else None
                    nxt = {nd["d"], nd["s"]} if nd else set()
                    l, r = sorted(opts, key=lambda o: 0 if o[1] in nxt else 1)[0]
                    seq.append(("DUMMY", None, None))
            seq.append((name, l, r))
            prev_r = r
        if best is None or breaks < best[1]:
            best = (seq, breaks)
    return best


def build(design):
    dev = design["devices"]
    rows_out = []
    for row in design["rows"]:
        seq, breaks = orient_row(row["slots"], dev)
        L_row = max(dev[n]["L"] for n in row["slots"])  # 행 안 L 혼재 허용(LR8), 더미는 행 최대 L
        ws = {dev[n]["w_s"] for n in row["slots"]}
        if len(ws) != 1:
            raise ValueError("행 %s 안 손가락 폭이 하나가 아님 (LR8): %s" % (row["name"], ws))
        w_s = ws.pop()
        x = Q["dummy_w_m"] + OV  # 왼쪽 더미 + 확산 끝 칸
        fingers = []
        for k, (name, l, r) in enumerate(seq):
            Lf = L_row if name == "DUMMY" else dev[name]["L"]
            fingers.append({"dev": name, "x0": snap(x), "L": Lf, "left": l, "right": r})
            x += Lf + OV
        length = snap(x - OV + OV + Q["dummy_w_m"])  # 마지막 확산 끝 칸 + 오른쪽 더미
        # 확산 공유 판정과 ad/as/pd/ps
        n_f = len(fingers)
        for k, f in enumerate(fingers):
            if f["dev"] == "DUMMY":
                continue
            for side, net in (("left", f["left"]), ("right", f["right"])):
                nb = fingers[k - 1] if side == "left" and k > 0 else (fingers[k + 1] if side == "right" and k + 1 < n_f else None)
                shared = nb is not None and nb["dev"] != "DUMMY" and (nb["right"] if side == "left" else nb["left"]) == net
                area = w_s * OV / 2 if shared else w_s * OV
                perim = OV if shared else w_s + 2 * OV
                term = "d" if net == dev[f["dev"]]["d"] else "s"
                f["a" + term] = area
                f["p" + term] = perim
                f["shared_" + side] = shared
        rows_out.append({"name": row["name"], "kind": row["kind"], "w_s": w_s, "length": length, "breaks": breaks,
                         "fingers": fingers, "pairs": row.get("pairs", {})})
    return rows_out


def symmetry(row):
    """행 손가락 열이 가운데 축에 대해 거울 대칭인가(짝 소자 사상 포함)."""
    pairs = dict(row["pairs"])
    pairs.update({b: a for a, b in row["pairs"].items()})
    fs = [f["dev"] for f in row["fingers"]]
    bad = 0
    for i in range(len(fs) // 2):
        a, b = fs[i], fs[-1 - i]
        if not (b == pairs.get(a, a)):
            bad += 1
    return bad == 0, bad


def euler_paths(row):
    """확산 공유로 이어진 구간 수(= Euler 경로 수). 끊김 0이면 1."""
    return 1 + row["breaks"]


def stack(rows, design):
    """행을 세로로 쌓는다: 아래부터 기판 tap, NMOS 행들, well 간격, PMOS 행들, nwell tap."""
    order = design["stack"]
    byname = {r["name"]: r for r in rows}
    y = Q["tap_w_m"]
    prev_kind = None
    placed = []
    for nm in order:
        r = byname[nm]
        if prev_kind is not None:
            y += Q["well_spacing_m"] if r["kind"] != prev_kind else Q["row_gap_m"]
        r["y0"] = snap(y)
        y += r["w_s"]
        prev_kind = r["kind"]
        placed.append(r)
    y += Q["tap_w_m"]
    box_w = max(r["length"] for r in rows)
    box_h = snap(y)
    # 행이 box 폭보다 짧으면 가운데 정렬(대칭 축 유지)
    for r in rows:
        r["x_off"] = snap((box_w - r["length"]) / 2)
    used = sum(r["length"] * r["w_s"] for r in rows)
    empty_rows = sum((box_w - r["length"]) * r["w_s"] for r in rows)
    return {"box_w": box_w, "box_h": box_h, "box_area": box_w * box_h, "row_area": used,
            "row_empty_area": empty_rows, "row_empty_ratio": empty_rows / (box_w * box_h)}


def per_device_geom(rows, dev):
    g = {n: {"fingers": 0, "ad": 0.0, "as": 0.0, "pd": 0.0, "ps": 0.0, "finger_geom": []} for n in dev}
    for r in rows:
        for f in r["fingers"]:
            if f["dev"] == "DUMMY":
                continue
            d = g[f["dev"]]
            d["fingers"] += 1
            for t in ("ad", "as", "pd", "ps"):
                d[t] += f.get(t, 0.0)
            d["finger_geom"].append({t: f.get(t, 0.0) for t in ("ad", "as", "pd", "ps")})
    return g


def svg(rows, box, path):
    s = 1e6 * 20  # 1 um = 20 px
    W, H = box["box_w"] * s, box["box_h"] * s
    col = {"nmos": "#7fb3d5", "pmos": "#f5b7b1"}
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%.0f" height="%.0f" viewBox="0 0 %.0f %.0f">' % (W + 20, H + 20, W + 20, H + 20),
           '<rect x="10" y="10" width="%.1f" height="%.1f" fill="none" stroke="black"/>' % (W, H)]
    for r in rows:
        y = 10 + H - (r["y0"] + r["w_s"]) * s
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" opacity="0.4"/>' % (10 + r["x_off"] * s, y, r["length"] * s, r["w_s"] * s, col[r["kind"]]))
        for f in r["fingers"]:
            x = 10 + (r["x_off"] + f["x0"]) * s
            out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (x, y - 4, f["L"] * s, r["w_s"] * s + 8, "#555" if f["dev"] == "DUMMY" else "#c0392b"))
            out.append('<text x="%.1f" y="%.1f" font-size="9" text-anchor="middle">%s</text>' % (x + f["L"] * s / 2, y - 6, "d" if f["dev"] == "DUMMY" else f["dev"]))
        out.append('<text x="%.1f" y="%.1f" font-size="10">%s (w_s=%.2fum, %d breaks)</text>' % (12, y + r["w_s"] * s / 2, r["name"], r["w_s"] * 1e6, r["breaks"]))
    out.append("</svg>")
    open(path, "w", encoding="utf-8").write("\n".join(out))


if __name__ == "__main__":
    design = json.load(open(sys.argv[1], encoding="utf-8"))
    rows = build(design)
    box = stack(rows, design)
    res = {"rows": [{k: v for k, v in r.items() if k != "fingers"} | {"symmetric": symmetry(r)[0],
                     "sym_mismatch": symmetry(r)[1], "euler_paths": euler_paths(r),
                     "sequence": [f["dev"] for f in r["fingers"]]} for r in rows],
           "box": box, "devices": per_device_geom(rows, design["devices"]), "pdk": Q}
    json.dump(res, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
    svg(rows, box, sys.argv[3])
