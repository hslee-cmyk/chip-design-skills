# 2차 독립 검토 -- V3 면제 묶기 card · V3 범위 정책 card(개정본, 사용자 승인 뒤 gate 전)

검토자: 2차 독립 reviewer(작성자·1차 검토자 아님). 저장소 읽기 전용(gate `master` HEAD `7535799`), 상태 변경 git 없음. scratch `C:/g65`(끝나고 삭제). `$PY` = `C:/Python314/python.exe -B`(3.14.2).
대상: `draft_v3_exempt_binding.spec.md`(id `20260930-v3-exempt-binding`), `draft_v3_scope_policy.spec.md`(id `20260930-v3-changed-stmt-scope`), `v3_cards_revision_log.md`, 1차 검토 `review_v3_cards.md`,
`v3_scripts/`(README), `user_decisions.md`(A1-a 승인, A1-b ② N2 (b)), `draft_v3_decision_question.md`(사용자가 본 문안), `review_b33.md` S6(번호 제안 34·35).
대조 원문: `tools/gates/mutate_changed.py` 전문, `reachability._approved_ids`·`_is_source`, `merge_gate.plan_tables_object`·N4.2 파서, redteam `lib/rt.py`(`subst_str`·`_file_content`·`build_vrepo`·`a_vcase`)·`lib/iface.vtool_command`·`run_all.py` 판정(80~102행),
기존 V3 redteam 케이스 v.json, design 05 317행, 계획 839·533행, design 10 382행, `tests/tools/engine_dup_scan.py`.

---

## 요약 판정

| card | 판정 | 막는 것 |
|---|---|---|
| 면제 묶기(34) | **gate 전 수정(should-fix 중심)** -- 1차 B1은 고쳐졌다(재현). 막는 결함 없음 | S1 번호, S2 공격 단계 판별력(유일 생존 조건), S3 `--out` 관찰 불가, S4 범위 card 뒤에도 케이스가 유효하게 |
| 범위 정책(35) | **gate 전 수정 필요** | **B1**: 승인 문안이 N2가 놓치는 것을 실제보다 좁게 적었다(같은 블록·한 단계·인접하지 않은 흐름도 놓침 -- 실측). 승인 기록 범위 설명 정정 + 사용자 한 줄 고지(또는 T6 보강) 필요 |

1차 검토 지적 처리: B1(docstring 밀림)·B2(머리만 바꾼 변경 대상 0)·S1·S3·S4·S5·S6·S7·S8·S9·S10·S11·M1~M7 모두 반영 확인(아래 §1). 적대적 동작 변경 21건 중 **N2가 지금 규칙보다 추가로 놓친 것 4건**, 그중 승인 문안에 적힌 공백 2건(1c·15), **적히지 않은 공백 2건(11·14)**(§2).

---

## 1. 1차 검토 지적이 실제로 고쳐졌는가(재현)

* **B1(묶기 해시) -- 고쳐짐.** 계약 머리의 정의(docstring·데코레이터 포함 원본 def의 `ast.dump(annotate_fields=True, include_attributes=False, indent=None, show_empty=False)` sha256)와 계약 1~4를
  프로토타입으로 구현(`C:/g65/scripts/bind_proto.py`, 도구 함수 읽기 전용 import):
  * `def f(x): y = clamp(x); log(y); return y`(Dk)와 docstring 한 줄만 더한 판 -- ① `def_hash` 같음(True), 묶기 해시 다름(False).
    원소 `m:f:stmt_delete:body[1]@<Dk 묶기 해시>`를 head(Dk+docstring)에 적용 → `run`, `exempt_ignored` = `hash_mismatch`(approved `14ac69c4…`, head `c989619b…`). Dk 자신에는 `exempt`.
  * 주석·서식만 바꾼 def(`# c`, 빈 줄, `return (y)`)는 묶기 해시 같음 -- 경로도 같으므로 면제 유지가 맞다.
  * 원소 분리 규칙: `X@<0*64>`, `X@H`, `X` 셋이면 `exempt`(계약 4). `X@<0*64>`, `X`, `X@abc`, `X@a@b`이면 실행 + `hash_mismatch`·`unbound`·`malformed`×2. 대문자 16진은 `malformed`(정규식 그대로 -- 결함 아님).
* **B2(머리만 바꾼 변경) -- 고쳐짐.** 계약 1 T5(`early_return` 무조건)로 해시가 바뀐 기존 def는 대상 ≥ 1이고, 인벤토리 0이면 그 변이가 생존 → FAIL. §2 표의 머리 변경 사례 1a·1b·1c·4b·10a·10b 모두
  N2 대상에 `early_return:body[0]`이 들어 있다(실측). 작성자 출력 `v3_b2_cases.txt`(bool·str·`None` 기본값, 이름 바꾸기, `*` 추가 = 2개, 쓰지 않는 매개변수 추가 = 1개, 데코레이터 추가 = 3개)과 같은 분류기를
  써서 같은 결과를 냈다.
* **데코레이터 NOOP(계약 9)**: 첫 데코레이터 줄부터 바꾸는 판으로 `@functools.lru_cache(maxsize=…)` 상수 변이가 실제로 적용되어 `cache_info().maxsize`를 보는 test가 죽인다(§2 사례 10a, strong만 죽임 2).
  지금 도구로는 같은 변이가 NOOP(작성자 `v3_probes.txt` 재확인).
* S6(삭제): 블록 안 삭제 → 감싸는 `if`(T4)·바로 뒤 문장(T6)이 대상, `else` 절 통째 삭제는 T4만(§2 사례 15) -- 계약 6이 적은 공백 그대로.
* S1·S3·S4·S5·S7·S8·S9·M1·M2·M5·M6: 문장 반영 확인. 줄 번호는 §4.

---

## 2. N2(b) 적대적 동작 변경 -- 21건 실측

방법(`C:/g65/scripts/adv.py`): 사례마다 base·head 모듈, **weak test**(base·head 모두 통과 -- 변경을 관찰하지 않지만 그 밖에는 성실한 test), **strong test**(base 실패·head 통과 -- 변경을 관찰). 작성자
분류기(`v3_scripts/v3_scope_classify.classify`, 계약 1 구현)로 정의별 대상을 고르고, 변이마다 계약 9 판 `_replace_def`로 소스를 바꿔 실행해 weak·strong이 죽이는지 기록했다.
'weak만으로 판정' = 그 정의에서 weak test 하나로 V3가 PASS인가(PASS면 **변경을 관찰하는 test 없이 병합 가능**). '변경 고유' = weak은 못 죽이고 strong만 죽이는 대상 변이 수(변경을 실제로 판정하는 변이).

| # | 동작 변경 | 지금(def 전체) 대상 / weak 판정 / 변경 고유 | **N2(b)** 대상 / weak 판정 / 변경 고유 | 분류 |
|---|---|---|---|---|
| 1a | `**kw` 전달 bool 기본값 `exact=False→True` | 4 / PASS / 0 | 2 / PASS / 0 | 기존 연산자 한계(bool 변이 없음) -- 차이 없음 |
| 1b | `**kw` 전달 int 기본값 `scale=2→3` | 6 / FAIL / 2 | 4 / FAIL / 2 | def 자기 필드 const±로 덮음 |
| 1c | bool 기본값 → 별칭 `s = strict` → 바뀌지 않은 `if s and x < 0` | 8 / FAIL / 3 | **2 / PASS / 0** | **N2가 놓침** -- 승인 문안의 '매개변수 값이 다른 이름을 거쳐 흐르는 문장'(적힌 공백) |
| 2 | 모듈 수준 상수 `THRESH = 5→6`(바뀌지 않은 def가 읽음) | 0 / PASS / 0 | 0 / PASS / 0 | 기존 공백(V3는 def만 본다) -- 차이 없음 |
| 3a | 문장 안 helper 이름 `ha(x)→hb(x)` | 3 / PASS / 0 | 3 / PASS / 0 | 기존 연산자 한계(이름 교체 없음) |
| 3b | 모듈 수준 `helper = ha → hb` | 0 / PASS / 0 | 0 / PASS / 0 | 기존 공백 |
| 4a | 문장 안 lambda `r[0] → -r[0]` | 5 / FAIL / 2 | 5 / FAIL / 2 | 새 문장으로 덮음 |
| 4b | 기본값 lambda `key=lambda r: r[0] → -r[0]` | 4 / FAIL / 2 | 4 / FAIL / 2 | def 자기 필드로 덮음 |
| 5 | 컴프리헨션 필터 `v > 0 → v >= 0` | 8 / FAIL / 1 | 8 / FAIL / 1 | 덮음 |
| 6 | 문장 순서 바꾸기 | 10 / FAIL / 7 | 6 / FAIL / 4 | 덮음(옮긴 문장 = 새 문장 + T6) |
| 7 | `raise ValueError → KeyError` | 7 / PASS / 0 | 6 / PASS / 0 | 기존 연산자 한계 |
| 8 | 반환식 피연산자만 `a + b → a + c` | 3 / PASS / 0 | 3 / PASS / 0 | 기존 연산자 한계(이름 교체 없음) |
| 9 | dict 리터럴 키 `'gain' → 'gm'` | 2 / PASS / 0 | 2 / PASS / 0 | 기존 연산자 한계(문자열 변이 없음) |
| 10a | 데코레이터 인자 `maxsize=128→1` | 7 / FAIL / 2 | 3 / FAIL / 2 | 덮음(계약 9 수정 전제 -- 지금 도구는 NOOP라 strong으로도 생존) |
| 10b | 데코레이터 문자열 인자 `@register('a')→('b')` | 5 / PASS / 0 | 1 / PASS / 0 | 기존 연산자 한계 |
| 11 | `mode = 'fast'→'exact'`, 한 문장 건너 같은 블록의 `if mode == 'exact':`가 사용 | 13 / FAIL / 6 | **6 / PASS / 0** | **N2가 놓침 -- 승인 문안에 없는 공백**(같은 블록·이름 한 단계·인접 아님) |
| 11b | 11과 같되 사용하는 `if`가 바로 뒤 문장 | 13 / FAIL / 6 | 4 / FAIL / 2 | 덮음(교체도 삭제 지점을 만들어 T6가 바로 뒤를 본다) |
| 12 | 문장 삽입 `y = max(y, 0)` | 9 / FAIL / 3 | 4 / FAIL / 3 | 덮음(삽입 문장 `stmt_delete` = 되돌리기) |
| 13 | `elif x > 5 → x > 6` | 18 / FAIL / 1 | 9 / FAIL / 1 | 덮음(T2) |
| 14 | `neg = False→True`, 두 문장 뒤 같은 블록 `if neg:` | 6 / FAIL / 2 | **3 / PASS / 0** | **N2가 놓침 -- 승인 문안에 없는 공백**(11과 같은 꼴) |
| 15 | `else` 절 통째 삭제(뒤의 `return y * 3`이 영향) | 15 / FAIL / 3 | 5 / FAIL(변경 무관 생존 1) / 0 | 승인 공백(블록 끝 삭제 -- 계약 6에 적힘) |

정리:
* 대상 변이 수: 지금 규칙 대비 N2는 사례마다 같거나 작다(합계 지금 146 / N2 80).
* **변경 고유 변이가 N2 대상에 하나도 없고 weak 판정이 PASS로 바뀐 사례 = 1c·11·14**(15는 weak FAIL이지만 그 생존은 변경과 무관한 `x > -1` -- 변경 고유 0). 이 넷이 '바뀌지 않은 문장 제외'로 새로 잃는 것이다.
* 1a·2·3a·3b·7·8·9·10b는 **두 규칙 모두** 변경을 관찰하지 않는 test로 통과한다 -- 연산자 집합(bool·문자열·이름·예외 종류 변이 없음)과 'def만 본다'의 기존 한계이고 N2의 새 구멍이 아니다(백로그 후보, §5 M3).
* 2·3b(모듈 수준 변경): 두 규칙 모두 변이 0개 → test가 하나도 없어도 V3 PASS. 범위 card 계약 2("해시가 바뀐 **기존 def**마다 대상 ≥ 1")와 결정 질문 문장("바뀐 def에 닿는 test가 없으면 FAIL")은 def에
  한정해 말하므로 거짓은 아니다.

---

## Blocking

### B1. [범위 정책] 사용자가 승인한 문안은 N2가 놓치는 흐름을 "다른 블록이나 두 단계 이상"으로 적었는데, 실제 규칙은 **같은 블록·이름 한 단계라도 바로 뒤가 아니면** 놓친다

* 사용자가 본 결정 질문 표 선택지 2 '놓치는 결함' 칸: "바뀐 값이 **다른 블록이나 두 단계 이상**을 거쳐 흘러드는 바뀌지 않은 문장, 매개변수 값이 다른 이름을 거쳐 흐르는 문장, 블록 끝에서 지운 절의 뒤 영향".
  이 문안은 '같은 블록 안에서 이름 한 단계로 흐르는 문장은 덮는다'로 읽힌다.
* 실제 규칙(계약 1): 바뀐(교체된) 단순문은 `replace` 구간의 짝 없는 base 원소 때문에 삭제 지점 `j2`를 만들고, T6는 그 **바로 뒤 문장 하나**만 본다. 그래서 덮이는지가 **인접 여부**로 갈린다
  (실측 §2: 사례 11b 인접 → 변경 고유 2개 대상, 사례 11·14 한 문장 건너 → 변경 고유 0, weak test로 PASS). 반복문의 다음 회차로 흐르는 **앞** 문장도 같은 블록·한 단계지만 대상 밖이다.
  card 본문 '작성 전 실측' 4는 "같은 블록 바로 뒤 문장만 T6로 본다"고 정확히 적었으나, 사용자에게 간 문안과 계약 10의 design 05 새 문구("지운 문장 자리의 **앞뒤**")는 실제보다 넓게 적었다(S6과 함께).
* 왜 막는가: 약화 승인(DEC-40 -- 매 건 사용자 승인)의 범위 설명이 실제 약화보다 작다. 승인 기록 범위 설명을 그 문안대로 쓰면 '승인 범위 밖 약화'가 기록에 남는다(작성자≠검증자, 보고 수치·판정은 측정 기반).
* 고칠 것(둘 중 하나, 오케스트레이터가 고르고 사용자에게 한 줄 고지):
  1. **문안 정정(규칙 유지)**: 승인 기록 범위 설명·card 의도·결정 필요 항목에 놓치는 것을 "바뀐·지운 문장 **바로 뒤 문장이 아닌** 바뀌지 않은 문장으로 흐르는 값(같은 블록이라도, 이름 한 단계라도), 반복문 다음 회차로
     흐르는 앞 문장, 매개변수 값이 다른 이름을 거쳐 흐르는 문장, 블록 끝에서 지운 절의 뒤 영향"으로 적고, 사용자에게 "승인하신 ② N2가 놓치는 범위를 정정합니다(같은 블록·인접하지 않은 흐름 포함). 그대로
     진행할까요?"를 한 줄로 알린다(규칙이 바뀌지 않으므로 재측정 불필요 -- B26-1 228 그대로).
  2. **T6 보강(문안에 맞춤)**: T6를 "바뀐·지운 문장이 대입하는 이름(`Store`)을 읽는 **같은 블록 뒤쪽** 문장의 몫(이름 한 단계)"으로 넓힌다. 문안이 약속한 범위로 규칙을 올리는 강화 쪽 변경이라
     새 약화 승인은 필요 없지만 승인한 정의와 달라지므로 사용자 고지는 필요하고, B26-1 수치(228)를 다시 재야 한다(상한 참고: D1 399 -- D1은 다른 블록까지 보므로 이것보다 크다).
  어느 쪽이든 redteam에 사례 11 꼴(인접하지 않은 같은 블록 사용)을 **기대값과 함께**(1이면 control exit 0 + `not_targeted` id, 2면 attack exit 1) 넣어 규칙을 고정한다.

---

## Should-fix

### S1. [두 card] redteam 번호가 아직 32·33이다 -- 34·35로
* 묶기 card 78·148·192행 `32-v3-exempt-binding`, 범위 card 83·85·147·214행 `32-…`·`33-v3-changed-scope`. `review_b33.md` S6 제안(D-18 원칙: 32 = G1 `32-moved-defs`, 33 = B33 `33-v7-registry-edges`,
  **34 = `34-v3-exempt-binding`, 35 = `35-v3-changed-scope`**, 병합 순서와 무관하게 미리 배정). 실측 `ls attacks/` 마지막 = `31-v3-git-history`, 32~35 없음.
* 고칠 것: 경로·계약 7 무동작 목록(`attacks/34-v3-exempt-binding/`)·'이름 충돌' 실측 문장을 바꾸고, "번호 머리가 겹친다 -- 나중에 병합하는 card가 번호를 바꾼다" 문장(묶기 148행, 범위 147행)을 "번호는 D-18 배정
  (34·35)"으로 바꾼다.

### S2. [두 card] 공격 단계 대부분이 '유일 생존' 조건이 없어 판별력이 없다(exit 1이 구현과 무관하게 나온다)
* `run_all.py` V 케이스 판정 = exit + `message_contains`(stdout·stderr 부분 문자열) + (`observe` 모드가 있을 때만) `observed_equals`(80~102행, `a_vcase` 611~624행). exit 1 기대 단계에서 다른 변이가 하나라도
  생존하면, 피검 구현이 그 단계가 겨냥한 동작을 빠뜨려도 exit 1이다.
* 묶기 card: (a)·(c)에는 'X가 유일한 생존 변이'가 있으나 **(b) `hash-mismatch`, (d) `bound-other-def`, (e) `docstring-shift`, (f) `malformed-element`에는 없다**. 예: 해시를 무시하고 id만 보는 구현(옛 누수)도
  (b)에서 다른 생존 변이가 있으면 exit 1이 되어 잡히지 않는다. (e)의 "① 해시로 묶었다면 exit 0"도 X가 유일 생존일 때만 참이다. (d)는 기대 `reason`이 없다(`hash_mismatch`일 것).
* 범위 card: (b)·(c)·(d)·(e)·(g)는 '좁힌 뒤에도 거부가 남는다'를 보이려는 attack인데, 겨냥한 변이(바뀐 문장·감싸는 `if a < b` `cmp_flip`·옮긴 문장·`for` 머리·삭제 뒤 `return`)가 **대상 변이 중
  유일한 생존**이어야 T1/T2/T4/T6를 빠뜨린 구현을 거부한다(빠뜨린 구현에서는 그 변이가 `not_targeted`가 되어 exit 0). (f)는 '대상 0 → exit 0' 구현을 겨냥하므로 지금 문장으로 판별된다.
  (a)의 "`not_targeted` ≥ 1"은 부분 문자열로 표현할 수 없다.
* 고칠 것: 각 attack에 "겨냥한 변이가 유일한 생존 변이(나머지 대상 변이는 test가 모두 죽인다)"를 넣고, 기대 출력을 `message_contains`로 쓸 **정확한 JSON 조각**으로 적는다(도구가 `json.dumps(…, ensure_ascii=False)`
  기본 구분자로 쓰므로 예: `"reason": "unbound"`, `{"id": "<X>", "reason": "hash_mismatch"`, `"not_targeted": 3`처럼 구성으로 정한 정확한 수). 계약 2·3의 레코드 키 순서(`id`, `reason`, …)를 '출력 순서'로 명시.

### S3. [두 card] `--out` 기록은 redteam V 케이스로 관찰할 수 없다 -- 판정 경로를 정해야 한다
* 묶기 계약 1("`exempt`를 `--out`에도 append")과 범위 계약 5(`not_targeted` 레코드를 `--out`에)는 새 관찰 동작이다. V 케이스는 `args`로 `--out <경로>`를 넘길 수는 있지만(`a_vcase`, 공격 28 선례)
  그 파일 내용을 읽는 `observe` 모드가 없다(`observe`는 `v4_first`·`tool_tmpdir`·`root_state`뿐). 게이트 도구에는 redteam 밖 unit test가 없다(`tools/gates/` 실측).
* 묶기 card 승인 범위 (ii)는 rt.py 동작 하나(`@bindhash(…)`)만 적었다. `--out` 관찰을 redteam으로 고정하려면 rt.py 동작이 하나 더 필요하다(예: `"observe": "out_jsonl"` → `--out` 파일의 `result` 값 목록을
  `observed`로) -- 승인 범위에 적어야 한다(선례 C10).
* 고칠 것: (가) rt.py `observe` 동작을 두 card의 승인 범위·쓰기 경로(test-author C10)에 추가, 또는 (나) `--out` 계약은 auditor 판정 기록에서 확인할 V2 항목으로 두고 card에 "redteam 고정 대상 아님"을 적는다.
  (나)를 고르면 WP-11 기록 누락 수정이 회귀 방지 없이 남는다는 것도 적는다.

### S4. [두 card 상호작용] 묶기 케이스(34)는 범위 card(35)가 병합된 뒤에도 같은 결과여야 한다 -- 지금 문장으로는 보장되지 않는다
* 순서는 두 card 모두 '묶기 먼저'로 일치하고 사용자 결정(A1-a: P9·P10·P10b 뒤, B26-1 전)과도 맞다. 그런데 범위 card 계약 7은 34 케이스를 "새 def이거나 def 전체가 바뀐 구성"으로 무동작이라 적었다.
  실측: 기존 V3 케이스(`v3_survivor`, 28의 4단계)는 모두 **새 def**(`rt_scale`)라 맞지만, 34의 (a)~(f)는 정의상 **기존 def를 바꾼다**(그래야 대상이 되고 면제가 걸린다).
  X가 head에서 바뀌지 않은 문장에 있으면 35 병합 뒤 X는 `not_targeted`가 되어 (a)는 exit 0(attack 실패), (c)의 `"result": "exempt"` 조각이 사라진다.
* 실행 여부와 면제의 우선순위도 없다: 묶기 계약 1은 대상 여부와 무관하게 '해시가 같으면 `exempt`'이고, 범위 계약 4·5는 대상 밖이면 `not_targeted`다. 둘 다 맞는 변이(묶인 면제가 있는 대상 밖 변이)의 결과 레코드가
  정해지지 않는다(판정은 같고 `--out`·카운트만 갈린다). 묶기 card의 '이번 실행의 변이 id' 정의는 `exempt_ignored`만 다룬다.
* 고칠 것: (i) 묶기 계약 9에 "X는 head def에서 base와 다른 문장의 부분 트리 안(범위 card T1 대상) 또는 `early_return`"을 넣는다 -- 범위 card가 나중에 와도 X가 대상으로 남는다.
  (ii) 범위 계약 4에 "대상 밖 변이는 면제 판정도 하지 않는다(`not_targeted`가 먼저)"를 넣고, 계약 7의 34 항목을 "(i) 조건으로 대상 집합 안 -- 결과 불변"으로 고친다.

### S5. [두 card] 결정이 끝났는데 card가 아직 '결정 대기'·선택지 정의를 품고 있다
* 범위 card: 의도 첫 문단 "선택적 게이트 변경(사용자 결정 대기)", '선택지별 대상 정의'(N2a·D1·N1), 계약 1 T3 "(a, 선택지 2a) 본문 전체", T7 "(선택지 3만)", 결정 필요 항목 "사용자 결정(대기)"·"선택지 1이면 … 별도 card".
  게이트 card의 계약은 하나의 규칙이어야 한다 -- code-author·test-author가 T3(a)·T7을 구현 범위로 오독할 여지가 있다.
* 묶기 card: 결정 필요 항목 "사용자 승인 요청".
* 고칠 것: 범위 card 계약 1에서 T3(a)·T7·N2a/D1 정의를 지우고(측정 비교는 '작성 전 실측' 1·2의 표로만), 의도·결정 필요 항목을 "사용자 결정 2026-10-01 A1-b ② N2, def 머리 변경은 (b)"로 바꾼다
  (원문 인용은 승인 기록에). 묶기 card는 "A1-a 승인"으로. 경위(개정 전 정의·옛 수치)는 history로(계획서=design, 이력=history 원칙).

### S6. [범위 정책, 문안] design 05 새 문구가 규칙보다 넓다 -- "지운 문장 자리의 앞뒤"
* 계약 10 새 ① 문구와 의도 절: "지운 문장 자리의 **앞뒤**". 규칙 T6는 삭제 지점 **뒤** 문장 하나뿐이고(T4는 감싸는 복합문), 앞 문장은 대상이 아니다. 또 문구에 T3(b)의 'def 자기 필드(기본값·데코레이터 인자)'가 빠졌다.
  승인 문안(A1-b)의 "삭제 지점 주변"과도 문자 그대로 맞추는 편이 안전하다.
* 고칠 것: "… 감싸는 제어문·바꾸거나 지운 문장 자리 바로 뒤 문장·def 머리가 바뀌면 그 자기 필드와 바뀐 매개변수를 읽는 문장·`early_return`(정의: spec card … 계약 1)"로. 계획 N4.2 문구는 card를 참조하므로 그대로 둬도 된다.
  (확인: N4.2 V3 칸은 `plan_tables_object` 입력이 아니다 -- `v_intro`는 '도입' 칸만 읽는다, `merge_gate.py` 124~133행 실측. 문구 변경이 표 해시를 바꾸지 않는다.)

### S7. [범위 정책] G1과의 순서가 이제 정해졌다 -- 조건문 대신 확정 문장으로
* A2 승인(B26-1·B34를 Phase 3 모듈 분할보다 먼저)과 A1-a/b 순서(묶기 → 범위 → B26-1)로 범위 card가 G1(Phase 3)보다 **먼저** 병합된다. 범위 card 계약 3·결정 필요 항목은 아직 "G1이 먼저면 / 나중이면" 두 갈래다.
* 고칠 것: 계약 3을 "새 def = base 같은 경로에 같은 qualname이 없는 def"(지금 규칙)로 확정하고, "G1 card(나중)가 계약 4에 'def 안의 변이 선택은 `20260930-v3-changed-stmt-scope` 계약 1 그대로'를 더한다"를
  G1 초안(`draft_p3_g1.spec.md`) 수정 항목으로 오케스트레이터 백로그에 올린다.

---

## Minor

* M1 [묶기] **실수 표기만 다른 상수는 묶기 해시가 같고 변이가 다르다.** `return x * 0.5`와 `x * 0.50`은 AST가 같아 묶기 해시 같음(실측 True), 같은 id `const+:body[0].value.right`의 변이는 `0.6` 대 `0.51`
  (단위가 `ast.get_source_segment` 표기에서 나온다 -- `mutants` 164~166행). 승인한 등가 판단은 0.6에 대한 것이었다. 의도 절 "면제가 그 문장에 정확히 적용된다"는 노드 기준으로는 맞지만 변이 기준으로는
  아니다. 고칠 것(택1): 묶기 해시 입력에 def 안 `float` 상수의 원문 표기 목록을 더하거나, 계약에 "실수 표기 변경은 같은 해시 -- 등가 판단은 표기와 무관한 경우에만 승인"을 적는다. 실제 발생 가능성은 낮다.
* M2 [묶기] rt.py `@bindhash(<base|head>:<경로>:<qualname>)` 치환 순서: `_file_content`는 `str` 명세에만 `subst_str`를 돌리고 `{"text": …}` 명세에는 `replace`만 한다(491~508행). 자리표시자는 명세 종류와
  무관하게 **모든 파일 내용을 만든 뒤 두 번째 단계**에서 치환하고, 자리표시자가 든 파일을 참조할 수 없다(순환 금지)고 적는다. 참조 파일이 사전에 없으면 RuntimeError(조용한 통과 금지).
* M3 [두 card, 기존 한계 -- 백로그] §2의 1a·3a·7·8·9·10b(bool·문자열·이름·예외 종류·비숫자 데코레이터 인자 변경)와 2·3b(모듈·클래스 수준 변경)는 지금 규칙에서도 변경을 관찰하지 않는 test로 V3 PASS다.
  N2의 새 구멍은 아니지만, '어느 선택지든 바뀐 def에 닿는 test가 없으면 FAIL'이 모듈 수준 변경에는 해당하지 않는다는 점을 백로그 한 줄로(연산자 확장·모듈 수준 상수를 읽는 def를 대상으로 삼기 검토).
* M4 [묶기] design 10 382행 "`target_kind: decision` 승인 기록(**변이 id 목록**)으로만 면제한다" -- card 실측 5는 "형식 주장 없음 -- 그대로"라 적었지만 원소 형식을 말한다. C8 서술(이력)이라 고치지 않는다면
  card에 그 판단을 그대로 적는다.
* M5 [두 card] 출력 세부: `exempt_ignored` 원소 순서(계약 4 '원소마다' -- 정렬 기준), 범위 card 뒤 출력 `mutants`(=`len(results)`)에 `not_targeted`가 드는지. 판정과 무관하나 redteam 조각과 auditor 보고 수치가
  갈릴 수 있다.
* M6 [참고] D1(선택지 3)의 T7은 def 머리 변경을 '바뀐 영역'에 넣지 않아 사례 1c도 놓친다(실측 D1 대상 2 / PASS). 선택되지 않았으므로 결정 질문 이력 메모로만.

---

## 3. 두 card 함께 -- 순서·상호작용·redteam 판정 가능성

| 항목 | 판정 | 근거 |
|---|---|---|
| 순서 | 맞음: 묶기(34) → 범위(35) → B26-1. G1(Phase 3)은 그 뒤 | 두 card 의도 절, `user_decisions.md` A1-a·A2. S7 |
| 면제 × `not_targeted` | 정의 없음 | S4 (ii) |
| 34 케이스가 35 뒤에도 유효 | 보장 안 됨 | S4 (i) |
| 묶기 redteam (a)·(c) red | 판정 가능 -- (a) base exit 0(해시 없는 원소 경로 적용, X 유일 생존), (c) base exit 1(`X@H`는 어떤 id와도 다름) | `mutate_changed.py` 375행 `if mid in approved` |
| 묶기 (b)(d)(e)(f) | 판별력 부족 | S2 |
| 묶기 rt.py 추가 | `@bindhash`는 승인 범위 (ii)에 있음. `--out` 관찰은 없음 | S3, M2 |
| 범위 redteam (a)·(h) red | 판정 가능 -- (a) base는 S 생존으로 exit 1, (h) base는 데코레이터 NOOP 생존으로 exit 1 | `_replace_def` 199·203행 |
| 범위 (b)(c)(d)(e)(g) | 판별력 부족, (a) `≥ 1` 표현 불가 | S2 |
| 범위 rt.py 추가 | 선언 없음 -- (a)~(h)는 `message_contains`로 가능(S2대로 고치면). `--out`은 S3 | `run_all.py` 92행 |
| B33(V7 그래프 → V3 인벤토리)과 | `review_b33.md` S6 주의 그대로: 34·35가 먼저면 B33 계약 14에서 34·35 합성 기대가 다시 판정된다 | -- |

## 4. 사실 재측정(HEAD `7535799`)

| card 문장 | 실측 |
|---|---|
| `mutate_changed.py` `exempt` `continue` 375~377, `--out` append 394~396 | 일치 |
| `main` base 읽기 359~364, `changed_defs` `bmap` 91~95, `mutants` bool 제외 160 | 일치(`bmap`은 90행 초기화) |
| `_approved` 219 | def 218행, 반환 219행 -- 일치로 봄 |
| `_replace_def` `fn.lineno`·`decorator_list = []` | 199·203행 일치 |
| `reachability._approved_ids` 180, `test_lint.py` 731 | 일치(729행 주석) |
| rt.py `subst_str` 39~48, `_commit_case` 446·459, `build_vrepo` 523 | 일치 |
| `engine_dup_scan.py` 102~122 | 일치(함수 101행, 머리 블록만 읽음 -- `_approved_ids`와 다름) |
| `topology_library.py` 248 `@functools.lru_cache(maxsize=256)` | 일치 |
| design 05 317행 V3 행 ⑤ 문구, 계획 839행 V3 행, 533행 이동 규칙 | 일치 |
| `merge_gate.plan_tables_object` 입력 = `v_intro`·`ic_parts`·`ic_test`·`phase_order`·`write_paths`, `v_intro`는 N4.2 '도입' 칸만 | 일치(158~168, 124~133행) |
| 기존 V3 redteam 케이스 = 새 def만 바꿈 | `v3_survivor` 2단계·28 4단계 모두 `rt_engine.rt_scale` 새 def(실측) |
| `attacks/` 마지막 `31-v3-git-history`, 32~35 없음 | 일치 |
| `ast.dump` 서명(3.14.2) | 일치 |

## 5. 승인 범위와 문구(design 05·N4.2) 대조

* **묶기 card** -- 승인(A1-a): "면제 = 변이 id@함수 원본 해시(docstring·데코레이터 포함), 해시 같을 때만 적용". 계약 10 design 05 ⑤·N4.2 새 문구는 이 범위와 정확히 같다(추가 약화 없음, 강화).
  rt.py 동작 추가·인터프리터 판·재시도 재승인은 승인 범위 설명 (ii)~(iv)에 있음. S3를 (가)로 고치면 (ii)에 rt.py 동작 하나를 더 적어야 한다.
* **범위 card** -- 승인(A1-b): "바뀐 문장 + 감싸는 제어문 + 삭제 지점 주변 + 새 함수 전체 + 항상 early_return(def 머리 변경은 (b) 좁은 판)", "놓치는 것: 바뀌지 않은 문장의 기존 test 강도".
  규칙(계약 1 N2 = T1·T2·T3(b)·T4·T5·T6)은 이 목록과 같다 -- **승인 밖의 추가 약화 규칙은 없다**. 문제는 문안이다: (1) 놓치는 범위 설명이 실제보다 좁다(B1), (2) design 05 새 문구 "앞뒤"가
  규칙보다 넓다(S6). 계약 9(데코레이터 NOOP 수정)는 강화이고 결정 질문에 고지됐다.

## 6. 측정 방법(재현용 -- scratch는 지웠다)

* `C:/g65/scripts/sim_head.py`: 도구 `mutate_changed`·`reachability`를 저장소 `tools/gates`에서 읽기 전용 import만 하는 대체 모듈(작성자 분류기가 `sim_head`를 import하므로).
* `C:/g65/scripts/v3_scope_classify.py`: `_drafts/v3_scripts/v3_scope_classify.py` 사본(경로 `C:/g60` → `C:/g65`만 바꿈), `classify`·`DEFS`(N2b = card N2) 사용.
* `C:/g65/scripts/adv.py`: §2 21건. 사례마다 base·head 소스 문자열, weak·strong test 함수 문자열. 변이 적용은 계약 9 판 `_replace_def`(첫 데코레이터 줄부터 `ast.unparse`), 모듈을 `exec`하고 test를 부른다(예외 = 죽음).
  sanity(weak가 base·head 통과, strong이 base 실패·head 통과)를 21건 모두 확인.
* `C:/g65/scripts/bind_proto.py`: §1 B1·원소 규칙·M1(실수 표기).
* 실행: `PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -B <스크립트>`. 저장소 `tools/gates/__pycache__`는 2026-09-21 기존 파일(이번 실행이 만들지 않음, `.gitignore` 대상), `git status` 변화 없음.
