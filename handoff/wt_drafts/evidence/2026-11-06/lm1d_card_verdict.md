# LM-1d spec·interface card 독립 판정 (card id `20261106-lm1d`)

- 대상: worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261106-lm1d-card`, 브랜치 `card/lm1d`, 커밋 `eb89ca11`(base `dcd54095`). 파일 = `docs/02-design/specs/20261106-lm1d.spec.md`(126줄), `docs/02-design/specs/20261106-lm1d.interface.md`(154줄).
- 판정자 = 독립 agent(card 작성자 아님). 대상 worktree는 수정·커밋하지 않았다(`git status` 깨끗).
- 기준: 계획 v6.38.22 N6.40 LM-1d(같은 worktree plan P:2617~2640), P:1311·1370, 사용자 결정 O-242(`_drafts/user_decisions.md`:1223), 위임 A-129·A-130·A-131(`la1_auto_decisions.md`:135~137), 계획 판정 `lm1_plan_verdict.md` 재판정 r1~r4, CLAUDE.md O-229.
- 방법: `git -C` 읽기, grep·sed·sha256sum·od, 읽기 전용 스크립트 1개(엔진 import 0, ngspice 0, pytest 0) `C:/Users/HSLEE/AppData/Local/Temp/la1s_lm1d_ver22/facts.py` → `facts_out.txt`.

## 결론: Major 1, minor 10, 관찰 2

Major는 글만 고치면 된다(설계 변경 없음). O-229 3에 따라 Major를 고친 뒤 재판정 1회가 필요하다. 재판정은 M-1 문언과 V-6 한 줄만 확인하면 된다.

## 1. 계획 N6.40 LM-1d 대조와 N = 120 재확인

| 계획 | card | 판정 |
|---|---|---|
| 1 조합 = `widths()` 전부(하한 PDK `min_finger_w_m`, A-129 뒤) × 앵커 2개 bin, 승인 중점 목록, 기준 폭도 같은 생성기로 | spec 범위 1·완료 1, interface S1 | 같음. 단 '중점 L = 제조 격자 값'을 확인하는 관문이 없다(m8) |
| 2 앵커를 만든 생성기, 열 ID·GM·VDSAT, sha256·명령·판 기록, 이관은 범위 밖 | spec 범위 2·'생성기 선택 근거'·완료 4 | 같음 |
| 3 git 밖 데이터 + 출처 기록 커밋 `Role: doc`, 위치 선언은 통합 병합 안 | spec 범위 3·완료 6 | 같음. 다만 병합 경로 문언이 틀렸다(M-1) |
| 4 (1) n/N, 실패·결측이면 멈춤(대체 금지) (2) 셀별 대조, 차 > 새 tol_V면 멈춤 (3) 출처 기록 (4) 작성자 ≠ 판정자 | spec 완료 1~5, interface §4·§5·§6 | 같음(빠진 것·더한 것 없음). 대조량 정의 = `id_equivalent`(r1 반영), P:682 용도 줄도 있음(grep으로 확인) |

**N = 120 재확인**(원 파일 직접):

- 하한: `A/sky130_pdk_decl.json`:98 `min_finger_w_m` = periphery_rules `difftap.2`. 원본 `C:/pdk/skywater-pdk/docs/rules/periphery/periphery.csv`:321 값 = 0.420 µm. 원본 sha256 `432c56b9…` = 선언 값.
- 격자: tlef :29 `MANUFACTURINGGRID 0.005`. 따라서 하한 키 = 84이고, nmos 키 72(0.36 µm)·78(0.39 µm)이 빠진다(`E/lut/widths.py`:9~18 `w_key >= round(w_min/grid)`).
- 슬라이스: manifest 32개(nfet 20, pfet 12), 32/32 sha = manifest 값. 하한 이상 = nfet 18 + pfet 12 = 30.
- 앵커 2개 bin: 30/30 슬라이스가 모두 같은 넷이다(meta `model_bin_bounds_per_L`로 묶음). (0.15, 0.18]은 앵커 0.15·0.18, (0.5, 1.0]은 0.7·1.0, (1.0, 2.0]은 1.5·2.0, (2.0, 4.0]은 2.5·4.0이다. 승인 중점 0.165·0.85·1.75·3.25 µm가 bin마다 정확히 하나씩 두 앵커 사이에 든다.
- 결과 N = 120(`facts_out.txt` `N_COMBOS 120`). 작성자 실측과 같다.
- 그 밖의 사실:
  - 축은 32/32 `array_equal`이다(VGS 49·VDS 49·VS 10, 0~1.8 V).
  - 생성기 VS 확장 식(:263~265)이 같은 VS를 낸다(True).
  - 비유한값은 32/32 슬라이스에서 0이다(ID·GM·VDSAT).
  - 모든 슬라이스의 meta가 `generator_sha256` 8df35d2e, ngspice-46, 27.0 °C, tt다.
  - 생성기 raw sha = LF sha = `8df35d2e…19df` = manifest 값이다(CR 0).
  - manifest `ref_npz`는 없다.
  - 옛 중점 파일은 L 4점, `w_ref_m` 5e-6, 축이 슬라이스와 같고, 생성기는 `sky130_lut_sweep.py` 67176017이다.
  - L 격자 파일의 raw sha `33127892…`는 CRLF checkout(`core.autocrlf=true`)에서의 값이고, LF·git blob 값은 `2e2d61f4…`다. cap·옛 중점 meta `L_source.sha256` = raw `33127892`다.

## 2. Major

### M-1 card base·병합 경로가 틀렸다 -- 병합하면 WB-1이 표 #24보다 먼저 master에 들어간다 (계획과 다름·범위 위반 위험)

- interface:4는 '**card base = `dcd54095`**(master)'라고 적었다. spec:49는 '충족(`dcd54095` 병합)', spec:54는 '이 card 산출은 그 전에 master에 들어가도 엔진 동작 0이다'라고 적었다.
- 실측 결과는 다르다.
  - `dcd54095`는 WB-1 브랜치 `role/code/20261104-wb1`의 머리다. 첫 부모가 `3397b834`(A-129)다.
  - `git merge-base --is-ancestor dcd54095 master`는 거짓이다.
  - master `d3782917`의 plan에는 'LM-1d'가 0회 나온다. 계획 v6.38.22가 master에 없다.
  - `master..dcd54095` = 50커밋이고, 엔진 243개 파일이 다르다.
- 스크립트가 쓰는 엔진 API도 WB-1에만 있다. `load_lut_set(..., bin_rule=)`, `gmid_engine.core.file_sha256`, `tests/pdk_min_w.py`가 그렇다(master에는 `bin_rule` 인자와 `core/file_sha256.py`가 없다).
- 그래서 `card/lm1d`를 master에 병합하면 WB-1 커밋 50개가 함께 들어간다. 이것은 표 #24(WB-1 + LM-1e 통합 병합)와 N6.40 'QB 답 전 WB-1 병합 보류'에 어긋난다. spec:54 문장은 사실이 아니다.
- **고칠 방법**:
  - (1) interface:4·spec:8을 'base = WB-1 브랜치 머리 `dcd54095`(계획 v6.38.22가 이 브랜치에 병합됨, master 아님)'로 고친다.
  - (2) spec '절차'의 '→ 병합'에 대상을 적는다. 예: 'WB-1 브랜치(`role/code/20261104-wb1`)에 병합하고, LM-1e base = 그 머리. master에는 WB-1 + LM-1e 통합 병합으로만 들어감'.
  - (3) spec:54의 'master에 들어가도' 문장을 지운다.
  - (4) V-6에 '병합 대상 = WB-1 브랜치'를 확인하는 줄을 더한다.

## 3. minor (고칠 방법)

- **m1 위치 선언 sha 규칙을 잘못 인용했다**(spec:70, interface §4 `file_sha256_lf` = '위치 선언이 대조하는 값 -- `data_location.py:14`').
  - 실제 코드: `files` 항목은 raw sha(`_sha256_of`, `E/lut/data_location.py`:32~34, 대조 :56)로 대조한다. LF 환산(`core.file_sha256`)은 `bin_rule`에만 쓴다(:65·:75).
  - 이진 npz에 CRLF→LF 치환을 적용한 sha는 의미가 없다. 그 값을 선언에 쓰면 통합 병합 때 `lut_location_sha256_mismatch`로 거부된다(fail-closed이지만 쓸데없는 왕복이다).
  - 고칠 방법: 출처 기록에서 선언 값으로 쓸 칸 = raw sha256으로 한다. LF 칸은 지우거나 '참고, 선언 값 아님'으로 표지한다. 인용 줄도 :32~34·:52~56·:75로 바로잡는다.
- **m2 V-4 재실행이 S0-2와 충돌한다.**
  - S0-2는 '`<V>`·`<D>`가 이미 있고 비어 있지 않으면 멈춤'이다. 판정 때는 `<D>`가 반드시 차 있으므로 V-4는 늘 S0에서 멈춘다.
  - 고칠 방법: 비어 있는지 확인하는 대상을 `--out` 폴더로 바꾼다. 그리고 판정 재실행 모드(`<D>` 있음 허용, S2 미실행)를 interface에 적는다.
- **m3 옛 체크포인트를 쓰는지 막는 관문이 없다.**
  - 생성기는 `<work>/ckpt`의 (장치, W, L) 이름 체크포인트를 그대로 재사용한다(:193~198, 진행 로그 'cached'). 키에 축·stub sha가 없다.
  - 고칠 방법: S0에 '`<T>/work` 없음 또는 빈 폴더'를 더한다. G 관문에 '`generation_progress.log`에 `cached` 줄 0, 시간 줄 = N'을 더한다.
- **m4 '새 폴더뿐'을 확인하지 않는다.**
  - spec 완료 6은 'git 밖 변경 = 두 새 폴더뿐'이라고 적었다. 그런데 G-f·V-7은 바뀐 파일·없어진 파일만 본다.
  - 고칠 방법: 실행 뒤 `<root>` 전체 파일 목록에서 새 파일이 `<V>`∪`<D>` 안에만 있는지 관문으로 확인한다.
- **m5 기대 수 18·12·120·784와 V-9(숫자 리터럴 0)의 관계가 정해지지 않았다.**
  - 상수 발명은 아니다. 정의(N = `widths` × 앵커 2개 bin, 셀 = Σ 2·bin 수 × VDS 수)가 데이터에서 나오고, 기대값은 작성 전 실측을 확인하는 장치('다르면 멈춤')다.
  - 하지만 스크립트에 숫자를 박으면 V-9를 어긴다.
  - 고칠 방법: 784는 plan.json으로 계산한다. 18·12·120은 spec 표를 인용하는 실행 인자로 넣거나, 오케스트레이터가 plan.json과 대조하게 한다.
- **m6 LutSpec 출처.**
  - S1-1이 '격자 = tlef'(conftest 정규식 꼴)로 적었다. 그런데 §4는 `pdk_decl.manufacturing_grid_m`을 기록한다.
  - 고칠 방법: 격자를 PDK 선언 역할 이름 `manufacturing_grid_m`(`read_pdk_decl(...).value`)으로 바꾼다(O-197, 출처 하나).
  - 장치↔kind·열 접미사는 conftest:47~48·`tests/generality/pipeline.py`:49~50에 이미 사본이 둘 있는데, 셋째 사본이 생긴다. 원 자리를 명시하고, 정리는 LA-1 재점검 입력으로 넘긴다.
- **m7 선례 인용이 틀렸다.**
  - `.ai/verification/20261104-op23/tools/`는 판정자 산출물이다(커밋 627e5443·b33d7e9f, `Role: audit`).
  - `.ai/verification/20261104-wb1/`은 base에 없다.
  - 작성자 스크립트를 `.ai/verification/<id>/scripts/`에 둔 맞는 선례는 `20261104-op7a/scripts/`(`Role: code`·`test`)와 `20261104-op1b/scripts/`다.
  - 기술자 경로 `tools/spice_oracle/descriptors/...`의 실제 자리는 `skills/analog-gmid-design/tools/spice_oracle/descriptors/lut_file_roles/8df35d2ea405a0f5.lut_file_roles.json`이다.
- **m8 계획 LM-1d 1 '중점 L = 제조 격자 값'을 확인하지 않는다.** S1에 `L_mid / manufacturing_grid_m`이 정수인지 확인하는 관문을 더한다. 실측으로는 4점 모두 정수다(33, 170, 350, 650).
- **m9 L_source raw sha를 ngspice 전에 확인하지 않는다.**
  - 적재(`lut_set.py`:327~334)는 중점 meta `L_source.sha256`이 cap 값(raw `33127892`)과 같기를 요구한다. LF checkout에서 만든 stub은 §5에서야 거부된다(ngspice를 돈 뒤).
  - 고칠 방법: S0에 'L 격자 raw sha = cap `L_source.sha256`, 아니면 멈춤'을 더한다.
- **m10 재실행 권한.**
  - spec 완료 1에는 '다시 돌리려면 보고 뒤 오케스트레이터 결정'이라고 적혀 있다. 그런데 두 번째 ngspice 실행은 O-242 '1회'(사용자 문언) 밖이다.
  - 고칠 방법: 재실행 = 사용자 확인(또는 O-242 범위 해석을 기록한 위임 결정)으로 적는다.

## 4. 작성자 남은 의문 1~7 판정

| # | 판정 | 근거 |
|---|---|---|
| (1) 'ngspice 1회' = 생성 1회(호출 둘, 재실행 없음) | **맞음** | `--widths`는 모든 `--devices`에 같은 목록을 적용하고, kind별 특성화 집합 밖이면 거부한다(:290~295). nmos 18폭과 pmos 12폭은 집합이 달라 한 호출로 정확히 120을 만들 수 없다. `--widths` 없이 한 호출로 돌리면 128조합(하한 아래 8개는 쓰지 않는 데이터)이 되고 manifest가 `<D>`에 써진다(:350). 그래서 계획 1의 '조합 = `widths()` 전부'와 어긋난다. O-242 취지('슬라이스마다 중점 ngspice 1회 생성')는 한 번의 생성 작업이다. 재실행 권한은 m10 |
| (2) 스크립트 셋 = O-229 4 예외 | **맞음(조건부)** | 세 스크립트는 계획 완료 조건 (1)~(3)을 내는 이 card의 산출 수단이다. 재사용 검증 도구·게이트·test 인프라가 아니다. 또 LM-1d → LM-1e → WB-1 → LA-1 사슬이라 LA-1을 막는 일이다. 조건: card 폴더 밖 import·배선 0, test·gate 등록 0, 엔진 식 재구현 0(V-8) |
| (3) manifest `ref_npz` 부재 시 stub 축 출처 | **맞음** | '그 슬라이스의 보간 오차'의 축은 앵커 파일 자신의 축이다. 32/32 축이 같다(실측). 생성기 VS 확장이 같은 VS를 낸다(실측 True). 슬라이스 생성 때 stub을 쓴 선례가 있다(`<root>/REGEN_REPORT.md` §1, `verification/make_axis_stub.py`) |
| (4) L 격자 CRLF sha 둘 | **맞음** | 두 값을 다 남기는 것이 맞다. 적재가 대조하는 값은 raw(checkout 의존)이고 cap meta와 같아야 한다. 이 확인을 ngspice 전으로 당긴다(m9) |
| (5) 재담기 meta 키 | **맞음(명시 보강)** | 적재가 읽는 것은 다음뿐이다(`provenance.py`:44~57·:86~93, `lut_set.py`:324~372). meta는 `L_source`(`sha256` 필수), 배열은 `corner`·`temp_c`(조건)·`L`·`VGS`·`VDS`·`VS`·`w_ref_m`, 열은 `ID`/`GM`/`VDSAT` + 접미사다. interface §5-2에 이 목록을 그대로 적는다. 값 변환 0, 임시 파일 삭제 + sha 기록이라 graph 사본 문제는 없다. `np.savez`의 zip 시각 때문에 `repack_sha256`은 실행마다 달라질 수 있다(V-2 예외 문언은 맞다) |
| (6) 데이터 하위 폴더 | **맞음** | 생성기 파일 이름(:318)이 root의 슬라이스 파일과 같아 root 바로 아래에 쓰면 덮어쓴다. 위치 선언 `_file`(:52~55)은 상대 경로의 하위 폴더를 허용한다(절대 경로·`..`만 금지) |
| (7) 미측정 표지 | **맞음** | spec '안 잼' 목록이 있고, 비용 근거는 'agent 인용'으로 표지했다(인용 파일 `la1s_wb1_rec13/out/qa_ngspice_mid.txt` 존재, RUN `sec 0.5`·`0.4` 확인). 기준 생성기 시간은 '추정'으로 표지했다. 사실 오류는 m1·m7·M-1에만 있다 |

## 5. graph 규칙 (항목 3)

- 대조값은 엔진 정의 함수 출력 그대로다: `midpoint_l_bin_checks(memo, kind, w_key).rows[*].id_equivalent_v`(`E/lut/midpoint_checks.py`:85~), `tol_v_table(memo, kind, w_key).cells[i][k].id_equivalent_v`(`E/lut/tolerance.py`:133~, `TolVCell` `lut_types.py`:347~355). 스크립트가 직접 하는 셈은 |new − old|·비율·짝짓기뿐이다. 이것은 계획이 정의한 대조량이라 엔진 식의 사본이 아니다.
- 두 LutSet·두 memo는 graph 규칙 2에 맞다.
  - memo 키 = `(lut.fp, fn_name) + key`(`lut_memo.py`:149~151)다. 지문에 중점 sha가 들어가므로(`fingerprint.py`:29~30) A·B는 서로 다른 키 공간이다.
  - memo는 LutSet 하나에 묶이므로 한 memo로 옛 값과 새 값을 함께 낼 수 없다. 그래서 둘로 나눈 것은 정본 우회가 아니라 서로 다른 입력 버전이다.
- U-87 임시 폴더도 문제없다.
  - `TableCache.default()`가 `os.environ`으로 폴더를 정하므로(`table_cache.py`:219~221) 환경 변수로 돌릴 수 있다.
  - 디스크 칸 키 = 코드 버전 + 입력 내용 + data_id(중점 sha 포함)다. 그래서 공용 캐시에 넣어도 섞이지는 않는다. 다만 쓰이지 않을 칸이 쌓이므로 임시 폴더로 돌리는 것이 맞다.
  - 결과는 캐시를 거치든 아니든 비트가 같다(`lut_memo.py`:153~158 docstring). 오염 0, 사본 0이다.
- 엔진 자리(필드·cache·sctx)에 남는 것은 0이다. 출처 기록은 reader 0인 출력 전용 문서다.
- 세어 보면: 새 graph 필드 0, 소비자 0인 필드 0, 정본 우회 의심 0, graph 밖 저장 자리 0(임시 재담기 npz·임시 표 캐시는 실행 수명 입력 파일이고 지운다).

## 6. 물리·fail-closed (항목 4)

- 사실 관문은 닫혀 있다.
  - G-a 모델 bin: showmod 경계 4값(W 포함)이 같아야 한다. W 경계에서 ngspice가 아래 bin을 고르는 경우도 같은 경로로 잡힌다.
  - G-b 축·W, G-c 모델 파일 sha·판·온도·corner·nf·m·기하, G-d 비유한, G-e 생성기·stub sha, S0-1 생성기 sha를 본다.
  - 생성기 자체도 오류 줄·showmod·격자·온도/판에서 실패하면 예외로 끝난다(:211~214·:129~131·:229·:313). 실측으로 이 인용 줄들이 맞다.
- 대조 문턱의 멈춤 갈래는 셋이다: 차 > 새 tol_V, 한쪽만 None, 새 tol_V None인데 차가 정의됨. 둘 다 None인 셀은 따로 센다(통과로 세지 않음). fail-open 0이다.
- 남은 틈은 m3(옛 체크포인트)·m4(새 파일)·m9(L_source를 늦게 확인)이고 모두 minor다. 이 셋에서도 잘못된 데이터가 정상으로 기록되는 경로는 (m3) 같은 이름의 다른 설정 체크포인트가 `<T>/work`에 미리 있을 때뿐이다. `<T>`는 역할 고유 새 폴더라 가능성이 낮다. 그래도 관문을 하나 더한다.

## 7. 상수·이름·PDK (항목 5)

- 'N ≠ 120이면 멈춤'의 120은 상수 발명이 아니다. 정의가 데이터에서 나오고(위 1 실측), 기대값은 실측을 확인하는 장치다. 리터럴로 넣을 자리는 m5로 정리한다.
- 멈춤 문턱은 새 tol_V다(새 상수 0). G-a의 상대 1e-12는 생성기 대조 꼴을 그대로 인용한 것이다(같은 showmod 값이라 정확히 같아야 하는 대조).
- 회로 이름은 0이다. PDK 역할 이름은 `min_finger_w_m`(규칙 번호를 card에 쓰지 않음, O-197)이다. 격자도 역할 이름으로 바꾼다(m6). 폭 값은 LUT 데이터 사실로만 나온다.

## 8. 기록 자리 (항목 6)

- `A/lut_v2_midpoints_w.provenance.json`: 경로 5분류(`tools/gates/role_paths.py`:59~66)에 걸리지 않는 자리이고, `tests/structure`에도 assets JSON 규칙이 없다(grep). 위치 선언·bin 규칙 선언 옆이라 맞다. 함수 레지스트리 대상(엔진 함수)이 아니다.
- `.ai/verification/20261106-lm1d/author/`: doc 분류(`.ai/**`)다. 작성자 스크립트를 `.ai/verification/<id>/scripts/`에 둔 선례(op7a·op1b)가 있다. 판정 기록 `.ai/verification/20261106-lm1d.json`과는 파일이 겹치지 않는다. 선례 인용만 고친다(m7).

## 9. 판정 재측정 명령의 충분성 (항목 7)

V-1~V-10은 계획 완료 조건 (1)~(4)와 graph·상수·범위를 덮는다. 보강할 것:

- V-4가 실행될 수 있게 고친다(m2).
- 체크포인트 재사용 0과 시간 줄 = N을 확인하는 줄(m3).
- 새 파일 ⊆ `<V>`∪`<D>`를 확인하는 줄(m4).
- 병합 대상 = WB-1 브랜치를 확인하는 줄(M-1).
- 중점 L이 격자 정수인지 확인하는 줄(m8).

나머지는 충분하다.

## 10. 관찰 (card 결함 아님 -- `la1_auto_decisions.md` 재점검 입력으로)

- **o1 대조 문턱은 한쪽 방향만 본다.**
  - 앵커 2개 bin 앵커 행의 새 tol_V = max(그 셀 LOO 값, 새 중점 값)이다(`tolerance.py` `with_external`). 그래서 새 값 ≥ 옛 값이면 diff ≤ 새 값 ≤ tol_new라 멈추지 않는다.
  - 멈춤은 옛 값 > 새 값 + tol_new(≥ 2·새 값)일 때만 일어난다. 즉 새 생성기가 과소 추정하는 쪽(위험한 쪽)만 잡는다.
  - 이것은 계획 문언(A-131 재점검 입력 m3)대로다. 셀 기록에 old·new가 다 남으니, 부호별 셀 수를 출처 기록에 더하면 나중에 검토하기 쉽다.
- **o2 계획 v6.38.22가 master가 아니라 WB-1 브랜치에 병합되었다**(`dcd54095` 첫 부모 `3397b834`, master에 LM-1d 0회). 원칙 28 'plan → master → integ' 순서와 맞는지 오케스트레이터가 확인한다(card 범위 밖, M-1의 원인).

## 11. 돌린 범위(통과로 세지 않은 것)

- 돌린 것: `git -C` log/show/grep/ls-tree/merge-base, sha256sum, od, grep/sed, `facts.py` 1회(npz meta·축·sha 읽기).
- 안 돌린 것: ngspice, pytest, 엔진 import(`widths`·`load_lut_set`·`tol_v_table` 실제 호출), 새 중점 값, 대조 값, 조합당 시간. N = 120은 엔진 함수가 아니라 엔진 식(`widths.py`:9~18)과 같은 정수 비교를 원 파일 값으로 다시 셈한 결과다. 실행 때 S1이 엔진으로 다시 잰다.
- 프로세스: 내 python은 끝났다. 남은 PID 29736은 다른 agent의 `la1s_wb1_diag19/scripts/d2_pipe.py`라 건드리지 않았다.

## 재판정 (커밋 `e3dde49c`, 2026-11-06)

- 대상: `card/lm1d` `eb89ca11..e3dde49c`(spec 64줄·interface 109줄 변경). `git diff --name-only dcd54095 e3dde49c` = card 두 파일뿐이고, worktree는 깨끗하다.
- 방법: 앞 판정과 같다(`git -C show/diff`·grep, 읽기만). ngspice·pytest·엔진 import는 0이다.

### 결론: **Major 0.** 남은 minor 4건(r1~r4)은 왕복 없이 고쳐도 된다(O-229 3).

### (1) M-1 해소

- spec:8·interface:4가 base = WB-1 브랜치 `role/code/20261104-wb1` 머리 `dcd54095`(master 아님)라고 실측 근거와 함께 적었다. 엔진 API가 WB-1에만 있다는 점도 적었다.
- spec '뒤따름·병합 경로'·'절차'와 interface §7이 병합 대상 = WB-1 브랜치, LM-1e base = 그 병합 뒤 머리, master = WB-1 + LM-1e 통합 병합으로만(QB 답 전 보류)으로 정했다.
- 옛 문장 'master에 들어가도 엔진 동작 0'은 grep 0이다.
- V-6b를 더했다. 표 #24·N6.40 'WB-1 병합 전 항목'과 모순이 없다. → **해소.** 다만 V-6b 측정에 남은 점이 하나 있다(r4).

### (2) minor 반영

| 지적 | 반영 | 판정 |
|---|---|---|
| m1 | `files[].sha256` = raw = 위치 선언 값(`data_location.py:32-34·:56`), 이진 npz의 LF sha 칸 삭제, LF는 `bin_rule`에만(:61-78), `notes.sha256_rule` | 반영 |
| m2 | `--verify` 모드(아래 (3)) | 반영(r1) |
| m3 | S0-5 `--work` 비어 있음, G-h `cached` 0·시간 줄 = N·(장치, W, L) 쌍 = plan | 반영 |
| m4 | G-f·V-7 새 파일 ⊆ `<V>`∪`<D>`, 완료 6 문언 | 반영 |
| m5 | `--expect`, 셀 기대 = plan.json `n_cells_expected` | 반영(아래 (3), r3) |
| m6 | 격자 = PDK 선언 `manufacturing_grid_m`(`read_pdk_decl(...).value`), 장치↔kind = conftest:47-48 인용 + 셋째 사본 표지·LA-1 재점검, `device_kinds_source` 칸 | 반영 |
| m7 | `<SC>` = `.ai/verification/20261106-lm1d/scripts/`, 선례 op7a·op1b, op23 인용 철회, 기술자 경로 정정 | 반영 |
| m8 | S1-3·G-b 중점 L 격자 정수 관문, plan `L_mid_grid_int` | 반영(r2) |
| m9 | S0-6 L 격자 raw sha = cap `L_source.sha256`(ngspice 전) | 반영 |
| m10 | 재실행 = 사용자 확인 뒤(완료 1, S2, 거부 표, 원래 취지와 다름 1) | 반영 |
| o1 | 부호별 셀 수 `n_new_gt_old`·`n_new_lt_old`·`n_equal`(판정 기준 아님, 기록) | 반영 |

### (3) 새 문언의 결함 점검

- **`--verify` 모드는 fail-open이 아니다(조건부).**
  - 이 모드는 판정 재실행 V-4 전용이다. 하는 일은 S0 기록·S1 조합 계획을 판정 폴더에 다시 쓰는 것뿐이다. 생성(S2)은 원래 `plan_midpoints.py` 밖의 별도 명령이고, 판정자는 ngspice를 돌리지 않는다(V 표).
  - 그래서 '판정에서 S2를 건너뛴다'는 것은 정의상 맞다. 판정 증거의 근거는 V-1(파일 sha)·V-3(관문 재실행)·V-5(npz 직접 표본)이고, 이들은 그대로 돈다.
  - 건너뛰는 검사도 생성 쪽 빈 폴더 검사(S0-2 `<V>`·`<D>`, S0-5 `--work`)뿐이다. S0-1·S0-6·S1의 모든 멈춤은 그대로 남는다.
  - 남은 틈(**r1**): `--verify`로 만든 plan.json으로 S2·`record_midpoints.py`를 돌리는 것을 막는 표지가 없다. 이렇게 돌리면 S0-5(옛 체크포인트)를 건너뛴 채 생성할 수 있다. 다만 G-h(`cached` 0)와 G-f가 뒤에서 잡으므로 잘못된 기록까지 가는 경로는 없다.
  - r1 고칠 방법: plan.json에 `mode`를 쓰고, `record_midpoints.py`가 `mode = verify`인 plan을 거부한다(S2 명령 문단에 '생성 모드 plan만'을 적는다).
- **`--expect`는 상수를 박는 꼴만 바꾼 것이 아니다.**
  - N·셀 수의 정의는 데이터에서 셈한다(`widths` × 앵커 2개 bin, Σ bin 수 × 2 × VDS 수). 기대값은 어떤 값도 만들지 않고, 결과를 바꾸지도 않으며, 다르면 멈추기만 한다. 판정을 받은 card의 실측 표와 실행 때 사실이 같다는 것을 확인하는 장치다(card 머리 '미측정 사실이 다르면 멈춤').
  - 그러니 물리 경계나 판정 문턱이 아니고, 상수 발명이 아니다. 인자로 옮긴 실익은 출처(spec 표)가 명령줄 기록에 남는다는 점이다. 스크립트 수정 없이 기대를 바꾸려면 card를 고쳐야 한다는 점도 같다.
  - 남은 점(**r3**): plan.json·출처 기록에 `--expect` 값과 출처('spec 작성 전 실측 표')를 남기는 칸이 없다. `commands`에는 S2만 들어간다. 이 칸을 더한다.
- **스크립트 자리 이동(m7)에는 충돌이 없다.**
  - `.ai/**` = doc 분류(`role_paths.py`:65)이고, 작성자 스크립트를 `<id>/scripts/`에 둔 선례가 둘 있다(op7a `Role: code`·`test`, op1b).
  - 판정 기록 `.ai/verification/20261106-lm1d.json`·판정자 부속 파일(`base_check.json` 등)과 파일 이름이 겹치지 않는다.
  - interface §1·§2·§4·§5·§7·V-6의 `<SC>` 표기가 모두 바뀌었다(`author/` 표기 grep 0).
- **격자 정수 관문(m8)**(**r2**):
  - '정수 판정 = `round`와 같음'이 실제 비교 식을 정하지 않는다. 0.85 µm·1e-6 = `8.499999999999999e-07`(옛 중점 파일 실측 값)이라 `L == round(L/grid)·grid`처럼 float로 같은지 비교하면 거짓이 나와 거짓 멈춤이 생긴다(fail-closed이지만 쓸데없는 멈춤).
  - 허용 오차를 새로 두는 것도 상수 발명이 된다.
  - 고칠 방법: 승인 목록 µm 값을 격자 µm로 나눈 값에 생성기와 같은 `round(·, 6)`을 적용한 뒤 정수 여부를 보는 꼴로 명시한다. 같은 단위 환산 꼴을 인용하므로 새 상수는 0이다.
- **V-6b 측정**(**r4**):
  - `git merge-base --is-ancestor dcd54095 card/lm1d`는 '분기점'만 보여 준다. '병합 대상'은 판정 시점에 잴 수 없다(오케스트레이터 계획 문언 확인뿐).
  - 고칠 방법: 병합 뒤 확인을 한 줄 더한다. 예: 병합 직후 `git merge-base --is-ancestor <card/lm1d 머리> role/code/20261104-wb1` 참, `... master` 거짓(통합 병합 전까지). 판정 기록에는 '병합 전 판정 = 계획 문언 확인'으로 적는다.
- 그 밖의 새 graph·물리·fail-open·상수·회로 이름·범위 결함은 0이다.
  - 격자를 PDK 선언에서 읽게 바뀌어 출처가 하나가 되었다. 값은 tlef MANUFACTURINGGRID 0.005 µm와 같은 원본이다(선언 `tech_lef` 출처).
  - 부호별 셈은 기록 전용이라 판정 기준이 바뀌지 않았다(계획 문언 그대로).

### 남은 minor (LA-1 재점검 입력으로 넘겨도 됨)

- **r1** `--verify` plan 표지·record 거부.
- **r2** 격자 정수 비교 식 명시.
- **r3** `--expect` 값·출처 기록 칸.
- **r4** V-6b 병합 뒤 확인 줄.

### 재지 않은 것(통과로 세지 않음)

앞 절 11과 같다. 이번에 더 잰 것은 없다(문언 대조만).
