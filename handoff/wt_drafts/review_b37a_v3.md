# B37a (#47) card v3 독립 검토 -- `review_b37a_v3.md`

검토자 = 작성자 아님. 저장소는 읽기만 했다(`git archive`·`git show`·`git rev-parse`·`git diff --stat`·`git status`). scratch `C:/g177`만 쓰고 끝에 삭제했다.
`git status --porcelain` md5 시작·끝 같음(`168fd530…`), HEAD `dd60db6` 그대로.

대상: `_drafts/draft_b37a.spec.md`(v3, 대조 `draft_b37a.spec.pre-p4v095.md`), `_drafts/draft_b37a_approval_question.md`(대조 `.pre-p4v095.md`).
기준: Phase 4 design 초안 v0.9.6 `_drafts/draft_phase4_design.md` §6 'E11 차이 집합 표'(성분 P·D47 행, 판정 (0)~(v)), §5.4 #47 행 조건 (가)(나).

## 판정

**PASS(조건부) -- blocking 0, should-fix 2, minor 4.**
핵심 재측정(항목 단위 삭제 목록, `ports` oracle, 쌍 집합, E3 표)은 작성자 시제품을 쓰지 않은 독립 구현에서 card 데이터 블록과 **완전히 같다**.
should-fix 둘은 계약 5(b)의 기대값 출처(E3 값)가 승인 기록 본문에 데이터로 실리지 않는 문제, 그리고 Q3이 고정하려는 값의 사실 하나(소자 6개가 결과에 없음)를 알리지 않는 문제다.

## 1. 독립 재측정(방법)

* base = `git archive dd60db6`(`gate/master` = `dd60db6515b6…`, `git ls-remote gate master`와 같음).
* head = base 사본 + **검토자 자체 구현** `C:/g177/rv_head.py`. card 텍스트(범위 1~4, 계약 1·2·6·7, '신규 시그니처')만 보고 썼다. `make_head.py`는 읽지도 실행하지도 않았다. 구현 내용:
  * SD: `PortDeclaration`(frozen dataclass `inputs`·`outputs`). `port_declaration`은 role 6어휘 표, `_` 키 건너뜀, 접근자 거부(키 없음·dict 아님·항목 형식·빈 이름·`direction` 모순)를 하고 sorted tuple을 돌려준다.
  * `load_topology`: 진입 파일에서 1회 호출한다. 연결 파일에 `ports`가 있으면 같아야 한다. 존재 검사(트랜지스터·passive·ideal_sources·연결 파일 passive 단자)와 레일 겹침 검사(raw `supply_nets` 대역)를 한다. E2·E1에 `inputs=`·`outputs=`를 넘기고 `meta["ports"]`를 싣는다.
  * SR: `resolve_stack_layout(…, *, ports)`, 경로 3 = `refine_differential_and_mirror_relations(t, ports.inputs, ports.outputs)`, `_build_theta_evaluator`가 `ports=meta["ports"]`를 넘긴다. `input_referred_offset_pairs`는 `meta["ports"].inputs`를 쓰고 '입력 0 + offset 쌍' 거부를 한다. 캐시의 raw `"ports"`는 지웠다.
  * 작성자 구현과 달라도 되는 세부(검사 위치, 예외 문구, `"ports"`를 meta dict 어디에 넣는가)는 내가 따로 골랐다. 그래도 결과가 같다는 것이 '목록이 구현 세부에 기대지 않는다'는 증거다.
* 키 측정(`keys.py`): base 16키, head = 16 + `ports` -- card '작성 전 실측' 8과 같다.
* `e_lib_p3.py`(`_drafts/p3_scripts/e_lib_p3_proposed/`, sha256 `c6b82fc7…` -- Phase 3 D-28 측정 도구. 작성자 시제품 아님)를 두 판에서 17키 전부 MASK로 실행했다(`PYTHONHASHSEED=0`, `-B -P`). rc 0, 9/9 load·V1·V2 ok, 전체 `hash` 두 판 모두 `223cdec96a4e…`(card와 같음).
* 목록 유도(`derive.py`): 쌍마다 `__dict__` 정규화를 풀었다.
  * `device_roles`·`_device_roles_autofilled`는 소자·필드 단위 집합 차이로 유도했다. head에서 소자가 없으면 그 소자의 base 필드 전부가 `field_removed`이고 소자는 `entry_removed`다.
  * review 목록은 순서 보존 다중집합 차이로 유도했다.
  * 추가·변경·재정렬은 이상(anomaly)으로 따로 셌다.

## 2. 결과(전부 card와 일치)

| 항목 | 검토자 측정 | card | 판정 |
|---|---|---|---|
| (c, u) 차이 쌍 | 17 = 8쌍 + 9 × `ports`. `per_hash.load`·V1·V2 차이 0 | `pairs` 8 ∪ 9 × `ports` | **같음** (`D_obs == D_exp`, extra 0, missing 0) |
| 이상(추가·값 변경·재정렬) | 0 | '삭제뿐' | 같음 |
| `field_removed` | 58 | 58 | **항목 집합 같음** |
| `entry_removed` | 40 | 40 | **항목 집합 같음** |
| `review_needed_removed` | 4(순서 포함) | 4 | **같음** |
| card 블록 배열 순서 | -- | 셋 다 정렬 순서 | 결정적 |
| card 블록 sha256(3칸 들여쓰기 제거, LF, 끝 LF 1) | `7c1871a6977a21fe0b7583540362816d721eb5435da754cb38042f3e585de58f` | `7c1871a6…` | 같음 |
| 승인 질문 블록 sha256 | 같은 값, 원문 바이트까지 같음 | 같음 | 같음 |
| card 적용 규칙 1~4를 base에 적용 → head | 9회로 × 3키 불일치 0, INVALID 0 | 0 | 같음 |
| `device_roles` 삭제 = `_device_roles_autofilled` 삭제(사람 선언 값 불변) | 29 = 29, 같은 (회로, 소자, 필드, 값) | 29·29 | 같음 |
| 승인 요약표 사실 | sf_pushpull M1·M2 남는 필드 `L_role`·`gm_id_role`, ngcc M4·M6B·M7 `gm_id_role`·M1 `L_role`+`gm_id_role`, two_stage_ota_sf M1·M2·M4 유지, nmcnr 12→10, two_stage_ota 9→7 | 같음 | 같음 |
| E3 경로 3(선언 vsid 없는 5회로) | ngcc `[M0,M1,M2]`→`[M0]`,`[M1,M2]`, sf_pushpull `[M17,M18]`·`[M19,M20]` → 단독 4, two_stage_ota_sf `[M8,M9]` 분리. common_gate·pushpull 같음 | 같음 | 같음 |
| 경로 3 대 레거시 폴백(head) | sf_pushpull만 다르다(레거시 = `[[M1,M2]]`만 묶음). 나머지 4회로는 같다 | card 'V3 계획' 1 | 같음 |
| `input_referred_offset_pairs` 9/9 | base = head. current_reuse `[[M1a,M1b],[M4a,M4b]]`, folded `[[M1,M2]]`, nmcnr `[[M102,M103]]`, two_stage_ota `[[M1,M2]]`, 나머지 `[]` | 같음 | 같음 |
| base→`dd60db6` 엔진 변화 | `git diff --stat 7535799 dd60db6`: SD `kcl_series_union` +3 −14뿐(library는 `.md` 2개) | 같음 | 같음 |

### `ports` 독립 oracle -- 9/9

`git -C R show dd60db6:…/library/<c>.topology.json`의 `ports`에서 `_` 키를 빼고, 6어휘 role 표로 나눠 `sorted`했다. 엔진은 import하지 않았다. 9/9가 head `masked.ports`와 `==`이고, base는 9/9 `"<ABSENT>"`다.
값: common_gate `vin`/`vout`, current_reuse `Vim,Vip`/`Vom,Vop`, folded `vin_n,vin_p`/`out`, ngcc `Vinn,Vinp`/`Vout`, nmcnr `Vin_n,Vin_p`/`Vout`, pushpull `vin`/`vout`, sf_pushpull `vin_n,vin_p`/`vout`, two_stage_ota `vin_n,vin_p`/`OUT`, two_stage_ota_sf `vin_n,vin_p`/`vout`(card 318행과 같음). 정규화 키는 정확히 `__dc__`·`inputs`·`outputs`다.

### 직렬화 모양 -- 충분히 고정됨

card '신규 시그니처' 311~315행이 고정하는 것:
* 형: frozen dataclass. 필드는 정확히 `inputs`·`outputs`이고 이 순서다. 다른 필드·기본값·`__post_init__`이 없다.
* 원소: `tuple[str, ...]`, 넷 이름(키) 그대로, Python `sorted`(코드 포인트 순), 중복 없음, 없으면 `()`.
* 정규화 결과(`ports: {}` 경우 포함)와 '바꾸면 design 개정' 목록.

`e_lib_p3.py`는 `sort_keys=True`로 내보내므로 JSON 키 순서는 판정에 영향이 없다. tuple은 list로 정규화되고 원소 순서는 정렬 규칙이 정한다. 빈틈은 minor m3(`_` 키 제외가 이 절이 아니라 계약 1·성분 P 문단에만 있다) 하나다.

## 3. 작성자≠검증자 -- 피검 함수 출력을 기대값으로 읽는 문장

* 계약 2: v3에서 고쳤다. 기대값은 JSON `ports` + role 표이고, `meta["ports"] == port_declaration(…)`은 '배선 관찰'로 명시돼 있다(93~94·339행). 문제 없다.
* 성분 P(317행)와 착수 조건 (다)(436행)도 피검 호출과 card 측정값을 명시적으로 금지한다. 문제 없다.
* 계약 9 D47: 기대값 = base 값 + 승인 기록 목록이다. 목록 자체는 작성자 시제품에서 나왔지만, 사용자 승인과 착수 시 재측정을 거친 값이다. 실제 code-author 구현이 그 값과 맞는지를 판정하므로 순환이 아니다(design D47 행과 같다). 검토자 독립 구현도 같은 목록을 냈다. 문제 없다.
* 계약 7 library 반환(138행)은 (c) base 실행값이다. 피검 판(head)이 아니므로 문제 없다.
* **남은 것 하나 -- 계약 5(b)와 계약 9의 E3 표.** 기대값 = 'E3 표의 병합 상당 값'(116·291행)이다. 이 값은 작성자 모의 head 측정이다. oracle은 '승인 기록'으로 돼 있지만(117행), 아래 S1처럼 승인 기록 본문에 이 값을 **데이터로** 싣는다는 요구가 승인 질문 §3에 없다. 그러면 test-author·auditor가 card(작성자 측정)에서 값을 읽게 된다. D47이 막은 순환과 같은 모양이 E3 쪽에 남는다. → S1.

## 4. 지적

### should-fix

**S1. 계약 5(b)·계약 9 E3 기대값이 승인 기록 본문에 데이터로 실리지 않는다.**
* card 407행(Q1)은 "삭제 목록과 **E3 표(3회로)**를 기록 본문에 그대로 싣는다"고 한다.
* 그런데 승인 질문 §3의 '승인 기록 본문에 반드시 넣는 것'(206~209행)은 D47 블록 하나뿐이다. E3는 scope 산문("E3 레이아웃 1차 그룹 변화(Q1 E3 줄)")에만 있다.
* 계약 5(b)의 oracle은 '승인 기록'(117행)이고 비교식은 `sorted(sorted(v) for v in g.values())`다. 그런데 승인 질문 24행 값은 사람 정렬(`[M9,M10]`) 산문이다. 실제 비교값은 `["M10","M9"]`이고 그룹 순서도 문자열 정렬이다.
* 고칠 것: §3 '반드시 넣는 것'에 E3 데이터 블록을 더한다. 3회로 base/병합 상당의 전체 그룹 목록을 card 5(b) 비교식 그대로의 정렬 모양으로 싣고, sha256과 착수 시 재측정 판을 함께 적는다. card 116·291행은 "기대값 = 승인 기록 본문 E3 블록"으로 가리킨다.
* 검토자 측정 값(head, `sorted(sorted(...))`): sf_pushpull `[["M10","M9"],["M11","M12"],["M15","M16"],["M17"],["M18"],["M19"],["M20"],["M21"],["M22"],["M5","M6"],["M7","M8"]]`.

**S2. Q3이 고정하려는 sf_pushpull 값의 사실 하나를 사용자에게 알리지 않는다.**
* 경로 3 결과에는 base·head 모두 **M1·M2·M3·M4·M13·M14(6개)**가 어느 그룹에도 없다(검토자 측정: uncovered = `M1, M13, M14, M2, M3, M4`). card 477행 관찰은 'M1~M4'만 적어 M13·M14가 빠졌다.
* 승인 질문 Q1(24행)과 Q3(181행)은 이 사실을 전혀 적지 않는다.
* Q3은 이 값을 '승인된 동작'으로 test에 고정하는 질문이다. 그래서 '소자 6개가 1차 그룹 결과에 없는 기존 동작까지 함께 고정된다(백로그 후보)'를 질문에 적어야 정확하고 중립적이다.
* card 477행도 'M1~M4·M13·M14'로 고친다.

### minor

* **m1.** card는 여러 곳에서 'Phase 4 design v0.9.5'를 인용한다(12·93·151·311·407·428·432·437행). 착수 조건 (라)(437행: "이 정정 전에는 card를 커밋하지 않는다")는 design v0.9.6이 이미 반영했다. 검토자가 대조한 결과, v0.9.6 D47 행 (1)~(4)가 card 계약 9 적용 1~4와 같은 문장이다. card를 v0.9.6 인용으로 바꾸고 (라)를 '반영됨(v0.9.6)'으로 닫는다.
  * design 쪽(card 밖, 오케스트레이터 몫): §5.4 #47 행(538행)이 여전히 'spec card **v2** -- 인용'이고, P·D47 행이 'card v2 계약 1/9'를 가리킨다.
* **m2.** Q1 질문 문안(154행)은 데이터 블록 항목만 묻는다. E3 3회로 그룹 변화는 같은 Q1의 승인 대상인데(card 407행, §3 scope) 질문 문장에 없다. 문장에 'E3 표(3회로)의 그룹 변화'를 넣는다. Q1이 '아니오'일 때 무엇이 되는지(B37a 보류 / 6a 선행)도 한 줄 적으면 선택지가 대칭이 된다.
* **m3.** 직렬화 절(313행) '원소는 `ports`의 넷 이름(키) 그대로'에 '`_` 접두 키 제외'를 함께 적는다. 계약 1·성분 P 문단에는 있지만 interface card로 옮기는 절은 이 절이다.
* **m4.** card 39행 '줄 번호는 `7535799` 기준'이라 틀린 것은 아니다. 다만 v3 측정 판 `dd60db6`에서는 SD 3020행 뒤 줄이 −11만큼 밀린다(`load_topology` 8550→8539, `propose_vertical_stack_id_gap_fill` 3261→3250, `if inputs or …` 3293→3282, E2·E1 호출 8643→8632·8668→8657). SR 줄은 같다. 착수 시 오케스트레이터가 다시 잴 대상이므로 표기만 확인한다.

## 5. 승인 질문 점검 요약

* 항목 단위 목록 그대로 승인: 된다. 블록이 card와 바이트 단위로 같고, 적용 규칙 (1)~(4)가 design v0.9.6 D47과 같다. '한 항목이라도 다르면 승인 무효'를 질문 문안과 §3 재검토 조건에 명시했다.
* 정확한 사실: 요약표와 '바뀌지 않는 것'은 검토자 측정과 전부 같다. 예외는 S2(누락 소자 6개 미기재)다.
* 중립성: '원칙으로 말할 수 있는 것 / 없는 것'을 나눴고 값의 옳고 그름은 6a로 넘긴다. Q3은 기본안·대안을 함께 제시하고, 대안의 대가(약화 = 사용자 승인)를 적었다. Q1의 '아니오' 경로 미기재는 m2다.
* Q2: 회로별 근거와 '메시지만으로 확인되지 않음'을 그대로 적었다. 중립이다.

## 6. 재현 메모

* 스크립트(검토자 작성, scratch에서 삭제함): `rv_head.py`(head 시제품), `keys.py`(meta 키 합집합), `run_elib.py`(`e_lib_p3.py` 두 판 실행), `derive.py`(목록 유도·card 블록 대조·적용·oracle), `e3.py`(경로 3·offset), `p3.py`(경로 3 대 레거시·미포함 소자), `facts.py`(승인 요약표 사실).
* 블록 sha 계산: card는 펜스 안 각 줄의 앞 3칸을 떼고 LF로 이은 뒤 끝에 LF 1개를 붙였다. 승인 질문은 들여쓰기가 없어 펜스 안 그대로 같은 방식으로 계산했다. 두 값 모두 `7c1871a6977a21fe0b7583540362816d721eb5435da754cb38042f3e585de58f`다.
