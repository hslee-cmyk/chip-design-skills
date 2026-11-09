# design 40·41 v1.13.0 독립 검증 (2026-10-22)

- 대상: worktree `wt/design-v634` 커밋 `a27210d0`(부모 master `821c9bf2` = 계획 v6.34). 줄 수 유지 확인: 40 = 2125, 41 = 1992(부모와 같음).
- 정본: 계획 v6.34(같은 worktree), `_drafts/user_decisions.md` O-106~O-110·DEC-103.
- 엔진 실측: `wt/integ-it12` `6afe4758`(IT-2b 병합본). 읽기 전용, git은 `git -C`만 썼다.
- 작성자 대응표(계획 문장 ↔ design 줄): **미확인**. 커밋 메시지와 `_drafts`(이 검증 직전 이후 파일)에서 찾지 못했고 전달받지 못했다. 그래서 검증자가 직접 대응표를 만들어 줄 단위로 대조했다(아래 1절).

## 점수: 79 / 100

계획 v6.34 범위·완료 조건 (0)~(12)는 design에 빠짐없이 들어갔다. graph 단일 정본(E 생산 자리 하나·`__canonical__`·cfg 한 칸·front 블록 없음)도 지켰다. 감점은 다음 때문이다. (a) design이 새로 정한 규칙 (2)가 L12 (a)와 계획 (12)(a)에 충돌한다(G-1). (b) test 판정 꼴 세 곳(L8 (a), L10 (j), L12 (a))이 그대로는 판정할 수 없다. (c) design 42 D-IT2·D-ICM 행이 지운 규칙을 살아 있는 설계로 적고 있다.

---

## 1. 계획 반영 대조 (검증자가 만든 대응표)

| 계획 v6.34 | design 자리 | 판정 |
|---|---|---|
| 완료 조건 (0) 끝 풀이 정의 0·호출 0 | 41:802 K3, 41:764 | 일치 |
| (1) 선언 회로 cfg 있음, 커널 `node.dc_window` 항목은 W4 뿌리만, 커널·front 같은 cfg 값, 다듬은 창·front 블록 정의 0 | 41:800 K1, 802 K3, 805 M1, 680 | 일치 |
| (2) `saturation_window` 하나, 부르는 자리 둘 | 41:807 M2, 695, 734 (4) | 일치 |
| (3) 변화표 (i)(i′)(ii) | 41:817 (4)(5)(10)·(2) | 일치 |
| (4) 포트 창 자리 하나 | 41:808 M3 | 일치 |
| (5) 소비자, E의 소비자, 삭제 확인 | 41:788, 803 K4, 812 L10 (c) | 일치 |
| (6) 동작 변경: 지문 D1·D4, O-108, O-107, card 0 발동률 | 41:817 (5)(6)(10)(11) | 일치 |
| (7) O-49 (a)(b)만 | 41:809 P | 일치 |
| (8)(a) KCL 손 조립 oracle, 비교 허용은 design이 정함 | 41:811 L8 (a) | 들어감. 판정 꼴은 S-2 참조 |
| (8)(e) δV_out 판정 불능·정확 산술 | 41:811 L8 (e) | 일치 |
| (9) O-54, 불일치 대상 없음 | 41:810 D, 713 | 일치 |
| (10)(c) E 생산 자리 하나, (10)(d) KCL 감도 자리 하나 | 41:812 L10 (c)(d) | 일치 |
| (11)(a) 예시 교체 | 41:813 | 일치 |
| (12)(a)~(d) | 41:814 L12 | 들어감. (a)는 G-1 참조 |
| N3.8 E 식·자리·`__canonical__`·c_s는 스탬프 옆 한 자리와 test | 41:739·740, 812 (j)(k) | 일치 |
| N6.6 범위 1 F 성분 판정·기록 = 측정 구성 블록이 `node.dc_writer`로 | 41:697, 737 (나), READS 731 | 일치 |
| D2 이어받기 없음, READS에 `node.dc_window` 없음 | 41:694, 737, 814 (d) | 일치 |
| `saturation_window` 쌍 roots·묶음 갈래 삭제 | 41:695, 40:1882 | 일치 |
| U-101 (가′): 행 부분만 옮김, solve 이동 없음 | 41:760·761 | 일치(구조 근거는 N-3 참조) |
| IT-2d 범위 축소 | 41:794, 834 | 일치 |
| DE-1 인계 C2·C3 | 41:831 (1)(1′) | 일치 |
| 차동 처리 정합 확인(병합 전) | 41:726 | 유지됨 |

빠진 계획 항목이나 계획과 다른 항목은 없다. 단, 계획 쪽 문언에 낡은 곳이 하나 있다(N-7).

---

## 2. design이 새로 정한 다섯 가지 판정

| # | 결정 | 계획이 맡긴 범위인가 | 원칙 | 판정 |
|---|---|---|---|---|
| (1) | cfg `tol_v` = 봉인점 `device.dc_tol_v`(MOS, None 아닌 값)의 최솟값 | 맡긴 범위다. D2 뒤 metric 분해능 출처가 비었고, 계획은 cfg 상태를 블록이 정한다고만 적었다 | 정의가 같다: 커널 `_tolerance`와 같은 `tol_v_cell`을 같은 해(봉인점 VDS)에서 쓴다. 엔진 `seal_tolerances.py:28-30`, `block_columns.py:559-571·695-701`. graph 필드를 READS로 읽고 재계산은 0이다 | **수용** |
| (2) | 봉인점 tol이 모두 None이면 cfg 항목을 모두 `"unmeasured"`로 | 맡기지 않은 새 fail-closed 규칙이다 | 기존 경로가 같은 일을 이미 한다. 분해능이 None이면 `ss_constraints.py:15-16·79`가 제약을 `resolution_undefined`로 unmeasured 처리하고, 4.7-5는 `tol_v` None이면 분해능 None이다. 이 규칙은 보고 값까지 숨기는 더 강한 사상이라 D2 취지(봉인점 KCL 창은 정의된다)와 어긋난다. 도달도 사실상 없다: 모든 MOS tol이 None이면 봉인 1·2·3·6·8 행 tol이 None이라 봉인이 `undefined`(`_helpers_seal.judge`)가 되고 측정 구성 블록이 돌지 않는다. 그리고 L12 (a)와 충돌한다(G-1) | **기각 권고** → `tol_v=None`으로 `"measured"`를 쓰는 기존 경로 |
| (3) | L8 (a) 비교 허용 = cfg `tol_v` | 맡긴 범위다(계획 (8)(a) '근거와 함께 정한다, 새 상수 금지') | 새 상수는 없다. 그러나 허용치를 **피검 블록의 출력**에서 읽는다. 엔진이 `tol_v`를 틀리게 크게 쓰면 test가 스스로 느슨해진다(작성자≠검증자, oracle 독립성 위반). 검출력도 tol_v(예 6.3e-3 V, 41:817 (8)) 이상인 오차로 한정된다 | **수정 수용**(S-2) |
| (4) | `kvl_sensitivity`는 닫음 분모가 정확히 0일 때만 None | 문턱이 계획에 없다는 사실 표시는 맞다 | 정확 0 비교는 부동소수점에서 사실상 검사가 아니다. 분모가 수치 분해능 아래면 slope 부호·크기가 의미 없는데도 `"measured"` 창이 된다(fail-open). 발명하지 않은 문턱이 이미 있다: e_outᵀv_u = A_u는 같은 인수분해 위의 전달이라 계획 N3.8 '판정 분해능의 정의 자리'(δA_num)를 그대로 쓸 수 있다. 다만 정의 자리를 새로 넓히는 일이라 계획 몫이다. 도달은 낮다(정상 follower는 \|1 − A_u\| ≫ 1) | **조건부 수용** + 계획 백로그(N-1) |
| (5) | `StampSet.g_ops` 칸 추가 | 맡긴 범위다(계획 'c_s는 스탬프 함수 옆 한 자리') | 값 사본이나 cache가 아니다. 스탬프 식이 정하는 정적 개수이고, 0 거르기와 순서를 맞추려면 나란한 tuple이 가장 단순하다. 기본값이 `()`라 기존 생성자는 호환된다. 다른 소비자(`mna_build`·`lut_parameters`·`offset_analysis`)는 `.g`·`.c`만 읽는다. 기존 test는 `isinstance`만 단언한다(`test_stamp_mos.py:39`) | **수용**. metrics CONTRACT의 StampSet 행 갱신을 4.7-6에 명시할 것 |

---

## 3. G (반드시 고칠 것)

### G-1. 규칙 (2)와 L12 (a)·계획 (12)(a)의 충돌
- 위치: 41:688(값 형식 (2)), 41:737 (라), 41:814 L12 (a), 계획 N6.6 완료 조건 (12)(a).
- 근거: L12 (a)는 'k_max 소진 toy·**tol 미정 toy**'에서 cfg `measured`이고 세 metric 값이 있다고 단언한다. 그런데 tol 미정 toy(A6 b)는 모든 MOS의 `tol_v_cell`이 미정인 해다(`block_columns.py:695-701`). 봉인점에서 `dc_tol_v`도 같은 셀이라 모두 None이다(`seal_tolerances.py:28-30`). 그러면 규칙 (2)로 cfg는 `"unmeasured"`가 되고 세 metric은 정의 불능이다. design 안에서 서로 모순이고, 계획 (12)(a)와도 어긋난다. 게다가 그 점은 봉인 `undefined`라서 L12 (a)의 '봉인 통과' 전제가 늘 깨진다. 그러면 tol 미정 사례는 구조적으로 늘 무효인 공허 사례가 된다.
- 수정 제안: (가) 규칙 (2)를 철회하고 `tol_v=None`, `"measured"`로 쓴다. 분해능 None → 제약 `resolution_undefined`는 기존 경로다. (나) L12 (a)의 tol 미정 사례는 봉인 통과가 불가능하다는 사실을 test interface에 적는다. 그 사례는 커널 상태(`unsettled`)만 단언하고 cfg 단언 대상에서 뺀다. 계획 (12)(a) 문언 정오는 계획 몫으로 올린다.
- 원칙: (가)는 '기존 경로 재사용·새 규칙 금지'와 D2 취지에 맞는다. 공허한 사례를 남기면 fail-closed 검증 원칙('실제로 거부함을 먼저 확인')에 어긋난다.

---

## 4. S (고쳐야 할 것)

### S-1. design 42가 지운 규칙을 살아 있는 설계로 적음
- 위치: `42-gap-checklist.design.md:229` D-IT2, `:218` D-ICM. 41:837은 D-J5·D-ICM만 '후속 정정' 목록에 둔다.
- 근거: D-IT2 행에 다음 내용이 그대로 남아 있다.
  - `node.dc_window_def_refined`(`dc_window_refine`)
  - '부르는 블록 셋'
  - 'O-61 P5 커널 미수렴 → cfg 상태 → metric 정의 불능'
  - 'P6 다듬은 창 출발'
  - `node.dc_output_structure` 필드
  - 'S-OS1'

  D-ICM에는 'front·보고 = `node.dc_window_def_refined`'가 남아 있다. 이 행들은 IT-2 gap 분석과 판정이 대조하는 체크리스트다. 이대로 두면 gap-detector나 감사가 지운 설계를 기준으로 MISS나 불일치를 낸다. D-J5는 `icm_window_metrics`만 가리켜서 충돌이 없다.
- 수정 제안: 이번 design 판에서 42의 D-IT2·D-ICM 두 행을 v6.34 문언으로 바꾸거나, '대체됨 → 41 v1.13.0 §4.7' 표지를 붙인다. 계획 IT-2c 착수 조건 (v)는 41만 명시하지만, 계획 S-7(구현이 design과 다르면 design부터)에 따라 IT-2c card 재동결 전에 고친다.
- 원칙: graph 정본 원칙 7(검증 단계 점검), '계획과 다르면 계획부터, design 일치'.

### S-2. L8 (a) oracle 입력 목록 오류와 허용치 출처
- 위치: 41:811 L8 (a). 같은 문언이 계획 (8)(a)에도 있다.
- 근거:
  - (i) '`device.dc_op` VDsat'라는 칸은 없다. `DeviceOp`의 칸은 kind, current, ln_idu, gm_id, L, W, vgs, vds, vsb, w_key, idu_forward이다(`s2_values.py:389-404`). VDsat는 graph 필드가 아니라 봉인 7과 `region_rows`가 블록 안에서 LUT로 잰다.
  - (ii) 행 여유의 tol_VDsat 출처가 목록에 없다. `device.dc_tol_v`는 tol_V(id_equivalent)이지 tol_VDsat가 아니다.
  - (iii) 허용치를 피검 출력 cfg `tol_v`에서 읽는다(2절 (3)).
- 수정 제안: oracle은 VDsat와 tol_VDsat를 공개 LUT 원시 함수 `gmid_engine.lut.vdsat(memo, kind, w_key, L, vgs, vds, vsb)`와 `tol_vdsat_table(memo, kind, w_key).at(L, vds)`로 `device.dc_op` 점에서 직접 구한다. 둘은 피검 함수가 아니라 LUT 원시 함수다. 허용치는 test가 `device.dc_tol_v`에서 손으로 낸 최솟값으로 둔다. 그 값과 cfg `tol_v`가 같은지는 따로 단언한다. 계획 문언 정오 '(dc_op 점의 LUT VDsat)'는 계획 몫으로 알린다.
- 원칙: 작성자≠검증자(oracle 독립성), 정본 필드 실측 확인.

### S-3. L10 (j) 판정 꼴이 그대로는 판정 불가
- 위치: 41:812 L10 (j).
- 근거:
  - (i) 'AST `BinOp` 수 = MOS 2·저항 1'은 실제 소스와 다르다. `mos_stamps`에는 `gm + gmb + gds`의 두 개 외에 오류 문장 `"..." % (device,)`(`BinOp(Mod)`)가 있어 3개다. `two_terminal_stamps`에는 `1.0 / element.ohm` 외에 `"..." % (element,)`가 있어 2개다(`stamp_mos.py:16`, `stamp_two_terminal.py:17`). 손 계수가 처음부터 틀린다.
  - (ii) '`bound=True`에 `g_ops` 길이가 틀린 `StampSet`을 주면 `ValueError`'를 재려면 `conductance_matrix` 안의 `mos_stamps`·`two_terminal_stamps`를 바꿔 끼워야 한다. 41:804 R2는 내부 이름 monkeypatch를 `block_columns.k_max`와 L11 (e)로만 한정한다. 그래서 이 단언은 R2와 충돌한다.
- 수정 제안: (i) 세는 대상을 '스탬프 값 식의 수치 이항 연산(문자열 피연산자 `%` 제외)'으로 정하거나 기대 수를 실측 값으로 고친다. (ii) R2에 주입 지점 하나(`gmid_engine.metrics._helpers_nodal.mos_stamps`)를 더하거나, 길이 검사를 순수 함수로 떼어 직접 단언한다.
- 원칙: 게이트는 '실제로 거부함'을 먼저 보인다. 측정 정의와 실측이 맞아야 한다.

### S-4. `sizing.__all__` 공개 목록 누락 (규칙 C 착수 장애)
- 위치: 41:760, 41:797(4.7-6 IT-2c 고치는 자리).
- 근거: `icm_config`(metrics)는 cfg `Window`에 `INPUT_STATUS_MEASURED`·`INPUT_STATUS_UNMEASURED`·`INPUT_STATUS_F_COMPONENT_UNDECLARED`를 써야 한다. IT-2d `metrics_aux`도 상태를 code로 옮길 때 이 상수가 필요하다. 그런데 지금 `sizing/__init__.py`의 `__all__`에는 `Window`만 있고 `INPUT_STATUS_*`는 없다(grep 확인). design은 `Circuit`·`saturation_window`만 더한다. 규칙 C (3)으로는 `__all__` 밖 이름을 import할 수 없다. 구현자는 '`as-built` 결정 금지, 멈추고 보고' 규칙 때문에 멈추게 되고, 그렇지 않으면 문자열 리터럴 사본을 쓰게 된다.
- 수정 제안: 4.7-4·4.7-6의 `__all__` 목록에 쓰는 상태 상수 셋을 더한다(IT-2c).
- 원칙: 정본 상수 하나, 규칙 C.

### S-5. 규칙 (2) 철회 (G-1과 같은 변경)
- 위치: 41:688, 737 (라).
- 근거와 제안: 2절 (2)와 같다. 철회하지 않으려면 계획 개정을 먼저 거쳐야 한다(새 fail-closed 규칙, D2 취지 경계).

---

## 5. N (권고)

- **N-1** 2절 (4): 닫음 분모 문턱. 계획 N3.8 판정 분해능을 A_u에 넓혀 쓰는 안을 계획 백로그로 올린다. design의 '문턱 없음' 표시는 그대로 두되 fail-open 가능성을 41:734 (3)에 한 구절 적는다.
- **N-2** `region_rows`가 봉인점에서 LUT로 VDsat를 다시 재는 것(검사 3)은 **둘째 생산자가 아니다**. 근거는 다음과 같다.
  - VDsat는 graph 필드가 아니다. 봉인 7은 `dc_seal_7` 판정만 쓴다(`seal_saturation.py:46-71`).
  - `vdsat`·`tol_vdsat_table`은 LUT memo point·derived 조회다(`vdsat_query.py:51`, 승인 예외 (a) LUT memo).
  - 인자가 같으므로 봉인점에서는 memo가 적중한다. `mos_point`와 `dc_widths`는 같은 `terminal_voltages`를 같은 `node.dc_v ∪ dc_rail_v`로 부른다.

  남는 것은 여유 식 VDS − VDsat − tol_VDsat가 봉인 7과 `region_rows` 두 자리에 있다는 점이다. 이 중복은 v1.13.0 이전부터 있었고, HC-S `sat_threshold` 통일 대상이다. 원하면 '봉인점 `region_rows` sat 행 여유 = 봉인 7 행 여유(비트 동일)'를 L10 단언으로 더할 수 있다.
- **N-3** U-101 (가′) 구조 규칙 판정:
  - 규칙 A 보충 (3): 검사기는 `_` 모듈의 공개 **함수**만 센다(`structure_checks.py:300-315·353-360`). 클래스뿐인 `_helpers_dc_solve.py`는 형식상 통과한다. 취지('실사용자 둘 이상')는 `block_columns` 상속과 `icm_config`(패키지 밖, `__all__` 경유)로 충족하지만, 규칙 문언('같은 하위 패키지 2파일')과 다르다. design 문장을 '검사기 공백에 기댄 통과'로 명시하고 오케스트레이터 확인을 받든지, 계획 U-101 이름을 공개 모듈(진입점 클래스 하나)로 바꾸는 계획 정오를 검토한다.
  - 규칙 B: `from ._helpers_dc_solve import Circuit` 형식은 허용되고 `_kind_sign` → 공개 정적 메서드도 맞다. 판정은 통과다.
  - 규칙 C: metrics(5) → sizing(4) 아래층 방향이다. S-4만 고치면 통과한다.
  - 모듈 지도 층: `_helpers_dc_solve`는 `_helpers_lut`·`scc_order`(층 1)를 import하므로 층 2다. 그러면 `block_columns`(지금 층 2)는 층 3으로 올라가야 '같은 층 import 금지'(`_module_map.py` 머리)에 맞는다. design에 층 배치를 적는다. 지금 이 지도 층 규칙은 구조 test가 강제하지 않는다(미강제, 확인함).
- **N-4** extras 키워드 계약과 지문: 입력 버전 = `fp_of((name, code_hash(블록 fn), projection.fp))`(`compute_block.py:127-129`), `projection.fp`는 extras 값을 포함한다(`projection.py:41-45`).
  - `dc_columns` extras tuple은 그대로라 projection 지문은 불변이다. 블록 함수 본문이 바뀌어 code_hash가 한 번 바뀌지만, D1으로 어차피 바뀐다.
  - S3 색인은 실행 수명뿐이라 실행 사이 영향은 없다.
  - `icm_config`는 새 블록이라 비교할 옛 버전이 없다.
  - 참고(전부터 있던 일): code_hash는 블록 함수만 보고 `Circuit` 메서드 코드는 보지 않는다. 실행 수명 색인이라 해는 없다.
- **N-5** 4.7-1a 기록 bullet(41:719~727)은 명령형 문장('WRITES에 더한다' 등)이라 agent가 지시로 읽을 위험이 있다. bullet마다 '(기록)' 머리를 붙이거나 history로 옮기는 편이 낫다. 또 41:719 안의 아직 유효한 지시가 '기록' 구역에만 있다. `SS_WRITES`에 `ss_nodal`·`icm_config` 행이 생겨 `test_s2_values.py`의 `SS_TABLE`·등식 기대가 깨진다는 test 작성 주체 몫 안내다. 이 문장을 4.7-6으로 옮긴다. 삭제 표지 줄 방식(41:683·689·763~776)은 앵커와 줄 번호를 지키고 읽기에도 무리가 없다. 41:17 Status 줄(한 줄 수만 자)과 41:734(15.5 KB)·753(12 KB)의 가독성 부채는 그대로다.
- **N-6** L8 (a) 검출력: 허용치가 tol_v 급이라 틀(θ 대 KCL) 판별에는 충분하다(전제 (ii)). 그러나 gmb 누락 같은 mV 이하 결함은 못 잡을 수 있다. `kvl_sensitivity` 공개 함수의 노드 감도를 손 조립 감도와 따로 대조하는 보조 단언을 test 작성 주체 몫으로 권고한다(허용치 근거는 같은 규칙).
- **N-7** 계획 쪽 낡은 문언: 계획 N7.2 U-101 행이 아직 '사용자 결정 대기 -- 오케스트레이터 권고 (가′)'로 남아 있다(O-110으로 결정됨). Status 줄에는 반영됐다. 계획 정오는 계획 몫이다.
- **N-8** 40:556 `ss_nodal` 행 '읽는 쪽: `icm_config`(`kvl_sensitivity`·`_transfer_resolution` -- E는 이것이 소비자)'는 E 소비자가 `_transfer_resolution`뿐이라는 뜻이 흐리다. 문구를 정리할 것을 권고한다.

---

## 6. 검사 항목별 요약

1. 계획 반영: 범위와 완료 조건은 빠짐없이 들어갔다(1절). 작성자 대응표는 미확인이다.
2. 다섯 결정: (1)·(5) 수용, (3) 수정 수용, (4) 조건부 수용, (2) 기각 권고.
3. graph 단일 정본:
   - E = `NodalSystem.g_bound`: 생산 자리는 `conductance_matrix(bound=True)` 호출 `ss_nodal` 하나이고 `__canonical__`에 든다(41:739·740, L10 (c)(f)). 통과.
   - `region_rows` VDsat 재측정: 둘째 생산자가 아니다(N-2). 통과.
   - cfg는 정본 칸 하나이고 front 전용 블록은 없다(41:736, 794). 통과.
4. U-101 (가′): 실현 가능하다. 규칙 B·C는 통과하고(C는 S-4를 고친 뒤), 규칙 A는 검사기 공백에 기대 통과한다(N-3). 키워드 계약의 지문 영향은 code_hash 한 번뿐이고 실행 사이 영향은 없다(N-4).
5. 삭제 정리: 41에서 살아 있는 규칙으로 남은 자리는 없다(grep: 남은 출현은 삭제 표지, 부재 단언, 기록 구역, 이력뿐). design 42에는 남아 있다(S-1). 4.7-1a 기록 구역의 가독성은 N-5.
6. 판정 가능성: L8 (a)는 S-2, L10 (j)는 S-3, L12 (a)는 G-1. L8 (e)(정확 산술)와 L10 (k)(E 손계산)의 oracle은 독립이다.
7. design 42: D-J5에는 충돌이 없다. D-ICM과 D-IT2가 계획 v6.34와 충돌한다(S-1).

## 7. 미확인
- 작성자 대응표 원본(전달받지 못함).
- 커널 컨텍스트에서 `icm_config` extras(선형 선언·되먹임 선언)를 `ss_evaluate`까지 넘기는 경로. design이 '착수 때 확인, 없으면 멈춤'으로 둔 항목이라 이번에는 재지 않았다.
- Higham 절·쪽(계획과 같이 미확인).
- 모듈 지도 층 규칙을 다른 곳(구조 test 밖)에서 강제하는지: `tests/structure`에서는 강제하지 않음을 확인했고, 그 밖은 미확인이다.
