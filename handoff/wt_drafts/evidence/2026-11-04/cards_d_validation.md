# card 묶음 d 독립 판정 (2026-11-04)

대상: `docs/cards1104d` head `a2114214`, master `e33100cc` 대비 전체 diff(`skills/` diff 0). oracle 계획 v0.6.27, gain-budget P:1393, oracle design v0.4.3, card `20261104-op7a`, `20261104-op1b`, 위임 A-5·A-8·A-10·A-13·A-23·A-53·A-54.

방법: 문서 읽기, `git show`·`git grep`, 텍스트 도구(grep·awk·sha256sum). pytest·LUT 배열 읽기·엔진·ngspice 실행 0. LUT meta 값은 커밋된 OP-1 측정 기록으로만 읽었다. PDK 모델 파일과 `REGEN_REPORT.md`, ngspice 실행 파일은 텍스트 검색만 했다. 엔진 인용은 재작성 범위·외부 사실 확인뿐이다(원칙 8).

## card별 판정

| card | 판정 | Major | 비고 |
|---|---|---|---|
| op7a | M4 정정 뒤 test·측정 가능 | M4 | toy 전 행 손 유도 일치. S-1·S-2 맞음 |
| op1b | M1~M3 정정 뒤 가능 | M1, M2, M3 | 그대로면 A-2·A-3·A-4가 모두 실행되지 않거나 확실히 실패한다. fail-closed로 멈추기는 한다 |
| 계획 v0.6.27·design v0.4.3 | M1·M2 문언 정정 | M1, M2 | S-1 둘째 자리 없음 |
| OP-0 gap | 실질 gap 0 | 0 | 아래 §7 |

위임 밖 항목은 없다(근본원칙 변경, connectivity, 기준 약화 0). 멈춤 표시 없음.

## Major

**M1. op1b J-1의 사실이 틀렸다: 결합 파일 r2도 `.bins.csv`를 기록한다. F-2가 그대로면 확실히 실패한다** (실현 가능성 판단 오류, 계획·design까지 전파)

- 실측: `.ai/verification/20261016-op1-baseline/op1_measurements/files/results/m2_m3_lut_meta.jsonl` 3~40행 38행 전부 `bins.csv`를 담는다(`grep -c` 38/38). 35~40행 결합 파일 6개는 kind마다 중첩으로 담는다(r2 = 38행). 생성기도 같다: `00085057`·`723f30e8` `sky130_lut_sweep.py`의 `files = _included_files(dev) + [... .bins.csv]`.
- 그래서 J-1 '결합 파일 6개에는 없다(S-29, 재측정 F-2)'는 틀렸다. design S-29 '38개 중 32개'도 중첩을 세지 않은 값이다. 물리·논리 영향: 옛 입력 includes에는 bins.csv가 없어 규칙 (i)에서 역할 미선언 기록이 모델 파일로 취급되고, T-4g 그대로 `model_bundle_mismatch`다. interface §5 A-2와 spec C-2는 `roles`를 어디서 받는지 적지 않았다.
- 결합 파일 선택 자체는 유지된다. 근거 '두 kind 입력은 결합 파일만 가능'은 맞다. 그리고 r2는 막히지 않는다: r2 `generator_sha256` `60584696…`(같은 파일 38행) = `00085057` blob의 CRLF 변환 바이트 sha256(내 측정: `git show 00085057:… | sed 's/$/\r/' | sha256sum`), 그 판 677행이 include 밖 추가 줄이다. §12.5 근거 (a)의 raw 일치 후보다. OP:769 미발견은 폭 슬라이스 `8df35d2e…`만 해당한다. 근거 (b)와 실제 통과는 미측정.
- **고칠 문언**
  - op1b spec J-1 근거 칸: '옛 형식은 `lut_npz` 하나라 두 kind 입력은 결합 파일만 가능. 결합 파일도 `.bins.csv`를 기록한다(`m2_m3_lut_meta.jsonl` 35~40행). 역할 근거 (a): r2 생성기 `60584696…`는 `00085057` blob CRLF 바이트와 같고(raw 일치), 폭 슬라이스 `8df35d2e…`는 못 찾았다(OP:769). 그래서 r2는 §12.5 역할 근거를 잴 수 있다.' 대안 칸은 그대로.
  - spec C-2 F-2 뒤, interface A-2: 'F-2의 `roles` = 검증자가 §12.5 근거 (a)(b)를 r2에 대해 재서 만든 값(판정 기록 안, 저장소 옆 선언 아님. 옆 선언 파일은 OP-3 (c) 몫). 근거 둘 중 하나라도 안 맞으면 역할 미선언으로 두고 F-2 실패 = 멈춤. 역할 없이 통과시키지 않는다.'
  - 계획 OP-1b 행 v0.6.27 문장: '(…두 kind 입력은 결합 파일만 가능; 결합 파일도 보조 입력을 기록하므로 묶음 대조에 역할 근거가 필요하다. r2 생성기 판은 이력에 있고 폭 슬라이스 판은 못 찾았다, OP:769.)' 옛 '폭 슬라이스는 역할 옆 선언이 필요'를 대체.
  - design S-29 끝, §12.5 '32/38'·'기존 LUT 32 슬라이스', §16 v0.4.3 '폭 슬라이스 32개' 세 자리에 정정 한 줄: '(v0.4.4 정정) 결합 파일 6개도 중첩 안에 기록한다: 38/38(`m2_m3_lut_meta.jsonl`). 32는 평탄 표만 센 값.'

**M2. 대표 입력 10건에 `process.ngspice_exe`가 없다: C-4가 틀렸고 A-3이 돌지 않으며 변환 계약에 구멍이 있다** (구현 불가)

- 실측: R1~R10 `git show … | grep -c '"ngspice_exe"'` 전부 0. `process` 키 = `lut_npz, models[, diffusion]`. 옛 코드 `oracle_run.py:86-88`: `a.ngspice or inp["process"].get("ngspice_exe")`, 없으면 '실행 파일 경로 없음'으로 끝난다.
- 따라서 spec C-4 '시뮬레이터 실행 파일은 입력 `process.ngspice_exe`'와 C-4 명령은 10/10 실패한다. C-1이 `lut_npz` 하나만 바꾸라 하므로 입력으로 넣을 수도 없다.
- 변환도 같다. T-9a만 `ngspice_exe`가 있는 경우이고 §11.5는 '옮긴 뒤 삭제'뿐이다. 없는 입력에서 `simulator.exe`를 비우면 §11.2 1e `simulator_exe_missing`이 8단계 D-7보다 먼저 걸려 §11.5 (i) 기대 결과(`lut_model_provenance_missing`)가 어긋난다. 옛 초안 `n4_convert_input.py`는 `exe = None`을 그대로 썼다.
- **고칠 문언**
  - spec C-4: '`$PY O/oracle_run.py <입력> <출력> --bias ... --ngspice <exe>`. `<exe>` = OP-7 선언 `simulator`와 판이 같은 실행 파일(입력 10건에 `process.ngspice_exe` 없음). 실행 로그의 판을 선언 `simulator.version`과 대조해 기록하고, 다르면 멈춘다.'
  - D §11.5 `process.ngspice_exe` 행: '옮긴 뒤 삭제. (v0.4.4) 옛 칸이 없으면 변환 인자 `exe`를 쓰고 기록에 `exe_absent`를 남긴다(값을 짓지 않음, 인자도 없으면 변환 거부).'
  - interface 서명: `convert_input(old, *, lut_files, descriptor, adapter, exe=None)`. toy 추가: 'T-9e `process.ngspice_exe` 없음, `exe = "x"` | `new.simulator.exe == "x"`, `record.exe_absent == True`' / 'T-9f 둘 다 없음 | `Op1bStop("exe_unresolved")`'.

**M3. A-4·C-6의 `dv5_vos_recompute.py`를 R10 기록에 돌릴 수 없고, `vos_samples`·`sigma_mean`은 소비자가 없다** (구현 불가, 만들면 배선)

- 실측: 스크립트 `CASES`는 고정 두 건이다(`pytest/tmp/mc5t0/o`, `u6/mc_5t` + `input_bundle/u6/…`, 117~124행). 인자 `<record 폴더>`만 바뀌면 `u6` 쪽 파일이 없어 죽는다. `verify_sha256.py`처럼 그대로 재사용할 수 없다.
- 그런데 interface §2의 `vos_samples`·`sigma_mean`은 toy만 있고 호출 자리가 없다. 소비자 표는 '`run_op1b.py`, 판정'이라 적었으나 측정 표가 dv5를 부른다.
- **고칠 문언**(spec C-6, interface A-4): 'MC: `scripts/vos_recompute.py`(이 card 폴더)가 R10 로그·meta·ac 파일에서 V_id·V_out·A를 `dv5_vos_recompute.py`와 같은 읽기로 얻고 `op1b_lib.vos_samples`·`sigma_mean`으로 표본별 V_os와 σ·mean을 낸다. OP-1 스크립트는 고치지 않는다. 2회 비트 동일, R10 `sigma_in_mV`·`mean_in_mV`와 비트 동일. 같은 스크립트를 OP-1 `mc5t0`에 돌려 `dv5_result.json` 그 case와 비트 동일(방법 동일성).' A-5의 OP-1 회귀 문장은 그대로.

**M4. op7a C-10의 시뮬레이션 조건이 슬라이스 생성 조건에 묶여 있지 않다. 문턱이 없어 조건이 틀려도 답이 나온다** (fail-open 경로, 원칙 2 정의 동일성)

- C-10은 `source_point`로 폭 슬라이스의 `ID`를 읽는데 넷리스트 꼴 근거는 `A/sky130_lut_sweep.py:248-258·:371`이다. 그 파일은 결합 파일 생성기(`DUT_LINE`: `w=5u ad=2.5p …`)이고, 슬라이스 생성기는 `sky130_dc_width_slices.py`이며 저장소에 없다(`git ls-files` 0, manifest). 슬라이스 meta에는 `w_m, nf, m, geometry, width_source, corner, temp_c_from_log, units`가 따로 있다(`m2_m3_lut_meta.jsonl` 3행 `top_keys`). 슬라이스 `ID` 단위는 이 판정에서 값을 못 읽었다(미측정. r2는 `"A at W_ref"`).
- `identify_mode`는 둘 중 가까운 쪽을 늘 고른다. 단위·nf·m·온도·코너가 틀린 시뮬레이션이어도 `"default"`가 나오면 `judge_source_modes`가 `ok`다. 문턱을 두라는 뜻이 아니다. 문턱 없음은 맞고(원칙 2), 대신 **조건 동일성**이 관문이어야 한다.
- **고칠 문언**(spec C-10 넷리스트 문장 대체): '시뮬레이션 조건 = 그 슬라이스 meta 기록: 폭·병렬 배수(`w_m`·`nf`·`m`), 확산 기하(`geometry`), 코너·온도(`corner`·`temp_c_from_log`, 넷리스트 `.temp`), 포함 파일(그 슬라이스 `model_files_sha256`의 모델 파일, 바이트 대조). 바이어스 극성·벌크는 슬라이스 meta `sign_convention`을 읽는다. `ID` 단위는 meta `units`로 환산해 비교한다. 칸이 없거나 뜻을 못 정하면 그 점은 `None`이고 값을 짓지 않는다. 판별된 점이 없으면 `source_mode_undetermined`로 멈춘다.' 거부 표와 D §16 문장 끝에 '조건 = 그 세트 meta'를 더한다. toy는 그대로(순수 함수 변경 없음).

## 볼 것별 결과

**1. test 작성자 유도(T-8·T-9·T-12~T-15 포함).** op7a T-1~T-15, op1b T-1~T-9 전 행을 손으로 유도했다. 값은 모두 맞다. 예: T-12a 격자 정수 (33, 1000)·(43, 1000), 정렬 (W, L) 맞음. T-13 (36, 800) = `("L",)`, (36, 1000) = `("L","W")`. T-14 거리 0.1/1.0, 0.9/0.1, 0.5/0.5. T-7b 변형 11 ↔ 기대 11. T-8 다섯 판정은 표에서 규칙이 유일하게 정해진다. T-7 σ = √2·10⁻³. 빈 sha256 상수 맞음. 소스 없이 낼 수 있다. 빈틈은 m1·m6·m7.

**2. 계획 ↔ design ↔ card, S-1.** 전체 grep: `<lut 폴더>`는 이력 문장 X-37·X-R10과 history뿐이다. `bin_rule` 코드 자리는 다른 뜻의 `test_pdk_decl.py:975` 하나다. OP:489 예외, OP:512, D:1387·1397, interface §1 모두 `A/lut_v2_bin_rule.json`. 둘째 자리 없음. OP-8 새 LUT meta는 계획이 정한 다른 세트의 writer다. 줄 인용 D:1389·1394·1395·1397·1899·1918, OP:482·489·506·512·769, P:1367·1375·1392·1393 대조 일치. 커밋 `b6787f4b`·`41e08c44`·`fb40a4e4`·`66f04511`·`5fea301e` 존재.

**3. S-2.** fail-closed 맞다. `mixed_direction`이면 선언 없음(T-3d 축 사이 포함), `w_boundary_no_interior` 멈춤. 승인된 근거는 P N6.32 범위 0('W·L의 bin 소속 … 경계 방향은 bin 경계 선언', 2470행 부근)이라 W 측정은 미승인 문서 없이 선다. 다만 미승인 §3.7-A를 근거 자리에 쓴 문장이 셋 있다(m5). S-2 필요성은 PDK에서 확인: 슬라이스 폭이 bin `wmin`과 겹친다(manifest 첫 `w_um` 0.36, bin 표). 텍스트 스캔 결과 bin 표는 kind 둘 다 직교 격자다(nfet 180, pfet 108, 다른 L 구간끼리 W 맞닿음 0, 다른 W 구간끼리 L 맞닿음 0, 경계를 가로지르는 셋째 bin 0).

**4. S-3.** 문턱 없음, 수치 일치 판정 아님: 맞다. 같은 값 처리 정해짐: `None`(T-14), 전부 `None`이면 `source_mode_undetermined`, 일부 `None`은 빼고 판정. 두 모드가 그 칸에서 같은 값이면 그 칸의 모드 차이는 LUT 값에 영향이 없으므로 합당하다. 두 모드 bin이 같고 값이 잡음만큼 다르면 가짜 판별이 될 수 있는데 결과는 `source_mode_differs` 멈춤 쪽이거나 해가 없는 쪽이다. 남는 문제 = M4, m12.

**5. S-5, op1b J-1~J-4.** S-5 정당: §11.2 2b(중첩이면 `kinds` 값 = 그 dict 키)와 §12.5가 요구하는데 §11.5가 `null`만 적어 그대로면 실제 입력 473/595가 2b에서 걸린다(작성자 수치, 재지 않음). 값은 기록(옛 `subckt` 끝)에서 유도하고 0·2개면 거부하니 D-7 우회가 아니다. 실제 키 `nfet_01v8`·`pfet_01v8`과 `subckt` `sky130_fd_pr__nfet_01v8` 맞음(38행, R10). J-1 = M1. J-2 맞음(§3 sha 12자 10건 내 계산 전부 일치, `free`·`forced`·`iso` 산출물 존재, 범주 표지 R2·R3·R4·R5·R6·R9·R10·R1 표본 대조 일치). J-3: sample 파일은 `5fea301e` blob으로 있다(13,835,060 B). 기대 D-7 거부는 §11.2상 `meta_json` 없음 → 8단계와 맞다. 단 m14. J-4 맞음(§11.5 '없으면 N4에 쓰지 않는다'). T-9a는 §11.5 표와 칸별 일치, 구멍은 M2.

**6. SPICE.** A-53 해석 = A-5 문언('card별 SPICE 다리')·P:1392·1393 '(다)'와 맞다. 표지 빠짐 없음: op7a A-2·A-3·A-8, op1b A-3·A-9가 ngspice 실행으로 적혔고 spec 판정 유형 표와 일치, 나머지는 '시뮬레이터 없음'. 'LA-1 재점검 사용자 확인 항목' 표지 있음. A-53이 위임 해석이라는 점은 그대로 사용자 확인 대상이다. 작성 = 검증자 예외(OP:489): op7a는 `assets/` 한 파일, op1b는 판정 기록 안만이고 배포 산출물 0(X-5). 범위 안. 역할 분리 셋(test ≠ 측정 ≠ 재확인) 명시됨.

**7. OP-0 gap(계획 DR 표 전 행 대 design).** 계획 686~723행 **38행**을 design v0.4.3 자리와 대조했다. 방법은 행이 요구한 내용의 문장·칸 grep과 판독이고, 정의 깊이 재검증은 아니다. v0.4.2와의 차이는 이번 diff(§11.5·§16·§19·§20 추가 문장)뿐이고 DR 대상 문장을 지우지 않았다.

| 행 | 자리(design v0.4.3 줄) | 판정 |
|---|---|---|
| DR-1 | 머리 `plan_version: 0.6.27`(5) | 맞음(대응 판 갱신) |
| DR-2·3 | 84, 199·1172 | 맞음 |
| DR-4·5 | 460·462, 549 | 맞음 |
| DR-6·7·8 | 687~690, 728, 688·199 | 맞음 |
| DR-9·10 | 1161, 1172·1192·583 | 맞음 |
| DR-10a~g | 46·51, 463·464·467, 467·738, 583, §9 키, §11.5·909, 1386 | 맞음 |
| DR-10h | §12.7 끝, '§15.4 `make_lut` 행' | 맞음, 자리 차이(행은 §18.2 지목). 경미 |
| DR-10i·j | §20 OP-2·OP-3, 1485 '옮겼다' + OP-3 교차 검사 행 | 맞음 |
| DR-11·12 | 394·430, 1361 | 맞음 |
| DR-13~16 | §18.1 X-13 행, 1556·1716, 1776·1777, 688·1556 | 맞음 |
| DR-17 | 358, 498~499, §14, §18.1, §21.6 | 맞음 |
| DR-18·20 | 행 자체가 [정정됨]. 1082 삭제, 1632 낡음 표지, 1637, 490 삭제 | 맞음(뒤 결정으로 대체, 표지 있음) |
| DR-19 | 492, 884, §21.5, 1764 | 맞음 |
| DR-21 | 1656, 1766~1768, 1104 | 맞음 |
| DR-22·23 | 2055~ 1번, 349, 486 삭제, 1080·1827 `[]` | 맞음 |
| DR-24·25 | 2060, 1674, 487, 1660 | 맞음 |
| DR-26 | 488, §21.2 머리, 113 | 맞음 |
| DR-27·28 | 500, 1889, 2068, 498, 2030 `ref_minus_servo_ref_V` | 맞음 |

**gap: 실질 0 / 38행, 자리 차이 1(DR-10h, 고칠 것 없음).** M1의 S-29는 DR 밖 사실 오기다.

**8. PDK·상수·회로 이름·fail-closed·배선·graph.**
- O-197: card·design v0.4.3에 PDK 값 규칙 없음. 격자는 역할 이름 `manufacturing_grid_m`. toy `T`는 합성 표이고 규칙이 아니다. 예외 지적 m9·m10.
- 상수 발명 0. `set ngbehavior=hsa`는 대조 입력이고 선언 값이 아니다. 시뮬레이터 이름은 §2 예시와 측정 도구에만.
- 회로 이름 규칙 0(R 표는 입력 목록, 판정 기록). kind·모델 이름은 읽어서 쓴다.
- fail-closed: 거부 표 전부 선언 없음·멈춤. 조용한 기본값 없음. 구멍 = M4, m3.
- 배선: 기간 예외 표지 둘 다 있음. 다음 소비자 실재: P:1367 'WB-1 … OP-7 선언 기록 조각(범위 0이 읽음)', P:1375 예외 둘, P:1392 'OP-1b | OP-3', D §18.1 '3 동일성'. 미소비 = M3.
- graph 단일 정본: 새 필드·cache·슬롯 0, 값 사본 0(판정 폴더엔 sha256만), `bundle_rules`는 운영 밖 판정 도구. 위반 없음.

**9. base·순서·A-34·GL-1·원칙 8.** P:1375 순서 OP-0 → OP-7 조각 → OP-1b → OP-2 + OP-3와 두 card 일치. op1b base 조건(선언 포함 master) 적힘. A-34: `S1V_RULE_FILES`·`STRUCTURE_RULE_EXTRA_FILES`(`E/graph/s1v_values.py:14·21`)는 graph 파일뿐이라 해당 없음이 맞다. GL-1: `gmid_engine/` diff 0이라 새 키 구조 없음. 정적 시험은 판정 때 실행(미측정). 원칙 8: 엔진 인용은 재작성 범위 표에만. master는 이미 `4467f389`로 앞서 있다(m13).

## minor(14)

- **m1** `point_direction`: 동률 축에서 `chosen`의 그 축 끝이 경계가 아니면 정의 없음. sky130은 스캔 0건이지만 PDK 이식(O-197) 일반 표에서 구현이 'upper'로 조용히 떨어질 수 있다. 문언: '그 축의 `chosen` 끝이 어느 쪽도 경계와 같지 않으면 `BinRuleStop("tie_interior")`' + toy 한 행.
- **m2** `w_boundary_points`: '같은 L 구간' 한정이라 L 구간이 부분만 겹치는 W 맞닿음을 빠뜨린다. sky130 0건. 문언: '겹치는 L 구간이 같지 않은 W 맞닿음이 있으면 `BinRuleStop("w_boundary_not_product")`'.
- **m3** `isolated_env`: `ngspice_con.exe` 안에 `SPICE_USERINIT_DIR` 문자열이 있다(`grep -c` 1, 동작은 미측정). '나머지 그대로'면 그 변수가 격리를 지난다. 문언: '`SPICE_USERINIT_DIR`도 삭제', T-9 입력·기대에 추가.
- **m4** C-5 본 측정 = `.spiceinit` 없음, §16·interface §7 `compat` = 실행 폴더에 `spiceinit_text`를 그대로 쓴 실행(빈 파일). J-1 '대조 run에서 미측정'인데 그 run이 C-5에 없다. 문언: 'C-5 넷째: 실행 폴더에 빈 `.spiceinit`, 빈 HOME. 점 전부 본 측정과 같아야 한다. 다르면 `control_undetermined`.'
- **m5** 미승인 40 §3.7-A를 근거 자리에 쓴 문장 셋: op7a spec '소비자' 첫 행, 'graph 단일 정본' 첫 항목, interface §7 `rule` 행. '남은 표지 … 그 문언에 맞췄고'도 같다. 문언: 근거를 'P N6.32 범위 0, DEC-105 (2)'로 바꾸고 §3.7-A는 'WB-1 승인 때 대조'로만 둔다.
- **m6** T-7a `s1`·`s2` 형식 미정. 문언: 's1, s2 = 소문자 hex 64자'. `validate_decl`이 형식을 보는지 한 줄 + 변형 하나.
- **m7** 측정 신호 빈칸: `include_bundle`의 `read_bytes` 없는 파일 신호(`FileNotFoundError`로 고정), `parse_probe_log`의 다른 줄 무시, `category_present` 칸 없음 = 거짓, 두 bias 입력의 범주 판정 단위('어느 bias든 참'. R3·R4는 양쪽 다 실측 참).
- **m8** op7a A-2 '선언 없음이 합격'은 card 완료로 읽힌다. 문언: '`stop`이면 선언 없음이 옳은 동작이고 판정은 **멈춤**(card 미완료, 보고)'. C-8 '멈춤'도 선언 쓰기 전인지 적는다: 값은 커밋 기록상 r2·noise·mismatch `ngspice` 칸 있음(`m2_m3_lut_meta.jsonl` 36~38행 top_keys).
- **m9** `netlist_lines`의 `m.<inst>.m<subckt>`는 PDK 부회로 안 소자 이름 관례다. 틀리면 `showmod_incomplete` 멈춤이라 fail-closed. 문언: 표지 '안쪽 이름 꼴 = 옛 입력 `op_probe`·`A/sky130_lut_sweep.py:168-171` 사실, 다른 PDK는 OP-8 경로'.
- **m10** C-2 격자 값 출처: `sky130_pdk_decl.json:103`은 `tech_lef` 식이라 값이 없고 엔진 import는 금지다. 문언: '선언이 가리키는 tech LEF를 측정 스크립트가 읽고, LUT meta `manufacturing_grid_um`과 대조, 다르면 멈춤'.
- **m11** interface §7 'LUT 출처 모드 대조 대상 = §16 v0.4.3'에 M4 조건 문장을 함께 넣는다.
- **m12** C-10은 폭 슬라이스만 본다(결합 파일 기준 폭은 L·W 동률이라 `source_point`가 고르지 않음). cap·noise·mismatch 세트 출처는 미대조인데 표지가 없다. 슬라이스 meta bin은 `E/lut/CONTRACT.md` 4.0.1이 틀렸다고 적었으니 대안이 안 되지만, r2 `model_bin_per_L_at_w_ref`는 showmod 기록이다(`REGEN_REPORT.md:41`, 작성자 측 문서). 문언: '결합 세트 = meta 멤버만 읽어 `model_bin_per_L_at_w_ref`와 본 측정 (L, 기준 폭) bin 대조, 다르면 `source_mode_differs`. noise·mismatch는 `cap_npz_sha256`으로 r2에 묶임.' 대조가 과하면 '미대조' 표지만 둔다.
- **m13** gain-budget P:1393 문장을 고쳤는데 그 계획의 판 표기·history 행이 없다. master가 `4467f389`(v6.38.11)로 앞서 있어 줄 번호가 밀렸을 수 있다. 병합 전 base 갱신과 P 줄 재측정, history 한 줄.
- **m14** J-3 '기대 D-7 유지'는 §11.2 앞 단계 통과가 전제다. v0.4.0 1d `bias_gate_nets_mismatch`가 옛 입력을 먼저 거부할 수 있다(미측정, design 기존 문제). 수치도 593(계획)·595(op1b)가 섞였다. 문언: 'OP-3 변화표에서 사유별로 세고, 다른 사유는 §11.5 규칙대로 원인 미설명으로 보고. 593 = OP-1 기록, 595 = 입력 파일 수(차이 사유 한 줄).' 그리고 op1b A-6 `blob_check` 모드는 `verify_sha256.py`에 없다(`raw`·`committed`만, `git grep` 0). 문언: 뜻을 적거나 뺀다.

## 원래 취지와 다름(재판정)

X-37·X-R10 표지 내용은 원문과 맞다. 추가 표지 필요: M1(결합 파일도 역할 근거 필요, OP-3 (c)의 근거 측정 일부를 앞당겨 함), M2(§11.5 '기계적 대응'에 인자 `exe`). A-53은 위임 해석이고 사용자 확인 항목이다.

## 미측정

- 전 측정 실행: ngspice(C-3~C-6, C-10, A-3, A-9), pytest toy, 구조 시험 §10.4.
- LUT 배열·슬라이스 `ID` 단위, 슬라이스 `sign_convention`·`geometry` 값 내용(칸 존재만 확인).
- r2 §12.5 근거 (b), F-1~F-4 실제 통과.
- `SPICE_USERINIT_DIR`의 실제 동작, 빈 `.spiceinit`과 파일 없음의 동등.
- 입력 473/595, 15건, 576건 수치(작성자 측정, 재지 않음). 1d 선행 거부 수.
- DR 행의 정의 깊이 재검증(문장·칸 대조까지만).

1차 판정(head `a2114214`): Major 4

## 재판정 (2026-11-04)

대상: `63d11b85..7d6ff7c6`(`29f44222`, `5cd36ace`, `7d6ff7c6`), base `4467f389`. 이 diff와 그것이 닿는 문장만 봤다. 실행 0, `skills/` diff 0. 반영 대조는 word-diff와 최종 원문으로 했다.

**새 Major 셋 가운데 R1·R2·R3은 모두 내 1차 고칠 문언에서 나왔다.** 작성자는 그 문언을 그대로 옮겼다. 작성자 결함이 아니다. 1차 판정의 문언 검증이 모자랐다.

### 1. 반영 대조

| 항목 | 들어감 | 비고 |
|---|---|---|
| M1 | 예 | J-1, C-2, A-2, 거부 표, 계획 OP-1b 행, D S-29·§12.5 둘·§16 정정 줄. 계획 F-18은 내 목록에 없어 남음(r1) |
| M2 | 예 | C-4, 서명 `exe=None`, T-9e·T-9f, D §11.5, X-R11. 판 대조 거부 행 추가 |
| M3 | 예 | C-6, A-4, 스크립트 자리, 소비자 표, `dv5_vos_recompute.py` 불변. 문언 자체에 결함(R3) |
| M4 | 예 | C-10, 거부 표, D §16, 계획 OP-7 행, interface §7. 문언 자체에 결함(R1·R2) |
| m1·m2 | 예 | T-2f, T-12c 추가. 값 맞음. 빈틈 r3 |
| m3 | 예 | 서명·T-9·미측정 표 |
| m4 | 예, 달리 적음 | 아래 2 |
| m5 | 예 | 소비자·graph·§7·남은 표지. §3.7-A는 'WB-1 승인 때 대조'로만 남음 |
| m6~m12 | 예 | T-7a·T-7c, `read_bytes` 신호, 다른 줄 무시, 칸 없음 = 거짓, 어느 bias든 참, A-2 '멈춤', C-8 선언 전 멈춤, 안쪽 이름 표지, tech LEF 대조, §7 조건, 결합 세트 대조 |
| m13 | 예 | base `4467f389`, v6.38.12, history 행·절, 옛 문언 인용 |
| m14 | 예, 달리 적음 | 아래 2. `blob_check` 정정 포함 |

### 2. 작성자가 달리 적은 곳

- **m14 '593 대 595 차이 미측정, OP-3 변화표에서 잰다': 수용.** '595 = 커밋된 입력 파일 수'는 내 측정과 맞다(`baseline/files` `input.json` 595). 차이 사유를 쓰는 소비자는 OP-3 변화표뿐이고 이 두 card의 판정이 그 값에 기대지 않는다. 내 문언 '사유 한 줄'보다 지어내지 않는 쪽이 옳다.
- **m4 `judge_empty_init`·T-8b: 수용.** C-5 넷째의 판정을 toy로 잠그는 순수 함수이고 소비자는 `measure_bin_rule.py`와 A-2다. 만들면 배선 충족. 구조 규칙 A·H: `gmid_engine/tests/structure`는 엔진 소스·test를 본다(`git grep verification` 0). `.ai/verification/` 스크립트는 대상 밖이고, 1차 spec의 'H 대상 아님' 판단과 같다. 입력 꼴은 `parse_probe_log` 결과와 맞다.
- **oracle 계획 판 유지 'v0.6.27 둘째 커밋': 판 표기 규칙과 맞음, Status 하나만 빠짐.** 선례: history 319행 '승인 전이라 판 번호 그대로', 168~170행 `0.6.22 (둘째 커밋)`. v0.6.27은 미승인이다. 다만 선례 169행은 'Status 둘째 커밋 기재'를 지적받아 고친 사례인데 이번 Status(15행)에는 없다(r2). gain-budget은 승인본 위 변경이라 v6.38.12가 맞고, design v0.4.4 판 올림도 해가 없다.
- **밀린 줄 인용: 모두 맞음.** P:1367·1375·1392·1393, D:1389·1394·1395·1397·1900·1919(내용 대조), OP 줄은 이번 diff가 줄 수를 안 바꿈.

### 3. 새 모순 점검

- **M4 None과 S-3: 모순은 아니나 fail-open 구멍이다 = R1.**
- **M2 `exe`와 거부 순서: 맞음.** 인자가 있으면 1e를 지나 8단계 D-7에 닿는다. 경로가 틀리면 1e가 먼저 걸리고 §11.5 v0.4.4 '앞 단계가 먼저 거부' 규칙에 든다. `/simulator/exe`는 선택 칸(CLI 우선)이라 '인자도 없으면 변환 거부'는 계약보다 엄격할 뿐 충돌이 아니다. `옛 칸 우선`도 §11.5 문언에서 유도된다.
- **M1 멈춤 경로: fail-closed 맞음.** 근거가 안 맞으면 역할 미선언 → T-4g `model_bundle_mismatch` → 멈춤. 옆 선언 파일을 만들지 않고 OP-3 (c)를 낮추지 않는다.
- 실행 로그 판 대조: 커밋된 로그에 `ngspice-46 done` 있음(`mc5t0` 2635행). 실현 가능. 판이 안 나오는 경우 r5.

### Major

**R1. M4 'None 처리'가 조건 미달 점을 조용히 뺀다** (fail-open, 원칙 10)

- `None`의 뜻이 둘이 됐다. 원래는 두 모드 거리가 같음·NaN이라 그 칸에서 모드가 LUT 값에 영향이 없다(1차 §4). 이제 '조건 칸 없음·뜻 못 정함'도 `None`이다. `judge_source_modes`는 `None`을 빼고 보므로, 한 kind의 meta가 비고 다른 kind가 판별되면 `ok`다(T-15 `["default", None]`). 그 kind의 LUT 생성 모드는 확인 없이 선언이 쓰인다. 'S-3 전부 None이면 멈춤'은 전 점이 빠질 때만 막는다.
- **고칠 문언**
  - spec C-10: '칸이 없거나 뜻을 못 정하면 그 점은 `None`이고 값을 짓지 않는다. 판별된 점이 없으면 `source_mode_undetermined`로 멈춘다.' → '칸이 없거나 뜻을 못 정하면 `source_condition_unresolved`로 멈추고 선언을 쓰지 않는다(값을 짓지 않음). `None`은 `identify_mode`의 같은 거리·NaN뿐이다. 판별된 점이 없으면 `source_mode_undetermined`로 멈춘다.'
  - spec 거부 표: '(조건 칸 없음·뜻 못 정함은 `None`)' 삭제, 행 추가 '슬라이스 조건 칸 없음·뜻 못 정함 | `source_condition_unresolved`, 선언 안 씀'.
  - interface §7: '칸이 없으면 그 점 `None`' → '칸이 없으면 멈춤'.
  - 계획 OP-7 행·D §16: '칸이 없거나 뜻을 못 정하면 그 점은 판별하지 않는다' → '칸이 없거나 뜻을 못 정하면 선언을 쓰지 않는다'.
  - 위임 A-56의 '칸이 없으면 None'도 같이 고친다. toy 변경 없음(순수 함수 밖, 측정 스크립트 판정).

**R2. C-10 '포함 파일 = 슬라이스 `model_files_sha256`의 모델 파일'은 정할 수 없다** (구현 불가)

- 슬라이스 기록에는 `.bins.csv`가 섞여 있고, 역할은 선언으로만 정하며 이름·확장자 규칙이 금지다(§12.5). 슬라이스 생성기 `8df35d2e…`를 못 찾아 역할 근거도 없다(OP:769). 글자대로면 모델 파일을 못 정해 모든 점이 멈추거나, 이름 규칙으로 §12.5를 어기게 된다.
- **고칠 문언**(spec C-10, D §16 '포함 파일' 자리): '포함 파일 = 결합 세트 생성기의 include 목록(엔진 밖 사실 `A/sky130_lut_sweep.py:220-228` `model_includes`). 재귀로 닿는 파일마다 LF·raw 중 하나가 그 슬라이스 기록 값에 있어야 한다(포함 파일 ⊆ 기록, 어기면 `source_condition_unresolved`). 기록에만 있는 파일은 `source_modes.jsonl`에 적고 역할은 여기서 정하지 않는다.' S-38의 슬라이스 기록 구성(nfet 3, pfet 4)과 목록이 맞아 실현 가능해 보인다(값 대조는 미측정).

**R3. A-4의 σ·mean 비트 동일을 `sigma_mean`이 낼 수 없다** (구현 불가)

- 옛 값 = `np.asarray(vos, float)`의 `arr.std(ddof=1) * 1e3`, `arr.mean() * 1e3`(mV, `5fea301e` `oracle_offset_mc.py:185·:190`, dv5도 같음). `op1b_lib`은 표준 라이브러리만 쓰고 V 단위다(T-7). numpy 합산 순서를 순수 Python으로 비트까지 맞춘다는 근거가 없다. 그대로면 거짓 멈춤이거나 기준을 낮추는 압력이 된다. `vos_samples`는 문제없다: 식이 옛 `:184` `(vo - vout0) / a_signed - (vi - vid0)`와 같고 float 연산 순서도 같다.
- **고칠 문언**
  - spec C-6, interface A-4: '`vos_recompute.py`가 `op1b_lib.vos_samples`로 표본별 V_os를 내고, σ·mean은 옛 `:185·:190`과 같은 식(`np.asarray(vos, float)`, `std(ddof=1) * 1e3`, `mean() * 1e3`)으로 낸다. 2회 비트 동일, R10 `sigma_in_mV`·`mean_in_mV`와 비트 동일. OP-1 `mc5t0`에 돌려 `dv5_result.json` 그 case의 `per_sample_vos`(`V_os_hex`)·σ·mean과 비트 동일.'
  - interface §2 `sigma_mean` 행과 T-7 둘째 행 삭제, spec 소비자 표에서 `sigma_mean` 삭제(소비자 0, 만들면 배선). `vos_recompute.py`는 toy 대상 밖이라 numpy 허용을 §1에 한 줄 적는다.
  - 대안: `sigma_mean`을 numpy로 바꾸는 안 ⚠ 표준 라이브러리 제한을 깸. 비트 동일을 분해능 비교로 바꾸는 안 ⚠ 기준 약화(위임 밖).

### 4. 새 toy 유도

T-2f(0.18/4 µm는 `x` 안, 끝 30·50 ≠ 36 → `tie_interior`), T-7c, T-8b, T-9(`SPICE_USERINIT_DIR`), T-9e, T-9f, T-12c(겹침 36~50, 구간 다름) 모두 interface만으로 값이 나오고 맞다. 빈틈은 r3·r4.

### minor(7)

- **r1** 계획 F-18(190행)이 아직 '38개 중 32개'다. 내 M1 목록이 설계만 들어 빠졌다. 문언: F-18 끝에 '(v0.6.27 둘째 커밋 정정) 결합 파일 6개도 중첩 안에 기록한다: 38/38. 32는 평탄 표만 센 값.'
- **r2** 계획 Status(15행)에 둘째 커밋 기재 없음(history 169행 선례). 문언: 'v0.6.27 둘째 커밋 -- 독립 판정 반영(위임 A-56), 재판정 전'.
- **r3** `w_boundary_points` '겹치지만 같지 않으면': 닫힌 구간으로 읽으면 `T`의 `m.0`(L 30~36, W 600~1000)과 `m.3`(L 36~50, W 1000~1400)이 끝점 36에서 닿아 T-12a가 `w_boundary_not_product`가 된다. 실제 bin 표도 그렇다. 문언: '겹침 = 정수 구간 공통 길이 > 0(끝만 닿으면 겹침 아님)'.
- **r4** T-7c는 `s1`이 형식과 순서를 함께 어길 수 있는데 기대는 포인터 하나다. 문언: '`validate_decl` 포인터는 중복 제거'.
- **r5** C-4 '다르면 멈춘다'에 판이 로그에 없는 경우를 더한다: '판을 못 읽어도 멈춘다'.
- **r6** C-10 'noise·mismatch는 `cap_npz_sha256`으로 r2에 묶인다'는 내 문언인데 값을 확인하지 않았다(`m2_m3_lut_meta.jsonl`에는 칸 이름뿐). 문언: '그 값을 위치 선언 `files.cap_npz.sha256`과 대조, 다르면 그 세트는 미대조로 멈춤 보고'. 결합 세트 대조의 bin 이름 꼴도 meta 값 형식이 미측정이라 '꼴이 다르면 값을 짓지 않고 멈춤'을 더한다.
- **r7** `vos_samples`는 None 없는 목록을 받는데 옛 `:184`는 실패 표본을 거른다. A-4에 '실패 표본은 옛 `:173-177`처럼 부르기 전에 거른다' 한 줄.

### 원래 취지와 다름

없음 추가. R1은 M4 의도(조건 틀린 판별 차단)를 맞추는 쪽, R3의 `sigma_mean` 삭제는 M3의 함수 목록 변경이다. 위임 밖 항목 없음, 멈춤 표시 없음.

### 재판정 미측정

ngspice·pytest 실행 전부, `cap_npz_sha256` 값, 슬라이스 meta 칸 값 내용, 슬라이스 기록과 `model_includes` 값 대조, numpy와 순수 Python 합산의 실제 차이(R3은 근거 없음을 지적한 것이고 차이를 재지 않았다), 593 대 595 사유.

재판정(head `7d6ff7c6`): Major 3

## 최종 재판정 (2026-11-04)

대상: `7d6ff7c6..2ce7021c`(`2dec0b7a`, `35befdb4`, `2ce7021c`). 이 diff와 그것이 닿는 문장만 봤다. 실행 0, `skills/` diff 0. PDK 파일과 커밋된 OP-1 기록은 텍스트로만 읽었다.

### 1. 반영 대조

| 항목 | 들어감 | 자리 |
|---|---|---|
| R1 | 예 | spec C-10·거부 표, interface A-2·§7, 계획 OP-7 행, D:1397, 위임 A-57 |
| R2 | 예, 줄 번호만 틀림(f1) | spec C-10·거부 표, D:1397, 미측정 표 |
| R3 | 예 | C-6, A-4, §1 numpy 문장, `sigma_mean` 행·T-7 둘째 행 삭제, 소비자 표. 남은 `sigma_mean`은 op1b spec:156 경위 한 줄뿐 |
| r1·r2 | 예 | F-18, Status, history 행. 표지 f2 |
| r3·r4 | 예 | 겹침 정의, 포인터 중복 제거 |
| r5·r7 | 예 | C-4·거부 표, C-6·A-4 |
| r6 | 예, 거부 표 빠짐(f3) | C-10, D:1397, 미측정 표 |

**작성자가 달리 적은 곳**

- **R2 `:218-226` '실측': 틀렸다.** `grep -n` 작업 트리와 `git show 2ce7021c:…` 모두 220행이 `def model_includes`, 228행이 `return L`이다. 218·219행은 빈 줄이고, 226행에서 끊으면 mismatch include(227행)가 빠진다. 1차 값 `:220-228`이 맞다. 함수 이름을 함께 적어 막지는 않는다(f1).
- **r1 표지 '둘째 커밋 정정' 대 실제 셋째 커밋:** 내 문언이 커밋 순서를 미리 적은 것이다. 작성자가 history에 불일치를 밝혔다. 값 문제는 없다(f2).

### 2. R1~R3 문언 자체 검증

**R1 `source_condition_unresolved`의 멈춤: card 완료 경로를 막지 않고, 막힐 때의 동작도 정해져 있다.**

- 실측: 슬라이스 32행 전부 `top_keys`에 `w_m`, `nf`, `geometry`, `units`, `sign_convention`, `temp_c_from_log`, `corner`, `ngspice`가 있다(`m2_m3_lut_meta.jsonl` 3~34행, 각 32/32). 칸 없음으로 멈출 일은 이 기록상 없다. 옛 측정이고 칸 **값의 뜻**은 미측정이다.
- 멈출 때: 거부 표 '선언 안 씀', A-2 '멈춤(card 미완료, 보고)', P:1393 '멈추고 보고, WB-1 범위 0은 선언 없음 fail-closed'. 다음 소비자가 막히는 것까지 문서에 적혀 있고 조용한 통과가 없다. 전 점이 아니라 한 kind만 빠지는 fail-open은 닫혔다.
- 남는 것: '뜻을 못 정함'의 기준이 없다(f5). 판정자가 산출물로 다시 보므로(A-4) 막지 않는다.

**R2 `model_includes`의 근거: 충분하다. 결합 파일 생성기 값이어도 대조가 값 기준이라 그렇다.**

- 대조는 생성기 동일성을 전제하지 않는다. 시뮬레이션이 읽을 파일의 LF·raw가 그 슬라이스 기록 값에 있는지 본다. 어긋나면 멈춘다(fail-closed).
- 재귀 false stop 없음: 기록은 include 목록을 재귀 없이 적지만, 모델 파일 5개 모두 `.include`·`.lib`가 0이다(`grep -c`, nfet·pfet `tt.pm3`·`mismatch.corner`, `lod.spice`). 재귀로 늘지 않아 ⊆가 그대로 선다.
- 구성 일치: 슬라이스 `n_model_files` nfet 20개 = 3, pfet 12개 = 4(SUMMARY). 목록은 nfet 2, pfet 3이고 남는 것은 `.bins.csv` 하나씩이다(같은 기록의 경로).
- 남는 구멍: ⊆는 '기록에만 있는 파일'이 시뮬레이션 값을 바꾸는 파일이 아님을 보이지 않는다. 지금 기록상 그 파일은 `.bins.csv`뿐이라 실제 발동은 없다. 값 대조 한 줄로 닫을 수 있다(f4).

**R3 numpy 의존: card 안에서 허용되고, 그 판정도 실현 가능하다.**

- interface §1 '표준 라이브러리 제한은 `op1b_lib.py`에만, `vos_recompute.py`는 numpy'. 머리 문장 '표준 라이브러리만'은 test 작성자·모듈 문맥이고 충돌하지 않는다. op1b에는 numpy 금지 잠금이 없다. op7a §5 잠금은 다른 card 폴더다. 옛 오라클·dv5도 numpy를 쓴다.
- 비트 대조 자리 실재: 옛 `:185·:190`과 dv5 `old_166_195`의 식이 같고, `dv5_result.json`에 `sigma_recomputed`·`mean_recomputed`가 있으며 `per_sample_vos`·`V_os_hex`는 스크립트가 쓴다. JSON float는 왕복이 정확하다. dv5 기록 판 `numpy 2.4.6`, `python 3.14.2`와 환경이 달라지면 깨질 수 있어 판 기록을 권한다(f6).
- `sigma_mean` 삭제로 소비자 0 함수가 없어졌다. `vos_samples` 소비자 = `vos_recompute.py`.

**r6 `cap_npz_sha256`:** 값은 여전히 미측정이지만, 엔진 로더가 이미 그 값을 읽어 대조한다(`E/lut/noise_set.py:46`, `mismatch_set.py:54`, 재작성 범위가 아닌 외부 기록 사실 확인용). 그 대조가 통과해 온 기록이면 card에서 멈출 가능성은 낮다.

### 3. 새 모순·toy

- 새 모순 없음. `None` = 같은 거리·NaN으로 좁혀 T-14·T-15와 맞고, '판별된 점 없음' 멈춤과 `source_condition_unresolved`가 구분된다. D §16, 계획 OP-7 행, spec, interface §7이 같은 말을 한다.
- 새 toy 없음. r3으로 T-12a(끝점 36에서 닿음 = 겹침 아님)와 T-12c(공통 길이 14)가 함께 성립한다. r4로 T-7c 기대 포인터 하나가 유일해졌다. T-7 첫 행과 T-7a는 삭제 영향 없음. interface만으로 값이 나온다.
- 줄 인용: D:1900·1919, P:1367·1375·1392·1393 변동 없음(이번 diff는 줄 수를 바꾸지 않은 문장 편집 + history 추가).

### Major

없음. 막는 항목 없음.

### minor(번호만, 막지 않음)

- **f1** `:218-226` → `:220-228`(D:1397 자리, op7a spec C-10, design history v0.4.5의 '실측' 문장).
- **f2** F-18 표지 '둘째 커밋' → '셋째 커밋'.
- **f3** op7a spec 거부 표에 'cap 묶음 값 다름, 결합 세트 bin 꼴 다름 | 선언 안 씀' 한 행.
- **f4** C-10: '기록에만 있는 파일의 값은 F-2·r2 보조 입력 값과 같아야 한다. 다르면 `source_condition_unresolved`.' 이름 규칙 없이 닫는다.
- **f5** '뜻을 못 정함' 예시 한 줄(`units`에 `ID` 항목 없음, `sign_convention`이 부호를 안 정함 등).
- **f6** `vos_recompute.py`가 numpy·python 판을 기록, dv5 기록 판과 다르면 표지.

### 원래 취지와 다름

추가 없음. 앞 표지(X-37, X-R10, X-R11, R3의 함수 목록 변경)는 원문과 맞다. A-53·A-54·A-56·A-57은 위임 결정이고 LA-1 재점검의 사용자 확인 항목이다. 위임 밖 항목 없음.

### 최종 재판정 미측정

ngspice·pytest 실행 전부, 슬라이스 meta 칸 값의 뜻, `cap_npz_sha256` 값, 슬라이스 기록과 include 파일의 sha 대조(경로·개수만 확인), r2 §12.5 근거 (b), numpy와 순수 Python 합산 차이, 593 대 595 사유. 이 항목들이 실행 때 어긋나면 card는 정해진 멈춤으로 간다.

verdict: Major 0
