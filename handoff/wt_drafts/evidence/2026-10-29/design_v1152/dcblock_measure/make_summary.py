import json, sys
from pathlib import Path
D = Path(__file__).parent
rows = [json.loads(l) for l in open(D / "results.jsonl", encoding="utf-8")]
last = {}
for r in rows:
    last[r["circuit"] if "circuit" in r else "?"] = r
f = lambda x, n=2: "-" if x is None else ("%.*f" % (n, x))
pc = lambda x: "-" if x is None else "%.0f%%" % (100 * x)
out = []
out.append("# dc_columns 합침 판단용 측정 (integ-it12 d759838a, E_B=40, 시간예산 600 s) -- 전부 실측/유도/추정 표기\n")
out.append("## 표 1: 실측 reuse·시간 (FD = fd_jacobian 의 evaluate 호출 중 발생한 블록 호출)\n")
out.append("| 회로 | 상태 | FD dc_columns calls | FD reuse비 | FD dc_widths calls/reuse비 | FD dc_currents calls/reuse비 | 전체(search) dc_columns calls/reuse비 | dc_columns compute 평균 ms (전체/FD) | 실행 wall s | search wall s | dc_columns compute 합 s | 합/실행 | 합/커널(size_and_seal 합) | 합/search |")
out.append("|" + "---|" * 14)
for c, r in last.items():
    if not r.get("searched"):
        out.append("| %s | %s | - | - | - | - | - | - | %s | - | - | - | - | - |" % (c, r["status"], f(r.get("wall_run_s"), 1)))
        continue
    fd, al = r["fd_rows"], r["search_rows_mine"]
    t = r["time"]["dc_columns"]
    s = t["all"]["sum_s"]
    ks = r["time_kernel_size_and_seal"]["all"]["sum_s"]
    out.append("| %s | %s | %d | %s | %d/%s | %d/%s | %d/%s | %s / %s | %s | %s | %s | %s | %s | %s |" % (
        c, r["status"], fd["dc_columns"]["calls"], pc(fd["dc_columns"]["reuse_ratio"]),
        fd["dc_widths"]["calls"], pc(fd["dc_widths"]["reuse_ratio"]), fd["dc_currents"]["calls"], pc(fd["dc_currents"]["reuse_ratio"]),
        al["dc_columns"]["calls"], pc(al["dc_columns"]["reuse_ratio"]),
        f(t["all"]["mean_ms"], 1), f(t["fd"]["mean_ms"], 1), f(r["wall_run_s"], 1), f(r["wall_search_s"], 1), f(s, 2),
        pc(s / r["wall_run_s"]), pc(s / ks if ks else None), pc(s / r["wall_search_s"])))
out.append("\n(전체 dc_columns 행은 perf.blocks 정본과 같은 값인지 아래 표 3에서 대조. 'search' = find_front 구간. 커널 = kernel.size_and_seal 시간 합(DC 커널만, ss 지표 제외).)\n")

out.append("## 표 2: 열 종류별 FD (실측)\n")
out.append("| 회로 | 1회 야코비안 열 수 (current/ln_idu/y/L/total) | θ 전류 열 비율 (1회, 실측) | FD 호출 수 | 누적 명목 열 수 (current/total) | FD evaluate 요청 current/전체 | 커널 실행 current/전체 | current 열의 dc_columns calls/reuse/compute | 다른 열(ln_idu,y,L)의 dc_columns reuse/calls |")
out.append("|" + "---|" * 9)
for c, r in last.items():
    if not r.get("searched"):
        out.append("| %s | %s | | | | | | | |" % (c, r["status"])); continue
    d = r["fd_first_jacobian_dims"]
    tot = d.get("_total", 0)
    cur = d.get("current", 0)
    nom = r["fd_cols_nominal_by_kind"]; nt = sum(nom.values())
    rq = r["fd_eval_req_by_kind"]; kq = r["fd_eval_kernel_by_kind"]
    bk = r["fd_rows_by_kind"]
    cc = bk.get("current", {}).get("dc_columns", {})
    other = [0, 0]
    for k, v in bk.items():
        if k != "current":
            other[0] += v["dc_columns"]["reuses"] + v["dc_columns"]["grafts"] + v["dc_columns"]["replays"]; other[1] += v["dc_columns"]["calls"]
    out.append("| %s | %d/%d/%d/%d/%d | %d/%d = %s | %d | %d/%d | %d/%d | %d/%d | %d/%d/%d | %d/%d |" % (
        c, cur, d.get("ln_idu", 0), d.get("y", 0), d.get("L", 0), tot, cur, tot, pc(cur / tot if tot else None), r["fd_calls"],
        nom.get("current", 0), nt, rq.get("current", 0), sum(rq.values()), kq.get("current", 0), sum(kq.values()),
        cc.get("calls", 0), cc.get("reuses", 0), cc.get("computes", 0), other[0], other[1]))
out.append("\n(1회 야코비안 = 해당 회로 첫 fd_jacobian 호출의 변수 수; 이후 호출에서 변수 수가 같은지는 누적 명목/호출 수로 확인. 고정(skip) 열은 평가 없음.)\n")

out.append("## 표 3: 유도 -- 합친 DC 블록의 예상 손실 (유도값, 실측 아님)\n")
out.append("식 A = (FD 중 current 열에서 dc_columns 가 reuse/graft/replay 되던 횟수 R_cur) × (dc_columns compute 1회 평균 ms, 전체 평균). 식 B = (current 열의 실제 커널 실행 수 K_cur) × 같은 평균. 둘 다 '그 열들이 전부 compute 로 바뀐다'는 가정.\n")
out.append("| 회로 | R_cur | K_cur | 평균 ms (전체) | A: 추가 s | A/실행 wall | B: 추가 s | B/실행 wall | perf.blocks dc_columns (calls/reuses/computes) 정본 |")
out.append("|" + "---|" * 9)
for c, r in last.items():
    if not r.get("searched"):
        out.append("| %s | %s | | | | | | | |" % (c, r["status"])); continue
    cc = r["fd_rows_by_kind"].get("current", {}).get("dc_columns", {})
    R = cc.get("reuses", 0) + cc.get("grafts", 0) + cc.get("replays", 0)
    K = r["fd_eval_kernel_by_kind"].get("current", 0)
    ms = r["time"]["dc_columns"]["all"]["mean_ms"]
    pb = [x for x in r["perf_blocks"] if x["block"] == "dc_columns"]
    pbs = "%d/%d/%d" % (pb[0]["calls"], pb[0]["reuses"], pb[0]["computes"]) if pb else "-"
    if ms is None:
        out.append("| %s | %d | %d | - (compute 0) | - | - | - | - | %s |" % (c, R, K, pbs)); continue
    A, B = R * ms / 1000, K * ms / 1000
    out.append("| %s | %d | %d | %.1f | %.2f | %s | %.2f | %s | %s |" % (c, R, K, ms, A, pc(A / r["wall_run_s"]), B, pc(B / r["wall_run_s"]), pbs))

out.append("\n## 표 4: 블록 안 반복 회차 추정 입력 (추정: 손가락 규칙 m=ceil(W/w_hi), w_f=W/m, w_hi=기준 슬라이스 W-bin 위 끝)\n")
out.append("| 회로 | input_dc | 입력 포트 | W4 뿌리 입력 포트 | 판정 | front 점 수 / 사용 점 | 슬라이스 바뀌는 쓰기 소자 (점별 바뀜/쓰기수) | 슬라이스 바뀌는 종속 소자 (점별 바뀜/종속수) | 기준 슬라이스 (nmos/pmos w_um, bin) |")
out.append("|" + "---|" * 9)
for c, r in last.items():
    if not r.get("searched"):
        out.append("| %s | %s | %s | %s | %s | - | - | - | - |" % (c, r["status"], r.get("input_dc_mode", "-"), ",".join(r.get("input_ports", [])) + " / " + ",".join(r.get("w4_input_roots", [])) or "-", ("W4 뿌리 " + ("예" if r.get("w4_input_roots") else "아니오") + " (" + r.get("w4_note", "") + ")") if "w4_input_roots" in r else "미판정 (" + r.get("w4_note", "") + ")")); continue
    pw, pd = [], []
    for p in r["points"]:
        w = p["per_role"].get("writer", [0, 0]); d = p["per_role"].get("dependent", [0, 0])
        pw.append("%d/%d" % (w[1], w[0])); pd.append("%d/%d" % (d[1], d[0]))
    rs = r["ref_slices"]
    refs = "; ".join("%s %.2f um [%.2f,%.2f]" % (k, v["w_m"] * 1e6, v["w_bin"][0] * 1e6, v["w_bin"][1] * 1e6) for k, v in rs.items())
    out.append("| %s | %s | %s | %s | %s | %d (%s) / %d | %s | %s | %s |" % (
        c, r["input_dc_mode"], ",".join(r["input_ports"]), ",".join(r["w4_input_roots"]) or "-", "W4 뿌리 " + ("예" if r["w4_input_roots"] else "아니오"),
        r["front_size"], r["point_pool"] + ", cache 봉인 %d" % r["sealed_in_cache"], len(r["points"]), " ".join(pw), " ".join(pd), refs))
Path(D / "summary.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
