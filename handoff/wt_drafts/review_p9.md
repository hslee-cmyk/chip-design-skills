# 검토: `_drafts/draft_p9.spec.md` (`20260930-p9-kcl-edges`, equivalence)

검토자 = 작성자 아님. 저장소 읽기 전용(측정 HEAD = gate master cd64170, `git status` 시작 때와 같음; 검토 중 gate가 8790b24로 전진 -- B28 병합, 엔진·레지스트리·design 20 diff 0).
scratch = `C:/g35`(끝에 삭제 완료).
고친 초안: `_drafts/draft_p9.reviewed.spec.md`(머리 `parse_spec_card(expect_id='20260930-p9-kcl-edges')` 통과, 본문 절 11개).

## 요약

| 등급 | 건수 | 항목 |
|---|---|---|
| blocking | 1 | B1 V3 등가 변이(경로 압축 줄 삭제)가 어떤 test로도 죽지 않아 V3 FAIL 확정 -- card는 "합성 입력이 변이를 죽이도록"이라 적고 결정 항목 '없음' |
| should-fix | 4 | S1 `Transistor`가 interface card에 실리지 않음(test-author 입력 공백) / S2 계약 5(b)·재현 수치 "줄 18→17"이 docstring에 흔들림 / S3 V3 실행 조건(B28 의존·timeout·인벤토리) 미기재 / S4 DIFF-DUP 입력 (i)이 실행 환경에 따라 조용히 달라짐 |
| minor | 4 | M1 선례 인용 문구 부정확 / M2 계약 2에 dict 키 순서 없음 / M3 '작성 전 실측' 4의 사실 오류(interface card에 Transistor 싣는다) / M4 interface card 잡음 심볼(`size_transistor`) |

사실 재측정은 모두 맞다(아래 §4). equivalence 규칙 해석(계약 1·6(b)를 auditor 측정으로)은 옳다.

## 1. blocking

### B1. V3: 바뀐 def 전체가 변이 대상이고 경로 압축 삭제는 등가 변이 -- 생존 1 확정

* 근거: `tools/gates/mutate_changed.py` ①·`changed_defs`는 **diff가 닿은 def 전체**를 변이한다(엣지 줄만이 아니다). 선례 `.ai/approvals/20260922-ic3-v3-exempt.md`
  "바뀐 def 전체를 변이하는 규칙(05 §9 V3 ①)으로 … 기존 줄이 대상에 들어왔다".
* 모의 실측(`C:/g35/mkhead.py` → 병합본 모양 모의: `net_uses` 블록과 두 union 루프를 `for a, b, _kind, _detail in _kcl_and_matching_edges(netlist, matching_pairs): union(a, b)`로 교체;
  `C:/g35/mut.py`가 저장소 도구의 `changed_defs`·`mutants`·`_replace_def`만 import해 후보 영구 test `C:/g35/test_dup_kcl_edges.py`(card '거부해야 할 입력' 그대로, 손 리터럴 7개)로 실행):
  * 대상 def = `kcl_series_union` 하나, 변이 24개 → killed 23(그중 timeout 2), **survived 1** = `stick_diagram:kcl_series_union:stmt_delete:body[2].body[0].body[0]`
    (`find`의 `parent[x] = parent[parent[x]]`). 결과는 연결 성분 분할만으로 정해지므로(대표·구성원·키 순서를 `netlist` 순서로 다시 고른다) 이 변이는 **등가**다 -- 어떤 입력으로도 못 죽인다.
  * card는 "V3는 바뀐 def `kcl_series_union`에 적용된다 -- 합성 입력(…)이 그 변이를 죽이도록 짠다"고만 적고 '결정 필요 항목: 없음'. 이대로면 V3 FAIL → 재시도.
* 고침(초안 반영, 기본안): 계약 1(d) -- `find`에 경로 압축 대입을 두지 않는다(루프 본문 `x = parent[x]`). 모의(`C:/g35/headb`, `mutb.py`): 대상 `kcl_series_union` 23 +
  바뀐 중첩 def `kcl_series_union.find` 5 = **28/28 killed, 생존 0**. 결과 동일(DIFF-DUP 18/18 + 합성 레일 2회 넷리스트, `diffdup.py`), 후보 test base·병합본 7/7 PASS.
  승인 불필요, 계약 7(최상위 def 하나)과 양립. 대안(경로 압축 유지 + `target_kind: decision` 면제 승인)은 사용자 승인·변이 id의 AST 경로 결속·승인 셋째 줄(계획 674행 논점)
  때문에 '결정 필요 항목'에 '택하지 않음'으로 적었다.
* 함께 고친 문장: 판정 유형 근거의 "union-find 구조까지 같고" → 경로 압축이 빠지면 내부 구조는 달라지나 결과는 분할만으로 정해진다는 문장으로.

## 2. should-fix

### S1. test-author가 넷리스트를 만들 정보가 없다 -- `Transistor`는 interface card에 실리지 않는다

* `tools/gates/interface_card.py` `engine_defs`는 최상위 def와 **클래스 메서드**만 모은다. 초안으로 모의 생성(`C:/g35/p9.interface.md`): 기존 함수 11개, `Transistor` 없음
  (`load_topology` 반환 주석에 이름만). 선례 interface card 중 `Transistor` 생성법을 준 것 없음, contracts test 중 `Transistor(`를 쓴 것 없음.
* test-author는 소스 열람 금지(agents/gmid-test-author.md 21-22행: interface card + spec card 계약·oracle·거부 입력·재현 수치). 초안 '작성 전 실측' 4의 "interface card에 …
  `stick_diagram.Transistor` 시그니처를 싣는다"는 사실이 아니다(M3).
* 고침: 계약 2에 원소 모양 명시 -- `Transistor(name=…, kind="nmos"|"pmos", source=…, drain=…)`(dataclass, 나머지 기본값, kind 밖이면 ValueError), `matching_pairs` 원소 = 이름 튜플.

### S2. 계약 5(b)·'재현할 수치'의 "`_RAIL_NETS` 참조 줄 18 → 17"은 docstring 한 줄에 깨진다

* 실측: `grep -c` 18줄, AST `Name` 참조 19(3719행 한 줄에 2개). 모의 병합본: 17줄 / AST 18.
* 계약 7이 docstring 갱신을 허용하고 현 docstring이 레일 제외 규칙을 설명하므로, code-author가 "정본의 `_RAIL_NETS` 판정" 같은 문장을 쓰면 줄 수는 18로 남는다 → '기대 17'·재현 수치
  불일치(auditor 재측정 실패 가능).
* 고침: AST `Name` 참조 수(base 19 → 병합본 18, "base보다 작다")로 판정, 줄 grep은 참고로만. 5(a)의 '문자열 상수'·'docstring' 정의도 AST로 못박음(모의에서 새 문자열 0 확인, `c15.py`).

### S3. V3 실행 조건이 card에 없다

* 인벤토리(HEAD 정적 그래프, `inv.py`): `kcl_series_union` 70개(+새 test 6~7), 1(d) 모양이면 중첩 `find`는 이름 색인 때문에 148개(`inv2.py`).
  둘 다 `contracts/test_ts6_probe_relocate.py::test_base_blob_reader_reads_the_base_tree`를 담는다 -- `.git` 없는 V3 사본에서 실패해 모든 변이가 '기준 실행 실패'로 생존 처리
  (선례 `20260930-dup-w-calc` V3 basis: 2060개 전부, `20260930-df36-instance-relpath`: 22개). **검토 도중 B28이 gate에 병합됐다**(2b41e79 병합, 8790b24 판정 기록;
  엔진·레지스트리 diff 0): V3는 이제 `--head` 격리 복제본(이력 포함)에서 돌아 이 test가 통과하고, 기준 실행 실패는 생존이 아니라 **ERROR exit 2**다.
* timeout으로만 죽는 무한 루프 변이: 경로 압축 유지 시 2개, 1(d) 모양 4개(부모·중첩 중복). 기본 `--timeout 600`이면 최소 20~40분. B28 뒤 `--timeout`은 기준 실행에도 걸려
  인벤토리 기준 실행 시간보다 짧으면 V3가 ERROR로 끝난다.
* 고침: 판정 유형 근거에 V3 단락 추가 -- B28 반영 상태 명시, timeout은 기준 실행 실측 시간보다 넉넉히·값과 근거를 basis에; 죽이는 입력의 실제 대상
  (대표 키 판정이 `members_sorted[0]` ±1을 죽인다; 3회 사용·source=drain 입력은 병합본 변이 줄과 무관). 복제본은 추적 파일만 담지만 `skills/analog-grammar/assets`가 추적돼
  S4 조건도 성립(`git ls-files` 확인).

### S4. DIFF-DUP 입력 (i)이 실행 환경에 따라 조용히 바뀐다

* 실측: `stick_diagram.py`를 트리 밖(`C:/g35/base`)에 복사해 `spec_from_file_location`으로 읽으면 `ngcc_3stage_ff`·`sf_pushpull_output_opamp`·`two_stage_ota_sf`의 current_forced 쌍이
  `[]`가 되어 그룹 수가 11·11·4가 아니라 12·12·5(`diffdup.out.txt`). 원인: `load_topology`의 자동 매칭 쌍 제안이 `_import_analog_grammar`(SD 1045, `__file__` 기준 상대 경로,
  ImportError면 조용히 None)에 기댐. 저장소 안 모듈로 읽으면 11(`p9_diff.out.txt`와 같음).
* base·병합본을 같은 방식으로 돌리면 비교 자체는 같다(18/18 equal)지만 '재현할 수치'가 어긋나 재측정 실패로 보일 수 있다.
* 고침: 계약 4에 실행 환경(복제본 트리 그대로, `A`를 sys.path에, 모듈 이름 `stick_diagram`) 명시. 이 soft-fail 자체는 P9 범위 밖 -- 백로그 후보(조용한 import 실패로 매칭 쌍 제안이
  사라짐, WP '조용한 면제 금지' 계열).

## 3. minor

* M1 선례 인용: P5b 판정 기록 원문은 "red 필드에는 싣지 않는다"(`.ai/verification/20260923-d-delete-telescopic.json`), 초안은 "equivalence는 red 필드에 쓰지 않는다"로 인용. 고침.
* M2 계약 2가 dict 키 순서를 말하지 않았다(계약 4는 `list(items())` 비교). 실제 = 대표의 `netlist` 순서. base PASS이므로 추가(test가 키를 판정하게 되어 B1의 상수 변이를 확실히 죽인다).
* M3 '작성 전 실측' 4의 interface card 문장(S1과 같은 사실 오류). 고침.
* M4 계약 8(b)의 백틱 `size_transistor`가 interface card에 무관한 심볼로 실린다(V4 피검 집합 잡음). "W 식 함수 행"으로 바꿈. 계약 4에 새로 쓴 `_import_analog_grammar`는
  interface card에 실리지만 무해(피검 호출 기대값 금지 대상에 하나 더 들 뿐).
* 참고(결함 아님): 계약 8(c)의 §4·§5·§6 다른 행 줄 번호 정리는 design §8 P9 행 "레지스트리 §2 행 정정"보다 넓다. 레지스트리 경로는 code-author 몫이고 판정은 reg_check exit 0 +
  auditor 판독이라 재시도 위험은 작다 -- 유지.

## 4. 사실 재측정 (HEAD cd64170)

| 주장 | 결과 |
|---|---|
| SD 2983 `_RAIL_NETS`, 3003 `kcl_series_union`, 3134 `_kcl_and_matching_edges`, 호출 3206(def 3158)·3291(def 3261)·7310(def 7304), SR 8055(def 7930), SD 8643(`load_topology` def 8550) | 맞음 |
| 엣지 규칙 줄 단위 동일(3023-3026·3041-3048 대 3142-3154), union 순서 같음 | 맞음 |
| SR 4293 레일 튜플, 4307·4309 부호, `_metric_kcl_residual` def 4267 | 맞음 |
| `_RAIL_NETS` 줄 18 → 17 | 줄은 맞음(모의 17), AST 19 → 18 -- S2 |
| 엔진 호출자 `kcl_series_union` = SR `_build_theta_evaluator`·SD `_kcl_branch_map` 2곳, `_kcl_and_matching_edges` = 2곳 | 맞음(run_harness·다른 A/*.py 0, unit test는 docstring만) |
| DIFF-DUP 9회로 × 2입력 18/18, `_TEMPLATE` 로드 실패, 그룹 수 표 | 맞음(저장소 안 import 조건 -- S4). 모의 병합본(두 모양)과 base: `list(items())`·엣지 목록 18/18 동일 |
| 레일 넷 정확히 2회 = `two_stage_ota` `gnd`뿐 | 맞음(`p9_railtwice.out.txt`) |
| 레지스트리 43·308·428·472·473·474행 내용, 43행 '3148행' 병합 뒤 낡음(모의: 3137) | 맞음 |
| design 20 134·136·193·196·218행, E1 명령 `-k "dup_w_calc or dup_kcl_edges"` | 맞음. 모듈 이름 `test_dup_kcl_edges.py`가 `-k`에 걸림, 다른 test에 두 부분 문자열 없음 |
| 계획 599·603·618·621·622(쓰기 경로), 674·680·686·838행 | 맞음 |
| `.ai/context.md` 14963행 B26 | 맞음 |
| approval 두 기록 존재, 여러 approval 줄 선례(`20260929-probe-engine-dup`·`20260930-restore-plan-functions` 각 3줄) | 맞음 |

## 5. 요청 항목별 판정

1. 사실 재측정 -- §4. 틀린 수치 없음, 판정 방식 취약 1건(S2).
2. equivalence 규칙 -- 후보 영구 test(계약 2·3(b)·5(c), '거부해야 할 입력' 전부) base 7/7 PASS, 병합본 모의 7/7 PASS. 계약 1은 base에서 어긋나므로(모의: base 호출 0·`_RAIL_NETS` 1·
   `.source/.drain` 2 → 병합본 1·0·0) auditor 측정이 맞다. 1(d)도 같은 이유로 auditor 측정.
3. V3 -- B1·S3. 기본안 1(d)로 생존 0.
4. V4 -- 기대값은 손 리터럴, 두 피검 함수 교차 기대값 금지가 적혀 있음. 문제 없음(M4 잡음만).
5. topology 무관 -- 5(a) AST로 결정 가능(모의 새 문자열 0), 5(b)는 AST 참조 수로 바꿔야 결정적(S2), 5(c)는 test 판독, 5(d)는 문서 판독.
6. glob 충돌 -- 없음. `test_dup_kcl_edges.py`는 E1 `-k`에 걸리고, `*.py` 전수 스캔 test(ts3 print·GONE 이름·IC 표식)의 조건을 지키면 무해. GONE 목록에 kcl 관련 이름 없음.
7. 쓰기 경로 -- SD·레지스트리 = code-author(599·603), test = test-author(618), 판정 기록 = auditor(621·622). 맞음.

## 6. scratch

`C:/g35`: `mkhead.py`(모의 병합본 두 모양), `mut.py`·`mutb.py`(+ `mut.out.jsonl`·`mutb.out.jsonl`), `test_dup_kcl_edges.py`(후보 test), `inv.py`·`inv2.py`(인벤토리), `c15.py`(계약 1·3(a)·5(a)(b)),
`diffdup.py`(+ out). 검토 끝에 삭제.
