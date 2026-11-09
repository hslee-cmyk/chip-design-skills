# 독립 검증 -- M1~M6·M8·M9 card 초안 + m_cards_plan.md의 gate master 2183f2e 갱신

작성 2026-10-06. 검증자(작성자 아님). 실제 저장소 읽기 전용(`git -C` 읽기·`clone --no-local`·`archive`만). 스크래치 `C:/g352`만 썼다(TMP/TEMP 그 안, `clone -c core.autocrlf=false`, cd 없음, 끝에 삭제).
실제 저장소 시작·끝: HEAD `6c724de`, `status --porcelain` md5 `76eea762…` 같음, reflog 새 항목 없음.

## 판정: **B 0 · S 0 · minor 5** -- 갱신은 근거와 맞고, 관찰 가능한 계약은 8개 모두 그대로다.

## (1) '관찰 가능한 계약' 바이트 같음 -- 8/8 PASS

`## ` 머리로 절을 나눠 backup(`*.pre-2183v.bak`)과 비교: m1 7286·m2 5603·m3 4821·m4 5407·m5 4644·m6 4590·m8 6730·m9 7552바이트, 모두 **바이트 같음**. 머리 블록(frontmatter)·절 목록·순서도 8개 모두 같다.

## (2) diff 범위

| 파일 | 바뀐 절 |
|---|---|
| m1 | 재현할 수치 |
| m2 | 의도(착수 조건 줄)·**판정 유형 근거**·재현할 수치·작성 전 실측 |
| m3 | 재현할 수치·결정 필요 항목(B26-1 계수 test 줄 -- `load_topology` 새 줄 범위 덧붙임)·작성 전 실측 |
| m4·m5·m6·m8 | 재현할 수치 |
| m9 | 의도(SD 파일 끝 행 줄)·재현할 수치 |
| m_cards_plan | §1만(표 M2 행 315→302, 합 12,384→12,371, 재측정 단락 추가) |

모든 변경은 '(gate `2183f2e` 사슬 …; `4a286f0` 사슬 …)' 형식의 덧붙임이거나 값 교체다. 계약·oracle·거부 입력·무발동 절은 손대지 않았다. 예외 1건 = m2 '판정 유형 근거'(아래 minor m-1).

## (3) 독립 재측정(사슬 `C:/g352/r`)

빌드 = `build278.sh` 인자판 직접 작성(REV `2183f2e`, qtok 단계 없음 -- 계획 521행에 토큰 이미 있음), `g1_kit/install_proto.py`(md5 `733d173f…`)·`g1_core.py`, `move_plan_sim.py` md5 `affb8694…`, `MP_STMT_KEY=names`·`PYTHONHASHSEED=0`.
`2183f2e` → FU(DR 27행 뒤·ACF 37행 뒤) → T0 W-1(1·3·1) → G1 **'installed 4'** → D0a → D0b 재생성(one 354·multi 0·nested 7·nounit 18) = M1 base `03caece`. 그 뒤 `chain226.py`(경로만 `C:/g352`) 전체판으로 M1~M9 8 card.

* D0b 전 `plan` exit 1: `reg_mismatch` 80, 배정 403 = A-1 61·A-2 38·A-3 1·A-4 235·A-5 57·A-6 7·A-7 2·A-K 2. M1 base `plan` exit 0, 일곱 목록 0, A-1 61·A-2 39·A-4 245·A-5 53·A-6 3·A-K 2, MOD 분포 8·18·82·104·21·11·30·16·SD 잔류 111·ACF 2 -- 같음.
* card별(단위/규칙/check/moved u·d/G1 V3/G1 없는 def·변이/IMPORT-ANY/LAYER/`mod_imports`/E3b/W-2/W-1) -- **8 card 모두 초안 값과 같다**:
  M1 8·A-1 6 A-4 2·0·8/22·0·0·22·590·6/6/0·0·3/0·SR 8/46 FAIL 9=9 새 0·W-1 77/48;
  M2 18·A-4 12 A-1 3 A-5 3·0·18/16·0·0·16·**302**·7·0·5/0·SR 7/1 9=9, **SD 10/2** 0=0, ACF 1/0·W-2 ok·78/49;
  M3 82·0·82/100·0·0·100·3052·8·0·8/0·SR 43/22 9=9, **SD 39/27** 0=0·131/54;
  M4 104·126·3999·9·10/0·SR 97/26·TL 7/3·215/60; M5 21·23·711·10·9/0·SR 21/9·230/60; M6 11·14·333·11·5/0·SR 11/7·245/60;
  M8 30·58·3077·12·13/1·SR 30/37·304/60; M9 16·16·307·13·**LAYER 2**·8/1·SD 8/10·DR 6/5·ACF 2/0·W-2 ok·315/61.
* 파일 줄 수: `topology_authoring.py` **587**, `circuit_state_graph.py` **4801**, `sizing_layout_convergence.py` **3994**, M9 병합본 SD **4971**(끝 줄 = `from instance_report_builder import …` 재수출) -- 같음.
  원본(2183f2e) SR 12014·SD 9010(4a286f0/7243f28: 12015·9024), SR blob `2a7a1a04` -- 같음. `7243f28..2183f2e` `tools/` diff 0 -- 같음.
* **줄 범위: 290단위 전부**(M1 8 + M2~M9 282) 초안 '재현할 수치'와 card base `gen` span이 **일치**. 그중 12단위는 card base 파일을 `ast`로 직접 다시 재서 일치(`find_idiom_matches` 1060~1077·`find_stack_edges` 1080~1089·`audit_theta_root_direction` 3323~3394·`apply_theta_kcl_gap_fill` 3765~3817·`load_topology` 8121~8310·`_theta_feed_footprint` 8874~8910·`_hr_resolve_vertical_group` 5447~5946·`make_matching_feasibility_check` 1829~1897·`repair_infeasible_baseline` 3492~3661·`resolve_stack_layout` 664~772·`run_topology_pipeline_with_finger_fixup` 4569~4697·`save_instance_json` 5125~5176).
* 옮겨진 단위 수(backup→현재 범위 차): M2 SD 9(−1~−14), M3 SD 37(−1~−3)·**SR 9**(−1), M4 SR 9, M5 SR 1, M6 SR 6, M8 SR 27(−1) + `resolve_stack_layout` 끝 −1, M9 SD 8(−2).
  **M3 SR = 9가 맞다**(초안 9 맞음; 원자료 `m_cards_at_2183.md` §3의 "SR 10개"가 틀림).
* card base/head 길이 실측: SR 12014→11397(M1)→11264(M2)→10067(M3)→6079(M4)→5097(M5)→4697(M6)→43(M8); SD 9010(M1·M2 base)→8606(M2 head)→5176(M3 head~M9 base)→4971(M9 head).

## (4) M7

`draft_p3_m7.spec.md`는 **없고, 만들면 안 된다**: design 30 §8 M7 행(`2183f2e` 616행) "M2·M3·M9에 흡수(빈 card 금지)", card 수 17(622행)에 M7이 없다. 2183f2e 사슬 M1 base `plan`에서 MOD7(`stick_diagram.py`) 잔류 **111단위**, `split` 파일 중 SD 밖 MOD7 배정 0이라 흡수 근거(m_cards_plan §1 표 (M7) 행 "SD에 111단위 잔류")도 그대로다. B34는 기존 def 4개 본문만 줄였고 단위를 더하거나 빼지 않았다. **갱신할 것 없음.**
(9번째 card = M10 `20261006-p3-mod10-entry`는 이미 `2183f2e` 판으로 새로 써졌다(backup 없음) -- 이번 갱신 대상 밖.)

## (5) parse_spec_card(gate `6c724de` `tools/gates/role_paths.py`, `git archive`)

M1~M6·M8·M9·M10 9개 모두 **OK**(머리 id로 `expect_id` 재호출도 OK). 공통 `phase 3`·`gate_change no`·approval `20260930-30-module-split-design`, evidence_type M1~M9 `equivalence`, M10 `red-green`. 절 11개, '관찰 가능한 계약'·'신규 시그니처' 둘 다 있음(`interface_card.py` 요구 충족). m7: 파일 없음(위 (4)).

## (6) 추가 요청 -- D-11(`29d2fc2`) 뒤 배정이 M1·M4·m_cards_plan에 반영되었는가

**반영되어 있다 -- 낡은 문장 없음.** `g1_at_6c7.md`의 M1 5→8·M4 93→90은 G1 card의 order sim 원자료(D0b 재생성 전, `m9_measure`) 값이다. M card 수치는 처음부터(r1, `4a286f0` + `variant.py qtok`) 토큰을 넣은 D0b 재생성 사슬로 쟀고, `2183f2e`에서는 계획 521행에 토큰이 이미 있다(`29d2fc2`는 2183f2e의 조상, 4a286f0의 조상 아님).
이번 재측정(토큰 들어간 판)도 M1 8단위(A-1 6·A-4 2)·def 22·G1 없는 변이 590, M4 104단위·def 126·변이 3999로 초안과 같다.
토큰 전 값이 남아 있는 줄은 모두 이름표를 단 이력이다: m1 216행(`<stmt:해시>` 키 판 A-1 60·A-4 229 -- "이 수치는 시제품 `<stmt:해시>` 키 값이다"), m1 218행·m_cards_plan 48행(토큰 없음 `be9f83e` MOD1 7단위), m_cards_plan 7행(r0 M4 102 등). 바꿀 문장 없음.
(order sim 값 M1 8·22·23·610 / M4 90·100·100·2,930은 G1 card 초안 몫이다 -- 이 검토 범위 밖.)

## minor(5) -- 하나도 계약·판정에 영향 없음

* **m-1** m2 '판정 유형 근거' 62행("V3 규모 … 변이 302(gate `2183f2e` 사슬 관찰 …)")도 바뀌었다 -- 보고한 절 목록 밖이다. 값은 실측과 맞으니 내용 문제는 아니고, 보고 목록에 이 절을 더하면 된다.
* **m-2** m2 '작성 전 실측' 10 R-5 줄(148행): "`-future` … G1 정적 V3 대상 def 16·변이 315·거부 18" -- `4a286f0` 원자료(`neg.jsonl`)의 값인데 이름표가 없다. 같은 16 def라 `2183f2e` 판이면 **302**다. 다른 R행처럼 "(`4a286f0` 사슬; `2183f2e` 사슬 302)"를 붙이면 된다(R-5는 G1이 모든 def를 거부하는 판이라 G1 없는 수와 같다 -- 추정, 거부 판 재실행은 안 했다).
* **m-3** m2 95행 "M2 base SD 8609 → 8606줄" -- 8606은 M2 **병합본(head)** SD다. M2 base SD는 **9010**(M1은 SR만 고침). → "M2 병합본 SD 8609 → 8606줄"(원자료 `m_cards_at_2183.md` §3-2의 같은 표기에서 옮김).
* **m-4** m8 100행 "그 뒤 SR 단위 28개 줄 범위 −1행" -- 실측 **27개**(`resolve_stack_layout` 뒤 `_HeadroomTopoEnv` … `run_topology_pipeline_with_finger_fixup`); 28은 `resolve_stack_layout`(끝 −1)을 넣은 수다. → "그 뒤 SR 단위 27개"(원자료 §1의 "28개"도 같은 실수).
* **m-5** 원자료 `m_cards_at_2183.md`(초안 아님): §3-1 M3 "SR 10개" → 9개, §3-2 "SR 11398 → 11397(M1 base)"는 M1 **head** 값(M1 base SR 12014). 초안이 이 표기를 따르지 않았는데, 따른 곳은 m-3·m-4 두 군데뿐이다.

## 격리

`C:/g352` 삭제함(확인). 실제 저장소 HEAD `6c724de`·porcelain md5 `76eea762…` 시작과 같음.
