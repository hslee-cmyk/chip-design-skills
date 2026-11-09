# 계획 v6.38.5 열다섯째 커밋 독립 검증 11 (2026-10-29)

- 대상: worktree `wt/plan-v6385`, 커밋 `adb3686a`(`git diff 6a31bf1c adb3686a` -- plan 11줄 교체·1줄 삽입(Q-CB2 1167) + history 6행: H1 1547 경위 1행, «원문» 1943~1947 5행).
- 검증자: 독립(작성자 아님). 문서 수정 0. git은 `git -C`로 읽기만(reset·checkout·stash·commit 0). worktree status 깨끗함.
- 엔진: `wt/integ-it12`(`b3336452`) 읽기만. python `C:\Python314\python.exe`.
- 기준: O-173(손계산 우선, E-0·E-1·E-2; SPICE 수치 동일성은 지적 기준 아님), graph 단일 정본 1~7, O-169, O-153, O-165 (a), 만들면 배선, 상수 발명 금지, 회로 이름 0, 원래 취지와 다름 표지, fail-closed.
- 측정 자리: `wt/_drafts/evidence/2026-10-29/plan_v6385_validation11/`

| 파일 | 내용 |
|---|---|
| `plan_<c>.md`·`hist_<c>.md` (c = 6a31bf1c·adb3686a) | 원본 |
| `segdiff.py` → `segdiff_{plan,hist}_6a31bf1c_adb3686a.txt` | 문장 단위 diff |
| `hist_check.py` → `hist_check.txt` | 지운 조각의 plan/history 보존 |
| `l304.txt` | 304 옛·새 표지 |
| `ctx_2190.txt` | SF-1 범위 3~10 원문(2187~2196) |
| `ctx_dr1.txt` | N6.36 DR-1 범위·완료·순서 + N6.1 SF-1·DR-1 행 |
| `grep_plan.txt`·`dr1_mentions.txt`·`refs.txt` | 참조·순서 grep |

## 판정

**승인 상정 불가.** Critical 0, **Major 1**, Minor 5.

- 검증 10의 Major 2·Minor 5는 문언으로 모두 반영됐다.
- 남은 결함은 MJ10-1 (2)를 고친 새 문언 쪽에 있다.
  - 'S0 θ 상자 블록 하나'를 상자 writer로 정했다. 그런데 같은 card SF-1 범위 6 (e)(2192)가 이미 `theta_bounds` 파생 S0 필드를 'S1 앞 S0 블록'으로 정하고 있다. 엔진에는 기존 S0 블록 `search_domain`도 있다. 이 블록이 이미 θ 수동소자 상자를 적용하고 미선언이면 정지한다.
  - 세 자리의 관계·층이 정해지지 않았다. 소비자 목록도 실제와 맞지 않는다 → **MJ11-1**.

## 1. 검사 1 -- 지적 해소·보존·정합

### 1.1 검증 10 지적

| 지적 | 해소 | 자리 |
|---|---|---|
| MJ10-1 (1) 판별 입력 정본 | 해소. '`graph.dc_current_basis`의 항이 빈 MOS 행 READS -- 새 집합 필드 0'. DR-1 범위 2348에 '재작성 뒤 0 전류 MOS를 빈 항 행으로 쓰고 정지는 VDS = 0 묶음 블록 쪽 조건 밖 갈래로 옮긴다'와 소비자를 적었다 | 1166, 2195, 2348 |
| MJ10-1 (2) writer 하나·소비자·표지 | **부분 해소**. 표지(원래 취지와 다름 -- 적용 자리 로더 → S0 블록)·Status·완료 조건(`git grep`)은 들어갔다. writer 정본 자리·층·소비자 목록에 새 결함 → MJ11-1 | 11, 304, 1166, 1217, 2195 |
| MJ10-2 순서 규칙 비교·등록 | 해소. (P)/(Q) 4축 비교 + 규칙 수, (Q) 권고 = DR-1 이관(SF-1 → DR-1). N6.1 SF-1 행 1217·DR-1 행 1231·N6.36 순서 2352·Status에 '(→ 승인 시)' 표지로 등록 | 11, 1166, 1217, 1231, 2352 |
| m10-1 304 '권고 (나) 역할별 분리,' | 해소(본문 복원 + «원문» 1947) | 304, H 1947 |
| m10-2 TB-1 표지 | 해소. 1211 파일 목록(`s2_values.py`·`CONTRACT.md:1001-1004`)·SPICE 다리 EO-1·O-149 재검토, 2214·2218 굵은 규칙 문장에 '(다)+(A) 승인 시 O-149 재검토' | 1211, 2214, 2218 |
| m10-3 보상 C 하한 백로그 자리 | 해소(N5.3 Q-CB2 열린 질문 신설, ⚠ 관례를 정의로 쓰는 상태 표지, 상정 조건 = LA-1·ME-1 변화표 E-2) | 1167, 11 |
| m10-4 구분자 | 해소('경향) -- **구현 자리·순서**') | 1166 |
| m10-5 `:130-133` | 해소. 계획 안 3곳 모두 `:130-133`, `129-133` 0 | 1166, 2348×2 |

### 1.2 history «원문»(5행 1943~1947, `hist_check.txt`)

- 1943 줄 인용, 1944 Q-CB1 구현 자리 문단 전체, 1945 SF-1 범위 9 표지, 1946 Status 줄 전체, 1947 304 조각(m10-1 소급)이 있다. 지운 조각 대부분이 여기에 담겼다.
- MISS 판정 조각은 대부분 표지 삽입으로 문자열이 나뉜 경우다(1211·1217·1231·2195 머리·2352 -- 삽입만).
- **실제 누락·부정확 3건** → m11-1:
  - (a) 304 옛 표지 '결합 C는 공통 상자 대상 밖·회로별 선언·미선언 정지(**card SF-1 범위 9**)'가 '(card DR-1 범위)'로 바뀌었다. 그런데 «원문» 행이 없다.
  - (b) 1166 옛 '…후속 질문(백로그)'의 «원문» 행이 없다.
  - (c) 1944 «원문»이 옛 문언의 `current_basis.py:129-133`을 `:130-133`으로 적었다. 원문 그대로가 아니다(1943과 겹침).
- H1 1547 경위 행은 MJ10-1·MJ10-2·m10-1~5 반영을 빠짐없이 적었다.

### 1.3 Status·N5.3(7행) 정합

- N5.3 v6.38.5 행 = Q-W1 1161·Q-CF1 1162·Q-ZG1 1163·Q-CA1 1164·Q-KV1 1165·Q-CB1 1166·Q-CB2 1167, 7행이다. 그 밖 Q-T0·Q-T3·Q-C1·Q-1·Q-2.
- Status 열린 결정 목록이 이와 1:1이다(Q-CB2 '열린 질문, LA-1·ME-1 변화표 뒤' 포함).
- Status 원래 취지와 다름 = Q-CB1('10번'·N13·DEC-105 (10)(a)·적용 자리 로더 → S0 블록·SF-1 → DR-1 순서)이다. 본문 표지(304·1166·2195)와 같다.
- 낡은 문언 grep('0 전류 MOS 집합 필드'·'후속 질문(백로그)'·'같은 통합 병합으로만 master에 들어간다'·`129-133`)은 모두 0이다.

## 2. 검사 2 -- Q-CB1·DR-1 독립 재판정

### (a) 빈 항 MOS 행 READS 대 DR-1 범위(2348) 일관성 -- 맞음

- 엔진 실측(`gmid_engine/sizing/current_basis.py`):
  - `:130` `dead = tuple(name for name in mos if not terms[name])`, `:131-133`은 비어 있지 않으면 `StructureUnresolvedError`(정지)다.
  - `:141` `CurrentBasis(..., tuple((name, terms[name]) for name in elements), ...)`는 모든 원소 행을 필드에 싣는다.
  - WRITES = `("graph", "dc_current_basis")` 하나(`:44`).
- 그래서 지금은 정지 때문에 빈 항 행이 필드에 실리지 않는다. 정지 갈래만 옮기면 dead MOS가 `rows`에 빈 tuple 행으로 실린다. 새 필드 없이 같은 정의(KCL 항등 0)가 graph 필드로 나온다.
- 계획 2348은 '재작성 뒤 빈 항 행으로 쓰고, 정지는 VDS = 0 묶음 블록 쪽 조건 밖 갈래로 옮긴다'고 적었다. 대상 정의는 '`dead`와 같은 정의'다. 범위 문언과 Q-CB1 (1)이 서로 맞는다. 둘째 생산자 0, 새 필드 0.

### (b) 상자 writer 하나·소비자 -- 결함(MJ11-1)

**엔진 실측: 상자를 쓰고 읽는 자리**

| 자리 | 역할 | 계획 목록 |
|---|---|---|
| `search/search_domain.py:76-80` `_passive_box`, `:106-112` 미선언 정지 `theta_{resistance,capacitance}_bounds_undeclared`, `:124-135` Variable 상자 | **이미 있는 S0 상자 적용 블록**(`@compute_block` writer `search_domain`). READS `graph.dc_current_basis`·`theta_schema`(`:89-90`) | 없음 |
| `search/search_context.py:164` | spec 선언 추출 → `search_domain` extras(writer **입력**) | '소비자'로 적음 |
| `search/iv_context.py:94`(`:32`는 상수 정의) | spec 직접 읽기 → `StartView.theta_bounds` 사본 칸 | `:32`로 적음 |
| `metrics/achievability.py:126`, `:248` | spec 직접 읽기(저항 상자·커패시터 면적) | 있음 |
| `search/macro_poles.py:133,141` | `ctx.box`(= `domain.variables`) 우선, 없으면 `ctx.theta_bounds` | 있음 |
| `search/iv_area.py:85` | `ctx.theta_bounds`**만** 읽음(최소 면적 하한값) | **빠짐** |
| `search/_helpers_area.py:24` | `ctx.box` 우선, 없으면 `ctx.theta_bounds` | **빠짐** |

**계획 안 다른 자리**: SF-1 범위 6 (e)(2192)
- `theta_bounds` 상자 선언 추출(`spec_bounds`)을 S0 필드로 둔다. writer는 S0 블록 하나이고, 층은 '입력 = spec뿐이라 **S1 앞** S0 블록'이다.
- 둘째 생산자 `search_context.py:164-166`·`achievability.py:115`·`iv_context.py:93`을 지운다.
- '**범위 9가 `theta_bounds` 상자 규칙을 바꾸면 같은 필드의 writer 본문이 바뀐다(새 자리 0)**'라고 적었다.
- 완료 조건은 '`THETA_BOUNDS` 엔진 소비 = 그 블록 하나'다.

**판정**
1. **writer 정본 자리가 셋으로 갈린다**(graph 규칙 1·6).
   - 1166·2195는 'S0 θ 상자 블록 하나'를 writer로 정하지만, 그것이 무엇인지 적지 않았다. 후보는 (i) 범위 6 (e) 블록, (ii) 기존 `search_domain`, (iii) 새 블록이다.
   - (iii)이면 `search_domain`의 `_passive_box`·미선언 정지가 같은 양(원소별 적용 상자)의 둘째 생산자로 남는다. 계획 변경 목록에 `search_domain.py`가 없다.
   - (i)이면 2192 '같은 필드 writer 본문이 바뀐다'와 맞는다. 그러나 다음 항목의 층 역전이 생긴다.
2. **층 역전 위험**.
   - (Q) 권고대로 DR-1이 결합 C 갈래를 'SF-1 범위 9의 S0 θ 상자 블록'에 넣으면 그 블록이 `graph.dc_current_basis`를 READS한다.
   - 엔진 순서는 `kernel_context.py:84` `dc_current_basis` → … → `:90` `dc_theta_schema` → `search_context.py:181` `search_domain` → `stage_b.py:169` `achievability`다.
   - 그 블록이 범위 6 (e)의 'S1 앞' 블록이면 S1 뒤 필드를 읽는 층 역전이다.
   - 열넷째 커밋 문언에 있던 층 진술 '그 필드 뒤 S0 θ 상자 블록'이 이번 개정에서 빠졌다(«원문» 1944로 옮겨짐). 새 문언에는 층 진술이 없다.
   - 이 역전은 SF-1 design 때가 아니라 DR-1 때 드러난다. 그때 블록을 옮기면 O-153 '넣었다가 옮김' 꼴이 된다.
3. **소비자 목록 '4곳'이 실제와 다르다**(만들면 배선·fail-closed).
   - `search_context.py:164`는 소비자가 아니라 writer 입력이다. 범위 6 (e)가 이미 지울 둘째 생산자로 등록했다.
   - `iv_context.py:32`는 상수 정의이고, 읽는 자리는 `:94`다.
   - `iv_area.py:85`·`_helpers_area.py:24`가 빠졌다. 특히 `iv_area.py:85`는 `ctx.theta_bounds`(spec 선언 사본)만 읽는다. 공통 상자를 받는 커패시터(회로별 선언 없음)는 `low_values`에서 빠진다.
     - 그러면 `area_estimate`가 `_helpers_area._passive_value`의 `ctx.box` 기하 중점 값을 쓴다.
     - 결과적으로 최소 면적 하한이 조용히 커지고, 면적 충돌(`StartConflict`)이 거짓으로 날 수 있다. 정지 없는 잘못된 값이다.
   - `StartView.theta_bounds`(`start_values.py:180`)는 이미 `ctx.box`(= `domain.variables`, `iv_context.py:106`)와 같은 양의 값 사본 칸이다(graph 규칙 2·4). 목록·처분이 없다.
   - 완료 조건 'spec 설정 직접 읽기 0(`git grep`)'은 이 사본을 거치는 `iv_area`를 잡지 못한다.
4. **범위 6 (e)와 범위 9가 같은 파일 줄을 서로 다른 목표로 재배선한다**.
   - 범위 6 (e)는 선언 추출 필드 READS로, 범위 9는 '그 필드(상자)' READS로 재배선한다. 같은 card 안에서 두 범위가 같은 자리를 서로 다른 필드로 잇는다.
   - 두 필드가 다른 양이라면(선언 상자 대 적용 상자) graph 규칙 3에 따라 정의 축(공통 상자·결합 C 판별 적용 여부)을 적어야 한다. 그런데 적지 않았다.
   - 2192 '같은 필드 writer 본문이 바뀐다(새 자리 0)'는 범위 9 새 문언과 맞지 않는 낡은 문언이다.

**검증자 권고 꼴**(문언 개정, 새 실측 불요 -- 위 표는 이 검증에서 읽기로 확인)
- 적용 상자 writer = 기존 S0 블록 `search_domain` 하나로 이름을 박는다.
  - 근거: 이미 `dc_current_basis`·`theta_schema` 뒤 층이다. 이미 미선언 fail-closed 사유를 가진다. 이미 `domain.variables`로 graph에 쓴다.
  - 그 본문 순서를 '회로별 선언 → (DR-1) 결합 C 선언 필수·미선언 정지 → 공통 상자'로 바꾼다. 새 블록 0, 층 역전 0.
- 범위 6 (e) 필드는 '선언 상자 추출(입력 = spec, S1 앞)' 그대로 두고 `search_domain`의 입력(READS)으로 둔다. 두 필드의 정의 축을 적는다(규칙 3). 2192 '같은 필드 writer 본문이 바뀐다'는 '적용 규칙은 `search_domain` 본문이 바뀐다'로 고친다.
- 소비자 재배선 목록을 실제로 맞춘다.
  - `iv_context.py:94`의 `StartView.theta_bounds` 사본 칸을 지우고 `ctx.box`(domain READS)만 둔다. 같이 `iv_area.py:85`·`_helpers_area.py:24`·`macro_poles.py:133,141`의 `theta_bounds` 갈래도 지운다.
  - `achievability.py:126,248`은 `graph/kernel: search_domain` READS로 바꾼다. `achievability`는 `search_domain` 뒤(`stage_b.py:169`)라 층이 맞다.
  - `search_context.py:164`는 범위 6 (e) 몫으로 남긴다.
  - 완료 조건 = 적용 상자 writer `search_domain` 하나, `theta_bounds` 사본 칸 0, 공통 상자 커패시터 toy에서 `iv_area` 최소 면적이 상자 하한을 씀(base는 중점 -- red).
- 대안 '새 S0 θ 상자 블록 + `search_domain`은 READS만'은 비교표에 ⚠로 적는다. 이 안은 `_passive_box`·미선언 정지를 지우는 범위가 따로 생긴다.

### (c) 로더 구문 검사만 -- 보완 필요(m11-5)

- 엔진 `authoring/spec_theta_bounds.py`는 원소가 topology 수동소자이고 kind ∈ {resistor, capacitor}이며 mode `engine`인지 교차 검사한다(hit `theta_bound_element`).
- '로더는 선언 구문 검사만'이라는 문언은 이 검사의 행방을 적지 않는다. 지워지면 θ 아닌 원소에 낸 선언이 조용히 무시된다(fail-open). 남는 자리(로더 -- 범위 6 '선언 형식 거부는 로더에 남음' 꼴 -- 또는 writer 블록)를 적어야 한다.

### (d) (Q) 순서 SF-1 → DR-1 등록·순환·층

- 등록: Status 11, N6.1 SF-1 행 1217('결합 C 갈래는 card DR-1로 -- 순서 SF-1 → DR-1'), DR-1 행 1231('card SF-1 선행 추가'), N6.36 순서 2352('card SF-1 선행 추가 … 새 병합 순서 규칙 하나 -- O-165 (a) 비교는 N5.3 Q-CB1 행'), 304, 2195. 모두 '(→ 승인 시)' 표지로 일관된다.
- 순환 0:
  - SF-1 선행 = EO-1, IT-1 + IT-2(VB-1 design 확인)이고 DR-1 선행 = IT-1 + IT-2다.
  - DR-1 → SF-1 관계는 계획 어디에도 없다(`dr1_mentions.txt`). 2350 (9)도 'card SF-1 범위 9 병합 뒤 heldout 판정 기록 통합 검사(순서 의존 없음)'라 같은 방향이다.
- fail-open 창 0: SF-1 병합 뒤 DR-1 병합 전에는 erfc가 `current_basis`에서 정지한다. 결합 C(0 전류 MOS ≥ 1)가 공통 상자를 받는 실행 경로가 없다.
- 층: writer가 `search_domain`(또는 `dc_current_basis` 뒤 블록)이면 0이다. 범위 6 (e) 'S1 앞' 블록이면 역전이다 → MJ11-1 2.
- 결함 하나: DR-1 완료 조건(2350 (1)~(9))에 결합 C 갈래 toy가 없다. 범위 2348이 '첫 소비자 toy를 넣음'이라고 적은 것과 맞지 않는다 → m11-2.

### (e) Q-CB2 자리 -- 맞음

- N5.3 1167 열린 질문이다. ⚠ 관례를 정의로 쓰는 상태라고 표지했다.
- 후보 물리 결정자는 PDK 최소 MIM·마디 기생 바닥이다. 마디 기생은 엔진 MNA가 이미 가지므로 새 상수가 아니다.
- 상정 조건은 하한 고착이 결정을 바꾸는지 실측하는 것이다(LA-1·ME-1 변화표, E-2). 시점 칸도 있다.
- 'STEP2 N7' 출처는 304에도 같은 인용이 있다. 지금 결정하지 않는다는 처리는 O-173 E-2(결정 영향이 있을 때만)와 맞다.

## 3. 검사 3 -- 6+1 질문 최종 표·끊긴 참조

| 질문 | 권고 | 대안·⚠ | 시점 | 판정 |
|---|---|---|---|---|
| Q-W1 | 이번 판은 표지·되돌릴 목록뿐 | (가)·순서 (i) 되돌릴 목록 | WB-1 착수 실측 → 결정 → 일괄 반영 | 상정 가능(변경 없음) |
| Q-CF1 | 안 A | B ⚠ IT-2c 재개정 | WB-1 범위 3a 착수 전 | 상정 가능 |
| Q-CA1 | (가) 삭제 | (나)(다) ⚠ | SF-1 spec data 커밋 전 또는 metric 등록 card 착수 전 | 상정 가능 |
| Q-ZG1 | (나) W_min·L_min, writer 하나, (i) fail-closed 기록 유지 | (가)~(마)·(i)~(iii) ⚠ 정확 | DR-1 design 착수 전 | 상정 가능 |
| Q-KV1 | (다) + (A) | (가)(나)(라)·(B)(C) ⚠ | TB-1 design 착수 전, E-0·I_Q 실측 뒤 | 상정 가능(m10-2 해소) |
| Q-CB1 | (나) 역할별 분리 + (α) + (Q) DR-1 이관 | (가)(다)(라)(마)(바)·(β) ⚠ fail-open·(P) ⚠ 새 꼴 규칙·'결합 C만 S0' ⚠ 규칙 1 -- 정확 | SF-1 design(범위 9) 착수 전 -- 맞음 | **수정 후**(MJ11-1, m11-2·m11-5) |
| Q-CB2 | 결정하지 않음(열린 질문) | 후보 2개, ⚠ 관례를 정의로 | LA-1·ME-1 변화표 뒤 | 상정 대상 아님(기록 맞음) |

**끊긴 참조 표본**
- '2533 선례'(1166)는 맨 줄 번호다. Q-CB2 삽입으로 한 줄 밀려 지금 2533 = U-131, 뜻한 선례 = 2534 U-132다 → m11-3(줄 번호 대신 U-132로).
- `iv_context.py:32`(1166·2195) → 읽는 자리는 `:94`다(MJ11-1에 포함).
- 정의 자리 확인:
  - `current_basis.py:130-133`(맞음)
  - `theta_*_bounds_undeclared`(304 (d), 엔진 `search_domain.py:108,112`)
  - `cbox_rereview.md`·`cbox_rereview/c5_sr2080.txt`(존재)
  - `plan_v6385_validation10.md`(존재)
  - 'STEP2 N7'(304·1167)

## 4. 지적

### MJ11-1 [Major] Q-CB1 '상자 writer 하나'의 정본 자리·층이 정해지지 않았고(범위 6 (e)·기존 `search_domain`과 셋으로 갈림), 소비자 재배선 목록이 실제와 다름

**자리**: 1166 (2), 2195 표지, 1217, 2192(범위 6 (e) '같은 필드 writer 본문이 바뀐다'), 2348·2352('SF-1 범위 9의 S0 θ 상자 블록').

**근거**: §2 (b) 표와 판정 1~4.
- 기존 S0 writer `search_domain`(`search_domain.py:76-80·106-112·124-135`)은 계획에 이름이 없다.
- 범위 6 (e)는 S1 앞 블록이 같은 필드라고 적었다. 새 문언에는 층 진술이 없다. 그래서 DR-1 결합 C 갈래(`graph.dc_current_basis` READS)가 들어올 때 층 역전 또는 둘째 생산자 중 하나가 생긴다.
- 소비자 4곳 가운데 1곳은 writer 입력이고, 1곳은 줄이 틀렸다. `iv_area.py:85`·`_helpers_area.py:24`와 `StartView.theta_bounds` 사본 칸은 빠졌다.
- 특히 `iv_area.py:85`는 공통 상자 커패시터에서 정지 없이 틀린 최소 면적 하한을 낸다.

**권고**: §2 (b) '검증자 권고 꼴'.
- writer = `search_domain` 하나로 이름을 박고, 층(`dc_current_basis`·`theta_schema` 뒤)을 적는다.
- 범위 6 (e) 필드는 선언 추출 입력으로 두고 정의 축을 적는다.
- 2192 낡은 문언을 고친다.
- 소비자 목록을 `iv_context.py:94`(사본 칸 삭제)·`iv_area.py:85`·`_helpers_area.py:24`·`macro_poles.py:133,141`·`achievability.py:126,248`로 바로잡는다.
- 완료 조건 = 사본 칸 0 + `iv_area` 공통 상자 하한 toy.
- 새 블록 안은 대안 ⚠로 비교표에 둔다. '원래 취지와 다름' 표지는 그대로 둔다(적용 자리 로더 → S0 블록).

### Minor

- **m11-1** history «원문»:
  - (a) 304 옛 '(card SF-1 범위 9)' 귀속 조각과 (b) 1166 옛 '후속 질문(백로그)' 조각의 «원문» 행이 없다.
  - (c) 1944가 옛 문언의 `129-133`을 `130-133`으로 고쳐 적었다(원문 그대로로).
- **m11-2** DR-1 완료 조건(2350)에 결합 C 갈래 toy를 더한다. (Q) 이관으로 범위에 '첫 소비자 toy'가 들어왔기 때문이다.
  - 미선언 결합 C → 정지(base = 공통 상자 적용 -- red)
  - 선언 결합 C → 선언 상자
  - 0 전류 MOS 없는 θ 커패시터 → 공통 상자 그대로
- **m11-3** 1166 '2533 선례' → 'U-132 선례'(줄 번호 참조가 Q-CB2 삽입으로 한 줄 어긋남).
- **m11-4** 1166·2195 소비자 인용 `iv_context.py:32`는 상수 정의다. 읽는 자리 `:94`로 고친다(MJ11-1 수정 때 함께).
- **m11-5** '로더는 선언 구문 검사만'에 기존 교차 검사 `theta_bound_element`(`authoring/spec_theta_bounds.py` -- topology 수동소자·kind·mode `engine`)가 어디에 남는지 적는다. 지워지면 θ 아닌 원소 선언이 조용히 무시된다(fail-open).

## 5. 검사 4 -- 승인 상정

**불가.** Critical 0, Major 1(MJ11-1). 문언 개정으로 고칠 수 있고, 새 엔진 실행·실측은 필요 없다. 소비자·writer·층은 이 검증에서 엔진 읽기로 확인했다. Q-CB1 밖 5질문(Q-W1·Q-CF1·Q-CA1·Q-ZG1·Q-KV1)은 상정 가능하고, Q-CB2는 기록이 맞다.

## 6. 원칙 점검표(실측/읽기/안 함)

| 항목 | 결과 | 방법 |
|---|---|---|
| graph 규칙 1(writer 하나) | Q-CB1 상자 writer 후보 셋(범위 6 (e)·`search_domain`·새 블록) 미정 → MJ11-1 | 실측(엔진 grep `theta_bounds`, `search_domain.py`, 계획 2192) |
| graph 규칙 2·4(사본) | `StartView.theta_bounds`가 `ctx.box`와 같은 양의 사본 칸인데 처분 없음 → MJ11-1 | 실측(`iv_context.py:94·106`, `start_values.py:180·184`) |
| graph 규칙 3·6(정의 축·정본 자리) | 판별 입력 `graph.dc_current_basis` 빈 항 행 = 맞음. 선언 상자/적용 상자 축 미기재 → MJ11-1 | 실측(`current_basis.py:130-141`) |
| 순환·층 역전 | 순서 SF-1 → DR-1 순환 0. 상자 블록 층 미진술(범위 6 (e) S1 앞이면 역전) → MJ11-1 | 실측(`kernel_context.py:84-90`, `search_context.py:181`, `stage_b.py:169`) + 계획 grep |
| 만들면 배선 | (Q)로 소비자 0 코드 0. `iv_area.py:85` 재배선 누락 시 틀린 값 → MJ11-1 | 실측 |
| O-165 (a)·O-153 | (P)/(Q) 비교 들어감. 층 미진술로 DR-1 때 블록 이동 위험(O-153) → MJ11-1 | 읽기 |
| fail-closed | (α) 미선언 결합 C 정지, SF-1~DR-1 사이 fail-open 창 0. `theta_bound_element` 행방 → m11-5 | 읽기 + 실측(`spec_theta_bounds.py`) |
| 상수 발명 | 0(Q-CB2는 결정 보류, 후보는 PDK·MNA 기존 양) | 읽기 |
| 회로 이름 | 규칙 문언 0(질문 사실 칸의 회로 이름만) | 읽기 |
| E-0·E-1·E-2 | Q-CB2 상정 조건 = E-2 맞음. TB-1 EO-1 선행 표지 들어감 | 읽기 |
| O-169·O-171 | 물리 판정 변경 없음 | 읽기 |
| 원래 취지와 다름 1:1 | 적용 자리 로더 → S0 블록·SF-1 → DR-1 순서가 본문·Status 1:1 | 읽기 |
| SPICE 수치 동일성 | 지적 기준으로 쓰지 않음 | -- |
| history «원문» | 5행, 누락 2·부정확 1 → m11-1 | 실측(`hist_check.py`) |
