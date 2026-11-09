# reference 검토 g2 -- `references/stick-diagram-euler-layout.md` 대 새 엔진 MOD7·MOD8

- 작성 2026-10-07. 읽기 전용 검토(저장소·코드 변경 없음).
- 기준 문서(전문 정독, 1~1241행): `chip-design-skills/skills/analog-gmid-design/references/stick-diagram-euler-layout.md`(이하 **SE**).
- 대조 문서(약칭):
  - **M7** = `wt/_drafts/engine/design_mod7_layout.md`
  - **LC** = `gmid_engine/layout/CONTRACT.md`
  - **P** = 계획서 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(N3.17 LY1~LY7 829~835행, LR8 529행, DEC-79 278행, N3.6 455·458행)
  - **NR** = `NEW_ENGINE_DESIGN_REQUIREMENTS.md`
  - **LP** = `layout_pipeline_analysis.md`
  - **LCS** = `lut_coverage_study.md`
  - **TV** = `tol_v_measurement.md`
  - **M15** = `design_mod1_lut_mod5_mna.md`
  - **M3S** = `design_mod3_structure_u2_u5.md`
  - **M6** = `design_mod6_search_front.md`
  - **PUD** = `PENDING_USER_DECISIONS.md`
  - **UD** = `_drafts/user_decisions.md`(2026-10-07 항목)
- 대원칙 표기: [반복] 반복 계산 금지·필드 = 캐시, [분할] 기능별 파일 분할, [위상] topology 종속 금지, [상수] 상수 금지. reference 권고가 대원칙과 부딪히면 그 사실을 적었다.
- '추측' 표시가 없는 수치는 인용한 문서의 실측값이다.

---

## 1. 발견 목록

### G2-01 [높음] 보존할 양이 '총 W'가 아니라 '(ID, gm/ID, L)'이어야 한다 -- 폭 슬라이스와 W 보존 규칙의 모순 (결정 재검토)

- **reference**: SE 976~988행 §8.3 "gm/ID LUT는 보통 특정 기준폭(`W_ref`)에서 캘리브레이션 … 같은 총 W=80µm라도 finger_w=5µm에서는 46.2µA, finger_w=20µm에서는 38.7µA로 ~16% 차이 … 실제 finger_w에서 target ID를 내는 VGS(혹은 필요하면 총 W)를 … 다시 찾아야 한다."
- **새 엔진 쪽**: P LY1(829행) "sizing이 … 소자별 총 W를 유도하고 그 값이 정본이다. 레이아웃은 총 W를 허용오차 안에서 보존", M7 §0 L1(12행), §3 2(a)(156행) "err = |nf·fw − W|/W", M15 O4(252행) "첫 사이징점 finger_w 폭 키 = `w_ref_cap`(5 µm)".
- **유형**: 잘못된 알고리즘 + 결정 재검토.
- **내용**: MOD4는 첫 사이징점에서 5 µm 슬라이스 전류밀도 J로 W = ID/J를 계산한다(M15 O4). 그다음 MOD7이 다른 슬라이스 폭 fw를 고르면 같은 gm/ID에서 J(fw)/J(5 µm)이 nfet 기준 −28 %~+170 %로 달라진다(LCS 표 A). 이 경우 W를 보존하면 ID가 같은 비율로 틀어지는데, LY1 허용오차(G2-02)는 이 차이를 보지 못한다. M7 §5 (3)의 슬라이스 재평가가 W를 다시 고치면 W가 바뀌고, 바뀐 W 때문에 fw 선택이 다시 바뀌는 순환이 생긴다. 수렴은 보장되지 않고, 순환하면 NONCONVERGENT(cycle)로 끝난다. reference가 요구하는 불변량은 "실제 finger_w에서 target ID"다. 즉 물리적으로 보존해야 할 것은 전류와 동작점이고, W는 fw의 함수다.
- **보강안**:
  1. `layout/finger_candidates.py`가 슬라이스 fw마다 `W_need(fw) = ID / J_slice(kind, fw, gm/ID, L, VDS, VSB)`를 계산한다. 그 값으로 `nf = W_need/fw`를 내림·올림 두 경우 모두 구하고, 오차는 `err = |nf·fw − W_need(fw)| / W_need(fw)`로 잰다.
  2. `ly.fw_cand` 키 = (kind, ID, gm/ID, L, VDS, VSB, 슬라이스 지문). 이 값은 S2 봉인 op에서 읽는다. 매 반복 같은 키를 다시 계산하지 않으므로 [반복] 원칙을 지킨다.
  3. W_m(5 µm 기준)은 '참고 W'로만 기록한다.
  4. 같은 matching group의 멤버들은 같은 fw를 쓰므로 비율 오차가 0이다(LCS 표 B의 미러비 오차가 사라진다).
  5. 이렇게 하면 '레이아웃이 fw를 고름 → MOD8이 W를 다시 계산함 → 레이아웃이 다시 고름'으로 이어지는 바깥 순환이 한 번의 후보 생성으로 접힌다.
- **누가**: 사용자 결정 필요. LY1 '총 W 보존' 문구를 '(ID, gm/ID, L) 보존 + 실현 W = 슬라이스에서 계산'으로 바꾸는 일이다. 구현은 엔진 내부다.

### G2-02 [높음] LY1 허용오차가 '재검증 생략'의 면허가 된다 -- reference §5·§10은 모든 W·finger_w 조정 뒤 재검증을 요구한다 (결정 재검토)

- **reference**:
  - SE 735~746행 §5 "재검증은 … 체크리스트를 그대로 재실행", 1226~1229행 §10 "finger 수/W 조정 … 이 있었다면, 조정 후 W로 gm/ID 검증 체크리스트를 재실행했는가? … 재검증 없이 사이즈만 바꾸고 넘어간 항목이 있는가 — 있다면 안 된다".
  - SE 1230행 "재검증을 통과한 W를 freeze".
- **새 엔진 쪽**:
  - P LY1(829행)·N3.6(455행): 상한 = tol_V(ID 환산 지표 셀값) × gm/ID.
  - M7 §5 수렴 조건(190행): `W_requests` 비어 있음 + `W_err_rel ≤ W_tol_upper`.
  - PUD DF-3(338행): "총 W는 tol_V×(gm/ID) 안에서 보존되므로 엔진 W와 같은 값".
- **유형**: 결정 재검토 + 빠짐.
- **내용**: TV §2·§3에 따르면 ID 환산 지표 tol_V는 셀 중앙 31.5 mV, 최대 189 mV다. 이 값으로 상한을 계산하면 gm/ID 12에서 38 %(중앙), 227 %(최대)이고 gm/ID 20에서 63 %다. TV 4절 결론도 "W 보존 판정이 거의 아무것도 거부하지 않는다"이다. 이 범위 안의 실현 오차는 W_request를 내지 않으므로 MOD8 재평가가 일어나지 않는다. 반면 SPICE 넷리스트는 실현 기하(`w=finger_w m=n_fingers`, spice_oracle README 29~30행)로 만들어진다. 그 결과 엔진이 봉인한 S2(W_m, 5 µm 슬라이스)와 SPICE 회로가 수십 % 다른 소자가 된다. 합격 조건은 'free 모드 스펙 만족 + 전 MOS 포화'다(P 458행). 그런데 여유가 W_m 기준으로만 확인되어 있으므로 합격 시험이 직접 흔들린다. 추가로, 첫 레이아웃에서 W_request가 0이면 M7 §5 (3)의 슬라이스 재평가가 실행되는지가 문서상 불분명하다(추측: 실행되지 않는다).
- **보강안**:
  1. `convergence/loop.py`에서 MOD7 결과가 나오면 W_request 유무와 관계없이 실현 기하(nf, fw 슬라이스, 실현 W)를 S2 `layout` 필드에 쓰고 평가 커널을 실현 기하로 한 번 돌린다. 이것이 reference의 '재검증'이다. 바뀐 소자의 필드만 miss가 나므로 [반복] 원칙을 지킨다.
  2. 그 결과가 봉인·제약을 통과하면 freeze, 위반하면 W_request로 처리한다.
  3. 판정 기준은 LUT 오차가 아니라 제약 여유가 된다.
  4. LY1 tol은 '후보 순위 기준'으로만 남긴다. 기본안: 상한 = min(tol_V×gm/ID, 그 소자가 기여하는 활성 제약 여유를 감도로 환산한 값).
  5. DF-3 문장 "엔진 W와 같은 값"은 사실이 아니므로 정정한다.
- **누가**: 사용자 결정 필요(LY1 의미 변경). 재평가 배선은 엔진 내부다.

### G2-03 [높음] diode 연결 소자를 슬라이스 재평가에서 빼면 노드전압 정본이 틀린다 (reference 오래됨 + 결정 재검토)

- **reference**: SE 984~985행 "Diode-connected 소자(자기 게이트=드레인)는 SPICE가 스스로 그 finger_w에서 target 전류를 내는 VSG를 재계산해주므로 별도 보정이 필요 없다."
- **새 엔진 쪽**: P LY2(830행) "diode 연결 소자는 자기바이어스라 재보정하지 않는다", M7 §5 (3)(189행) "diode 연결 소자 제외", NR 287행 `self_biased_diode`.
- **유형**: reference 오류(옛 SPICE 중심 맥락) + 결정 재검토.
- **내용**: reference의 이 문장은 'SPICE에서 전류가 맞는다'는 뜻이다. 새 엔진은 노드전압을 정본으로 예측하는 엔진이다(GB7, 봉인 1·2·6·7, VDS−VDsat 포화 판정). diode의 fw가 5 µm가 아니면 같은 ID에서 VGS가 바뀐다(LCS 표 A의 J 차이를 VGS로 환산하면 수십 mV 규모, 추측). 그 gate 넷은 미러 출력·캐스코드 바이어스가 함께 쓰므로 그 소자들의 VDS·포화 여유와 헤드룸 판정이 틀어진다. 합격 조건 '전 MOS 포화'에 직접 닿는다.
- **보강안**: `convergence/loop.py`의 재평가 대상에서 diode 제외를 없앤다. 모든 소자를 자기 fw 슬라이스로 다시 평가한다(diode는 VGS = f(ID, 슬라이스), 출력 소자는 그 VGS에서 ID). `self_biased_diode` 필드는 'VGS를 자기 전류로 정함'이라는 계산 경로 표시로만 쓴다. reference §8.3에는 '엔진 노드전압 예측에는 해당 없음'이라는 주석 정정을 제안한다.
- **누가**: 사용자 결정 필요(LY2 문장 정정). 구현은 엔진 내부다.

### G2-04 [중간] 차동쌍 LY5 (ii) 단계가 `W_adjustable=false`(= 활성 제약 소자)에서 건너뛰어진다

- **reference**: SE 729~734행 §5 "입력 差동쌍 … 은 최후의 수단으로만 건드린다", 753~756행 FAIL 시 "(i) 다른 비-critical branch … (ii) gm/ID 재선택 … (iii) diffusion break".
- **새 엔진 쪽**:
  - NR 288행 `"W_adjustable": true // false = W_request 금지(활성 제약 소자) [제안]`.
  - M7 §3 2(d)(159행) "(iii) `W_adjustable=false`이거나 … 거부 … 면 interdigitation으로 완화".
  - P LY5(833행) "(i) nf 조정 (ii) W_request … 둘 다 불가능할 때만 완화".
- **유형**: 충돌(설계 대 사용자 결정) + 빠짐(출처 미정의).
- **내용**: 차동쌍은 대개 gain·GBW 활성 제약 소자다. `W_adjustable=false`이면 (ii)를 시도하지도 않고 곧바로 완화한다. 이는 사용자 결정의 "둘 다 불가능할 때만"과 어긋난다. 또 `W_adjustable`의 계산 주체·규칙이 어느 design에도 없다. reference의 critical 개념은 '재검증 없이 건드리면 위험'이라는 뜻이다. 새 엔진은 MOD8이 θ 재탐색을 포함해 전체를 재평가하므로(M7 §5 (1)) 사전 금지 플래그가 필요 없다. 실제로 막는 것은 재평가 결과(거부)다.
- **보강안**: `W_adjustable`을 계약에서 빼고, 모든 W_request를 MOD8 재평가가 판정하게 한다. 거부되면 M7 2(d)(iii)으로 간다. 꼭 둘 경우에는 'spec·ratify로 W가 고정된 소자'만 false로 하고 MOD4가 유도한다(선언·태그 금지 [위상]). T5 픽스처에 '활성 제약 차동쌍 + MOD8 수용' 경우를 더해 relaxed=false를 확인한다.
- **누가**: 엔진 내부(사용자 결정 LY5 문언을 지키는 방향).

### G2-05 [중간] 박스 개선에 finger_w 재선택(Case A)이 없다 -- 행 접기만 있다

- **reference**:
  - SE 943~953행 §8.1 "finger_w(unit cell)는 stack마다 달라도 된다 — 오히려 이 자유도가 §8의 실제 실행 수단".
  - SE 955~966행 §8.2 "나머지 stack마다 … 총 finger 수가 target에 가장 가까워지는 finger_w 후보를 탐색".
  - SE 679~725행 §4.2 Case A/B, 최종 결정은 숫자로.
- **새 엔진 쪽**:
  - M7 §3 3(161행) "매칭 그룹이 없는 소자는 … 행 finger 수 합이 가장 작은 공통 fw".
  - 2(c)(158행) 정렬 키 "행 폭 합 = Σnf·pitch(L)".
  - 5(163행) box FAIL이면 `apply_explicit_row_split`만 한다.
  - M7 §1 58행: `search_stack_finger_w`·`search_shared_finger_w` 복사 제외.
- **유형**: 빠짐.
- **내용**: 행마다 'finger 수 최소' = '가장 넓은 슬라이스'를 고르면 행들이 서로를 보지 않고 정해진다. 이후 박스 개선 수단은 접기 하나뿐이다. reference는 fw를 박스 맞춤의 주 수단으로 쓴다. 이 결과는 판정 축 면적(사용자 결정 12번 (나): front 점마다 floorplan 외곽 면적으로 비지배 재필터, P DEC-79)에 직접 들어가므로 front 순서에 영향을 준다.
- **보강안**:
  1. `layout/rows.py`의 박스 단계를 2단계로 나눈다. (a) 행마다 허용 후보 집합(`ly.fw_cand`, G2-01 방식)을 그대로 보관한다(이미 계산된 값이므로 [반복] 원칙에 맞는다). (b) 목표 행 폭 T를 '행 후보 폭들의 합집합'에서 차례로 고르고, 각 행에서 T에 가장 가까운 (fw, nf, 접기 수)를 고른다. 판정은 floorplan 외곽 면적(판정 축)이다. 이 과정이 reference Case A를 이산 슬라이스로 옮긴 것이다.
  2. 탐색 폭 = Σ행 후보 수(상한은 슬라이스 수 × 행 수, 상수 없음).
  3. Case B(공통 fw)는 같은 루프에서 T 대신 공통 fw를 고정한 경우로 포함한다.
- **누가**: 엔진 내부.

### G2-06 [중간] stage를 넘는 hub 병합(§4.1)이 행 그룹 유도에 없다

- **reference**:
  - SE 591~597행 §4 "stack 배정의 기준은 '같은 stage인가'가 아니라 '같은 극성 + 하나의 공유 net(hub) + 그 병합이 실제로 한붓그리기 되는가'".
  - SE 1185~1193행 §10 "stack_id를 배정하기 전에 `find_hub_merge_candidates()`를 회로 전체 … 에 대해 먼저 돌렸는가 … DON'T 병합 후보 탐색 자체를 생략하지 말 것".
- **새 엔진 쪽**: M7 §3 1(154행) "`row_groups`(MOD3 기둥 + matching 그룹에서 유도, (kind, body 넷)으로 먼저 분리)". `find_hub_merge_candidates`·`check_multi_leaf_hub_parity`는 복사 목록(M7 §1.1)에 없다.
- **유형**: 빠짐.
- **내용**: 기둥(전기 KVL 컬럼) + matching group으로만 행을 만들면 p.29 사례(1단 PMOS 부하 + 2단 PMOS gain 소자, hub = vdd)처럼 '같은 극성·같은 hub·matching 아님' 병합을 탐지하지 못한다. 행 수가 늘면 면적(판정 축)이 커진다. 반대로 병합할 때 Euler 실현성을 확인하는 단계도 없다(reference §4.1 '후보 발견 ≠ 실제로 가능').
- **보강안**:
  1. `layout/hub_merge.py`(새 파일, 진입점 1)를 둔다. (kind, body, hub 넷, hub가 source인지 drain인지)로 후보를 찾는다. 같은 hub라도 역할이 반대면 제외한다(SE 668~671행).
  2. leaf ≥ 3이면 패리티 공식(SE 637~649행: 홀수 finger leaf m ≥ 3이면 불가)으로 거른다. `check_multi_leaf_hub_parity`는 복사하고 해시를 고정한다.
  3. 병합안과 비병합안 모두 G2-05의 판정 축 면적으로 비교하고, 채택·거부 근거를 `LayoutResult`에 기록한다(reference §10 '확인 후 근거 있게 거부').
  4. 노이즈 결합 우려로 거부하는 기준은 회로 해석이므로 사용자 몫이다(기본안: 기록만).
- **누가**: 엔진 내부. 병합 거부 정책은 사용자 결정 필요.

### G2-07 [중간] 캐스코드 대칭쌍(stacked matching)이 matching group에 없고, 패턴 함수(hub-leaf 전용)로 배치할 길도 없다

- **reference**:
  - SE 290행 §2.6 표 "캐스코드 대칭쌍(folded cascode M5/M6, M7/M8, M9/M10 등) … 두 差동 branch의 출력 임피던스·극점 위치가 어긋나면 CMRR·PSRR 저하 … `find_stack_edges()`+`find_stacked_matching_candidates()` … '확정된 쌍 위에 대칭으로 얹혀 있다'는 구조적 근거".
  - SE 1182~1184행 §10 "캐스코드쌍 … 전부 식별했는가".
- **새 엔진 쪽**:
  - M3S 149행 matching 규칙: `matching_ratio`(같은 gate·source 묶음) / `matching_offset`(같은 비레일 source 2개). 캐스코드쌍은 source가 서로 달라 둘 다에 걸리지 않는다.
  - M7 §1 58행 `_branch_composite_pair` 제외("선언 축C·2-tuple 펼침").
- **유형**: 빠짐.
- **내용**: 파일럿 M2a/M2b·M3a/M3b, folded M5/M6·M7/M8 같은 쌍이 matching 레코드 없이 일반 행에 들어간다. LP §4 실측에서 옛 엔진은 M3 FAIL(dx=3.0)이었고, 새 엔진에서는 아예 판정 대상이 아니다. SPICE 합격(불일치 없음)에는 닿지 않는다. 하지만 CMRR·PSRR의 실칩 성능과 reference §10 DoD 미충족이다. `_branch_composite_pair`를 제외한 이유는 '선언 입력'이었는데, 개념 자체는 connectivity로 유도할 수 있다.
- **보강안**:
  1. `graph/matching_groups.py`에 role `stacked_pair`를 추가한다. 규칙: 확정 matching 쌍 (a, b)가 있고, 소자 c, d가 같은 kind·같은 gate 넷이며, c의 채널 단자가 a의 drain 넷, d의 채널 단자가 b의 drain 넷이면 (c, d)를 쌍으로 등록한다. 재귀로 상속한다. 증거는 `evidence{base_pair, shared_gate}`([위상] 원칙에 맞음).
  2. MOD7 `pattern_select.py`는 `stacked_pair`를 base 쌍의 배치 순서를 그대로 따르는 '복합 열'로 배치한다. 복사 금지 대상인 옛 함수 대신, base 쌍 패턴의 `transistor_sequence`를 이름 사상으로 옮겨 `check_walk_sequence`로 검산하는 새 코드를 쓴다.
  3. 실패하면 판정만 기록한다(LY6).
- **누가**: 회로 해석 성격의 규칙('얹힌 쌍도 matching 필요')이므로 사용자 확인 필요. 구현은 엔진 내부다.

### G2-08 [중간] Euler 막힘 해소에 'W를 보존하는 finger 패리티 전환'이 없고 곧바로 crossover로 간다

- **reference**:
  - SE 494~499행 §3 설계 레버 "(a) finger 수 조정으로 parity 전환 … 비-critical branch에서 이 조정을 우선 시도 … (b) diffusion break … (c) stack 재구성".
  - SE 643~649행 "leaf가 3개 이상일 때 k는 반드시 짝수".
- **새 엔진 쪽**: M7 §3 4(162행) "impossible이면 `find_min_crossover_layout`(W 불변, crossover 수 기록)". §3 2(c) 정렬 키에 Euler 실현성이 없다.
- **유형**: 빠짐.
- **내용**: 같은 W(또는 G2-01의 W_need)를 다른 슬라이스 fw로 실현하면 nf의 짝·홀이 바뀐다. 옛 방식(nf ±1, W 변경)과 달리 새 후보 집합 안에서는 총 W를 그대로 둔 채 패리티를 바꿀 수 있다. crossover는 diffusion break와 추가 metal을 뜻하므로 면적·기생 비용이 있다. 그런데 그 비용이 정렬 키에 없다.
- **보강안**:
  1. `layout/row_euler.py`가 막힌 행이면 그 행 소자들의 `ly.fw_cand` 후보 중 홀수 차수 노드를 줄이는 (fw, nf) 조합을 먼저 찾는다. 패리티는 공식으로 걸러 그래프 생성을 줄이고, 최종 채택 때만 `check_euler_condition`으로 확인한다(reference 649행).
  2. 조합이 없을 때만 crossover로 간다.
  3. pattern_select 정렬 키에서 crossover_count는 이미 2순위이므로, 위 패리티 후보를 같은 키로 비교하면 된다.
  4. 탐색 상한 = 행 소자 수 × 후보 수(상수 없음).
- **누가**: 엔진 내부.

### G2-09 [중간] 판정 축 면적(floorplan 외곽)에 well·tap·guard ring·dummy가 없다

- **reference**:
  - SE 1240~1241행 §10 "Well/substrate bias, I/O 연결 레이어 공간을 stick diagram 단계에서 미리 확보했는가 (PDF p.33, p.38)".
  - SE 378~380행 §2.7.1-3 "unit 하나하나를 독립적으로 guard-ring/dummy로 감싸면".
- **새 엔진 쪽**:
  - M7 §2 135행 `pack_floorplan_grouped`의 gap = "PDK 간격 규칙".
  - M6 197~198행 front 재필터 A_L = bbox_w·bbox_h.
  - P DEC-79(278행): 수동소자 미포함 명시 규칙만 있다.
- **유형**: 빠짐.
- **내용**: 판정 축 면적은 front 비지배 재필터의 정본이고, 동률 폭은 격자 한 칸이다(사용자 결정 12번). 그런데 탭·well 경계(다른 body 넷 그룹 사이 nwell 간격)·행 끝 dummy가 빠져 있다. 이것들은 행 수와 행 수에 비례한 고정비라서, 행 수가 다른 front 점 사이에서 순위를 뒤집을 수 있다(추측: 크기는 미측정).
- **보강안**:
  1. `core/pdk_decl.py`에 tap 폭·nwell 간격·nwell 여유·poly 끝 dummy 폭을 출처 규칙 번호와 함께 선언한다([상수] 원칙에 맞음).
  2. `layout/floorplan.py`가 행마다 '행 끝 dummy 2개 + 그룹 경계 tap'을 더하고, body 넷이 다른 그룹 사이는 well 간격을 gap으로 둔다.
  3. front 표에 '포함 항목' 열을 둔다(DEC-79 수동소자 표기와 같은 방식).
  4. dummy 수·tap 방식은 방법론 선택이다.
- **누가**: 사용자 결정 필요(dummy·tap 포함 여부). 구현은 엔진 내부다.

### G2-10 [중간] 박스 허용 비 선언이 spec 형식에 없다 -- 판정 축 면적으로 대체를 제안한다

- **reference**: SE 1048~1056행 §8.5 "비율 임계값(보통 1.5)", SE 921~936행 `check_box_shape(rows, row_width_tol=1.5 …)`.
- **새 엔진 쪽**:
  - M7 §2.3(148행) "허용 비 = 사람 선언(회로 spec 레이아웃 기준 -- D5 형식에 항목 추가, 없으면 로드 거부)".
  - M7 §8-1(237행).
  - `design_spec_format.md`에는 박스 기준 항목이 없다(grep 0건. 판정 축은 98·113·167행의 floorplan 외곽 면적뿐).
- **유형**: 충돌(design 사이) + reference 상수.
- **내용**: 이대로 구현하면 9회로 spec에 항목이 없으므로 MOD7 로드가 전부 거부된다. reference의 1.5는 상수다([상수] 원칙과 충돌). reference가 박스를 요구하는 목적은 floorplan 효율이다(SE 938~941행). 사용자 결정 12번으로 floorplan 외곽 면적이 이미 판정 축이므로 박스 비는 그 대리 지표다.
- **보강안**: `layout/box_shape.py`의 판정을 '행 폭 비 ≤ 선언값'에서 'floorplan 외곽 면적과 packing 밀도를 보고'로 바꾼다. 박스 개선 루프(M7 §3 5, G2-05)의 목적함수를 판정 축 면적으로 둔다. 행 폭 비는 기록만 한다. 그러면 spec 항목 추가가 필요 없다. 'ㄱ자 셀' 같은 극단 형상은 외곽 bbox 면적이 자동으로 벌한다.
- **누가**: 엔진 내부(기본안). 박스 비를 하드 게이트로 남기려면 사용자 결정이 필요하다.

### G2-11 [중간] finger_quantization W_request가 거부되면 갈 곳이 없다 -- reference §5 FAIL 사다리가 빠졌다

- **reference**: SE 753~756행 "FAIL → (i) … 다른 비-critical branch로 조정 대상 변경 (ii) … gm/ID(qF) 재선택 … (iii) 그래도 … diffusion break(면적 비용 감수)로 후퇴".
- **새 엔진 쪽**: M7 §3 3(161행) "어떤 fw로도 상한을 못 지키면 … `W_request{reason="finger_quantization"}`". §5(189행)에서 거부는 '3단계 2(d)(iii)'(차동쌍 완화)로만 연결된다. `W_new` 계산 규칙도 없다.
- **유형**: 빠짐.
- **보강안**:
  1. `W_new` = 그 소자의 실현 가능한 격자 {nf·fw | fw ∈ 슬라이스, G2-01이면 W_need(fw)}에서 W에 가장 가까운 두 값(위·아래)으로 정한다. 둘 다 요청하고 MOD8이 먼저 통과하는 쪽을 채택한다.
  2. 둘 다 거부되면 MOD8이 '그 소자를 W 고정 대신 실현 격자 값 집합 제약'으로 θ를 재탐색한다(reference (ii) gm/ID 재선택에 해당).
  3. 그래도 실패하면 그 front 점을 `removed{reason: layout_unrealizable, device}`로 기록한다(조용한 무효 금지).
  4. 반복 상한은 기존 K_max 규칙이다.
- **누가**: 엔진 내부.

### G2-12 [중간] 매칭 멤버의 L 동일성을 레이아웃이 확인하지 않는다

- **reference**: SE 335~338행 §2.7 "두 소자가 정확히 같은 unit geometry·같은 orientation을 갖도록", 365~368행 "W/L 반올림, contact 배치, edge 효과가 … 완전히 동일".
- **새 엔진 쪽**:
  - M7 §3 2(a)(156행)은 "매칭 멤버는 같은 finger_w"만 요구한다.
  - M3S 149행 `l_class` 엣지는 status `proposed`다(강제 아님).
  - P LR8 "매칭 그룹이면 LR2가 우선".
- **유형**: 빠짐(확인 장치).
- **보강안**: `layout/pattern_select.py`가 그룹 멤버의 L이 모두 같은지 확인한다. 다르면 패턴을 적용하지 않고 `ok=false, reason="matching_L_mismatch"`를 기록한다(LY6 전 그룹 판정). L 통일 자체는 LR2(MOD4) 소관이므로 레이아웃은 바꾸지 않는다.
- **누가**: 엔진 내부.

### G2-13 [낮음] 축대칭 검증(`check_mirror_symmetry`)과 홀수 개수 분할(`find_interleaved_symmetric_splits`)이 복사·사용 목록에 없다

- **reference**: SE 175~179행 §2.5.3 `check_mirror_symmetry(sequence, pair_map)`, SE 215~223행 §2.5.4, SE 1221~1225행 §10 "실제로 대칭(`check_mirror_symmetry()`)과 매칭 품질(가장 고르게 섞인 후보)을 둘 다 만족하는지 확인".
- **새 엔진 쪽**: M7 §1.1 복사 표(`build_mirror_symmetric_pattern`만 있다). 그룹 판정 지표는 residual·isolated_pairs·crossover뿐이다.
- **유형**: 빠짐(reference DoD 항목).
- **보강안**: `check_mirror_symmetry`를 `mirror_trail.py`에 복사한다(해시 고정). `ly.group` 결과에 `axis_symmetric: bool`을 더한다. `interdigitate_layout` search 경로 결과에도 적용한다. 홀수 분할은 `common_centroid_layout` search 경로가 대신 처리하므로 복사하지 않고 기록만 한다.
- **누가**: 엔진 내부.

### G2-14 [낮음] 박스 FAIL을 받아들일 때 '필요 행 수' 계산 기록이 없다

- **reference**: SE 1048~1056행 §8.5 "`ceil(문제_stack의_총_핑거수 / (다른_극성_최대_행폭 × max_ratio))` … 그 계산 결과 숫자를 결정 추적에 남겨야".
- **새 엔진 쪽**: M7 §3 5(163행) "개선 없으면 정지 … 그래도 FAIL이면 FAIL을 결과에 남긴다".
- **유형**: 빠짐(보고).
- **보강안**: G2-10을 채택하면 기준이 면적이 되므로 '접기 수별 외곽 면적 곡선(시도한 n_rows와 면적)'을 `LayoutResult.box.attempts`에 남긴다. 루프가 이미 계산한 값이므로 [반복] 원칙에 맞고 추가 비용이 없다.
- **누가**: 엔진 내부.

### G2-15 [낮음] reference의 출판 정답 사례가 test 오라클에 없다

- **reference**: SE 811~829행 §6.1 Maloberti p.37 정답 4행 node 시퀀스와 홀수 노드(top ['2','5'] path, mid A·B circuit, bottom ['3','6'] path), SE 836~851행 13소자 넷 표, SE 905~911행 §7 2단 OTA 3 stack 전부 closed circuit.
- **새 엔진 쪽**: M7 §6 T1~T15는 옛 엔진 실측(LP)·손계산·PDF 표만 쓴다. LC 1절 6은 SD 대조(같은 코드 = 같은 결함 공유)다.
- **유형**: 빠짐(test).
- **보강안**: `tests/layout/test_row_euler.py`에 SE §6.1 넷 표와 §7 넷으로 `row_euler`를 돌려 홀수 노드 집합과 kind를 출판 정답과 비교한다. SD와 독립인 외부 오라클이다(작성자 ≠ 검증자 원칙).
- **누가**: 엔진 내부.

### G2-16 [낮음, 추측] finger 패리티(확산 공유)와 SPICE 접합 용량 표현이 맞지 않는다

- **reference**: SE 66~73행 §2 "finger 수가 짝수면 strip의 양 끝이 같은 타입".
- **새 엔진 쪽**: spice_oracle README 98~99행 "`w=finger_w`, `m=n_fingers` … `ad=as=ad_per_w_m*finger_w`". M15 110행 "접합 용량(cdb·csb)은 LUT에 없어 MOD5가 별도 열로 보고".
- **유형**: 빠짐(추측: 크기 미측정).
- **내용**: `m=nf` 복제는 finger마다 S·D 확산을 따로 세므로, 실제 공유 확산(nf+1개, 짝수 nf면 drain이 안쪽) 대비 Cdb·Csb를 최대 약 2배로 잡는다. PM이 고임피던스 노드 극점에 민감한 회로에서는 SPICE와 엔진 사이에 차이가 생기고, 그 차이가 레이아웃 실제값과도 다르다.
- **보강안**: MOD7 `LayoutResult`에 소자별 (nf, 패리티, 행 끝 위치)에서 계산한 유효 AD/AS/PD/PS를 더한다. spice_oracle은 m 대신 이 값을 쓰는 선택을 둔다. 다만 LCS 표 E 때문에 nf 인스턴스는 금지이므로 m 유지 + 소자당 ad/as 조정이다. MOD5 접합 용량 열과 연결한다.
- **누가**: 엔진 내부(측정 먼저).

### G2-17 [중간] reference §8.2~§8.4의 연속 finger_w 탐색과 사례 수치는 E5 이후 오래된 내용이다 (reference 오류)

- **reference**:
  - SE 955~966행 `search_stack_finger_w`가 임의 실수 finger_w(예: 19.6 µm, 1.9 µm)를 고른다.
  - SE 991~996행 "finger_w≈19.6µm … fT 스펙 오차는 0.44%→0.52%로 사실상 그대로".
  - SE 1018~1019행 "sky130 실측 관찰로는 대략 수십 µm 이내가 안전".
  - SE 463~468행 Walker 사례 "세 finger_w 전부 … 스냅 오차 0%".
- **근거(실측·다른 문서)**:
  - LCS 표 A·L: nfet은 W 10·20·40 µm에서 같은 gm/ID의 ID/W가 +5~+171 %, 넓은 쪽 극한 +17~+35 %다. 19.6 µm 사례의 '스펙 유지'는 SPICE 이분탐색으로 VGS를 다시 맞춘 결과다(SE 994~995행). 새 합격 정의인 free 모드 + 엔진 예측에서는 성립하지 않는다.
  - '수십 µm 안전'의 실제 경계는 모델 bin wmax 100 µm다(LCS 16~17행: W 경계 … 7.0, 100). 156.8 µm 실패는 bin 밖이라서 생긴 것이다. 정확도 경계는 그보다 훨씬 좁은 슬라이스 집합(최대 7 µm, M15 55행)이다.
- **새 엔진 쪽**: M7 L9·E5(슬라이스만 쓰고 보간하지 않음)는 이미 올바른 방향이다.
- **유형**: reference 오류·오래됨.
- **보강안**: reference §8.2~§8.4에 'E5(2026-10-07) 이후 finger_w 후보 = PDK 특성화 폭 슬라이스. 연속 탐색 사례는 SPICE VGS 재보정 전제의 옛 사례'라는 정정 주석을 단다. §8.4 '안전 상한'은 '모델 bin wmax(모델 파일에서 파싱)와 슬라이스 최대 폭'으로 바꾼다. 새 엔진에는 영향이 없다(이미 반영됨).
- **누가**: 엔진 내부(문서 정정).

### G2-18 [낮음] reference 안의 서술 충돌과 낡은 경로

- SE 967행 §8.2 5단계 "`check_box_shape({행_이름: 실제_finger_개수, ...})`"(finger 개수)는 SE 921~936행 §8 머리 "n_fingers(finger 개수)만 비교 … 함정 … 재설계 이후 물리 행 길이"와 모순된다. 5단계 문장이 재설계 전 서술로 남아 있다.
- SE 1058~1073행 §9 `from stick_diagram import …`와 'assets/stick_diagram.py'는 현재 `legacy/stick_diagram.py`(M7 5행)다. `render_stick_diagram` 삭제 주석만 갱신되어 있다.
- SE 143~155행 §2.5.2 CC 표에는 PDF p.19 3·4열(3행·4행 배열)이 빠져 있다(M7 §7 228행 원문 대조 결과).
- **유형**: reference 오류(낮음). **보강안**: 문서 정정 3건. **누가**: 엔진 내부.

### G2-19 [낮음] design 사이의 재사용 방식 충돌(복사 대 import)

- PUD DF-14(349행) "복사가 아니라 import 재사용"과 P LY4(832행)·M7 L10(21행)·NR 148행 "본문 복사 + AST 해시"가 서로 반대다. LC는 복사로 이미 구현했다(LC 0절).
- **유형**: 충돌(reference 외. 대조 중 발견). **보강안**: PUD DF-14를 LY4(복사)로 정정하고 이력은 history에 남긴다. **누가**: 엔진 내부(문서 정정).

### G2-20 [낮음] 단순 미러는 '1행 자연 Euler trail'로 충분하다는 reference 기준이 선택 기준에 없다

- **reference**: SE 402~405행 §2.7.2 표 "단순 전류거울, 바이어스 회로 → 1행, 진짜 오일러 trail 그대로 … 면적 효율적이고 배선이 간단", "차동쌍, DAC/ADC … 정밀도가 특히 중요한 경우 → N행".
- **새 엔진 쪽**: P LY4(832행)·M7 §3 2(b)(157행) "그 밖 → common-centroid와 interdigitation 둘 다", 정렬 키는 (method, crossover, isolated, residual, 행 폭 합, err) 순이다.
- **유형**: 결정 재검토(경미).
- **내용**: 정렬 키 1순위 'method가 표·회전이면 0'은 7멤버 미러에 대해 회전 경로 N = 7행을 고르게 만든다(SE 390~395행 기본 N행). 면적 축에서는 손해일 수 있다. 사용자 결정 "그 밖 = 둘 중 선택(box·면적·residual)"과 정렬 키의 우선순위(method 먼저, 면적 나중)가 어긋난다.
- **보강안**: 비차동 그룹의 정렬 키를 (crossover_count, 판정 축 면적 기여, residual) 순으로 둔다. method는 기록만 한다. 사용자 결정 문언(box·면적·residual)과 같은 순서다.
- **누가**: 엔진 내부(사용자 결정 문언 안).

### 참고(문제 없음 확인)

- §3.6 kind 혼합 금지는 `build_graph` 복사와 (kind, body) 행 분리(LR8)로 반영되어 있다.
- §3.7 n_fingers=1 게이트의 한계는 새 엔진이 finger 확정 뒤 판정하므로 해소된다.
- §9.5 기하·전기 루프 분리는 LY7과 NR test `test_layout_retry_no_electrical_recompute`로 반영되어 있다.
- §2.6 M57/M58 오탐(gate만 같고 source가 다름)은 M3S `gs_groups`(gate+source)로 막힌다.
- §2.5.6·§2.7 hub-leaf 한계는 복사 함수 안 crossover 폴백이 처리한다.
- §8.4 PDK 폭 거부는 E5 슬라이스로 원천 차단된다.

---

## 2. 요약표

| 심각도 | 개수 | ID |
|---|---|---|
| 높음 | 3 | G2-01, G2-02, G2-03 |
| 중간 | 10 | G2-04, G2-05, G2-06, G2-07, G2-08, G2-09, G2-10, G2-11, G2-12, G2-17 |
| 낮음 | 7 | G2-13, G2-14, G2-15, G2-16(추측), G2-18, G2-19, G2-20 |
| 합계 | 20 | |

유형별 개수:

| 유형 | 개수 | ID |
|---|---|---|
| 빠짐 | 11 | 05·06·07·08·09·11·12·13·14·15·16 |
| 결정 재검토 | 5 | 01·02·03·04·20 |
| reference 오류·오래됨 | 3 | 03(일부)·17·18 |
| 충돌 | 2 | 10·19 |

사용자 결정이 필요한 항목은 01·02·03(LY1·LY2 문언), 06(병합 거부 정책), 07(캐스코드쌍 matching 해석), 09(dummy·tap 포함)이다.

## 3. 상위 5개 권고

1. **G2-01 + G2-02 (LY1 재정의)**: '총 W 보존'을 '(ID, gm/ID, L) 보존, 실현 W = 슬라이스 fw에서 계산한 W_need(fw)'로 바꾼다. 레이아웃 결과는 W_request 유무와 관계없이 실현 기하(슬라이스·nf)로 평가 커널을 한 번 다시 돌린 뒤 freeze한다(바뀐 소자 필드만 miss). tol_V×gm/ID(셀 중앙에서 gm/ID 12일 때 38 %)는 재검증 생략 기준이 될 수 없다. 사용자 결정이 필요하다.
2. **G2-03 (LY2 diode 예외 삭제)**: 노드전압 정본 엔진에서는 diode 소자도 자기 fw 슬라이스로 VGS를 다시 계산해야 '전 MOS 포화' 예측이 맞다. reference §8.3 문장은 SPICE 맥락의 옛 서술이다. 사용자 결정이 필요하다.
3. **G2-05 + G2-10 (박스를 판정 축 면적으로)**: 행별 fw 후보를 보관하고, 목표 행 폭을 맞추는 이산 Case A 탐색과 접기를 판정 축(floorplan 외곽 면적)으로 고른다. spec에 없는 박스 비 선언(로드 거부 위험, [상수] 원칙 위반)은 기록 지표로 낮춘다.
4. **G2-04 + G2-11 (W_request 경로 완결)**: `W_adjustable`(활성 제약이면 false)이 차동쌍 LY5 (ii)를 건너뛰게 하는 문제를 없애고, MOD8 재평가가 판정하게 한다. finger_quantization 거부 뒤의 사다리(실현 격자 두 값 → 격자 제약 θ 재탐색 → 이유를 남긴 front 점 제거)를 정한다.
5. **G2-06 + G2-07 + G2-08 (reference DoD 빠진 단계)**: stage를 넘는 hub 병합 탐지와 패리티 선별, connectivity로 유도한 캐스코드 stacked_pair matching, crossover 전 W를 보존하는 패리티 전환 후보를 MOD3·MOD7에 넣는다. 캐스코드쌍 해석과 병합 거부 정책은 사용자 확인이 필요하다.
