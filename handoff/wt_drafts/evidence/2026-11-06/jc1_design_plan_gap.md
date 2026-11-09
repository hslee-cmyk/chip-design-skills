gaps: 8 (빠짐 3 / 다름 4 / 넓음 1)

# JC-1 design ↔ 계획 gap 분석

- 분석자: gap 분석 agent(design 작성자·design 검증자와 다름). 읽기·grep·`git -C show/diff/log/grep`만 했다. test·ngspice는 돌리지 않았다.
- 대상: worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261106-jc1-card`, 브랜치 `design/jc1`, 커밋 `14ed24a3`(design 40·41·42·history, `git diff f1dd8f52 14ed24a3`).
- 계획 정본(같은 worktree `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, v6.38.27): N6.42 `:2683-2702`(근거 :2685, LA-1 차단 :2687, 임시 규칙 :2689, graph 규칙 :2691, 범위 1~5 :2694-2698, 완료 :2700, 순서 :2702), DEC-91 `:291`, N6.1 행 `:1325`·`:1392`. 결정 O-247·O-248·O-249 = `wt/_drafts/user_decisions.md:1228-1230`.
- 병렬 계획: `wt/20261106-plan-v63828`, 머리 `c3129a4a`(v6.38.28, DEC-107 = O-249).
- 아래에서 줄 번호 접두는 이렇게 쓴다. P = 계획, D40·D41·D42 = design 40·41·42(`14ed24a3` 기준), E = `skills/analog-gmid-design/gmid_engine`(base `f1dd8f52`).

## 1. 요구 항목 대조표

| # | 항목 | 계획 문언 | design 자리 | 판정 | 근거 |
|---|---|---|---|---|---|
| 1 | 접합 식 Cdb = (CDD−CGD)_off·r, Csb = (CSS−CGS)_off·r | P:2694 범위 1, P:291 DEC-91 (2) | D40:1355 정의, D40:1365 (i) 1~5 | 담김 | `caps(memo,kind,L,vgs_min,vds,vsb,w_ref)`는 `E/lut/cap_query.py:24-52`에 실재한다. CDD·CSS 열은 `Caps.cdd/css`로 온다. memo 키에 W가 있지만 w_ref 고정이라 소자 폭과 무관하다(:52). |
| 2 | off 점 VGS = LUT VGS 축 최소 격자점(상수 0) | P:2694, P:291 | D40:1365 (i) 1 `min(table.grids[1])`, D40:1356 | 담김 | `AXES`가 (L, VGS, VDS, VS)이므로 grids[1]은 VGS다(`cap_query.py:30`). 두 kind 모두 축 끝이 0 V다(`combo5_offregion_junction.md:12`). |
| 3 | (L, VDS, VSB) = 그 소자 봉인점 값 | P:2694 | D40:1365 (i) 2, (ii) | 담김 | 켜진 점 `caps` 조회와 같은 인자를 쓴다(`E/metrics/ss_linearize.py:77-79`). |
| 4 | r = 단일 확산 양의 비(양 = design 40) | P:2694, P:291 | D40:1357(면적 AD·AS), (i) 4 | 담김 | 면적 비를 골랐다. 생성 규칙의 pd = w + pd_extra는 폭에 비례하지 않아 면적만 O-247 동치를 만족한다(`E/metrics/junction_cap.py:108-115`). 배치 기하 `ly.diffusion`은 finger 평균에 m = n_fingers를 곱하는 꼴이라(`E/layout/diffusion.py:17-18`, `E/convergence/realized_geometry.py:22`) ad·m = 총 면적이 맞다. |
| 5 | **레이아웃 전 r = W/w_ref 동치 확인** | P:2694 '동치 확인 포함', P:2700 (1) 'r = W/w_ref', P:291 '소자 폭 비 W/w_ref … 아니면 멈추고 보고', O-247 '접합(과 C 열)은 기준 폭 LUT 값을 소자 폭으로 비례' | D40:1372 | **다름 → G1** | 비례 동치(ad ∝ w_f) 확인은 담겼다. 그러나 design은 W = `dc_finger` m·w_f로 정했고, 탐색 평가에서는 r = (1+residual)·`DeviceOp.W`/w_ref가 된다(D40:1202). 계획은 W를 정의하지 않았다. 한 평가 안에서 C 열 스탬프(cgg·cgd·cgs·cgb)는 `op.W`로 비례하고(`ss_linearize.py:79`) 접합은 m·w_f로 비례한다. 같은 소자가 두 폭을 쓰는 셈이다. 계획 완료 (1) 'r = W/w_ref'를 `DeviceOp.W`로 읽으면 toy가 갈린다. |
| 6 | 레이아웃 뒤 배치 소자 r = `ly.diffusion` 같은 양의 비 | P:291 LAJ (다), P:2700 (1) | D40:1357, (ii), LY8 D40:1394, D41:1038 | 담김 | 기하를 읽는 자리 둘(배치 확산 / `dc_finger`)은 그대로다. |
| 7 | `off` 소자도 같은 규칙 | P:2694 | D40:1356·1371 (ii)(점 = `off_op`, 기하 = (선언 W, 1)) | 담김 | `ss_linearize.py:112-115`의 off 경로가 같은 `_linearize`를 지난다. |
| 8 | 오염 구간·좁은 finger에 경계·보정 0, 새 상수 0 | P:2694, P:2700 (3) | D40:1365 (i) 5 '분기·문턱·클램프 0', D40:1359 | 담김 | 상수 0의 검사 방법은 #27·G4에서 따로 본다. |
| 9 | 삭제: BSIM4 식 `junction_caps`·`JunctionParams`·온도·전위 식 | P:2695 | D40:1374 (iv) `junction_cap.py` :1-19·23·26·37-88·119-124·127-148·150-171 | 담김 | `JunctionCaps`도 지운다. 소비자가 0이 되기 때문이다(범위 4 규칙). |
| 10 | 삭제: PDK 접합 54키(tnom 2키 제외 52) | P:2695 + P:2696 | D40:1374 (iv) '52키', :5 note 정정 | 담김 | 실측 결과 `junction_*` 키 54개, 그 가운데 tnom 2개다(`assets/sky130_pdk_decl.json`). |
| 11 | 삭제: 그 로더 | P:2695 | D40:1374 `JunctionParams.from_pdk_decl`(:37-88 안), `search_context.py:178` `pdk_decl` 인자 | 담김 | core `E/core/*.py`에는 접합 전용 로더가 없다(`junction` grep 0). |
| 12 | 삭제: 계약 문언(core CONTRACT PDK 선언 절) | P:2695 | D40:1374 core CONTRACT :340-342·:450-469·:537-539 | 담김(일부 빠짐 → G8) | `junction` grep 밖에서 한글 '접합'만 쓴 줄이 남는다. 근거는 G8. |
| 13 | 삭제: `JunctionSource` 파라미터 운반(`params`·`params_of`·`from_pdk_decl`·sha256 지문 성분), `junction_field`의 `pdk_decl` 입력 | P:2695 | D40:426, D40:1373 (iii), D40:1374 (iv) | 담김 | 지금 코드는 `E/metrics/junction_source.py:19-40`, `junction_field.py:18-19`다. 새 extras는 `(lut_rule_decl, lut)`다. |
| 14 | 삭제: `junction_model` 값 `pdk_bsim4_*` 둘을 새 이름 둘로 1:1 | P:2695 | D40:1360 `lut_vgs_min_rule_area`·`lut_vgs_min_layout_area` | 담김(as-built 표지 A2) | 이름에서 'pdk'·'bsim4'·'off'를 뺐다(O-197·O-249). 상수 식별자 유지의 근거 일부가 '소비자 이동 0'이다. |
| 15 | 삭제: metrics CONTRACT 8절 | P:2695 | D40:1374 :825-913을 (i) 정의 절로 교체 | 담김 | 새 함수가 같은 파일에 있으므로 교체(재배선 문언)가 맞다. |
| 16 | 같은 변경에서 삭제(O-153) | P:2695 | D40:1374 '같은 변경' | 담김 | |
| 17 | 유지: 봉인 6·`ss_off_op` `junction_forward` | P:2696 | D40:1375 ① | 담김 | |
| 18 | 유지: MOD8 `junction_change` | P:2696 | D40:1375 ② | 담김 | |
| 19 | 유지: `ly.diffusion`·`DiffusionGeometry`·`lut_diffusion_*`(파일 자리 = design) | P:2696 | D40:1375 ③, D40:1362 파일 = `junction_cap.py` 유지 | 담김 | 파일 자리를 유지한 근거는 '파일당 진입점 하나'라는 규칙이다. as-built가 근거는 아니다. |
| 20 | 유지: 측정 온도 칸(잡음 kT) | P:2696 | D40:1375 ④, (iii) `temp_c` = `cap_conditions["temp_c"]` | 담김 | 온도는 지금도 LUT에서 읽는다(`junction_source.py:31-35`). 이 칸은 PDK tnom과 무관하다. |
| 21 | 유지: tnom 2키는 oracle 소비. 엔진 분류는 '엔진 소비자 0, oracle 소비자 있음'. 이동·삭제는 oracle-portability 개정 뒤(원래 취지와 다름(시점)) | P:2696 | D40:1375 ⑤ | 담김 | oracle 소비 자리는 `tools/spice_oracle/descriptors/sky130.oracle_descriptor.json:151·154` 둘뿐이다. 엔진 .py의 tnom 읽기는 `JunctionParams`뿐이다(`.py`에서 `tnom` grep 0). |
| 22 | 재배선: 층 0 기생 고정점 | P:2697 | D40:1376 (vi)(as-built 자리 0 → LA-1), D41:1251 '같은 함수' | 담김 | `node_c_farad` 계산이 엔진 .py에 없다(실측: `E/metrics/ls_fields.py:8` 설명 한 줄뿐). 함수 `junction_at_vgs_min`을 두는 이유는 LA-1에서 둘째 식이 생기지 않게 하려는 것이다. 지금 소비자는 `ss_dev`라 배선 원칙에 맞는다. |
| 23 | 재배선: GB5 `C_out,total` | P:2697, P:291 (4) | D40:1376 (vi) | 담김 | as-built 자리가 0이다(`C_out`·`c_out_total` .py grep 0). |
| 24 | 재배선: 전회로 MNA·잡음 | P:2697 | D40:1376 (vi) `ss_circuit`·`stamp_mos`·`metrics_aux`·`ss_metrics`·MOD8 | 담김 | 옛 출처 직접 호출은 `ss_linearize.py:80-81`과 `junction_field.py:19` 두 곳뿐이다. 실측과 맞다. |
| 25 | 소비자 0이 되는 함수·칸 삭제 | P:2697 | D40:1376 끝 | 담김 | 관찰 O-1 참고: CGS 열이 없을 때 정지하는 규칙 때문에 `ss_dev`의 `cap_model` 값 `cgg_minus_cgd_at_gs`가 도달 불가가 된다. `caps`의 다른 호출자(`lut/ft_curve.py:24`, `search/iv_currents.py:107`)는 그 경로를 그대로 쓴다. |
| 26 | 분류 표 기준(`junction` grep 전수: 엔진·계약·PDK·oracle·test, 삭제/유지(근거)/재배선, test는 `retired_tests`) | P:2698 | D40:1377 (vii) | 담김(범위 밖 표지 일부 빠짐 → G8) | `references/design-report-spec.md`·`references/sky130-worked-example.md`에 `junction` 줄이 있는데 grep 대상에도 범위 밖 표지에도 없다. |
| 27 | 완료 (1) 정의 toy 두 경우 + base red, 피검 함수로 만들지 않음 | P:2700 (1) | D40:1378 (viii)(1) a·b·c·d | 담김(G1 종속) | 이진 유한 소수를 써서 허용오차 상수가 0이다. (a)는 'r_d == m·w_f/w_ref'로 단언한다. 계획 'r = W/w_ref'의 W 정의(G1)에 달려 있다. |
| 28 | 완료 (2) 수동성 | P:2700 (2) | (viii)(2) | 담김 | |
| 29 | 완료 (3) 상수 0(`git grep` + **리터럴 lint**) | P:2700 (3) | (viii)(3) '판정자가 diff에서 확인 -- 새 lint 도구 0' | **다름 → G4** | 기존 리터럴 lint가 있다(`E/tests/structure/README.md:47` 규칙 D, `structure_checks.py`). |
| 30 | 완료 (4) O-197(BSIM4 이름·식 grep 0, PDK 접합 키 = oracle 소비 키만) | P:2700 (4) | (viii)(4) 정규식, 키 집합 == tnom 2키 | 담김 | |
| 31 | 완료 (5) 분류 표 대조 | P:2700 (5) | (viii)(5) | 담김 | |
| 32 | 완료 (6) graph(writer `ss_dev` 하나, 새 cache·사본 0, G-10 memo 적중) | P:2700 (6) | (viii)(6) | 담김 | |
| 33 | 완료 (7) 변화표, 좁은 finger 감소 방향, 오염 구간 소자 수와 L | P:2700 (7) | (viii)(7) | 담김 | |
| 34 | 완료 (8) O-229 2 test 범위 + 회로 이름 0 + fail-closed(VGS 축·C 열·`w_ref_m` 없음 → 분류된 정지) | P:2700 (8) | (viii)(8) toy 셋(CDD 없음·CGS 없음·AD_ref = 0), D40:1359 사유 확정 | **빠짐 → G6, 다름 → G7** | CSS 열 없음 toy가 없다. VGS 축·`w_ref_m` 결손은 기존 적재 관문을 인용만 했다. S0 정지가 bare `ValueError`다. |
| 35 | 완료 (9) 작성자 ≠ 판정자 | P:2700 (9) | (viii)(9) | 담김 | |
| 36 | 완료 머리 '결정성 비트 동일' | P:2700 머리 | 없음 | **빠짐 → G5** | (viii)에 결정성 항목이 없다. |
| 37 | graph: writer `ss_dev` 하나, 새 필드 0 | P:2691 | D40:1355, (ii) | 담김 | |
| 38 | graph: 새 cache·memo·sctx·파생표·사본 0, 1-D 접합 표 금지 | P:2691 | (i) 2(기존 `caps` memo point 영역), (vi) '새 소비자 0' | 담김 | 표를 따로 만들지 않고 점마다 조회한다. |
| 39 | graph: S0 비례 기준 필드 하나(칸 정리 = design) | P:2691 | D40:426, D40:470, (iii) `JunctionSource(lut_rule_decl, reference, temp_c)` | 담김 | 필드·writer 이름은 그대로라 소유표 행 변경이 0이다. |
| 40 | graph: 기하 자리 둘 그대로 | P:2691 | (ii) | 담김 | |
| 41 | graph: 정의 축 기록(출발 단계 CDD 열 계수 대 MNA Cgd + Cdb(off)) | P:2691 | D40:1361, (ix) | 담김 | |
| 42 | DEC-91 (2) LUT DC 열 = W-bin 슬라이스, 용량 열 = 기준 폭 표 | P:291 | (i) 1 `cap_map[kind]` | 담김 | |
| 43 | DEC-91 (2) 대칭 5칸, 비상호 성분 버림 | P:291 | D40:1355 | 담김 | |
| 44 | DEC-91 (2) 오라클 넷리스트 ad/as/pd/ps 그대로(LY8) | P:291 | D40:1394, D41:1038 | 담김 | |
| 45 | DEC-91 (2) 이식성 한계: 면적이 폭에 비례하지 않는 PDK는 fail-closed | P:291 | D40:1372 '선언 꼴로 적을 수 없어 `pdk_quantity_undeclared`' | 담김 | 새 검사가 0이다. 꼴에서 바로 나온다. |
| 46 | DEC-91 (3) 정본 = LUT C 열 off 점, PDK 접합 선언·엔진 BSIM4 식 0, `junction_forward` 유지 | P:291 | (iv)·(v) ① | 담김 | |
| 47 | DEC-91 (4) 층 0·GB5가 `ss` cdb·csb를 읽음, MOD8 nf 변경 시 무효화 | P:291 | (vi), (v) ② | 담김(암묵) | 무효화는 `ss_dev` READS `dc_finger`와 extra `diffusion` 입력 버전으로 따라온다. design이 이를 명시하지는 않았다(지적 아님). |
| 48 | 'off 점' 의미(O-249) | 계획 v6.38.27에는 없음. v6.38.28 DEC-107 인용 자리 목록에 DEC-91·N6.42가 없음 | D40:1356 ''off 점'은 조회 좌표다' | **넓음 → G3** | design이 자기 base 계획에 없는 결정(O-249)을 끌어와 해석 규칙을 정했다. |
| 49 | 순서: WB-1 + LM-1e 통합 병합 뒤 → 범위 승인 → design | P:2702, P:1325 | D40:1364 'base `f1dd8f52`(WB-1 + LM-1e 병합 뒤 master 계열)' | **다름 → G2** | `f1dd8f52`는 `role/code/20261104-wb1` 머리다. master 위에 있지 않다(`merge-base --is-ancestor f1dd8f52 master` 거짓). `card/lm1e`(머리 `ddd73c62`)에는 spec·interface 문서만 있고 LM-1e code는 base에 없다. |
| 50 | 병합 위치: LA-1a + LA-1 통합 병합 앞 | P:2687, P:2702, P:1392-1393 | D40:12 Status·history | 담김 | design이 병합 위치를 바꾸지 않았다. |
| 51 | design 자리 목록(40 §3.8 10·§2.4.8·§3.9 LY8, 41 §5.3.6 1·§4.9 `diffusion`, 42 '91') | P:2702 | D40:426·470·1355-1379·1394, D41:1038·1251, D42:140 | 담김 | |

## 2. gap 목록과 고칠 쪽

| gap | 분류 | 내용 | 고칠 쪽 |
|---|---|---|---|
| **G1** | 다름(중) + as-built 표지(부분) | 계획은 레이아웃 전 r를 'r = W/w_ref'라 적었고(P:2694·2700 (1)·291), O-247은 '접합(과 C 열)'을 같은 '소자 폭'으로 비례하라고 했다. design(D40:1372)은 W = 그 평가 `dc_finger`의 m·w_f로 정했다. 그래서 탐색 평가에서 r = (1+residual)·`DeviceOp.W`/w_ref가 되고, 같은 평가에서 C 열(cgg·cgd·cgs·cgb)은 `DeviceOp.W`로 비례한다(`ss_linearize.py:79`). 한 소자가 두 폭을 쓴다. design은 이를 'WB-1 뒤 지금 엔진과 같은 꼴, 손계산 오차 → E-1'로 받았다. '지금 엔진과 같은 꼴'은 as-built 근거(원칙 8)다. 계획 근거로 남는 것은 DEC-91 (2) '기하 자리 = `dc_finger`'뿐이다. 계획 문언 안에서도 'r = W/w_ref'와 '기하 자리 = `dc_finger`'는 residual ≠ 0일 때 서로 다른 값이다. 그 차가 어느 쪽인지 계획이 정하지 않았다. 물리 판단: 실현될 기하는 m·w_f라 접합 쪽은 물리적이다. 다만 C 열과 접합이 다른 폭을 쓰는 것은 O-247의 '같은 소자 폭 비례'와 어긋난다. E-0 위반은 아니고(판정 자리인 실현 평가는 residual = 0) 정의 문제다. | **계획 먼저**: N6.42 범위 1·완료 (1)과 DEC-91 (2)에 'W = 그 평가 `dc_finger` m·w_f(탐색 평가에서는 `DeviceOp.W`와 (1+residual) 차, 판정 자리 = 실현 평가라 같음)'을 적는다. 아니면 C 열과 같은 W로 통일할지 결정한다. 그다음 design D40:1372에서 '지금 엔진과 같은 꼴' 근거를 지우고 계획 문언을 인용한다. 그 전에 spec/interface card를 쓰면 toy (a)의 기대값이 W 해석에 따라 갈린다. |
| **G2** | 다름(소) | design이 base `f1dd8f52`를 'WB-1 + LM-1e 병합 뒤 master 계열'이라 적었다(D40:1364). 사실은 WB-1 code 브랜치 머리이고, master에는 없고, LM-1e code도 없다. 계획 순서(P:2702)는 'WB-1 + LM-1e 통합 병합 뒤 → 범위 승인 → design'인데, design이 통합 병합보다 먼저 나왔다. 줄 실측 base = 'WB-1 브랜치 머리'(P:2693)이므로 실측 자체는 계획대로다. LM-1e는 v6.38.28에서 잡음·mismatch tol 조회를 바꾸므로 design이 유지로 분류한 `noise_devices.py` 줄이 rebase 때 바뀔 수 있다. | **design**: base 문언을 'WB-1 code 브랜치 머리(LM-1e code 미포함)'로 고친다. 순서 앞당김은 `la1_auto_decisions.md`에 기록한다(O-229 7). 착수 때 통합 병합 base에서 줄을 다시 잰다(design이 이미 적음). |
| **G3** | 넓음(근거 시점) + 계획 감사 누락 | design D40:1356이 O-249를 근거로 ''off 점' = 조회 좌표, 소자 분류 아님, 코드 식별자에 'off' 금지'를 정했다. design의 base 계획 v6.38.27에는 DEC-107이 없다. 병렬 계획 v6.38.28 DEC-107의 인용 자리 목록(N3.6 표 9·10행·정본, DEC-90 (1), N6.14, N6.40, graph-consumption, oracle-portability)에는 DEC-91 (2)·N6.42의 'off 점'·'off 점 오염 구간' 문언이 빠졌다. 원칙 19(새 원칙 → 기존 계획 문언 전수 대조)의 누락이다. 내용 모순은 없다. DEC-91 (2)도 off 점을 'VGS 축 최소 격자점'이라는 좌표로 정의했고, design 해석은 DEC-107과 맞는다. 다만 해석 규칙은 지금 design에만 있다. | **계획 먼저**: v6.38.28 병합(또는 그 둘째 커밋)에서 DEC-107 인용 자리에 DEC-91 (2)·N6.42를 더하고, DEC-91 (2)에 'off 점 = 조회 좌표(소자 꺼짐 분류 아님, DEC-107)' 한 문장을 둔다. 그 뒤 design은 DEC-107·DEC-91 (2)를 인용하도록 바꾼다. 병합 순서는 plan v6.38.28 → design JC-1이다. |
| **G4** | 다름(소) | 완료 (3)은 '`git grep` + 리터럴 lint'를 요구한다. design (viii)(3)은 '판정자가 diff에서 확인 -- 새 lint 도구 0'이라 적었다. 그런데 리터럴 lint는 이미 있다(`E/tests/structure/README.md:47` 규칙 D, `structure_checks.py`). 새 도구가 필요 없으므로 O-229 4와 충돌하지 않는다. | **design**: (viii)(3)에서 `tests/structure` 규칙 D(숫자 리터럴)를 상수 0의 lint로 인용한다. 이 test는 O-229 2 범위 안이다. |
| **G5** | 빠짐(소) | 완료 머리 '결정성 비트 동일'(P:2700)이 design (viii)에 없다. | **design**: (viii)에 결정성 항목을 더한다(같은 입력 두 실행의 `ss_dev` cdb·csb 비트 동일). |
| **G6** | 빠짐(소) | 완료 (8)의 fail-closed 대상은 'LUT VGS 축·C 열·`w_ref_m`'이다. design test 꼴(viii)(8)에는 CDD 없음·CGS 없음·AD_ref = 0만 있다. CSS 열 없음 toy가 없다(식 (i) 3에는 CSS 분기가 있음). VGS 축·`w_ref_m` 결손은 '기존 적재 관문이 보장'이라고 인용만 했고, 어느 기존 test가 그것을 거부로 확인하는지 적지 않았다. | **design**: CSS 없음 toy를 더한다. VGS 축·`w_ref_m` 결손은 기존 관문 test 이름(`lut_cap_width_unresolved` 등)을 적는다. 없으면 toy를 더한다. |
| **G7** | 다름(소) + as-built 표지 | S0 단계 정지(kind 기준 폭 표 없음, AD_ref·AS_ref ≤ 0)를 bare `ValueError`로 정했다(D40:1359, (iii)). 근거는 '같은 블록의 온도 기록 없음 `ValueError`와 같은 꼴'로, as-built 선례다. 계획 완료 (8)은 C 열 결손에 '분류된 정지'를 요구한다. kind 기준 폭 표 없음은 C 열 결손에 해당한다. | **design**: 분류된 사유로 정하거나, S0 설정 오류의 `ValueError`가 분류된 정지에 해당한다는 근거를 계획 정의(fail-closed 규칙)에서 끌어온다. as-built 선례를 근거로 쓰지 않는다. |
| **G8** | 빠짐(소) | 범위 5 분류 grep이 `junction`(영문)만 보기 때문에 한글 '접합'만 쓴 낡은 문언이 빠진다. 실측: `E/core/CONTRACT.md:343`('접합 용량 F/m²·F/m … `tnom` °C'. design (iv)의 core :340-342 밖), `E/core/pdk_decl.py:14` 설명('접합 용량 F/m²'). '접합' 줄 수는 core CONTRACT 7, metrics CONTRACT 21, search CONTRACT 2다. 또 `references/design-report-spec.md`·`references/sky130-worked-example.md`의 `junction` 줄이 (vii) 범위 밖 표지에 없다. | **design**: (iv)에 위 두 자리를 더하고, (vii) 범위 밖 표지에 `references/` 둘을 더한다. 계획 범위 5 grep에 '접합'을 더하는 것은 선택이지만 권고한다(계획 먼저). |

### as-built 표지(gap으로 세지 않음)

- **A1**: G1 안의 '탐색 평가의 (1+residual) 몫은 WB-1 뒤 지금 엔진과 같은 꼴'(D40:1372).
- **A2**: 상수 식별자 `JUNCTION_LUT_RULE`·`JUNCTION_LAYOUT_DIFFUSION` 유지 근거 가운데 '소비자 … 이동 0'(D40:1360)은 바꾸는 비용 근거라 원칙 8 위반이다. '내용과 맞음'은 정당한 근거이므로 결론은 그대로 둘 수 있다. 문언만 고친다.
- **A3**: 필드 이름 `junction_source` 유지 근거 '소비자·지문 자리 이동 0'(D40:1358)도 같은 꼴이다. 계획 graph 규칙(P:2691 '지금 자리')이 자리를 정했으므로 결론은 계획에서 나온다. 문언만 고친다.
- **A4**: G7.

### 관찰(gap 아님, LA-1 재점검 입력 후보)

- **O-1**: CGS 열이 없으면 접합 쪽이 정지하므로(D40:1365 (i) 3), `ss_dev`의 `cap_model` 값 `cgg_minus_cgd_at_gs`가 도달 불가가 된다. `ss_metrics` M6 표지 값 하나의 소비자가 사실상 0이다. `caps`의 다른 호출자(`lut/ft_curve.py:24`, `search/iv_currents.py:107`)는 그 경로를 쓰므로 `caps` 코드는 남는다. 계획 완료 (8)이 요구한 정지라 기준 위반은 아니다. 분류 표에 적어 두면 된다.

## 3. 병렬 계획 v6.38.28(`c3129a4a`)과의 병합 충돌·모순

두 브랜치 모두 `f1dd8f52`에서 갈라졌다(실측 `merge-base --is-ancestor f1dd8f52 c3129a4a` 참).

- **계획 본문**: v6.38.28은 N6.42와 DEC-91 행을 건드리지 않는다(diff에서 `JC-1`·`N6.42`·`DEC-91`·`접합`·`junction` 0건). JC-1 계획 문언과 텍스트 충돌은 없다.
- **의미 모순**: off 원리(DEC-107) 대 'off 점'. DEC-107은 수치 문턱으로 꺼짐을 분류하지 않는다고 정한다. N6.42와 DEC-91 (2)의 off 점은 VGS 축 최소 격자 좌표이고, 오염 구간 소자 수는 기록만 하며 판정에 쓰지 않는다. 그래서 내용 모순은 없다. 다만 용어 충돌 위험이 있고 v6.38.28의 원칙 19 감사 범위에서 빠졌다. 이것이 G3이다.
- **design 텍스트 충돌(확실)**:
  - D40 `version`(:3)·`plan_version`(:4)·Status(:12): 두 쪽 모두 바꾼다.
  - D41 `version`·`plan_version`(:3-4)·Status(:17): 두 쪽 모두 바꾼다.
  - D42 `version`(:3)과 :10 뒤 글머리 삽입: 같은 자리에 둘 다 넣는다.
  - design history :1021 뒤 삽입: 같은 자리에 둘 다 넣는다.
- **판 번호 충돌**: 두 쪽 모두 'design v1.16.25'라 내용이 다른데 번호가 같다. JC-1 history가 '병합 때 정리'라고 이미 적어 두었다. 권고: v6.38.28이 먼저 병합되면 JC-1 design을 v1.16.26·`plan_version` 6.38.28로 다시 매긴다.
- **본문 줄 충돌**: 없음. v6.38.28이 D40에서 바꾼 줄(:345·434·517·1178·1259·1483·1635·1637)은 JC-1이 바꾼 줄(:426·470·1355-1379·1394)과 겹치지 않는다. D41의 JC-1 줄(:1038·1251)도 v6.38.28 줄(:516·664·669·718·792·898·942·946·970)과 겹치지 않는다.

## 4. 점검(이 분석의 범위)

| 점검 | 결과 |
|---|---|
| graph 단일 정본 | design은 writer `ss_dev` 하나, S0 칸 하나, 새 필드·cache 0이다(표 #37~#40). G1은 한 소자에 폭 정의 두 개(`DeviceOp.W` 대 m·w_f)가 쓰이는 정의 축 문제다. JC-1이 새로 만든 것은 아니고(WB-1 산물), 계획이 정할 몫이다. |
| 상수 발명 | 0. off 점 VGS는 축 데이터이고 toy 값은 이진 유한 소수다. |
| fail-closed | G6·G7 |
| 원래 취지와 다름 | design이 '없음'이라 적었다. 이 분석은 G3(O-249를 base 계획보다 먼저 반영)을 별도 보고 대상으로 올린다. |
| 실측 출처 | 이 문서의 파일:줄은 모두 직접 열거나 grep한 것이다. agent 인용은 없다. |
