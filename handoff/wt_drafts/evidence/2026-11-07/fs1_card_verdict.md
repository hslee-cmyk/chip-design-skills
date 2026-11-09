verdict: Major 2

# card FS-1 (spec + interface) 독립 판정 1회

- 대상: `card/fs1` 114a9cd1 (첫 판 9513d9fe, base f42a13f8). 그 뒤 60f17fb3 = master(계획 v6.39.3, 598d87d0) 병합. card 파일 두 개는 바뀌지 않았다(`git diff 114a9cd1 card/fs1 --stat` = 계획·history 2파일만).
- 판정자 ≠ card 작성자. 읽기만 했다(수정·커밋·pytest·ngspice 0, 엔진 import 0).
- 정본: 계획 v6.39.3(master 598d87d0 -- 오케스트레이터 통지에 따라 이 판으로 봄; N6.43 범위 (2)·완료 (2), DEC-108 (3) 끝), design v1.16.29 D40 §3.7-B 1~11, 결정 A-171~A-179, CLAUDE.md O-229, `fpga/CLAUDE.md` '★graph 단일 정본'.
- 판정자 스크립트·결과 (`C:/Users/HSLEE/AppData/Local/Temp/la1s_fs1_v/`):
  - `fs1v_hand.py` → `fs1v_hand_out.txt`: interface §1 1~4를 그대로 옮긴 곱집합 전수(float) + `Fraction` 정확 산술 + 옛 꼴 `|r−1|` 대조.
  - `fs1v_tie.py` → `fs1v_tie_out.txt`: 정확 산술 (E1~E4) 동률 탐색. 격자 q/6·q/10, 멤버 2~3, 선언 묶음 하나 → `hits=0`.
  - `grep_old.txt`: master f42a13f8 비test 엔진에서 옛 이름 `git grep` 결과(146줄).
  - DEC-108 행 `dec108.txt`, D40 §3.7-B `d40_37B.txt`, 계획 v6.39.3 `plan6393.md`.

## Major

**M-1. toy M-1이 계획 v6.39.3 완료 (2) 구조 단언과 계획 판정 minor n4-1(A-179)을 충족하지 못하고, 공허해질 수 있다.**
- 계획 v6.39.3 N6.43 완료 (2) 문언: "구조 단언: 4단계 matching L 하한의 slope bin 조회가 출발 w_f 필드를 읽지 않음(READS 집합에 그 필드 없음·기준 폭 슬라이스 키로 조회)". n4-1은 이 단언이 공허하다고 봤다. L 하한과 `wf_start` writer가 같은 블록 `start_intervals`라 READS 집합으로는 가를 수 없기 때문이다. 그래서 n4-1은 **기준 폭 bin ≠ 출발 w_f bin 꼴의 toy에서 L 하한 = 기준 폭 slope로 손계산한 값**인지 보는 값 toy를 요구한다.
- interface §3.4 M-1이 하는 것:
  - (a) spy에 기록된 slope bin w_f 인자가 `w_ref_m`인지 본다.
  - (b) '`wf_start`가 다른 키를 고르도록 후보를 바꿔도 **(가능하면** -- 후보 둘 이상 LUT) L 하한 값 `==` 불변'을 본다.
- 이것이 모자란 이유:
  - 기준 폭 슬라이스 키가 출발 w_f 키·옛 선택 함수가 고르는 폭과 **다르다**는 전제 단언이 없다. 같으면 (a)는 틀린 구현(칸 키나 옛 선택 폭으로 조회하는 구현)도 통과한다. M-2에는 "칸 키 ≠ 기준 폭 키인 toy에서"가 있는데 M-1에는 없다.
  - (b)는 '가능하면'이라 빠질 수 있다. 값이 불변인지만 보고 손계산 값과 대조하지 않는다.
  - L 하한의 손계산 기대값(기준 폭 slope bin으로 낸 `_l_lower` 결과)이 없다. n4-1이 요구한 '값 toy'가 아니다.
- 수정 방향(권고): M-1 전제에 '그 toy의 `cap_map[kind].w_key` ≠ `wf_start` 칸 키'(그리고 ≠ base 선택 폭)를 단언한다(안 서면 멈춤). 그 toy에서 L 하한 기대값을 기준 폭 slope bin으로 손계산한 값 `==`로 둔다(피검 함수 0, 기존 `test_iv_matching_l.py`의 손 식 꼴). '가능하면'은 지운다. 그런 toy를 만들 수 없으면 멈추고 보고한다.

**M-2. 종속 멤버 출발 W = I_i·L/IDu_p 손계산 toy가 사실상 없다(K-5는 공허하다).**
- design D40 §3.7-B 10 (2)는 "종속 멤버 출발 W = I_i·L/IDu_p(1회차 전류·KVL 짝 쓰기 멤버의 1회차 밀도) 손계산"과 "KVL 짝 없음(gate만 공유·source 다름 포함)·I_i 없음 → `no_member_density`"를 완료 toy로 둔다. spec 완료 2도 "종속 멤버 W_i = I_i·L/IDu_p 손값"을 적는다.
- interface가 실제로 덮는 것:
  - K-5는 `W_i = 2e-6 * 1e-6 / math.exp(math.log(4.0))`라는 식 한 줄뿐이고 피검 함수가 없다. 어떤 구현도 통과한다.
  - K-5는 "출발 블록 통합 toy(§3.4 S-B2)의 기대 꼴"이라고 적지만, S-B2(같은 toy 두 번 → 둘째 계산 0)에는 W_i 단언이 없다. 참조가 끊겼다.
  - `wf_start_value`는 `start_w`를 이미 계산된 입력으로 받는다(S-7·S-8은 why 문자열을 직접 넣음). 그래서 'kvl_partner None 또는 I_i None → `no_member_density`', '종속 멤버 W_i = I_i·L/IDu_p(1회차 값·5의 L)' 경로(`start_intervals` 안)를 단언하는 toy가 하나도 없다.
- 결과: design 완료 (2)의 두 항목(W_i 손값, 짝 없음 → `no_member_density` 배선)이 card에서 빠졌다. fail-closed 갈래 하나(`no_member_density`)도 운영 경로 단언이 없다.
- 수정 방향(권고): 출발 블록 통합 toy(S-B 묶음)에 종속 멤버가 있는 미러 칸 하나를 둔다. 기대 = 그 멤버 출발 W = (그 toy 1회차 전류)·L/exp(짝 쓰기 멤버 1회차 ln IDu)로 손계산한 W_c, 그리고 그 W_c로 고른 `wf_start` 키(손 선택). 기존 conftest 꼴에서 1회차 값을 관찰할 자리가 없으면, 기대값을 `wf_start` 키로 낼 수 있게 W_c가 후보 경계를 가르는 toy로 둔다. 'gate만 공유(source 다름)' 멤버가 있는 칸에서 `graph/start: records`에 `wf_start_undefined`{why `no_member_density`}가 남는 toy를 하나 더한다.

## minor (LA-1 재점검 입력 -- 왕복 안 함)

1. **design 문언 뒤처짐(A-178 S-1·S-3)**: D40 §3.7-B 3 '소비자'(출발 slope bin = 그 소자 칸의 w_f)와 11 (다)(칸 E1·E2 = 결과 JSON front 점 행 출력 전용 칸)는 계획 v6.39.3·A-178과 다르다. card는 이를 '원래 취지와 다름' 9·11로 표지했다. 다음 design 개정 때 §3.7-B 3·11 (다)에 v6.39.3 두 갈래와 'LA-1 측정 시점' 표지를 넣는다.
2. **S-2 과도기(`ratios=()`) 뒤따름이 계획에 아직 없다**: A-178은 "SF-1 완료 조건에 배선 단언 추가"라고 적었다. 그러나 계획 v6.39.3에 `realize_fingers`·`ratios` 문언은 0건이다(grep). 과도기 자체는 위임 결정 A-178(O-229 7)로 승인됐다. 함수는 운영 DC 블록에서 실제로 불리고, 빈 것은 인자뿐이다. 그래서 '만들면 배선' 위반으로 보지 않는다. (c) 경로의 운영 소비자 0은 SF-1 병합까지 남는다. SF-1 계획 문언 추가를 확인해야 한다.
3. **줄 번호 어긋남(재작성 범위)**:
   - `iv_matching_l.py`: `_sigma_vgs` 실제 :59(card :58), `_l_lower` :85(card :84), `matching_bounds` :107(card :108).
   - `search/__init__.py:196`의 `__all__` `"polish_l_cells"` 줄이 W24에 없다(:28만 적힘).
   - 착수 조건 6 재측정 때 바로잡는다. 빠진 파일은 없다. `metrics/block_gain_bound.py`의 `_reference_pick`은 이름만 같은 다른 함수다.
4. **G-2 판정 꼴이 약하다**: '`wf_start_value`를 부르는 비test 모듈이 `start_intervals.py` 하나'는 둘째 폐포 구현(그 함수를 부르지 않고 `matching_groups`를 묶는 코드)을 잡지 못한다. `matching_groups`를 READS하는 search·sizing 블록 집합 단언을 더하면 낫다.
5. **조건부 toy**: D-8('가능한 toy가 있을 때 -- 없으면 생략')은 fail-closed 'DC 블록 칸 멤버 조회 불능 → 그 평가 실패, 다른 슬라이스 0'의 유일한 운영 단언인데 빠질 수 있다. 생략하면 그 사실을 판정 기록에 남긴다고 문언에 적기를 권고한다.
6. **`DeclaredRatio` k 비유한**: §1 2의 정수 판정 `float(k) == int(k)`는 k = inf에서 OverflowError, NaN에서 ValueError를 낸다. R-V에 k 비유한·k ≤ 0 case가 없다. 계약 위반 분류(ValueError)를 명시하기를 권고한다.
7. **K-5 숫자 표기**: 기대 꼴은 `5e-13`(판정자 계산)이다. M-2와 함께 정리한다.
8. **E5 값 toy 대체(원래 취지와 다름 5)**: card 탐색(q/4) + 판정자 탐색(q/6·q/10, `hits=0`) 모두 (E1~E4) 동률 최적 0건이다. 구조 대체(R-E5)는 타당하다. design 10 (1) 'E5 toy' 문언의 실현 가능성은 LA-1 재점검으로 넘긴다.

## 항목별 판정

### 1. 범위·완료·착수 조건, card 결정 사항
- 계획 N6.43 범위 (1)~(7)과 D40 §3.7-B 1~11은 spec 범위 1~8·재작성 범위에 빠짐없이 대응한다. 예외는 M-2(design 10 (2) toy)와 minor 1(design 문언 뒤처짐)이다.
- 착수 조건 5(JC-1)·6(base 재측정)·7(v6.39.3 -- 이제 병합됨, 598d87d0)·10(13회로 n/N)은 계획 순서와 맞는다.
- **멤버 오차 |m − x|/x**: |m_i·w_f/W_i − 1| = |m − x|/x로 수학적으로 같다. x ≥ 1이면 m ∈ {⌊x⌋, ⌈x⌉}이 x/2 ≤ m ≤ 2x라 Sterbenz로 m − x가 정확하다. F-2에서 옛 꼴은 (1, 3, 3, 4), 이 꼴과 정확 산술은 (1, 3, 3, 3)으로 실측했다. 맞음.
- **E3 `math.fsum`**: 정의 Σ|r − 1|과 같다. 정확 반올림 합이다. 맞음.
- **E1 = max(r)/min(r) − 1**: max_{i,j}|r_i/r_j − 1|과 같다(D40 6 증명). `hi / v - 1` 꼴은 D40 v1.16.29 r-m2 그대로다. F-1에서 `v*(1+E1) = 0.9999999999999999 < hi = 1.0`을 실측했으므로 창 비교 꼴 고정 toy가 실제로 가른다. 맞음.
- **(c) 후보 `max(1, ·)`**: 계획 '∩ {≥1}'과 같은 집합이다(⌊y⌋ = 0이면 ⌈y⌉ = 1이 이미 있음). 맞음.
- **E5 구조 대체**: minor 8.
- **새 이름**: `wf_start_value`·`kvl_partner`·`initial_wf`·`polish_cells`는 각각 계산 자리 하나·순수 함수다. 원칙과 맞는다. `kvl_partner`의 bulk 같음 조건은 v6.39.3 'VGS·VSB 공유 = 같은 source + bulk 기본 DEC-61'과 맞는다.
- **`slice_of_finger` L 삭제**: as-built :13-17에서 L은 `seal_violation` detail에만 쓰인다(실측). D40 1 '쓰이지 않으면 지운다'와 맞는다.

### 2. 재작성 범위 29행
- master f42a13f8에서 W1~W29의 파일·줄을 직접 열었다(`git show`·`git grep`). 대부분 정확하다:
  - `lut/__init__.py:12·117·121·123`, `lut_set.py:369·389`
  - `block_param_tables.py:22·74`, `ss_off_op.py:56`
  - `start_intervals.py:234-239·295·332`, `s0_fields.py:31`
  - `block_dc.py:46-47·111·336·524·607·628·829·835·868·873`
  - `finger_slice.py:25·33·53`, `s2_values.py:248·257`, `kernel_run.py:68-76`, `size_and_seal.py:31-32`, `size_and_seal_local.py:113·119`
  - `kernel.py:96·106-107·134-137`, `realize_front.py:52·77-80`, `find_front.py:71-83·151`, `l_bin_search.py:34·54·59`, `eps_sweep.py:19·32·129-142`
  - `evaluate` 호출 12자리, `StartPoint(` 4자리
- 어긋남은 minor 3에 적었다.
- 옛 이름 비test 전수(`grep_old.txt`): `finger_slice`·`FingerSlice`·`reachable_slices`·`slice_cycle`·`slice_rounds`·`RealizedFinger`·`realized_finger_missing`·`polish_l_cells`·`w_f_m`·`lb_stops`가 든 파일 24개는 모두 W행 또는 '변경 0 -- 확인만'에 있다. 다만 `metrics/ss_linearize.py`는 W20(JC-1 몫)이고, `metrics/block_gain_bound.py`는 이름만 같은 다른 함수다.
- 출발 소자별 선택 소비자 `iv_matching_l.py:66`은 W9, Rʳ·키 벡터 반복(`block_dc` `_solve`·`_rounds`)은 W10에 있다. 빠진 자리: `search/__init__.py:196`(minor).

### 3. interface toy
- 손계산 재계산 **30개**:
  - R·F·P 18개(R-1, R-2, R-3, R-3b, R-4, R-5, R-6, R-6b, R-7, R-8, R-E3, F-1, F-2, P-1~P-5): 기대 `m`·E1·E2 참고값이 card와 비트까지 같다. 정확 산술 답도 같다. 가르는 것(R-1의 (10, 11)·(11, 11), R-2의 (5, 5), R-3의 (2, 10), R-E3의 (1, 2, 4))을 확인했다.
  - S 9개(S-1~S-9): 폐포·정준 순·선택 (i)(ii)(iii)·격자 float 비교(`50*1e-8 <= 0.5e-6` True 등)를 확인했다.
  - K 3개(K-1~K-4 중 K-1, K-2, K-3 대표 + K-5 식 값 5e-13).
  - **불일치 0**.
- interface만으로 test를 쓸 수 있다. 관찰 지점 3개(§9)는 통과 spy이고, 기존 conftest 꼴을 지명한다.
- 피검 함수로 기대값을 만들게 하는 문언은 없다(§머리·§1 끝 '손 oracle = test 파일 안').
- 공허 단언: M-1(Major), K-5(M-2), G-2·D-8(minor).

### 4. graph 단일 정본
- 새 필드 = `graph/start: wf_start` 하나, writer `start_intervals`. 소비자 `initial_wf`·6단계 slope bin·S3 `wf_keys`가 있다.
- `dc_finger` writer는 `dc_solve` 하나이고, `w_f_m` 칸을 삭제한다(사본 제거).
- `WfInput.cells_ref`는 필드 객체 참조이고(S-B3 `is` 단언), `RealizeInput`은 참조와 표지뿐이다.
- 새 cache·memo·sctx 슬롯 0. `initial_wf`는 저장 0이다.
- 출력 전용 칸(`perf` 이웃 시험·`small_m`)은 선언돼 있다.
- E1·E2 운영 칸은 만들지 않는다(사본 0, A-178 S-3).
- `ratios=()`는 minor 2다. 함수는 운영에서 불리므로(D-6 spy) 소비자는 있다. (c) 경로는 함수와 toy로만 덮인다.
- 위반 0.

### 5. fail-closed·상수·이름
- `wf_candidates_empty`(C-1), `wf_start_undefined` 세 why(S-6~S-8·O-2), `realize_tie_unresolved`(R-T 5 case), `wf_cell_kind_mixed`(S-9)는 단언이 있다.
- `no_member_density`는 운영 경로 단언이 없다(M-2).
- 상수 발명 0. 작은 m의 2는 계획 Q-FS1 문언이고 출력 전용이다.
- 회로 이름 0. PDK 역할 이름(`min_finger_w_m`·`manufacturing_grid_m`·`w_ref_m`)을 쓴다.

### 6. S-1 해소
- 순환 경로(4단계 L 하한 → slope bin → 5a 전 w_f)를 끊는 규칙은 계획 v6.39.3 문언과 맞는다(W7·W9). 그러나 그것을 단언하는 M-1이 공허할 수 있다(Major M-1).
- M-2(6단계 = 칸 키, 평가 σ = `w_key`, 칸 키 ≠ 기준 폭 키 toy)는 갈래 둘째 쪽을 실제로 가른다.

## 재판정 범위
Major 2건을 고치면 재판정 1회를 받는다. 대상은 interface §3.3 K-5·§3.4 M-1·S-B 묶음과 spec 완료 2 문언이다.

## 재판정

verdict: Major 1

- 대상: `git diff 60f17fb3 a41fb366`(셋째 커밋)만 봤다. 읽기만 했다.
- 첫 판정 M-2는 해소했다. M-1은 판별력은 갖췄지만, 기대값 출처에 Major가 하나 남는다(RM-1).

### Major

**RM-1. M-1 기대값이 엔진 함수와 엔진 소스 정의에 기댄다.**
- (가) interface §3.4 M-1은 s_ref·s_wf(그리고 전제 P2)를 "test가 `mismatch_sigma_vgs`로 잰다"고 적는다. 이 함수는 피검 사슬 `matching_bounds → _l_lower → _sigma_vgs → mismatch_sigma_vgs` 위에 있고, 같은 toy의 spy 대상이다. 그래서 기대값(답 앵커 L_k와 제약 값)을 피검 경로의 엔진 reader로 만들게 된다. 이는 '피검 함수로 기대값을 만들지 않는다'에 어긋나고, JC-1 선례(LUT npz 원 파일 + 손 식)와도 다르다.
- (나) 인자 출처(g = gm/ID 하한, 출발 동작점 VDS·VSB, 1회차 I, W = max(I·L/IDu, W_min))를 "기존 `_sigma_vgs` 정의, iv_matching_l 머리 독스트링"으로 지시한다. 이는 엔진 소스 열람이라 'interface만으로 test를 쓴다'에 어긋난다. g 하한·VDS·VSB·W_min 클램프는 interface에 정의가 없다.
- 판별력((a) spy w_f = 기준 폭 + P1·P3, (c) s_wf 앵커 ≠ L_k)은 갖췄다. 고칠 것은 기대값 출처뿐이다.
- 수정 방향:
  - 손 식 입력은 spy가 잡은 그 호출의 인자 (g, L, VDS, VSB, W)를 그대로 쓴다.
  - σ는 LUT npz 원 파일(두 슬라이스의 mismatch slope 열)을 직접 읽고 PDK mismatch 모델 선언 식으로 손계산한다. 열 이름과 식은 interface에 적는다.
  - 불가능하면 멈추고 보고한다.

### 항목별
1. **M-1**: RM-1. 전제 P1~P3 '생략 없음', (b) `== L_k`, '가능하면' 삭제로 n4-1 값 toy 꼴은 갖췄다.
2. **`member_start_w`·`reference_slice_undefined`**:
   - `reference_slice_undefined`는 새 정지 사유가 아니다. design D40 §3.7-B 3·출발 불능 항목이 이미 정한 `wf_start_undefined`의 why 값이다. 범위 안이다.
   - `member_start_w`는 design 3 '멤버 출발 W(블록 안 중간값, 필드 아님)'를 순수 함수 자리로 둔 card 이름이다(새 필드·저장 0, 호출자 `start_intervals` 하나, W25·신규 시그니처·§9 표지). graph 정본 위반 0이다. S-B5 (c) `start_w is` 출력이 자리 하나를 묶는다.
   - minor r-1: 쓰기 멤버 `current` None → `no_member_density`는 design 문언(종속 멤버 I_i 없음)을 넓힌 것이다. fail-closed 쪽이라 위반은 아니고, '원래 취지와 다름' 표지·LA-1 재점검 입력으로 둔다.
3. **S-B5·S-B6**:
   - 공허하지 않다. S-B5는 `is` 같은 객체·`partner[B] == "A"`·잡힌 인자 손 식 `==`·손 선택 키를 본다. S-B6은 `w_key is None`·정확한 records 항목·`initial_wf` None·find_front 평가 0을 본다.
   - '서지 않으면 멈추고 보고'는 정지(fail-closed)이고 통과로 세는 skip이 아니다. 맞음.
   - minor r-2: S-B5 (d) 'defined = 정의 후보 전부(전제)'는 단언 방법이 없다.
   - minor r-3: S-B6의 'topology 문서로 test가 만든다'는 test 픽스처 한정이고 library topology는 바꾸지 않는다는 점을 명시하기를 권고한다(원칙 15).
4. **D-8·G-2·R-K**: 판정할 수 있다.
   - D-8은 무조건이 됐고, 적재 실패 시 멈춘다.
   - G-2: (a)(b)는 결정적이다. minor r-4: (c)의 AST 휴리스틱은 오탐 가능성이 있다.
   - R-K는 4 case·메시지 토큰·검사 순서가 명확하다.

minor 4건(r-1~r-4)은 LA-1 재점검 입력이다. RM-1을 고치면 그 부분만 재판정한다.

## 재판정 2

verdict: Major 0

대상은 `git diff a41fb366 42ddbfce`뿐이다(interface §3.4 M-1 절차, spec 머리 한 단락). 읽기만 했다. 대조 자료는 master `lut/mismatch_sigma.py` 독스트링·식(정의 대조 용도만), `assets/lut_v2_bin_rule.json`(`rule: lower`), `sky130_pdk_decl.json` `min_finger_w_m`, LUT `manifest`·위치 선언 슬라이스 목록, 작성자 `fs1_slope_bins2_out.txt`다.

### RM-1 해소
**(1) 기대값 출처**: spy가 잡은 인자, mismatch npz `DVGS_*` 열의 3축 보간, `meta_json.slope_ref`, 모델 카드 블록 slope 이름과 `.param` 값, bin 규칙 선언만 쓴다. 피검 사슬의 엔진 함수는 0이다. 파일 위치(선언 키)·열·축·식·NaN 처리가 interface에 적혀 있어, interface만으로 test를 쓸 수 있다. 해소.

**(2) σ 손 식**: σ = √(Σ_k (D_k·s_k/s_k^ref)²)·√(w_ref/W), 쌍 √2·σ. 엔진 정의(lut CONTRACT 10.4, `mismatch_sigma.py` 머리 식 `√(Σ(DVGS_k·slope_k(bin(w_f,L))/slope_k(bin_ref)))²·√(W_ref/W)`)와 같다. 엔진의 |DVGS|는 제곱 안이라 무관하다. 블록 선택이 W bin 먼저인 것은 'lmin ≤ L ≤ lmax · wmin ≤ w_f ≤ wmax + 경계 = bin 규칙'과 같은 집합을 낸다. 맞음.

### 항목별
**(3) 단순성·실현 위험 -- minor(멈춤 사유는 아님)**

손 식은 엔진 σ의 독립 재구현이다. 원 자료에서 기대값을 내는 정도의 복잡도이고, JC-1 꼴과 같다. 위험은 전제 쪽에 있다.
- r2-1(guidance 오류): bin 규칙 선언이 `rule: lower`(경계는 아래 블록)이다. 그래서 W = 7 µm 슬라이스는 [5, 7] µm 블록(`vth0_slope`)에 들어 w_alt가 되지 못한다. card 안내 '≥ 7 µm'은 틀렸다. 슬라이스 목록에 7 µm 초과는 없으므로 쓸 수 있는 w_alt는 0.42·0.52 µm(W_min = difftap.2 이상, [0.42, 0.52]·[0.39, 0.42] 블록 = `vth0_slope1`)뿐이다. P2가 걸러 주므로 잘못된 기대값은 생기지 않지만, 안내 문장은 고친다.
- r2-2(실현 위험): 전제는 'nmos 입력이고 matching L 하한 탐색 범위가 [4, 8] µm bin 앵커(8 µm)에 닿는 library 회로'다. 이것은 재지 않았다. 서지 않으면 test 단계에서 멈춘다(fail-closed, skip 아님).
- 더 단순한 대안(toy LUT·toy mismatch 선언)을 따졌다. toy `PdkMismatchModel` 블록은 `tests/lut/test_mismatch_sigma.py`(`_block`·`_model`)에 있다. 그러나 출발 블록을 도는 toy LUT에는 mismatch 데이터가 없다(`test_iv_matching_l.py` 머리: 'toy LUT(mismatch 데이터 없음)', `mismatch_lut_missing` 거부). 그래서 toy 경로를 쓰려면 출발 toy 흐름에 mismatch npz·PDK mismatch 모델을 끼우는 새 픽스처 배관이 필요하다. 이는 card 범위에서 지금보다 단순하지 않고, O-229 4(새 인프라 0)에도 걸린다. 지금 꼴을 유지하기를 권고한다.
- 대신 권고: test 착수 전에 오케스트레이터가 기존 자료로 전제 두 가지(입력 kind = nmos, 출발 L 앵커 범위 ⊇ 8 µm)를 한 번 확인한다. 서지 않을 때의 처리도 미리 정한다. 계획 v6.39.3 완료 (2) 문언('기준 폭 슬라이스 키로 조회')은 (a) spy 인자 + P1·P4로 판별되고, (b) 값 toy는 n4-1(minor)의 보강이다. 그래서 (b)를 뺄지는 기준 약화 여부로 오케스트레이터가 결정하고 기록한다(조용한 skip 금지).

**(4) 새 공허 단언·skip 꼴**: 없음.
- (a) spy w_f, (b) `== L_k`, (c) 실행 A·B 인자 `==`, 그리고 P1~P4(P2가 '다른 폭이 실제로 가름', P4가 '칸 키 ≠ 기준 폭')는 모두 판별력이 있다.
- '안 서면 멈추고 보고'는 정지다.
- r2-3: s_k^ref = 0이고 s_k ≠ 0인 경우가 빠졌다. 엔진은 이 경우 `lut_mismatch_slope_unscalable`로 거부하는데, card 손 식은 0으로 나누게 된다. '그 L은 손값 없음 → 멈춤'을 적는다.
- r2-4: 실행 A의 기대 'L 하한이 최대 앵커이고 `conflicts`에 matching 항목'은 둘 중 무엇이 성립해야 하는지 모호하다. 하나로 적는다.

**PDK 이식성(O-197) -- minor r2-5**: 4단계 손 식 규칙에 sky130 고유 이름이 있다. slope 이름 꼴 `sky130_fd_pr__nfet_01v8__<변수>_slope<N>`, 모델 카드·mismatch 파일 이름, 소자 키 `nfet_01v8`이 그것이다. 파일은 이미 PDK 선언 역할 키(`sources` `spice_model_card`·`nfet_01v8_mismatch_slopes`)로 찾게 돼 있다. slope 식별자는 '그 블록의 그 변수 식에 나오는 `.param` 이름'으로만 정의하고, 구체 이름은 예시 표지로 내린다.

minor 5건(r2-1~r2-5)은 LA-1 재점검 입력이다. r2-1·r2-3·r2-4는 test 착수 전 문언만 고치면 되고, 재판정은 필요 없다.
