---
title: headroom-chain -- 계획 이력
plan: headroom-chain.plan.md
date: 2026-10-16
---

# headroom-chain 계획 이력

계획 본문은 [headroom-chain.plan.md](headroom-chain.plan.md)다. 이 문서에는 경위, 측정 근거, 버전 이력만 둔다.

## H1. 결정 경위

### 2026-10-16 current_reuse 층 0 실패 조사

* 사용자 결정 S-14·O-5의 F-1 (a)에서 파일럿(`current_reuse_telescopic_ota`)의 층 0 실패(front 0, `start_no_root_in_window+probe_eval_budget`)를 별도 엔진 조사 card로 뺐다(`wt/_drafts/user_decisions.md` 610행).
* 읽기 전용 조사(원자료 `wt/_scratch_m2`)가 40점 모두 봉인 7 `no_root_in_window`(1변수 노드 풀이)임을 확인했다. 실패 노드는 공통 source 노드(33점), class-AB 출력 gate 두 곳(4점·1점), CMFB tail(2점)이다. 가설 H-A(SCC 안 GS 비엄격 투영), H-B(VDS = VGS 차 부등식 위반)를 세웠다(`wt/_drafts/engine/U17_FOLLOWUPS.md` 52-55행).
* 회로 해석(`wt/_scratch_cr_layer0/interpretation.md`)은 연결과 원문만으로 했다(topology 메타데이터를 근거로 쓰지 않음, 사용자 2026-10-16 지시). 결론: 공통 source 기준 cascode gate 레벨 시프터, class-AB translinear 루프 2개, diode 2단 분압 CMFB 기준. 제안 R-1(VGS 루프 결합 규칙 (a) 등식·(b) 부등식), R-2(Halton 스크램블, 부차), R-3(바이어스 셀 포화 요구 여부, 사용자 질문).

### 2026-10-16 사용자 결정 C-1

"I-1~I-3 승인, R-1·SP-2·CI-15 권고대로"(`user_decisions.md` 613행). 해석 승인, R-1 승인(순서 측정 → (b) → (a), 새 기능 계획부터), SP-2 `{"engine": true}`, CI-15 `{}`. R-3은 대기.

### 2026-10-16 측정 M-1~M-9와 사용자 결정 C-2

* 측정(H2)이 H-B를 확정했고 (a) 등식 루프는 이미 쓰기 계획의 `cycle_vgs` 종속으로 처리됨을 보였다.
* 사용자 결정 C-2 "R-1′, skill 문서 모두 권고대로"(`user_decisions.md` 615행): R-1′(사슬 일반화), (a) 범위 제외, R-3 (나)(연결로 정의한 의도된 triode), M63 L 결정 경로 조사를 계획 근거 측정에 포함, 입력 CM 상하한 비겹침 위험(확신도 중간), 새 기능 계획부터, skill 문서 신설.

### 2026-10-16 계획 v0.1 작성 방침

* 형식은 같은 폴더의 offset-strategy·oracle-portability 계획을 따랐다(N 절, 원래 취지와 다름 표, 결정 표, card, 완료 조건).
* 엔진 사실은 worktree `wt/headroom-chain-plan`(base `083b103`)에서 직접 읽어 `파일:줄`로 적었다. 설계서 문장을 옮기지 않았다.
* 오케스트레이터 추가 지시(작성 중): R-3 탐지는 새 탐지기 대신 기존 정본(`composite_diodes` -- dc_role rule 1c, `gvgs_cycles`, `loop_classify`, `matching_groups` 중 해당하는 것)을 재사용하는 것을 기본안으로 하고 같은 집합인지 card 0에서 잴 것, R-1′ 사슬 탐지도 graph 기존 정본(stack/series 관련)을 먼저 찾아 재사용 여부를 적을 것, 옛 analog-grammar idiom `m_diode_cascode`는 근거로 쓰지 말 것. 반영: 계획 N3.4(사슬 = `gvgs_summary.vds_saturation` 일반화, 가지·기둥은 segment 단위라 재사용 불가 이유, R-3 = dc_role·gs_groups·vds_saturation 파생 우선), N6 M-H3, N3.4 끝 문단.
* grep 결과(base `083b103`): graph에서 직렬·적층 관련 정본은 `graph/branches.py`(DC 가지), `graph/columns.py`(기둥), `graph/coupling_vars.py`(K3 `stacked_vsb` 결합 변수), `graph/gvgs_cycles.py`(VDS-1)다. `loop_classify`는 신호 루프 분류이고 복합 diode 묶음을 입력으로 받기만 한다(`E/graph/loop_classify.py`, `E/graph/view_analysis.py:130`). `matching_groups`는 매칭 묶음이다. 사슬 정의(Gs 성분에 끝 넷이 있음)를 담을 수 있는 것은 VGS 변을 보는 `gvgs_cycles`뿐이었다.

## H2. 측정 근거

모두 `wt/_scratch_cr_m/results/`(2026-10-16 16:28~16:41). 진단 스크립트는 엔진 코드를 바꾸지 않고 프로세스 안 계측만 했다(`scripts/diag.py:1-3`). **spec은 library 원본(083b103)이고 C-1의 SP-2·CI-15 결정은 반영되지 않은 상태였다**(각 줄의 `_spec_note`). 입력 포트 DC는 측정 θ에서 0.9 V였다(m4 pins).

| 측정 | 내용 | 결과 요지 | 원자료 |
|---|---|---|---|
| M-1 | 기록된 실패 θ 한 점(seq 4) 재실행과 SCC 사건 기록 | 같은 실패가 재현된다(공통 source 노드, 창 [0, −0.0375] -- 빈 창). 그 노드는 4넷 SCC(공통 source, cascode gate, 적층 중간 넷, cascode source)에 있다. GS 비엄격 단계에서 cascode source 넷이 창 끝 0 V로, 공통 source가 −0.01875 V(VS 축 하한 아래)로 투영된다 | `m1.jsonl`, `m1_events_readable.txt` 13-34행 |
| M-2 | 실패 θ 13점의 레벨 시프터·cascode·적층 diode·입력 소자 ln IDu, L, VGS 차 | 13점 모두 ln IDu(시프터) = ln IDu(적층 diode)이고 L도 둘이 같다(0.15 µm). 그래서 VGS(시프터) − VGS(diode) = 0, 즉 시프터 VDS = 0. VGS(시프터) − VGS(cascode)는 −0.22 ~ −0.90 V로 모두 음수, 필요값(VDsat + tol_VDsat)은 +0.06 ~ +0.85 V -- 부등식 위반 | `m2.jsonl` |
| M-3 | 출발 구간 행 | 시프터·적층 diode: L 출처 = LUT L 칸 하한(활성 L 하한 없음: 이득 L `u9_value_not_certified`, 속도 `gbw_target_missing` 등), gm/ID 하한 출처 = `w_min_gm_id`(22.48, 약반전 쪽). 입력 소자만 matching L 하한(3.22 µm). cascode도 L 칸 하한 | `m3.jsonl` |
| M-4 | seq 4에서 시프터 ln IDu만 상자 전 구간 훑기(62점) | 모든 점에서 실패(공통 source 노드 또는 LUT 조회) | `m4.jsonl` |
| M-4b | seq 8·13에서 시프터 ln IDu 훑기(81점씩) | 상자 하한 쪽은 `vgs_of_coordinate` `lut_target_out_of_range`(상자 하한이 그 VDS의 LUT 강반전 분지 하한보다 낮음), 그다음 공통 source 노드 실패, 중간에 음수 VDS `tol_v` 조회 실패, ln IDu(시프터) − ln IDu(cascode) ≈ +1.3 부근에서야 공통 source SCC를 지나 PMOS 쪽 공통 source 노드에서 실패, 더 올리면 cascode source 노드 실패, 그 위는 다시 LUT 조회 실패. 통과(ok) 0 | `m4b.jsonl` |
| M-4c | 시프터를 SCC 통과 값(−11.1, −11.0)에 고정하고 PMOS 쪽 시프터 ln IDu 훑기 | 324점 모두 PMOS 쪽 공통 source 노드 `no_root_in_window`(창 하한은 VDS 축, 창 양끝 h가 모두 음수). 입력 DC 0.9 V에서 PMOS 입력쌍 쪽이 풀리지 않는다 -- 입력 CM 상하한 비겹침 위험의 근거 | `m4c.jsonl` |
| M-5 | 실패에서 멈추지 않고 한 θ의 실패 노드 전부 모으기(seq 1~7) | 한 θ에 실패 노드가 최대 13개 함께 나온다(class-AB 출력 gate 둘, NMOS·PMOS 쪽 공통 source·cascode source·적층 넷, CMFB tail). 마지막은 음수 VDS(−0.032, −0.019 V)의 `tol_v` 조회 실패 | `m5.jsonl` |
| M-6 | seq 1에서 ln IDu 좌표 하나씩 바꿔 첫 실패를 뒤로 미는 탐욕 탐색 | 첫 걸음에서 막힘(CMFB tail) -- 좌표 하나로는 못 푼다(결합) | `m6.jsonl` |
| M-7 | seq 1에서 CMFB 분압 diode·기준 입력 소자 ln IDu 훑기 | 통과 0(CMFB tail·분압 노드·LUT 조회 실패) | `m7.jsonl` |
| M-8 | 분압 diode 고정 + 시프터 훑기 | 통과 0(공통 source 노드 48, LUT 조회 12, Newton 시작점 정의역 밖 1) | `m8.jsonl` |
| M-9 | 분압 diode 고정 + 시프터 네 값 | 통과 0(음수 VDS `tol_v` 조회 3, Newton 시작점 정의역 밖 1) | `m9.jsonl` |
| coord | 좌표 역할 덤프(seq 4) | MOS 51개: `tree` 29, `parallel_vgs` 15, `cycle_vgs` 7(M15·M16·M1b·M25·M26·M39·M4b). 시프터·적층 diode·cascode·입력 소자는 모두 쓰기 소자(`tree`) -- C-2의 '(a)는 이미 있음' 근거 | `coord.jsonl` |

해석(계획에 쓰는 결론):
* H-B 확정: 공통 source 노드 실패는 VDS(입력) = VGS(시프터) − VGS(cascode) ≥ VDsat + tol 위반이다(M-2, M-4b). 길이 1 사슬 부등식이다.
* 같은 전류·같은 L·같은 최소 폭 하한이 시프터와 적층 diode의 ln IDu를 같게 만들어 시프터 VDS가 0이 된다(M-2, M-3). 원문은 시프터 L이 7배 길고 밀도비가 6.1배다(해석 문서 Q1 표). 그래서 L 결정 경로 조사(card 0 M-H1)와 R-3 정의역 하한(계획 N3.3-2)이 필요하다.
* 한 θ에 여러 실패가 함께 있어(M-5) 한 좌표 수리로는 안 된다(M-6). 출발에서 사슬 부등식을 함께 맞춰야 한다.
* 입력 DC 0.9 V에서 PMOS 쪽이 풀리지 않는다(M-4c). 입력 DC가 엔진 변수가 되면(SP-2) 사슬 두 쪽이 y의 하한과 상한을 따로 줄 것으로 보고, 비겹침은 남을 수 있다(C-2 확신도 중간).
* 부수 관측: VS 축 밖 투영(M-1), 음수 VDS `tol_v` 조회(M-4b·M-5·M-9, search CONTRACT r5c 표 'tol_V VDS 축 밖 31'과 같은 결), 상자 하한 < LUT 분지 하한(M-4b). 모두 사슬 부등식을 어긴 θ에서 관측됐다.

### 계획 작성 중 추가 읽기(2026-10-16, base `083b103`)

* `gvgs_summary.vds_saturation`의 엔진 안 소비자는 0이었다(grep: graph 블록 정의와 `E/tests/graph/test_gvgs_cycles.py`, `E/tests/generality/test_metamorphic_s1.py`뿐).
* 오라클은 `intended_region`·`linear_devices`를 참조하지 않는다(grep 0, `O/`). 선언 triode 소자도 SPICE 포화 판정에 들어간다.
* `start_values.py:37`의 `SRC_W_MIN` 주석('gm/ID 상한(IDu 하한)')과 실제 쓰임(M-3: side `lo`, `start_intervals.py:156-168` 'g 를 올린다')의 방향이 다르다. 결함 판정은 하지 않고 card 0 M-H1 확인 항목으로 넣었다.

## Version History

| 판 | 날짜 | 내용 |
|---|---|---|
| 0.1 | 2026-10-16 | 초안. C-1·C-2, 측정 M-1~M-9·coord, 해석, 백로그를 근거로 작성. 독립 검증·사용자 승인 전 |
