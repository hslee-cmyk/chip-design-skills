verdict: Major 2

# FS-1 (20261107-fs1) 순서 3 동결 재판정 -- 판정자 독립 측정

- 대상: test head `47617174`. audit worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261107-fs1-audit`에 `git merge --no-ff role/test/20261107-fs1`로 들였다. 병합 커밋은 `cf609919`, tree는 `67a34d39`. 엔진 코드 변경은 0이다.
- 격리: `git -c core.longpaths=true clone --no-hardlinks --no-local <audit wt> C:/fzf1/iso2`를 하고 `remote remove origin`을 했다. 모든 실행은 이 복제본 안에서 했다.
  - 실행 래퍼는 `C:/fzf1/run2.sh`다. cwd = `gmid_engine/tests`, `-p no:cacheprovider`, OPENBLAS_NUM_THREADS=1, PYTHONIOENCODING=utf-8, `GMID_LUT_TABLE_CACHE_DIR=C:/fzf1/lutcache`.
  - 결과 파일은 `C:/fzf1/out2/`에 있다.
- 작성자 보고는 증거로 쓰지 않았다. 아래 수치는 모두 이 복제본에서 잰 값이다.

## 앞 Major 처리 확인

| 앞 Major | 결과 | 근거 |
|---|---|---|
| M-1 LutAccess | **고침** | g1·g2·g3 출력에 `'LutAccess' object has no attribute`가 0건이다. `fs1_wf`·`hand_wf_of`·S-B1·S-B5·M-1 P4는 `ctx.lut.memo.lut`로 바꿨다(`LutAccess.memo.lut` = `lut_memo.py:109`). `test_type_error_ctx`는 PASS다. 영향 파일의 base 실패는 모두 코드 없음 메시지다(아래 표). |
| M-2a·b·c·d | 고침 | (a) CMFB 3건 RETIRED: 단계 A가 루프를 정지시킨다(대상 소멸). (b) 단계 B 선거부를 단언하도록 바꿨다(PASS, 문자열 단언 -- minor n-2). (c) E-2·E-3·N 계열은 `jc1_cols=True`(base 코드 없음). (d) S1 전제 2건 RETIRED. |
| **M-2(e)** | **미해결 → MR-1** | 아래 진단 |
| M-3 stub | 고침 | O-2는 `tamper`로 `wf_start` 칸 하나를 `w_key=None`으로 쓴 손 스냅샷이다(S-B4 허용 범위). O-3은 R-6c에서 실제로 잃는 점이다. 동작 대체는 0이다(diff 확인). |
| M-4 spy | 고침 | `metrics.device_sigma.mismatch_sigma_vgs`에 통과 spy를 둔다(card 5c5909c6 §9). 정적 판정이며, `test_iv_matching_l`은 지시로 실행하지 않았다. |
| M-5 재작성 | 대부분 고침, **잔여 → MR-2** | R-5·R-6(2)·R-6c·R-6 피벗·R-15·S3-6·R-13a·R-13b·L-2(2)를 다시 썼다. 옛 test(510eb146)와 단언을 줄마다 대조했다. 핵심 식·tol·사유 단언은 그대로다. R-2 삭제 근거는 맞다(아래). |

**R-2 삭제 근거 확인**:
- interface §1 정의상 한 칸 멤버의 m 벡터는 E1 = max(r)/min(r) − 1을 먼저 최소화한다. 같은 W(x1 = x2)면 같은 m이 E1 = 0을 내므로 m이 다를 수 없다.
- diff_pair 멤버가 한 칸이면, 탐색 W가 같은 점에서 실현이 입력 차 이동을 만들지 않는다. 그래서 옛 R-2의 비대칭 입력(M1만 r = 0.5)은 실현 경로로 만들 수 없다(대상 소멸).
- 닫힌 식 `diff_pair_input_shift` 자체는 R-13a(레이아웃이 소자 하나만 바꿈)가 그대로 단언한다.
- 대체 test는 손 oracle(`hand_oracle`)로 m을 내고, 입력 차 이동 ≤ tol을 단언한다. 타당하다.

## M-2(e) 원인 진단 -- 분류 (a) test 입력 결함. 그 점의 실현 불능은 (b) 물리적으로 맞다. (c) 엔진 결함 증거는 없다.

측정은 `C:/fzf1/probe_m2e.py`로 했다(pytest 아님, base 엔진). 같은 toy를 옛 S1 수준 `build_case`(2cb26c92 판 그대로)와 새 정본 `build_case`로 만들어 비교했다. 출력은 `C:/fzf1/out2/probe_{c,z,cp}.txt`, `tab_c.txt`다.

1. **스냅샷 차이**(circuit_c, 실측):
   - 새 경로 base에만 있는 필드 32개다. 모두 단계 B writer가 쓴 것이다(`start_intervals`·`achievability`·`build_s1v`·`coupling_vars`).
   - 공통 필드 값 차이 4개:
     - `device.M1.theta_class`: B → F. S1v가 없으면 전부 B, 있으면 입력 = F(`sizing/theta_class.py:42`).
     - `graph.s1v.metric_structure`: None → 있음.
     - `noise_input_cells`: () → `(('in',),('out',),('M1',))`.
     - `mismatch_source` sha(PDK 선언 경로 차).
   - sctx 칸은 context_fp만 다르다(domain 같음).
2. **탐색 출발이 달라진다**:
   - 층 0(`search/layer0_center.py:128-135`)은 `graph/start: rungs` 칸 0이 정한 성분을 쓴다. 옛 경로에는 이 레코드가 없어 상자 중심에서 출발했다.
   - 새 경로 출발은 cells [0,0], 전류 37 pA(power 6.7e-11 W)다. 옛 경로는 cells [1,1], ~5 nA다.
3. **front 점이 실현에서 잃는다**(`runs.jsonl` realize.lost):
   - 새 경로 유일 탐색 front 점 EA:s1: M1 W = 5.0e-7(= toy PDK `MINW_UM = 0.5`, w_min 활성), M2 W = 7.59e-7, 슬라이스 w_f = 1e-6 하나.
   - 실현 m = 1, 1이므로 r1 = 1.0, r2 = 0.317이다.
   - circuit_c는 입력 고정 갈래(`as_is_single_input`)이고, r4 toy는 ID ∝ e^{λ·VDS}(λ = 0.1, triode 없음)다.
   - 그래서 out KCL 손 근 = V0 − ln((1+r1)/(1+r2))/(2λ) = 0.9 − 2.089 = **−1.19 V (gnd 아래, 레일 밖)**다.
   - 엔진은 `NONCONVERGENT newton_line_search`(norm 0.0178 → 0.0101, tol 0.0078)로 그 점을 잃는다. 그래서 front가 비고 failed_eps는 0이다.
   - 옛 경로 EA:s1은 r = 0.790/0.758이고 손 근 0.81 V(레일 안)여서 살아남았다(우연한 궤적).
   - 같은 손 식이 6개 경우 모두에서 엔진 실현 결과(잃음/남음)를 맞혔다. 손 근이 레일 안이면 sealed, 밖이면 lost였다(probe_c·probe_c_w1.0·probe_c_w3.0).
4. **세 test 모두 같은 원인이다**(z·cp 출력도 같은 점·같은 수치). 작성자가 본 `C-78`·`DEC-79 passive_area_undeclared`·`gain_ss_db passive_value_undeclared`는 원인이 아니다. 앞 둘은 정보 줄이고, 마지막은 cp test가 기대하는 미측정 사유다.
5. **코드 뒤 예측**: FS-1 실현은 `realize_fingers((W,), w_f, ())`다. x = 0.5 → 후보 {1}, x = 0.759 → {1}이므로 m은 같다. 탐색 목적(게이트 면적·전력)은 `dc_finger`를 읽지 않고, 슬라이스가 하나라 w_f 이웃 이동도 없다. 그래서 **코드 뒤에도 세 test는 red로 예측**된다. 코드 없음으로 설명되지 않는 test 결함이다.
6. **분류 근거**:
   - 엔진은 정본 경로에서 물리적으로 맞게 움직인다. 고이득 입력 고정 노드에서 손가락 반올림 잔차 비가 출력을 레일 밖으로 민다. 그 점을 잃는 것은 E-0 fail-closed다.
   - toy 자체에는 실현 가능한 점이 있다(옛 궤적 EA:s1). 그래서 'feasible 점이 없다'는 (b)는 아니다.
   - test 기대 'front ≥ 1(예산 30)'이 출발 궤적에 기대고 있었다 → (a).
7. **고칠 입력**(test 작성자 몫, 판정자 실측):
   - 실측 ①: toy PDK `minw_um="3.0"`(`write_decls(root, minw_um=...)`를 `build_case(pdk=, rule=)`로 넘김)이면 세 경우 모두 새 경로에서 front 1 / unmeasured 1이 나온다. 손 근 1.365 V로 레일 안이다(`probe_c_w3.0.txt`·`probe_z_w3.txt`·`probe_c_cap_pending_w3.txt`).
   - ⚠ ①은 권하지 않는다. PDK 최소 finger 3 µm > LUT finger 슬라이스 1 µm라 선언이 물리적으로 맞지 않는다(finger가 PDK 최소보다 좁다).
   - 실측 ②: `minw_um="1.0"`(슬라이스와 같음)은 front 0이다(M2 m = 2, r = 0.317 → 손 근 2.28 V, 레일 밖).
   - 권고: 세 test는 실현과 무관한 성질(memo 동일성·미측정 점 front 제외·θ 수동소자 측정)을 본다. 그러니 실현 조건이 좋은 toy로 바꾸고, 전제 단언 '손 근이 레일 안'을 붙인다. 예: 저항 부하(V 이동 ≈ a·r로 유한), servo 피벗 회로. 서지 않으면 A-188 규칙대로 RETIRED와 덮이지 않는 성질을 기록한다. 어느 쪽이든 `pytest.skip`이나 기대 약화는 금지다.
8. 작성자의 엔진 소스 grep 열람(C-78·find_front.py) 흔적은 RETIRED 문장에만 있다. 기대값 줄에는 0이다(diff `^+` grep: `C-78|DEC-79|counted_rails|passive_area_undeclared|CONTRACT` → RETIRED 2줄뿐). 세 test는 23c81fe1 이후 바뀌지 않았다.

## Major (새 판정)

**MR-1 (M-2(e) 미해결, test 입력 결함 → 코드 뒤 범위 test 실패 예측)**: 위 진단. 세 test 위치는 `search/test_find_front.py:262`·`:152`, `search/test_search_context.py:512`다.
- 재현: `bash C:/fzf1/run2.sh m2e -q --tb=long <세 id>`, `C:/Python314/python.exe C:/fzf1/probe_m2e.py <out> c_default`.

**MR-2 (다시 쓴 test 의 단언 약화 잔여 -- 기준 약화)**:
- (a) `convergence/test_realized_geometry.py::test_layout_resolve_l2_waiting_device_row_is_the_request_and_junction_follows_two_places`:
  - 옛 공허 방지 `cdb1 != cdb2 and csb1 != csb2`가 `cdb1 != cdb2 or csb1 != csb2 or junction_model 다름`으로 바뀌었다. junction_model 두 값은 위에서 각각 단언되므로 OR은 늘 참이다.
  - 손 계산: `TOY_RULE_LINE` as/w = 0.3e-6이고 요청이 nf 3·1e-6이다. csb1 = s_cap·(3e-13·3)/(0.3e-12) = 3·s_cap = csb2다. 요청 nf를 2 → 3으로 바꾼 결과, csb는 두 자리(레이아웃 면적/규칙 면적)를 가르지 못한다.
  - 고칠 입력: 요청 nf 4(W' 4e-6 ≠ 기준 2e-6, cdb2 = 4·d_cap ≠ 1.8·d_cap, csb2 = 4·s_cap ≠ 3·s_cap). AND를 되살린다.
- (b) `search/test_realize_front.py::test_realize_r16_power_is_rail_current_of_realized_channel_current`:
  - 옛 단언 `dict(rsnap.column("device","dc_current"))["I2"] == R16_IB`(이상 전류원 항 출처)가 빠졌다.
  - 탐색 평가 `ev.objectives.power_w == V_dd·(I + I_b)`(전제·성질)도 빠졌다. `v0["s"] == I·R` 전제도 빠졌다.
  - 새 입력(i 스케일)으로 그대로 쓸 수 있다(`i` 대입).

## minor (LA-1 재점검 입력으로)

- n-1 S3-6의 둘째 test `test_realize_s3_6_resolve_has_no_held_target_set`(block_dc.py `held` 0, 정적)이 되살려지지 않았다.
  - RETIRED A-190은 'S3-6 되살림'이라고 둘을 구분하지 않았다. 삭제 사유 '같은 입력 없음'은 정적 검사에 맞지 않는다.
  - 성질은 행동 test(목표 넷을 고정하면 봉인 3 실패 → lost)가 덮는다.
- n-2 M-2b 두 test가 `SchemaRejectedError.record.detail`의 reason·capacitors 대신 `build_case` AssertionError 문자열 포함(`"Cz" in str(e)`)으로 바뀌었다. 정밀도가 줄었다. fail-closed(커널 0)는 유지된다.
- n-3 `test_initial_wf_missing_field_is_a_lookup_error_fail_closed`는 `KeyError` 타입을 요구한다. interface에는 없지만 S-B3이 `snapshot.value(...)` 읽기를 명시하므로 함의된다. `LookupError`로 넓히는 것을 권한다.
- n-4 R-13a·R-13b·L-2에서 옛 `_assert_input_rows`(레이아웃 뒤 dc_finger 행 = (nf, w_f, 0.0))가 빠졌다. interface §4.4가 레이아웃 뒤 `dc_finger` 행을 정하지 않고 FingerGeom 칸이 바뀌었으므로 정당하다(기록).
- n-5 R-16·S3-6 재작성에서 `icm_config` 입력 고정 갈래 전제 단언이 빠졌다(R-6은 유지).
- n-6 `search/test_realize_front.py:209`의 모듈 수준 `from sizing.test_realize_fingers import hand_oracle` 때문에 base에서 파일 전체가 수집 오류다. R-1·R-4·R-7·R-9·O-1의 base red도 측정되지 않는다. test 모듈 사이 import보다 helper 파일로 옮기는 것을 권한다.
- n-7 test가 `LutAccess.memo.lut`(LutMemo 속성)을 읽는다. 공개 docstring(`s2_values.py:241`)에 있는 이름이라 허용한다.
- n-8 O-3이 `small_m` 값 꼴(None 또는 정렬)만 단언한다. 이 시나리오는 손으로 `["M1"]`(m = 1)이다. interface는 키만 요구한다(강화 권고).
- n-9 (엔진 쪽, FS-1 밖) 레일 안 근이 없는 실현을 엔진이 `newton_line_search` 비수렴으로 분류한다(근 없음 사유 아님). R-6c는 사유가 비어 있지 않은지만 본다.

## base 재측정 (O-229 범위)

| 묶음 | 결과 | 분류 |
|---|---|---|
| (a) `tests/structure` 전체 | 8 failed / 198 passed / 1 deselected (174 s) | 8 = 코드 없음 (앞과 같음: test_fs1_source G-1~G-5 7, wb1 finger_slice 1) |
| (c) `--collect-only` | 11263/11292, 수집 오류 4 | 모두 코드 없음 ImportError: test_l_bin_search(polish_cells)·test_start_intervals(initial_wf)·sizing/test_realize_fingers(DeclaredRatio)·**search/test_realize_front(209행 hand_oracle import → DeclaredRatio, 새로 생김)** |
| (b) g1 lut 4 + sizing 13 | 321 failed / 265 passed / 3 errors | 324 코드 없음(WfCell 287, ImportError 18, slice_of_finger 서명 5, C-1 DID NOT RAISE 3, 결정성 subprocess 2(WfCell) …) + 1 `dc_finger` 칸 목록(FingerGeom 새 칸 = 코드 없음). test 결함 0 |
| (b) g2 metrics 5 + convergence 2 + integration/test_layer0_boundary_rows | 90 failed / 66 passed / 2 xfailed (199 s) | 90 코드 없음(WfCell 55, FingerGeom 서명 34, RealizeInput 1) |
| (b) g3 search 변경 20 (test_iv_matching_l 제외) | 110 failed / 108 passed / 1 deselected / 11 errors (289 s) | 코드 없음 118(WfCell 91, eval_key 서명 11, perf `wf_neighbor_*` 5, 수집 3 …) + **MR-1 3** |

**안 돌린 범위(통과로 세지 않음)**:
- `search/test_iv_matching_l.py`(지시로 제외, M-4는 정적)
- search 디렉터리 전체
- generality 3파일, `integration/test_s0_layer_9circuits.py`(앞 판정에서 메모리 정지가 있었다. 이번에는 돌리지 않았다 -- 미측정)
- 2회로 연기 stage_b·s0·g10, `search/test_canonical_order.py`, slow 표지
- 변경 없는 파일

## 판정자 절차 이탈 (자기 기록)

- probe 준비 중 실수로 `python -`(stdin) 프로세스를 하나 띄웠다. 바로 그 PID(36680)만 정지했다(실행 0, 파일 변경 0).
- 내 임시 스크립트 `C:/fzf1/groups.sh`에 `sed -i`를 한 번 썼다(저장소 밖, 실행 결과 영향 없음 -- 새 `rerun.sh`로 다시 돌림).
- 빈 stdin `cat > /dev/null`을 한 번 썼다. 모두 금지 목록 위반이라 기록한다.
- 끝날 때 python 프로세스는 0개였다.

## code 착수 가능 여부

**불가 (Major 2).**
- MR-1: 세 test의 입력을 고치거나(실현 조건이 좋은 toy + 손 근 전제), RETIRED와 기록이 필요하다.
- MR-2: L-2 요청 nf 4 + AND 복원, R-16 단언 복원이 필요하다.
- 둘 다 test 쪽만 고치면 된다. 다시 판정할 범위는 고친 파일 + 세 test다.
