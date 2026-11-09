# IT-2c 착수 조건 'Circuit 접근 경로 결정' 판정 자료

- 작성 2026-10-22. 읽기 전용 분석 agent가 작성했다. 저장소 파일은 하나도 고치지 않았다.
- 정본 위치
  - design 41 v1.12.11: master `b0620220`. 4.7-3b 734행 (1)~(5), 739행 `graph.ss_nodal`, 760행 '이동 시점'·(가)/(나).
  - 계획 v6.33: N3.8(596행) '엔진 θ 고정 손계산 근거', N6.6 범위 1(1514행).
  - card: `wt/integ-it12/docs/02-design/specs/20261021-it2c-icm-config.{spec,interface}.md`, `20261021-it2-common.md` 104-108행.
- 엔진: integ/it12 head `6afe4758`. `git archive`로 `wt/_scratch_it2c/src/`에 풀었다.
- 실측 스크립트(엔진은 import만 했다)
  - `wt/_scratch_it2c/scripts/meas_it2c.py`: 회로마다 layer0 시작점을 봉인한다. 같은 봉인점에서 θ 고정 연립과 봉인점 컨덕턴스 계를 조립해 비교한다. (a)의 T_p·δA_num도 이 스크립트가 잰다.
  - `toy_b.py`, `toy_b_scan.py`: (b) 측정.
  - 결과: `wt/_scratch_it2c/out/meas.jsonl`, `toy_b.jsonl`.
- 봉인점 컨덕턴스 계의 조립: `graph.ss_nodal`은 head에 아직 없다(IT-2c가 새로 만든다). 그래서 design 739행과 같은 조립을 썼다. `conductance_matrix(ss.circuit)` + `nodal_factor`, 고정 집합 = ac 접지 ∪ 입력 넷이다. 앞선 측정 `_drafts/evidence/2026-10-21/dvout_feasibility.md`와 같은 경로다.

## 0. 결론

1. **같은 행렬이 아니고, 해도 다르다.** 734행 (2)의 θ 고정 follower 연립과 `graph.ss_nodal`은 미지수 집합, 행의 뜻, 물리 가정이 모두 다르다.
   - θ 고정 연립: 쓰기 소자마다 'ΔI = 0'을 둔다. W4 행은 'V_out = x'로 바꾼다.
   - `graph.ss_nodal`: 노드마다 KCL을 두고, 바이어스·입력 넷을 고정한다.
   - 실측(follower 구성 가능한 단일 출력 HZ 4회로): 행 변화율 차는 최대 0.18 V/V, 창 끝 차는 2~69 mV였다.
   - 두 계산 모두 DC 양이다. ss_nodal도 ω→0, 용량 개방이라 봉인점 KCL의 DC 야코비안이다. 그래서 둘을 가르는 축은 DC 대 AC가 아니다. 축은 **선형화하는 DC 방정식**이다. 'θ(쓰기 소자 전류·밀도) 고정 손계산식'과 'W·바이어스 고정 물리 KCL'의 차이다. design 760행이 (나)의 조건으로 건 '같다면'은 성립하지 않는다.
2. **(나)는 접근 경로 문제를 풀지 못한다.** design 734행 (4)에 따라 `icm_config`는 모든 구성에서 `region_rows`와 `saturation_window`를 부른다. `region_rows`는 `_Circuit`의 메서드이고, `saturation_window`는 `sizing.__all__`에 없다.
   - 그래서 (나)를 골라도 `Circuit`(또는 그 행 셋)과 `saturation_window`의 공개는 필요하다.
   - (나)가 바꾸는 것은 고임피던스(HZ) follower 감도의 **정의**뿐이다. θ 고정에서 W 고정 KCL로 바뀌고, 계획 N3.8 '엔진 θ 고정 손계산 근거'를 고쳐야 한다. 원래 취지와 다르다.
3. **권고는 (가′)다.** (가)를 다듬은 안이다. 계획 정의는 그대로 둔다.
   - `Circuit`만 IT-2c에서 `_helpers_dc_solve.py`로 옮기고 `Circuit`·`saturation_window`를 `sizing.__all__`에 공개한다. `solve`·`FAILURES`의 이동은 IT-2d에 남긴다.
   - `icm_config` READS에 `("node", "dc_v")`를 더한다.
   - extras 위치 계약을 고정한다.
   - **사용자 결정이 필요하다.** design이 결정을 비워 두었고, 카드 경계가 바뀐다(IT-2d 몫의 일부가 IT-2c로 옮겨진다). design 760·731행도 개정해야 한다. 계획 정의는 바뀌지 않는다.
4. **'IT-2c 착수 실측' (a)~(c)**
   - (a) **미측정**: current_reuse_telescopic_ota는 `layer0_start` 시작점이 None이었다. 이 회로는 차동 출력이라, IT-2c 갈래 순서상 T_p 판정 전에 `icm_config_differential_output_undeclared`로 끝난다.
   - (b) 대칭 정확 0 toy에서는 판정이 발동했다. 다만 **앞먹임 상쇄 toy 2000개 가운데 253개**는 조립 반올림으로 |V_out| ≈ 1e-16 V가 남았는데 δV_out = 0이라 '판정 가능'이 나왔다. 계획 N3.8 정의의 취지와 어긋날 수 있어 보고한다.
   - (c) 오라클 선언값은 vntol = 1e-7, reltol = 1e-4다.

## 1. 판정 1 -- 같은 행렬인가

### 1.1 엔진 코드가 실제로 조립하는 것

| 항목 | θ 고정 연립(734행 (2), `block_columns._Circuit` + `input_window._sensitivities`) | 봉인점 컨덕턴스 계(`graph.ss_nodal` 설계 = `conductance_matrix` + `nodal_factor`) |
|---|---|---|
| 미지수 | `FIXED_RELATIONS`(레일·W3 목표·입력 DC) 밖의 writer 넷 전부. 바이어스 gate 넷, 입력 DC 미선언 입력 포트, W3 아닌 내부 넷이 들어간다(`block_columns.py:277`). | 고정(ac 접지 = 레일 ∪ gate 전용 미구동 넷, 그리고 입력 넷) 밖이면서 G 행이 0이 아닌 노드(`_helpers_nodal.py:39-44`, `ss_circuit.py` 머리말). W3 목표 넷은 미지수다. |
| 행 n의 뜻 | 노드 n의 **writer 식 하나**를 선형화한 것(`writer_grad`, `block_columns.py:470-528`). MOS writer의 행은 `∂VGS/∂VDS = −gds/gm`, `∂VGS/∂VSB = gmb/gm`(ID 고정 음함수, `:474-475`)이므로 **그 writer 소자의 gm·Δvgs + gds·Δvds + gmb·Δvbs = 0, 곧 ΔI_m = 0**이다. 저항 writer 행은 s_far = s_near, 곧 ΔI_R = 0(`drop` 전류 고정, `:504-505`)이다. W4 행은 이웃 보간(`:506-528`)이고, follower에서는 'V_out = x'로 바꾼다(`input_window.py:38-41`). | 노드 n의 **KCL**: 닿는 모든 소자 gm·gmb·gds·1/R 스탬프의 합 = 0(`conductance_matrix`, `_helpers_nodal.py:26-33`). 이상 전류원은 개방이다(`ss_circuit.py:52`). |
| 종속 소자(writer 아닌 MOS) | 행이 없다. 전류가 x를 따라 바뀌어도 어느 식에도 들어가지 않는다. | KCL에 들어간다. gds를 통한 가지 전류 변화가 반영된다. |
| 물리 가정 | **θ 고정**: 쓰기 소자의 W·ID가 고정이고, 바이어스 gate가 움직여 전류를 지킨다. | **W·바이어스 전압 고정**(오라클 `.dc` 훑기와 같은 가정): 전류는 KCL이 정한다. |
| follower 닫음 | 반전 입력 u의 행은 θ 고정 writer 식(예 `vin_n` = M1 `vgs_gate`)이다. u = V_out은 강제되지 않는다(실측 s_u = 0.993~0.999, s_out = 1). | design (3)의 Schur 1칸으로 u = V_out을 정확히 강제한다(실측 s_u = s_out). |

두 연립이 같아지는 경우는 다음 셋이 모두 성립할 때뿐이다. 이것은 추론이고, 실측으로 확인하지 않았다.
- 모든 가지 전류가 이상 전류원으로 묶여 있다. 곧 종속 소자 gds = 0이다.
- 바이어스 gate 넷이 θ 고정 writer로 움직이지 않는다.
- W3 목표 넷이 없다.

library에서 측정 가능한 4회로는 모두 이 조건 밖이다.

### 1.2 실측 -- 같은 봉인점, 같은 행 셋(`region_rows`), 같은 끝 식(`saturation_window`)

조건은 다음과 같다.
- 출력 구조 = `high_impedance`(`node.dc_output_structure`), 두 입력, T_p 음수 후보 하나.
- θ 고정 follower: roots = (비반전 포트, (W4 뿌리, 출력)), design 734행 (4)의 꼴.
- KCL follower: v = v_x + u·v_u, u = V_out(design 734행 (3)의 Schur 꼴을 HZ 출력에 그대로 적용).
- 표의 '창'은 이동량 [dlo, dhi](V)다.

| 회로(layer0 봉인점) | W4 뿌리 / 출력 | θ 고정 창 | KCL 창 | 끝 차(mV) | 노드 감도 최대 차(V/V, 노드) | θ 고정에서만 움직이는 고정 넷 |
|---|---|---|---|---|---|---|
| two_stage_ota | OUT / OUT | [−0.584, +0.553] | [−0.615, +0.543] | 31 / 10 | 0.060 (O1·N_cc_rz) | `bias` s = −0.048 (ss에서는 ac 접지) |
| two_stage_ota_sf | OUT / vout | [−0.159, +0.541] | [−0.163, +0.519] | 4 / 22 | 0.093 (OUT) | `bias` s = −0.047 |
| folded_cascode | out / out | [−0.426, +0.447] | [−0.428, +0.453] | 2 / 6 | 0.061 (Vg7) | 없음(`bias3` s = 0) |
| ngcc_3stage_ff | Vout / Vout | [−0.791, +0.538] | [−0.844, +0.607] | 52 / 69 | 0.185 (V2) | 없음 |

- 4회로 모두 θ 고정 연립에만 있는 미지수가 있다. 바이어스 넷과 입력 넷이다(`unknown_only_in_theta`). 반대로 ss에만 있는 미지수는 0이다.
- 행 변화율 예(two_stage_ota)
  - M7(OUT–gnd): KCL 0.987, θ 1.000.
  - M4 계열(D3–vdd): KCL 0.058, θ 0.000. θ 고정에서는 다이오드 노드 D3가 움직이지 않는다.
  - CS–gnd: KCL 0.795, θ 0.837.
- 나머지 회로
  - nmcnr_amplifier는 `kvl_fixed`(W4 뿌리 = 레일 agnd)라 θ 고정 follower가 정의되지 않는다. design (3)이 맡는다.
  - common_gate_amplifier·pushpull_follower_buffer는 단일 입력이라 (5)가 맡는다.
  - current_reuse_telescopic_ota·sf_pushpull_output_opamp는 `layer0_start` 시작점이 None이었다.
  - HZ 판정 대상은 위 4회로다.

### 1.3 판정

- **같은 행렬·같은 해가 아니다.**
  - 행렬: 미지수 집합(바이어스·입력·W3 넷)과 행 정의(소자 전류 고정 대 노드 KCL)가 다르다.
  - 해: 감도 차가 최대 0.185 V/V, 창 끝 차가 최대 69 mV였다.
- DC/AC 분리 원칙에 비추어 보면 다음과 같다.
  - **둘 다 DC 감도다.** ss_nodal은 ω→0·용량 개방이고, gm·gds·gmb는 LUT의 ∂ID/∂V다. 그래서 봉인점 KCL의 DC 야코비안이다. 계획도 이 계를 'DC 야코비안'(1514행)·'DC 극한 전달과 같은 계'(596행)로 쓴다. 그러므로 'AC 양을 DC에 쓴다'는 문제는 없다.
  - **정의가 같은 양은 아니다.** 다른 축은 **측정 구성의 물리 가정**이다. 하나는 θ(쓰기 소자 전류·밀도) 고정 손계산이고, 다른 하나는 W·바이어스 전압 고정 물리 회로다. 주파수 0 소신호 대 DC 감도의 차이가 아니라, 같은 DC 회로를 어떤 변수를 고정하고 선형화하느냐의 차이다.
  - graph 규칙 3('정의가 다를 때만 새 필드, 축을 적는다')에 따라 두 계산은 같은 정의의 양이 아니다. 그래서 (나)로 바꾸면 'graph 정본 하나로 합치기'가 아니라 **HZ follower 창의 정의 변경**이다.
- 계획 안의 문언 차(보고): 1514행 앞부분은 "봉인 뒤 블록 하나가 봉인점 컨덕턴스 계(DC 야코비안)로 반전 입력 식별·**follower 행**·영역 경계 행을 함께 풀어"라고 적는다. 그런데 같은 단락 뒷부분과 N3.8(596행) '엔진 θ 고정 손계산 근거'는 HZ follower를 "W4 뿌리 행을 V_out = x로 바꾼 **같은 감도 연립**(θ 고정)"으로 정의한다. design 734행 (2)는 후자를 따랐다. 계획 문언 정리가 필요하다(4절).

## 2. 선택지 비교

공통 사실이 하나 있다. 이 사실이 (가)/(나) 선택보다 앞선다. design 734행 (4)에 따라 `icm_config`는 **모든 구성**((2) HZ·(3) KVL 고정·(5) 단일 입력)에서 다음을 한다.
- `region_rows`로 행을 세운다. 이 메서드는 `_Circuit`에 있다(`block_columns.py:247-268`).
- `saturation_window`를 부른다.

`icm_config`는 metrics 패키지라 규칙 C를 받는다. 그런데 `sizing/__init__.py`의 `__all__`에는 `saturation_window`도 `_Circuit`도 없다(실측 grep: `__init__.py` 9행 `from .block_columns import dc_columns`만 있고, `saturation_window`는 0건). 그러니 어느 선택지든 **행 셋 접근과 `saturation_window` 공개는 필요하다.** design 760행은 `Circuit`만 적었고 `saturation_window` 공개는 적지 않았다. 이것은 design 공백이다.

### (가) `Circuit`을 helper로 옮겨 `sizing.__all__`에 공개(design 760행 원안)

| 점검 | 결과 |
|---|---|
| graph 단일 정본 | follower 감도는 `saturation_window` 안 `_sensitivities` 하나가 푼다. 행 셋은 `region_rows` 하나다. 다시 만드는 생산자는 없다. **단, 동작점 값의 출처가 비어 있다.** `icm_config` READS는 'dc_columns READS(`node.dc_v` 제외)'(731행)이고, `dc_columns` READS(`block_columns.py:95-100`)에는 `node.dc_v`가 없다. `region_rows`·`writer_grad`는 노드전압 `values`가 필요하다(`:254`, `:485`). 값을 얻으려고 `solve`로 다시 풀면 `node.dc_v`의 **둘째 생산자**가 된다(금지). 그러므로 READS에 `("node", "dc_v")`를 넣어야 한다. 이는 다듬은 창 블록과 달리 봉인점 그대로의 값이 필요하기 때문이다. |
| 규칙 A | `_helpers_dc_solve.py`로 옮길 때, 검사기는 `_` 모듈의 **공개 함수**만 2파일 사용을 센다(`structure_checks.py:301-315` -- 클래스는 세지 않는다). 대상은 같은 하위 패키지 파일뿐이다(`:324-325`). `solve`까지 IT-2c에 옮기면 sizing 안 사용자는 `block_columns` 하나다. `icm_config`는 metrics라 세지 않는다. 그러면 `helper_single_user`로 FAIL한다. 그래서 IT-2c에서는 **`Circuit`(과 그 비공개 도우미 `_vgs_of_coordinate`·`_kind_sign`·`_vds_floor`·`_inward`)만** 옮기고 `solve`·`FAILURES`는 IT-2d로 미룬다. 이때 클래스는 검사기가 세지 않으므로 형식상 통과한다. 다만 규칙 취지('공용 helper = 2파일 이상')의 근거는 실사용자 둘(`block_columns`·`icm_config`, 그중 하나는 패키지 밖)이라, design에 그 근거를 적어야 한다. |
| 규칙 B | 공개 이름 `Circuit`을 `gmid_engine.sizing`에서 import하므로 위반이 없다. |
| 규칙 C | metrics(5) → sizing(4)는 아래층 방향이므로 허용된다. `__all__`에 `"Circuit"`, `"saturation_window"`를 더해야 한다. |
| DC/AC 분리 | 계획 정의 그대로다. HZ = θ 고정 DC 손계산 연립(`writer_grad`), KVL 고정·단일 입력 = 봉인점 DC 야코비안(`ss_nodal`). 위반이 없다. |
| 바뀌는 파일 | 새 `sizing/_helpers_dc_solve.py`(`Circuit` + 비공개 도우미). `sizing/block_columns.py`(`_Circuit` 정의 삭제 → import). `sizing/__init__.py`(`__all__` 2개). `_module_map.py`(helper 행, 지금 618·641행 근처). 새 `metrics/icm_config.py`. |
| 바뀌는 test | 새 `tests/sizing/test__helpers_dc_solve.py`(규칙 H, design은 IT-2d로 적음). `tests/` 안 `_Circuit` 직접 참조는 0건이다(head grep; 엔진 안 참조 = `block_columns.py`와 `input_window.py` docstring). `tests/metrics/test_icm_config.py`. |
| 계획 개정 | 정의는 바뀌지 않는다. 1514행 앞부분 문언('컨덕턴스 계로 … follower 행')은 정리해야 한다(1.3, 문언 정정). |
| design 개정 | 760행: 결정 기록, 이동 시점을 'Circuit = IT-2c, solve·FAILURES = IT-2d'로. 731행: READS에 `node.dc_v`. extras 계약(아래 점검표 5). `saturation_window` 공개. card 공통·IT-2c·IT-2d 재동결. |
| 실현 가능성 | 아래 점검표. 이 분석은 같은 계산을 `_Circuit`을 직접 써서 봉인점 4회로에서 끝까지 실행했다(1.2). |

실현 가능성 점검표 (가′):

| # | 점검 | 근거 | 결과 |
|---|---|---|---|
| 1 | `Circuit` 생성 입력 = 블록 투영 + extras | `_Circuit.__init__`이 읽는 열은 `dc_columns` READS뿐이다(`block_columns.py:162-195`). `icm_config` READS ⊇ 그 집합이다(731행). | 가능. 실측 스크립트가 `Projection.from_snapshot(snap, dc_columns.reads, extras)`로 만들었다. |
| 2 | 동작점 값 | `node.dc_v` + `node.dc_rail_v`(이미 READS) | READS 추가가 필요하다(design 개정). 다시 풀기는 금지다. |
| 3 | 행 셋 | `region_rows(values)`가 봉인점에서 None이 아니었다. | 4/4 회로에서 행이 있었다. |
| 4 | follower 감도·창 | `saturation_window(unknown, roots=(비반전, (W4 뿌리, 출력)), values, c.writer_grad, rows)` | 4/4 회로에서 값이 나왔다. 특이 0이었다. |
| 5 | extras 위치 계약 | `_Circuit.__init__`은 `theta_items, fixed_values, resistor_values, lut, *rest`이고, `rest[0]` = 선형 선언 소자다(`:163-164`). `icm_config` extras에는 spec 되먹임 선언이 더 붙는다(731행). | **위험**: 선형 선언이 없을 때 되먹임 선언이 `rest[0]`에 오면 `linear`로 잘못 읽힌다. `Circuit`에 넘길 extras는 앞 4(+선형) 칸만 잘라 넘기거나, `Circuit` 서명을 명시 인자로 바꿔야 한다. design이 정해야 한다. |
| 6 | 블록 안 상태 | `Circuit.override`·`tol_cells`(`:165`, `:194`)는 인스턴스 지역이다. | 블록 지역 memo는 승인 예외(O-15 (E)) 범위다. 새 graph 밖 cache는 없다. |
| 7 | 출력 W3 뿌리(S-OS1)·HZ 판정 | `writer_head(out)`이 (뿌리, relation)을 준다. 실측 `free_window` 4건이었고, nmcnr은 `rail`이었다. | 갈래 판정에 쓸 수 있다. 분류 정본은 `node.dc_output_structure`(READS)다. |

### (나) follower 행을 `graph.ss_nodal`로 푼다

| 점검 | 결과 |
|---|---|
| 같은 행렬 전제 | **성립하지 않는다**(1.3). (나)는 'graph 정본 하나로 합치기'가 아니라 HZ follower 정의를 θ 고정에서 W 고정 KCL로 바꾸는 것이다. |
| graph 단일 정본 | 감도 연립은 (3)·(5)와 같이 `kvl_sensitivity` 하나로 통일되어 코드 경로가 줄어든다. 하지만 **행 셋(`region_rows`)과 `saturation_window`는 여전히 필요하다.** 그래서 `Circuit` 접근 문제는 남는다(위 공통 사실). 동작점 값(`node.dc_v`) 공백도 똑같이 남는다. |
| 규칙 A·B·C | (가)와 같은 공개가 필요하다. `region_rows`만 함수로 꺼내는 길도 있지만, 그러면 `region_rows` 이름만 공개 함수로 옮기는 것이라 결국 (가)와 같은 종류의 이동이다. |
| DC/AC 분리 | ss_nodal은 DC 야코비안이므로 위반이 없다. 그러나 다듬은 창(`dc_window_refine`, 4.7-4)의 끝 풀이는 θ 고정 대신호 풀이(전류 θ 고정, W4 y로 V_out = x)다. 그래서 커널 측정 구성 창(W 고정 KCL)과 다듬은 창(θ 고정)의 **고정 변수가 달라진다**. 계획 N6.6 범위 1 '출발 창 = 같은 측정 구성·같은 기준의 커널 창'의 취지와 어긋날 수 있다(실측 끝 차 2~69 mV). |
| 물리 | KCL 쪽이 오라클 `.dc`(W·바이어스 고정)와 같은 가정이고, 반전 입력 u = V_out을 정확히 강제한다. θ 고정 쪽은 바이어스 gate(two_stage `bias`)를 움직여 전류를 지킨다. 그래서 오라클 측정 구성과 가정이 다르다. **어느 쪽이 오라클 값에 더 가까운지는 미확인**이다(SPICE 대조 없음). |
| 바뀌는 파일·test | (가)의 공개 변경 전부 + `icm_config` (2) 갈래가 `kvl_sensitivity`로 바뀐다. L8 (a) toy의 손계산 기대값(θ 고정 follower 연립 끝, 811행)이 바뀐다. 다듬은 창의 출발·끝 정의 정합 test도 바뀐다. |
| 계획 개정 | **필요**: N3.8(596행) '엔진 θ 고정 손계산 근거'(HZ follower 정의), N6.6 1514행, 다듬은 창의 출발 창 정의. **원래 취지와 다르다** -- 계획은 HZ를 "θ 고정 손계산으로 정의된다"고 적었다. |
| design 개정 | 734행 (2)·(4), 4.7-4 1·2, 811행 L8 (a), 760행. |
| 실현 가능성 | 계산은 가능하다. 실측 스크립트가 4회로에서 KCL follower 창을 냈다. 그러나 접근 문제를 풀지 못하므로 착수 조건 해소책이 되지 않는다. |

### (다) 행 셋을 graph 필드로 승격하고 (나)와 묶는다

방법: `dc_columns`가 마지막 풀이(봉인점) 행 셋을 새 필드(예 `device.dc_region_row`)로 쓴다. `icm_config`는 그것과 `ss_nodal`만 READS한다. 그러면 `Circuit` 공개가 필요 없고, `saturation_window`(함수 하나) 공개만 남는다.

| 점검 | 결과 |
|---|---|
| graph 단일 정본 | 행 여유(VDS − VDsat − tol)는 지금 `region_rows`(커널)·봉인 7·`metrics_aux._sat_devices`(`metrics_aux.py:108-128`)가 각자 잰다(기존 상태). 필드로 승격하면 정본 자리가 생긴다. 다만 새 필드이므로 계획 N3.3 필드표를 먼저 고쳐야 한다(S-7). |
| 규칙 A·B·C | `saturation_window` `__all__` 하나만 필요하다. |
| DC/AC | (나)와 같다(정의 변경 포함). |
| 계획·design 개정 | 둘 다 크다. 새 필드, HZ 정의 변경, 기존 생산자 정리가 필요하다. |
| 판단 | IT-2c 착수 조건 해소 범위를 넘는다. 구조 개선 후보로 기록만 하고 권고하지 않는다. |

(라) `icm_config`를 sizing 패키지에 두는 안: `nodal_solve`·`nodal_adjoint`(metrics `_helpers_nodal`)를 import해야 하는데, sizing(4) → metrics(5)는 규칙 C 위 방향이라 불가능하다. 기각한다.

## 3. 권고 -- (가′)

내용:
1. IT-2c가 `_Circuit`과 그 비공개 도우미를 `sizing/_helpers_dc_solve.py`로 옮긴다(이름 `Circuit`). `solve`·`FAILURES`·끝 풀이 관련은 IT-2d에 남긴다.
2. `sizing.__all__`에 `"Circuit"`, `"saturation_window"`를 더한다.
3. `icm_config` READS에 `("node", "dc_v")`를 더한다.
4. `Circuit`에 넘길 extras의 위치 계약을 design에 적는다.
5. HZ follower = θ 고정 연립(계획 정의 그대로)으로 둔다.

근거(원칙별 자기 점검):
- **graph 단일 정본**
  - 감도 연립: `_sensitivities` 하나.
  - 행: `region_rows` 하나.
  - 끝 식: `saturation_window` 하나.
  - 동작점: `node.dc_v` READS.
  - 둘째 생산자가 없다. 새 cache·사본 칸도 없다.
  - (나)는 같은 행렬이 아니므로 '정본 통합' 근거가 성립하지 않는다.
- **DC/AC 분리**: 두 계산 모두 DC 선형화이고, 계획이 정한 갈래(HZ θ 고정, KVL·단일 입력 KCL)를 그대로 지킨다.
- **물리 우선, 가장 일반적인 형태**
  - KCL+닫음은 출력 구조와 무관한 더 일반적인 꼴이다. 오라클과 가정이 같은 쪽도 KCL이다.
  - 다만 그 채택은 계획 정의 변경이고, 다듬은 창(θ 고정)과의 정합까지 함께 바꿔야 한다. 그래서 착수 조건 해소와 분리해 **별도 계획 안건**으로 올린다(아래 4절 ②).
  - 이 안건은 착수를 막지 않는다. (가′)의 공개 구조는 그 안건이 어떻게 정해져도 그대로 쓰인다. `region_rows`·`saturation_window`가 늘 필요하기 때문이다.
- **fail-closed**: `region_rows` None·특이 → `Window(None, None, 0, "unmeasured")`(731행 그대로). 동작점을 다시 풀어 채우는 대체는 없다.
- **상수 발명·회로 이름**: 새 상수 0, 회로 이름 0.

사용자 결정 필요 여부: **필요하다.** 범위가 바뀌기 때문이다. 카드 IT-2d 범위(helper 이동)의 일부가 IT-2c로 옮겨지고, design 760행이 결정을 비워 두었다. 계획 정의(취지)는 바뀌지 않는다. 결정 문안 초안은 다음과 같다.
- (1) (가′) 채택
- (2) design 41 개정 항목
  - 760행: 결정 기록, 이동 분할.
  - 731행: READS `node.dc_v`, extras 계약.
  - `saturation_window` 공개.
  - card 재동결.
- (3) 계획 1514행 앞부분 문언 정정(문언 정정, 정의 불변).

## 4. 함께 올릴 안건과 위험

- ① **design 공백 3건.** (가)/(나) 공통이다. IT-2c code 전에 design 개정이 필요하다.
  - `node.dc_v` 출처(731행)
  - `saturation_window` 공개(760행에 없음)
  - `Circuit` extras 위치 계약
- ② **계획 안건(별도, 원래 취지 관련).** HZ follower 측정 구성 창의 선형화 가정 문제다. 하나는 θ 고정(지금 계획)이고, 다른 하나는 W·바이어스 고정 KCL(오라클 가정, (3)·(5)와 같은 꼴)이다. 실측 끝 차는 2~69 mV, 감도 차는 최대 0.185 V/V다. 어느 쪽이 오라클에 더 가까운지는 미확인이다(oracle `.dc` 대조가 필요하다). 다듬은 창(θ 고정 끝 풀이)의 정의와 함께 정해야 한다.
- ③ **계획 문언 불일치.** 1514행 앞부분('컨덕턴스 계로 … follower 행')과 같은 단락 뒷부분·596행('W4 뿌리 행 … θ 고정')이 서로 다르게 적혀 있다.
- ④ **행 여유의 다중 계산(기존 상태).** `region_rows`·봉인 7·`metrics_aux._sat_devices`가 같은 VDS − VDsat − tol을 각자 잰다. 이 card 범위 밖이다. 백로그 후보다.

## 5. 'IT-2c 착수 실측' (a)~(c) -- head `6afe4758`

| 항목 | 결과 | 근거 |
|---|---|---|
| (a) current_reuse_telescopic_ota 봉인점 T_p·δA_num | **미측정**. 사유: `layer0_start(sctx).start is None`이라 봉인점이 없다. 대체 회로·점은 넣지 않았다(O-72 (1)). 추가 사실: 이 회로는 차동 출력(Vop·Vom)이다. IT-2c 갈래 순서상 선언이 없으면 `icm_config_differential_output_undeclared`, 선언이 있으면 S-OS2 `icm_config_differential_output_structure`로 T_p 판정 **전에** 끝난다(734행 (1), 735행 '차동 출력이면 … 이 판정 전에 끝나므로 쓰이지 않음'). 그래서 이 회로의 T_p·δA_num은 IT-2c 운영 경로에서 쓰이지 않는다. | `out/meas.jsonl` current_reuse 행 |
| (a) 참고: T_p 판정이 실제로 도는 단일 출력 2입력 회로(같은 식, 구동 = 레일 폭 1.8 V) | 아래 표 | `out/meas.jsonl` |
| (b) 진짜 A = 0 대칭 사례에서 갈래 발동 | `icm_config`가 head에 없어 **엔진 갈래 code의 발동은 잴 수 없다**. 정의 식(\|V_out\| ≤ \|z_u\|ᵀ\|r\|, `nodal_solve`·`nodal_adjoint`)만 toy로 쟀다. 대칭 반쪽 둘(b1 단일 출력 반대칭, gds = 0)과 차동 관측(b2): V_out = 0, δV_out = 0 또는 5e-16 V이고 **발동했다**. **앞먹임 영점(b3, R1 = 1/gm)을 무작위 gm·gds·R 2000개로 훑었다**: 253개는 조립 반올림으로 \|V_out\| ≤ 2.6e-16 V가 남았는데 r = 0이라 δV_out = 0이 되었다. 그래서 **'판정 가능'(발동 안 함)이 나왔고, 그 부호는 임의**다. δV_out은 LU 풀이 잔차만 전파하고 G 조립(스탬프 합)의 상쇄 반올림은 보지 못한다. | `out/toy_b.jsonl`. **계획 N3.8 정의('수치 분해능')의 취지와 어긋날 수 있어 멈춤 보고 대상이다.** dvout_feasibility.md §1 '상쇄를 정확히 다룬다 … zᵀr가 잡는다'는 조립 단계 상쇄에서는 성립하지 않았다. 실제 회로에서 진짜 A = 0 포트가 생길지는 미확인이다. 생기면 음수 후보로 잘못 셀 수 있다. |
| (c) 오라클 선언 vntol·reltol | **vntol = 1e-7, reltol = 1e-4**(abstol 1e-14, gmin 1e-15). 출처: `tools/spice_oracle/legacy_testbench.json:9` `options`. smoke 입력 3개(`smoke/current_reuse_telescopic_ota.{layout.engine,layout.topology,sizing.engine}.oracle_input.json:1423·1425`)도 같은 값이다. 참고: `oracle_simulate.py:402`는 options가 없으면 ngspice 기본(1e-3, 1e-6)을 쓴다. oracle 계획 N0 29행 '둘 다 없으면 실행하지 않는다'와의 관계는 확인하지 않았다(미확인, 이 card 범위 밖). | grep 실측 |

(a) 참고 표 -- `graph.ss_nodal`과 같은 조립, design 735행 식:

| 회로 / 관측 ← 구동 | T_p (V/V) | δV_out (V) | δA_num (V/V) | 판정 불능? |
|---|---|---|---|---|
| two_stage_ota OUT ← vin_n | −41.33 | 1.2e-14 | 6.7e-15 | 아니오 |
| two_stage_ota OUT ← vin_p | +41.78 | 1.8e-12 | 1.0e-12 | 아니오 |
| two_stage_ota_sf vout ← vin_n | −31.20 | 2.8e-14 | 1.5e-14 | 아니오 |
| two_stage_ota_sf vout ← vin_p | +31.49 | 1.5e-14 | 8.3e-15 | 아니오 |
| folded_cascode out ← vin_n | −28.77 | 2.1e-13 | 1.2e-13 | 아니오 |
| folded_cascode out ← vin_p | +28.75 | 1.2e-13 | 6.6e-14 | 아니오 |
| ngcc_3stage_ff Vout ← Vinn | −144.96 | 6.3e-13 | 3.5e-13 | 아니오 |
| ngcc_3stage_ff Vout ← Vinp | +147.10 | 8.3e-13 | 4.6e-13 | 아니오 |
| nmcnr_amplifier Vout ← Vin_n | −132.75 | 3.8e-13 | 2.1e-13 | 아니오 |
| nmcnr_amplifier Vout ← Vin_p | +192.21 | 7.2e-13 | 4.0e-13 | 아니오 |
| common_gate_amplifier vout ← vin(단일 입력, 판정 안 함) | +7.52 | 0 | 0 | -- |
| pushpull_follower_buffer vout ← vin(단일 입력) | +0.637 | 2.6e-16 | 1.5e-16 | -- |

반전 입력 후보는 2입력 5회로 모두 음수 1개(`vin_n`·`Vinn`·`Vin_n`)로 정해졌다. 실측은 layer0 봉인점 하나이고, 탐색 해는 재지 않았다.

## 6. 미확인

1. θ 고정 창과 KCL 창 가운데 어느 쪽이 오라클 `.dc` ICMR에 가까운지(SPICE 대조 없음).
2. current_reuse_telescopic_ota·sf_pushpull_output_opamp 봉인점(layer0 시작점 없음). heldout 4회로는 재지 않았다.
3. 실제 회로에서 '조립 상쇄로 진짜 A = 0인 포트'가 생기는지(5절 (b)의 위험이 운영에서 발동하는지).
4. oracle 계획 N0 29행과 `oracle_simulate.py:402` 기본값 대체의 정합.
