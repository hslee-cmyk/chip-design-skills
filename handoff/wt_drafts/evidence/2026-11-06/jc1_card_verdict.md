verdict: Major 1

# JC-1 spec·interface card 독립 판정 (판정자 ≠ 작성자)

- 대상: worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261106-jc1-spec`, 브랜치 `card/jc1`, 커밋 `b1b3d305`(기점 `e884a2ab`). `docs/02-design/specs/20261106-jc1.spec.md`(341줄)·`20261106-jc1.interface.md`(203줄).
- 정본 대조: 계획 N6.42(plan.md :2686-2705), design 40 §3.8 10 (i)~(ix)(:1354-1377), design 42 '91 접합 용량' 행(:141 OK 조건 (1)~(8)), 위임 A-155·A-156(`la1_auto_decisions.md` :243-261), design 검증 재검증 2 s-m1~s-m3.
- 원본: Jespers & Murmann 2017 3장(로컬 `skills/analog-gmid-design/references/gmid_sources/jespers_murmann_2017/extracted/3 basic-sizing-using-the-gmid-methodology.pdf`, `pdftotext`로 추출) -- 112쪽 `Cdd = W.*lookup(nch,'CDD_W',…)`, `Cdb = Cdd-Cgd`; 90-91쪽 'Cdd = Cdb + Cgd'(그림 3.21).
- 측정 스크립트(읽기 전용, `C:/Users/HSLEE/AppData/Local/Temp/la1s_jc1v2/`): `grepcount.py`(→ `grepcount_e884a2ab.txt`), `cover.py`(→ `cover_out.txt`), `showlines.py`(→ `show_out.txt`), `rc.py`(→ `rc_out.txt`), `o197.py`(→ `o197_out.txt`), `dump.py`. 엔진 import·실행 0, test 0, ngspice 0, 저장소 수정 0.

## 1. card ↔ 계획·design gap

| 기준 | card 자리 | 판정 |
|---|---|---|
| 계획 완료 (1) 정의 toy 세 경우 + base red | spec 완료 1, J-1·J-2, D-a·D-a2·D-b·D-c·D-d | 담음 |
| (2) 수동성 기록 | 완료 2, A-5 | 담음 |
| (3) 상수 0 | J-11(VGS 인자 = 축 첫 값 0.25), J-12, 규칙 D | 담음(minor m6) |
| (4) O-197 | N-1~N-3 | 담음(minor m4 사실 문장) |
| (5) 분류 표 | 80행 | 담음(아래 재측정) |
| (6) graph | G-1~G-5 | 담음(minor m2 계수 방법) |
| (7) 변화표 + 오염 구간 소자 수와 L | 완료 7, A-6 | 담음 |
| (8) fail-closed(VGS 축·C 열·w_ref_m·음수·NaN·MNA 미도달) | J-3~J-10, D-e~D-g, S-2·S-3, X-1~X-7, `lut_cap_width_unresolved` 인용 | 담음 |
| (10) 분해능 소속 (a)(b)(c) + 폐형식 문언 0 | R-a·R-b·R-c | 새 toy는 담음. **기존 test 기대식이 공통 ε_d로 cdb·csb Δ를 단언하게 되는 경로 -- M1** |
| design (i) 1~5 계산 순서 | interface §1 1~5 | 같음(문언 그대로) |
| (ii) READS·`_query` 갈림·불변식 | §3, 원래 취지와 다름 7, A-12 | 같음 |
| (iii) `JunctionSource`·S0 정지 | §2 | 같음(`lut_cap_kind_undeclared` 안전망은 spec 범위 2에만 -- 도달 불가라 toy 없음, 문제 아님) |
| (iv) 삭제·교체 자리 | W1~W23 | 같음(W20·W21은 card 추가 -- 아래 4 (e)) |
| (v) ①~⑫ | 분류 표 근거 번호 + card ⑬⑭ | 확인(4 (e)) |
| (vi)(vii)(ix) | 범위 5, 분류 표, '정의 축 기록' | 같음 |
| (viii) test 꼴 | 완료 1~12 | 같음(정의 toy를 이진 소수 대신 '같은 연산 순서 + 마디 조회 + 전제 C-0'로 바꿈 -- 아래 2에서 확인, 비트 동일 성립) |
| D42 OK 조건 (1)~(8) | 관찰 계약 1~11 | 전부 대응 |

재작성 범위 표본 대조(base `e884a2ab` `git show`, `show_out.txt`): W1(:23 `_PREFIX`, :26 `_PERMODS`, :37-88 `JunctionParams`(데코레이터 :83, `from_pdk_decl` :84-87), :119-124 `JunctionCaps`, :127-148, :150-171), W2(:12, :19-25, :28-36, :38-40), W3(:18-19), W4(:178), W5(:36·:38·:41·:46-47·:50-56·:71-89·:80-81·:92-97·:106·:115), W6(:17-18), W7(:28), W8(:95·:257·:258·:340), W9(:682-686·:797), W10(:5-7·:22·:48 순회 하나), W11(:8-10), W12(:183/:184·:288/:290·:344/:346·:404), W13(mismatch :66/:71, noise :58/:63, except 블록 :52-60·:42-50 밖), W17(:10·:14), W19(contract_output :321·:323, diffusion :13-14), W20(realized_geometry :7·:9), W21(smoke :8), W22(:5, tnom :253-257·:388-392, `junction_` 키 54) -- **전부 일치(24자리 이상)**.

분류 표 재측정(`grepcount.py`, Python subprocess로 `git grep -n -I -i -E "junction|접합"`): 엔진 소스 32파일 182줄, 엔진 CONTRACT 7파일 99줄, PDK 선언 1파일 103줄, LUT 생성 규칙 선언 1파일 1줄, oracle 소스 4파일 11줄, oracle .md 8파일 19줄, 엔진 test 37파일 477줄, oracle test 2파일 16줄, assets 다른 파일 5파일 6줄 + 이진 1파일(`offset_trim__kay_2024/paper.md`), references 8파일 16줄, legacy 4파일 18줄 -- card와 같음. `cover.py`: 표 행 = **80**(card와 같음), 숫자 열 행의 줄 대조에서 빠짐·남음·중복 0; 차이는 묶음 행뿐(PDK 96줄 범위 행 -- 빠진 96줄 모두 :133-251·:258-266·:268-386·:393-401 안, `*.compare.md` 7파일 각 :9, 논문 2파일 3줄, references·legacy) -- 의도된 묶음.

## 2. toy 계약이 소스 없이 쓸 수 있는가 + 정의 식 물리

- **물리**: Cdb = (CDD − CGD)·r_d, Csb = (CSS − CGS)·r_s는 원본 112쪽 `Cdb = Cdd-Cgd`(폭 정규화 열 × W)와 90-91쪽 Cdd = Cdb + Cgd의 정의와 맞다. 원본은 켜진 점 조회이고 card는 VGS 최소 조회(사용자 결정 O-249/DEC-107, 긴 L·VDS ≈ 0 오염은 design·완료 (7) 기록으로 둠) -- 물리 정합 위반 아님. r: 레이아웃 전 (ad_per_w·W)/(ad_per_w·w_ref) = W/w_ref(그 평가가 쓴 W, `off` = 선언 `w_m`), 레이아웃 뒤 (ad_m2·m)/AD_ref -- `realized_geometry.py:21`이 `m = n_fingers`, 손가락 평균 면적이라 AD = ad_m2·m이 소자 전체 면적. 맞음.
- **비트 동일 성립 근거(실측)**: `cap_query.py:44-45` 비례는 `v * (W / w_ref_m)`라 W = `reference.finger_w_m` = w_ref면 배율 정확히 1.0, 마디 조회는 표 값 그대로(전제 C-0이 막음). memo 키 = (kind, lo, hi, l_val, vgs, vds, vsb, W)(:52)라 같은 (kind, L, VDS, VSB) 접합 조회는 소자 폭과 무관하게 적중 -- G-2 성립.
- **입력 꼴**: `ToyBuild`·`toy_cap_arrays`·`TOY_L/VDS/VS`·`MismatchToy`·`NoiseToy`·`mid_toy_arrays`(base에 이미 있음 -- conftest :1681)·`circuit12`·`mos_t`·`LUT_P` 모두 base test 쪽에 실재(`tests/lut/conftest.py`, `tests/metrics/conftest.py`). toy C는 `TOY_VGS`(0, 0.5, 1.0)를 (0.25, 0.5, 1.0)로 바꾸므로 test 작성자가 r5 닫힌 식(conftest :101-127, 공개 상수)을 새 격자에서 다시 계산해야 한다 -- 가능, 적재 실패는 C-0·D-0 전제로 멈춤.
- **base red 이유**: J(ImportError), S(서명), D-a(BSIM4 값), D-a2(`realized_finger_missing`), D-e~D-g(정지 없음), X(`npz_grids` :10 분류 안 된 `KeyError` -- mismatch·noise는 except 블록 밖이라 그대로 KeyError, 실측), R-a·R-b(목록에 없음), R-c(실측 HIT 3줄: `lut_parameters.py:6`, metrics CONTRACT :941·:1054), N-3(54키 실측) -- 모두 타당.

## 3. 공통 ε_d 점검

- 새 toy 45 id(J·S·D·G·X·R·N + 전제 C-0·D-0·X-0): 공통 ε_d를 규칙 근거·기대값·toy 식에 쓰지 않음. R-b는 존재·유한·≥ 0·B₈ > B₆만 단언, §6 '단언 금지'에 Δ 값·Δ/|p|·열 사이 비·B₈ − B₆ 크기. **새 toy는 통과**.
- R-b 경로 판정 가능성: base `lut_parameters.py:48`이 `for name in LUT_PARAMETERS:`(호출 때 모듈 전역)라 monkeypatch로 '항 없는 경로'가 같은 빌드에서 선다. 엄격 부등식은 `resolution.py` 머리 문서 `value = max(lut, numeric)` 때문에 `value`로 비교하면 numeric이 클 때 같아질 수 있다(거짓 red 쪽 -- fail-open 아님) → minor m1.

### M1 (Major -- 공통 ε_d가 기존 test의 새 기대값에 들어가는 경로, 계약 자기모순)

- 사실(base 실측): `tests/metrics/test_lut_parameters.py:55-66` `test_all_six_parameters_and_negative_capacitance_magnitude`는 `ps.delta == [eps[k]*abs(p) for k, nm in lut_params_of(...)]`를 단언하고, `lut_params_of`(conftest :1092-1094)는 `LUT_P`를 돈다. `tests/metrics/test_resolution.py:315-327` `_expected_lut`은 `Σ|∂q/∂p|·eps[k]·|p|`를 6열 고정 tuple로 계산한다. `MILLER_V_MOS`·`EX7V_MOS`(cdb = 0.05e-12)는 cdb ≠ 0이다.
- interface §8은 `LUT_P`를 8열로 바꾸고 '이 파일들의 Δ 기대식은 과도기 as-built 꼴이고 RS-1이 다시 쓴다 -- JC-1은 그 식을 새 기대의 근거로 쓰지 않는다'고 적는다. 그러나 LUT_P가 8열이 되면 위 test는 (d, cdb)·(d, csb)의 Δ를 `eps·|cdb|`·`eps·|csb|`로 **새로** 단언하게 되고, `test_resolution`은 엔진 lut 몫이 커져 6열 기대와 어긋나므로 기대에 `eps·|cdb|` 항을 더하는 것 말고는 green이 될 길이 card에 없다. 이는 §6 '단언 금지(Δ 값 그 자체, Δ/|p|)'·완료 (10)(c)·계획 v6.38.30(A-151·A-152가 'Δ = ε_d·|cdb| 손계산'을 철회)과 모순이고, 판정 기준 3('공통 ε_d가 기대값에 쓰이면 Major')에 해당한다.
- 고칠 것(interface §8·spec 원래 취지와 다름 10 문언): 기존 test에서 cdb·csb 항은 (a) 피검 함수가 `lut_parameters`인 test(`test_lut_parameters.py`)에서는 존재·유한·≥ 0만 단언하고 6열 ε·|p| 단언은 기존 6열 원소로 한정(기존 as-built 회귀, RS-1 몫 -- 넓히지 않음) (b) 피검 함수가 분해능·감도인 test(`test_resolution.py`·`test_sensitivity.py`·`test__helpers_dc.py`)에서는 Δ를 **입력 `ParameterSet.delta`**에서 읽어 Σ|∂q/∂p|·Δp를 만든다(입력 값이므로 피검 함수로 기대값을 만드는 것이 아님) -- 어느 쪽도 cdb·csb Δ를 ε_d 꼴로 단언하지 않는다. '열 목록 밖 기대 변화면 멈춤' 문언과 `_expected_lut`의 6열 고정 tuple이 부딪히는 점도 같은 문언으로 정리한다.

## 4. 작성자 의문 판정

- (a) **X-7 조건부**: 받아들인다(fail-closed -- 전제가 안 서면 멈추고 보고). 다만 card 자신의 graph 규칙 '축 키 판정 = `npz_grids` 하나(호출 자리마다 둘째 검사 0)'에 따르면 LM-1e G1c가 `npz["L"]`을 축 helper 앞에서 직접 읽는 것은 둘째 축 키 읽기이므로, 기본 처리는 'JC-1이 그 자리에서 `npz_grids`를 먼저 부르게 순서를 맞춘다(같은 파일 :344 자리, W12 범위)'로 적는 편이 맞다 -- '범위 밖'이 아니다. minor m8.
- (b) **S0 기준선 `junction_content`**: 기준 약화 아님 -- 정의 교체에 따른 기준선 갱신이고 card가 정한 변화다(계획 범위 2가 `params`·PDK sha 지문 성분을 지움, design (iii)). 조건(card에 이미 있거나 보강): Role: test 커밋(코드 커밋과 분리), 기대 = LUT 생성 규칙 선언 × LUT 데이터의 `w_ref_m`(피검 `from_decls`·`from_lut_rule` 미사용), 9회로 모두 값 단언 유지, `temp_c_hex` 유지, 지운 단언은 `RETIRED_TESTS_jc1.md`에 `covered_by`. 보강 권고: fixture `junction_content` 키(`params_fp`·`pdk_decl_sha256`) 처분과 test 이름('unchanged_from_base')을 명시 -- minor m9.
- (c) **기존 분해능 test 기대 목록 변화**: 열 목록만 계약 사본을 따르는 것은 맞다. 그러나 지금 문언으로는 과도기 식이 cdb·csb 기대에 새로 들어간다 -- M1.
- (d) **관찰 지점 제약**: 정당한 계약이다. `junction_cap.caps` 모듈 전역 이름은 design (i) 3이 `caps(…)`를 부르는 자연 꼴이고(J-11 '상수 0' 판정의 유일한 비침습 관찰 수단), `LUT_PARAMETERS` 호출 때 읽기는 base 순회(:48) 그대로이며 design (viii)(10)(b)가 '항 없는 경로 = `LUT_PARAMETERS`만 옛 6열로 둔 경로'로 정의한 것을 실현하는 유일한 test 쪽 치환 자리다(대안 = test 전용 인자 → 엔진 API 오염, 더 나쁨). `ss_evaluate.ss_circuit_field`도 base 전역(:52). 엔진 구조를 test 편의로 새로 묶는 것이 아니다(원칙 8 위반 아님). 이름을 바꾸면 얼린 test가 깨지므로 '바꾸면 같은 커밋에서 표 갱신'은 사실상 이름 고정이다 -- interface 계약으로 받아들임.
- (e) **원래 취지와 다름(card 몫)**: 5(축 키 관문 범위 -- A-156 s-m1 그대로, 받아들임), 6(detail `axis` 칸 -- 실측: 비test 엔진·oracle에 `*_axes_mismatch` detail 소비자 0, `"axis"` 키 읽기 0 → 받아들임), 8(분류 card 몫 -- design (v) ③이 `realized_geometry.py:7·15·21`을 유지로 적었으나 :15·:21은 `junction|접합` 줄이 아니고(import·생성자), :7·:9 문언은 DEC-91 (2)(3) 뒤 거짓이 됨 → card의 재배선(문언)이 design (vii) 정의 '설명 사실이 바뀌는 자리'와 맞음. ⑬⑭ 추가도 해당 줄 실측과 맞음. 받아들임, design (v) ③·⑧ 줄 포인터 정정은 LA-1 재점검 입력 -- minor m7), 9(받아들임, (b)), 10(M1).

## 5. 원칙 점검

| 항목 | 판정(근거) |
|---|---|
| 물리 정합 | 맞음(2절, 원본 112쪽). minor m3: toy F의 CGG = (16 + …)는 전하 보존 항등식 CGG = CGS + CGD + CGB(= (6 + l + 2g + d + s)·1e-16)와 10e-16 어긋남 -- 접합 식은 CGG를 읽지 않지만 `SsDevice.cgg`에 실리는 물리 불일치 toy. CGG = 세 열의 합으로 두기를 권고 |
| graph 단일 정본 | 위반 없음: writer `ss_dev` 하나·새 필드 0·`junction_source` 칸 내용만 바뀜·VGS 최소 조회 = 기존 `caps` memo point 영역(키에 W = w_ref, 실측 :52)·1-D 표·새 cache·사본 0·식 정의 1곳·`dc_finger` READS 삭제(재사용 증가) |
| fail-closed | 음수·NaN `not (v >= 0)`, 열 결손 셋, 기준 면적 0, 축 키 결손 여섯 자리, `_query` 불변식 A-12(실측 `lut/` 비test `devices=` 0건). fail-open 없음 |
| 상수 발명 0 | VGS = 축 첫 값(J-11), 관문 = 부호 0, 경계·보정 0 |
| O-197 | 맞음. minor m4: 착수 실측 ':71 O-197 정규식 = junction_cap.py 44줄만, 다른 파일 0'은 BSIM 하위 패턴만의 수다 -- 정규식 전체(N-1·D40 (viii)(4))로는 74줄 5파일(junction_cap 58·junction_source 8·ss_linearize 4·`metrics/__init__` 3·`_module_map` 1, `o197_out.txt`). 나머지 30줄은 모두 W2·W5·W8·W9 삭제 자리라 N-1 = 0은 달성 가능 -- 사실 문장만 고침 |
| 회로 이름 0 | 규칙 문언 0(회로 이름은 test 선택에만) |
| 만들면 배선 | `junction_at_vgs_min` → `ss_dev`(지금), LA-1 둘째 소비자; `reference` → `ss_dev`; 축 키 관문 → 여섯 호출 자리 |
| O-229 범위 | 맞음. `sizing/test_s2_values.py`를 범위에 더한 것은 CLAUDE.md O-229 2 목록 밖이지만 넓히는 쪽(약화 아님) -- 기록 |

## 6. minor(왕복 없음 -- `la1_auto_decisions.md` 입력)

- m1 R-b: 비교 대상을 `Resolution.lut`(LUT 몫)로 명시하거나 전제 'lut₆ > numeric'를 둔다(`value = max(lut, numeric)`). metric은 cdb·csb 감도가 0이 아닌 필드(ugf·gbw·PM -- gain_db는 용량 감도 0)로 한정.
- m2 G-2: `LutMemo.stats()`는 영역 합계(`lut_memo.py:40-57`)라 'caps' 이름별 miss를 따로 못 센다. 통과 spy(`junction_cap.caps`) 안에서 원 호출 앞뒤 `memo.stats().misses` 차를 기록하는 방법을 적고, M3(W = 1e-6 = w_ref)의 켜진 점 VGS가 0.25가 되지 않게(키 충돌) 적는다.
- m3 toy F CGG 전하 보존(5절).
- m4 착수 실측 O-197 문장(5절).
- m5 정의 toy 비트 동일: 손 식의 `a`·`b`·`pd_extra`는 리터럴이 아니라 toy 선언을 `read_pdk_decl`로 읽은 값을 쓴다고 적는다(단위 환산이 끼면 리터럴과 비트가 다를 수 있음).
- m6 J-12는 VDS = 축[0](0.5)이라 '축 데이터 기준 첫 칸' 동치류로는 맞다. design (viii)(3) 문언 'VDS = 0 열'과 맞추려면 toy VDS 축에 0 마디를 두는 선택지 -- 필수 아님.
- m7 design (v) ③(`realized_geometry.py:7·15·21`)·⑧ 줄 포인터 정정 → design 이력.
- m8 X-7 기본 처리(4 (a)).
- m9 S0 기준선 fixture 키·test 이름 처분(4 (b)).
- m10 interface 45 id 셈의 'X 7(X-0 전제)' 표기: X-1~X-7 = 7, X-0 별도 1이어야 합 45 -- 문언 정리.

## 7. 돌린 범위

읽기·`git -C … show/grep/log/diff`·읽기 전용 Python 스크립트(위 경로)·`pdftotext`(원본 3장). test 0, ngspice 0, 엔진 import 0. 안 잰 것: LM-1e 병합본(X-4·X-7 전제, :344·:404 줄), 2회로 값 변화, 통합 병합 base 재측정(착수 조건 6).

## 8. 재판정 조건

M1을 interface §8(과 spec 원래 취지와 다름 10) 문언으로 고친 뒤 그 부분만 재판정. 그 밖은 minor.

## 재판정

re-verdict: Major 0

- 대상: 같은 worktree 둘째 커밋 `4b369d4d`(부모 `b1b3d305`), `git -C <wt> diff b1b3d305 4b369d4d`(interface +8/-6, spec +9/-7). 처리 = A-157. 범위 = M1 + 함께 고친 m1·m3·m5·m8 + 새 모순. 읽기 전용(`rediff.txt`·`rediff_w.txt`, base test 파일 `git` 작업 트리 읽기), test 0, ngspice 0.

### M1 -- 해소

- interface §8이 두 행으로 나뉘었다. (a) 피검 함수 = `lut_parameters`(`test_lut_parameters.py`): (d, cdb)·(d, csb)의 `delta`는 존재·유한·≥ 0만 단언하고, `delta == eps·|p|`는 기존 6열 원소로만 한정. (b) 피검 함수 = 분해능·감도(`test_resolution.py`·`test_sensitivity.py`·`test__helpers_dc.py`): Σ|∂q/∂p|·Δp의 Δp는 입력 `ParameterSet.delta`에서 읽고, `_expected_lut`(:315-327)의 6열 고정 tuple·`eps·|p|`를 그 꼴로 바꿈. spec 원래 취지와 다름 10 같은 문언.
- **판정 가능한가(base test 실측)**: `_expected_lut`은 이름마다 `perturbed(mos, k, name, 1 ± FD_H)` 중심 차분을 쓰고 `MOS_IX`에 cdb·csb(10·11)가 이미 있어, `ParameterSet.params`를 돌며 `delta`를 곱하는 꼴로 바로 바뀐다. 이를 쓰는 test는 `MILLER_V_MOS`(cdb 2e-15·4e-15, csb 1e-15)·`EX7V_MOS`(cdb 0.05e-12)뿐이고, 폐형식 test(`closed_ex7_resolution`·`closed_ex8`)는 `EX7_MOS12`(cdb = csb = 0)라 기대 변화 0. `test_sensitivity`·`test__helpers_dc`는 `d_param`(∂V/∂p) 중심 차분 대조라 Δ를 쓰지 않는다 -- cdb·csb 행은 열 목록(`lut_params_of`)만 따라 늘어난다. 공통 ε_d가 cdb·csb 기대값에 드는 길 0.
- **기준 약화가 아닌가**: 6열 `eps·|p|` 단언의 원소·강도는 그대로다. 없어지는 단언은 '`cdb`·`csb`는 파라미터가 아니다' 하나이고, 이는 계획 N6.42 범위 4가 바꾸는 정의(목록 소속) 그 자체다 -- 정의 교체이지 약화가 아니다. 분해능 test에서 Δ를 입력으로 읽는 것은 피검 함수(`metric_resolutions`)의 기대를 피검 함수로 만드는 것이 아니고(Δ는 그 함수의 입력), Δ 값 자체의 6열 정확성은 (a)가 계속 덮는다.
- 관찰(minor 아님): `test_r3_doubling_epsilon_doubles_resolution_exactly`(miller)·`test_r3_per_mos_share`는 cdb·csb 행을 새로 포함하게 되어 'Δ가 소자 rel_tol에 선형'을 함께 덮는다. 이 성질은 as-built 꼴과 DEC-105 (8) 꼴(Δp = |∂ln p/∂VGS|·tol_V·|p|) 모두에서 참이라 공통 ε_d 고유 단언이 아니다. 다만 `test_r3_per_mos_share`의 `P = 12`(허용오차 계수, 2 MOS × 6열)는 8열에서 15가 된다 -- 열 목록을 따르는 갱신이며 §8 (b)의 '이 바꿈 밖 기대 변화' 경계에 걸리지 않게 test 작성자가 기록할 것(LA-1 재점검 입력 수준).

### m1 -- 해소, 새 minor rm1

- R-b·완료 10 (b)가 `Resolution.lut` 비교·대상 ugf·gbw·PM·gain_db 제외를 명시. 해소.
- **rm1(새 minor)**: PM을 '모든 대상 metric마다 B₈ > B₆'에 넣은 것은 toy에 따라 서지 않는다. 단일 극 루프의 PM은 용량과 무관하다(base `test_resolution.py:110-123` 예 7 폐형식 PM 몫 = degrees(2ε/√(t0² − 1)) -- C가 없음; ω_u/ω_p = √(T0² − 1)). R-b toy는 소스 노드(csb, 소스 저항)가 둘째 극을 만들어 대개 감도 ≠ 0이지만 card 문언 'C 하나 극점'과 겹치면 PM의 접합 몫이 0 또는 반올림 이하가 될 수 있다(거짓 red 쪽 -- fail-open 아님). 문언을 '대상 = ugf·gbw, PM은 그 toy에서 접합 감도 ≠ 0을 전제 단언으로 먼저 확인한 경우'로 두기를 권고.

### m3 -- 해소

CGG = (6 + l + 2g + d + s)·1e-16 = CGD (2 + g + d) + CGS (3 + g + s) + CGB (1 + l) -- 항등식 성립(손 확인). 접합 손 식(CDD − CGD, CSS − CGS)·양수 확인 문장은 바뀌지 않음.

### m5 -- 해소

손 식 계수 = toy 선언을 `read_pdk_decl`로 읽은 `decl.values((…4 키…))` 값, §1~§3 전부 적용. `from_lut_rule`(base `junction_cap.py:114-116`)과 같은 키·같은 곱 순서라 비트 동일 전제가 선다.

### m8 -- 해소(조건 표지 있음)

- X-7이 조건부에서 code 계약으로 바뀜: 중점 파일 축 키를 `npz_grids(…, reason="lut_midpoints_axes_mismatch", path=…)`가 처음 읽게 순서를 맞춘다(W12, interface §5, 완료 8, '이 card에 없는 것'에서 LM-1e 몫 항목 삭제, '안 잼' 갱신). G1c 자리 미확정 표지 있음('LM-1e 병합본에서 다시 잰다', `lut_set.py:344` 또는 `lut_provenance` 쪽).
- LM-1e 병합본과의 맞물림: 순서 변경이 바꾸는 입력은 `L` 키가 없어 지금 분류 안 된 `KeyError`로 멈추던 파일뿐이라 받아들이던 파일·LM-1e G0~G5 판정 값은 불변(LM-1e 관문 판정과 충돌 0). 사유는 그 자리 기존 사유 그대로라 새 사유 0, 축 키 판정 helper 하나 규칙과 맞음. 착수 조건 5(통합 병합 뒤 code)·6(base 재측정)이 이 자리를 덮는다.
- **rm2(새 minor)**: G1c가 `lut_provenance` 쪽이면 JC-1이 W12 표의 파일 칸(`lut/lut_set.py`) 밖 파일을 고치게 된다. 재작성 범위 W12(또는 W13 옆 행)의 파일 칸과 spec '원래 취지와 다름' 5(축 키 관문 범위)에 '중점 파일을 먼저 읽는 LM-1e 관문 자리(파일은 병합본 재측정)'를 한 줄 더하기를 권고 -- 범위 표지 누락이지 범위 위반 아님(관문 helper 하나의 호출 순서, 값 불변).

### 새 모순 점검

- spec·interface 사이: T-X '조건부' 삭제·완료 8 '(1 -- X-7, W12 순서 계약)'·'이 card에 없는 것' 항목 삭제가 서로 맞음. R-b(interface)와 완료 10 (b)(spec)가 같은 비교 대상(`Resolution.lut`)·대상 metric을 적음. §6 '단언 금지'와 §8 새 두 행 사이 모순 0(cdb·csb Δ 값 단언 0).
- 계획·design: 완료 (10)(b)(c)·A-151~A-153과 맞음. design (viii)(10)(b) '항 없는 경로' 정의 그대로.
- 머리 상태 블록: 첫 판 블록을 '[첫 판]'으로 남기고 둘째 커밋 블록을 앞에 더함 -- 이력 문언이 계획서 원칙 25 기준으로 길지만 card 머리 표지라 문제 아님.

### 결론

Major 0. 새 minor rm1(PM 엄격 부등식 전제)·rm2(W12 파일 칸·원래 취지와 다름 5 범위 표지)와 관찰 1건(`P = 12` → 15)은 왕복 없이 `la1_auto_decisions.md` 입력. 원래 minor m2·m4·m6·m7·m9·m10은 card 표지대로 LA-1 재점검 입력.
