# NFR-4 BLAS 스레드 결정론 결함 card 초안 (사용자 결정 8)

- 작성: 2026-10-14. 읽기 전용 원인 조사와 초안만 담았다. 엔진 코드·test·저장소는 고치지 않았고 커밋하지 않았다.
- 기준 저장소: master `af10c9b`. 측정용 복제본 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_nfr4_probe/repo`(`git clone --local`). 측정 뒤 `git -C repo status --short`는 비어 있다(저장소에 쓴 것 없음).
- 실험 위치: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_nfr4_probe/`.
  - 스크립트: `probe_blocks.py`(ComputeBlock 호출마다 입력 버전·출력 열 지문 기록), `probe_calls.py`·`probe_calls2.py`(start_intervals 안 numpy/scipy 선형대수 호출과 `_Network.at_target`·`scipy_minimize` 입출력 기록), `probe_pin.py`(SLSQP 호출 동안만 scipy OpenBLAS 스레드 1), `micro_blas.py`·`micro_blas2.py`·`micro_blas3.py`·`micro_lu.py`(작은 크기 BLAS/LAPACK 단독 비교), `micro_split.py`(numpy 쪽·scipy 쪽 OpenBLAS 중 어느 것이 결과를 바꾸는지), `bench_pyqr.py`(순수 Python 최소제곱 비용), `analyze.py`(비교).
  - 결과: `r1/`·`r8/`(블록 단위), `q1/`·`q8/`(호출 단위), `v_<회로>_<1|8>/log.jsonl`(세 회로 호출 단위 + 출발 구간 값), `p_<회로>_<pin8|nopin8|nopin1>/`(고정 실험), `summary.txt`, `micro_*.json`, `m2_*.json`, `m3_*.json`, `lu_*.json`.
- 실행 환경: Python 3.14.2, numpy 2.4.6(OpenBLAS 0.3.31 `libscipy_openblas64_`, SkylakeX, MAX_THREADS=24), scipy 1.18.0(별도 OpenBLAS `libscipy_openblas-197ee2fc…dll`). 프로세스마다 빈 S0 폴더·빈 표 캐시 폴더.
- 결정 원문: `wt/_drafts/user_decisions.md` 2026-10-14 "8 test 환경 OPENBLAS 스레드 1 고정 + 엔진 결정론 원인 수정은 2 착수 전(백로그)". 기록: `U17_FOLLOWUPS.md` 2026-10-14 항목, 감사 자료 `wt/_audit_u17_1b_r2/results/blas_runxfail.txt`(--runxfail 시 10개 필드 차이: `device/M1~M7: start.row`, `graph/start: area_est_m2·macro·rungs`).

경로 접두 `E/` = `skills/analog-gmid-design/gmid_engine/`. 아래에서 **[사실]** = 이번 측정으로 확인, **[추측]** = 측정하지 않은 추론.

---

## 0. 요약

- **원인 한 줄 [사실]**: `E/search/macro_poles.py:345`의 `scipy.optimize.minimize(method="SLSQP")` 반복 계산이 scipy 쪽 OpenBLAS 스레드 수(1 대 2 이상)에 따라 다음 반복점을 몇 ulp 다르게 낸다. 같은 함수값·같은 FD 기울기를 받은 직후의 다음 반복점부터 갈라진다. SLSQP가 이 차이를 수렴 허용오차 규모(x 상대 1e-11~3.5e-4)로 키우고, `start_intervals`가 그 해로 전류·면적·사다리를 만들어 `graph/start`·`device: start.row` 의 float가 바뀐다. 지문(`float.hex`)은 비트 단위라 모두 다른 값이 된다.
- **numpy 쪽 OpenBLAS는 무관 [사실]**: 엔진이 쓰는 나머지 선형대수(`numpy.linalg.solve`·`lstsq`·`norm`, `scipy.linalg.lu_factor`·실수 `lu_solve`·`eig`, `einsum`·`@`)는 엔진 크기(n ≤ 39)에서 스레드 1 대 8 비트가 같다. **[측정 2 정정] 복소 `scipy.linalg.lu_solve`(zgetrs)는 n ≥ 3에서 스레드에 따라 갈린다 -- §6.3.**
- **권고 한 줄**: SLSQP 4개 호출 자리를 엔진 소유 결정론 SQP(순수 Python, 고정 연산 순서, BLAS 호출 없음)로 바꾼다(후보 A). 런타임 스레드 고정(후보 B)은 근본 수정이 아니다(사용자 분류). 반올림·허용오차 비교(후보 C·D)는 근거 상수가 없고 비트 동일을 보장하지 못해 제외한다.

---

## 1. 처음 갈라지는 계산 지점 (이분 탐색)

### 1.1 블록 단위 (`probe_blocks.py`, 결과 `r1/`·`r8/`, two_stage_ota) [사실]

단계 A(블록 1~15)와 단계 B(16~25), 탐색 컨텍스트 앞부분(26~40)은 입력 버전·출력 지문이 모두 같다. 처음 다른 블록은 **41번 `start_intervals`** 이고, 입력 버전은 같은데 출력 `device/start.row`·`graph/macro`·`graph/rungs`·`graph/area_est_m2` 가 다르다. 42번(`dc_currents`)부터는 입력 버전이 달라 차례로 다시 계산되고 다른 값이 된다(결과 지문 외 `dc_seal_*`·`metrics_*` 까지 전파).

세 회로 요약(`summary.txt`, `v_<회로>_<1|8>/`):

| 회로 | 처음 다른 블록 | SLSQP 호출 | x 다름 | nit 다름 | success 다름 | x 최대 상대차 | 다른 출발 구간 필드 | 구조(실수 뺀 표기) |
|---|---|---|---|---|---|---|---|---|
| two_stage_ota | start_intervals (입력 같음) | 40 | 36 | 6 | 0 | 2.26e-06 | rungs, macro, area_est_m2, start.row 7개 | 같음 |
| two_stage_ota_sf | start_intervals (입력 같음) | 65 | 65 | 2 | 0 | 3.54e-04 | rungs, macro, area_est_m2, start.row 9개 | 같음 |
| sf_pushpull_output_opamp | start_intervals (입력 같음) | 30 | 30 | 0 | 0 | 4.93e-11 | rungs, macro, area_est_m2, **conflicts**, start.row 20개 | 같음 |

- 결과 값 예(two_stage_ota): `area_est_m2` 8.641582030501444e-11 대 8.64157359324065e-11(상대 9.8e-07), `macro.gm[O1]` 9.392049363375181e-06 대 9.392037232538864e-06, `Cc` 1.2571912970259104e-13 대 1.257189670438935e-13, `rungs` 실수 98개 중 36개 다름(최대 상대 1.29e-06).
- 이산 구조(사다리 칸 수, 충돌 종류, 선택된 출발 블록, success 플래그)는 세 회로 모두 같다. nit는 다른 경우가 있다(two_stage_ota 실패 출발점에서 100 대 11).

### 1.2 호출 단위 (`probe_calls.py`·`probe_calls2.py`, 결과 `q1/`·`q8/`) [사실]

`start_intervals` 안의 `numpy.linalg.*`, `scipy.linalg.*`, `numpy.einsum`, `_Network.at_target`, `scipy_minimize` 를 감싸 입력·출력 해시를 순서대로 기록했다.

- 첫 차이: two_stage_ota 의 at_target 이벤트 211번(첫 SLSQP 호출 안, `inmin = 1`). 207~210번은 FD 섭동 4점(gm 2개 + Cc 1개, 기준점 포함)이고 입력·출력 모두 같다. 211번은 SLSQP가 낸 **다음 반복점**인데 `Cc` 의 ln 변수만 `0x1.104f0e463aceap-41` 대 `0x1.104f0e463acd8p-41`(18 ulp)로 다르다.
- 같은 모양: two_stage_ota_sf 490번(첫 gm 성분 9 ulp), sf_pushpull 71번(둘째 gm 성분 6 ulp). 모두 `inmin = 1`(SLSQP 안), 직전까지 함수값·제약값 같음.
- 즉 SLSQP 가 받은 (목적, 제약, 기울기) 가 같은데 낸 다음 x 가 다르다 -> 차이는 SLSQP 내부 계산에서 생긴다.

### 1.3 어느 라이브러리인가 (`micro_split.py`) [사실]

장난감 SLSQP(3변수, 등식 1·부등식 2, 60문제)를 `OPENBLAS_NUM_THREADS=8` 에서 돌리며 ctypes로 OpenBLAS 스레드 수만 바꿨다.

| 설정 | 결과 해시 |
|---|---|
| 8, 고정 없음 | 129187ddd6d3c900 |
| 8, numpy 쪽 OpenBLAS만 1 | 129187ddd6d3c900 |
| 8, scipy 쪽 OpenBLAS만 1 | 28fa7767b7a8c5fa |
| 8, 둘 다 1 | 28fa7767b7a8c5fa |
| 1, 고정 없음 | 28fa7767b7a8c5fa |

- 스레드 1 대 2·4·8·미지정은 두 갈래로만 나뉜다(같은 설정 반복 실행은 비트 같음, `micro_blas.py` slsqp_toy: 1 = d5551f88…, 2·4·8·unset = dd86da2d…). 병렬 축약 순서의 비결정이 아니라 **'스레드 1 경로' 대 '다중 스레드 경로'의 결정론적 차이**다.
- scipy 1.18 `_slsqplib` 는 scipy 쪽 OpenBLAS의 `daxpy ddot dgelsy dgemv dgeqr2 dgerq2 dlarf dlarfgp dlartgp dnrm2 dorm2r dormr2 dscal dtrsm dtrsv` 를 부른다(바이너리 기호 목록).
- **미확인**: 이 중 어느 루틴이 갈리는지는 찾지 못했다. `scipy.linalg.blas/lapack` 래퍼로 같은 루틴들(ddot·dnrm2·dgemv N/T·dtrsm 16조합·dtrsv·dgelsy·dgeqrf·dger·dlarf·dlarfg·dlartg·dormqr·dgemm·dtrmm)을 크기 ≤ 13에서 300~500회 돌린 결과는 스레드 1 대 8 비트가 같았다(`m2_*.json`, `m3_*.json`, `micro_*.json`). `_slsqplib` 이 넘기는 특정 인자(leading dimension·stride·작업공간 크기)에서만 경로가 갈리는 것으로 [추측]한다. 수정 방향은 이 루틴을 몰라도 정해진다(§3).

### 1.4 엔진의 다른 선형대수는 스레드 무관 [사실, 엔진 크기 한정 -- 측정 2에서 복소 lu_solve 예외 발견, §6.3]

`micro_lu.py`(n = 1~39, 400회): `scipy.linalg.lu_factor`·`lu_solve`(trans 0/1), 복소 `numpy.linalg.solve`, 묶음 `numpy.linalg.solve`(k ≤ 59), 일반화 `scipy.linalg.eig`, `numpy.linalg.lstsq`, `einsum("rn,knm->krm")`, 중간 크기 `@` -- 9종 모두 스레드 1 대 8 비트 같음. 실제 회로 실행에서도 start_intervals 이전 40개 블록(MNA·pencil·LU 포함)이 같았다. 단 OpenBLAS는 큰 크기(예: getrf 의 m·n 문턱)에서 다중 스레드 경로를 쓰므로 회로가 커지면 같은 결함이 생길 수 있다 [추측] -- §5 test 5가 지킨다.

### 1.5 같은 결함을 가진 다른 호출 자리 [사실: 같은 라이브러리 경로 / 추측: 실제 값 차이]

엔진의 `scipy.optimize.minimize(method="SLSQP")` 호출은 4곳이다.

| 위치 | 용도 | 이번 측정 |
|---|---|---|
| `E/search/macro_poles.py:345-348` | 출발 구간 매크로(전원 전류 합 최소, 다중 출발) | 차이 확인(§1.1) |
| `E/search/layer0_center.py:235-236` | 층 0 Chebyshev 중심 | 측정 안 함(탐색 실행 전 단계에서 멈춤) |
| `E/search/layer0_center.py:374-377` | 층 0 max-min 위치 | 측정 안 함 |
| `E/search/slsqp_outer.py:195-197` | 외층 ε-제약 SLSQP(front) | 측정 안 함 |

세 곳은 같은 `_slsqplib` 를 쓰므로 같은 결함이 있다고 본다 [추측]. 출발 구간이 이미 달라 지금 test로는 따로 볼 수 없다.

---

## 2. 차이가 지문·선택으로 증폭되는 지점

| 위치 | 증폭 방식 | 이번 측정 |
|---|---|---|
| SLSQP 반복 자체(`macro_poles.py:345`) | 1 반복의 수 ulp 차이가 이후 BFGS 갱신·선 탐색을 거쳐 수렴 허용오차 규모로 커진다(x 상대 최대 3.54e-04). 수렴 못 한 출발점은 반복 수가 갈린다(100 대 11). | 사실 |
| `E/search/macro_poles.py:349` `sweeps += int(out.nit)` -> `MacroResult.sweeps` | nit 차이가 `graph/start: macro` 의 정수 칸을 바꿀 수 있다. 이번 세 회로는 합이 같았다(18). | 경로 사실, 값 변화 없음 |
| `E/search/macro_poles.py:353-357` 채택 판정(`abs(log mag) <= √tol`, `pm >= 목표 − √tol`, 극점 여유 ≥ −√tol)과 `power < best·(1 − tol)` 다중 출발 선택 | 경계 근처 해에서 채택·선택 출발점이 뒤집힐 수 있는 이산 증폭. 이번 측정에서는 success·선택 모두 같았다. | 경로 사실, 뒤집힘 미관측 |
| `E/search/start_intervals.py:364-395` 실행 가능 판정 `feasible`(`macro_failed`, `area <= budget`)과 `bracket_root(… feasible(solve(v)) …)` | t 선택이 이산 판정의 부호로 정해진다. 매크로 해가 경계에 걸리면 t 칸이 바뀐다. 이번에는 같았다. | 경로 사실, 뒤집힘 미관측 |
| `E/search/start_intervals.py:388-389` 충돌 레코드 값(`bottom.area − budget`) | float 그대로 `conflicts` 에 들어간다(sf_pushpull 의 conflicts 지문 차이). | 사실 |
| `E/core/fingerprint.py:37-38` float 를 `float.hex` 로 인코딩 | 1 ulp도 다른 지문. `value_fp` -> 하류 블록 `input_version`(`E/core/compute_block.py:137`)이 달라져 42~59번 블록이 모두 재계산·다른 값. S0 스냅샷 적중·graft 재사용도 깨진다. | 사실 |

정리: 이번 세 회로에서 갈린 것은 **연속값뿐**이고 이산 구조는 같았다. 그러나 비트 단위 지문이 field cache(입력 버전)의 열쇠이므로, 연속값 차이만으로 NFR-4("같은 입력은 같은 산출물")와 EP-2(재계산 0)가 함께 깨진다. 탐색 단계(층 0·외층)의 이산 선택(pareto 남김 순서, 채택 판정)에서 뒤집힘이 생기는지는 재지 않았다 [미측정].

---

## 3. 수정 후보 비교

### 3.1 후보

| 후보 | 내용 | 근본 수정인가 |
|---|---|---|
| **A** 엔진 소유 결정론 SQP | 4개 SLSQP 자리를 엔진 모듈 하나(예: `E/sizing/sqp_det.py`, 이름은 test glob 충돌 확인 뒤)의 순수 Python 구현으로 바꾼다. Kraft SLSQP와 같은 알고리즘(BFGS 갱신 + LSQ 부분문제 + Han-Powell 선 탐색), 내부 선형대수는 Python float와 고정 순서 루프(Householder·삼각해)만 쓴다. numpy·scipy BLAS/LAPACK을 부르지 않는다. 호출 계약(경계, 등식·부등식, 해석·FD 기울기, `ftol`·`maxiter`, callback, 결과 x·nit·success·status·message)은 지금 쓰는 부분만 같게 둔다. | 예. 결과가 입력만의 함수가 된다(스레드·BLAS 공급자·버전 무관). |
| B 런타임 스레드 고정 | SLSQP 호출 동안 scipy 쪽 OpenBLAS 스레드를 1로(ctypes 또는 threadpoolctl) 엔진 안에서 고정. | **아니다(사용자 분류)**. 결과가 여전히 라이브러리 경로에 의존한다(OpenBLAS 버전·공급자 바뀌면 다시 깨질 수 있다). |
| C SLSQP 해 반올림(격자 맞춤) | 반환 x 를 분해능 격자로 반올림. | 아니다. 격자 경계 양쪽에 걸리면 여전히 갈린다(보장 없음). 격자 폭 상수가 필요하다 -- 근거 없음. **제외** |
| D 지문·비교에 허용오차 | value_fp 또는 test 비교를 허용오차로. | 아니다. field cache는 입력 버전 비트 동일에 기대므로 재계산·graft 실패가 남는다. NFR-4 문언("같은 산출물") 약화 = 기준 약화(사용자 승인 대상). 허용오차 상수 근거 없음. **제외** |

참고: 계획 IC2(`test_order_shuffle_invariance`)의 '연속 필드 tol 안'은 순서 섞기 불변식이지 같은 입력 반복 실행 불변식(NFR-4)이 아니다 -- D의 근거로 쓰지 않는다.

### 3.2 정확도 영향

| 후보 | 측정·근거 |
|---|---|
| A | 같은 알고리즘이라 같은 국소해로 가되 연산 순서가 달라 마지막 비트·반복 수가 scipy와 다르다 [추측]. 지금 스레드 1과 스레드 8 사이 차이(x 상대 4.9e-11~3.5e-4, 출발 구간 값 상대 ≤ 1.3e-06)와 같은 규모로 base 기준선(`tests/integration/fixtures/u17_1b_s0_baseline.json` 등)이 바뀐다 -> **기준선 재측정 필요 = 사용자 승인 대상**. 구현 뒤 9회로에서 scipy(스레드 1) 대비 이산 구조 일치와 연속값 차이를 재서 보고한다(판정 기준이 아니라 보고). |
| B | 실측: SLSQP 호출 동안만 scipy 쪽 스레드 1이면 OPENBLAS 8 에서도 출발 구간 지문이 스레드 1·base 기준선과 비트 같다(2회로, §3.3). 기준선 변화 0. |
| C·D | 제외(위). |

### 3.3 비용

- **B 실측** (`probe_pin.py`, 결과 `p_<회로>_<pin8|nopin8|nopin1>/`; `OPENBLAS_NUM_THREADS=8` 에서 `macro_poles.scipy_minimize` 호출 동안만 scipy 쪽 OpenBLAS 스레드 1) [사실]:

| 회로 | pin8 대 nopin1(스레드 1) | nopin8 대 nopin1 | nopin1·pin8 대 base 기준선(`u17_1b_s0_baseline.json` 출발 구간 8필드) | SLSQP 구간 시간 s (nopin1 / nopin8 / pin8) |
|---|---|---|---|---|
| two_stage_ota | 출발 구간 8필드 + start.row 7개 모두 같음 | rungs·macro·area_est_m2·start.row 7개 다름 | 둘 다 같음 | 341.2 / 269.7 / 340.7 (40회) |
| sf_pushpull_output_opamp | 모두 같음 | rungs·macro·area_est_m2·conflicts·start.row 다름 | 둘 다 같음 | 218.1 / 219.2 / 221.0 (30회) |

  - 시간은 probe 기록(호출마다 해시·JSON 쓰기) 부하와 6 프로세스 병렬 실행 안의 값이고, 대부분 콜백(MNA 평가) 시간이다. two_stage_ota 의 nopin8 이 짧은 것은 BLAS 속도가 아니라 궤적이 달라 평가 수가 적었기 때문이다(at_target 기록 7,694 대 5,771). 고정 자체의 비용은 관측되지 않는다(pin8 ≈ nopin1).
  - 이 실험은 '다른 엔진 선형대수는 스레드 무관'(§1.4)도 실제 회로에서 뒷받침한다: numpy 쪽 OpenBLAS는 8 스레드 그대로인데 결과가 기준선과 같다.
- **A 추정**: 반복당 비용은 LSQ 부분문제 몇 번. 순수 Python Householder 최소제곱 1회(`bench_pyqr.py`): (n, m) = (4, 10) 0.093 ms, (12, 30) 1.0 ms, (20, 60) 4.3 ms, (40, 120) 29 ms. 매크로(n ≤ 4)는 무시할 만하다. 외층은 반복마다 FD 기울기에 평가 n+1회가 들고, 평가 1회 비용(기록: 세션47 72.9 ms)이 n=20이면 반복당 약 1.5 s라 QP 몫은 수 % 이하로 [추측]. 외층 θ 차원은 회로별로 재지 않았다(착수 전 실측 필요).
- **A 작업량 [추측]**: 구현 600~1,200줄(LSQ/LSEI/LDP/NNLS, 선 탐색, BFGS, 경계 처리) + 단위 test. scipy C 소스(BSD)를 이식할지 새로 쓸지는 card 범위 결정 사항.

### 3.4 권고안

**A** -- 엔진 소유 결정론 SQP로 4개 호출 자리를 대체하고 `scipy.optimize` import를 엔진에서 없앤다(같은 변경에서 옛 호출 삭제).

근거: (1) 원인이 '라이브러리 내부 경로가 스레드 수에 따라 갈림'이라 엔진이 그 경로를 쓰는 한 B는 우회다(사용자 분류와 같다). (2) C·D는 새 상수가 필요하고 비트 동일을 보장하지 못한다. (3) A의 비용은 매크로에서 무시할 수준, 외층에서 평가 비용 대비 작다(추정, 착수 전 θ 차원 실측). (4) ~~나머지 엔진 선형대수는 엔진 크기에서 스레드 무관이 실측되었으므로 범위가 SLSQP 4곳으로 닫힌다.~~ [측정 2 정정: 복소 `lu_solve` 자리가 더 있다 -- 권고는 §6.6]

착수 조건(사용자 몫): 기준선 재측정 승인(A는 결과 비트를 바꾼다). 이 승인이 없으면 B가 유일하게 기준선을 유지하는 안이며, 그때는 '근본 수정 아님'으로 기록하고 결함 test(strict xfail)를 남긴다.

---

## 4. design 40 정정 문장 초안

### 4.1 §11 ② 선행 조건(1679행) "NFR-4 결정론 원인 수정" 괄호 안 교체

> (v1.9.2 결정 8. 원인(2026-10-14 실측 `wt/_drafts/engine/NFR4_BLAS_CARD_DRAFT.md`): `E/search/macro_poles.py`의 scipy SLSQP(`_slsqplib`)가 scipy 쪽 OpenBLAS 스레드 1 경로와 다중 스레드 경로에서 다음 반복점을 다르게 내고, 그 차이가 수렴 허용오차 규모로 커져 `start_intervals` 출력(`start.row`·`rungs`·`macro`·`area_est_m2`·`conflicts`)이 비트 단위로 달라진다. [측정 2 정정 반영 필요: 복소 `scipy.linalg.lu_solve`(`metrics/point_solve.py:46-47` 등)도 스레드에 따라 갈린다 -- §6.7 문장으로 교체] 수정: SLSQP 호출 4곳(`macro_poles`, `layer0_center` 2곳, `slsqp_outer`)을 엔진 소유 결정론 SQP(§7.4)로 바꾼다. ①-b의 test 환경 스레드 1 고정은 이 card 병합과 같은 변경에서 거둔다.)

### 4.2 §1.2 엔진 원칙 표에 행 추가 (EP-9)

> | EP-9 | **결과는 입력만의 함수다.** 판정·출발값·지문에 들어가는 계산은 실행 환경(스레드 수, BLAS 공급자·버전, 해시 시드)에 따라 비트가 달라지는 경로를 쓰지 않는다. 반복 최적화(SQP)는 엔진 소유 결정론 구현만 쓴다(§7.4). 작은 크기 선형대수(numpy·scipy LAPACK)는 스레드 1·N 비트 동일 test가 지키는 동안만 쓴다 | 계획 NFR-4, 사용자 결정 8(2026-10-14) |

### 4.3 §7 에 절 추가 (§7.4 결정론 SQP)

> ### 7.4 결정론 SQP
> **문제**: scipy SLSQP는 내부 BLAS/LAPACK 경로가 OpenBLAS 스레드 수(1 대 2 이상)에 따라 갈려, 같은 문제에서 다른 해를 낸다(실측: 출발 구간 3회로, x 상대 최대 3.5e-4).
> **규칙**: 엔진의 제약 최적화는 `E/sizing/<이름 미정>.py` 하나만 쓴다. 알고리즘은 SLSQP(Kraft)와 같고, 내부 산술은 Python float의 고정 순서 연산이다(numpy·scipy 선형대수 호출 없음). 공개 계약은 §10.1 서명 표에 둔다. `ftol`·`maxiter`·척도화 규칙은 §7.2 그대로다.
> **불변식**: 같은 입력이면 반환(x, nit, success, status)이 비트 같다(스레드·BLAS 무관).
> **상태**: 계획(② 선행).

### 4.4 §10.3 또는 §10.2 test 목록에 추가

> | NFR-4 | `test_blas_thread_determinism`(9회로) | `OPENBLAS_NUM_THREADS` 1 대 max(2, cpu) 별도 프로세스 | S0 전 필드 `value_fp` 같음, 탐색 결과 지문 같음 | ② 선행 |

### 4.5 history 기록 (H1, 계획서 아님)

> 2026-10-14 NFR-4 원인 조사(읽기 전용): 처음 갈림 = `start_intervals` 블록 안 scipy SLSQP 반복점(입력 같음), 라이브러리 = scipy 쪽 OpenBLAS(numpy 쪽 무관), 갈린 루틴은 미확인. 증폭 = SLSQP 반복 + float.hex 지문. 후보 A(결정론 SQP) 권고, B(런타임 고정) 근본 아님, C·D 제외.

### 4.6 함께 고칠 문서 문구 [사실: 현재 문구 위치]

- `E/search/macro_poles.py:15`(모듈 docstring) "SLSQP(`scipy`)가 목적을 줄인다" -> 엔진 결정론 SQP.
- 41 design §6.5(783행 '공동 SLSQP … as-built 그대로', 1389행) -- 알고리즘 같음, 구현 출처만 바뀜을 한 줄.
- `E/tests/conftest.py:17-27` 스레드 1 고정 주석·코드, `E/tests/convergence/test_converge.py:243` 의 `OPENBLAS_NUM_THREADS="1"` -- 병합 때 거둔다(test agent 몫).

---

## 5. interface card 초안 (공개 계약만)

### 5.1 계약: 결정론 제약 최적화 함수

```
minimize_sqp(fun, x0, *, bounds, constraints=(), jac=None, ftol, maxiter, callback=None) -> SqpResult
```
(이름·위치는 착수 때 확정: test glob 충돌 grep, `_module_map.py` 등록, 레지스트리 §2 개념별 정본표에 'SQP' 행.)

- `fun(x) -> float`. `x` 는 Python float tuple(또는 1차원 float 배열 -- 착수 때 하나로 고정).
- `bounds`: 변수마다 (lo, hi), 한쪽이 None이면 열림.
- `constraints`: `("eq" | "ineq", fun, jac 또는 None)` 의 tuple. `ineq` 는 `fun(x) >= 0`.
- `jac` 가 None이면 2점 전진 차분(스텝 규칙은 지금 scipy 기본과 같은 식 √ε·max(1, |x|) -- 착수 때 as-built 대조로 확정, 새 상수 없음).
- `ftol`, `maxiter`: 지금 호출부 값 그대로(§7.2). 기본값 없음(호출부가 반드시 넘긴다).
- `callback(x)`: 주 반복마다 한 번. True를 돌려도 멈추지 않는다(지금 호출부 사용과 같게 -- 착수 때 확인).
- 반환 `SqpResult`(불변): `x`(float tuple), `fun`, `nit`(int), `success`(bool), `status`(int, 의미 표 고정), `message`(str).
- **결정론 계약**: 같은 인자(함수가 같은 값을 내면)면 `SqpResult` 의 모든 칸이 비트 같다. 프로세스의 `OPENBLAS_NUM_THREADS`, `PYTHONHASHSEED`, numpy·scipy 설치 여부와 무관하다(내부에서 numpy·scipy를 import하지 않는다).
- 실패 규칙: 문제 형식 위반(경계 lo > hi, 길이 불일치)은 `ValueError`. 수렴 못 함은 예외가 아니라 `success=False` + status.

### 5.2 test 목록 (test author는 소스를 보지 않고 이 계약만으로 작성)

1. `test_sqp_thread_independent` -- 장난감 문제 세트(등식·부등식·경계 활성 섞음, 비볼록 포함)를 `OPENBLAS_NUM_THREADS` 1·2·max(2, cpu) 별도 프로세스에서 풀어 `SqpResult` 전 칸 비트 같음.
2. `test_sqp_no_blas_import` -- 모듈 AST에 numpy·scipy import 없음(구조 규칙 형식). 또는 import 후 `sys.modules` 에 scipy.optimize 미적재.
3. `test_sqp_kkt_oracle` -- 닫힌 해가 있는 문제(2변수 이차 목적 + 선형 제약, 활성 집합 바뀌는 경우)에서 해석해와 분해능 안(분해능 = 문제 선언에서 유도, 상수 박지 않음).
4. `test_engine_no_scipy_optimize` -- `E/` 소스 전수 AST: `scipy.optimize` import 0(재발 방지, G-8 lint 계열).
5. `tests/integration/test_blas_thread_determinism.py` 확장 -- 대상 회로를 two_stage_ota 하나에서 **library 9회로**로, 비교 필드를 출발 구간 8필드 + `device: start.row` 에서 **S0 전 필드 `value_fp`** 로. strict xfail 제거.
6. 탐색 단계 1회로 이상(two_stage_ota) 층 0·외층 결과 지문 스레드 1 대 N 같음(현재 test 범위 밖이던 §1.5 세 자리).
7. 기준선: 새 기준선은 test agent가 독립 측정(작성자≠검증자). 옛 기준선 대비 이산 구조 일치·연속값 차이를 보고(판정 아님).

### 5.3 xfail·고정 제거 조건

- test 5가 9회로에서 통과(XPASS가 아니라 xfail 표시 제거 뒤 PASS).
- 같은 변경에서 `E/tests/conftest.py` 의 `_BLAS_THREAD_ENV` 강제(17-27행)와 `E/tests/convergence/test_converge.py:243` 의 `OPENBLAS_NUM_THREADS="1"` 를 거둔다. 거둔 상태에서 전체 test가 바깥 `OPENBLAS_NUM_THREADS` 미지정·1·8 세 환경에서 같은 결과(독립 판정 V 항목).
- 엔진 소스에 `scipy.optimize` import 0(test 4).

### 5.4 착수 전 사용자 몫·확인 항목

- 기준선 재측정 승인(후보 A는 결과 비트를 바꾼다). 승인 없으면 B로 가되 '근본 아님' 기록 + 결함 test 유지.
- 구현 출처: scipy C(BSD-3) 이식 대 새 구현 -- 범위 결정.
- 외층 θ 차원(9회로) 실측 -> 순수 Python QP 비용 확인.
- 갈린 OpenBLAS 루틴 특정은 수정에 필요 없음(미확인으로 남김).

---

## 6. 측정 2 (사용자 승인 "결정 전 측정부터", 2026-10-14)

- 규칙은 같다. 읽기 전용 복제본 `wt/_nfr4_probe/repo`(master af10c9b, 측정 뒤 `git status` 0줄)만 썼고, 저장소 수정·커밋은 없다. 원자료는 `wt/_nfr4_probe/measure2/`.
  - harness `run_full.py`: 단계 A -> B -> `build_search_context` -> `find_front(sctx, [])`. 탐색 설정은 test 와 같은 `SearchSettings(600 s, 평가 40, 저항 (1e2,1e5), 용량 (1e-13,1e-10))`. 실행기 `launch.sh`, 작업 목록 `jobs.txt`, 실행 결과 `runs/<회로>__t<스레드>_<풀이기>_<자리>_r<재생>/`(`calls.jsonl` 호출마다 한 줄, `summary.json`).
  - 시제품 `sqp_proto.py`(A = backend "py", A2 = "np"), 장난감 확인 `toy_check.py`, 분석 `analyze2.py` -> `results.md`, `quality2a.py` -> `quality2a.md`, A2 크기 시험 `a2_maxn.py` -> `a2_maxn.txt`, numpy 문턱 `np_threshold.py` -> `np_threshold.txt`, 복소 LU `micro_zlu.py` -> `micro_zlu.txt`, 재현 `dbg_analyse.py`·`rep_lu.py`·`lu17.pkl`, 고정 확인 `runs_zlu/`.
- 실행: 9회로 × {scipy t1(재생 켬), scipy t8, A t1/t8/t18, A2 t1/t8/t18, A 커널 자리만 t1, A2 커널 자리만 t1} = 90 실행, 9개씩 병렬.
- **시간 주의**: 9개 병렬 부하 안의 벽시계라 실행 사이 총 시간 비교는 잡음이 크다(같은 회로의 find_front 시간이 실행마다 2배 넘게 흔들림). 그래서 풀이기 비용은 '풀이기 안 시간'(최소화 호출 시간 − 콜백 시간)으로 비교한다.
- `ngcc_3stage_ff` 는 단계 A 가 `review_needed`(탐색 없음)라 SLSQP 호출이 0이다. 표에는 그대로 둔다.

### 6.1 SLSQP 호출 통계 (scipy, OPENBLAS_NUM_THREADS=1) [사실]

| 회로 | 상태 | 자리 | 호출 | n (최소/중앙/최대) | m_eq/m_ineq 최대 | nit 합/중앙/최대 | 함수평가 합 | 예외(_Abort) | SLSQP 안 시간 s | 콜백 포함 s |
|---|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | ok/ok | layer0_center:235 | 2 | 2/2/2 | 0/6 | 28/14/14 | 48 | 0 | 0.082 | 0.09 |
| common_gate_amplifier | ok/ok | layer0_center:374 | 1 | 10/10/10 | 0/15 | 1/1/1 | 1 | 0 | 0.001 | 0.00 |
| common_gate_amplifier | ok/ok | slsqp_outer:195 | 4 | 9/9/9 | 0/14 | 7/6/6 | 8 | 2 | 0.008 | 2.92 |
| current_reuse_telescopic_ota | ok/ok | layer0_center:235 | 8 | 8/8/8 | 0/54 | 176/23/24 | 197 | 0 | 0.063 | 0.11 |
| folded_cascode | ok/ok | layer0_center:235 | 2 | 6/6/6 | 0/26 | 36/18/18 | 34 | 0 | 0.085 | 0.09 |
| folded_cascode | ok/ok | layer0_center:374 | 1 | 26/26/26 | 0/40 | 1/1/1 | 1 | 0 | 0.003 | 0.01 |
| folded_cascode | ok/ok | slsqp_outer:195 | 6 | 25/25/25 | 0/50 | - | 7 | 6 | 0.029 | 9.99 |
| ngcc_3stage_ff | review_needed/None (탐색 없음) | (호출 없음) | 0 | | | | | | | |
| nmcnr_amplifier | ok/ok | layer0_center:235 | 8 | 5/5/5 | 0/16 | 276/31/70 | 333 | 0 | 0.038 | 0.06 |
| nmcnr_amplifier | ok/ok | layer0_center:374 | 1 | 36/36/36 | 0/47 | 1/1/1 | 1 | 0 | 0.002 | 0.02 |
| nmcnr_amplifier | ok/ok | macro_poles:345 | 8 | 5/5/5 | 1/2 | 491/100/100 | 5115 | 0 | 2.603 | 26.35 |
| pushpull_follower_buffer | ok/ok | layer0_center:235 | 2 | 4/4/4 | 0/12 | 26/13/13 | 26 | 0 | 0.071 | 0.08 |
| pushpull_follower_buffer | ok/ok | layer0_center:374 | 1 | 15/15/15 | 0/24 | 1/1/1 | 1 | 0 | 0.005 | 0.01 |
| pushpull_follower_buffer | ok/ok | slsqp_outer:195 | 3 | 14/14/14 | 0/25 | - | 11 | 3 | 0.009 | 2.60 |
| sf_pushpull_output_opamp | ok/ok | layer0_center:235 | 8 | 3/3/3 | 0/16 | 231/28/36 | 267 | 0 | 0.083 | 0.12 |
| sf_pushpull_output_opamp | ok/ok | macro_poles:345 | 30 | 3/3/3 | 1/2 | 298/9/11 | 1192 | 0 | 1.115 | 9.68 |
| two_stage_ota | ok/ok | layer0_center:374 | 1 | 16/16/16 | 0/24 | 1/1/1 | 1 | 0 | 0.001 | 0.00 |
| two_stage_ota | ok/ok | macro_poles:345 | 40 | 3/3/3 | 1/2 | 502/9/100 | 2668 | 0 | 2.085 | 19.25 |
| two_stage_ota | ok/ok | slsqp_outer:195 | 2 | 15/15/15 | 0/30 | - | 4 | 2 | 0.004 | 2.55 |
| two_stage_ota_sf | ok/ok | layer0_center:374 | 1 | 19/19/19 | 0/29 | 1/1/1 | 1 | 0 | 0.001 | 0.00 |
| two_stage_ota_sf | ok/ok | macro_poles:345 | 65 | 4/4/4 | 1/2 | 664/10/23 | 3412 | 0 | 1.412 | 14.94 |
| two_stage_ota_sf | ok/ok | slsqp_outer:195 | 1 | 18/18/18 | 0/38 | - | 1 | 1 | 0.001 | 0.00 |

회로 전체(LUT 적재 제외, replay 시간 뺌) 대비 비율:

| 회로 | 실행 s (A+B+ctx+front) | find_front s | SLSQP 안 s | 비율(안) | SLSQP 콜백 포함 s | 비율(포함) |
|---|---|---|---|---|---|---|
| common_gate_amplifier | 129.9 | 8.2 | 0.091 | 0.0007 | 3.0 | 0.023 |
| current_reuse_telescopic_ota | 159.2 | 31.6 | 0.063 | 0.0004 | 0.1 | 0.001 |
| folded_cascode | 147.5 | 21.5 | 0.117 | 0.0008 | 10.1 | 0.068 |
| ngcc_3stage_ff | 1.6 | - | 0.000 | 0.0000 | 0.0 | 0.000 |
| nmcnr_amplifier | 190.9 | 22.4 | 2.642 | 0.0138 | 26.4 | 0.138 |
| pushpull_follower_buffer | 91.0 | 5.5 | 0.085 | 0.0009 | 2.7 | 0.030 |
| sf_pushpull_output_opamp | 136.4 | 6.2 | 1.198 | 0.0088 | 9.8 | 0.072 |
| two_stage_ota | 134.4 | 9.2 | 2.091 | 0.0156 | 21.8 | 0.162 |
| two_stage_ota_sf | 246.1 | 5.8 | 1.414 | 0.0057 | 14.9 | 0.061 |

- 변수 수 n 최대 = **36**(nmcnr `layer0_center:374`), 부등식 행 최대 = **54**(current_reuse `layer0_center:235`). 등식은 `macro_poles` 의 1행뿐이다.
- `layer0_center:374` 는 9회로 모두 nit = 1이다(시작점이 곧 해). `slsqp_outer:195` 는 평가 예산 40 안에서 대부분 `_Abort`(`candidate_failure`·`eval_budget`)로 끝난다. 끝까지 푼 것은 common_gate 1회뿐이다.
- 풀이기 안 시간 합은 회로 실행 시간의 0.04~1.6 %다. 콜백(엔진 평가)을 포함해도 0.1~16 %이며, 시간 대부분은 콜백이다.
- 벽시계 예산 정지(`stops_wall_budget`)는 9회로 모두 0이다.

### 6.2 scipy 스레드 1 대 8: layer0_center·slsqp_outer 도 갈리는가 [사실, 지난번 추측 확인]

'같은 x0 -> 다른 x' = 두 실행에서 입력 시작점이 비트 같은 호출 중 결과(x·nit·예외)가 다른 수.

| 회로 | 출발 구간 지문 | front 지문 | 자리별 '같은 x0 -> 다른 x' / 같은 x0 호출 수 | 처음 x0 가 갈린 자리 |
|---|---|---|---|---|
| common_gate_amplifier | 같음 | 같음 | layer0_center:235 0/2, layer0_center:374 0/1, slsqp_outer:195 0/4 | 없음 |
| current_reuse_telescopic_ota | 같음 | 같음 | layer0_center:235 8/8 | 없음 |
| folded_cascode | 같음 | 같음 | layer0_center:235 2/2, slsqp_outer:195 0/6 | layer0_center:374 |
| ngcc_3stage_ff | 같음 | - |  | 없음 |
| nmcnr_amplifier | 다름(17필드) | 같음 | layer0_center:235 6/6, macro_poles:345 4/4 | macro_poles:345 |
| pushpull_follower_buffer | 같음 | 다름 | layer0_center:235 2/2, slsqp_outer:195 1/3 | layer0_center:374 (호출 수 6 대 11) |
| sf_pushpull_output_opamp | 다름(24필드) | 같음 | macro_poles:345 6/6 | macro_poles:345 |
| two_stage_ota | 다름(10필드) | 같음 | macro_poles:345 8/12, slsqp_outer:195 0/2 | macro_poles:345 |
| two_stage_ota_sf | 다름(12필드) | 같음 | macro_poles:345 22/22, slsqp_outer:195 0/1 | macro_poles:345 |

- **확인**: `layer0_center:235` 는 같은 입력에서 4회로가 갈린다(current_reuse 8/8, folded 2/2, nmcnr 6/6, pushpull 2/2).
- `slsqp_outer:195` 는 pushpull 에서 같은 입력 1/3이 갈리고, **front 지문도 달라진다**.
- `layer0_center:374` 는 nit = 1이라 갈림을 관측하지 못했다(같은 입력 1/1 같음). 결함이 없다는 증거는 아니다.
- 출발 구간이 갈리는 회로는 지난 측정의 3개에 **nmcnr_amplifier 를 더해 4개**다. 지금 test 는 two_stage_ota 하나만 본다.
- 층 0(`layer0_center:235`)의 갈림은 출발 구간이 같은 회로에서도 생긴다. 다만 이번 설정(평가 40)에서는 front 점이 0~1개라 front 지문까지 바뀐 것은 pushpull 하나였다.

### 6.3 두 번째 원인: 복소 `scipy.linalg.lu_solve` [사실, 새 발견]

- **어디서 보였나**: A(순수 Python SQP)로 4자리를 모두 바꾼 실행에서 two_stage_ota 만 출발 구간 `macro` 필드가 스레드 1 대 8·18 에서 달랐다. SLSQP 호출의 x 는 35/35 모두 같았다.
- **추적**(`dbg_analyse.py`): `MacroResult.ugf_hz`·`pm_deg` 의 마지막 비트가 다르다.
  - 같은 입력에서 처음 갈리는 호출은 `metrics/point_solve.py:47` `scipy.linalg.lu_solve((lu, piv), b - a @ x)`(복소 3×1)다. 호출 경로는 `_helpers_product.py:53` -> `crossing.py:96` -> `loop_analysis.py:92`.
  - 그 인자만 저장해 따로 재생해도(`rep_lu.py`) 스레드 1 대 8 결과가 마지막 비트에서 다르다.
- **무작위 시험**(`micro_zlu.py`, 1,000회, n = 1~11):
  - 복소 `lu_solve`(1차원·(n,1)·trans=1 모두)는 n = 3, 5~11 에서 갈린다.
  - 복소 `lu_factor` 와 numpy 복소 `solve` 는 같다. 실수 `lu_solve`(`micro_lusolve.py`, 2,000회)도 같다.
  - 즉 scipy 쪽 OpenBLAS 의 복소 getrs 경로가 스레드 수에 따라 갈린다.
- **엔진의 복소 `lu_solve` 자리**(코드 확인): `metrics/point_solve.py:46-47`, `metrics/sensitivity.py:81-83`, `metrics/_helpers_probe.py:125·128·139·140`. 실수만 쓰는 자리는 `_helpers_nodal.py`, `dc_limit.py`, `offset_analysis.py` 다.
- **고정 확인**(`runs_zlu/`): A에 '복소 `lu_solve` 동안만 scipy 쪽 스레드 1'을 더해 two_stage_ota 를 돌렸다.
  - 스레드 1·8·18 에서 출발 구간·front 지문이 같았다.
  - 고정 없는 A 스레드 1 결과와도 같았다.
  - 남은 차이가 이 한 경로뿐이었다는 증거다.
- **영향**: §1.4 와 §4.1 의 '다른 선형대수는 스레드 무관' 문장은 틀렸다(정정 표시함). 수정 범위는 SLSQP 4자리 + 복소 `lu_solve` 자리다.

### 6.4 시제품 (측정용, 엔진 이식 아님)

- **공통 구조**: Kraft SLSQP 를 따른다.
  - 구성: Powell 감쇠 BFGS(0.2), LDP→Lawson-Hanson NNLS 로 QP 풀이, 비호환 선형화는 보강 변수 δ(헤시안 100), L1 선 탐색(alfmin 0.1·최대 10회), 리셋 5회, 같은 형식의 수렴 판정.
  - 상수는 SLSQP 원문 값이다. 새로 정한 것은 LDP 행 척도(행 노름으로 나눔, 실현 집합 불변) 하나뿐이다.
  - 원문과 다른 점: 등식을 부등식 두 줄로 넣는다(원문 LSEI 는 등식을 소거한다).
- **A**: 선형대수 전부를 Python float 고정 순서 루프로 한다.
- **A2**: 반복은 A와 같고, 선형대수(cholesky·삼각해·lstsq·행렬곱)만 numpy 로 한다.
- 개발 중 결함 2건을 고쳤다: NNLS 0 나누기, LDP 척도를 빼면 `layer0_center:235` 에서 발산. 고친 뒤 9회로 전체를 다시 돌렸고 이전 결과는 버렸다.
- 장난감 60문제(`toy_check.py`): scipy 와 목적 상대차 ≤ 2.5e-7. 실패 3건은 scipy 도 반복 한도(100)에 걸린 같은 문제다.

### 6.5 결과

**(a)(b) 같은 입력 재생**: 순수 자리(`macro_poles:345`, `layer0_center:235`)는 scipy t1 실행 안에서, scipy 호출 직후 같은 콜백으로 A·A2 를 다시 풀었다(`quality2a.md`).

| 자리 | 시제품 | 문제 수 | 둘 다 성공 | 목적 상대차(둘 다 성공) | 목적 절대차 | 시제품이 더 낮음 / 더 높음 | scipy만 성공 / 시제품만 성공 / 둘 다 실패 | 풀이기 내부 시간 합 시제품/scipy | 위반 최대 시제품 / scipy (둘 다 성공) |
|---|---|---|---|---|---|---|---|---|---|
| layer0_center:235 | A2 | 30 | 30 | 중앙 5.2e-10 / 최대 1.0e+00 | 최대 3.8e-05 | 9 / 5 | 0 / 0 / 0 | 2.863 / 0.422 s (6.79배) | 5.1e-07 / 1.5e-07 |
| layer0_center:235 | A | 30 | 29 | 중앙 3.3e-09 / 최대 6.1e+00 | 최대 3.8e-05 | 8 / 9 | 1 / 0 / 0 | 0.899 / 0.422 s (2.13배) | 8.9e-07 / 1.5e-07 |
| macro_poles:345 | A2 | 143 | 128 | 중앙 3.4e-12 / 최대 1.6e-03 | 최대 3.2e-06 | 33 / 44 | 0 / 5 / 10 | 4.775 / 7.215 s (0.66배) | 7.8e-07 / 7.8e-07 |
| macro_poles:345 | A | 143 | 128 | 중앙 3.7e-12 / 최대 1.7e-03 | 최대 3.2e-06 | 38 / 43 | 0 / 6 / 9 | 2.267 / 7.215 s (0.31배) | 7.8e-07 / 7.8e-07 |

**커널 자리**(`layer0_center:374`, `slsqp_outer:195`): 이 두 자리만 바꾼 전체 실행에서 첫 호출(입력 비트 같음)을 비교했다(`results.md` 2b).
- `layer0_center:374`: 6/6 같은 해·같은 목적.
- `slsqp_outer:195`: 정지 사유가 같은 것은 A 11/13, A2 10/12. 다른 2건은 scipy 가 `candidate_failure` 로 멈춘 곳에서 시제품이 다른 반복점으로 가 `eval_budget` 까지 간 경우 등이다(common_gate).
- front 점 수는 9회로 모두 scipy 와 같다(0 또는 1).
- 이 두 자리의 풀이기 안 시간은 호출당 0.004~0.44 s다(scipy 0.001~0.007 s).

**(a) 시간**: 회로당 풀이기 안 시간 합의 scipy 대비 차이.

| 시제품 | 차이 범위 | 매크로(n = 3~5) | 층 0 Chebyshev(n ≤ 8, 행 ≤ 54) |
|---|---|---|---|
| A | −1.5 s ~ +0.75 s | 0.31배(scipy 보다 빠름) | 2.1배 |
| A2 | −0.45 s ~ +1.84 s | 0.66배 | 6.8배 |

- 회로 실행 시간(50~290 s) 대비 증가는 ≤ 1.5 %다.
- [추정 상한] 궤적이 달라 평가 수가 바뀌는 효과는 병렬 잡음보다 작아 따로 재지 못했다.

**(c) 스레드 1 / 8 / 18 비트 동일**: 4자리를 모두 바꾼 실행에서 출발 구간 지문 + front 지문 + 모든 SLSQP 호출의 x·nit·예외를 비교했다.

| 회로 | 시제품 | 출발 구간 지문 1=8=18 | front 지문 1=8=18 | 호출 x 전부 같음 | 실행 s (t1) / scipy t1 실행 s | SLSQP 안 s (t1) / scipy t1 |
|---|---|---|---|---|---|---|
| common_gate_amplifier | A | 예 | 예 | 예 (5 호출) | 60.5 / 129.9 | 0.017 / 0.091 |
| common_gate_amplifier | A2 | 예 | 예 | 예 (5 호출) | 61.5 / 129.9 | 0.045 / 0.091 |
| current_reuse_telescopic_ota | A | 예 | 예 | 예 (8 호출) | 100.7 / 159.2 | 0.328 / 0.063 |
| current_reuse_telescopic_ota | A2 | 예 | 예 | 예 (8 호출) | 102.3 / 159.2 | 1.294 / 0.063 |
| folded_cascode | A | 예 | 예 | 예 (9 호출) | 93.0 / 147.5 | 0.863 / 0.117 |
| folded_cascode | A2 | 예 | 예 | 예 (9 호출) | 95.8 / 147.5 | 1.159 / 0.117 |
| ngcc_3stage_ff | A | 예 | 예 | 예 (0 호출) | 2.2 / 1.6 | 0.000 / 0.000 |
| ngcc_3stage_ff | A2 | 예 | 예 | 예 (0 호출) | 1.1 / 1.6 | 0.000 / 0.000 |
| nmcnr_amplifier | A | 예 | 예 | 예 (10 호출) | 102.8 / 190.9 | 1.117 / 2.642 |
| nmcnr_amplifier | A2 | 예 | 예 | 예 (17 호출) | 119.3 / 190.9 | 2.194 / 2.642 |
| pushpull_follower_buffer | A | 예 | 예 | 예 (6 호출) | 51.9 / 91.0 | 0.050 / 0.085 |
| pushpull_follower_buffer | A2 | 예 | 예 | 예 (6 호출) | 47.6 / 91.0 | 0.156 / 0.085 |
| sf_pushpull_output_opamp | A | 예 | 예 | 예 (38 호출) | 63.3 / 136.4 | 0.466 / 1.198 |
| sf_pushpull_output_opamp | A2 | 예 | 예 | 예 (38 호출) | 60.8 / 136.4 | 1.027 / 1.198 |
| two_stage_ota | A | 아니오 | 예 | 예 (35 호출) | 108.7 / 134.4 | 2.690 / 2.091 |
| two_stage_ota | A2 | 예 | 예 | 예 (35 호출) | 112.9 / 134.4 | 3.933 / 2.091 |
| two_stage_ota_sf | A | 예 | 예 | 예 (67 호출) | 283.6 / 246.1 | 1.437 / 1.414 |
| two_stage_ota_sf | A2 | 예 | 예 | 예 (67 호출) | 291.0 / 246.1 | 2.392 / 1.414 |

- two_stage_ota A 의 '아니오'는 §6.3 복소 `lu_solve` 때문이다(`macro` 필드만). 그 경로를 고정하면 같다(§6.3 고정 확인).
- A2 two_stage_ota 가 '예'인 것은 궤적이 달라 그 경로의 차이가 비트에 닿지 않았을 뿐이다. 보장이 아니다.

**(d) A2 의 numpy 선형대수가 엔진 최대 크기에서 스레드 무관한가** (`a2_maxn.txt`, `np_threshold.txt`):
- 엔진 최대 크기는 n = 36(보강 변수 포함 37), LDP 행 ≤ 130 이다. 이 크기에서 다음이 스레드 1·8·18 비트 같았다.
  - cholesky·삼각해·lstsq·행렬곱·dot 300회.
  - A2 전체(n = 36, 부등식 60) 3문제.
- **문턱**: 정사각 n = 96 까지는 같고, **n = 128 부터 `numpy.linalg.solve`·`cholesky` 가 스레드에 따라 갈린다**. 엔진 최대의 약 3.5배 여유다.
- 회로가 커지거나 θ 차원이 늘면 A2 는 같은 결함을 다시 만난다.
- 엔진 MNA 의 `numpy.linalg.solve` 도 같은 문턱을 가질 것이다 [추측: 노드 수 128 이상 회로가 없어 미측정].

### 6.6 A / A2 / B 비교와 권고

| 항목 | A 순수 Python SQP | A2 엔진 SQP + numpy 선형대수 | B 런타임 스레드 고정(scipy 쪽 OpenBLAS 1) |
|---|---|---|---|
| 풀이기 속도(같은 입력) | 매크로 0.31배, 층 0(:235) 2.1배, 커널 자리 호출당 ≤ 0.44 s | 0.66배, 6.8배, ≤ 0.36 s | 측정 1: 비용 관측 안 됨 |
| 회로 실행 시간 증가 | ≤ 1.5 % (추정 상한) | ≤ 1.5 % (추정 상한) | 0 |
| 해 품질(같은 입력, 둘 다 성공) | 매크로 128/143: 목적 상대차 중앙 3.7e-12·최대 1.7e-3. scipy 실패 15건 중 6건 성공, scipy 성공인데 실패 0. 층 0 29/30(1건 실패, scipy 는 성공) | 매크로 128/143: 중앙 3.4e-12·최대 1.6e-3. 5건 추가 성공, 성공→실패 0. 층 0 30/30 | scipy 그대로 |
| 결정성 범위 | Python float 연산만 쓴다. BLAS 스레드·공급자·버전 무관. 9회로 1/8/18 같음(복소 `lu_solve` 수정 전제, §6.3) | numpy 결과가 같은 동안만: 실측 n ≤ 96 스레드 무관, n ≥ 128 갈림. 9회로 1/8/18 같음 | '스레드 1 경로' 재현만. OpenBLAS 버전·공급자·비공개 기호 이름에 의존. 고정을 SLSQP 와 복소 `lu_solve` 모두에 걸어야 함 |
| 근본 수정인가 | 예(SLSQP 몫). 복소 `lu_solve` 는 별도 수정 필요 | 부분(반복은 엔진 소유, 선형대수는 라이브러리 + 크기 문턱 test 로 감시) | 아니다(사용자 분류) |
| 기준선 영향 | 출발 구간·탐색 결과 비트가 바뀜 -> 기준선 재측정(사용자 승인) | 같음 | 없음(스레드 1 기준선 그대로) |
| 시제품 상태 | 층 0(:235) 1건 실패 -- 원문 LSEI(등식 소거)·LDP 정밀도 보강 필요 | 같은 코드 | -- |

**권고: A**. SLSQP 4자리를 순수 Python 결정론 SQP 로 바꾼다. 그리고 **같은 card 범위에 복소 `lu_solve` 자리**(`point_solve.py:46-47`, `sensitivity.py:81-83`, `_helpers_probe.py:125·128·139·140`)를 결정론 경로로 바꾸는 일을 넣는다. 대체 후보는 측정에서 스레드 무관이던 numpy 복소 `solve`, 또는 lu 인수 위 엔진 삼각해다(둘 다 측정 필요).

근거:
1. A 만 결정성이 라이브러리 크기 문턱·버전에 기대지 않는다(A2 는 n ≥ 128 에서 깨짐을 실측).
2. 속도 비용은 실행 시간의 1.5 % 이하로 측정됐고, 매크로에서는 오히려 빠르다.
3. 같은 입력에서 해 품질은 scipy 와 같은 수준이다(둘 다 성공 시 목적 상대차 중앙 1e-12 규모). 수렴 성공은 오히려 많다.

남은 위험은 층 0(:235) 1건 실패다. 이식 때 원문 LSEI 구조를 따르고, 9회로 + 장난감에서 '시제품 실패 ⊆ scipy 실패'를 완료 조건으로 둔다(판정은 독립 감사). B 는 비교 기준으로만 둔다.

### 6.7 design 40 §11 문장 갱신 초안 (§4.1 대체)

> (v1.9.2 결정 8. 원인(2026-10-14 실측 `wt/_drafts/engine/NFR4_BLAS_CARD_DRAFT.md` §1·§6): scipy 쪽 OpenBLAS 의 스레드 1 경로와 다중 스레드 경로가 (i) SLSQP(`_slsqplib`) 반복점, (ii) 복소 `lu_solve`(getrs) 결과를 다르게 낸다. (i)은 `macro_poles`·`layer0_center:235`·`slsqp_outer` 에서 같은 입력의 다른 결과로 실측됐고(출발 구간 4회로·front 1회로), (ii)는 `metrics/point_solve.py` 등에서 `MacroResult` 마지막 비트를 바꾼다. 수정: SLSQP 4자리를 엔진 소유 결정론 SQP(§7.4)로, 복소 `lu_solve` 자리를 스레드 무관 경로로 바꾼다. ①-b 의 test 환경 스레드 1 고정은 이 card 병합과 같은 변경에서 거둔다.)

### 6.8 test 목록 추가 (§5.2 에 더함)

8. 복소 LU 결정성: 복소 MNA 계(n = 3~40)에서 `point_solve`·`sensitivity`·`_helpers_probe` 결과가 스레드 1·8·18 비트 같음.
9. 9회로 전 단계(단계 A -> find_front) 스레드 1·8·18: 출발 구간 지문 + front 지문 + 엔진 SQP 호출 결과 같음(이번 harness 와 같은 비교).
10. 엔진 선형대수 크기 감시: 엔진이 numpy/scipy 에 넘기는 최대 행렬 크기를 9회로에서 재고, 스레드 무관이 실측된 크기(현재 n ≤ 96) 안인지 단언한다. 넘으면 FAIL(결정성 test 범위 밖으로 나갔다는 신호).
11. SQP 품질: 장난감 + 9회로 재생 문제에서 '엔진 SQP 실패 ⊆ scipy 실패'를 본다. 둘 다 성공 시 목적·위반은 기준 상수 없이 보고만 한다(판정 기준은 감사가 정한다).

---

## 7. 측정 3: 이산 판단이 스레드 수에 따라 뒤집히는가 + 반복 재현성 (2026-10-14)

- 범위: 설계 변경·수정 결정은 하지 않는다. 측정만 했다.
- 기준: 측정 복제본 `wt/_nfr4_probe/repo` 를 **34932a9** 로 옮겨 측정했다. af10c9b 대비 엔진 차이는 CONTRACT.md 2개뿐이고 코드 차이는 없다. 측정 뒤 `git status` 0줄이며, 저장소 수정·커밋은 없다.
- 원자료: `wt/_nfr4_probe/measure3/`.
  - harness `run3.py`, 실행기 `launch3.sh`(순차)·`launch3b.sh`(반복)·`pair.sh`(S0 적중/미적중), 분석 `analyze3.py` -> `results3.md`(전체 표·뒤집힌 항목 전부).
  - 실행 결과 `runs/<회로>__<tag>/record.json`.
- 실행: 단계 A -> B -> `build_search_context` -> `find_front(sctx, [])`. 설정은 test 와 같다(평가 40, 600 s). 9회로 실행 묶음은 아래와 같다.
  - 스레드 1·8·18 각 1회: 순차, 다른 부하 없음 = r1.
  - 같은 스레드 반복 r2·r3: 4개 병렬.
  - 기본(OPENBLAS_NUM_THREADS 미설정) 3회.
  - S0 적중/미적중 쌍(t1): 같은 S0 폴더로 두 번 실행.
  - 모든 실행은 별도 프로세스, 빈 표 캐시를 쓴다.
- 이산/연속 분리:
  - 이산: 단계 상태·정지 사유, 출발 구간 충돌 종류·비활성 목록·사다리 칸 수·행 bin·경계 출처, 매크로 기록 코드·선택된 다중 출발(`macro_call.chosen`)·`_state.macro_failed`, SLSQP 결과(성공/status/_Abort 사유, nit 따로 표시), 층 0(`hard_ok`·stop·start_status·출처·cells·iterations 등), 시작점 목록, ε 풀이별 stop·aborts·frozen·restarts·best, front/pending/unmeasured 점 집합(점 id = 출처 tag), 평가마다 status·실패 class·active 제약 집합·cone active·미측정.
  - 연속: 그 외 값.
  - 연속 비교는 같은 구역(같은 eval·같은 SLSQP 호출·같은 solve 등)의 이산이 같을 때만 한다.
  - 분해능은 엔진 선언값만 썼다: b_P(`Objectives.power_resolution_w`), b_A(`domain.area_resolution_m2`), 제조 격자(`manufacturing_grid_m`, L·W), `ConstraintRow.c`(이미 분해능 단위), 층 0 `t`(허용오차 단위). 새 상수는 없다.

### 7.1 회로별 이산 판단 일치 (기준 = 스레드 1 r1) [사실]

| 회로 | 이산 키 수 | 8 과 다른 키 | 18 과 다른 키 | 8 대 18 다른 키 | 다른 범주(8 / 18) |
|---|---|---|---|---|---|
| common_gate_amplifier | 507 | 0 | 0 | 0 | - / - |
| current_reuse_telescopic_ota | 747 | 7 | 7 | 0 | SLSQP / SLSQP |
| folded_cascode | 730 | 0 | 0 | 0 | - / - |
| ngcc_3stage_ff | 2 | 0 | 0 | 0 | - / - |
| nmcnr_amplifier | 853 | 8 | 8 | 0 | SLSQP / SLSQP |
| pushpull_follower_buffer | 606 | 156 | 156 | 0 | SLSQP, 층 0, 탐색·front, 평가(봉인·제약) / SLSQP, 층 0, 탐색·front, 평가(봉인·제약) |
| sf_pushpull_output_opamp | 714 | 8 | 8 | 0 | SLSQP / SLSQP |
| two_stage_ota | 804 | 7 | 7 | 0 | SLSQP / SLSQP |
| two_stage_ota_sf | 981 | 2 | 2 | 0 | SLSQP / SLSQP |

- 8 과 18 은 9회로 모두 이산이 서로 같다(다중 스레드 경로는 하나).
- 범주 정리:
  - **SLSQP 반복 수(nit)만 다른 회로**: current_reuse(층 0 :235 7건), nmcnr(매크로 3·층 0 5), sf_pushpull(층 0 :235 8), two_stage_ota_sf(매크로 2).
  - **SLSQP 종료 상태가 다른 회로**: two_stage_ota(매크로 1건 status 9 → 8, nit 6건).
  - **판단까지 뒤집힌 회로**: pushpull_follower_buffer 하나(아래 §7.2).

### 7.2 뒤집힌 이산 항목 (반복 수 제외) [사실]

| 회로 | 항목 | 스레드 1 | 8·18 | 위치·원인 경로 |
|---|---|---|---|---|
| pushpull_follower_buffer | `layer0/hard_ok` | True | False | `layer0_center:235` SLSQP(전류 중심 u) 해가 스레드에 따라 다르다(centre_u 마지막 비트 `0x1.bbed50a9c218fp-2` 대 `…d8747p-2`). 그 결과 층 0 시작점에서 `w_min:M1` 제약 c 가 +1.13e-10 대 −2.30e-06(분해능 단위)으로 부호가 바뀐다. 이 값은 경계 위에 놓인다: `layer0_center.py:238-242` 의 e^u 끌어올림이 W = W_min 을 겨냥한다 [경로는 사실, '겨냥해서 0 근처'는 코드 주석 근거]. 부호 판정 `np.all(c >= 0)` 이 `layer0_center.py:683`(hard_ok)·`:407`(최선점 선택 키)에 있다 |
| 〃 | `search/solve[EP:s1]` aborts / frozen / restarts | 3개 / 없음 / 2 | 8개(`frozen:L:M1` 포함) / ((L, M1),) / 6 | 시작점 c 부호가 달라 외층 SLSQP(`slsqp_outer:195`)의 첫 QP 가 다르고, FD 열 실패로 L:M1 이 고정된다. 판정 `slsqp_outer.py:230` `np.all(c >= 0)` |
| 〃 | `slsqp_outer:195` 6번째 호출 종료 | `_Abort:eval_budget` | `_Abort:fd_column_failure` | 위와 같은 경로 |
| 〃 | 커널 평가 수(`eval/count`, perf kernel_calls·unique_keys) | 40 | 52 | 위와 같은 경로(재시작 증가) |
| 〃 | 평가 봉인 결과 eval[30]·[34]·[35]·[36]·[37] | sealed | failed(SEAL_VIOLATION, M2) | 다른 반복점을 평가한 결과(같은 seq 번호지만 다른 점) |
| 〃 | active 제약 집합 eval[18~22, 27~29, 32, 38~40] | … | `spec:area_search_m2<=` 추가 | 같음(다른 점) |
| 〃 | `search/failed_eps` 내용 | aborts 3개 | aborts 8개 | 같음 |
| two_stage_ota | 매크로 SLSQP 35번째 호출 종료 | status 9(반복 한도, nit 100) | status 8(선 탐색 양의 방향 미분, nit 11) | `macro_poles.py:345` SLSQP. 두 쪽 모두 실패라 그 호출의 채택(`macro_call.chosen`)·매크로 기록 코드·`_state.macro_failed` 는 같다 -- 하류 이산 판단은 바뀌지 않았다 |

**지난번 미확인 2건의 답**:
1. **pushpull 의 front 지문 차이**: front 점 집합 차이가 아니다.
   - front·pending_front·unmeasured_front 는 스레드 1·8·18 모두 **비어 있다**(같음).
   - 측정 2의 front 지문에는 `failed_eps`(정지 사유·aborts·accepted)가 들어 있었고, 차이는 그쪽이다.
   - 그 밑에는 위 표의 이산 판단 뒤집힘(층 0 hard_ok → 외층 경로 → 평가 수 40 대 52)이 있다.
2. **nit 100 대 11 이 이후 이산 판단을 바꾸는가**: 바꾸지 않았다.
   - 측정 1 기록상 이 사례는 two_stage_ota 매크로 호출이다(two_stage_ota_sf 아님). 이번 측정에서도 two_stage_ota 35번째 매크로 SLSQP 가 status 9(nit 100) 대 status 8(nit 11)이었다.
   - 둘 다 실패라 그 macro_solve 의 선택 출발점·기록 코드·`macro_failed`·출발 구간 이산(사다리 칸 수·충돌·bin)은 같았다.
   - two_stage_ota_sf 는 nit 차이(22 대 26, 14 대 19)뿐이고 이산 판단은 같았다.

### 7.3 연속 차이 (같은 구역의 이산이 같을 때) [사실]

| 필드 부류 | 비교 수 | 다른 수 | 다른 회로 | 상대차 최대 | 분해능 비 최대 (abs 차/분해능) | 분해능 출처 |
|---|---|---|---|---|---|---|
| `eval[].c.*` | 13392 | 7888 | folded_cascode, nmcnr_amplifier, pushpull_follower_buffer, two_stage_ota, two_stage_ota_sf | 1.00e+00 | 1.34e+07 | ConstraintRow.c 는 분해능 단위(정규화 c = 여유/분해능) |
| `eval[].area_m2` | 468 | 386 | folded_cascode, nmcnr_amplifier, pushpull_follower_buffer, two_stage_ota, two_stage_ota_sf | 5.61e-01 | 5.05e+06 | domain.area_resolution_m2 (b_A) |
| `eval[].gate_area_m2` | 468 | 386 | folded_cascode, nmcnr_amplifier, pushpull_follower_buffer, two_stage_ota, two_stage_ota_sf | 5.61e-01 | 5.05e+06 | domain.area_resolution_m2 (b_A) |
| `start/row.*.w_m` | 252 | 94 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 4.42e-05 | 1.50e+01 | manufacturing_grid_m |
| `start/area_est_m2` | 16 | 8 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 1.31e-06 | 1.48e+01 | domain.area_resolution_m2 (b_A) |
| `eval[].power_w` | 468 | 386 | folded_cascode, nmcnr_amplifier, pushpull_follower_buffer, two_stage_ota, two_stage_ota_sf | 3.88e-02 | 6.13e-01 | Objectives.power_resolution_w (b_P) |
| `eval[].cone.*` | 11472 | 1400 | current_reuse_telescopic_ota, folded_cascode, nmcnr_amplifier | 5.60e-01 | 3.86e-01 | ConstraintRow.c 분해능 단위 |
| `layer0/t` | 12 | 4 | nmcnr_amplifier, two_stage_ota_sf | 1.66e-01 | 1.62e-01 | 봉인 여유 허용오차 단위(min s_i) |
| `eval[].kcl_residual_a` | 468 | 324 | folded_cascode, nmcnr_amplifier, pushpull_follower_buffer, two_stage_ota, two_stage_ota_sf | 2.00e+00 | 분해능 없음 | 분해능 없음 |
| `eval[].theta.*` | 22966 | 6556 | current_reuse_telescopic_ota, folded_cascode, nmcnr_amplifier, pushpull_follower_buffer, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 8.89e-01 | 분해능 없음 | 분해능 없음 |
| `layer0/centre_u` | 12 | 10 | current_reuse_telescopic_ota, folded_cascode, nmcnr_amplifier, pushpull_follower_buffer, sf_pushpull_output_opamp | 7.32e-01 | 분해능 없음 | 분해능 없음 |
| `slsqp[]macro_poles:345.x[]` | 938 | 688 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 6.49e-01 | 분해능 없음 | 분해능 없음 |
| `slsqp[]layer0_center:374.x[]` | 244 | 66 | folded_cascode, nmcnr_amplifier, pushpull_follower_buffer, two_stage_ota, two_stage_ota_sf | 1.66e-01 | 분해능 없음 | 분해능 없음 |
| `slsqp[]layer0_center:235.x[]` | 94 | 84 | current_reuse_telescopic_ota, folded_cascode, nmcnr_amplifier, pushpull_follower_buffer | 1.41e-01 | 분해능 없음 | 분해능 없음 |
| `layer0/start.theta.*` | 232 | 62 | folded_cascode, nmcnr_amplifier, pushpull_follower_buffer, two_stage_ota, two_stage_ota_sf | 4.07e-02 | 분해능 없음 | 분해능 없음 |
| `search/start.*.theta.*` | 232 | 62 | folded_cascode, nmcnr_amplifier, pushpull_follower_buffer, two_stage_ota, two_stage_ota_sf | 4.07e-02 | 분해능 없음 | 분해능 없음 |
| `eval[].failure.margin` | 90 | 64 | folded_cascode, nmcnr_amplifier, sf_pushpull_output_opamp | 1.92e-02 | 분해능 없음 | 분해능 없음 |
| `start_state[].area` | 358 | 268 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 7.43e-06 | 분해능 없음 | 분해능 없음 |
| `start/macro.pole[]` | 24 | 20 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 3.06e-06 | 분해능 없음 | 분해능 없음 |
| `start/rung[].theta.*` | 2520 | 386 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 2.62e-06 | 분해능 없음 | manufacturing_grid_m |
| `start/row.*.ln_idu` | 252 | 62 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 2.24e-06 | 분해능 없음 | 분해능 없음 |
| `start/row.*.i_start` | 252 | 88 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 2.02e-06 | 분해능 없음 | 분해능 없음 |
| `start/macro.gm.*` | 20 | 14 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 2.02e-06 | 분해능 없음 | 분해능 없음 |
| `start/macro.cap.*` | 10 | 2 | two_stage_ota | 1.29e-06 | 분해능 없음 | 분해능 없음 |
| `start/rung[].current_ref.*` | 910 | 170 | nmcnr_amplifier, sf_pushpull_output_opamp | 9.93e-07 | 분해능 없음 | 분해능 없음 |
| `start/row.*.gm_id_lo` | 252 | 54 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 8.93e-07 | 분해능 없음 | 분해능 없음 |
| `start/row.*.source[].value` | 2366 | 108 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 8.93e-07 | 분해능 없음 | 분해능 없음 |
| `start/conflicts[].bound.*` | 66 | 64 | nmcnr_amplifier, sf_pushpull_output_opamp | 7.27e-07 | 분해능 없음 | 분해능 없음 |
| `start/conflicts[].gap` | 64 | 64 | nmcnr_amplifier, sf_pushpull_output_opamp | 5.32e-07 | 분해능 없음 | 분해능 없음 |
| `start/row.*.gm_id_chosen` | 252 | 64 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 5.15e-07 | 분해능 없음 | 분해능 없음 |
| `start/macro.pm_deg` | 8 | 8 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 3.59e-07 | 분해능 없음 | 분해능 없음 |
| `start/macro.res.*` | 2 | 2 | two_stage_ota | 1.33e-07 | 분해능 없음 | 분해능 없음 |
| `start/macro.ugf_hz` | 8 | 8 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 1.79e-10 | 분해능 없음 | 분해능 없음 |
| `start/row.*.gm_id_hi` | 252 | 42 | nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | 4.22e-11 | 분해능 없음 | 분해능 없음 |

차이가 없던 연속 필드 부류: `layer0/start_failure.margin`, `search/front[].area_m2`, `search/front[].power_w`, `search/resolution.b_A_m2`, `search/resolution.b_P_grid_w`, `search/resolution.e_eps`, `slsqp[]slsqp_outer:195.x[]`, `start/area_fraction`, `start/row.*.l_chosen`, `start/row.*.l_hi`, `start/row.*.l_lo`, `start/rung[].t`

이산 차이가 난 구역이라 연속 비교에서 뺀 필드 부류(건수): `eval[].area_m2`(24), `eval[].c.*`(456), `eval[].cone.*`(216), `eval[].gate_area_m2`(24), `eval[].kcl_residual_a`(24), `eval[].power_w`(24), `eval[].theta.*`(504), `slsqp[]layer0_center:235.x[]`(210), `slsqp[]macro_poles:345.x[]`(82)

읽는 법:
- **같은 점의 값 차**(입력 점이 같다고 볼 수 있는 출발 구간):
  - `start/row.*.w_m` 최대 **15 격자 단위**(제조 격자 5 nm).
  - `start/area_est_m2` 최대 **14.8 b_A**.
  - `layer0/t` 최대 0.16 허용오차 단위.
  - 매크로 gm·pm·ugf 는 상대 ≤ 2e-6 이지만 **분해능 없음**.
- **`eval[]` 행은 다른 점을 비교한 경우가 많다**. 같은 seq 번호가 같은 θ 를 뜻하지 않는다(층 0·외층 반복점이 이미 달라 θ 상대차 최대 0.89). 그래서 `eval[].c.*` 1.3e7, `area_m2` 5e6 b_A 같은 큰 비는 '같은 점의 수치 잡음'이 아니라 '다른 점'이다. 같은 점 대응을 θ 비트 일치로 다시 맞추는 분석은 하지 않았다 [미측정].
- **분해능이 정의되지 않은 필드**(차이가 난 것): `eval[].kcl_residual_a`, `eval[].theta.*`, `layer0/centre_u`, SLSQP 변수(`macro_poles`·`layer0_center:235·374` 의 x), `layer0/start.theta.*`, `search/start.*.theta.*`, `eval[].failure.margin`, `start_state[].area`, `start/macro.pole[]·gm·cap·res·pm_deg·ugf_hz`, `start/rung[].theta.*`(L 성분 외), `start/rung[].current_ref.*`, `start/row.*.ln_idu·i_start·gm_id_lo·gm_id_hi·gm_id_chosen·source[].value`, `start/conflicts[].gap·bound.*`.

### 7.4 같은 스레드 반복 재현성 + S0 적중 대 미적중 [사실]

각 칸 = 'r1 대 r2; r1 대 r3'. 비교 = 이산 + 연속 + S0 전 필드(`search_base.fp` = 탐색 기준 스냅샷의 값 내용 지문, 모든 필드 value_fp 포함) + 단계 A·B s1.snapshot.fp + context_fp. t1·t8·t18 의 r1 은 순차 실행분(common_gate t1 r1 은 S0 기록 추가 전 실행이라 S0 칸 비교 없음). S0 적중 대 미적중 칸은 적중 실행에서 다시 계산되지 않는 출발 구간 관찰 기록(macro SLSQP·macro_call·start_state)을 빼고, 나머지 SLSQP 호출은 순서열로 비교.

| 회로 | t1 | t8 | t18 | 기본(미설정) | 기본 대 t18 | 기본 대 t1 | S0 적중 대 미적중(t1) | s0_snapshot (1회→2회) |
|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음 | 같음 | 다름(A s1.fp, B s1.fp) | 'miss'→'hit' |
| current_reuse_telescopic_ota | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음 | 다름(이산, 연속) | 다름(A s1.fp, B s1.fp) | 'miss'→'hit' |
| folded_cascode | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음 | 다름(연속) | 다름(A s1.fp, B s1.fp) | 'miss'→'hit' |
| ngcc_3stage_ff | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음 | 같음 | 같음 | 'miss'→'miss' |
| nmcnr_amplifier | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음 | 다름(이산, 연속, S0 전 필드(base.fp)) | 다름(A s1.fp, B s1.fp) | 'miss'→'hit' |
| pushpull_follower_buffer | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음 | 다름(이산, 연속) | 다름(A s1.fp, B s1.fp) | 'miss'→'hit' |
| sf_pushpull_output_opamp | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음 | 다름(이산, 연속, S0 전 필드(base.fp)) | 다름(A s1.fp, B s1.fp) | 'miss'→'hit' |
| two_stage_ota | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음 | 다름(이산, 연속, S0 전 필드(base.fp)) | 다름(A s1.fp, B s1.fp) | 'miss'→'hit' |
| two_stage_ota_sf | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음; 같음 | 같음 | 다름(이산, 연속, S0 전 필드(base.fp)) | 다름(A s1.fp, B s1.fp) | 'miss'→'hit' |

- **같은 스레드 반복은 비트 재현된다**: t1·t8·t18·기본 각각 3회가 9회로 모두 같다(이산·연속·S0 전 필드·context_fp).
- **기본(미설정) = 스레드 18 과 같다**(9/9). 기본은 스레드 1 과 7/9 회로에서 다르다. current_reuse·folded·pushpull 은 출발 구간(S0)은 같고 층 0 부터 다르며, nmcnr·sf_pushpull·two_stage_ota·two_stage_ota_sf 는 S0 부터 다르다.
- **3차 판정 관측(`_audit_u17_1b_r3/audit_report.md` 119행, 기본 스레드 base fp 4/9 회로가 2차와 다름)의 설명**: 같은 기본 스레드를 반복하면 결과는 비결정이 아니고 결정론적으로 '다중 스레드 경로' 결과다.
  - 2차 기준선은 pytest(conftest 스레드 1 강제) 안에서 잰 값이라 '스레드 1 경로'다.
  - 다른 4/9 회로는 이번 측정에서 S0 가 갈리는 바로 그 4회로(nmcnr·sf_pushpull·two_stage_ota·two_stage_ota_sf)다.
  - 따라서 원인은 실행 환경의 스레드 수 차이다 [사실: 이번 측정 / 2차 측정 환경이 pytest 안이었다는 것은 3차 판정 문서의 서술에 근거]. S0 적중/미적중 차이나 코드 차이는 아니다(아래).
- **S0 적중 대 미적중(같은 t1)**:
  - 하류 결과는 같다: 탐색 기준 스냅샷 `search_base.fp`, context_fp, 층 0·외층 SLSQP 호출 전부, 평가·front 이산/연속.
  - 다른 것은 단계 A·B 의 `s1.snapshot.fp` 뿐이다. 원인은 적중 실행의 단계 A 스냅샷이 디스크에서 읽은 **S0 전체(출발 구간 등 S0 수준 필드 포함)**라는 데 있다.
  - 확인: 적중 실행의 A·B `s1.snapshot.fp` = 미적중 실행의 `search_base.fp`(two_stage_ota·folded 대조, 둘 다 일치). 즉 같은 값을 다른 시점에 잰 것이고 값 결함이 아니다 [사실]. 후속 기록의 '단계 A s1.snapshot.fp 가 miss·hit 에서 다름' 관찰은 이것으로 설명된다.
- 측정 한계:
  - 비교 대상 S0 필드는 `search_base.fp` 하나(모든 필드 value_fp 를 담은 값 내용 지문)로 봤다. 필드별 목록 덤프는 harness 결함(`GraphRecord` 반복 불가)으로 남지 않았다.
  - 출발 구간 관찰 기록(매크로 SLSQP 등)은 적중 실행에서 다시 계산되지 않아 비교에서 뺐다.
