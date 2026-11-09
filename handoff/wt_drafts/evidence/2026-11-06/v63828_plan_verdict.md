verdict: Major 3

# 계획 v6.38.28 (O-249 + A-145) 독립 판정 (2026-11-06)

판정자 = 독립 판정 agent(작성자 아님). 대상 = worktree `wt/20261106-plan-v63828`(브랜치 `plan/v63828`, 머리 `c3129a4a`). 작성 diff = `f1dd8f52..4d57d9d4`, 병합 충돌 해소 = `4d57d9d4..c3129a4a`. 문서: gain-budget plan v6.38.28(+history), graph-consumption v0.14.11(+history), oracle-portability v0.6.33(+history), design 40·41·42 v1.16.25(+design history). 기준: O-249(`user_decisions.md` 마지막 행), A-139·A-144·A-145(`la1_auto_decisions.md`), 근거 파일 다섯(`off_principle_question.md`, `..._validation.md` m1~m4, `off_rules_audit.md` 인용만, `off_rules_contradiction_check.md`, `lm1e_card_verdict.md` 재판정·재판정 2).

방법: `git -C … show/diff/log`와 grep만 썼다. 문서는 `C:/Users/HSLEE/AppData/Local/Temp/la1s_v28v/`에 뽑아 읽었다(`gb_head.md`·`gb_base.md`, 줄 단위 word diff `*.wd.txt`, 키워드 문맥 `gb_kkeo.txt`·`gb_misc.txt`·`gc_k.txt`·`op_k.txt`·`d4?k.txt`; 스크립트 `wd.py`·`kw.py`·`seg.py`). 줄 번호 P = gain-budget plan `c3129a4a` 기준. worktree 수정·커밋 0, test·ngspice 0.

## Major

### M1 -- mismatch tol 둘째 결합 구현 삭제가 '가능하면'으로 약해짐 (A-145 (3)과 다른 문언, graph 규칙 3 누출)
- **자리**: P:2653 LM-1e 3b (i) «가능하면 `table_at`을 재사용해 둘째 결합 구현을 지운다», P:2656 완료 (1) «`table_at`을 재사용했으면 둘째 결합 구현 정의 `git grep` 0», P:664 표 10행 (i)은 '같은 결합'이라고만 적고 삭제를 적지 않음.
- **사실**: A-145 (3) 원문은 «LM-1e 재작성 범위에 넣고 `table_at` 재사용으로 둘째 결합 구현 삭제(graph 규칙 3)»다(조건 없음). design 40 :1259(v1.16.25)도 «`table_at` 재사용으로 둘째 구현을 지운다»로 조건이 없다. card 개정 3(`ddd73c62` spec :38·:181)도 조건 없이 재사용·삭제한다. 계획만 '가능하면'과 조건부 완료라, 같은 결합 규칙의 둘째 구현이 남아도 완료가 되는 문언이다(같은 정의 = 한 자리, graph 규칙 3).
- **고칠 방법**: 3b (i)의 '가능하면'을 지우고 «`table_at`을 재사용해 둘째 결합 구현을 지운다(셀 값 접근 꼴은 card)»로 쓴다. 완료 (1)을 «`TolMismatchTable.at` 안 셀 결합 구현 0(`table_at` 호출) -- `git grep`»으로 조건 없이 쓴다. 표 10행 (i) mismatch 괄호에 '둘째 구현 삭제 -- 재작성 = LM-1e 3b'를 더한다.

### M2 -- LA-1 계산 표의 '반전 하한'이 정본 (10)·DEC-107·같은 card의 O-207 묶음과 모순
- **자리**: P:2086 card LA-1 '계산 단계별 원칙 점검표' ln IDu·ID 행, 물리 정합 장치 칸 «LUT on_mask 정의역·단조 검사(…)·**반전 하한**».
- **사실**: 정본 (10)(P:689)은 «DEC-88 '반전 수준 하한(정점) 연속 부등식 제약'(P-7)을 지운다 -- … 바닥은 LUT 정의역»이고, 같은 card의 O-207 묶음(P:2060)과 완료 8(P:2116)은 `CON_INVERSION`·`_peak_floor`를 지운다. DEC-107(P:307)·정본 (0)(P:679)은 gm/ID 정점 문턱으로 정의역·탐색 상자를 자르지 않는다고 적는다. 그런데 LA-1이 구현할 표가 반전 하한을 물리 정합 장치로 남긴다. 작성자는 이것을 history 'v6.38.28' «고치지 않은 낡은 의심 문언»에 '결정 문언이 아니라 손대지 않음'으로 남겼다. 이 칸은 결정 기록이 아니라 card 규칙 칸이다. 원칙 19(원리 추가 뒤 낡은 문언 전수 대조)에 따르면 고칠 대상이다.
- **고칠 방법**: '·반전 하한'을 지우고 «(바닥 = LUT 정의역 -- 정본 (10), 반전 하한 없음 -- O-207·DEC-107)»로 쓴다. history 'v6.38.28'의 '고치지 않은 낡은 의심 문언'에서 이 항목을 '바꾼 자리'로 옮긴다.

### M3 -- 표 9행 (ii)에 더한 'DC 전류 0 triode 스위치는 KCL 항등 0 예외가 받는다'가 그 예외의 적용 범위와 모순 (판정 내용이 바뀐 것으로 읽힘)
- **자리**: P:663 표 9행 (ii) 새 괄호 «DC 전류 0인 `triode` 스위치(예: 게이트만 구동하는 경로의 pass 소자)는 아래 KCL 항등 0 전류 MOS 예외가 받으므로 '0 전류라 거부'가 아니다».
- **사실**: 같은 행의 예외 정의(정의 자리 = 이 행 하나)는 «KCL 항등 0 전류 MOS … 는 **(i)과 oracle 포화·비전도(방향 위반) 판정**의 대상 밖»이다. 엔진 (ii)(`triode` 선언 MOS의 선언 방향 ID ≤ 0 = 선언 오류 거부)는 적용 범위에 없다. EO-1 완료 (c)(P:2279)의 «`triode` 선언인데 비전도(방향 위반) … 인 toy는 거부»에도 예외가 없다. 그래서 지금 규칙에서 ID = 0인 triode 스위치는 거부된다. 새 괄호는 그 반대를 적었다. 이 괄호를 그대로 읽으면 예외 범위가 (ii)까지 넓어진다. 그러면 O-249 Q3 '현행 유지'와 다른 판정 변경이고 거부 갈래 축소(기준 완화 쪽)다. 문언의 출처는 A-145 (1) m4다(검증 m4 «DC 전류가 0인 닫힌 스위치는 KCL 항등 0 예외(표 9행)가 받는다»). 그 전제가 표 9행 정의와 맞지 않는다.
- **물리**: 켜진 triode 스위치는 VDS = 0이면 ID = 0이다(채널 전도). 지금 규칙이 이것을 거부하는 것은 거짓 거부다. 다만 fail-closed 쪽이고 발동은 0(library `triode` 선언 0/13, 감사 인용)이다. 실제 문제이므로 LA-1 재점검 입력(Q3)이 맞다.
- **고칠 방법**: (가) 권고 -- 괄호를 «KCL 항등 0 예외는 (i)·oracle에만 적용되고 (ii)에는 적용되지 않는다. 그래서 연결상 DC 전류가 0인 `triode` 스위치는 지금 규칙으로 선언 오류 거부(거짓 거부, fail-closed)이고, 발동 0이며 LA-1 재점검에서 잰다»로 고친다. 이렇게 하면 Q3 '현행 유지'와 맞는다. 오케스트레이터는 A-145 (1) m4 기록의 전제를 정정한다. (나) 예외 범위를 (ii)까지 넓히는 안은 거부 축소라 위임 밖이다(기준 약화 -- 사용자 결정 필요). 이 판에서는 택하지 않는다.

## minor

1. **P:290 DEC-90 (1)** «(O-50 G3 'ID ≤ 0 = 꺼짐' 유지)»는 이름 교체 바로 뒤에 '꺼짐'을 유지한다고 읽힌다. «(O-50 G3 'ID ≤ 0' 판정 유지, 이름 O-249)»로 고친다.
2. **P:2155** design 정정 표 oracle-portability design v0.3.10 행 «oracle 포화 (ii)·꺼짐 판정에서 KCL 항등 0 MOS 제외»는 지금 효력이 있는 정정 지시인데 이름이 바뀌지 않았다. '비전도(방향 위반)'로 바꾼다.
3. **graph-consumption :312** N3.2 `dc_off_current` 행 «oracle 꺼짐 = 채널 op ID ≤ 0»도 이름이 바뀌지 않았다(정정됨 표지 없는 행).
4. **P:1370** N6.1 GC-2 칸 «GC-2 g = s 꺼짐 분류·정지 이전»은 O-210 RR-6(꺼짐 분류·정지 삭제)과 graph-consumption :119(판정식 결과만 옮김) 대비 낡은 문언이다. v6.38.28 이전부터 있었다. «GC-2 g = s 판정식(S1) 결과 이전»으로 고친다.
5. **선언 없는 깊은 약반전 소자를 '꺼짐/꺼진'으로 부르는 서술**: DEC-105 P:305(«꺼진 영역 모서리»), U-134 P:2888(«VGS = 0 누설, 셀 꺼짐»·«꺼진 소자 gm의 포락»·«꺼짐 모서리»), design 40 :913, design 41 :902·:915. 판정이나 문턱으로는 쓰이지 않는다(서술). 그러나 정본 (0)의 «'꺼짐'·`off`는 선언된 `off` 소자에만 쓴다»와 용어가 부딪힌다. '깊은 약반전(ID ≤ …)'으로 바꾼다(이번 판이나 LA-1 재점검).
6. **P:2653 'LA-1 차단 판정'**: mismatch tol(과 잡음 tol)을 (i) '차단'에 넣은 것은 A-145 (3)('표 10행 (i) 범위 안')·표 10행 (i)과 맞는다. LM-1e는 어차피 LA-1 앞(표 #24)이라 순서도 그대로다. 다만 (i)의 차단 근거 «봉인 허용오차·SCC 수렴 tol 입력»은 mismatch·잡음에 해당하지 않는다. 그 둘의 근거(판정 제약 분해능 입력 -- None을 버리면 분해능이 실제보다 곱게 보이는 fail-open 쪽)를 한 줄 더한다.
7. **DEC-107(P:307)과 정본 (0)(P:679)**: 원리 문장을 두 자리에 거의 그대로 적었다. 이 계획의 관례(DEC-90 (1) = 정의 자리 (6)을 가리키며 정의를 다시 적음, DEC-103·DEC-104 = 원리 전문)와 같다. DEC 행은 '정의 자리 = (0)(다른 자리는 인용)'을 적었다. 내용 모순은 0이다(DEC-107에는 (0)의 역할 셋·용어 한정 문장이 없을 뿐). 규칙 3 위반으로 보지 않는다. 표류를 막으려면 DEC 행을 요지 + 가리킴으로 줄이는 안이 있다(선택).
8. **Status 줄(P:11)** '원래 취지와 다름' 괄호에 (5) `current_box` 거부 삭제 선행 조건이 빠졌다(history 'v6.38.28'에는 있음).
9. **A-139 (4) 과도기 예외 기록**: 계획 표 10행 (ii)·3b (ii)와 D40 :1259에는 기록됐다. 모순 점검 (b)가 권한 `la1_auto_decisions.md` 기록은 없다(grep '과도기' 0). 오케스트레이터 몫(계획 밖).
10. **P:663 표 9행 (ii)** 괄호에 실측 서술('library `triode` 선언 0/13')이 있다. 원칙 25상 history 쪽이 맞다(경미).
11. **P:2027** [정정됨] 후속 정정 표 행의 «`conduction_mask`(탐색 격자)와의 관계를 적음»은 기록 행이라 효력은 없다. 그래도 철회 표지를 한 줄 달면 오독을 막는다(선택).
12. **card LM-1e 개정 3(`ddd73c62`) 대 v6.38.28**(볼 것 6): 아래는 card 착수 조건 7을 닫을 때 card에서 고칠 것이다.
    - (가) table_at 재사용 삭제: card는 조건 없이 지우고, 계획은 '가능하면'이다. M1로 계획을 card·D40에 맞추면 차이가 사라진다.
    - (나) card 원래 취지와 다름 5(손실 원인 '잡음 tol'·'mismatch tol' 추가)·6(전도 하한 범위 밖): 둘 다 '계획 v6.38.27과 다름'으로 적혀 있다. 그런데 v6.38.28이 둘 다 계획에 넣었으므로 더는 다른 점이 아니다. 상태 머리의 '계획 v6.38.28(작성 중)' 문언과 함께 갱신한다.
    - (다) 계획 3b (ii) '과도기 예외'(LM-1e ~ LA-1 사이 `_conduction_floor` '정의된 항만')가 card 관찰에 없다. 계획은 'toy·완료 대상 아님'이므로 card에 관찰 한 줄만 더하면 된다.
    - 그 밖(호출자 표 `cell_floor.py:69` 범위 밖·변경 0, `device_sigma.py:27`, 잡음 경로 unmeasured, 완료 정의 1곳)은 v6.38.28 문언과 같다.

## 볼 것별 결과

1. **O-249·A-145 반영**: 원리 문장(DEC-107·정본 (0)), 용어 교체, 전도 하한 몫 철회, `conduction_mask` 신설 철회, GC-7 축소, A-139 (4) 과도기 예외, `current_box` 값 동일 실측 선행, KCL 0 예외 인용·다리 밖 정지, U-122 비결정, Q2 LA-1 O-207 묶음(범위 P:2060·완료 8 P:2116·`sctx.cell_floors` 소유 P:2078), Q3 현행 유지가 모두 들어갔다. 검증 m1(history에 `:41-51`), m2(P:2653·P:664·P:2078·D40 :1259), m3(정본 (7) P:686), m4(P:663 -- 단 M3)도 들어갔다. A-145 (2) C-1과 (3) 잡음·mismatch(표 10행 (i)·3b·완료 (1)·`device_sigma.py:27`·원인 분류)도 들어갔다. 다른 점: M1('가능하면'), M3(m4 전제). 원래 취지와 다름은 history·각 자리에 표지됐다(Status 누락은 minor 8).
2. **'꺼짐' 교체**: 바꾼 자리(history 'v6.38.28' 목록, 판정자가 diff로 대조)는 모두 부호 판정 결과(선언 없는·`triode` 선언 소자의 선언 방향 ID ≤ 0)다. 선언된 `off` 소자의 꺼짐(정본 (5)·(바) O-h·N3.8 `judged_by`·offset-trim 의도적 꺼짐, oracle :439·:557 `off` 경로)은 그대로다. 남긴 목록은 맞다. 다만 바뀌지 않은 부호 결과 자리 셋(minor 1·2·3)과 약반전 서술(minor 5)이 남았다. 판정 내용이 바뀐 자리: M3 하나(새 괄호가 예외 범위를 넓히는 것으로 읽힘). 그 밖은 0이고, 기준 약화 문언도 M3 말고는 0이다.
3. **계획 전체 grep**(`conduction` 23·`전도 하한` 19·`cell_floor` 14·`on_mask` 18·`conduction_mask` 5·`GC-7` 10·`GD-12` 1·`U-G4` 3·`꺼짐/꺼진/꺼지` 106·`TolMismatch` 4·`table_at` 8·`_conduction_ok` 5): 이중 배정은 0이다(N6.1 GC-7 칸이 LA-1 O-207 묶음으로 옮김, graph-consumption GC-7 = 순수 리팩터링, GD-12 철회 -- graph-consumption 전수 grep으로 확인). 낡은 문언·모순은 M2(반전 하한)와 minor 1~5·11이다.
4. **작성자 의문**:
   - (a) DEC-107과 정본 (0): 기존 관례와 같아 규칙 3 위반 아님(minor 7).
   - (b) mismatch '차단': A-145·표 10행과 맞음. 근거 문장은 보강 필요(minor 6).
   - (c) D41 v1.16.23 → v1.16.25: D41 마지막 커밋이 `2cdd09da`(v1.16.23)이고 v1.16.24는 D41을 건드리지 않았다(design history :1022). 세 문서가 같은 판을 쓰는 관례대로 건너뛴 것이고, design history :1021에 적혀 있다. 문제없음.
   - (d) 셋 가운데: DEC-105·U-134 = 서술 용어만 걸림(minor 5). LA-1 표 '반전 하한' = 실제 모순(M2). D41 '선언 off가 전도' toy(:792) = 그 줄 머리에 «[v1.16.3 대체 -- 4.7-W W3·W5, 이 줄의 해당 문언은 효력 없음]»이 있어 효력 있는 모순이 아니다(W3 '삭제'가 정본). 이번 판이 효력 없는 그 줄 안의 '꺼짐'을 바꾼 것은 해가 없다.
5. **병합 충돌 해소**: master v0.14.10(O-241) 내용을 잃지 않았다. N3.1-5의 fail-closed 문단과 손 분류 표 `op_copy_cleared`(:269-270)는 `4501c61f`와 같다. history 0.14.10 행은 master `d3782917`과 md5가 같다. Status는 v0.14.11 → v0.14.10 → v0.14.9 순서로 이어진다. 0.14.11 행에서는 '이 브랜치 base … 없어' 문구만 지웠다.
6. **LM-1e card 개정 3 대 v6.38.28**: minor 12. 실질 차이는 M1 하나(계획이 card보다 약함)다.
7. **원칙**:
   - 물리 정합: M3 괄호의 물리 사실(켜진 triode 스위치의 ID = 0)은 맞다. 다만 규칙 적용 범위를 잘못 적었다.
   - graph 단일 정본: M1(둘째 결합 구현이 남을 수 있음). 새 필드·cache·사본 0, `conduction_mask` 둘째 필드 철회는 맞다.
   - fail-closed: 잡음·mismatch None 경로는 unmeasured·`extra = None`로 맞다. 과도기 예외는 탐색 상자를 넓히는 쪽이고 판정은 아니다.
   - 상수 발명 0, 회로 이름 0(새 문언 기준).
   - 계획서엔 규칙만: minor 10.
   - O-229: 새 test·인프라 0.

## 재지 않은 것 (통과로 세지 않음)
- test·ngspice 0. 엔진 파일 줄(`mismatch_tolerance.py:34-47`, `device_sigma.py:27`, `cell_floor.py:69`, `derived_fns.py:41-51` 등)은 직접 열지 않았다. `lm1e_card_verdict.md`·검증 파일 인용이다.
- 계획 전문은 읽지 않았다. diff 전체와 위 키워드 grep 문맥만 읽었다. 키워드 밖의 낡은 문언은 재지 않았다.
- `off_rules_audit.md` 원문(39행 분류), headroom-chain 계획(DEC-107 영향 칸에 없음), oracle-portability design 본문은 대조하지 않았다.
- graph-consumption의 'VGS = 0 누설 술어 소비자 0'(:262) 주장: `current_box`가 I_off 값을 쓰는 것과 구별되는지(술어 대 값)는 문언으로만 봤다.
- KCL 항등 0 집합에 실제 `triode` 소자가 드는 회로 수는 재지 않았다(감사 인용 0/13).


## 재판정 (둘째 커밋 `31da8ff5`, 부모 `c3129a4a`, 2026-11-06)

re-verdict: Major 0

- **대상과 기준**: `git -C wt/20261106-plan-v63828 diff c3129a4a 31da8ff5`(gain-budget plan·history, graph-consumption plan·history 네 파일만 바뀜). 위임 A-146(`la1_auto_decisions.md` 마지막 행).
- **방법**: 앞 판정과 같다(읽기·`git show`/`diff`/`grep`, 줄 단위 diff `la1s_v28v/r2.txt`·`r2gc.txt`·`r2h.txt`·`r2gh.txt`). 이번에는 엔진 소비자 네 파일(`metrics/device_sigma.py`, `metrics/offset_analysis.py`, `metrics/noise_integral.py`, `search/ss_constraints.py`)과 경로상의 `metrics/mirror_ratio.py`·`metrics/metrics_aux.py`를 `31da8ff5`에서 직접 열었다(원칙 8 -- 외부 사실·재작성 범위 대조 용도).
- **실행·수정**: 실행 0, 수정·커밋 0.

### Major 해소

- **M1 -- 해소.**
  - P:2653 3b (i): «`table_at`을 재사용해 둘째 결합 구현을 지운다(같은 규칙 하나; 셀 값 칸 접근 꼴은 card)» -- '가능하면'이 없어졌다.
  - P:2656 완료 (1): «`TolMismatchTable.at` 안 셀 결합 구현 0(`table_at` 호출 -- `git grep`)» -- 조건 없이 걸린다.
  - P:664 표 10행 (i): «둘째 구현 삭제 -- 재작성 = card LM-1e 3b».
  - A-145 (3), D40 :1259, card `ddd73c62`와 같다. 계획 안 `가능하면` + `table_at`/mismatch grep은 0이다.
- **M2 -- 해소.** P:2086 ln IDu 행의 물리 정합 장치 칸이 «…; 바닥 = LUT 정의역 -- 정본 (10), 반전 하한 없음 -- O-207·DEC-107»이 됐다. 정본 (10)·O-207 묶음·DEC-107과 맞는다. history '고치지 않은 낡은 의심 문언'에서 이 항목을 옮긴 기록도 있다(history 'v6.38.28 둘째 커밋' M2).
- **M3 -- 해소.** 표 9행 (ii)의 새 괄호는 «아래 KCL 항등 0 전류 MOS 예외는 (i)과 oracle 판정에만 적용되고 이 (ii)에는 적용되지 않는다 -- 그래서 연결상 DC 전류가 0인 `triode` 스위치(켜진 채 VDS = 0 -- 채널은 전도)도 지금 규칙으로 선언 오류 거부(거짓 거부 쪽, fail-closed); 지금 발동 0, LA-1 재점검 …(예외 범위는 넓히지 않음 -- 기준 변경)»다.
  - 표 9행 예외 정의: 정의는 «(i)과 oracle 포화·비전도(방향 위반) 판정의 대상 밖»이고, 괄호의 범위 서술과 같다.
  - EO-1 완료 (c)(P:2279): «`triode` 선언인데 비전도(방향 위반) 또는 포화인 toy는 거부», 예외 없음 -- 맞다.
  - O-249 Q3 '현행 유지': 맞다. 판정 내용 변경 0, 기준 약화 0.
  - A-145 m4 전제 정정은 A-146 행에 기록됐다.
  - 물리 서술(켜진 스위치 VDS = 0 → ID = 0이고 채널은 전도)도 맞다.

### 함께 고친 minor (A-146 1·4·6·8 = 앞 판정 파일 번호 minor 1·2·3·6·8·10)

- **이름 셋**: P:290 «(O-50 G3 'ID ≤ 0' 판정 유지, 이름 O-249)», P:2155 «oracle 포화 (ii)·비전도(방향 위반) 판정에서 … (…; 이름 O-249)», graph-consumption :312 «oracle 비전도(방향 위반)(이름 상위 O-249)». 셋 다 맞고, 판정 내용 변경은 0이다.
- **차단 근거(P:2653)**: «잡음 tol·mismatch tol … 차단 근거는 … 판정 제약의 분해능 입력»이고, 엔진 경로와 대조했다.
  - **mismatch**: `device_sigma.py:27-32`에서 `table.at`이 None을 내면 `extra = None`이 되고, 행 tol도 None이 된다. `offset_analysis.py:117-118`은 tol None이면 `(None, None)`을 낸다. `metrics_aux.py:69·:82-83`은 `offset_in_sigma_mv`·`offset_excess`의 `MetricResult.resolution`을 그 칸에서 읽는다. `ss_constraints.py:79-81`은 resolution None이면 행 없이 `unmeasured`(`resolution_undefined`)로 둔다. **맞다.**
  - **잡음**: `noise_integral.py:150-160`에서 tol NaN이면 `lut_i = None`, `lut_v = None`이 된다. `:231`에서 `known = False`, `:246`에서 `resolution = None`이 되고, 같은 `ss_constraints.py:79-81`로 간다. **맞다.**
  - **fail-open 쪽 주장**: 정의된 셀만으로 결합하면 tol이 작아지고 분해능 s가 작아진다. 그러면 c = 여유/s와 `active` = c ≤ 1(`ss_constraints.py:86-87`) 판정이 실제보다 곱게 나온다. 이는 표 10행 (ii) b_P와 같은 논리다. **맞다.**
- **Status**: '원래 취지와 다름'에 `current_box` 선행 조건이 추가됐다. 맞다.
- **실측 서술 이동**: 표 9행 (ii)의 '0/13'이 history 'v6.38.28 둘째 커밋'으로 옮겨졌다(본문은 '발동 실측 = history …' 인용). 맞다.
- **과도기 예외**: '기록 A-146' 인용이 추가됐고, A-146 행에 기록이 있다. D40 :1259 인용은 오케스트레이터 결정대로 그대로다.

### 새 모순·기준 약화 -- 0 (minor 3)

- **r1 (mismatch 경로 한 갈래 누락)**: 3b 차단 근거는 mismatch tol의 소비를 'offset 판정 분해능'으로만 적었다. `device_sigmas`의 다른 소비자로 `mirror_ratio_sigma_pct`가 있다(`metrics_aux.py:69`, `mirror_ratio.py:58-62` -- tol None이면 resolution None). 같은 fail-closed 경로이고 결론은 바뀌지 않는다. 한 줄 보탤 수 있다(LA-1 재점검 입력 또는 다음 판).
- **r2 (문언 짝)**: «각각 `extra = None`·`unmeasured`»는 mismatch = `extra = None`, 잡음 = `unmeasured`로 짝지은 꼴이다. 실제로는 둘 다 최종이 `unmeasured(resolution_undefined)`다(mismatch는 `extra = None`을 거침). 오독 위험은 낮다.
- **r3 (번호 표기)**: A-146 행의 'minor 1·4·6·8'은 앞 판정 보고(handback) 번호이고, history 'v6.38.28 둘째 커밋'은 판정 파일 번호(minor 1·2·3·6·8·9·10)를 쓴다. 대상 자리는 같아 실질 차이는 없다.
- **관찰(새 결함 아님, v6.38.28 이전부터)**: KCL 항등 0 예외가 oracle에서는 '비전도(방향 위반) 판정'에 적용되고 엔진 (ii)에는 적용되지 않는다. 그래서 KCL 0 전류 `triode` 소자는 엔진이 봉인에서 거부하고, oracle 쪽 예외가 쓰일 길은 그 점에 대해 0이다(fail-open 아님). LA-1 재점검 'triode 스위치 DC 0 거짓 거부'(A-146 재점검 입력)에 함께 넣으면 된다.
- **안 바꾼 곳**: P:1370·약반전 '꺼진' 서술·P:2027(A-146 재점검 입력)은 그대로이며 판정 대상 밖이다. 바뀐 것은 네 파일뿐이고 design 문서 변경은 0이다.

### 재지 않은 것 (통과로 세지 않음)

- 실행 0.
- `TolMismatchTable.at`(`lut/mismatch_tolerance.py`) 본문과 `metrics_aux.py`에서 offset 결과를 `MetricResult`로 묶는 전 줄은 열지 않았다(`:69`·`:82-83` 분해능 칸 대응만 확인).
- 이번 diff 밖 계획 문언은 다시 grep하지 않았다(앞 판정 grep 결과 사용).
