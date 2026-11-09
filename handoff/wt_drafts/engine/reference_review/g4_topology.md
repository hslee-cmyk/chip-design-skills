# reference 검토 G4 -- topology 추출·진단·보상 함수 유도·analog grammar·함수 선택

- 작성 2026-10-07. 읽기 전용 검토(코드·저장소 수정 없음).
- 사용자 지시(2026-10-07): "reference 문서를 기준으로 모든 결정을 다시 살펴. 문서를 정독하고 빠진 부분, 잘못된 알고리즘을 찾아서 보강해."
- 정독한 reference(처음부터 끝까지): `skills/analog-gmid-design/references/`
  - TEC = `topology-extraction-checklist.md`(141행)
  - TBD = `topology-behavior-diagnosis-workflow.md`(149행)
  - TFD = `topology-fn-derivation-guide.md`(195행)
  - AGI = `analog-grammar-integration.md`(554행)
  - FSM = `function-selection-map.md`(193행)
- 대조 대상(약칭):
  - UD = `wt/_drafts/user_decisions.md` 2026-10-07 항목
  - REQ = `wt/_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md`(끝 '확정 사항' 우선)
  - U25 = `design_mod3_structure_u2_u5.md`, S1D = `design_mod3_s1_graph.md`, M7 = `design_mod7_layout.md`, M15 = `design_mod1_lut_mod5_mna.md`, M6 = `design_mod6_search_front.md`, SPF = `design_spec_format.md`, RM = `ROADMAP.md`, PUD = `PENDING_USER_DECISIONS.md`, LP = `layout_pipeline_analysis.md`
  - P = `chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(1281행판)
  - 계약: `gmid_engine/graph/CONTRACT.md`(GC), `gmid_engine/authoring/CONTRACT.md`(AC), `tools/spice_oracle/README.md`(OR)
- 실측(이번 검토에서 직접 잰 것): library 9회로 topology JSON에서 gate 전용 넷과 ports 선언 대조(G4-08), 파일럿 `Vbias4` 연결(G4-14), authoring 코드의 넷 이름 대소문자 검사 유무(G4-09), 계획서·엔진 초안의 준정적 검사 유무(G4-10). 실측이 아닌 추론은 **[추측]**으로 표시했다.
- 문제 유형: 빠짐 / 잘못 / 충돌 / reference 오류 / 결정 재검토. 심각도: 높음 = 합격 시험·정확도에 직접 영향, 중간, 낮음.

---

## 0. 요약 판단

1. **보상(GB5)은 새 엔진에서 가장 큰 빈칸이다.** 계획은 "극점·영점 식을 극점 노드 목록과 MNA에서 조립하는 규칙 하나"(P 496)라고만 적었다. gm 요구량 `gm_req`과 보상 수동소자 값을 어떻게 계산하는지는 어느 초안에도 없다(M6 155행은 `gm_req`를 쓰기만 한다. RM D4 design은 아직 없다). reference TFD §3은 회로별 닫힌 근사식(NMCNR Eq10/11)이 PM 60~90° 전 구간에서 GBW를 2.5~21배 틀리게 예측한다는 것을 이미 실측해 두었다. 그래서 일반 규칙이 극점·영점 **근사식**에서 제약을 만들면 nmcnr·ngcc 합격 시험이 흔들린다(G4-01, G4-02).
2. **matching 유도에서 캐스코드 대칭쌍(M2a/M2b류)이 빠진다.** AGI §6.3은 이 공백을 이미 발견했고 해결책(확정된 쌍 위로 stack을 따라 전파하는 방식)까지 실측으로 검증해 두었다. 새 엔진 U4 규칙(gs 묶음 + 공통 비레일 source)은 바로 이 공백을 다시 만든다. MOD7의 패턴 함수도 hub-leaf 전용이라 이 쌍을 배치할 경로가 없다(G4-03, G4-05).
3. **TEC·TBD의 "입력 netlist 자체를 먼저 의심하라"는 요구가 새 엔진에는 구조로 들어가 있지 않다.** gate 전용 넷은 선언 없이 외부 바이어스(교류접지)로 자동 분류된다. 넷 이름의 대소문자 충돌은 엔진이 받아들이고 오라클은 막는다. 오라클 netlist와 topology 사이의 연결 동일성 검사도 없다(G4-08, G4-09, G4-12).
4. reference 쪽의 문제도 있다. TFD·FSM은 회로별 보상 함수(`miller_ota_topology` 등)를 쓰라고 권한다. 이것은 대원칙 3(topology 종속 엔진 금지)과 정면으로 충돌하고, AGI의 이름 힌트 폴백도 같은 원칙과 충돌한다. reference를 고치지 않으면 다음 AI가 회로별 함수를 다시 만든다(G4-15, G4-17).

---

## 1. 발견 목록

### G4-01 GB5 보상 일반 규칙의 계산 방법이 정의되지 않았다 -- 근사식 기반이면 틀린다

- **reference**:
  - TFD 114~138행: "Eq10/11이 전제하는 '우세극이 나머지 극점들과 충분히 떨어져 있다'는 근사 자체가 ... PM_target 범위(60~90도) 전체에서 사실상 항상 깨져 있다". 실측은 "GBW≈5.45MHz(6.7배)/PM≈124.6도(+54.6도)"이고, "PM_target을 61도~140도까지 스윕해도 GBW 비율은 21.4배(61도)에서 ... 90도 근처에서도 여전히 2.5~3배"였다.
  - TFD 140~145행: R→∞ 극한에서는 PM이 목표보다 높고, 유한 R 실측에서는 70°→48.32°로 낮다. 두 오차가 "서로 다른 방향으로 작용한다".
  - FSM 55행: "근사식(Eq 10/11)이 아니라 정확한 4-노드 전달함수 -- 사이징 후 반드시 호출".
  - FSM 59행·TFD 4절: NGCC 보상소자 실값은 "아직 전용 함수 없음".
- **새 엔진 쪽**:
  - P N3.7 '보상 규칙(GB5)' 496행: "보상 해법은 극점·영점 식을 극점 노드 목록과 MNA에서 조립하는 규칙 하나".
  - M15 3.5절: GB5는 "θ 제약(gm 요구량·수동소자 값·기생 극점 L 상한)을 낸다".
  - M6 155행: 제약 `gm_i ≥ gm_req`가 있지만 `gm_req`의 정의는 어디에도 없다.
  - RM 141행: D4 `7b-compensation-allocation` design은 아직 작성되지 않았다. RM 282행: "GB5 일반 규칙(K7)은 마일스톤에 필요 없다".
- **유형**: 빠짐(알고리즘 부재)과 잘못(근사식으로 채울 위험).
- **심각도**: 높음. nmcnr(GBW 816 kHz, CL 100 pF ∥ 25 kΩ, PM 70°)와 ngcc(feedforward, DEC-81 복합 블록)의 SPICE 합격이 이 규칙에 직접 걸린다.
- **보강안**(MOD5 `metrics/compensation.py`, D4 design):
  1. **판정과 값 결정 모두 정확한 MNA로 한다.** 보상 수동소자 값(Cc, Cm1, Cm2 등)은 연속 θ 성분으로 둔다(GB6 외층 SLSQP 변수). GBW·PM 제약은 봉인 스냅샷 `ss` 위의 전회로 MNA(`mna_solve`)에서 잰 `ugf_ss_hz`·`pm_ss_deg`로 판정한다. 이미 계획의 판정 위치(DEC-74)와 같으므로 `gm_req`를 닫힌식으로 따로 만들 필요가 없다. `gm_req`가 꼭 필요하면 "다른 θ를 고정했을 때 MNA 제약을 만족하는 최소 gm_i"를 1-D 근 찾기로 정의한다(같은 스냅샷 MNA 재사용, 조립 1회).
  2. **극점·영점 근사식은 시작점 생성기로만 쓴다.** pole-splitting·Butterworth 배치 같은 식은 층 0 조립점의 초기 Cc·gm 추정에만 쓴다. 결과에는 근사 예측과 MNA 값의 차를 `comp_approx_gap`으로 기록한다(TFD 3절 실측 사례를 재발 감지 test로).
  3. **test 오라클**: TFD 2~4절의 원문 닫힌식은 회로별 함수로 이식하지 않는다. 대신 이상 VCCS 손계산 회로에 넣어 MNA 결과와 비교하는 대조 test 기대값으로 쓴다. 근사가 유효한 영역에서만 쓰고, 유효 영역 밖(NMCNR PM 60~90°)에서는 "근사 ≠ MNA"가 기대값이다. NGCC는 Lee et al. Table 4(k=4, GB=10 MHz, CL=10 pF, α=0.3, gm1=0.105 mS, gm2=0.186 mS)를 **검증 오라클로만** 쓴다. 메모리 원칙 '논문 값을 설계값으로 쓰지 않음'을 지키기 위해 설계 입력으로 넣지 않는다.
  4. feedforward(ngcc gmf1/gmf2)가 만드는 LHP 영점은 근사식 경로로 처리하지 않는다. 정확한 MNA는 feedforward를 자동으로 포함하므로 1번 방식이면 따로 분기할 필요가 없다. 근사식 경로를 택하면 이 구성은 `기록만` 분기가 되어 ngcc가 정지한다(DEC-59).
- **결정 주체**: **사용자 결정 필요**(방법론 선택: 근사식 조립 대 정확한 MNA 제약). 기본안은 1번이다. 근사식 경로는 계획 문구 "극점·영점 식 조립"의 한 해석일 뿐이고, reference 실측이 그 해석을 반박한다.

### G4-02 영점 상쇄 저항(Rz·Rm)의 기준 소자를 일반 규칙으로 정하는 방법이 없다

- **reference**:
  - FSM 58행: "Miller OTA의 nulling resistor Rz 실값 ... `1/gms[1]`(=1/gm2)".
  - TFD 84행: "Rm = 1/gm3 (본문, Structure 4 조건)".
  - 두 식은 회로별로 '어느 gm인지'를 사람이 지정한 것이다.
- **새 엔진 쪽**:
  - M15 3.5절: "영 상쇄 저항 `Rz = 1/gm_ref`류 종속 값은 `ss.passive` 필드로 쓰고 입력 버전 = 기준 소자 `ss` 버전". 그런데 `gm_ref`를 어떻게 고르는지는 없다.
  - SPF 196행: "Rz1·Rz2 `engine` ... 확인(옛 Rz=1/gm 규칙)".
  - AC 126행: topology 의 `nulling_reference_device` 키는 "허용하되 읽지 않는다". 회로별 선언을 엔진이 쓰지 않으므로 구조 유도 규칙이 필요하다.
- **유형**: 빠짐.
- **심각도**: 높음. 파일럿 Rz1·Rz2, two_stage Rz, nmcnr Rm 세 회로의 보상망 값이 이 규칙에 걸린다. 선택이 틀리면 RHP 영점이 남아 PM이 떨어진다.
- **보강안**(`metrics/compensation.py` + S1v):
  - (a) 구조 규칙(기본안): 보상 루프(N3.2-2 (2) Miller형)의 '수동소자만의 극대 구간'에서 저항의 한쪽 끝 넷 b를 본다. b를 출력노드로 갖고 gate가 그 루프의 반대쪽 끝 넷 a 쪽 신호 경로 위에 있는 CS 셀 집합 S를 찾는다. 이때 `R = 1/Σ_{c∈S} gm_c`가 순방향 영점(gm/C)을 상쇄하는 조건이다. 2단 Miller(S = 2단 CS)와 NMCNR Structure 4(S = 출력단 gm3)가 같은 규칙으로 나오는지를 손계산 대조 test로 확인한다.
  - (b) 대안: R을 θ 연속 변수로 두고 G4-01의 MNA PM 제약에 맡긴다. 규칙이 필요 없지만 탐색 차원이 1~2개 는다.
  - 어느 쪽이든 S 판정 결과(회로별 소자 목록)는 J7(Cc–Rz 직렬 루프, P 1125)에서 ratify한다.
- **결정 주체**: 규칙 (a)/(b) 선택은 **사용자**(방법론). 회로별 S 결과는 **사용자 J7 ratify**. 기본안은 (a)이고 (b)를 폴백으로 둔다.

### G4-03 캐스코드 대칭쌍(branch_symmetric)이 matching 유도에서 빠진다

- **reference**:
  - AGI 266~310행(§6.3): "`m_mirror()`의 `(G,S,type)` 그룹핑은 source가 다르면 애초에 다른 그룹으로 갈라놓으므로, **이 재설계 이후 `M2a`/`M2b`는 current_mirror 후보로도, ... 어떤 기존 idiom으로도 전혀 안 잡힌다**". 해결은 "선택지 4 ... 이미 확정/발견된 매칭쌍 위에 직접 stacked된 소자쌍"이고, 실측으로 `{M2a,M2b}`·`{M3a,M3b}` 재현과 M57/M58 비유입을 확인했다(AGI 303~309).
  - FSM 67행: 캐스코드 대칭쌍은 `find_stack_edges` + `find_stacked_matching_candidates`로 찾는다.
  - FSM 134행: "3번째 kind `branch_symmetric` ... **common-centroid(3c)는 diff_pair와 같이 필수 게이트**다 ... solo는 dy=1.00으로 FAIL".
- **새 엔진 쪽**:
  - U25 3.2절 `rel_matching`: matching_ratio = "gate 가 레일이 아닌 `gs_groups` 묶음", matching_offset = "같은 kind, 같은 비레일 source 넷, gate가 서로 다른 MOS가 정확히 2개". 같은 gate·다른 source·다른 drain 쌍은 어느 쪽에도 들지 않는다.
  - M7 L8: matching 그룹 = `graph/matching_groups.py` 출력(아직 design 없음). LP 165행에는 role `cascode_pair`가 적혀 있지만 유도 규칙은 없다.
  - M7 1절 패턴 함수(`common_centroid_layout`·`interdigitate_layout`)는 "전부 같은 `source`=hub 공유"(FSM 100·102행)를 입력 전제로 둔다. 공유 노드가 없는 캐스코드 쌍에는 적용할 수 없다.
- **유형**: 빠짐(reference가 이미 찾고 고친 회귀가 새 엔진에서 재발).
- **심각도**: 높음. 파일럿·folded·nmcnr의 차동 신호 경로 캐스코드 쌍의 matching이 사라진다. 레이아웃 면적은 front의 판정 축이고(DEC-79), offset 관련 metric이 생기면 정확도에도 닿는다.
- **보강안**:
  1. MOD3 `rel_matching.py`(또는 새 파일 `rel_matching_stacked.py`, 규칙 C)에 **stack 전파 규칙**을 넣는다. seed는 matching_ratio·matching_offset 묶음이다. 채널 stack 엣지(같은 kind에서 X.s == Y.d이고 그 넷이 비레일)를 따라 각 멤버 바로 위 소자들이 같은 kind이고 서로 다를 때 새 묶음을 만들고, 고정점까지 전파한다. AGI §6.3 `find_stacked_matching_candidates`를 graph 인덱스(`channel_adj`) 위에서 다시 쓴다(이름 리터럴 없음). PMOS/NMOS 경계 drain-drain 접합은 AGI 10.5절 `m_cascode` 확장처럼 같은 kind 조건으로 걸러진다. status는 `derived`, role은 `cascode_pair`로 한다.
  2. U25 5.3 metamorphic test에 "T2 telescopic 캐스코드 → 캐스코드 대칭쌍 2개", "seed 없는 같은 gate 쌍(M57/M58형) → 0개"를 추가한다.
  3. MOD7에는 hub가 없는 쌍의 배치 경로를 새로 둔다. 두 행에 swap-대칭으로 분배하고 dx/dy residual로 판정한다(FSM 134 "양쪽 행에 swap-대칭으로 분배하면 dy가 크게 개선"). `mirror_symmetric_trail`(복사됨)을 행 안 대칭 trail에 재사용한다.
- **결정 주체**: 유도 알고리즘은 **엔진 내부**. 회로별 결과는 **J-U4 ratify(사용자)**. 레이아웃 요구 패턴은 G4-05(사용자).

### G4-04 차동쌍 후보(matching_offset)가 diode 멤버를 거르지 않는다

- **reference**:
  - AGI 222~223행: `m_diffpair()`는 "source 공유 + gate 상이 + 둘 다 AMPLIFYING"을 요구한다. AGI 484~485행: CMFB 비교기 쌍(`CONTROLLED_CURRENT_SOURCE`)도 인정한다.
  - AGI 437~440행(§9 test 3): M11/MN은 "둘 다 role=DIODE_CONNECTED라 `m_diffpair()`의 AMP 요구를 애초에 통과 못함".
- **새 엔진 쪽**: U25 3.2 matching_offset은 kind·비레일 source·다른 gate·정확히 2개만 본다.
- **유형**: 잘못(필터 부족).
- **심각도**: 중간. 레일 source를 제외해서 M11/MN 사례(source = gnd)는 이미 막힌다. 그래도 비레일 공통 source에 diode 2개가 물린 구조(diode stack 쌍)는 차동쌍으로 잘못 잡힌다 **[추측: 9회로 발동 여부 미측정]**. 반대로 source가 레일인 의사차동(pseudo-differential) 입력쌍은 놓친다.
- **보강안**: `rel_matching`에 "두 멤버 모두 `is_diode == False`" 조건을 넣는다. 의사차동은 "공통 source가 레일이고 두 gate가 대칭 대응 입력 포트(`graph.symmetry`)"일 때 matching_offset으로 넣되, 9회로 발동이 0이면 DEC-76에 따라 구현하지 않고 `review_needed` 기록만 한다. S6a 5절 '차동쌍 후보' 열과 대조해 다시 잰다.
- **결정 주체**: 엔진 내부. 결과는 J-U4-b ratify.

### G4-05 [결정 재검토] 레이아웃 matching 규칙: reference는 kind마다 필수 게이트가 다르다

- **reference**: FSM 134행: "전류거울(같은 gate 공유)=interdigitation(3b)만 필수, 차동쌍(같은 source 공유+다른 gate)=common-centroid(3c)만 필수 ... **`branch_symmetric` ... interdigitation(3b)은 공유 노드가 없어 그래프상 불가능 ... common-centroid(3c)는 diff_pair와 같이 필수 게이트**". 또 "**전류거울 쌍은 common-centroid dx=1.0이어도 실패가 아니다**".
- **오늘 결정**: UD 120행 "differential pair는 common centroid필수, 나머지는 둘 중 하나". UD 122행에서 차동쌍 완화를 허용했다. P N3.17 LY4·LY5.
- **어긋남**:
  - (1) 캐스코드 대칭쌍에서는 '둘 중 하나'가 사실상 common-centroid 하나뿐이다. interdigitation이 그래프상 불가능하기 때문이다. 규칙 문장이 이 사실을 담지 않아서, 구현이 interdigitation을 시도하다 실패하거나 solo 배치로 떨어질 수 있다.
  - (2) 전류거울은 reference에서 interdigitation이 필수이고, 오늘 규칙에서는 '선택'이다. 오늘 규칙이 더 넓어서 충돌은 아니다. 다만 box·면적으로 고를 때 common-centroid를 택해 거울의 interdigitation(체계적 기울기 상쇄의 주 수단)을 잃을 수 있다.
- **유형**: 결정 재검토(제안만, 결정을 뒤집지 않는다).
- **심각도**: 중간.
- **제안**: LY4·LY5에 두 줄을 더하는 것을 사용자에게 묻는다. (a) 공유 hub가 없는 matching 그룹(캐스코드 대칭쌍)은 common-centroid(행 간 swap-대칭)만 허용하고, 실패하면 차동쌍과 같은 완화 순서(LY5)를 따른다. (b) 전류거울 그룹의 정렬 키 첫째를 'interdigitation 성립'으로 두고, 둘 다 성립하면 box·면적으로 고른다.
- **결정 주체**: **사용자**.

### G4-06 행 접기(row_fold) 뒤에 matching 대칭·diffusion 안전 재확인이 없다

- **reference**: FSM 133행: "**diffusion 안전(이 함수)과 matching 안전(`check_mirror_symmetry()`)은 별개다** -- `build_mirror_symmetric_pattern()`으로 만든 행은 diffusion-safe 분할점이 있어도 그 지점에서 자르면 대칭이 깨질 수 있다(PRE-FLIGHT 사고14) -- 분할 전 두 검사 모두 확인할 것". FSM 97행에서는 Euler trail과 매칭 대칭이 별개라고 적는다.
- **새 엔진 쪽**: M7 3절 5단계는 box FAIL이면 `apply_explicit_row_split` n_rows = 2, 3, ...을 시도한다. 복사 목록(M7 1.1)에 `check_mirror_symmetry`가 없고, `find_diffusion_safe_split_points`는 `floorplan_pack.py` 안에서만 쓰인다.
- **유형**: 빠짐.
- **심각도**: 중간. 패턴 단계에서 맞춘 common-centroid가 box 단계에서 조용히 깨질 수 있다.
- **보강안**: `check_mirror_symmetry`(SD)를 복사 목록에 넣는다(AST 해시 대조). `rows.py` 5단계 행 접기 후보마다 (i) 접는 지점이 `find_diffusion_safe_split_points`의 안전 지점인지 (ii) 그 행에 든 matching 그룹마다 접은 뒤 residual·dx·dy를 다시 계산해 패턴 단계 값보다 나빠지지 않는지 확인한다. 둘 다 통과한 후보만 채택하고 기각 사유는 `attempts`에 남긴다.
- **결정 주체**: 엔진 내부.

### G4-07 단 경계를 넘는 diffusion 공유(hub merge) 탐지가 행 구성 앞에 없다

- **reference**: FSM 68행: "stage 경계를 넘는 물리 행 병합 후보 탐지(**stack_id 배정 전에 반드시 먼저 실행**) `find_hub_merge_candidates` -- stage별로 먼저 나누고 시작하면 이 탐지 자체가 누락된다".
- **새 엔진 쪽**: M7 3절 1단계 행 그룹 = "MOD3 기둥 + matching 그룹에서 유도, (kind, body 넷)으로 먼저 분리". `find_hub_merge_candidates`는 복사 목록에도 '복사하지 않는 함수와 이유' 목록에도 없다(M7 58행).
- **유형**: 빠짐(누락 사유도 기록되지 않음).
- **심각도**: 낮음. 면적 축의 질이 떨어질 뿐이고 합격 시험에는 닿지 않는다.
- **보강안**: `rows.py` 1단계에서, 같은 (kind, body) 안에서 source·drain 넷을 공유하는 서로 다른 기둥·그룹의 소자를 행 병합 후보로 기록한다. 레일 공유만 있는 후보는 FSM 155행처럼 `false_positive_shared_supply_rail`로 기각 기록한다. 그다음 행을 구성한다. 채택하지 않을 거면 M7 58행 '복사하지 않는 함수' 목록에 사유를 적는다(조용한 누락 금지, WP-02).
- **결정 주체**: 엔진 내부.

### G4-08 gate 전용 넷이 선언 없이 외부 바이어스(교류접지)로 자동 분류된다 -- 추출 오류를 조용히 흡수

- **reference**:
  - TEC 23~24행: 사고4 "'vdd' 라벨을 독립 소스 연결로 오독", 사고5 "M57 gate를 'Vip'로 오독".
  - TEC 85~87행: `topology_to_markdown.py`가 "source/drain 어디에도 없이 gate로만 참조되는 net(구동 소자 없음)을 자동으로 ⚠️ 표시".
  - TEC 104행: "net 참조 카운트 1(dangling) ... 오독 가능성 있는 net 이름 후보".
  - AGI 143~144행: analog-grammar 자체도 "잘린 도면에서 INPUT/BIAS는 구조적으로 구별 불가 -- 이름 힌트 또는 사용자 선언 필요".
- **새 엔진 쪽**: GC 4.1 `ac_ground_class = gate_only_undriven` = "레일 아님·입력 포트 아님·단자가 전부 `g`"이고 자동으로 정해진다. AC 계약에는 dangling 넷 검사가 없다.
- **실측**(이번 검토, library JSON 직접 집계): 입력 포트가 아닌 gate 전용 넷이 6회로에 선언 없이 있다. common_gate {VNBias1, VNBias2, VPBias1}, folded {bias3}, ngcc {VBP, VBN}, nmcnr {VB1~VB5}, pushpull {VPB1, VNB1}, two_stage·two_stage_sf {bias}. 이름을 잘못 읽어 생긴 넷(사고5형)도 똑같이 '외부 바이어스'가 되어 사이징이 그대로 진행된다.
- **유형**: 빠짐.
- **심각도**: 중간. library는 사람이 검토했으므로 지금 당장 틀린 것은 아니다. 다만 새 회로를 추가할 때 추출 오류를 막는 유일한 구조 신호가 사라진다.
- **보강안**(MOD2): DEC-60(레일을 이름이 아니라 선언으로 정함)과 같은 원리를 적용한다. topology에 `bias_inputs`(gate 전용 외부 바이어스 넷 목록) 선언을 추가한다. 새 키를 만들지 않고 `ports` role로 표현할 수도 있다. 그 위에 MOD2 게이트를 둔다. (i) 입력 포트도 bias 선언도 아닌 gate 전용 넷은 `SchemaRejectedError(gate_only_undeclared)` (ii) 선언했지만 gate 전용이 아닌 넷은 거부. 별도로 비차단 이상 보고(`authoring_anomalies`)를 둔다. 채널 단자가 1개뿐이고 다른 단자가 없는 넷(dangling)과 G4-19의 대칭 미해결 목록을 담는다. 오라클 OR C6(gate 전용 넷은 `bias_voltages` 필요)과도 입력이 맞춰진다.
- **결정 주체**: 형식은 엔진 내부(오케스트레이터). 6회로 topology에 선언을 추가하는 일은 **사용자**가 한다(topology 선언은 사용자 소관, 정정 대기열로).

### G4-09 넷 이름 대소문자 충돌 검사가 원소 이름에만 있다(엔진은 받고 오라클은 막는다)

- **reference**: FSM 155행: "**0번(먼저 실행): net 이름 대소문자 스캔** -- `Vbias1`/`vbias1`처럼 표기만 다른 같은 net이 있으면 그 자체로 `ok=False`(사고9 재발 방지) ... 자동 소문자 통일 없이 반드시 사람이 원본을 고치게 한다". AGI 509~525(§11.1)는 rail 대소문자 불일치가 "크래시가 아니라 **조용한 오분류**로만 나타나 발견이 늦어진다"고 적는다.
- **새 엔진 쪽**: AC 3.8 `name_case_collision`은 "세 종류를 합친 이름 공간"(소자·수동·이상원 이름)만 본다. `authoring/*.py`에 넷 이름 casefold 검사가 없다(grep 실측). 반면 OR C4는 "대소문자만 다른 두 넷 ... 막힘"이다. 엔진이 받아들인 topology가 합격 시험 단계에서야 `BLOCKED`된다.
- **유형**: 빠짐(그리고 엔진·오라클 간 충돌).
- **심각도**: 중간. 오탈자 하나가 넷 둘로 갈라져 기둥·DC 해가 조용히 바뀐다.
- **보강안**: MOD2 `name_uniqueness.py`(또는 규칙 A에 따라 새 파일 `net_case.py`)에 `net_case_collision`을 넣는다. 대상은 MOS d/g/s/bulk, 2단자 terminals, `supply_nets`, `ports` 키 전체다. 레일 별칭은 예외 없이 거부한다(엔진에는 별칭 개념이 없다).
- **결정 주체**: 엔진 내부.

### G4-10 준정적(quasi-static, f_nqs) 유효성 검사가 새 엔진에 없다

- **reference**: FSM 37행: "준정적 조건 확인 `check_quasi_static(fT, gm, Cgg, margin=0.1)` → `QuasiStaticVerdict(ok)` -- §5 체크리스트 항목". 근거는 gm-id-methodology.md 2.6·320행 "f_nqs = gm/(2π·Cgg) 계산, fT ≤ 0.1·f_nqs".
- **새 엔진 쪽**: 계획서 '준정적|quasi' 0건(실측). `_drafts/engine/*.md`·`gmid_engine/`에도 0건. M15 metric 목록(gain·gbw·pm·rout·swing·offset·power·area)에 없다.
- **유형**: 빠짐.
- **심각도**: 중간. MNA는 LUT 준정적 용량 모델을 쓴다. ugf가 소자 f_nqs에 가까운 설계점(높은 GBW, 큰 L)에서는 엔진 예측과 SPICE의 차가 커진다. 그 차를 모델 오차(DEC-72)로만 흡수하면 원인이 보이지 않는다.
- **보강안**: MOD5에 `metrics/nqs_margin.py`를 둔다. 소자마다 `f_nqs_i = gm_i/(2π·cgg_i)`(봉인 `ss`)와 `nqs_ratio_i = ugf_ss_hz / f_nqs_i`를 기록한다. 기본은 보고만 한다. 비율 상한 0.1은 reference의 경험 상수라 WP-03(상수 금지)과 충돌한다. 상한은 spec 선언으로 받거나, SPICE 대조에서 '비율 대비 모델 오차'를 실측해 유도한다.
- **결정 주체**: **사용자**(제약으로 쓸지, 임계값 출처). 기록 metric 추가는 엔진 내부.

### G4-11 SPICE 불합격 진단 절차(Z1)가 정의되지 않았다 -- reference 8단계를 도구로 배선

- **reference**: TBD 전체. 0.5 "netlist 자체가 맞는가", 1 "층 A(sizing) `.op` 대조", 2 "제거법", 3 "이상화(VCCS + ro)", 4 "정확한 노드방정식", 5 "공변 변수 분리", 6 "실측 SPICE로 최종 재검증", 7 "측정 방법론 자체도 의심 ... 대안적인 측정 방법을 하나 더 만들어 교차검증", 8 "무엇을 희생했는가".
- **새 엔진 쪽**:
  - RM 281행 Z1 "불합격 원인 반복": 절차가 없다.
  - OR: forced 모드가 층 A에 해당하고, PM은 Middlebrook β 루프 또는 개루프 A 하나로 잰다.
  - P 549행: MNA VCCS ngspice 오라클(층 3 이상화에 해당)이 계획만 되어 있다.
- **유형**: 빠짐.
- **심각도**: 중간. 9회로 합격 반복(Z1)의 속도와 결론의 신뢰도에 닿는다.
- **보강안**(`tools/spice_oracle/` + MOD5): Z1 절차를 reference 단계에 1:1로 대응시킨다.
  - 0.5 → G4-12
  - 1 → forced 모드 경고(이미 있음)
  - 2 → `oracle_netlist.py --omit <원소들>`·`--short <원소들>` 옵션(제거법)
  - 3 → 엔진 `ss`에서 VCCS+gds+C 등가 netlist를 내는 `--ideal` 모드. 계획된 MNA 오라클을 재사용하고 같은 테스트벤치에서 트랜지스터판과 나란히 비교한다.
  - 4 → G4-13 극점·영점 추출
  - 7 → PM 교차 측정 1종 추가. 폐루프 소신호 step 오버슈트 또는 폐루프 주파수 응답 peaking에서 PM을 역산해 `pm_crosscheck_deg`로 기록만 한다.
  - 8 → front 표의 활성 제약·희생 축 열
- **결정 주체**: 엔진 내부(도구). 측정 방법의 추가 정의는 PM 정의(U-48 확정)를 바꾸지 않는 '기록만'이다.

### G4-12 오라클 netlist와 topology 사이의 연결 동일성 검사가 없다(TBD 0.5단계)

- **reference**: TBD 23~39행: "1~8단계는 전부 '내가 SPICE에 조립한 토폴로지(netlist)가 원문 논문과 정확히 같다'는 것을 전제로 한다 ... NMCNR 사례가 정확히 이 실패 양상이었다(... 잘못된 노드 연결 → '노치가 있다'는 결론까지 도달)". TFD 54~61행도 같은 경고를 한다.
- **새 엔진 쪽**: OR 23~38행: 오라클 입력 `devices`·`passives`·`sources`는 엔진(또는 `legacy_adapter.py`)이 만든 JSON이다. 오라클은 topology JSON과 대조하지 않는다. 계획 P 557행은 "결과 JSON과 topology만 읽는다"고 적었지만, OR 계약 C1~C14에 topology 대조 항목이 없다.
- **유형**: 빠짐.
- **심각도**: 높음. 합격 판정의 입력 자체가 검증되지 않는다. 어댑터·결과 JSON 작성기·수동소자 이관(정정 대기열 Q3~Q5의 RL·Cc·Rz·CL)에서 연결이 하나만 어긋나도 '합격/불합격'이 다른 회로의 결과가 된다.
- **보강안**: 오라클에 `--topology <path>` 필수 인자와 계약 C15를 둔다. 오라클이 자기 netlist에서 원소별 (이름, 종류, 단자 넷 정렬 튜플)을 다시 파싱하고, topology JSON(netlist + passive_elements + ideal_sources)과 집합 동일성을 비교한다. 테스트벤치 원소(choke, 결합 C, Vrail, Efb)는 접두사 규칙으로 뺀다. 다르면 `BLOCKED`로 하고 차이 목록을 출력한다. 오라클은 엔진을 import하지 않으므로 topology JSON을 직접 읽는 최소 파서를 오라클 안에 둔다(OR C1 유지). 결과 JSON에도 topology `connectivity_fp`를 실어 오라클이 대조한다.
- **결정 주체**: 엔진 내부(도구 계약).

### G4-13 MNA에서 극점·영점을 뽑는 기능이 없다

- **reference**: TBD 86~100행: "정확한 노드방정식 ... 정확한 극점/영점을 근사식이 가정한 구조와 비교한다 -- 구조 자체가 다르면 근사가 이 영역에서 무너진 것". TFD 123행에는 NMCNR 정확 H(s) 사례가 있다.
- **새 엔진 쪽**: M15 metric은 주파수 응답 기반(ugf·gbw·pm·f3dB)뿐이다. GB5 문구 "극점·영점 식 조립"(P 496)에 대응하는 극점·영점 계산 블록은 없다.
- **유형**: 빠짐.
- **심각도**: 중간. G4-01(근사 시작점과 근사 격차 기록)과 G4-11(진단 4단계)의 입력이다.
- **보강안**: MOD5 `metrics/poles_zeros.py`(계산 블록, 입력 = `ss.mna[view]` 조립 결과)를 둔다. 극점 = (G, C) 일반화 고유값 `det(G + sC) = 0`, 영점 = 감지 출력에 대한 확장 계의 일반화 고유값이다. 지문 키는 조립 fp이고 ω와 무관하다(조립 1회 원칙 유지). 결과는 `ss.poles`·`ss.zeros` 필드다. 손계산 2극점 회로와 TFD 123행 NMCNR 닫힌 H(s)(R→∞)를 test 오라클로 쓴다.
- **결정 주체**: 엔진 내부.

### G4-14 DC 역할 유도에 '바이어스 넷 재귀 전파'가 없다(미러가 구동하는 bias 넷)

- **reference**: AGI 527~540행(§11.2): "'diode로만 구동되면 BIAS' ... 규칙은 **전류미러가 만드는 bias net**을 원천적으로 못 잡는다 ... **해결**: 드라이버 소자의 게이트 클래스를 **재귀적(고정점 반복)**으로 확인 -- '이 net을 구동하는 소자 전부의 게이트가 이미 BIAS로 분류돼 있으면, 이 net도 BIAS로 전파한다'". §11.3: 이렇게 구조로 구별할 수 없는 것은 "오탐이 아니라 matching_pairs 미선언(설계 판단)"이다.
- **새 엔진 쪽**: P 용어집 '소자 역할(DC·AC)' (2)(3), U25 2.2. 바이어스 판정은 (2) diode 멤버가 있는 gs 묶음, 또는 (3) gate가 '모든 뷰에서 교류접지'(정적 rail·gate_only_undriven뿐)이고 source가 레일인 경우뿐이다.
- **실측**: 파일럿 `Vbias4`는 지금 diode `M66`(drain = gate = Vbias4)이 있어 (2)로 잡힌다(이번 검토 JSON 확인). 그래서 library 9회로에서는 발동 0으로 보인다 **[추측: 9회로 전수로 확인하지 않음]**. 일반 회로에서 diode 없이 미러 출력만이 구동하는 bias 넷의 gate를 받는 단독 전류원(source = 레일)은 (2)·(3) 어디에도 걸리지 않는다. 그래서 `review_needed`도 아닌 `signal`로 **조용히** 떨어진다. 그러면 DEC-65 최대 전류(신호 셀 = LUT ID(VGS_max))와 규칙 5 stage 시작 예외가 틀린 입력을 받는다.
- **유형**: 빠짐(일반성).
- **심각도**: 중간.
- **보강안**(MOD3 `dc_roles.py`): 규칙 (3′)을 추가한다. S1 단계에서 뷰와 무관한 술어 'DC 바이어스 넷'을 고정점으로 정의한다. 조건은 (i) 입력 포트 전부를 동시에 여기한 최소 고정점 도달성(U25 4.2 3단계와 같은 정의, 뷰 생성 전 1회)에서 도달하지 않고 (ii) 그 넷의 채널 구동 소자가 전부 diode_reference 또는 bias_current_source인 것이다. gate가 DC 바이어스 넷이고 source가 레일인 소자는 bias_current_source가 된다. 고정점에 들지 못한 경우는 `signal` 대신 `review_needed`로 둔다. U25 5.3 metamorphic에 '미러 사슬 bias 넷(diode 없음)' 픽스처를 추가한다. 9회로 수치(28/46/68)가 바뀌는지 다시 재고, 바뀌면 J-U3 ratify를 받는다.
- **결정 주체**: 알고리즘은 엔진 내부. 결과 분류는 **사용자 J-U3 ratify**.

### G4-15 [충돌] reference가 회로별 보상 함수를 권한다 -- 대원칙 3과 정면 충돌

- **reference**:
  - FSM 44~59행: "`optimize_multistage()`의 `topology_fn` 인자로 그대로 넘긴다 -- 새 토폴로지가 이 목록에 없으면 ... `topology_library.py`에 추가한다". 표에 `miller_ota_topology`·`nmcnr_3stage_topology`·`ngcc_3stage_topology`, "`ngcc_compensation_elements()`를 추가할 것"이 있다.
  - FSM 160행: `_COMPENSATION_REGISTRY` allowlist.
  - FSM 166행: "compensation은 회로 **구조**가 기존 3개 함수 중 하나와 일치하는지".
  - TFD 1~7행·194행: "새 토폴로지를 추가할 때마다 이 표에 행을 추가하라".
- **새 엔진 쪽**: UD 141행 대원칙 3: "회로별 분기·회로별 함수(옛 compensation.function: miller_ota_topology/nmcnr_3stage_topology 등) 금지". P DF-31(975행), DEC-62. SPF 8·145행.
- **유형**: 충돌(reference가 원칙과 어긋남).
- **심각도**: 중간. 엔진 코드에는 이미 반영돼 있다. 하지만 SKILL.md가 "harness → 원소 함수 → 새 코드"(FSM 12행) 순서로 이 문서를 먼저 읽게 하므로, 다음 작업자가 회로별 함수를 다시 만드는 경로가 열려 있다.
- **보강안**:
  - TFD는 'GB5 일반 규칙의 검증 오라클 목록'으로 성격을 바꿔 다시 쓴다. 원문 식·유도·유효 영역·NMCNR 근사 붕괴 실측은 그대로 두고, "topology_library에 추가하라" 문장은 지운다.
  - FSM은 새 엔진 `gmid_engine/_module_map.py`를 가리키는 판으로 새로 쓰고, 옛 판은 `legacy/` 참고 문서로 옮긴다.
  - SKILL.md의 진입 순서 문장도 같이 고친다.
- **결정 주체**: 문서 개정은 엔진 내부(오케스트레이터). reference 삭제·이동은 **사용자 승인**(삭제·공유 설정은 사용자 몫, 메모리 원칙).

### G4-16 [reference 오류] '완전 결정'이라 적었지만 실제로는 상수가 숨어 있다

- **reference**:
  - TFD 63~75행: "Miller 2단 OTA -- 완전 결정 케이스 ... `Z`, `NDP`는 설계자가 지정하는 값"인데, FSM 52행 기본값은 `Z=10.0, NDP=4.0`이고 표에는 "완전 결정(자유도 없음)"이라 적혀 있다.
  - TFD 75행: "초기 반복엔 `C1=0.1*CL` 추정치".
  - TFD 183행: NGCC `mu_ratio` 기본값 3.9775. 다른 공정 예제에서 역산한 값이다.
- **판단**: Z·NDP는 PM을 정하는 설계 자유도다. '자유도 없음'은 틀린 서술이다. 0.1·3.9775는 WP-03이 금지한 상수다. 새 엔진은 이것들을 이관하지 않는다(SPF 185행 "`Z 10`·`NDP 4` ... → GB5 일반 규칙"). 새 엔진에 끼치는 영향은 없고 reference만 오래됐다.
- **유형**: reference 오류.
- **심각도**: 낮음.
- **보강안**: G4-15 재작성 때 "Z·NDP는 PM 목표가 정하는 자유도이고, 새 엔진에서는 MNA PM 제약이 대신한다"로 고친다. 상수 3개에는 '새 엔진 사용 금지' 표시를 한다.
- **결정 주체**: 엔진 내부(문서).

### G4-17 [reference 오래됨·충돌] analog-grammar 연동 문서의 상태와 이름 힌트 폴백

- **reference**:
  - AGI 3~9행: "§6(Tier 1) 구현 완료 ... 아직 미커밋".
  - AGI 489~501행(§10): '구현 확정 시 문서 갱신 목록'이 이행되지 않았다(FSM 65행 첫 행은 여전히 옛 그룹핑을 기본으로 안내).
  - AGI 158~161행: "`Vcmfb`류 내부 feedback net은 ... `analog-grammar`의 이름 힌트(`HINT_FB` 정규식이 `cmfb`를 이미 잡는다)로 폴백".
  - AGI 509~518행: `RAILS_POS`/`RAILS_NEG` 이름 집합.
- **새 엔진 쪽**: 새 엔진은 analog-grammar를 import하지 않고 S1 `gs_groups`로 `m_mirror`의 (G, S, type)을 대신한다(U25 2.1). 이름 리터럴은 금지된다(REQ 1.4 `test_no_name_literals`). 레일은 선언으로만 정한다(DEC-60).
- **유형**: reference 오래됨, 그리고 원칙과 충돌(이름 힌트·레일 이름 집합).
- **심각도**: 낮음.
- **보강안**: AGI 머리에 '새 엔진과의 관계' 절을 단다.
  - (a) S1 `gs_groups` = `m_mirror` 그룹 키.
  - (b) 새 엔진은 diode 레퍼런스를 요구하지 않는다(AGI §11.3 '비율이냐 1:1이냐는 mirror 여부와 무관' 결론과 일치).
  - (c) 캐스코드 대칭쌍은 G4-03 규칙이 맡는다.
  - (d) 이름 힌트·레일 이름 집합은 새 엔진에서 쓰지 않는다.
  - 상태 줄은 사실대로 고친다.
- **결정 주체**: 엔진 내부(문서).

### G4-18 [reference 오류] "10~20% 오차는 1차 근사의 정상 한계로 넘어간다"

- **reference**: TBD 16~19행: "단순한 10~20% 오차 ... 는 그냥 '1차 근사의 정상적 한계'로 문서화하고 넘어가면 된다".
- **새 엔진 쪽**: 새 엔진은 LUT 직접 조회와 전회로 MNA(gmb·cgd 포함)를 쓴다. 엔진과 SPICE의 차는 metric별 모델 오차 선언값(DEC-72)이 되어 NFR-5 여유 바닥·bin 해상도·bisection 종료의 공통 근거가 된다(P N3.8 `verified_by`). 오늘 사용자 결정(UD 129)으로 성능 차이는 기록하고 제약 여유에 넣는다.
- **판단**: 10~20%를 '넘어가도 되는 값'으로 두면 모델 오차 선언값이 근거 없이 커진다. 그러면 여유 바닥과 bin 폭이 함께 부풀어 전력·면적 front가 나빠진다. 이 문장은 옛 square-law·근사식 시절 기준이다.
- **유형**: reference 오류(오래됨).
- **심각도**: 낮음.
- **보강안**: TBD 0절을 "질적 불일치 → 8단계 진단. 양적 차 → 모델 오차 기록(DEC-72). 크기가 같은 회로 부류 기록보다 크면 1단계(층 A)부터 확인"으로 고친다.
- **결정 주체**: 엔진 내부(문서).

### G4-19 저작 단계 검토 보고(net 기준 표·대칭 기대 위반)가 새 엔진에 없다

- **reference**:
  - TEC 77~96행: "필수 절차(이제부터 topology.json을 새로 만들거나 connectivity를 수정할 때마다) `python topology_to_markdown.py` ... **net 기준**과 **소자 기준** 두 표 ... **같은 내용을 stdout에도 출력**".
  - TEC 102행: "대칭성 기대치 위반 ... 짝이 안 맞는 그룹 flag".
  - TEC 54~55행: 하위 블록 목록 diff(사고2: 반쪽 12소자 누락).
- **새 엔진 쪽**: 정정 대기열 Q1~Q5를 "한꺼번에 반영"하라는 지시가 있다(UD 140). PUD 138행은 옛 `topology_to_markdown.py`로 만든 표를 쓴다. 새 엔진 MOD2·MOD9에는 이에 해당하는 보고가 없다. U25 4.1 `graph.symmetry`에는 '미해결 목록'이 있지만 사람에게 보이는 보고로 나가지 않는다.
- **유형**: 빠짐(절차·도구).
- **심각도**: 낮음. 지금은 옛 스크립트로 대신하고 있다.
- **보강안**: MOD9 `report/topology_review.py`에서 `TopologyDoc`·S1을 입력으로 넷 기준 표, 소자 기준 표, G4-08 이상 보고(gate 전용 미선언·dangling), `graph.symmetry` 미해결 소자 목록을 Markdown으로 내고 stdout에도 출력한다. 정정 대기열을 일괄 반영할 때마다 이 보고를 세션에 띄운다(메모리 '회로도 이미지 판독은 부정확' 원칙과 같음).
- **결정 주체**: 엔진 내부.

### G4-20 matching 그룹의 status(derived/proposed/review_needed)를 레이아웃이 어떻게 쓰는지 정해지지 않았다

- **reference**: FSM 155행: "후보마다 (a) `matching_pairs`에 채택되거나 (b) `dispositions`에 기각 사유가 있어야 `ok=True`". AGI 549~553행(§11.3): 매칭이 필요한지는 "설계자가 결정할 문제"다.
- **새 엔진 쪽**: U25 3.0 RelEdge status는 `derived`/`proposed`/`review_needed`이고, `l_class`는 proposed, 3개 이상 공통 source는 review_needed다. M7 L8은 "MOD3 구조 유도 출력 레코드"를 그대로 쓰고 status 정책을 두지 않는다.
- **유형**: 빠짐.
- **심각도**: 중간. review_needed 묶음을 레이아웃이 매칭으로 쓰면 강제 패턴 때문에 면적이 늘고, 무시하면 기록 없이 빠진다.
- **보강안**: `graph/matching_groups.py` 계약에 정책을 둔다. MOD7은 `derived`와 ratified만 matching 그룹으로 쓴다. `review_needed`·`proposed`는 '매칭 없음'으로 배치하고 결과 JSON `matching_dispositions[{group, status, 처리}]`에 남긴다. J 대조표에서 ratify하면 다음 실행부터 반영한다.
- **결정 주체**: 정책은 엔진 내부. 회로별 ratify는 **사용자 J**.

### G4-21 [결정 재검토] bulk 기본 규칙과 도면의 body 태그(TEC 사고4)

- **reference**: TEC 23행 사고4: "M57/M58의 'vdd' 라벨을 독립 소스 연결로 오독(실제로는 well/body bias 태그)". TEC 106행: 반복 라벨이 '다른 의미(well/body bias 태그)'일 수 있으니 작성자가 명시적으로 확인했다는 플래그를 요구한다.
- **오늘 결정**: UD 131행 6번 "bulk 기본 규칙(전위 극값: nmos 최저·pmos 최고, 예외는 소자별 bulk 선언)". S1D 8.2절: bulk 선언은 9회로 모두 0이고, follower 소자(two_stage_sf M8, pushpull M1~M4, sf M18~M22)에 기본 규칙이 그대로 적용된다.
- **어긋남**: 기본 규칙 자체는 reference와 충돌하지 않는다. 다만 reference가 겪은 사고는 '도면의 body 태그를 연결로 잘못 읽은 것'이다. 기본 규칙이 조용히 적용되면 도면이 body를 source에 묶은 follower(별도 well)를 확인할 기회가 사라진다. follower의 gmb와 VSB는 출력 레벨·이득에 직접 닿는다.
- **유형**: 결정 재검토(제안만).
- **심각도**: 낮음(S1D 8.2가 이미 사용자 확인을 요청해 둠).
- **제안**: S1D 8.2 확인 요청을 TEC 6절(Stage 3) 형식으로 좁힌다. "이 소자들(목록)의 body가 도면에서 어느 넷입니까, 후보 A(극값 레일)/B(자기 source)"처럼 소자별 구체 질문으로 바꾸고, 답은 정정 대기열에 넣는다.
- **결정 주체**: **사용자**.

---

## 2. 대원칙과 충돌하는 reference 권고(따로 모음)

| reference 위치 | 권고 | 충돌하는 원칙 | 처리 |
|---|---|---|---|
| FSM 44~59, 160, 166 / TFD 1~7, 194 | 회로별 `topology_fn`·보상 함수 추가, allowlist 레지스트리 | 대원칙 3(topology 종속 금지), DEC-62, DF-31 | G4-15 |
| FSM 52 / TFD 75·183 | `Z=10`, `NDP=4`, `C1=0.1·CL`, `mu_ratio=3.9775` 기본값 | WP-03 상수 금지 | G4-16 |
| FSM 37 / gm-id-methodology 2.6 | 준정적 `margin=0.1` | WP-03 | G4-10(선언 또는 실측 유도) |
| AGI 158~161, 509~518 | 이름 힌트(`HINT_FB` `cmfb`)·레일 이름 집합 | DEC-60, REQ 1.4 이름 리터럴 금지 | G4-17 |
| FSM 0절(harness 재사용 우선) | 옛 harness 함수부터 호출 | 대원칙 2(기능별 파일)·새 엔진 재설계(UD 119) | G4-15(문서 재작성) |
| TBD 2·5절 | 제거법·변수 분리 스윕을 매번 수동으로 | 대원칙 1(같은 값 반복 계산 금지) | G4-11: 오라클 결과는 (netlist sha256, 모델 fp, 명령) 디스크 캐시(REQ 4.1)로 반복 실행 비용 0 |

---

## 3. 요약표

| 심각도 | 개수 | ID |
|---|---|---|
| 높음 | 4 | G4-01, G4-02, G4-03, G4-12 |
| 중간 | 11 | G4-04, G4-05, G4-06, G4-08, G4-09, G4-10, G4-11, G4-13, G4-14, G4-15, G4-20 |
| 낮음 | 6 | G4-07, G4-16, G4-17, G4-18, G4-19, G4-21 |
| 합계 | 21 | |

유형별: 빠짐 14(G4-01, 02, 03, 06, 07, 08, 09, 10, 11, 12, 13, 14, 19, 20) · 잘못 1(G4-04, G4-01 일부 포함) · 충돌 2(G4-15, G4-17 일부) · reference 오류 3(G4-16, 17, 18) · 결정 재검토 2(G4-05, G4-21). G4-01과 G4-17은 두 유형에 걸친다.

결정 주체별: 사용자 결정 필요 6(G4-01 방법론, G4-02 규칙 선택·J7, G4-05, G4-08 topology 선언 추가, G4-10 제약 여부·임계값, G4-21). 사용자 ratify(J) 동반 4(G4-03, G4-04, G4-14, G4-20). 나머지는 엔진 내부.

## 4. 상위 5개 권고

1. **G4-01 GB5를 정확한 MNA 제약으로 정의한다(사용자 방법론 결정).** 보상 수동소자 값을 θ 연속 변수로 두고 GBW·PM을 봉인 `ss` 전회로 MNA로 판정한다. 근사 극점·영점 식은 시작점과 `comp_approx_gap` 기록에만 쓴다. 근거: TFD 3절, NMCNR Eq10/11의 GBW 2.5~21배 붕괴 실측.
2. **G4-03 캐스코드 대칭쌍을 stack 전파로 유도하고(MOD3), hub 없는 쌍의 배치 경로를 둔다(MOD7).** AGI §6.3이 이미 찾아 고친 공백이 U4 규칙에서 다시 생긴다. G4-05(이 쌍은 common-centroid만 가능)와 함께 사용자에게 레이아웃 규칙 보강을 묻는다.
3. **G4-12 오라클에 topology 연결 동일성 검사(C15)를 넣는다.** 오라클 netlist를 다시 파싱해 topology JSON(netlist + passive + 이상원)과 집합 비교하고, 다르면 BLOCKED로 한다. 합격 판정의 입력 자체를 검증하는 장치이고, TBD 0.5단계(NMCNR 잘못된 조립 사고)의 구조적 차단이다.
4. **G4-02 영점 상쇄 저항의 기준 소자를 구조 규칙으로 유도한다.** R = 1/Σgm(저항 끝 넷을 출력노드로 갖고 루프 반대쪽에서 신호를 받는 CS 셀)으로 두거나, R을 θ로 둔다. 회로별 결과는 J7에서 ratify한다. 엔진이 `nulling_reference_device` 선언을 읽지 않으므로 이 규칙이 없으면 Rz·Rm 값이 정해지지 않는다.
5. **G4-08·G4-09 MOD2 입력 게이트를 보강한다.** gate 전용 외부 바이어스 넷을 선언하게 하고(미선언은 거부, 6회로 선언 추가는 사용자), 넷 이름 대소문자 충돌을 거부한다. 지금은 추출 오류(TEC 사고5형)가 '외부 바이어스'로 조용히 흡수되고, 대소문자 충돌은 엔진이 받은 뒤 오라클에서야 막힌다.
