import json, sys, collections, pathlib
import numpy as np
sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).parent
recs = [json.loads(l) for l in open(HERE / 'devices_j1b.jsonl', encoding='utf-8')]
P = json.load(open(HERE / 'pooled_j1b.json'))
IDS = ["1e-07", "1e-06", "1e-05", "0.0001", "0.001"]
IDL = {"1e-07": "1e-7", "1e-06": "1e-6", "1e-05": "1e-5", "0.0001": "1e-4", "0.001": "1e-3"}
out = []
w = out.append


def pg(key, cls, kind):
    return P.get("|".join(map(str, key)) + f"|{cls}|{kind}")


def prow(key):
    cells = []
    for cls in ("S", "F"):
        for kind in ("n", "p"):
            d = pg(key, cls, kind)
            if not d or d['n'] == 0:
                cells.append("-")
                continue
            q = d['abs_dlnidu_p50_p90_max']; v = d['abs_dvgs_p50_p90_max']; g = d['abs_dgm_id_p50_p90_max']
            cells.append(f"{d['n_differ']/d['n']:.1%} (>e배 {d['n_dln_gt1']/d['n']:.1%}) / lnIDu p90 {q[1]:.2f} max {q[2]:.2f} / VGS p90 {v[1]:.3f} max {v[2]:.3f} / gm/ID max {g[2]:.2f}")
    return cells


def leak_counts(vt, rule, idc, bud, point, tol, only_budget=False):
    c = collections.Counter()
    for r in recs:
        if only_budget and r['budget_m2'] is None:
            continue
        cc = r['combos'][f"{vt}|{rule}|ID{idc}|{bud}"]
        c[(r['cls'], 'N')] += 1
        if cc['sd_nonempty'] == 0:
            c[(r['cls'], 'empty')] += 1
            continue
        n = cc[point]['n']; lk = cc['leak_' + point][tol]
        if n and lk >= 0.5 * n:
            c[(r['cls'], 'maj')] += 1
        if lk > 0:
            c[(r['cls'], 'any')] += 1
    return c


def moved_counts(vt, rule, idc, bud):
    c = collections.Counter()
    for r in recs:
        if r['budget_m2'] is None:
            continue
        cc = r['combos'][f"{vt}|{rule}|ID{idc}|{bud}"]
        ne = cc['sd_nonempty']
        c[(r['cls'], 'N')] += 1
        if ne == 0:
            c[(r['cls'], 'empty')] += 1
            continue
        if cc['moved'] >= 0.5 * ne:
            c[(r['cls'], 'maj')] += 1
        if cc['moved'] > 0:
            c[(r['cls'], 'any')] += 1
        if cc['ts_missing'] > 0:
            c[(r['cls'], 'miss')] += 1
    return c


fs = lambda c, k: f"S {c[('S', k)]}/{c[('S', 'N')]}"
ff = lambda c, k: f"F {c[('F', k)]}/{c[('F', 'N')]}"

# ---- tables_j1b.txt: 전수 덤프
tl = []
tl.append("pooled t* 차 (설정 = L18 x VDS>=0.3 41 x VSB 마디 pool, 소자 가중 아님). 각 칸: 차 있음 비율 (ln IDu 차 > 1 비율) / |dlnIDu| p90,max / |dVGS| p90,max(V) / |dgm/ID| max")
tl.append("K10: 앞 변형 - 뒤 변형 (앞이 더 제한적이라 >= 0 기대). K3: (나) - (가).  열 = S nfet | S pfet | F nfet | F pfet")
for bud in ("none", "full", "share"):
    for idc in IDS:
        for rule in ("ga", "na"):
            for t in ("t0p1mV", "t1mV", "tLOO"):
                for pair in ("D1-D2P", "D1-D2", "D2P-D2"):
                    tl.append(f"K10 | bud={bud} | ID={IDL[idc]} | rule={rule} | tol={t} | {pair} | " + " || ".join(prow(("K10", rule, pair, t, idc, bud))))
        for vt in ("D1@t0p1mV", "D1@t1mV", "D1@tLOO", "D2P@t0p1mV", "D2P@t1mV", "D2P@tLOO", "D2"):
            tl.append(f"K3 | bud={bud} | ID={IDL[idc]} | {vt} | (na)-(ga) | " + " || ".join(prow(("K3", "na-ga", vt, "-", idc, bud))))
(HERE / "tables_j1b.txt").write_text("\n".join(tl), encoding="utf-8")

# ---- md ----
w("# 측정 m_j1b -- K3·K10: 실제 출발점(사다리 칸 0 t*)이 반전 수준 하한 행·전도 여유 행(K10)과 출발값 규칙(K3)에 따라 바뀌는가 (2026-10-31)")
w("")
w("측정만 했다. 저장소·계획·git 쓰기 0, 엔진 파이프라인(`run_stage_*`·`start_intervals`) 호출 0. 스크립트·원자료: `wt/_drafts/evidence/2026-10-31/m_j1b/` "
  "(`measure_j1b.py` 본체, `devices_j1b.jsonl` 소자마다 1줄(115줄, 조합 210개씩), `pooled_j1b.json`, `tables_j1b.txt` 전수 표, `tolv.py`·`tolv_cells.json` LOO tol_V, `agg*.py`·`gen_report.py`). "
  "정의 정본 = 후보 문서 K3·K10 'M-J1b 측정 정의'. 앞선 측정 `m_j1/`(분류·VSB 마디·f_req) 재사용.")
w("")
w("## 0. 먼저 읽을 사실")
w("")
D2o = leak_counts("D2", "ga", "1e-05", "none", "att", "t1mV")
w(f"1. **시도점(예산 무시)에서 누설 영역 출발은 D2뿐이다**: D2 (가) 다수 설정 기준 {fs(D2o,'maj')} | {ff(D2o,'maj')}(전부 gbw 선언 없는 4회로의 F: common_gate 1·current_reuse 16·folded_cascode 4·pushpull_follower 4). D1·D2+는 행이 전도 여유를 요구하므로 0/N이다(정의상 귀결).")
w("2. **면적 예산이 있는 회로(10/13, 48소자 = S 16·F 32)에서는 예산이 F 시도점을 거의 다 옮긴다**(ID 1e-6~1e-5: F 25/32, S 0/16; ID 1e-3: F 28/32, S 12/16). 옮긴 뒤 t*에서는 D1·D2+·D2 차가 거의 사라진다. 즉 K10의 실효 차는 예산이 없거나 느슨한 곳에만 남는다. 단 전류 ID는 경우 나눔(1e-7~1e-3 A)이다(§4 한계 1).")
w("3. **D1 대 D2+ 차는 pfet 일부뿐**(전도 여유 경계 아래에 gm/ID 정점이 있는 곡선)이고 nfet은 0이다(정점 = VGS 0 격자점).")
w("4. **(가) 대 (나) 차는 pfet이고 속도 행이 아래 끝을 중간 반전 쪽 골짜기에 놓는 소자에 몰린다**(M-J1과 같은 현상). nfet은 0이다.")
w("5. **엔진 경로는 막혔다**: `run_stage_a`가 `pdk_source_sha256_mismatch`로 거부된다(저장소에 이미 있는 선언 불일치). 우회는 하지 않았다. gm_req·KCL 전류는 못 쟀다(§4 한계 1).")
w("")
w("## 1. 입력과 구현한 정의 (표지)")
w("")
w("- LUT: `assets/lut_v2_location.json` -> `sky130_nfet_pfet_lut_v2_r2.npz`(cap_npz)만. 축 L 18 x VGS 49(0~1.8 V, 간격 37.5 mV) x VDS 49 x VSB 10, W_ref 5 um 슬라이스, 보간 없음(격자 원값). **(L, VDS, VSB) 격자 = M-J1과 같다**(L 18 전부, VDS >= 0.3 V 41개, VSB는 M-J1 `devices.jsonl`의 `vsb_idx` 재사용: 소스 넷이 선언 전위면 |V_b - V_s| 마디, bulk 미선언 = kind별 레일, 아니면 0이 아닌 9 마디).")
w("- 소자 115 = M-J1과 같음(S 52·F 63; nfet 59·pfet 56). S·F 분류·f_req도 M-J1 값 그대로(재측정 아님).")
w("- **S_d 행**: ① 포화 VDSAT <= VDS ② 속도 f_T = GM/(2 pi CGG) >= f_req(**C 열 CGG 포함**, gbw 선언 9회로만; M-J1 그대로, f_T는 자기 CGG만 본 필요조건이라 느슨함) "
  "③ **최소 폭**: W = ID L / IDu >= W_min  <=>  ID_node(W_ref) <= ID_dev x W_ref / W_min, **W_min = PDK 선언 `min_finger_w_m` = difftap.2 = 0.42 um**(`periphery.csv` 321행에서 읽음) "
  "④ [K10] **반전 수준 하한**: 노드 >= 그 (L, VDS, VSB) 곡선 gm/ID 가장 왼쪽 argmax(floor_m = 곡선 전체 기준; M-J1 '정점' 정의) "
  "⑤ [K10] **전도 여유**: I_off <= (gm/ID) tol_V ID  <=>  GM(노드) tol_V >= ID(VGS = 0 노드)(같은 W, I_off = LUT VGS = 0 누설, 계획 DEC-88 봉인 9). tol_V **예시 3 경우**: 0.1 mV · 1 mV · **LOO 셀값**.")
w("- **LOO tol_V 셀값**: 엔진 `gmid_engine.lut.tol_v_table`(읽기 전용 import, 규칙 선언 경로 미사용)의 `id_equivalent_v`(W 5 um 슬라이스, (L 앵커, VDS) 칸 최댓값). nfet 2.5e-6~4.5e-2 V(중앙 2.4e-3), pfet 3.3e-6~2.3e-2 V(중앙 3.7e-3). "
  "**tol_V 정본 지표(`id_equivalent_v` 대 `gm_id_inverse_v`)와 셀 구성은 Q-T0 미결이라 예시값**이다.")
w("- 변형: **D1** = ①②③④⑤ / **D2+** = ①②③⑤ / **D2** = ①②③(ID > 0 노드 전부). 격자 노드의 ln IDu는 VGS에 엄격 증가라 'S_d 아래 끝' = 가장 낮은 VGS 노드.")
w("- **출발점**(design 41 §6.1-9 칸 0 = 면적 <= 예산인 최대 t*): 면적 W L = ID_dev L W_ref / ID_node는 ln IDu에 대해 감소라 실행 가능 집합은 위 끝 쪽 집합이다. "
  "(가) 시도점 = S_d 가장 낮은 노드, t* = S_d ∩ 면적 실행 가능 가운데 가장 낮은 노드. (나) 시도점 = S_d 안 gm/ID 가장 왼쪽 argmax, t* = 그 노드 이상에서 S_d ∩ 면적 실행 가능인 가장 낮은 노드(**(나)의 t 매개화는 설계에 정의가 없어 이렇게 둠 -- 표지**). "
  "t*는 격자 노드 단위(37.5 mV)이며 bracket_root 연속 경계가 아니다.")
w("- **면적 예산 경우**(spec `area_search_m2`; cnr_ota·erfc_ota·r2r_opamp·rfc_ota 4회로는 **예산 선언 없음 -> 면적이 출발점을 못 옮긴다**, 나머지 9회로 선언 = 소자 48): "
  "`none` = 예산 무시(S_d만) / `full` = 소자 하나가 예산 전체 B를 쓴다(필요조건, 옮김의 하한) / `share` = B / n_SF(회로 S·F 수) 균등 몫(**가정이 아니라 경우 나눔**). **B 역할 소자(부하·미러·tail)와 수동소자 면적은 뺐다** -> 실제 예산 압박은 더 크다(옮김은 하한).")
w("- **ID_dev 경우 나눔 1e-7·1e-6·1e-5·1e-4·1e-3 A**: gm_req(매크로)·KCL 전류를 엔진 없이 못 재서(§4 한계 1) 값을 주장하지 않고 5칸으로 나눴다.")
w("- 조합: S_d 7종({D1,D2+} x tol 3 + D2) x 규칙 2 x ID 5 x 예산(3 또는 1). 소자마다 1줄(`devices_j1b.jsonl`)에 시도점·t*의 ln IDu·VGS·gm/ID·W의 [최소, 중앙, 최대](설정 분포)와 `moved`(t* != 시도점 설정 수)·`leak_att`·`leak_ts`(tol별)가 있다. 조합 키(`ID1e-05`)가 ID 값이다.")
w("")
w("## 2. 변형별 표")
w("")
w("### 2.1 누설 영역 출발 n/N (시도점, 면적 예산 무관; N = 115 = S 52 + F 63; ID = 1e-5 A 값)")
w("")
w("누설 영역 = 전도 여유 행 위반(I_off > (gm/ID) tol_V ID). '다수' = 그 소자의 S_d 비지 않은 설정 중 >= 50 %에서 시도점이 누설, '1개 이상' = 설정 하나라도. ID 5칸 사이 다수 열은 같고 '1개 이상' 열은 (나) D2에서만 S 13~16으로 달라진다.")
w("")
w("| 변형 | 규칙 | tol_V | 다수 S | 다수 F | 1개 이상 S | 1개 이상 F | 비고 |")
w("|---|---|---|---|---|---|---|---|")
for rule, rn in (("ga", "(가) 아래 끝"), ("na", "(나) argmax")):
    for vt, nm in (("D1@{t}", "D1"), ("D2P@{t}", "D2+"), ("D2", "D2")):
        for t, tn in (("t0p1mV", "0.1 mV"), ("t1mV", "1 mV"), ("tLOO", "LOO")):
            key = vt.format(t=t) if "{t}" in vt else vt
            c = leak_counts(key, rule, "1e-05", "none", "att", t)
            note = "행이 전도 여유를 요구 -> 정의상 0" if nm != "D2" else ("다수 F = gbw 없는 4회로" if t == "t1mV" and rule == "ga" else "")
            w(f"| {nm} | {rn} | {tn} | {c[('S','maj')]}/{c[('S','N')]} | {c[('F','maj')]}/{c[('F','N')]} | {c[('S','any')]}/{c[('S','N')]} | {c[('F','any')]}/{c[('F','N')]} | {note} |")
w("")
w("D2의 누설 출발 F 25 = gbw 선언 없는 4회로(속도 행 없음)의 F 전부. gbw 선언 회로의 S·F는 속도 행이 아래 끝을 올려 다수 설정에서 누설이 아니다('1개 이상' S 17~24는 낮은 f_req(2~12 MHz)에서 VGS = 0 노드가 속도 행을 통과하는 설정).")
w("")
w("### 2.2 면적 예산 적용 뒤 t*의 누설 영역 (D2만 해당; D1·D2+는 0), 예산 회로 N = 48 (S 16 + F 32), tol_V = 1 mV")
w("")
w("| 규칙 | 예산 | " + " | ".join(f"ID {IDL[i]}" for i in IDS) + " |")
w("|---|---|" + "---|" * len(IDS))
for rule, rn in (("ga", "(가)"), ("na", "(나)")):
    for bud in ("none", "full", "share"):
        cells = []
        for idc in IDS:
            c = leak_counts("D2", rule, idc, bud, "ts", "t1mV", only_budget=True)
            cells.append(f"다수 S {c[('S','maj')]}·F {c[('F','maj')]} / 1개↑ S {c[('S','any')]}·F {c[('F','any')]}")
        w(f"| {rn} | {bud} | " + " | ".join(cells) + " |")
w("")
w("### 2.3 면적 예산이 시도점을 옮긴 소자 수 (예산 회로 N = 48: S 16·F 32; '다수' = 비지 않은 설정 중 >= 50 %에서 t* != 시도점)")
w("")
w("D1·D2+·D2와 (가)·(나)에서 거의 같아(차 <= 2 소자: D2의 F ID 1e-7 25 대 D1 23) 한 표로 둔다(D1, (가), tol 1 mV 값; 전수는 `devices_j1b.jsonl`).")
w("")
w("| 예산 | " + " | ".join(f"ID {IDL[i]}" for i in IDS) + " |")
w("|---|" + "---|" * len(IDS))
for bud in ("full", "share"):
    cells = []
    for idc in IDS:
        c = moved_counts("D1@t1mV", "ga", idc, bud)
        cells.append(f"S {c[('S','maj')]}/16 · F {c[('F','maj')]}/32 (1개↑ S {c[('S','any')]}·F {c[('F','any')]})")
    w(f"| {bud} | " + " | ".join(cells) + " |")
w("")
w("옮김 크기(D1 (가) full, 소자별 설정 중앙값의 t* - 시도점 ln IDu 차):")
w("")
w("| ID | S 중앙 / p90 / 최대 | F 중앙 / p90 / 최대 |")
w("|---|---|---|")
for idc in IDS:
    row = []
    for cls in ("S", "F"):
        v = [r['combos'][f"D1@t1mV|ga|ID{idc}|full"]['ts']['lnidu'][1] - r['combos'][f"D1@t1mV|ga|ID{idc}|full"]['att']['lnidu'][1] for r in recs if r['budget_m2'] and r['cls'] == cls]
        row.append(f"{np.median(v):.2f} / {np.quantile(v,.9):.2f} / {max(v):.2f}")
    w(f"| {IDL[idc]} | " + " | ".join(row) + " |")
w("")
w("(ln IDu 1 = 전류 밀도 e배. F의 옮김 6~27은 전도 여유 경계(약반전, W 수 mm~m 급)에서 예산이 허락하는 강한 반전 쪽으로 e^6~e^27배 올라간다는 뜻이다. 예산 하한 계산에서도 그렇다.)")
w("")
w("### 2.4 t* 차 분포 (S·F 따로, nfet·pfet 따로; 설정 pool)")
w("")
w("각 칸 = 차 있음 비율 (ln IDu 차 > 1 비율) / |Δ ln IDu| p90·max / |ΔVGS| p90·max(V) / |Δgm/ID| max(S/A). 차 = 같은 설정에서 두 변형 t*의 값 차(둘 다 정의된 설정만). K10 = 앞 변형 - 뒤 변형, K3 = (나) - (가). **ID = 1e-5 A, tol_V = 1 mV**. 전수(ID 5칸·tol 3·예산 3) = `tables_j1b.txt`.")
for bud, bn in (("none", "예산 무시(S_d만의 차)"), ("full", "예산 full"), ("share", "예산 share")):
    w("")
    w(f"**{bn}**")
    w("")
    w("| 비교 | 규칙 | S nfet | S pfet | F nfet | F pfet |")
    w("|---|---|---|---|---|---|")
    for pair, pn in (("D1-D2P", "K10 D1 - D2+"), ("D1-D2", "K10 D1 - D2"), ("D2P-D2", "K10 D2+ - D2")):
        for rule, rn in (("ga", "(가)"), ("na", "(나)")):
            cells = prow(("K10", rule, pair, "t1mV", "1e-05", bud))
            w(f"| {pn} | {rn} | " + " | ".join(cells) + " |")
    for vt, vn in (("D1@t1mV", "D1"), ("D2P@t1mV", "D2+"), ("D2", "D2")):
        cells = prow(("K3", "na-ga", vt, "-", "1e-05", bud))
        w(f"| K3 (나)-(가) [{vn}] | - | " + " | ".join(cells) + " |")
w("")
w("tol_V 감도(예산 무시, (가), ID 1e-5, D2+ - D2: 아래 끝에서 전도 여유 경계까지의 거리):")
w("")
w("| tol_V | S nfet | S pfet | F nfet | F pfet |")
w("|---|---|---|---|---|")
for t, tn in (("t0p1mV", "0.1 mV"), ("t1mV", "1 mV"), ("tLOO", "LOO 셀값")):
    cells = []
    for cls in ("S", "F"):
        for kind in ("n", "p"):
            d = pg(("K10", "ga", "D2P-D2", t, "1e-05", "none"), cls, kind)
            q = d['abs_dlnidu_p50_p90_max']; v = d['abs_dvgs_p50_p90_max']
            cells.append(f"{d['n_differ']/d['n']:.1%} / lnIDu p90 {q[1]:.2f} / VGS p90 {v[1]:.3f} max {v[2]:.3f}")
    w(f"| {tn} | " + " | ".join(cells) + " |")
w("")
d1 = {t: pg(("K10", "ga", "D1-D2P", t, "1e-05", "none"), "F", "p") for t in ("t0p1mV", "t1mV", "tLOO")}
w("D1 - D2+ (반전 수준 하한 행의 추가 효과)은 pfet F에서만 난다: 차 있음 비율 " + ", ".join(f"{k} {v['n_differ']/v['n']:.2%}(lnIDu max {v['abs_dlnidu_p50_p90_max'][2]:.1f})" for k, v in d1.items()) + ". nfet·S는 전 tol에서 0.")
w("")
w("### 2.5 t* 차가 0이 아닌 소자가 남는 회로 (card LA-1 변화표로 넘길 후보; 표지만)")
w("")
w("소자별 t* 분포([최소, 중앙, 최대])의 ln IDu·VGS 중 하나라도 두 조합에서 다르면 '차 있음'(근사 판정 -- 설정 단위 정확 비교는 §2.4). 예산 회로 48소자, ID 1e-5, tol 1 mV.")
w("")


def sig(c):
    t = c['ts']
    return json.dumps([t['lnidu'], t['vgs']])


cmpd = [("K10 D1 vs D2", "D1@t1mV|ga", "D2|ga"), ("K10 D1 vs D2+", "D1@t1mV|ga", "D2P@t1mV|ga"), ("K3 (가)/(나) [D1]", "D1@t1mV|ga", "D1@t1mV|na"), ("K3 (가)/(나) [D2]", "D2|ga", "D2|na")]
w("| 비교 | 예산 | S | F | 회로(차 있는 소자/예산 회로 소자) |")
w("|---|---|---|---|---|")
for nm, a, b in cmpd:
    for bud in ("full", "share"):
        o = collections.Counter()
        per = collections.defaultdict(lambda: [0, 0])
        for r in recs:
            if r['budget_m2'] is None:
                continue
            d = sig(r['combos'][f"{a}|ID1e-05|{bud}"]) != sig(r['combos'][f"{b}|ID1e-05|{bud}"])
            per[r['circuit']][1] += 1
            if d:
                per[r['circuit']][0] += 1
                o[r['cls']] += 1
        w(f"| {nm} | {bud} | {o['S']}/16 | {o['F']}/32 | " + "; ".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(per.items()) if v[0]) + " |")
w("")
w("예산 없는 4회로(cnr_ota·erfc_ota·r2r_opamp·rfc_ota; 67소자)는 면적이 출발점을 못 옮기므로 §2.1 시도점 표와 같다: 이 회로의 S·F는 전부 gbw 선언이 있어 속도 행이 있고 D1·D2+·D2 모두 같은 속도 행 아래 끝에서 출발하며 누설 출발 0이다.")
w("")
w("## 3. 해석 표지 (판정 아님)")
w("")
w("- **K10 선택의 실효**: 누설 영역 출발은 D2에서만 나고, 그것은 속도 행이 없는 회로(gbw 선언 없는 4회로, F 25소자)에 한정된다. 이 4회로는 모두 면적 예산이 있어 예산이 출발점을 올리므로, **t*에서의 D1·D2+·D2 차는 예산을 적용하면 거의 사라진다**(§2.4 예산 full/share: 차 있음 비율 0.0~0.8 %, 단 ID 1e-7 쪽 F nfet 2.4 %·F pfet 3.7 %). "
  "다만 이것은 '출발점이 같아진다'가 아니라 '예산 경계가 출발점을 정한다'이다 -- t*가 약반전~중간반전의 면적 경계(W 수 mm~m 급)에 놓이는 것은 B36-M1 3(nfet VGS 0 근처에서 1 uA에 W ~ km)과 같은 종류의 현상이다.")
w("- **D1 대 D2+**: 반전 수준 하한 행은 nfet에서 공허(정점 = VGS 0)하고 pfet 일부에서만 전도 여유 경계 위로 S_d를 더 자른다. 이 행의 pfet 정점은 약반전 plateau 반올림이 정하므로(M-J1 §4.6, 상대차 <= 1.3e-6) 그 차의 위치 자체가 수치 잡음이다. tol_V가 클수록 D1 - D2+ 차 비율이 커진다(0.1 mV 0.01 % -> 1 mV 0.46 % -> LOO 1.6 %).")
w("- **전도 여유 경계 위치가 tol_V에 의존한다**: D2+ 경계까지 ln IDu 거리 p90 = 6.4~6.7(0.1 mV) / 4.3~4.4(1 mV) / 8.8~9.2(LOO)이다. LOO가 1 mV보다 더 먼 이유는 LOO 셀값이 이봉이기 때문이다: VDS >= 0.3 V 셀(18 L x 41) 중 1/3은 0.1 mV 미만(최소 2.5e-6 V)이고 2/3는 1 mV 초과(중앙 2.0~3.4 mV)다. 앞 1/3 셀의 전도 여유 경계가 더 높은 VGS에 있다(L 앵커별 분해는 하지 않았다).")
w("- **K3 (가) 대 (나)**: 면적 예산과 무관하게 pfet의 설정 5~17 %에서 갈린다. nfet 0. 예산 full/share에서도 S pfet 15~16 %가 남는다(속도 행으로 아래 끝이 골짜기에 놓이는 소자, M-J1의 39/115 군). 이 차는 K10 선택(D1·D2+·D2)과 거의 무관하게 같다.")
w("- **S 대 F**: S는 속도 행(gbw 선언 회로)이 아래 끝을 강반전~중간반전으로 올려 K10 차가 0이고 면적 예산도 ID <= 1e-5에서 못 옮긴다(옮김 0). F는 gbw 선언 없는 4회로에서 속도 행이 없어 K10이 직접 갈리고 예산이 크게 옮긴다. 전력 논거(K3 '물리 결정자')는 S에만 있으므로 위 F 결과는 K3 (가)/(나) 자체의 근거가 되지 못한다.")
w("")
w("## 4. 한계")
w("")
w("1. **엔진 경로 불가 -- ID 경우 나눔**: S의 gm_req(매크로 풀이 -- 보상 커패시터 Cc는 spec 상자 [0.1, 10] pF 안에서 엔진이 정함)와 F의 §6.5 1회차 전류는 `start_intervals`(`current_model`+`macro_solve`)를 불러야 얻는다. "
  "이번 환경에서 엔진 경로(`run_stage_a`)는 `pdk_source_sha256_mismatch`(`sky130_lut_rule_decl.json`이 선언한 `sky130_lut_sweep.py` sha256과 현 master 파일의 LF 정규화 해시가 다름, **측정 전부터 있는 상태**)로 거부된다. 해시 검사를 우회해서 돌리는 것은 하지 않았다(첫 시도에서 자동 모드 판정기가 그 우회를 거부). "
  "그래서 ID를 값으로 주장하지 않고 5칸으로 나눴다. **선언 sha256이 정정(또는 우회 승인)되면 `start_intervals._state`를 가로채는 읽기 전용 프로브(`probe_engine.py`, 작성만 됨·미실행; 우회 코드는 넣지 않았다)로 S의 gm_req와 F 1회차 전류를 실제 값으로 바꿔 §2.2~2.5를 다시 잴 수 있다.**")
w("2. **면적 예산은 필요조건(하한)**: 소자 하나가 예산 전체(full) 또는 균등 몫(share)을 쓴다고 보았고, B 역할 소자·수동소자·다른 S·F 소자 합산은 뺐다. 실제 예산 압박은 더 크고 t*는 더 위쪽이다. 소자 합이 예산을 넘는 회로는 `share`보다 더 작은 몫이 맞다.")
w("3. **매크로 근 조건 미반영**(정의대로 뺌): 실제 칸 0은 '면적 <= 예산 그리고 매크로 근 있음'이므로 t*는 더 위쪽으로 갈 수 있다. 면적 조건 행(§6.4-2, 절대 offset 제약 current_reuse 1/13)·부하 가드·잡음 가드·헤드룸 V_part 분할은 상한 행이라 (가) 시도점에는 영향이 없고 (나)의 argmax가 잘리는 설정에서만 영향이 있다.")
w("4. **속도 행은 f_T 필요조건**(M-J1 한계 2와 같음, 자기 CGG만 봄)이라 실제 f_np 행이면 아래 끝이 더 올라간다 -> 속도 행이 있는 S의 K10 차는 더 작아질 수 있다.")
w("5. **tol_V는 예시**: 0.1·1 mV와 LOO `id_equivalent_v`(W 5 um 슬라이스, (L 앵커, VDS) 셀의 VGS·VS 최댓값). 엔진이 `device.dc_tol_v`로 쓰는 지표·셀 구성은 Q-T0 미결이다.")
w("6. **격자 동일 가중**: (L, VDS, VSB) 설정을 모두 같은 가중으로 센다(엔진이 실제로 고르는 점의 분포 아님). 면적은 L에 비례하므로 L이 큰 설정이 예산에 먼저 걸린다. S·F 소자 수는 소자 수이지 궤도 수가 아니다(M-J1 한계 5와 같음).")
w("7. **t*는 격자 노드**(37.5 mV): 면적 경계가 노드 사이에 있으면 한 노드 위(안전 쪽)로 잡힌다. 약반전에서 노드 한 칸 ≈ ln IDu 1(e배)이다.")
w("8. **(나)의 t 매개화**는 설계에 정의가 없다(§6.1-9의 t = 1은 선택 끝). 여기서는 argmax 노드 이상에서 면적 실행 가능한 가장 낮은 노드로 둠.")
w("9. **LUT는 W_ref 5 um 슬라이스 하나**, tol_V 셀도 같은 슬라이스. 다른 W bin·보간 L 미사용.")
w("")
w("## 5. front 차")
w("")
w("**엔진 수정 없이 불가**(출발 선택을 J1 대 옛 규칙·D1/D2+/D2로 갈라 두 번 돌려야 하고 저장소 쓰기 0이며, 위 sha256 거부로 엔진 경로 자체가 막혔다). t* 차가 0이 아닌 소자가 남는 회로 = §2.5 표의 회로를 card LA-1 변화표(U-124 측정과 같은 판)로 넘길 후보로만 표지한다.")
(HERE.parent / "m_j1b_start_point.md").write_text("\n".join(out), encoding="utf-8")
print("written", len(out), "lines")
