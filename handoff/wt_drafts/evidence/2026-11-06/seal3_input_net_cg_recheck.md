# 봉인 3 입력 포트 넷 행 -- A-124 뒤 CG 재측정 (2026-11-06)

자리: WB-1 worktree `wt/20261105-wb1-c` 머리 `3397b834`를 `git archive | tar -x`로 푼 사본 두 벌(읽기만, worktree 무변경).
- base = `C:/Users/HSLEE/AppData/Local/Temp/la1s_seal3_18/src/` (코드 그대로)
- 안 A = `.../la1s_seal3_18/srcA/` -- `gmid_engine/sizing/seal_kcl.py`만 고침: READS에 `("node","port_direction")` 추가, `port_direction == INPUT_DIRECTION` 넷을 레일처럼 KCL 행에서 뺌, 그 넷의 Σ 전류를 같은 `graph.dc_seal_3` 레코드 detail `input_source_current`로 기록(새 필드·새 writer·cache 0).
- 측정 스크립트 `.../la1s_seal3_18/scripts/s3_measure.py`(엔진 파일 무수정 -- `seal_kcl.judge`·`converge_point.evaluate`·`realize_front.evaluate` 스파이만), 실행 `run_all.sh`·`run2.sh`, 원 출력 `.../la1s_seal3_18/out/*.txt`(측정 뒤 임시 폴더 전체를 지웠다(`rm -rf "${X:?}"`) -- 아래 표가 기록 정본. worktree 상태 무변경·머리 3397b834 확인, 남은 python 프로세스 0).
- 출발 점 = `tests/convergence/conftest.py` `RealPath.start` 꼴(층 0 θ, ln_idu = −14, current ×3e5). ngspice 0, pytest 0, 동시 실행 1.
- 모드: **direct** = RealPath처럼 탐색 평가 점을 `converge`에 바로 넣음. **pipe** = `realize_front`(실현 평가) → 살아남은 점을 `converge`.

## 1. 측정 표

### 1-1 common_gate_amplifier (입력 `vin` = M1 drain + M2 source, 갈래 `as_is_single_input` = 입력 고정 KCL 재풀이)

| 출발 점 | 모드 | 판 | 결과 | 재평가·키 제외 | 끝 점 변화(대 탐색 점) | 봉인 3 vin 행 / 원 전류 | 제약 행 c(재평가) |
|---|---|---|---|---|---|---|---|
| 손 점(세 소자 W 같음) | direct | base | converged | 1·0 | vout +83.1 mV, I M1 +6.49 %, M2·M3 −0.015 %, ΔVGS 0 | res 6.96e-7 A, tol 1.97e-6(키 1000 셀), 비 0.35 통과 | ss:1 gain 17.35, ss:2 ugf 4.76, ss:3 gbw 4.76, ss:4 pm 896, ss:5 ppm 896, ss:6 rout 1.06e7, spec:area 2.33e6 -- 전부 ≥ 0 |
| 같음 | direct | A | converged | 1·0 | base와 비트 동일 | 행 없음, 원 전류 +6.96e-7 A 기록 | base와 같음 |
| 같음 | pipe | base·A | 실현 평가 sealed(Δ 0, r 같아 vin 행 0), **`realize_front` 탈락** `realized_spec_unmeasured`(noise_excess_th) | - | - | 0 | 탐색 점과 거의 같음(ss 행 ≥ 0) |
| probe(ln_idu M1 ×1.01, M3 ×0.99 -- 소자별 r 다름) | direct | base | **infeasible_after_layout** | 22·21(재평가 1~6 newton 비수렴, 7 봉인 7 M2, 8~22 봉인 3 vin) | - | 비 6.7~3209(res 1.3e-7~4.9e-6 A, tol 7.3e-10~2.0e-8) | 실패 평가라 제약 행 없음 |
| 같음 | direct | A | **converged** | 8·7(1~7은 base와 같은 사유로 키 제외, 8에서 통과) | vout −128.0 mV, I M1 +7.27 %, M2·M3 +1.36 %, ΔVGS 0, 그 뒤 고정점(추가 재평가 0) | 행 없음, 원 전류 6.33e-7 A(I_D의 5.9 %) | ss:1 gain 35988, ss:2 ugf 10748, ss:3 gbw 10748, ss:4 pm 1.40e6, ss:5 1.40e6, ss:6 rout 3.0e10, spec:area 2.33e6 -- 전부 ≥ 0 |
| 같음 | pipe | base | 실현 평가 **failed** 봉인 3 vin 비 100.2 → `realize_front` 탈락 `seal_item_3` | - | - | res 7.33e-8 A, tol 7.31e-10 | 없음 |
| 같음 | pipe | A | 실현 평가 sealed(vout +39.7 mV, I M2·M3 +0.74 %, M1 +0.05 %) → `realize_front` 탈락 `realized_spec_unmeasured`(noise_excess_th) | - | - | 원 전류 −7.33e-8 A 기록 | ss:1 36919, ss:2 12588, ss:3 12588, ss:4 1.48e6, ss:6 2.96e10, spec:area 2.32e6 -- 전부 ≥ 0 |

같은 재평가(probe direct 8번)에서 base와 A의 vin 잔차는 같은 6.33e-7 A다. base는 그 행을 비 849로 거부하고, A는 원 전류로 기록하고 통과시킨다. 다른 행(vout)·다른 봉인 항목·제약 행 판정은 두 판이 같다.

### 1-2 입력이 채널에 닿지 않는 회로

| 회로(입력 연결) | 갈래 | 모드·출발 | 판 | 결과 | 끝 점 변화 | 봉인 3 입력 넷 행 | 제약 행 c |
|---|---|---|---|---|---|---|---|
| two_stage_ota(vin_p·vin_n = M1·M2 gate) | servo | direct, (i, j) = (12, 5) | base | converged, 재평가 1·키 제외 0 | 입력 ±0.23 mV(servo), D3 +52.6 mV, O1 −50.2 mV, I −1.9 %~−5.7 %(M6·M7), ΔVGS M3·M4 −52.6 mV, M6 +50.2 mV | **행 없음**(입력 넷이 `dc_current_basis.ends`에 없음) | ss:0 gain 5.06, ss:1 gbw 0.54, ss:4 pm 0.21, ss:5 ugf 4.97, ss:6 ppm 13.0, ss:7 rout 1.03e8, spec:area 5.09e6 -- 전부 ≥ 0 |
| 같음 | servo | 같음 | A | converged 1·0, base와 비트 동일(출력 diff = detail 빈 기록 한 줄) | 같음 | 행 없음, 원 전류 기록 () | base와 같음 |
| two_stage_ota | servo | pipe, 기본 (10, 6) | base·A | 실현 평가 sealed(입력 ±0.05 mV, I ≤ 0.11 %) → `realize_front` 탈락 `realized_spec_unmeasured`(offset_excess·noise_excess_th) | - | 행 없음, base·A 출력 동일(차이 = detail 빈 기록 한 줄) | - |
| two_stage_ota | servo | direct, 기본 (10, 6) | base·A | 출발 점 ss:1 gbw c = −330 → `converge` 입력 거부(측정 불가) | - | - | - |
| folded_cascode(vin_p·vin_n = M1·M2 gate) | servo | pipe | base·A | 실현 평가 sealed(내부 넷 9행 비 ≤ 0.095) → `realize_front` 탈락 `realized_spec_unmeasured` | - | 행 없음, base·A 동일 | - |
| folded_cascode | servo | direct | base·A | 레이아웃 뒤 재평가 1번째에서 **`KeyError 'M5'`**(`metrics/ss_linearize.py:99` -- 레이아웃 뒤 평가의 빈 `dc_finger` 열을 실현 확산 기하가 없는 소자 M5에 대해 읽음). 봉인 3까지는 계산됨(내부 넷 행 비 ≤ 1e-6) | - | 행 없음, base·A 같음 | 측정 불가 |
| pushpull_follower_buffer(vin = M3·M4 gate) | 입력 고정(`as_is_single_input`) | pipe, ln −20, M1 ×1.01·M3 ×0.99·M5 ×1.005 | base·A | 실현 평가 sealed(ΔV ≤ 0.02 mV) → `realize_front` 탈락 `realized_spec_unmeasured`(ugf·pm·ppm `dc_not_above_level`) | - | 행 없음, base·A 동일 | - |

### 1-3 n/N

- 안 A가 판정을 바꾼 회로: CG 1개(입력이 채널 끝점인 유일한 회로). 바꾸지 않음을 직접 잰 회로: two_stage_ota(servo), folded_cascode(servo), pushpull(입력 고정) 3개 -- 셋 다 입력 넷이 gate에만 닿아 봉인 3 행 자체가 없다(구조상 원 전류 0, base·A 출력 동일).
- 측정한 회로 4/13(library). 레이아웃 루프까지 잰 회로 2/13(CG, two_stage_ota). folded는 레이아웃 뒤 첫 재평가에서 위 KeyError, pushpull은 실현 평가 단계만.
- pipe 모드는 측정한 회로 전부(4/4)가 `realize_front`의 `realized_spec_unmeasured`(미측정 spec 행이 하나라도 있으면 탈락)에서 끝나 converge까지 가지 못했다. 같은 미측정 행은 탐색 출발 점에도 있다(converge의 `_accepted`가 출발 점 대비 '잃은' 미측정만 보므로 direct는 통과). 봉인 3과 무관한 사실이라 기록만 한다.

### 1-4 two_stage_ota 안 A
direct (12, 5): base와 같은 converged(재평가 1, 키 제외 0, 레이아웃 3, converge 52.2 s). 출력 diff는 `seal3 detail (('input_source_current', ()),)` 한 줄뿐 -- 판정·전류·제약 c 동일.

## 2. 잴 것 3 답

**(a) 전류 표류가 A-124 뒤에도 생기는가.** 생기지 않는다. 앞 측정(`wb1_resolve_check.md:36·41`)의 −40 %·−70 % 걷기는 재평가 스냅샷이 다음 레이아웃 입력이 되는 되먹임이었다. 지금 코드(`convergence/converge_point.py:101` -- `place_layout`은 늘 `start.evaluation.snapshot`)에서는 안 A 판도 재평가 1번 통과 뒤 바로 고정점이다(probe CG: 통과 1회, 그 뒤 재평가 0, 레이아웃 9회 중 8회는 키 제외 재시도). 남는 변화는 한 번의 실현 오차뿐이다: probe CG I M1 +7.3 %·M2·M3 +1.4 %, vout −128 mV, ΔVGS 0(M1·M2·M3 gate = 고정 바이어스, vin = 고정 입력이라 VGS가 바뀔 수 없다). M1과 M2의 전류 차 6.3e-7 A는 입력 전압원이 댄다.
  - 단 two_stage_ota(base)에서 VGS 최대 52.6 mV·전류 −5.7 % 이동은 남는다. 이건 입력 넷과 무관하고(행 없음), 레이아웃이 아직 gm/ID 보존(`layout/slice_density.py`의 `vgs_for_gm_id`, LI-1 미병합)이라 생기는 실현 기하 어긋남이다. 되먹임 걷기가 아니라 1회 이동이다(재평가 1, 고정점).

**(b) 실현 평가·레이아웃 뒤 재평가가 AC 제약 행을 다시 판정했는가.** 그렇다. 재평가 결과의 `constraints`에 `spec:`·`ss:` 행이 c 값과 함께 있고 값이 탐색 점과 다르다(표 1-1·1-2 c 열; 예 probe CG ss:2 ugf 12485 → 10748, two_stage_ota ss:4 pm 156 → 0.21). `ls:` 행은 측정한 회로 spec에 없다. `_accepted`(`converge_point.py:54-57`)가 c ≥ 0 전부와 미측정 비증가를 요구하고, `realize_front._judge`(`search/realize_front.py:51-66`)가 `spec:`·`ss:`·`ls:` 행 c < 0과 미측정을 거부한다.

**(c) 표류(변화)가 남은 점이 spec을 만족하는가.** 만족한다. 안 A로 통과한 probe CG 점의 재평가 제약 행은 모두 c ≥ 0(최소 = 출력 단 w_min 등 수천, ss 행 최소 ugf 10748)이고, 그 판정은 레이아웃 실현 W′·입력 고정 KCL 재풀이 점에서 다시 계산한 AC 소신호 값이다. 그러므로 '입력 고정 회로의 실제 물리(입력원이 차 전류를 댐) + AC 판정 통과'이며 fail-open이 아니다. base의 거부는 물리 결함이 아니라 원 전류를 KCL 위반으로 셈한 것이다.

## 3. 결론

### 3-1 'LI-1 이후 적용' 조건을 유지할 근거
**남지 않는다.** 그 조건의 근거는 '입력 행을 빼면 레이아웃 기준점 되먹임 표류가 거부에서 조용한 수렴으로 바뀐다'(`wb1_questions_check.md` 2-3, `wb1_resolve_check.md:41·64`)였다. A-124(기준점 = front 점, `converge_point.py:9-11·101`)가 그 되먹임을 없앴고, 실측에서 안 A 판은 1회 실현 이동 뒤 고정점이며 그 점은 AC 제약을 다시 판정받아 통과했다. VGS 보존(LI-1)은 two_stage_ota 같은 회로의 실현 이동 크기를 줄이는 별개 사안이고, 입력 넷 행과는 독립이다(two_stage_ota·folded·pushpull에 입력 넷 행 자체가 없음).

추가 근거(물리 정합, O-200): 같은 물리량(입력원 전류 ≈ I_D의 6 %)이 슬라이스 tol 셀에 따라 통과(손 점, 키 1000 셀 tol 1.97e-6 A, 비 0.35)도 되고 거부(probe 점, 다른 키 tol 7.4e-10 A, 비 849)도 된다. 지금 판정은 tol_V(수치 자기 정합 tolerance, O-240)가 물리 경계를 정하는 꼴이다. 안 A는 이 행을 방정식이 아닌 원 전류로 돌려 이 의존을 없앤다.

### 3-2 안 A 조건 셋과 측정
| 조건 | 측정 | 판정 |
|---|---|---|
| servo 출력 넷 행 유지 | 안 A 코드는 `port_direction == input`만 뺀다. CG vout 행·two_stage_ota OUT 행이 두 판에서 그대로 판정됨(비 ≤ 1e-4). servo 회로 2개(OTA·folded)에서 A 출력 = base | 맞음 |
| spec 노드 목표 넷 판정 유지 | 목표 넷(REL_TARGET)은 port_direction이 input이 아니라 제외되지 않는다(코드 대조). 측정 4회로에 목표 넷 선언 행이 있는지는 따로 세지 않았다 → 행 유지는 코드로 확인, 실측 사례 0 | 조건부(실측 사례 없음) |
| 입력원 전류 기록 | `graph.dc_seal_3` detail `input_source_current`로 기록됨(CG +6.96e-7, 6.33e-7, −7.33e-8 A; 다른 회로는 빈 기록). writer = `dc_seal_kcl` 하나, 새 필드 0 | 맞음 |

### 3-3 물리 판정
**맞음(조건: 입력 포트 = 측정 구성의 이상 전압원).** 근거: (1) CG `vin`은 원문상 전압 구동 입력(Allen L20 p.2 'Voltage-driven', `assets/library/sources/common_gate_amplifier__allen_2014/source.pdf` p.2 -- 앞 점검 인용, 이번에 다시 열지 않음)이고, oracle도 입력을 이상 전압원으로 구동한다(`tools/spice_oracle/oracle_netlist.py:110`, 앞 점검 인용). 이상 전압원 넷의 KCL은 원 전류로 늘 닫히므로 방정식이 아니다 -- 레일을 빼는 이유와 같다(`seal_kcl.py:31·48`). (2) 입력 고정 갈래 재풀이(`block_dc.py:780·791-793`)는 이미 입력을 미지수에서 빼고 행을 두지 않는다. 봉인 3만 그 행을 판정해 풀이 정의와 봉인 정의가 어긋나 있었다(정의 동일성). (3) 내부 넷 판정은 그대로라 진짜 KCL 위반은 숨지 않는다. (4) 측정에서 통과한 점은 AC 재판정을 통과했다(DC sizing의 충분성은 AC 판정이 확인 -- 사용자 의견과 맞음).
⚠ 전류 구동 입력(TIA 등)이 들어오면 '입력 포트 = 전압원' 전제가 깨지므로 측정 구성 정의부터 바뀌어야 한다(앞 점검 2-2 그대로). 원 전류 크기 거부 문턱은 두지 않는다(상수 발명·tol 경계 금지, 앞 점검 2-5) -- 입력 바이어스 전류 spec이 선언되면 그 제약이 판정한다.

### 3-4 graph 규칙 점검(안 A 구현 꼴)
- 새 필드 0, 새 writer 0: `dc_seal_kcl` READS에 기존 S1 필드 `node.port_direction`(`graph/s1_values.py:142` 등) 한 칸 추가. 원 전류 기록은 같은 블록이 이미 계산하는 넷별 Σ의 일부를 같은 레코드(`graph.dc_seal_3`) detail로 둔다 -- 다른 블록의 재계산(둘째 생산자) 없음.
- 새 cache·memo·sctx 슬롯·사본 0. READS 추가로 입력 버전이 바뀌므로 graph reuse·S3 graft 키에 자동 반영(별도 처리 불요).
- 문서 대조: 계획 N3.6 표 3행(P:656) '모든 넷 검사, E-30' 문언과 `seal_kcl.py:9` docstring이 바뀐다 → 원래 취지와 다름 표지·사용자 승인 대상(앞 점검 2-6 E-30 행 그대로).

## 4. 부수 관찰(이번 질문 밖, 기록만)
1. folded_cascode direct: 레이아웃 뒤 첫 재평가에서 `KeyError 'M5'`(`metrics/ss_linearize.py:96-99` -- 레이아웃 뒤 평가는 `dc_finger` 행을 쓰지 않고(빈 열), `realized`(실현 확산 기하)가 없는 소자는 `fingers[m]`을 읽어 KeyError). 분류된 FailureRecord가 아니라 예외가 `converge` 밖으로 나간다. base·A 공통, 3397b834 코드 사실.
2. pipe 모드 4/4 회로가 `realize_front`의 미측정 거부(`realize_front.py:61-62`)에서 탈락. 탐색 출발 점도 같은 미측정을 갖는다. 실제 파이프라인이 front 점을 모두 잃는 경로인지 확인 필요.
3. probe CG 재평가 1~6은 `newton_line_search`·`newton_iteration_cap` 비수렴(입력 고정 KCL 재풀이), 7은 봉인 7(M2). 두 판 같음.

## 5. 못 잰 것
- two_stage_ota 기본 (10, 6) 출발 점은 지금 spec에서 gbw c = −330이라 converge 입력이 안 됨 → (12, 5)로 잼(앞 측정과 같은 점).
- folded·pushpull 레이아웃 루프(위 KeyError, pushpull은 c ≥ 0 출발 점 없음 -- 앞 측정과 같음).
- 목표 넷(REL_TARGET)이 있는 회로의 실측 사례.
- ngcc_3stage_ff 등 나머지 9 회로.
