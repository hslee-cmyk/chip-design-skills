# 계획 v6.38.5 Q-KV1·Q-CB1(+Q-CB2) 대 design v1.15.3 -- 영향 자리 보충 대조 (읽기 전용 분석)

- 작성: design↔계획 대조 분석 agent, 2026-10-29. 문서 수정 0, git은 `git -C` 읽기만. 이 파일이 유일한 산출물이다.
- 보충 대상: `plan_v6385_design_impact.md`(DI, 계획 열째 커밋 `6b0d70f6` 기준). DI는 Q-KV1을 권고 (가) 기준으로만 다뤘고 Q-CB1·Q-CB2는 다루지 않았다.
- 계획: worktree `wt/plan-v6385` HEAD `74e62d53`(열여섯째 커밋). 읽은 행: N5.3 Q-KV1(1165)·Q-CB1(1166)·Q-CB2(1167), DEC-64(263)·DEC-95(294)·DEC-104 R13·(3)(a)(303)·DEC-105 (10)(304), N6.1 TB-1(1211)·SF-1(1217)·DR-1(1231), SF-1 범위 6 (e)(2192)·9(2195), TB-1 범위 1·만들면 배선·완료·순서(2209~2218), DR-1 범위·완료 (10)·순서(2348~2352), held-out 정의(1305)·U-75(2478).
- design: worktree `wt/design-v115` HEAD `792cd0bd`(DI와 같은 HEAD), 40·41·42 = v1.15.3. 줄 번호 = 이 HEAD 실측.
- 엔진 확인: 같은 worktree `skills/analog-gmid-design/gmid_engine`(master 병합본) -- `search/search_domain.py`, `search/iv_context.py`, `search/start_values.py`, `sizing/writer_plan.py`, `sizing/kernel_context.py`, `graph/structure_load.py`, `pipeline/stage_b.py`, `assets/heldout/erfc_ota.sizing_spec.json`, `assets/sky130_pdk_decl.json`.
- 범례: **[실측]** 파일에서 직접 확인 / **[추론]** 실측 사실에서 유도(검증 안 함). 구분 칸: (R) 권고 승인 시 / (A) 대안 승인 시 / (N) 결정과 무관.

---

## 0. 요약

1. **Q-KV1 (다)+(A)** 승인 시 design 자리는 **22곳**(40 아홉·41 열·42 셋 + 새 행 두셋)이다. 승인 문서가 적은 10곳 밖에 핵심 누락이 있다: (i) 41 §6.7-11 R6 출력 `loop_dep.b_ln_idu`와 41:882 B 행 -- (다)에서는 고리의 종속 멤버가 B이므로 그 B의 ln IDu를 R6 블록과 커널 쓰기 계획이 함께 정하게 된다(같은 양 생산자 둘, graph 규칙 1). 'dc_coord 종속 B 멤버는 R6 출력에서 뺀다'는 규칙이 design에 있어야 한다 [추론] (ii) 40:462 쓰기 계획 필드 행(READS에 `theta_class`·ratified 사실이 더해짐) (iii) 40:905~913 `structure.json` concept 표 -- ratified 고리 종속 선택(J12-f)을 담을 concept가 없어서 (A)의 'ratified 로더 READS'를 받을 자리가 없다 [실측] (iv) 40:1913 J12-f '엔진 유도·열림'과 (다)의 'ratified는 B 안에서만, 아니면 정지' 사이의 상호작용 (v) 41:644 IT-1 test interface '서명 불변'(`order_hints=` 인자는 (A)에서 사라짐) (vi) 40:2162 U4 행·40:1780 R14 행·40:2174 U15 행(O-149) (vii) 42:311 D-TB1a(쓰기 계획 다음·`dc_coord` 입력·소비자 0 -- 세 문언 모두 바뀜).
2. **Q-CB1 (나)+(α)+(Q)** 승인 시 design 자리는 **20곳 안팎**이다. 승인 문서 칸은 '독립 대조 안 함'이라고 적었다. 대조해 보니 핵심 자리 다섯이 빠졌다:
   - (i) 40:873 θ 상자 머리 -- '로더가 정하고 결과는 θ 스키마의 그 성분 상자'가 (α)의 writer(검색 정의역 S0 블록)와 정면 충돌한다.
   - (ii) 40:875 `zero_cancel_box`를 'θ 스키마가 부름' -- 적용 상자 writer가 하나라는 조건과 겹친다. 계획 본문 순서 넷에도 (b) 영점 R·(c) DC 경로 R의 자리가 없다(계획 쪽 공백).
   - (iii) 40:877·41:1635·41:1648의 '(d) 거부 = 단계 A' -- as-built `search_domain`은 단계 B다(`stage_b.py:158`).
   - (iv) 41:886·41:1716·41:1761·42:315 -- R6·층 0이 V_R 구간을 'spec `search.theta_bounds`'에서 직접 읽는다. 계획 완료 조건 'spec 설정 직접 읽기 0'과 충돌하는데, 계획 소비자 목록에도 없다.
   - (v) **40:2092 §10.5 held-out 정의('spec 값 조정에 쓰지 않은 회로', 계획 1305·U-75)** -- Q-CB1은 erfc(held-out) 결합 C 하한을 erfc oracle SR sweep으로 정하겠다고 한다. 이것은 held-out 회로의 spec 값 조정이다(⚠ 계획·승인 문서·`cbox_rereview.md` 어디에도 DEC-98·U-76 언급 0건) [실측].
3. **지금(결정 없이) 고칠 수 있는 곳** 6건:
   - 42:146 D-GB1a·42:67의 '`structure.json` 로더 MISS·rg 0' -- 낡았다(`graph/structure_load.py` 있음, 엔진 .py 19건).
   - SF-1 범위 6 (e) 선언 상자 S0 필드 -- design에 이름·블록이 없다(v6.38.4 승인분).
   - 40 §11 card 표에 DR-1 행이 없다.
   - 41:886·1716·1761의 'spec 키 직접 READS' -- 이 가운데 S0 필드 READS로 바꾸는 부분만 결정과 무관하다.
   - 두 질문의 '계획 v6.38.5 대기' 표지 -- 지금은 Q-W1·Q-CF1 자리에만 있다.
   - 40:874 기록 문언. 결정 원문이 '보상 커패시터'라는 사실을 표지로 남긴다.
4. **승인 문서 대조 -- 틀리거나 빠진 곳 14건**(§4). Q-KV1 칸에는 줄 번호·문언 착오 2(41:874에는 '쓰기 계획 다음'이 없음, 'HC-D design 재작성' -- HC-D design은 없음)와 누락 7이 있다. Q-CB1 칸에는 누락 5('StartView' 자리는 design에 없어 40:392 행 추가가 필요하다는 것 포함)가 있다. 별도로 승인 문서와 계획은 (가) 반례 고리 예시가 서로 다르다(계획 {M11a, M11b, M15, M9a} 대 승인 문서 {M14a, M14b, M16, M9b}). 계획 본문의 '확신도 상 = M9b 고리'와 맞는 쪽은 승인 문서다(계획 1165 문언 정정 대상).

---

## 1. Q-KV1 -- `kvl_branch` 고리 종속 멤버 선택과 옛 OrderHints

### 1.1 권고 (다) B 멤버 종속 + (A) OrderHints 삭제·Kruskal 키 재작성 -- design 자리 전수

계획 근거: Q-KV1 행(1165), DEC-95 (3) 주석(294), DEC-104 R13·(3)(a) 주석(303), TB-1 N6.1(1211)·범위 1(2209)·만들면 배선(2214)·완료 (5)(2216)·순서(2218).

| # | 자리 | 지금 문언 [실측] | 바뀔 내용(R) | 근거(계획) |
|---|---|---|---|---|
| K1 | 40:449 §2.4.8 `theta_class` 행 | `kind ∈ {S, F, B, X}`, X = `dc_coord.relation` 종속; 입력에 `device.dc_coord`; 'sizing 층 4: 쓰기 계획 블록 `dc_writer_plan` **다음** S0 블록'; '읽는 쪽 ... TB-1 병합 때 엔진 소비자 0(O-146 K2)' | X 삭제(`dc_coord.role` READS로 대체 -- graph 규칙 3), 입력에서 `dc_coord` 삭제(순환 방지), 층 진술 '쓰기 계획 **앞** S0 블록'(입력 = S1v `Block.roles`·spec·L 동치류 -- 모두 graph·authoring 층이라 층 순서 검사는 그대로 성립 [추론]), 읽는 쪽 맨 앞에 `dc_writer_plan`(Kruskal 키) 추가, 'TB-1 병합 때 엔진 소비자 0' 삭제 | 1165 (다), 2209, 2214 |
| K2 | 40:462 §2.4.8 쓰기 계획 필드 행 | writer `dc_writer_plan`(S0, 그대로), 형식 불변 | writer READS에 `device: theta_class`와 ratified 고리 선택 사실 추가. `device: dc_coord` **값** 변경(종속 = B 멤버 -- current_reuse 4고리 M15·M16·M25·M26 → M11a·M14a·M20a·M23a), `graph: dc_tie_breaks` decision에 B 안 이름 결정이 들어올 수 있음 [추론] | 1165 (A), 2216 (5) |
| K3 | 40:1107 §3.7 항목 4 | 'ratified 선택(`structure.json`)과 ② GB5 gm 요구·뒤 stage 독립을 Kruskal 엣지 키 앞에. ②의 입력은 S1v stage 번호' | 전면 재작성: 고리에 R13 B 멤버가 있으면 B 멤버가 종속이다(B 안 순위 = diode → 대칭 궤도 대표 → 이름). ratified 선택은 B 멤버 안에서만 하고, 아니면 정지·기록(사유 이름은 design). 대칭 고리 쌍은 대표 고리 선택의 상(image)으로 고른다(design 몫 -- 검증 9 m9-2). ①·②는 B 멤버가 없는 고리에만 쓰고, ② 입력은 R13 S·F다(S2 양 'GB5 gm 요구' 삭제). Kruskal 키에서는 '키가 큰 엣지 = 비트리 = 종속'이므로 B 멤버 키를 **위로** 올린다(as-built 'diode < 그 밖'은 diode를 독립으로 남기는 방향 -- `writer_plan.py:11-15`) [실측] | 294, 1165 |
| K4 | 40:1122 §3.7 상태 표 'DEC-95 (3) 전체 순서' | PART(① 구조 색·이름만) | 증거 칸에 OrderHints 미배선(`stage_b.py:152`), 구현 card = TB-1 | 1165 (A) |
| K5 | 40:1780 §8 R14 행 | 'DEC-95 (3) ratified·② 없음 → 복원(§3.7)' | 복원 대상 = 개정된 DEC-95 (3)((다) 순위). '② 복원'이라는 문언은 낡는다 | 294 |
| K6 | 40:2162 §11 U4 행 | U4 sizing 보강에 'DEC-95 (3) 전체 순서' | 그 항목을 card TB-1로 넘긴다(U4에서 뺌) | 1211, 2209 |
| K7 | 40:2174 §11 U15 행 | '선행 card TB-1(O-144 J3; TB-1 master 병합은 HC-1·LA-1 가운데 먼저 ... O-149)' | O-149 병합 규칙 재검토(첫 행동 소비자 = TB-1 자신) -- 병합 규칙 문언 정정 | 2214, 2218 |
| K8 | 40:2193 §11 TB-1 행 | '범위 1·2', '선행 = HC-S', 'master 병합 = HC-1·LA-1 가운데 먼저 ... (O-149). 병합 때 엔진 소비자 0(O-146 K2)' | 범위에 `E/sizing/writer_plan.py`·`kernel_context.py`·`sizing/__init__.py` 추가, 삭제 `s2_values.py` OrderHints·`sizing/CONTRACT.md:1001-1004`. 파일 겹침 IT-1·DR-1(같은 통합 병합 금지, 나중 card가 rebase), 동작 변경 → SPICE 다리 선행 EO-1, O-149 재검토, '엔진 소비자 0' 삭제 | 1211 |
| K9 | 40:905~913 §3.2-3 `structure.json` concept 표 | concept 7개(`drive_kind`·`stage_members`·`dc_role`·`loop_role`·`feedforward_cell`·`ac_ground_exception`·`matching_pair`·`l_owner`) -- **고리 종속 선택 concept 없음**. 엔진 `graph/structure_load.py`의 닫힌 어휘도 같음 [실측] | (A)의 'ratified 단계 = structure ratified 로더를 쓰기 계획이 READS(형식 design)'를 받을 새 concept 행(예: 고리 id → 종속 멤버, 소비 = `dc_writer_plan`, override). 없으면 ratified 단계는 빈 입력이다 | 1165 (A) |
| K10 | 40:1913 §9.3 J12-f | '루프 종속 gm_id 소자 선택·합류 노드 KCL -- 엔진 유도 -- 열림' | (다)의 'ratified 선택은 B 안에서만, 아니면 정지'와 J12-f ratify 후보(DEC-64 예: `sf_pushpull_output_opamp` M21/M22 -- 계획 263)가 B인지 TB-1 분류로 확인해야 한다. B가 아니면 ratify가 정지로 바뀐다 [추론] | 263, 1165 '(다)의 6고리 선택' |
| K11 | 41:644 §4.7 IT-1 test interface | '`dc_writer_plan(snapshot, target_nets, input_dc_declared, order_hints=NO_ORDER_HINTS)`(서명 불변)' | (A)로 `order_hints` 인자가 없어짐 -- TB-1이 서명을 바꾼다(IT-1 test는 인자를 넘기지 않으므로 호환되나 '서명 불변' 문언은 IT-1 시점 한정으로 적어야 함) [추론] | 2209 (OrderHints 삭제 목록) |
| K12 | 41:874 §5.3.3 '분류의 정본' | '표의 '제외'가 R13의 X(쓰기 계획 종속)다' | '제외'의 출처 = `dc_coord.role`/`relation` READS(R13에는 X 칸 없음) | 303 R13 주석 |
| K13 | 41:880 §5.3.3 '제외' 행 | `dc_coord.relation` = `cycle_vgs`·`fixed_vgs` 종속 + `parallel_vgs` 비뿌리 | 정의 그대로. (다)에서는 제외 대상에 **B 멤버(diode)**가 들어온다는 문장 추가(종속 = B) | 1165 |
| K14 | 41:882 §5.3.3 B 행 | 'B ... 고리 종속이면 후보마다 DEC-104 R6 블록 값' | (다)에서는 고리의 쓰기 계획 종속 멤버가 B다. 그 B의 ln IDu는 커널 고리 등식이 정하므로 **R6 값 대상에서 뺀다**는 문장이 필요하다(아니면 같은 양의 생산자가 둘 -- graph 규칙 1). R6이 정하는 것은 같은 고리의 다른 B(쓰기 계획 writer 역할)뿐이다 [추론 -- 계획 문언에 없음, design 결정] | graph 규칙 1, 1165 'R6(B ln IDu 종속)과 정합' |
| K15 | 41:1759~1763 §6.7-11 R6 블록 '값'·'출력 자리' | `LoopDep(b_ln_idu, w4, v_r, reopen)` -- B ln IDu 대상 한정 없음 | K14와 같음: `b_ln_idu` 대상 = 고리 B 멤버 중 `dc_coord.role = writer`. 종속 B 멤버는 E-0 검사(LUT 정의역 안·포화)만 하고 쓰지 않는다 [추론] | 1165 E-0 기준 |
| K16 | 41:1406 §5.12.6 E11 | `ThetaClass(kind ∈ {S,B,F,X})`, writer 'theta_class(쓰기 계획 다음 S0 블록)' | `{S,B,F}`, '쓰기 계획 앞 S0 블록' | 2209 |
| K17 | 41:1521 §6.7 7a·41:1698·41:1722 | '쓰기 계획 v2 고리 등식(**X**)', '고리 종속 멤버(**X**)', '`loop_lo`·`loop_hi`는 ... 고리 등식(**X**)의 종속 소자 구간 행' | 'X' 기호를 `dc_coord` 종속으로 바꾼다(R13에 X 칸 없음). 41:1722의 `loop_lo/hi` 구간은 (다)에서 종속 다이오드에 걸린다 -- E-0(종속 다이오드 W가 LUT 정의역 안) 검사 자리 [추론] | 303 |
| K18 | 41:1703 §6.7-1 | '종속 소자는 DEC-95 (3) 우선순위로 이미 정해져 있다' | '개정 DEC-95 (3)(B 멤버 종속)' | 294 |
| K19 | 41:1277 §5.12 대응표 | 'S/B/F/X 분류 S0 필드(card TB-1)' | 'S/B/F'(이름 변경). 41:1318(B 정의 행)·41:898(처리 자리)은 내용 변경 불요 [추론] | 303 |
| K20 | 42:311 D-TB1a | '쓰기 계획 다음', 입력 `device.dc_coord`, '병합 때 엔진 소비자 0(O-146 K2) -- ... O-149' | 셋 다 바뀜 + 확인 칸에 TB-1 완료 (5)의 동작 변경 변화표·E-0 단언·I_Q E-1 | 2209, 2214, 2216 |
| K21 | 42:134·42:267 D-GB7c | 'PART -- `writer_plan.py:13-17`' | card = TB-1, 확인 = (다) 6고리 선택 toy·OrderHints grep 0 | 1165 (A) |
| K22 | 42:67 | 'ratified 선택(J12-c·f)을 읽는 곳이 없다(`structure.json` 로더 MISS)' | 로더는 있음(§3 N1). 빠진 것은 고리 선택 concept와 쓰기 계획 READS -- K9와 짝 | 1165 (A) |
| 새 | 42 새 행(D-TB1d 꼴) | 없음 | OrderHints 삭제·Kruskal 키 재작성·ratified READS·(다) 6고리 손 판정 toy·E-0 | 2209 |

**결정과 무관하지만 함께 볼 것(N)**: 40:1473·41:629(IT-1 입력 점 Kruskal 묶음)는 키 재작성 뒤에도 그대로다(정점 묶음은 키와 별개 [추론]). 파일 겹침(IT-1·DR-1 `writer_plan.py`)은 계획대로 '나중 card가 rebase'다.

### 1.2 대안 승인 시 자리

| 대안 | 자리 | 내용 |
|---|---|---|
| (가) 규칙 그대로 + ② 입력만 S0 술어 | K3(40:1107 ② 술어 정의 -- 술어 출처 design)·K4·K5·K11·K21. **(A)는 (가)에서도 필요**(계획 1165)하므로 K9·K10·K22와 TB-1 행(K8)의 OrderHints 삭제 범위도 바뀐다. R13 층 위치(K1·K16·K20 '쓰기 계획 다음')·X 칸(K12·K17)은 **그대로** | ⚠ 계획 TB-1 행(1211·2209)은 '(다)+(A) 승인 시'만 적었다. (가)+(A)일 때 (A)를 맡는 card·파일 범위가 계획에 없다 -- 계획 쪽 공백 |
| (나) ② → R13 S·F 독립, ① 유지 | (다)의 K1·K2·K4~K9·K11·K12·K16·K17·K19~K22(R13 앞당김·X 삭제·OrderHints)와 같음. K3 규칙 문언만 다르다(B 멤버 종속 없음). K13~K15(종속 B와 R6)는 해당 없음 | 계획이 적은 모순(L-11·R6) 유지 |
| (라) L-11 범위 개정 | 41:872 L-11 개정 문단·41:882 B 행('가드 선택점') + K3 | O-127·O-128 원칙 문언 |
| (B) OrderHints 그대로 배선 | 40:1107(② = S2 양 유지)·40:2162 U4 | ⚠ 층 역전(S0 쓰기 계획이 S2 양을 읽음) |
| (C) 미배선 유지 | design 변경 0 | ⚠ 만들면 배선 위반 |

---

## 2. Q-CB1 -- θ 커패시터 상자 역할별 분리 (+Q-CB2)

### 2.1 권고 (나)+(α)+(Q) -- design 자리 전수

계획 근거: Q-CB1 행(1166) (1)~(4), DEC-105 (10)(a) 주석(304), SF-1 범위 6 (e) 끝 문장(2192)·범위 9 주석(2195), DR-1 범위(2348)·완료 (10)(2350)·순서(2352).

| # | 자리 | 지금 문언 [실측] | 바뀔 내용(R) | 근거 |
|---|---|---|---|---|
| C1 | **40:873** §3.1-1 θ 상자 머리 | '로더(spec 로더 하나)가 소자마다 아래 순서로 정하고 결과는 θ 스키마의 그 성분 상자다(필드 사본 0)' | **적용 상자 writer = 검색 정의역 S0 블록 `search_domain` 하나**(층 = `graph.dc_current_basis`·`theta_schema` 뒤, 결과 = `graph/kernel: search_domain`의 `variables` 상자). 로더는 구문 검사만 한다. 본문 순서 = 회로별 선언(선언 상자 READS) → 결합 C 선언 필수·미선언 정지 → 그 밖 커패시터 공통 상자 → 출처 없는 θ 수동소자 정지. '원래 취지와 다름(로더 → S0 블록)' 표지 | 1166 (2), 2195 |
| C2 | **40:874** (a) | '보상·결합 커패시터 -- 물리 결정자: 값을 정하는 법칙이 없는 AC 설계 변수' + 공통 선언 `theta_box_common.json`(기록 원문 '**engine 보상 커패시터** θ 상자 [0.1 pF, 10 pF]') | 둘로 나눔: (a1) 보상 C = 공통 상자('10번', ⚠ 관례 -- Q-CB2) / (a2) 결합 C = 구조 판별('C 한 끝 넷에 닿는 소자가 MOS 게이트와 구조적 0 전류 MOS(≥ 1)뿐', 게이트·커패시터만의 DC 부유 넷 제외) → 회로별 선언 필수·미선언 정지(`theta_*_bounds_undeclared` 꼴), 물리 결정자 = 결합비 α·SR(대신호), 하한 = oracle `.tran` SR sweep 경계 | 1166 사실·권고, 304 |
| C3 | **40:875** (b) 영점 R 상자 | '`zero_cancel_box(...)` 하나(자리 `E/sizing/theta_schema.py` -- **θ 스키마가 부름**)' | 적용 상자 writer가 `search_domain` 하나이면 `zero_cancel_box`도 그 블록 본문이 불러야 한다. θ 스키마가 상자를 쓰면 적용 상자 생산자가 둘이 된다(graph 규칙 1). 순수 함수 자리는 어디든 된다(O-153). ⚠ **계획 1166 (2)의 본문 순서 넷에는 (b) 영점 R·(c) DC 경로 R 갈래가 없다** -- 계획 쪽 공백(design이 순서에 넣거나 계획 정정) | 1166 (2), 304 (b)(c) |
| C4 | **40:877** (d) | 'fail-closed 거부 `theta_*_bounds_undeclared`(**단계 A**, 탐색 전)' | 거부 자리 = 검색 정의역 블록(as-built 단계 B -- `pipeline/stage_b.py:158`, `search/search_context.py:173`), 탐색 전은 그대로. `theta_bound_element` 교차 검사(`authoring/spec_theta_bounds.py`)도 이 블록 안 거부로 옮긴다 -- design에 이 이름이 0건이라 새 문장이 필요하다 | 1166 (2) |
| C5 | 40:879 '지우는 것' | `SearchSettings` 재정의·`_passive_box` 재정의 경로, 회로별 커패시터 사본 9개(library) | 그대로 맞다. **erfc(held-out) CBAT1_L·CBAT1_R·CBAT2 선언 추가 data 커밋**이 새로 생긴다(지금 erfc spec에 `theta_bounds` 0 -- `assets/heldout/erfc_ota.sizing_spec.json:67-87`은 `engine: true`만 있다 [실측]). 그 전까지 erfc는 '미선언 결합 C 정지' | 1166 권고, 2350 (10) |
| C6 | 40:418 §2.4.7 `domain` 행 | 'writer `search_domain`, 읽기: θ 스키마·S1·PDK 선언·**spec θ 범위**·면적 예산·untie' | 'spec θ 범위' → SF-1 범위 6 (e) 선언 상자 S0 필드 READS + `graph.dc_current_basis`(결합 C 판별 -- as-built READS에 이미 있음 `search_domain.py:89-90`) | 2192, 1166 (1)(2) |
| C7 | 40:458 §2.4.8 S0 필드 행 | `graph/kernel: search_domain` 외 | 두 필드의 정의 축을 적는다: 선언 상자(6 (e), S1 앞, 입력 = spec) 대 적용 상자(`search_domain`, 공통 상자·결합 C 판별·미선언 정지를 적용한 양) -- graph 규칙 3 | 1166 (2) |
| C8 | 40:392 §2.4.7 `StartContext` 행 | `box` 등 사본 '없앤다' -- **`StartView` 이름 0건** | 사본 칸 `StartView.theta_bounds`(`search/start_values.py:180`, 채움 `iv_context.py:94`) 삭제를 행에 넣는다 | 1166 (2) 소비자 |
| C9 | 소비자 재배선 -- design 문언 없음 | `iv_area.py:85`(41:1465 행은 `w_min_gm_id`만), `_helpers_area.py:24`(40:2181 'S0 필드 이동 ①-b 이월'), `macro_poles.py:133,141`, `achievability.py:126,248` | 적용 상자 = `domain.variables` READS로 다시 잇는 문장 + `iv_area` 공통 상자 커패시터 최소 면적 하한 toy(base red). **파일 겹침**: `macro_poles.py:131-157`은 LA-1 범위 15 (g)도 고친다(41:1635·1648, 40:1466). `achievability.py`는 WB-1 소비자 전환(40:1192)과 겹치고, `iv_context.py`는 LA-1 범위 15 (a)(41:1582)와 겹친다 -- 계획은 `iv_context` 겹침만 적었다(2192) | 1166 (2), 2195 |
| C10 | **41:886**(§5.3.3 θ 저항)·**41:1716**(§5.3.4 (c-1) V_R 구간)·**41:1761**(§6.7-11 READS)·**42:315**(D-L0) | '상자 = spec `search.theta_bounds.<원소>`', 'V_R 구간 = spec 저항 상자(`search.theta_bounds`) × I_R', R6 READS에 '`graph/kernel: search_domain`·spec `search.theta_bounds`' | 계획 완료 조건 'spec 설정 직접 읽기 0(`git grep`)'이 R6·층 0(LA-1)에도 걸린다 → 적용 상자(`search_domain`) READS. ⚠ **계획 1166 소비자 목록에 이 자리가 없다**(LA-1이 만들 소비자라 as-built grep에 안 잡힘) | 1166 (2) 완료 조건 |
| C11 | 41:1635·41:1648 §6.5 | '상자 미선언은 단계 A 거부(DEC-105 (10)(d))라 매크로에 닿지 않는다' | '단계 B 검색 정의역 블록 거부'(매크로에 닿지 않는 것은 그대로 -- 출발 단계가 그 뒤 [추론]) | C4와 같음 |
| C12 | 40:2194 §11 SF-1 행 | '범위 9 θ 상자 공통 규칙(v6.38.2) 포함' | 범위 9 = `search_domain` 재작성·소비자 재배선·사본 칸 삭제·완료 조건(적용 상자 writer 1곳·사본 0·spec 직접 읽기 0·`iv_area` toy). 결합 C 갈래는 DR-1로 | 1217, 2195 |
| C13 | 40 §11 표 -- **DR-1 행 없음** | -- | DR-1 행(선행 = IT-1 + IT-2·**SF-1**, 결합 C 갈래 + 완료 (10) toy, design = 새 DR-1 design) | 1231, 2352 |
| C14 | 41:2029 §9 SF-1 범위 8~11 test 행 | 'θ 상자 (a)~(d) toy·`zero_cancel_box`' | `iv_area` 하한 toy 추가. 결합 C toy 셋(미선언 → 정지, 선언 → 선언 상자, 0 전류 MOS 없는 θ 커패시터 → 공통 상자)은 DR-1 test 행(새로) | 2350 (10) |
| C15 | 42:340 D-TBX | '(a) 커패시터 공통 선언 ... (d) 출처 없음 거부' | (a1)/(a2) 분리, writer = `search_domain`, 소비자 재배선·사본 칸. 결합 C 갈래는 새 D-DR1 행 | 1166 |
| C16 | 새 DR-1 design(없음 -- DI §2.3) | -- | 결합 C 판별 입력 = `graph.dc_current_basis`의 빈 항 MOS 행 READS(DR-1 재작성 뒤 -- as-built는 `current_basis.py:130-133`에서 정지라 빈 항 행이 아직 없다), 판별 정의, 첫 소비자 toy | 1166 (1)(3), 2348 |
| C17 | 40:1440·40:1674~1676 §6-8 D-1(`search_domain` 궤도 넘는 상자) | `search_domain` 변경(승인됨) | 같은 블록 본문에 결합 C 갈래가 더해진다 -- 묶음 상자 교집합 규칙과 순서 관계 확인(묶인 원소에 결합 C가 섞이면 선언 상자끼리 교집합) [추론] | -- |
| C18 | 40:1237 §3.8-3 | 엔진 슬루 칸 0 | 그대로(O-122) | 1166 (라) 비권고 |
| C19 | **40:2092** §10.5 held-out 정의 | 'held-out = ... 엔진 개발(코드·test 픽스처·`structure.json` 사실·**spec 값 조정**·발동표 측정)에 쓰지 않은 회로(P DEC-98 (4))' | ⚠ **충돌**: Q-CB1 권고는 erfc(held-out) 결합 C 하한을 'oracle `.tran` SR sweep 실측 경계'로 정한다(기준 θ = 원문 Table 1). 이것은 held-out의 spec 값 조정이다. 계획 1305·U-75(2478) 정의와도 같은 충돌이고, U-76 (5)('held-out 실패를 고치려고 엔진을 바꾸면 개발 회로로 옮긴다')도 걸린다(결합 C 규칙 (α)는 erfc 실패에서 나왔다). 계획 Q-CB1 행·승인 문서·`cbox_rereview.md`에 DEC-98·U-76 언급 0건 [실측]. 결정 전에 계획에서 다뤄야 한다(예: 하한 값을 erfc가 아닌 일반 유도·원문에서 / erfc를 개발 회로로 옮김 / held-out 자격 유지 근거) | 1305, 2478 |

### 2.2 대안 승인 시 자리

| 대안 | 자리 |
|---|---|
| (가) 현행 유지 | design 변경 0(C1·C2 그대로). DR-1 heldout 판정 기록의 '결정 전' 사유 문언만(계획 2352) |
| (다) 공통 하한 상향 | 40:874 값·`assets/theta_box_common.json`·42:340. ⚠ 새 상수 |
| (라) 엔진 SR 행 | 40:1237 §3.8-3(O-122 '엔진 슬루 칸 없음')·42:103 grep 기대 '엔진 슬루 칸·행 0' -- 충돌 |
| (마) front 공백 수용 | 40 §10.5 fail-closed 분류만(DI C10) |
| (바) O-144 재개 | 40 §10.5 'oracle FAIL 되먹임 없음' 문언 |
| (β) 선언 우선 | C2만(결합 C에 선언이 있으면 선언, 없으면 공통). C1의 writer 이동은 (α)와 독립이다(계획 1166 (2)는 writer 자리를 (나) 전체에 둠) |
| writer 자리 대안 '새 S0 블록' | 40 §2.4.8 새 필드 행 + `search_domain`의 `_passive_box` 잔존 -- 생산자 둘 ⚠ |
| '범위 6 (e) S1 앞 블록' | C6·C7 대신 6 (e) 블록 행에 상자 규칙 -- `dc_current_basis` READS가 층 역전 ⚠ |
| '결합 C만 S0, 나머지 로더' | C1이 둘로 갈림 -- 같은 양을 두 자리가 씀 ⚠ |
| (P) 결합 C 갈래 = SF-1 범위 9 + DR-1 같은 통합 병합 | C12에 결합 C 갈래, C13 DR-1 행 대신 '같은 통합 병합' 규칙(새 꼴), C14 결합 C toy가 SF-1 test 행으로 |

### 2.3 Q-CB2(열린 질문) -- design 자리

| 자리 | 내용 |
|---|---|
| 40:874 (a1) 보상 C 공통 상자 | Q-CB2가 결정되면 하한 출처가 바뀐다(관례 → 물리 결정자) |
| `assets/sky130_pdk_decl.json:46-53·93-96`(design 40 §3.1-1·§7 면적이 인용) | 후보 'PDK 최소 MIM'의 실현 가능성: PDK 선언에는 MIM 면적 밀도(`camimc`)만 있다. 같은 note가 '`cap_mim_m3` 셀 모델 원본은 로컬에 없다'고 적고, 엔진 `search_domain.py` 주석도 '커패시터 상자는 PDK 선언에서 유도할 수 없다(capm.* 규칙값 N/A)'라고 적는다 [실측]. 그래서 최소 MIM 후보는 PDK 선언 추가가 먼저다(Q-CB2 상정 때 실현 경로로 적을 것) |
| 마디 기생 바닥 후보 | 엔진 MNA가 이미 가진 양 -- 새 design 자리 없음(하한 규칙 문언만) |

---

## 3. design에 남은 문언 -- 두 결정과 충돌하는 곳 / 지금 고칠 수 있는 곳

### 3.1 지금 충돌(결정 뒤 고침 -- 계획 먼저 원칙)

| ID | 자리 | 충돌 | 결정 |
|---|---|---|---|
| X1 | 40:873·874·875·877, 41:1635·1648 | 상자 적용 자리(로더·θ 스키마·단계 A) 대 Q-CB1 (α)(검색 정의역 S0 블록·단계 B). 40:874의 '결합 C = 법칙 없는 AC 변수'는 계획 1166 사실('결합 C에 틀림')과 다르다. 다만 계획 DEC-105 (10)(a) 본문이 아직 같은 문언이라 design 먼저 고치지 않는다 | Q-CB1 |
| X2 | 40:2092(§10.5), 계획 1305·2478 | held-out 'spec 값 조정 금지' 대 Q-CB1 하한 값 출처(erfc oracle sweep) | **Q-CB1 결정 전 계획에서 다룰 것** ⚠ |
| X3 | 41:882·41:1759~1763 | R6 `b_ln_idu` 대상 한정 없음 -- (다)에서 종속 B 멤버의 생산자가 둘이 된다 | Q-KV1 (다) -- TB-1/LA-1 design |
| X4 | 40:449·41:1406·42:311 '쓰기 계획 다음'·X 칸·`dc_coord` 입력 | (다)·(나) 층 역전 | Q-KV1 |
| X5 | 40:1107 '② 입력 = S1v stage 번호' | 'GB5 gm 요구'가 S2 양이라 S0 쓰기 계획에서 층 역전(DI §2.5 N) -- 대안 셋 모두 고친다 | Q-KV1 |
| X6 | 41:644 '서명 불변' | (A)는 대안 (가)·(다) 모두에서 필요(계획 1165) → `order_hints` 인자 삭제 | Q-KV1 (A) |
| X7 | 40:1913 J12-f '엔진 유도·열림' | (다) 'ratified는 B 안에서만' -- ratify 후보 M21/M22가 B가 아니면 정지 | Q-KV1 (다) |

### 3.2 결정 없이 지금 고칠 수 있는 곳

| ID | 자리 | 내용 | 근거 |
|---|---|---|---|
| N1 | 42:146 D-GB1a·42:67 | '`rg "structure.json"` 0(엔진 .py)'·'로더 MISS' -- 낡음. `gmid_engine/graph/structure_load.py`(`load_structure_facts`, concept 닫힌 어휘)가 있고 엔진 .py `structure.json` 19건 [실측]. 남은 MISS는 '고리 종속 선택 concept·쓰기 계획 READS'다 | 엔진 실측 |
| N2 | 40:418·40:458·40:128 | SF-1 범위 6 (e)(v6.38.4 승인 O-173 P9-M1a) 선언 상자 추출 `spec_bounds`·`untie`·`symmetry_marks` S0 필드 -- design에 블록·필드 이름이 없다(`spec_bounds`·`B13`·'선언 상자' grep 0). 계획은 '블록·이름은 design'이다 -- S-7 몫 | 2192 |
| N3 | 41:886·41:1716·41:1761·42:315 | 'spec `search.theta_bounds`' 직접 READS → S0 필드 READS(6 (e) 승인분 -- 결정과 무관한 부분). 어느 필드인지(선언 대 적용)는 Q-CB1 몫이다 -- 41:1761은 이미 `search_domain`을 함께 READS하므로 적용 상자 하나로 줄이는 쪽이 graph 규칙 3에 맞다 [추론] | 2192 |
| N4 | 40 §11 card 표(40:2192~2203) | DR-1 행 없음(승인 O-173 BL-DR1). 선행 = IT-1 + IT-2(지금 계획)만으로도 행을 둘 수 있다 | 1231 |
| N5 | 40:449·40:1107·40:873~877·41:874·41:1406·42:311·42:340 | '계획 v6.38.5 Q-KV1/Q-CB1 대기' 표지(지금 표지는 Q-W1·Q-CF1 자리 7곳뿐 -- DI §1.1) | DI 꼴 |
| N6 | 40:874 기록 문언 | 공통 선언 `record`가 '**engine 보상 커패시터** θ 상자'라고 적는다. 결정 원문의 대상이 보상 C였다는 사실(계획 1166 사실)을 design이 이미 담고 있다는 표지만 남긴다(규칙 변경은 X1) | 1166 |

---

## 4. 승인 문서(`plan_v6385_approval_items.md`) 'design 반영 자리' 칸 대조 -- 틀린 곳 목록

### 4.1 Q-KV1 칸(승인 문서 150행)

| # | 승인 문서 문언 | 판정 | 바른 내용 |
|---|---|---|---|
| A1 | '41:874·1406 E11('쓰기 계획 다음 S0 블록' → '쓰기 계획 앞')' | **부분 틀림** | '쓰기 계획 다음' 문언은 40:449·41:1406·42:311에 있다. 41:874에는 없고, 41:874에서 바뀌는 것은 ''제외' = R13 X' 대응이다(K12) |
| A2 | '41:898·1318' | 과대(변경 불요 [추론]) | 898(처리 자리)·1318(B 정의)은 내용이 그대로다. 실제로 바뀌는 곳은 41:882·41:1759~1763(K14·K15 -- 종속 B와 R6 생산자) |
| A3 | (없음) | **누락** | 40:462 쓰기 계획 필드 행(K2) |
| A4 | (없음) | **누락** | 40:905~913 `structure.json` concept 표에 고리 종속 선택 concept가 없음(K9) -- (A) 'ratified 로더 READS'를 받을 자리 |
| A5 | (없음) | **누락** | 40:1913 J12-f와 (다)의 상호작용(K10) |
| A6 | (없음) | **누락** | 41:644 IT-1 test interface 서명(K11) |
| A7 | (없음) | **누락** | 40:1780 R14·40:2162 U4·40:2174 U15(O-149)(K5~K7) |
| A8 | (없음) | **누락** | 42:311 D-TB1a(K20)·42:67(K22)·41:1521·1698·1722의 'X' 기호(K17)·41:1277(K19) |
| A9 | 'R13 X 칸 제거'(자리 없음) | 자리 미기재 | 40:449·41:874·41:1406·41:1521·41:1698·41:1722·42:311 |
| A10 | card 순서 칸 'TB-1 design·HC-D design 재작성' | **틀림** | TB-1 design은 40·41 안의 절이라 '개정'이다. HC-D design은 아직 없다(42:312 '미작성', `docs/02-design/features/headroom-chain*.design.md` 0개 [실측]) -- '작성 때 반영'이다. R-1′ 필드 **형식**은 종속 멤버 선택에 의존하지 않고 값만 바뀐다 [추론] |
| A11 | 대안 칸 '(가) ... 고리 {M14a, M14b, M16, M9b}에서 다이오드 둘이 θ 독립 좌표' | 승인 문서는 맞음 -- **계획 1165가 다름** | 계획 1165는 같은 자리에 '{M11a, M11b, M15, M9a}'를 적었다. 그런데 바로 앞 문장이 '(가)의 모순은 M9b·M18b 고리(F 확신도 상)에서 성립'이라, 예시 고리는 M9b 고리여야 맞다. M9a는 F/B 경계(확신도 중하)다 → 계획 문언 정정 대상 |

### 4.2 Q-CB1 칸(승인 문서 166행)

| # | 승인 문서 문언 | 판정 | 바른 내용 |
|---|---|---|---|
| B1 | '40 §3.1-1·42:340 D-TBX' | 맞음, 단 핵심 충돌 미기재 | 40:873(로더 → θ 스키마 결과)·40:875(`zero_cancel_box` θ 스키마 호출)·40:877('단계 A')가 (α)와 정면 충돌한다(C1·C3·C4) |
| B2 | '검색 정의역(`search_domain`) 블록을 다루는 design 절' | 자리 불명 | 전용 절은 없다. 자리 = 40:418·40:458·40:1440·40:1674~1676(C6·C7·C17) |
| B3 | '사본 칸 `StartView.theta_bounds` 삭제 자리' | 자리 없음 | design에 `StartView` 0건. 40:392 §2.4.7 `StartContext` 행에 더해야 한다(C8) |
| B4 | (없음) | **누락** | 41:886·41:1716·41:1761·42:315 -- R6·층 0이 V_R 구간을 spec에서 직접 읽음. 완료 조건 'spec 직접 읽기 0'에 걸린다(C10). 계획 소비자 목록에도 없음 |
| B5 | (없음) | **누락** | 41:1635·41:1648 '단계 A 거부'(C11), 40 §11 SF-1 행(40:2194)·DR-1 행 부재(C12·C13), 41:2029 test 행(C14), 파일 겹침 `macro_poles.py`(LA-1 15 (g))·`achievability.py`(WB-1)(C9) |
| B6 | (없음) | **누락 ⚠** | 40:2092 §10.5 held-out 정의와 하한 값 출처의 충돌(C19·X2) |
| B7 | (없음) | 누락 | 계획 1166 (2) 본문 순서에 (b) 영점 R·(c) DC 경로 R 갈래가 없다 -- design C3에서 드러나는 계획 공백 |

---

## 5. graph 단일 정본 규칙 점검(이 보충의 권고·지적 기준)

| 항목 | 결과 |
|---|---|
| 규칙 1(writer 하나) | ⚠ X3: (다)에서 종속 B 멤버 ln IDu의 생산자가 R6과 커널 둘이 될 수 있다 -- design에서 R6 대상 한정이 필요하다. ⚠ C3: `zero_cancel_box`를 θ 스키마가 부르면 적용 상자 생산자가 둘이다 |
| 규칙 2(새 cache·사본 0) | C8 사본 칸 `StartView.theta_bounds` 삭제는 계획과 같다. 이 보충의 지적에는 새 칸 0 |
| 규칙 3(정의 축) | C7: 선언 상자 대 적용 상자. K1: X 칸 삭제(`dc_coord.role`과 같은 정의) |
| 규칙 4(참조 전달) | C10: R6이 spec 대신 적용 상자 필드를 READS |
| 규칙 6(정본 자리 없으면 멈춤) | K9: ratified 고리 선택 concept 자리가 없다 -- (A) 구현 전 design에서 정해야 한다(없으면 S-7 멈춤 대상) |
| 회로 이름 | 지적 문언의 소자 이름(M11a 등)은 실측·예시에만 있다. 규칙에는 0 |

## 6. 한계

- [추론] 표시(K2 tie-break, K10, K11 호환, K14·K15 R6 대상, K17 E-0 자리, A2 변경 불요, A10 형식 불변, C11·C17)는 실행 실측을 하지 않았다.
- 엔진 줄 번호는 `wt/design-v115`(master 병합본) 기준이다. 계획이 인용한 integ/it12 `b3336452`와 `iv_context.py:94`·`start_values.py:180`·`macro_poles.py:133,141`·`achievability.py:126,248`·`iv_area.py:85`·`_helpers_area.py:24`는 같다(계획 6 (e)의 `iv_context.py:93`은 `search = spec.search` 줄이고, :94가 상자 읽기 줄이다).
- headroom-chain HC-D design·DR-1 design·DE-1 design은 아직 없어서, 그 design이 받을 영향은 계획 문언에서 유도했다.
