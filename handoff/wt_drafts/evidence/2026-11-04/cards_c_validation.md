# card 묶음 c 독립 판정 (2026-11-04)

대상: 브랜치 `docs/cards1104c` head `9a70020e`(master `4467f389` 대비). headroom-chain 0.7.9.10, graph-consumption 0.14.9, design v1.16.8, HC-D v0.1.4, GD v0.1.1, card `20261104-hc1-gc8`. 위임 A-50~A-52.

방법: 문서 읽기와 `git grep`·`git show`만 썼고 실행은 없다(pytest·LUT 읽기·엔진 0). 엔진 인용은 재작성 범위·호출 자리·구조 규칙 판정식 대입과 엔진 밖 사실(LUT 격자 선언)에만 쓴다(원칙 8). 작성자 설명은 원문과 대조했다. 줄 번호는 `docs/cards1104c` 기준이다.

## 판정 요약

| 대상 | 판정 | Major |
|---|---|---|
| E-4 단좌표 자르기 | 자리(L 칸)와 HC:258 읽기, bin 경계, tol은 맞음. 칸 표본·좌표 수·대상 변·배선 toy가 틀림 | V1, V2, V3, V4 |
| E-1 구조 규칙 | 규칙 A 맞음, `upward_pair` 사용 파일 둘 맞음. 규칙 H·층 규칙(C) 틀림 | V5, V6 |
| E-3 빈 서명 | `f_exist`·`j_point`·`stack_unsat` 손 값은 맞음. `judge_rungs`의 입력 조립과 F-9가 빠졌거나 어긋남 | V7, V12 |
| E-6 구간 칸 | **기준 약화 아님**. 멈춤 아님. reader 빈칸은 고친다 | V8 |
| E-9 값 칸 | `TriodeRegion` 값 칸 삭제는 맞음. `vgs_y`·`rhs`는 L-5에 걸린다 | V9 |
| 구조적 0 | 정의가 계획보다 좁고 H20 toy가 성립하지 않음 | V10 |
| 선언 triode | `judge_region` 둘째 호출이 graph 규칙 1과 EO-1 test를 어김 | V11 |
| test 작성 가능성 | monkeypatch 관찰 지점 없음 | V13 |
| E-5, E-7, E-8, N6.1 순서, A-34, GL-1 | 맞음(minor만) | 없음 |

**멈춤(위임 밖) 0.** 근본원칙 변경, connectivity 수정, 기준 약화로 시험을 통과시키는 일 어느 것도 아니다. V9의 HC:299 문언 변경은 계획 개정이고 O-226 위임 안이다.

## E-6 판정: 기준 약화 아님

**판정식 대입.** L-4(GC:256~259, GC-1 spec 계약 6)는 칸마다 '클래스 본문 밖 속성 읽기가 있거나, 없으면 목록'이다. `_chain_start_note`가 `node_lo`·`node_hi`·`vr_lo`·`vr_hi`를 실제로 읽으면 L-4는 **목록 없이 통과**한다. 면제로 통과하는 것이 아니므로 판정 기준이 느슨해지지 않는다. GC:663 '새 필드도 규칙 L 통과'를 부채 없이 지킨다.

**출력 함수 자격(N3.1-2 (i)(ii)).** `notes`의 엔진 reader를 grep한 결과 0이다(`.notes` 자리는 `search_context.py:115`의 `constraint_classes.notes`뿐, 다른 객체). 경로는 `find_front`의 notes → 결과 JSON뿐이다. 자격이 맞다. 검증자 독립 재측정은 병합 때 한다(미측정).

**실질 정보 여부.** 위반 칸의 구간은 'W4·V_R을 어디로 옮기면 사슬이 풀리는가'이고 R6가 쓸 값과 같은 정의다. 이름만 읽는 꾸밈이 아니다. 다만 절대원칙 기간 예외(A-18)는 그대로 남고 사용자 보고 항목이다.

**`LoopConflict.cycle` → `exist`.** spec E-6 행에는 있으나 **A-52 결정 문언에는 없다**(m12). 내용은 문제없다. 값이 그 칸 판정 묶음 한 자리에만 있고 `f_exist` 재호출이 0이며, D40:496·D41:2095·2121·2225는 칸 이름을 인용하지 않아 낡은 문언이 0이다(`.cycle` grep 0). 기준 변경도 아니다.

**남은 지적(약화 아님).**
- `output_only_slots` 등록은 reader가 있으면 **불필요**하다. 등록의 유일한 효과는 reader를 지워도 L-4가 통과하게 하는 것이다(N3.1-6 (d) '허용 확대'). H23b가 그 구멍을 막지만, 안 넣으면 H23b의 목록 단언도 지문 변경도 필요 없고 reader 삭제 때 L-4가 직접 잡는다. 더 엄격하고 단순하므로 권고한다(m12). 넣어도 소유표 근거가 있어 GD §3 J1상 기록된 기준 변경이다.
- `feasible`과 `ChainCycle` 칸은 reader가 없다. 이것은 V8이다.

## Major

### V1. L 칸 안 g는 선형이 아니다 -- 칸 끝 표본이면 해를 잃는다 (E-4)

**사실.** LUT L 격자 선언 = 0.15, 0.18, 0.185, 0.2, 0.25, 0.255, 0.3, 0.35, 0.425, 0.5, 0.7, 1, 1.5, 2, 2.5, 4, 8, 20 µm(`skills/analog-gmid-design/assets/sky130_lut_L_grid.json`). bin (0.25, 0.5]에 앵커 다섯, (0.18, 0.25]에 앵커 셋이 든다(bin = `lut/CONTRACT.md:190`). `l_cells.py:6-7`은 칸을 [bin 최소 앵커, 최대 앵커]로 만들고, 보간은 **양옆 앵커 사이**다(`_helpers_anchor.py:32-37`, `lut/CONTRACT.md:414`). 그래서 칸 안 g는 구간 선형이지 선형이 아니다. VDSAT(L)이 칸 안에서 단조라는 근거도 없다.

**결과.** 칸 끝이 (−, −)이고 안쪽 앵커가 +이면 행 5가 칸을 통째로 지워 유효 L을 잃는다. HC:258 근거 '상자를 잘라도 해를 잃지 않는다'가 깨진다. 표 행 2·3·4도 같은 이유로 틀릴 수 있다. HC-D §6.5와 spec E-4의 '칸 끝 부호로 구간이 정해진다'는 틀린 문장이다.

**고칠 문언.** interface §4.1:
> `chain_cut(edge, component, cells, anchors, margin_of, tol) -> (cells′, records)`. `anchors` = 그 좌표의 꺾임점(L이면 LUT L 앵커, 그 밖 `()`). **표본 = 칸마다 칸 끝 ∪ 칸 안 앵커**, 오름차순. 칸 안 g는 앵커 사이에서 L 선형이므로 표본 부호로 만족 집합이 정해진다. 표의 '끝 g' → '표본 g'. 행 5: 전부 위반인 칸 삭제, 부호가 바뀌는 앵커 구간마다 근을 내어 그 칸 끝으로 한다(한 칸 안에서 만족 구간이 양쪽 다 좁아질 수 있다). `bracket_root`에 `None`을 넘기지 않는다: 근 찾기 중 `margin_of`가 `None`이면 행 1과 같이 칸 불변 + `cut_undefined`.

`bracket_root`는 f의 `None`을 걸러 주지 않아 `(fa > 0)`에서 사유 없이 `TypeError`가 난다(`bracket_root.py:43-47`). 그래서 마지막 문장이 필요하다.

H19에 더한다: `cells` ((1,4),), `anchors` (1,2,3,4), 구간 선형 g 표본 (−1,+1,+1,−1) → ((1.5,3.5),), 기록 `"lo"` 1.5·`"hi"` 3.5(옛 끝 표본이면 `cut_empty`라 red). 표본 (−1,+1,−1,+1) → `cut_not_interval`.

HC-D §6.5 풀이 줄: '칸 안 VDSAT는 같은 bin의 양옆 앵커 사이 L 선형이다. 앵커가 셋 이상이면 구간 선형이라 앵커 표본으로 구간을 정한다'. spec E-4 행도 같게 고치고 서명을 바꾼다.

### V2. `coords`에 gate 넷 경로가 없어 다변수 부등식이 `cut`이 된다 (E-4, C-10)

**사실.** VDSAT는 `sat_threshold(memo, kind, w_key, L, vgs, vds, vsb)`로 VGS에 의존한다. 비 writer MOS의 VGS는 gate 넷 전압으로 정해진다. interface §2.3 `coords`는 양 끝 넷, source 넷, 소자 자신만 세고 gate 넷 `steps`를 세지 않는다. HC-D §5.1도 같다. 그런데 HC-D §6.5는 'VGS와 양 끝 전압이 θ에 안 걸리는 변'이라 적어 **문서가 서로 어긋난다**.

**반례(손).** M1 nmos (nb, nb, gnd), M3 nmos (vdd, nb, gnd). M3는 비 writer이고 양 끝·source가 레일이다. 규칙대로면 `coords` = (`("L","M3")`,), `route = "cut"`. 실제 g는 VGS(M3) = V(nb)를 통해 ln IDu(M1)·L(M1)에 걸린다. `margin_of`는 가정 동작점 없이 정의되지 않거나, 가정을 넣으면 C-10이 금지한 판정으로 칸을 지운다.

**고칠 문언.** interface §2.3 `coords` 끝: '…, 소자 source 넷 경로**와 gate 넷 경로**의 같은 좌표(gate 넷 뿌리 W4 y 포함)'. HC-D §5.1 `coords` 줄에 'VSB를 정하는 source 넷'에 이어 '**VGS를 정하는 gate 넷**의 좌표'. H-P에 손 값 한 행: 위 두 소자에서 M3 `coords` = (`("L","M1")`,`("L","M3")`,`("ln_idu","M1")`), `route = "filter"`. 기존 §2.3 손 값 둘은 M1·M2가 writer라 변하지 않는다(재확인함).

### V3. `off`·구조적 0 변도 자른다 (E-4, 계약 10)

**사실.** §4.1 'route == cut인 변마다 부른다', HC-D §6.5 같음. `on_structural` False 변은 지우지 않고 표지한다(§2.3). `route`는 좌표 수만 본다. `off` 선언 소자가 레일에 걸리면 `cut`이다.

**결과.** (1) 계약 10 '`off`: 출발 `sat_threshold` 호출 0' 위반. (2) `term`이 없어 `margin_of` 정의가 안 된다. (3) 구조적 0 소자에 포화 부등식을 걸어 유효 L을 잘라낸다(HC:348 '비전도 소자의 VDS 부호는 물리가 정하지 않아 그 변을 넣으면 유효점을 자를 수 있다'). H18은 `test_chain_graph`·`test_iv_kvl_choice`만 보므로 못 잡는다.

**고칠 문언.** interface §4.1 `search_domain` 줄:
> `route == "cut"`이고 **`on_structural`인 변**마다 부른다. `margin_of(c)` = V(hi) − V(lo) − term. V = 그 넷의 F 값(`steps` 없는 뿌리 값, θ 무관). term = `sat`이면 `sat_threshold(memo, kind, w_key, c, vgs, vds, vsb).vdsat_v`(`None`이면 g = `None`), `lut_floor`이면 `vds_floor`. `m`이 `l_cells`에 없으면(묶음 구성원) `chain_cuts`에 `coordinate_not_in_box`.

H18에 `tests/search/test_search_domain.py` 추가: 레일에 걸린 `off` 소자에서 그 소자 L 칸 불변, `sat_threshold` 호출 0.

### V4. H19 배선 toy의 기대값이 나올 수 없다 (E-4, test 작성)

**사실.** R4 LUT는 bin 지도가 없다(`tests/sizing/conftest.py:116` 주석, `tests/search/test_l_cells.py:24-25`가 `l_cells == ((a,a) for a in R4_L)`을 단언한다). 칸은 (1e-6,1e-6), (2e-6,2e-6)이고 앵커 밖 L은 `lut_l_not_anchor`다(`_helpers_anchor.py:33`). '근 1.4375e-6 → 그 칸 hi'가 될 칸이 없고 표본도 못 잰다.

g 값 자체는 맞다(g(1e-6) = 0.125 − 0.09765625 = 0.02734375, g(2e-6) < 0, 손으로 재확인).

**고칠 문언.** H19 배선 문장 교체:
> 배선: M1 `mos("M1","nmos","vdd","vdd","gnd")`, 레일 vdd 0.125·gnd 0, R4 LUT(bin 지도 없음, 칸 = 앵커 점). g(1e-6) = +0.02734375, g(2e-6) = −0.03515625 → M1 칸 = ((1e-6,1e-6),), `chain_cuts` 한 행 `"hi"`, 값 = 남은 끝 1e-6. 근은 나오지 않는다. 칸 안 근은 `chain_cut` 순수 toy(위 행들)가 잠근다.

§4.1 행 5에 '칸을 통째로 지우면 기록 값 = 남은 끝'을 더한다.

### V5. 구조 규칙 H: 새 파일 넷의 test 자리가 없고 옮긴 test가 고아가 된다 (E-1)

**판정식 대입**(`structure_checks.py:966-985` `check_h`). 원본마다 `tests/<패키지>/test_<파일>`이 있어야 하고(`h_exempt`는 함수 없는 `_` 모듈과 데이터 모듈뿐, `:955-963`), `tests/<패키지>/test_X.py`는 `<패키지>/X.py`가 있어야 한다.

| 원본 | 필요한 test | interface §7 |
|---|---|---|
| `sizing/chain_exist.py` | `tests/sizing/test_chain_exist.py` | **없음**(F 표를 `test_chain_judge.py`에 둠) |
| `sizing/chain_cut.py` | `tests/sizing/test_chain_cut.py` | **없음**(H19를 `test_chain_judge.py`에 둠) |
| `sizing/_helpers_polarity.py` | `tests/sizing/test__helpers_polarity.py` | **없음** |
| `sizing/current_symmetry.py` | `tests/sizing/test_current_symmetry.py` | **없음** |
| (옛) `search/current_symmetry.py` 삭제 | `tests/search/test_current_symmetry.py` = `orphan_test` | '(import 자리)'로 남긴다고 적음 |

spec E-1의 'test는 패키지 이름만 쓰므로 영향 없음'은 틀렸다. HC-D §10 '파일명은 구조 규칙 H로 card에서 확정'이 안 닫혔다. A-2가 `missing_test` 4 + `orphan_test` 1로 실패한다.

**고칠 문언.** §7: H1·H2·H4·H5와 H6의 F 부분 → `tests/sizing/test_chain_exist.py`. H6 행 표와 H8 `j_point` 부분은 `test_chain_judge.py`. H19 표 부분 → `tests/sizing/test_chain_cut.py`. H-P §2.1 표 → `tests/sizing/test__helpers_polarity.py`(공개 필드 경유, 기존 `test__helpers_bins.py` 꼴). 옛 test 정리: `tests/search/test_current_symmetry.py` → `tests/sizing/test_current_symmetry.py` 이동, `search_domain`이 읽는 단언만 `tests/search/test_search_domain.py`에. spec E-1 영향 칸: 'test 자리는 규칙 H로 §7에 확정'. HC-D §10 자리 줄 같음.

### V6. `chain_cut`(sizing)이 search 층 타입 `ChainCut`을 돌려준다 (층 규칙 C)

**사실.** interface §1 '`gmid_engine.search`: …`ChainCut`', §4.1 '`gmid_engine.sizing`, records = `ChainCut` tuple'. 층 순서는 sizing(4) < search(6)이고 '작은 번호 쪽으로만'이다(`structure_checks.py:24-31`). sizing 함수가 그 타입을 import할 수 없다.

**고칠 문언.** §1 `gmid_engine.search` 줄에서 `ChainCut`을 빼고 `gmid_engine.sizing` 값 목록에 `ChainCut(component, side, value, device, reason)`을 넣는다. `SearchDomain.chain_cuts`는 그 tuple을 담는다. spec 재작성 범위의 `sizing/s2_values.py` 값 형식 행이 받는다.

### V7. `judge_rungs`의 `weights`·`vr_bounds` 조립 규칙이 없다 -- `None`이 산술로 들어간다 (E-3)

**사실.** §3.1은 `f_exist` 인자의 뜻만 적고 §4는 '`f_exist`를 한 번 부르고'뿐이다. HC-D §6.1-2 '그 칸 동작점으로', §5.1 '저항 전류를 읽는 일은 호출자 몫'도 조립 규칙이 아니다. `j_point` 행 4(`reverse_vds`)·행 5(`vdsat_v` None)는 **`violated` 칸에 그대로 나타난다**. 다른 행으로 `violated`인 칸에 `vdsat_v` None 소자가 섞이면 `term + K_lo − K_hi`가 사유 없는 `TypeError`다. 사슬이 깨지는 칸에서 역방향 VDS는 흔한 경우이고 H3이 그 경로다. K의 출처와 `vr_bounds`의 값도 코드 작성자가 지어내야 한다.

**고칠 문언.** interface §4 `judge_rungs` 뒤에 추가:
> **`f_exist` 입력**(그 칸 스냅샷 읽기, 호출 안에서 만들고 버린다).
> - K(net) = `node.dc_v[net]` − (넷의 마디가 `F_STAR`면 0, 아니면 `node.dc_v[마디 넷]`).
> - MOS 변: `on_structural`이고 `op.current > 0`이면 `weights[소자]` = (term, K(lo_net), K(hi_net)). term = `sat`이면 `sat.vdsat_v`, `lut_floor`이면 `vds_floor`.
> - **`vdsat_v`가 None인 변은 `weights`에 넣지 않는다**(대체값 없음, 그 행은 `rows`에 이미 있다).
> - 저항: `weights[저항]` = (None, K(near_net), K(far_net)). `vr_bounds[저항]` = (min, max) of I·R, R ∈ θ 저항 상자, I = 그 칸 `far → near` 방향 전류(`device.dc_current`). 값이 θ로 고정된 칸이어도 구간은 상자로 준다(HC:220).

H3·H23에 `reverse_vds` 소자가 섞인 위반 칸을 추가: 예외 없이 `LoopConflict` 생성, 그 소자가 `exist` 입력에서 빠진다.

### V8. reader 없는 새 칸: `ChainExist.feasible`, `ChainCycle` 칸, `StackJudge` 두 칸 (E-6, 원칙 26 소비자)

**사실.** `.feasible`·`.violation`·`.path_kind`·`.theta_free`·`.l_at_max`·`.vgs_at_max` 엔진 읽기 0(이름이 겹치는 기존 칸 없음, grep). §4 JSON은 `"cycle"`을 'exist 칸 값 그대로(tuple은 목록)'라 하는데 `ChainCycle`은 dataclass라 형식이 없다. `feasible`은 JSON에 없고 `judge_rungs`도 읽지 않는다. §7 `output_only_slots`에도 없다.

**결과.** 값 선언 모듈(`s2_values`)이면 새 `L-4` 키 `slot_no_reader`이고 A-6에서 멈춘다(GD §1 '근거 없는 새 L-4 키는 부채로 넣지 않고 멈춘다'). `cycle` 비어 있지 않은 줄의 기대값은 test 작성자가 낼 수 없다. `StackJudge`는 `stack_unsat.py`(공개 def 있음)에 두면 L-4 대상 밖이지만 소비자 0은 같다.

**고칠 문언.** §4 JSON 항목: `{"rung", "state", "rows", "reason", "feasible", "cycle", "node_lo", "node_hi", "vr_lo", "vr_hi"}`, `cycle` = `{"edges": [...], "path_kind", "theta_free", "violation"}` 또는 null, `exist` None이면 뒤 여섯 null. `chain_cuts` 항목 = `{"component", "side", "value", "device", "reason"}`. H23: `ChainExist(False, ChainCycle(("M1","M2"),"via_f",True,0.2), (), (), (), ())` 주입 행 추가, `feasible`·`cycle` 네 칸 단언. §5 `detail`에 `l_at_max`, `vgs_at_max`를 더한다(최대가 나온 크기는 triode 선언 판단 근거). HC-D §6.3 같은 줄 맞춤.

### V9. `vgs_y`·`rhs`는 L-5 `op_copy`에 걸린다 -- 지금 정한다 (E-9)

**판정식 대입**(GC N3.1-5). 출처 = `column("device","dc_op")`의 칸, 사본 = 같은 값을 영속 자리에 담는 것, 영속 자리 (i) = graph 필드 쓰기, 전파 = 인자·반환·객체 칸.
- 봉인 `detail.vgs_y` = `op[Y].vgs` → `graph.dc_seal_7` 쓰기. **사본**(writer `dc_seal_region`은 `dc_op` writer가 아니다).
- `detail.rhs` = `StackJudge.rhs` = 인자 `vgs_y`의 반환 → 같은 필드. **사본**, 그리고 같은 detail 안에서 `vgs_y`와 같은 값이다(graph 규칙 3).
- `loop_stack_notes.rhs` → `graph.loop_stack_notes` 쓰기. **사본**. 출력 함수 면제는 (iii) 결과 JSON에만 있어 graph 필드 쓰기에 해당하지 않는다.
- `lhs_max`, `vp_v`, `vp_n`은 산술이라 새 값이다. 통과.

spec의 '걸리면 멈춤'은 멈춤이 확정된 일을 코드 뒤로 미루는 것이다.

**고칠 문언.** 계획부터. HC:299: '함께 적는 값: X·Y 이름, 판정식 좌변 값과 좌우 차 `gap_v`(우변 = 좌변 + 차. VGS(Y)는 같은 점 `device.dc_op[Y].vgs` -- 규칙 L-5·graph 규칙 4), VP 보고 칸'. 원래 취지와 다름에 올린다.

interface §5 `detail`: `reason = "stack_unsaturable"`, `x`, `y`, `lhs_max`, `gap_v`, `l_at_max`, `vgs_at_max`, `vp_v`, `vp_n`. `gap_v` = `vgs_y` − `lhs_max`, **`lhs_max`가 None이면 None**(모든 점 제외인 `holds` True 경우, 산술 금지). `graph.loop_stack_notes` = ((칸, X, Y, `lhs_max`, `gap_v`), ...). `StackJudge.rhs`는 호출 안 임시 묶음으로 남긴다(R-1~R-4 그대로). HC-D §7.2·§7.3, spec E-9 행·'값 칸' 문단 같음. H13: `gap_v` 손 값(R-1: 0.25).

### V10. `on_structural` 정의가 계획보다 좁고 H20 toy에 그런 소자가 없다

**사실.** 계획 HC:350 '`zeros` 때문에 **전류가 늘 0이 되는 MOS**'. interface §2.3은 '`("current", device)`가 `zeros`에 없음'이다. `zeros`는 독립 θ 전류 성분뿐이다(`search/current_symmetry.py` 머리). 직렬 가지의 다른 MOS는 `dc_current_basis.rows`에서 그 성분을 항으로 읽을 뿐 자기 성분이 없다. 그래서 직렬 MOS 둘이면 하나만 잡히고 나머지는 `on_structural` True로 남아 방향 변이 들어간다. 비전도 VDS 부호는 물리가 정하지 않으므로 유효점을 자를 수 있다.

H20 '기존 `test_current_symmetry` 구조적 0 회로: `on_structural` False'는 그 회로(`series_sense`)의 `zeros` ⊆ {R1, R2}(`test_current_symmetry.py:149`)라 MOS가 없어 **성립 불가**다. H-I·G3의 '구조적 0 toy'도 회로가 없다.

**고칠 문언.** §2.3: '`on_structural` = `off` 선언이 아니고, 구조적 0 전류가 아니다. **구조적 0 전류 = 그 소자 `dc_current_basis.rows` 행의 항이 하나 이상이고 항의 source가 전부 `zeros` 성분(`("current", source)`)이다.** 고정 전류 항이 하나라도 있으면 구조적 0이 아니다'. HC-D §5.1 같음.

H20·H-I·G3 공용 toy를 interface에 적는다: `series_sense`의 감지 가지를 o1 — M7 — R1 — m — R2 — M8 — o2로 바꾼다(M7·M8 대칭, gate 바이어스, m은 M6 gate만 구동). `I(M7) = I(R1) = I(R2) = I(M8) = 0` → M7·M8 둘 다 `on_structural` False(한쪽만 `zeros` 성분). 이 회로가 `dc_current_basis`·`s1_symmetry`에서 정지하지 않는지는 **미측정**이라 test 작성 때 먼저 확인하고, 정지하면 멈추고 보고한다.

### V11. `dc_seal_triode`의 `judge_region` 둘째 호출 (graph 규칙 1, EO-1 test)

**사실.** interface §1·§5, HC-D §7.4: `region` = `judge_region` 값, writer `dc_seal_triode`. `dc_seal_region`은 이미 **모든 MOS**에 `judge_region`을 한 번 부른다(`20261104-eo1r4-sf1l.interface` :44). 같은 소자·같은 입력의 재계산이고 둘째 생산자다. EO-1 T-R3 '호출 자리 = `dc_seal_region`·`off_region_gate` 둘', T-S5 '한 평가에서 소자당 1회'가 깨진다. HC-1 '옛 test 정리'에 이 둘이 없고, 고치면 기준 약화다.

**고칠 문언.** `device: dc_triode_region` writer = **`dc_seal_region`**(같은 순회의 `RegionJudgment.actual`을 씀, READS에 `graph.triode_protected`, WRITES에 이 필드). `dc_seal_triode`: READS `device.dc_op`, `device.region_decl`, WRITES `graph.dc_seal_triode`만(게이트). `dc_sat_v`·`triode_protected` READS 삭제(안 읽는 READS는 L-3 위반). HC-D §2 소유표 두 행·§7.4, D40 소유표(`triode_protected` 소비자), interface §5 표 머리 맞춤. EO-1 test는 그대로 둔다. H15·H16은 필드 값만 보므로 그대로다.

### V12. F-9가 §3.1 닫힌 식과 어긋난다

**사실.** F-9: `vr_bounds` None, 기대 '`vr_lo`·`vr_hi` 항목 None'. §3.1 식: `vr_lo[R]` = K(far) − K(near) + (near → far 최장 경로). `F_STAR → x` 경로가 M1(0.25)으로 있으니 0 − 1.8 + 0.25 = **−1.55**다. `vr_hi`는 x → `F_STAR` 경로가 없어 None이다. 같은 card 안 두 oracle이 달라 작성자 간 dispute가 난다. 물리로도 식이 맞다(x ≥ 0.25이면 V_R ≥ −1.55). F-1~F-8은 손으로 재계산해 모두 맞다.

**고칠 문언.** F-9 기대: 'x 하한 0.25, `vr_lo` −1.55, `vr_hi` None'. §3.1에 '`vr_lo`·`vr_hi` = ((저항, 값 또는 None), ...) `vr_edges` 순, 경로 없으면 None. `vr_bounds`가 None이어도 식 그대로'.

### V13. monkeypatch 관찰 지점이 없다 (test 작성)

**사실.** H8 `f_exist` 호출 0, H14 `stack_unsat` 호출 0, H15 호출 0, H18 `sat_threshold` 호출 0, H23 `f_exist` 감싸기는 모두 호출을 가로채야 한다. interface의 관찰 지점은 `layer0_center.evaluate` 하나뿐이고, 머리는 '파일 자리는 단언하지 않는다'이며 `iv_kvl_choice`라는 모듈 이름도 §7 test 파일 이름에만 나온다. `from … import` 꼴이면 패키지 이름을 감싸도 잡히지 않아 test가 공허하게 통과한다. 소스를 볼 수 없는 작성자는 낼 수 없다.

**고칠 문언.** §4 끝 또는 §7 머리:
> **관찰 지점**(모듈 전역 이름, 파일 단언 금지의 예외): `gmid_engine.search.iv_kvl_choice.f_exist`, `.stack_unsat`, `.sat_threshold`; `gmid_engine.sizing.seal_region.stack_unsat`; `gmid_engine.search.search_domain.sat_threshold`; `gmid_engine.search.layer0_center.evaluate`. 구현은 이 이름으로 부른다. 호출 0 단언마다 '있어야 할 입력에서 호출 ≥ 1'을 같은 test에 둔다(공허 통과 방지).

§7 '단언 금지: 파일 자리'에 '(관찰 지점 제외)'를 더한다.

## 지시 항목별 확인

**1. 손 값 대조.**
- F-1~F-8·F-10, 표 3.2, R-1~R-4(lhs = 0.75V − 0.25V² − 0.0625 − 0.125·VS − 0.0625·iL, 정점 V = 1.5), G-a~G-d, `order_terms` 손 값(as-built와 부호 같음), §2.1·§2.3 손 값 전부를 직접 유도해 **맞음**.
- 틀림: F-9(V12), H19 배선(V4), H20(V10).
- `None` 산술: V1(`bracket_root`), V7, V9.
- 자리 없음: V5, V6, V13.

**2. E-4.**
- HC:258 '그 좌표의 구간' 대 L 칸: 맞음. L은 상자의 좌표이고 칸이 그 구간이다(LR3·DEC-95 (1)).
- bin 경계: 넘지 않음. 칸 = bin이고 `bracket_root` 구간이 칸 안이다. 맞음.
- tol = `grid_m`: PDK 역할 이름이고 `manufacturing_grid_m`에서 온다. 반복 정지 기준이고 근 오차가 tol/2 이내라 물리 경계를 정하지 않는다. 상수 발명 아님. 맞음.
- `chain_cut` 호출자: `search_domain`이 있어 만들면 배선은 충족한다. 발동 드묾은 A-18 보고 항목.
- 칸 표본(V1), 좌표(V2), 대상 변(V3)은 틀림. 세 건 모두 '해를 잃는' 쪽이다.

**3. E-6.** 위 절. **기준 약화 아님**, 멈춤 아님.

**4. E-7.**
- 계획 정정 맞음: `headroom_bound.py:131` status는 전역 순환 여부뿐이고 경로 없는 넷은 CERTIFIED다.
- GC:644 수정 정당: 같은 거짓 문장의 전파 자리이고 안 고치면 두 계획이 모순된다. A-51 '계획에서 먼저 고침'의 범위 안이며 history 행이 있다.
- UNKNOWN: `_judge`(`:159-161`)가 UNDETERMINED를 내므로 거짓 정지가 없다. 예산 행만 빠져 좁히지 않을 뿐이고, 거부는 봉인·J_point가 맡는다. fail-closed 맞음.
- 무동작: `on_structural` False 변이 없으면 발동 0이고 저항 넷은 CERTIFIED + 레일 끝 불변이다. 맞음.
- 낡은 문장 하나는 m1, test 빈칸은 m2.

**5. E-5.**
- 새 memo 아님: 기존 `LutMemo`의 창 시점만 바뀐다(승인 예외 안).
- 퇴출 재계산 0 방향: 창 안 키 집합 ⊇ 첫 `evaluate` 키(graft된 DC 키도 칸 판정 때 세고, 안 된 키는 첫 평가에서 센다)라 U는 줄지 않는다. 옛 그대로면 U 과소이므로 후보 판단이 맞다.
- 상태 기계: `evaluate:120`은 `counting`일 때만 열고 `:168`은 `window_open`일 때 닫아 이중 열기 `ValueError`가 없다. 칸이 없으면 `evaluate`가 연다.
- 색인 상한: `judge_rungs`는 `open_bound`(`find_front` 진입) 앞이라 등록 검사 밖이나 항목 수에는 든다. A-9가 잰다.
- 문언 잔재 m6.

**6. E-9·E-2 graph 규칙.**
- `TriodeRegion` 값 칸 삭제: 맞음(V11로 writer만 옮김).
- `ends_theta`·`far_node`·`near_node`: 값 사본 아님(같은 블록의 구조 파생), reader `f_exist`.
- writer 하나: `dc_triode_region` 위반 없음이나 `judge_region`이 V11.
- 소유표: HC-D §2 행 전부 존재.
- 새 칸 소비자: V8 외 충족(`coords` = `search_domain`·`route`, `VrEdge.far_net` = 드라이버).
- `vgs_y`·`rhs` = **걸린다**(V9).
- `Layer0Result.chain_filtered`는 m7.

**7. E-1 대입.**
- 규칙 A: `chain_exist`·`chain_judge`·`chain_cut`·`seal_triode`·`stack_unsat`·`stack_candidates` 각 진입점 1. `iv_kvl_choice`는 `judge_rungs`가 `loop_dependents`를 Name으로 부르니 개념 1. `kernel.py`는 `evaluate`가 `dc_prefix`를 부르면 개념 1(`entry_points`, `:233-249`). 통과.
- `upward_pair` 사용 파일 둘: `writer_plan.py`, `chain_graph.py` 둘 다 sizing이고 `helper_users` 범위 안, import 꼴 `from ._helpers_polarity import upward_pair`면 사실이다. 입력이 달라 재계산도 아니다.
- 규칙 H는 V5, 층은 V6.

**8. E-8 소비자 전수(git grep).**
- `vds_saturation`, `REL_VDS_SATURATION`, `_edge_nets`, `vds_min_v`, `order_terms`, `headroom_bound(` 호출자 둘, `current_symmetry`(`graph/s1_*`의 같은 이름 필드는 다른 정의) 모두 표와 일치.
- 빠진 것: `tests/sizing/test_seal.py:31·73`, `test_seal_report.py:21`, `test_s2_values.py:189`(m3), `pipeline/stage_b.py`(m9).

**9. 정합.**
- N6.1(P:1370) 선행 TB-1·HC-S·IT-1·GC-1·card C = spec 착수 4와 일치. GC-1 직후 병합(GD §1, A-32) 일치.
- O-224·A-16 칸 단위 읽기: 일관(`rung`만 거르기, 나머지 출력).
- 재개방·R6 없음: 지킴.
- DC·AC: DC만이고 맞음.
- 상수 발명 0, PDK 역할 이름만, 규칙에 회로 이름 0(회로 이름은 A-10 측정 칸뿐).
- 만들면 배선: 충족(A-18 기간 예외 표지 있음).
- A-34: 대입 결과 `gvgs_cycles.py`·`s1_values.py`·`stack_candidates.py`·`s1_build.py`(`graph/s1_build.py` 실재)가 `S1V_RULE_FILES` ∪ `STRUCTURE_RULE_EXTRA_FILES` 밖이므로 해당 없음. 맞음.
- GL-1 래칫: 구조 금지 문장 충족, 수치는 미측정.
- 순서: 계획 → design → card 커밋 순서 지킴.
- 원칙 8: m10.

## minor

- **m1** HC:342 남은 문장 '레일에서 닿지 않는 넷은 구조적 0 전류 소자를 뺄 때에만 생긴다'가 같은 행 뒤 문장과 어긋난다. → '**방향 변을 빼서 새로 닿지 않게 되는 넷**은 구조적 0 전류·`off` 소자를 뺄 때에만 생긴다(저항만 닿는 넷은 원래 경로가 없다)'.
- **m2** `WHY_WINDOW_UNKNOWN`에 test가 없다(H-I는 '예산 행 없음'만). G3에 `headroom_bounds(...).inactive` 단언을 더하고 공개 이름 자리(`gmid_engine.search`)를 §6.1에 적는다. §6.2에 '전역 순환이면 전부 UNKNOWN, 지금과 같음'(GD에는 있음).
- **m3** 옛 test 정리에 `tests/sizing/test_seal.py:31·73`, `test_seal_report.py:21`(`range(1,10)`), `test_s2_values.py:189` 추가(새 항목 번호).
- **m4** `SearchContext.loop_conflicts`는 `self.dc.base.field("graph", START_KEY, "loop_conflicts")` 꼴로 적는다(`rungs`와 같음). `_field` 꼴이면 L-1이 읽기로 세지 않는다(GC-1 spec S-6).
- **m5** `dc_prefix(sctx, theta, cells, origin)`의 `cells`·`origin`은 §4 어디서도 쓰이지 않는다. 쓰임을 적거나 뺀다. `expand_ties`를 거친 θ임도 적는다(graft 입력이 같아야 H11이 성립).
- **m6** LUT memo 창 문장 '첫 커널 평가'가 D40 §2.4.6, `lut/CONTRACT.md:307·318`, `search/CONTRACT.md:457`에 남는다. HC-D §13 인계와 재작성 범위에 추가.
- **m7** spec '정본은 `loop_conflicts`' → '`chain_filtered` = 순회가 실제로 건너뛴 칸(첫 수용 칸에서 멈추므로 `loop_conflicts` 칸 번호의 부분집합, 축이 다르다. HC:259 보고 칸)'. graph 규칙 3 '다른 축을 적는다'.
- **m8** 입력 점 n 포트의 `RootPath` 값이 없다(IT-1 `input_point`). §2.1에 'n 포트 = p 포트와 같은 `root_kind`·`root_net`·`steps`' 한 줄(작성자 표지 '안 잼' 닫음, 손 판정 기준 IT-1 T-1a·T-1c).
- **m9** `pipeline/stage_b.py:156-159`도 `search_domain`을 부르고 `untie`를 따로 만든다. 표에 '무변경 확인' 행. `untie_element_unknown`·`untie_orbit_trivial` 정지 자리가 `search_domain`에서 `build_kernel_context`로 옮겨 가는 것을 H20에 적는다(gate 이름 포함).
- **m10** spec E-4 '사실' 칸이 as-built `search_domain.py`로 자리를 유도한다(원칙 8). 근거를 '계획 LR3·DEC-95 (1): L은 칸 고정 뒤 칸 안 연속'으로 바꾼다. 결론은 같다.
- **m11** VP 식이 interface에 없다. §5에 `vp_v = (V_G − V_B − VT0)/n`(HC N3.2), `gm` 0이면 `vp_v` None + `vp_reason`을 적는다(0 나눗셈 방지).
- **m12** A-52 결정 문언에 `LoopConflict.cycle` → `exist`를 적는다(로그는 오케스트레이터 몫). `ChainExist` 구간 칸의 `output_only_slots` 등록은 빼는 것을 권고: reader가 있으면 L-4 통과, 지문 변경 0, reader 삭제 때 L-4가 직접 잡는다. H23b는 'AST 읽기 위치'만 남긴다. HC-D §2·§6.3, GD §3, spec 규칙 L 문단 같음.

## 미측정(실행 필요)

pytest 전부, 규칙 L·구조 test 실행 결과, `ratchet.new`, `scan_shared_calls`, 13회로 칸 거르기·단좌표 발동·구조적 0 소자 수, 칸당 시간, `lut_memo_evictions`·`block_index_bound`, V10 toy의 `dc_current_basis`·`s1_symmetry` 통과 여부, IT·EO-1·card C·TB-1·HC-S·GC-1 코드 뒤 줄과 이름, `_chain_start_note` 출력 함수 자격의 검증자 독립 재측정. VDSAT(L)이 실제 LUT 칸 안에서 비단조인 점의 존재는 재지 않았다(V1은 '근거 없이 가정함'의 지적이고, 앵커 표본이면 어느 쪽이든 맞다).

1차 판정(head `9a70020e`): Major 13

---

# 재판정 (head `ae589892`)

대상: `docs/cards1104c`의 `b0d8af25..ae589892`(headroom-chain 0.7.9.11, design v1.16.9, HC-D v0.1.5, GD v0.1.2, card), base `3c12014a`. 범위는 이 diff와 그것이 닿는 문장이다. 내 V1~V13 문언도 같은 잣대로 다시 봤다. 실행은 없고 문서 읽기와 `git grep`·`git show`만 썼다.

**결론: V1~V13·m1~m12는 모두 들어갔고 Major 4가 새로 나왔다.** R1·R2와 R3의 H18은 **내 문언에서 나온 결함**이고, R3의 나머지와 R4는 1차 때 내가 놓친 것이다. 멈춤(위임 밖) 0. 넷 다 문언 몇 줄로 닫힌다.

## 1. 반영 확인(원문)

| 항목 | 자리 | 상태 |
|---|---|---|
| V1 | interface §4.1 표본·행 2·3·5·`anchors`, H19 앵커 표본, HC-D §6.5, spec E-4 | 들어감. (−1,+1,+1,−1) → (1.5, 3.5) 손 재확인 |
| V2 | §2.3 `coords`, HC-D §5.1 | 들어감. 손 값 회로는 R2 |
| V3 | §4.1 `on_structural`, `margin_of`, H18 | 들어감. H18 문장은 R3 |
| V4 | H19 배선, 행 5 '남은 끝' | 들어감. 회로는 R2 |
| V5 | §7 test 자리, 옛 test 정리, spec E-1, HC-D §10 | 들어감. `check_h` 대입 통과 |
| V6 | §1 `ChainCut` sizing | 들어감 |
| V7 | §4 `f_exist` 입력, HC-D §6.1-2, H3·H23 | 들어감(레일 처리는 작성자 쪽이 맞음) |
| V8 | §4 JSON, H23, §5 `l_at_max`·`vgs_at_max`, HC-D §6.3 | 들어감 |
| V9 | HC:299, §4·§5 `gap_v`, HC-D §7.2·§7.3, H13 | 들어감 |
| V10 | §2.3 정의, 공용 toy, H20·H-I·G3, HC-D §5.1 | 들어감 |
| V11 | §5, HC-D §2·§7.4·§9, D40 소유표, spec 계약 9 | 들어감 |
| V12 | F-9, §3.1 | 들어감 |
| V13 | §4 관찰 지점, §7 단언 금지 | 들어감. `search_domain` 지점은 R1 |
| m1~m4, m6~m8, m10~m12 | HC:342, §6.1·§6.2, 옛 test 정리, §4, HC-D §9·§13, spec, §2.1, §5 | 들어감(m12는 구간 칸까지, r1 참조) |
| m5, m9 | 택일함 | 아래 3 |

정지 사유: 계획 커밋 `5cb36338` → design `c5b7bdda` → card `ae589892` 순서를 지켰다. history 행 있음(`headroom-chain.history.md:330`). spec '원래 취지와 다름' 5에 HC:299가 있다.

## 2. 작성자가 내 문언과 달리 적은 네 곳

| 곳 | 판정 | 근거 |
|---|---|---|
| V7 `V(net)` = 레일이면 `node.dc_rail_v`, 아니면 `node.dc_v` | **작성자가 맞음, 내 문언이 틀림** | `block_columns.py:776`이 `dc_v`에서 레일을 뺀다. 내 `node.dc_v[net]`이면 레일에서 `KeyError`다. `sizing/CONTRACT.md:228` '노드전압 정본: 레일 = `dc_rail_v`, 그 밖 = `dc_v`', `front_query.py:21·45`도 같다 |
| V13 `gmid_engine.sizing.block_widths.sat_threshold`, `iv_kvl_choice.sat_threshold` 삭제 | **작성자가 맞음** | `dc_sat_v` writer = `dc_widths`(HC-S spec :34·:56). `judge_rungs`는 블록 열로 필드를 읽고(§3.2 `view.sat`), `stack_unsat`은 `sat_threshold_grid`를 쓴다. 내 목록의 `iv_kvl_choice.sat_threshold`는 호출이 없어 공허한 지점이었다. 커널 창 행 호출은 EO-1 '창 행에 `off` 소자 행 없음'(interface :85)이라 관찰이 필요 없다. 같은 목록의 `search_domain` 지점은 R1 |
| m2 `gmid_engine.search.iv_headroom.headroom_bounds`, 세 이름 `gmid_engine.search.start_values` | **작성자가 맞음** | `search/__init__.py`에 `headroom_bounds`·`iv_headroom` 재수출이 없다(grep 0). `SRC_HEADROOM_*`은 `start_values.py:25-26`, `WHY_*`도 같은 파일이다 |
| V5 H6 = `test_chain_judge.py`, H3 = `test_chain_exist.py` + `test_iv_kvl_choice.py` | **작성자가 맞음** | H6은 §3.2 행 1·2뿐이라 내 'H6의 F 부분'이 없다. H3의 F-4는 `f_exist`다. H7이 F-10을 `test_chain_graph.py`에 두는 것도 규칙 H에 걸리지 않는다 |

## 3. 작성자 택일

- **m5 `dc_prefix(sctx, theta, geometry=None)`**: **틀림(R4).** 안 쓰는 `cells`·`origin`을 뺀 것은 맞다. 그러나 `geometry`를 넣은 근거('`evaluate`가 이 함수를 지나간다')가 성립하지 않는다.
- **m9 gate `"dc_current_symmetry"`**: **맞음.** 지금 gate 문자열은 writer 이름이고(`current_symmetry.py:37`), writer가 옮겨 가므로 같은 규칙이다. gate 문자열 엔진 소비자 0(`"search_domain"` 다른 자리는 READS·writer 이름). 기대값 교체는 `broken_tests`로 기록되고 판정 완화가 아니다. 정지 자리도 안전하다: `build_kernel_context`의 탐색 전 호출자 `stage_b.py:152`가 `SchemaRejectedError`를 받는 `try` 안이다. `test_orbit_ties.py`는 :156만 적혀 있고 :165·:171도 있다(r3).
- **V12 K = `weights[저항]`**: **맞음.** `vr_bounds`가 None이어도 저항 K 출처가 인자 하나로 닫히고 §4 `f_exist` 입력과 일치한다. F-9 −1.55 재확인. `VrEdge`가 있는데 `weights`에 키가 없는 경우만 안 적혔다(r5).
- **V10 toy**: **형식 맞음, 통과는 미측정.** 손 유도: KCL(a) I(M7) = I(R1), KCL(m) I(R1) = I(R2), KCL(b) I(M8) = −I(R2), 대칭 I(M8) = I(M7) → x = −x → 0. KCL만으로는 0이 아니어서(자유 변수 하나) `mos_zero_current_structural`이 아니다. M7↔M8은 자기 맞바꿈이 아니어서 `ds_self_swap`도 아니다. `zeros` 성분이 어느 원소든 §2.3 정의로 M7·M8 둘 다 False다. 이 회로는 `basis.mos`의 전류가 0이라 모든 칸이 원뿔 밖이지만(`block_currents.py:35-37`) H20·H-I·G3는 S0 단계만 보므로 성립한다. 쓰기 계획 통과 여부는 card의 표지대로 test 때 먼저 잰다.

## 4. E-6

**`ChainExist`·`ChainCycle` 등록을 뺀 상태: L-4 통과.** GC-1 spec 계약 6 판정식은 '값 선언 모듈의 칸마다 `self`가 아닌 수신자의 속성 읽기, 상수 `getattr`, 모듈 수준 문자열 중 하나'이고, 진입점 도달은 요구하지 않는다. §4 JSON이 칸 이름을 하나씩 정의했으므로 `_chain_start_note`의 `e.node_lo` 꼴이 그 읽기다. `dataclasses.asdict`나 동적 `getattr` 꼴로 구현하면 L-4가 실패해 드러나므로 안전한 방향이다. 등록이 없으니 reader를 지우면 `slot_no_reader`가 직접 난다. H23b와 맞다. **기준 약화 아님**은 그대로다.

**`LoopConflict` 내용 칸·`SearchDomain.chain_cuts` 등록이 남은 것: 옳지 않으나 기준 위반은 아니다(minor r1).** 같은 `_chain_start_note`가 `state`·`rows`·`exist`·`reason`·`chain_cuts`를 읽으므로 같은 논리로 등록이 필요 없다. 등록의 유일한 효과는 reader 삭제를 L-4가 못 잡게 하는 것이고, interface §7이 `ChainExist`를 뺀 근거 문장이 이 칸들에도 그대로 적용된다. 소유표 근거가 있어 GD §3 J1상 기록된 변경이므로 멈춤은 아니다.

## 5. V9 판단

**`gap_v`는 L-5를 실제로 비껴가고, 꾸밈이 아니다.**
- **규칙 문언**: N3.1-5 '칸으로 계산한 산술 결과는 새 값이다', '출처 값이 산술로 끊기면 그 값의 추적은 끝난다'. `vgs_y − lhs_max`가 그 꼴이다.
- **규칙 취지**: L-5가 막는 것은 정본과 따로 사는 같은 양이다. `gap_v`는 VGS(Y)와 다른 양이다. `holds` ⇔ `gap_v` > 0인 판정식의 여유 자체이고, 이미 통과로 분류된 `rows`의 VDS − VDSAT, EO-1의 `slack_v`, `indistinct`의 VDS − vdsat과 같은 부류다. 엔진 reader가 0이라 더해서 VGS(Y)를 되살려 계산에 쓰는 자리도 없다.
- **꾸밈이 되는 조건**: 어떤 소비자가 `lhs_max + gap_v`로 VGS(Y)를 복원해 계산에 쓰면 그때는 정본 우회다. 지금은 없다. HC:299 '우변 = 좌변 + 차'는 보고를 읽는 사람용 설명으로 둔다.
- **남는 한계**: HC:299의 'VGS(Y)는 같은 점 `device.dc_op[Y].vgs`'는 봉인점에 맞다. `loop_stack_notes`의 칸 점 스냅샷은 JSON에 남지 않으므로 칸 기록에서는 합으로 읽는다. 결과 차이는 없다.

**`lhs_max`는 사본이 아니다.** LUT 격자 위 VGS − VDsat의 최댓값이고 `dc_op` 칸이 아니다. `vgs_y`·`vsb_x`는 입력으로 들어가 격자 산술에서 끊긴다. `l_at_max`·`vgs_at_max`도 LUT 축 값이다.

**`StackJudge.rhs`는 내 문언의 흠이다(minor r2).** '호출 안 임시 묶음으로 남긴다'고 적었으나 이제 `.rhs` 엔진 reader가 0이고 입력을 되돌려 줄 뿐이다. 그리고 `gap_v` 산술과 None 가드가 `seal_region`·`iv_kvl_choice` 두 자리에 있다.

## Major

### R1. 관찰 지점 `gmid_engine.search.search_domain.sat_threshold`는 점 표기로 모듈이 아니다 (내 V13 문언)

**사실.** `search/__init__.py:54` `from .search_domain import search_domain`이라 `gmid_engine.search.search_domain`은 **함수(블록)**다(GC-1 spec 계약 9 '패키지의 재수출 이름은 같은 이름 하위 모듈보다 앞선다'). `monkeypatch.setattr("gmid_engine.search.search_domain.sat_threshold", …)`는 그 함수의 속성을 찾아 `AttributeError`로 끝난다. test 작성자는 소스를 볼 수 없어 이유를 모른다. 다른 지점(`iv_kvl_choice`, `seal_region`, `block_widths`, `layer0_center`)은 같은 이름 재수출이 없어(`search/__init__.py`, `sizing/__init__.py` grep) 문제없다.

**고칠 문언.** §4 관찰 지점 뒤:
> `search_domain` 모듈은 `sys.modules["gmid_engine.search.search_domain"]`로 얻는다. 패키지가 같은 이름의 함수를 재수출해 점 표기로는 함수가 나온다. 구현은 그 모듈 전역 이름 `sat_threshold`로 부른다.

### R2. 손 값 회로 둘이 불러들이기에서 멈춘다 (내 V2·V4 문언)

**사실.**
- `authoring/ports.py:13`: 유효한 input·output 포트가 없으면 `no_input_port`·`no_output_port`로 거부한다. §2.3 M1·M3 toy와 H19 M1 toy는 레일과 `nb`뿐이라 포트 자리가 없다.
- §2.3의 `mos("M1","nmos","nb","nb","gnd")`는 넷 `nb`에 M1 drain만 전류를 대므로 KCL상 I(M1) = 0이다. `sizing/current_basis.py` `mos_zero_current_structural`로 정지한다. 내가 V2에서 낸 회로이고 전류원을 빠뜨렸다.

**고칠 문언.** §2.3 손 값(gate 넷 좌표):
> `circuit_mirror()`(M1 nmos (nb,nb,gnd), I1 vdd → nb, 포트 있음) netlist에 `mos("M4","nmos","vdd","nb","gnd")`를 더한다. M4 `coords` = (`("L","M1")`,`("L","M4")`,`("ln_idu","M1")`), `route = "filter"`(gate 경로 없이 세면 `cut`이라 red). `build_ctx`(L 동치류 주입 없음).

H19 배선:
> `circuit_cs_pmos_load()` netlist에 `mos("M9","nmos","vdd","vdd","gnd")`를 더한다. 레일 vdd 0.125·gnd 0, R4 LUT. M9 `route = "cut"`, g(1e-6) = +0.02734375, g(2e-6) = −0.03515625 → M9 칸 = ((1e-6,1e-6),), `chain_cuts`에 M9 한 행 `"hi"`, 값 1e-6. M1·M2는 `filter`이고 칸 불변.

HC-D §10·spec 인용은 id만이라 변경 없음. 두 회로의 실제 통과는 미측정이고 test 작성 때 확인한다.

### R3. `off` 소자는 `dc_op`·θ 스키마에 없다 -- 그 사실과 어긋나는 칸 셋

**사실.** EO-1 interface :85 '`off` 소자: `device.dc_op` 키에 없다. 쓰기 계획 열거, 전류 기저 항, θ 스키마 변수에 없다'.

1. **H18(내 V3 문언)**: '레일에 걸린 `off` 소자: 그 소자 L 칸 불변'. L 칸이 없어 기대값이 성립하지 않는다.
2. **§5 봉인 세분, HC-D §7.2**: `dc_op[Y].current > 0`. Y가 `off` 선언이면 사유 없는 `KeyError`다. `off` 소자 보정점 관문보다 앞이고 fail-closed 사유가 아니다. §7.3은 `off` 선언 X만 적었다. 1차 때 내가 놓쳤다.
3. **§2.4 `triode_protected`**: Z 조건에 `off` 제외가 없다. `off` Z는 포화 판정을 받지 않는데 Z로 세면 `protected_none`이 False로 나와 '지켜지는 소자의 포화 판정이 남는다'는 거짓 기록이 된다(N3.3-3).

**고칠 문언.**
- H18: '레일에 걸린 `off` 소자: `l_cells`에 항목 없음, `chain_cuts`에 그 소자 행 없음, `sat_threshold` 호출 0(`search_domain`, 같은 test에 다른 `cut` 변이 호출 ≥ 1)'.
- §5: '(X, Y) ∈ `stack_candidates`, **Y가 `off` 선언이 아니고**(`dc_op` 키가 없다, `region_decl`로 먼저 거른다) `dc_op[Y].current > 0`'. HC-D §7.2·§7.3 같음. H14에 Y `off` 행 추가: 일반 사유, 예외 0, `stack_unsat` 호출 0.
- §2.4: 'Z = (Z ≠ X, `off` 선언 아님) 지우기 전 …'. H17에 `off` Z 행 추가: 목록에 없음.

### R4. `dc_prefix`가 `evaluate`의 길이 될 수 없고, 그대로면 규칙 A를 어긴다 (m5 택일, 1차 내 대입의 조건부)

**사실.**
- `evaluate`는 `parent`를 받아 `size_and_seal(dc, dict(pairs), parent=base, w_request=…)`를 부르고(`kernel.py:94·128`), 실패에서 `failure, partial = exc.record, exc.partial`을 쓴다. 새 서명 `dc_prefix(sctx, theta, geometry=None) -> (snapshot | None, failure | None)`에는 `parent`도 부분 스냅샷도 없다. HC-D §5.3 '`evaluate`도 이 함수를 지나간다', interface §4 '`evaluate`도 같은 길을 지난다'를 지키면 lineage 재사용과 `EvalResult.partial`을 잃는다.
- 지나가지 않으면 `kernel.py`에서 `evaluate`와 `dc_prefix`가 서로 Name으로 안 불려 뿌리 둘이다. `entry_points`(`structure_checks.py:233-249`) 개념 2 → `check_a` 위반. 1차 7항에 '`evaluate`가 `dc_prefix`를 부르면 개념 1'이라 조건을 달고 넘어간 자리다.
- `geometry`는 유일한 호출자 `judge_rungs`가 안 넘긴다. 호출자 없는 인자다.

**고칠 문언.**
- interface §4: `dc_prefix(sctx, theta) -> (snapshot | None, failure | None)`. '`evaluate`와 **같은 블록 열 함수**를 지난다: `gmid_engine.sizing`의 커널 앞부분을 `run_kernel`과 `dc_prefix`가 함께 부른다(같은 `donors`·`counters`, `parent = None`, `w_request` 없음). `evaluate` 자체는 `dc_prefix`를 부르지 않는다'. 창 열기 문장은 그대로.
- HC-D §5.3 결정 문장: '`E/search/dc_prefix.py`(새 파일, 진입점 하나)에 `dc_prefix(sctx, theta)`를 둔다. 블록 열은 `E/sizing/kernel_run.py` 앞부분을 나눈 함수이고 `run_kernel`이 부른다(`kernel_run.py` 뿌리 하나)'. §9·spec 재작성 표: `search/kernel.py` 행을 `search/dc_prefix.py`(새 파일, `_module_map`·`search/__init__.py`)로. `kernel.py`는 창 열기 조건이 이미 `counting`일 때만이라 변경 없음.
- §7: H11·H24 행에 `tests/search/test_dc_prefix.py`(규칙 H) 추가.

## minor

- **r1** `output_only_slots`에서 `LoopConflict` 내용 칸·`SearchDomain.chain_cuts`도 뺀다. 그러면 목록이 GC-1 그대로 빈 tuple이다. 이유는 위 4. interface §7, HC-D §6.3 '규칙 L 표현' 문장, GD §3. `output_only_fields`·`output_functions` 추가는 L-2가 요구하므로 남는다.
- **r2** `StackJudge(holds, lhs_max, gap_v, l_at_max, vgs_at_max)`로 바꾼다. `rhs` 칸 삭제(reader 0), `gap_v`와 None 가드를 `stack_unsat` 한 자리에서 낸다. R 표에 `gap_v` 칸(R-1 0.25, R-2 0, R-3 1.265625, R-4 0.28125). §5 닫힌 식 문장 `rhs` 줄 교체. R-2 `holds` False(엄격)는 그대로다.
- **r3** 옛 test 정리에 `tests/search/test_orbit_ties.py` :165·:171을 더한다(gate·호출 경로). `_domain(case, ("Nope",))` 꼴은 `search_domain`만 부르므로 `DcInputs.untie_orbits` 경로로 바꿔야 한다. 안 바꾸면 `orbit_ties.py:33`의 `KeyError`다.
- **r4** §4 '그 행은 `rows`에 이미 있다'는 `reverse_vds`에만 맞는다. 행 5는 표지다. → '(대체값 없음. `reverse_vds`는 `rows` 행, 그 밖 사유는 정의 불능 표지)'. `vr_bounds`의 'θ 저항 상자'에 '묶음 구성원은 대표의 상자(`domain.ties`)', 전류 부호에 '`dc_current`의 저항 양의 방향 = 정렬 전 첫 단자 → 둘째 단자, far → near로 환산'을 더한다(전류 부호는 착수 때 base에서 확인, 미측정).
- **r5** §3.1: '`VrEdge`가 있으면 `weights`에 그 저항 키가 있어야 한다. 없으면 호출 계약 위반 `ValueError`'.
- **r6** HC-D §13 표에 '41 §4.8-3: `dc_seal_region` WRITES에 `device.dc_triode_region`, READS에 `graph.triode_protected`·`graph.stack_candidates`' 행.

## 6. 새 모순 점검 결과

R1~R4 외 없음.
- `None` 산술: V7(`vdsat_v` None 제외), `gap_v`(가드), `margin_of`(None 처리), `bracket_root`(넘기지 않음), `vr_lo`(경로 없음 None) 모두 닫혔다. `dc_op` 키 없음만 R3.
- 공개 함수 자리: R1·R4 외 닫힘.
- interface만으로 기대값 불가: R2·R3 외 닫힘. 손 값 재계산 F-1~F-10, H19 순수 toy 전부, G-a~G-d, R-1~R-4, `gap_v` 일치.
- 계획 ↔ design ↔ card: `dc_triode_region` writer, `coords`, `on_structural`, `gap_v`, `output_only_slots` 문장이 HC-D·GD·D40·spec·interface에서 일치(r1은 근거 문장 쪽). A-34는 변경 파일 변동 없음. 회로 이름·상수 발명 새로 0.

## 재판정 미측정

pytest 전부, 규칙 L·구조 test 실행 결과, R2 두 회로와 V10 toy의 실제 통과, `dc_current` 저항 부호, 선행 card 코드 뒤 줄과 이름. 첫 판정 미측정 목록은 그대로 유효하다.

재판정(head `ae589892`): Major 4

---

# 최종 재판정 (head `b8c26cea`)

대상: `docs/cards1104c`의 `ae589892..b8c26cea`(design v1.16.10, HC-D v0.1.6, GD v0.1.3, card). 범위는 이 diff와 그것이 닿는 문장이다. 계획 변경 0(`git diff --quiet`로 확인). 실행은 없고 문서 읽기와 `git grep`·`git show`만 썼다.

**결론: R1~R4·r1~r6은 모두 들어갔고 Major 0.** 멈춤(위임 밖) 0. 막지 않는 minor 5(f1~f5)는 아래에 있고 test 작성 전에 넣으면 된다.

## 1. 반영 확인(원문)

| 항목 | 자리 | 상태 |
|---|---|---|
| R1 | interface §4 관찰 지점 끝 `sys.modules` 문장 | 들어감 |
| R2 | §2.3 `circuit_mirror()` + M4, H19 `circuit_cs_pmos_load()` + M9 | 들어감. 손 값 재확인(아래 3) |
| R3 | §2.4 Z, §5 Y, H14, H17, H18, HC-D §7.2·§7.3, §4 필드 줄 | 들어감 |
| R4 | §4 서명·문장, HC-D §5.3·§9·§10, spec 계약 5·재작성 표, H11·H24 | 들어감 |
| r1 | §7 `output_only_slots` 빈 tuple, HC-D §6.3 두 줄, GD §3, spec 규칙 L | 들어감. GC-1 interface :62와 같다 |
| r2 | `StackJudge(holds, lhs_max, gap_v, l_at_max, vgs_at_max)`, §5 닫힌 식, R 표 | 들어감. R-1 0.25, R-2 0, R-3 1.265625, R-4 0.28125 손 재확인. `rhs`는 spec E-9 사실 칸과 A-6 '없음' 문장에만 남는다 |
| r3 | 옛 test 정리 :156·:165·:171, `DcInputs.untie_orbits` 경로 | 들어감 |
| r4 | §4 `vdsat_v` None 괄호, 묶음 대표 상자, 전류 부호 | 들어감 |
| r5 | §3.1 `ValueError`, F-11 | 들어감(f1) |
| r6 | HC-D §13 41 §4.8-3 행 | 들어감 |

## 2. 작성자가 달리 적거나 더한 곳

- **r4 `t0 → t1`: 맞음, 내 '정렬 전 첫 단자'보다 낫다.** 엔진 어휘가 t0·t1이다(`current_basis.py:6` '2단자 t0->t1', `s2_values.py:243`, `block_columns.py:527` 'V(far) − V(near)를 저항 r의 전류(t0 -> t1)와 저항값으로'). `block_columns.py:531-533`의 `-v if near == t0 else v`는 이 card의 'far → near로 환산'과 같은 결과다. 부호는 §3.1 정의 V_R = V(far) − V(near)가 정하므로 어긋날 여지가 없다.
- **`off` 소자 `coords` '자기 좌표를 세지 않는다': 맞음.** EO-1 interface :85 'θ 스키마 변수에 없다'에서 바로 나온다. 빠지면 없는 θ 성분을 좌표로 세게 된다.
- **'`none`은 `off` 소자와 합성 입력에서만': 맞음.** `off` 아닌 MOS는 자기 L이 θ 성분이라 좌표 ≥ 1이다. 레일에 걸린 `off` 소자는 0개다. 다만 양 끝 W4 `off` 소자는 y 하나로 `route = "cut"`일 수 있어 같은 줄의 '`cut`의 좌표는 그 소자의 L'이 `off`에는 틀린다. §4.1이 `on_structural`을 먼저 거르므로 동작 영향이 없다(f4).
- **F-11: 맞음, test 자리만 빠짐.** `weights`에 저항 키가 없으면 `ValueError`는 r5 문언 그대로다. F-1~F-10은 `VrEdge`가 있으면 `weights`에 키가 있어 깨지지 않는다. §7 H5가 F-7~F-9만 적어 F-11을 받는 test가 없다(f1).
- **H24 이동: 맞음.** 규칙 H가 `search/dc_prefix.py`에 `tests/search/test_dc_prefix.py`를 요구하고(`check_h`), H24가 그 파일을 채운다. `evaluate`를 함께 부르는 test가 그 파일에 있어도 위반이 아니다.
- **H11 양쪽 배치: 규칙 H 위반 아님, 같은 test를 둘 필요는 없음.** `check_h`는 파일 존재와 고아만 본다. 한 id가 두 파일에 걸치는 것은 H3·H8에도 있다. 내용은 나누는 편이 맞다(f3).

## 3. 새 모순 점검

**`search/dc_prefix.py` 구조.**
- **G-10·S3 graft: 맞음.** 블록 호출이 `run_kernel`과 같은 앞부분 함수를 지나므로 extras가 같다(`kernel_run.py`의 `dc_currents`·`dc_lengths`·`dc_columns`·`dc_widths`). 칸의 첫 평가는 `layer0_start`가 `parent` 없이, `geometry` 없이 부르니 `dc_prefix`와 입력이 같다(`layer0_center.py` `evaluate(sctx, theta, cells, origin=tag)`). 색인 키는 (블록, 분할, 입력 버전)이고 계보와 무관하다(D40:209). `parent`가 있는 뒤 평가에도 해가 없다.
- **둘째 생산자 아님.** `dc_prefix`는 필드를 직접 쓰지 않고 writer는 그대로 블록이다(`dc_op`, `dc_sat_v` = `dc_widths`). 스냅샷은 칸 판정 안에서 버린다. 앞부분 함수가 한 정의이고 호출자가 둘이라 계산식 사본도 없다.
- **규칙 A: 맞음.** `dc_prefix.py` 뿌리 하나. `kernel_run.py`는 새 함수를 `run_kernel`이 Name으로 부르므로 뿌리 그대로(`entry_points`). 새 함수는 공개 이름이어야 하고(규칙 B, 다른 패키지의 `_` import 금지) `gmid_engine.sizing`이 재수출한다. interface가 이름을 안 적었으나 test가 안 부르므로 막지 않는다(f5).
- **규칙 H: 맞음.** `tests/search/test_dc_prefix.py`, `tests/sizing/test_kernel_run.py`(있음).
- **층 순서: 맞음.** search(6) → sizing(4). import 순환 없음: `iv_kvl_choice` → `dc_prefix`·`layer0_center`, `search_context` → `iv_kvl_choice`, `layer0_center`는 `sctx.loop_conflicts` 속성만 읽는다.
- **재수출:** `search/__init__.py`가 `dc_prefix`를 재수출하면 `gmid_engine.search.dc_prefix`는 함수다. 관찰 지점이 아니어서 R1 같은 문제가 없다.

**E-5 계수 창: 새 자리에서도 성립.**
- `kernel.py:120`은 `counting`일 때만 열고 `:168`은 `window_open`이면 닫는다. `kernel.py` 변경 없음이라는 card 문장이 맞다. 이중 열기 `ValueError` 없음.
- `dc_prefix`는 `sctx.dc.lut.memo`를 쓰고 `_wire_sweep_memo` 뒤에 불리므로 같은 memo다.
- 창 안 키 ⊇ 첫 평가 키라는 1차 판단 그대로다. `dc_prefix` 실패로 창이 열린 채 남아도 첫 평가가 닫는다. 끝내 평가가 없으면 `find_front.py:122`가 `unfixed_no_kernel_eval`을 내며 예외는 없다.

**R1~R4 문언 자체.**
- **R1:** `sys.modules` 키는 모듈이 import돼 있으면 있다. `gmid_engine.search` import가 하위 모듈을 올린다. 같은 목록의 나머지 지점은 재수출 충돌 없음(1차 grep).
- **R2 M4:** 쓰기 계획 엣지 키가 'diode < 그 밖'이라 평행 셋 중 diode M1이 writer이고 M4는 `parallel_vgs`다(`writer_plan.py` 머리 3·6항, `theta_mirror`에 `ln_idu` M1). 손 값과 red 사유(gate 경로 없이 세면 `cut`)가 성립한다.
- **R2 M9:** gate·source가 둘 다 고정이라 `fixed_vgs`(같은 머리 6항), 비 writer, 좌표 = 자기 L 하나로 `cut`. g 값 재확인.
- **V10 toy:** 저항 엣지가 MOS보다 키가 작아 트리에 들어가 `dc_resistor_cycle`이 나지 않는다(같은 머리 3항과 정지 문장). 통과 전망이 1차 때보다 낫다. 실제 통과는 미측정.
- **R3:** Y `off`를 `region_decl`로 먼저 거르는 자리는 `dc_seal_region`이 이미 READS한다. H18 '`l_cells`에 항목 없음' = EO-1 interface :85. '다른 `cut` 변 호출 ≥ 1'은 test가 M9 꼴을 더하면 된다.
- **R4:** `failure` = `exc.record` 하나로 충분하다(`judge_rungs`가 부분 스냅샷을 안 쓴다).

**r1 뒤 L-4.** 빈 tuple이어도 §4 JSON이 내용 칸을 하나씩 정의해 reader가 있다. `graph.loop_stack_notes`·`device.dc_triode_region`의 `output_only_fields`와 출력 함수 둘은 L-2가 요구하므로 남는다. HC-D §2의 '나머지 칸 = 출력 전용'은 읽기 뜻의 표지이고 목록 등록을 말하지 않아 모순이 아니다.

**`gap_v` 한 자리.** `lhs_max` None이면 `stack_unsat` 안에서 None. 두 호출자에 산술이 없다. `holds` ⇔ `gap_v` > 0은 값이 있을 때만이고 `holds` 정의가 None 경우를 따로 적었다. 맞다.

## 4. 문서 표기

**40·41·42 본문 변경 0이라는 보고는 맞다.** diff 원문: 40·41은 `version`과 Status 줄 각 1쌍, 42는 `version` 1쌍과 판 안내 줄 1개 추가뿐이다(numstat 2/2, 2/2, 2/1). 41 §4.8-3은 HC-D §13 인계 행으로 남아 '병합 전 문서 card' 몫이다(spec 절차 줄). history 행 있음. 41:2116의 `dc_prefix` 언급은 '그 문서 §5.3·§6' 포인터라 낡지 않았다.

## 5. 미측정 표지: 어긋나면 어떻게 되는가

| 표지 | card 문언 | 어긋날 때 |
|---|---|---|
| 구조적 0 toy | 먼저 확인 | **정해짐**: '정지하면 멈추고 보고' |
| gate 넷 좌표 회로(M4) | test 작성 때 확인 | **안 적힘**(f2). 위 3의 근거로 어긋날 가능성은 낮다 |
| H19 배선(M9) | test 작성 때 확인 | **안 적힘**(f2). 근거는 같다 |
| `dc_current` 저항 부호 | 착수 때 base에서 확인 | **정해짐**: 정의 V_R = V(far) − V(near)로 환산하니 부호가 달라도 환산만 바뀐다. test는 감싸기로만 보므로 영향 없음 |

공통 브리핑의 멈춤 규칙이 있어 막지 않는다. 다만 test 작성 주체는 소스를 못 보므로 회로를 혼자 바꾸지 않게 한 문장을 둔다(f2).

## minor(막지 않음)

- **f1** §7 H5: 'F-7~F-9, **F-11**, `inspect.signature(f_exist)`…'.
- **f2** §7 머리에 추가: '미측정 표지 회로(§2.3 gate 넷 좌표·구조적 0 toy, H19 배선)가 불러들이기에서 정지하거나 손 값과 다르면 회로·기대값을 고치지 말고 멈추고 보고한다'.
- **f3** H11 나눔: `test_dc_prefix.py` = 같은 θ로 `dc_prefix` 두 번 `computes` 1 + `grafts` 1, `kernel_calls` 불변, 근 없음 칸 실패 재연 1. `test_iv_kvl_choice.py` = B1 평가의 graft, `context_fp` 불변. 같은 단언을 두 곳에 두지 않는다.
- **f4** HC-D §5.1 `route` 줄: '`on_structural`인 변에서 `cut`의 좌표는 그 소자의 L이다(L 동치류면 주인의 L)'.
- **f5** 다음 셋. §2.1 '저항 변은 정렬 첫 단자 → 둘째 단자로 걸으면 +1'을 't0 → t1로 걸으면 +1'로(같은 양에 두 표기, 손 값에는 영향 없음). §7 이름 규칙 접두에 `test_dc_prefix_` 추가. spec 재작성 표 `sizing/kernel_run.py`에 '앞부분 함수 공개 이름, `gmid_engine.sizing` 재수출'.

## 최종 재판정 미측정

pytest 전부, 규칙 L·구조 test 실행 결과, §2.3 두 회로·H19 회로의 실제 통과, 선행 card 코드 뒤 줄과 이름(`dc_columns`·`dc_widths` 앞부분 포함), 13회로 수치와 첫 판정 미측정 목록. 이 판정의 통과는 문서 정합의 판정이고 코드 동작의 판정이 아니다.

verdict: Major 0
