# review3 -- B33 착수 키트 편집 독립 검토(작성자 아님)

검토 2026-10-01. 대상: `draft_b33.final.spec.v1.md` → `draft_b33.final.spec.md`, `approval_20260930-v7-registry-edges.v1.md` → `.md`, `b33_briefs.md`, `b33_kit/`.
재측정: gate master `0f237862c007f6a53122f2bdfb3c87e6366ec133`(gate `refs/heads/master`를 `ls-remote`로 확인)을 작업 저장소에서 `C:/g122/r`로 복제(origin 제거, 빈 hooksPath)해서 키트 스크립트를 그대로 실행.
잘못된 구현 시제품은 키트 `reachability_b33.py` 사본에 구멍 하나씩만 연 변형을 더해 만들었다(`C:/g122/kit/reachability_holes.py`, 검토용, 삭제함). 저장소 `git status --short`는 시작 때와 같다(diff 0).

## 판정: 조건부 통과(blocking 0 / should-fix 1 / minor 4)

## (1) 사용자 승인 범위 -- 범위 안(넓히지도 좁히지도 않음)

* 사용자 답(세션 jsonl AskUserQuestion 2026-10-01T04:33:58Z) (a)의 선택지 설명 원문: "Cls(...)와 raise Cls가 있을 때만 생성자가 도달한 것으로 봅니다. 엄격한 쪽입니다. defaultdict(Cls) 같은 팩토리 모양은 거짓 FAIL이 나며, 면제 승인으로 처리합니다." (b): "isinstance나 except에만 쓰인 클래스의 생성자도 '도달'이 됩니다."
* 새 계약 4 문장(팩토리 = 호출 위치가 아님 → `Cls.__init__` 미도달, exit 1)과 계약 8 문장(같은 면제로 exit 0), 단계 `ctor-factory-limit`(exit 1)·`ctor-factory-exempt`(exit 0, `unreached`=[`RtFac.__init__`], `uwa`=[])는 이 설명을 그대로 옮긴 것이다. 범위를 넓히는 새 규칙은 없다(면제 경로는 원래 있던 V7 메커니즘).
* 넓힘을 거부하는가(실측): 클래스 이름 참조 전부를 생성자로 보는 (b) 구현(`q1b_nameref`) → `ctor-isinstance-only`·`ctor-factory-limit`·`ctor-factory-exempt` FAIL. 호출 인자로 넘긴 클래스를 생성자로 보는 중간안(`q1_factory`) → 같은 3단계 FAIL(이 변형은 `isinstance(v, RtOnly)`의 인자도 잡아서 isinstance 단계까지 떨어졌다. 팩토리만 넓히는 구현이면 `ctor-factory-limit`·`ctor-factory-exempt`만 FAIL할 것). 그래서 (a)가 아닌 구현이 조용히 들어올 수 없다. 이것이 사용자가 고른 엄격도다.
* 좁힘 없음: 개정 시제품(`fixed`, card 문장 구현)이 28/28 PASS. (a)를 지키는 구현을 거부하는 단계는 없다.
* 단계 수 일관성: red 12 + 거부 11 + known_limit 1 + 대조군·면제 4 = 28. spec '판정 유형 근거'·승인 초안 범위 설명·briefs가 서로 맞는다.

## (2) 승인 초안 원문 인용과 수치 재현

| 항목 | 주장 | `0f23786` 재측정(C:/g122) | 결과 |
|---|---|---|---|
| 질문 원문 두 개·선택지 라벨 | 바이트 단위 부분 문자열 | `check_user_quote.py` → `question_in_draft [true,true]`, `options_in_draft [true,true]` | 재현 |
| 미도달(합집합 루트, R3) | 115 → 39 | base 115(R3만 116), fixed 39. 두 벌 base 116/122 → 39/39 | 재현 |
| 비운영 노드 누수 | 66 → 0 | 66 → 0(R3) | 재현 |
| V3 쌍 | 34,163 → 44,765(×1.310) | 34,163 → 44,765(×1.3103), test 함수 478 | 재현 |
| 인벤토리 0 / 중앙값 | 82 → 19 / 61 → 67 | 82 → 19(fixed − base 차집합 0) / 61 → 67, `SemiEmpiricalGmIdLUT.__init__` 0 → 259 | 재현 |
| 계약 9 | 옛 간선 제거 3(전부 dunder), 도달 감소 0 | 3(`InfeasibleSizingError.__init__`), 전부 dunder, 도달 감소 0(세 루트 벌, R3 있이·없이) | 재현 |
| 정적 인벤토리(m5) | `width_from_id_density` 237/259, `compute_metric` 82/87 등 | 같음 | 재현 |
| 과거 V7 쌍 | 29건·29쌍 전부 불변 | 스캔 29건·정규식 36·서로 다른 쌍 29. 29/29 `same_fixed` true, 전부 PASS, `--config` 전부 head 트리, new_defs 있는 쌍 4개(ic3 2·df36 1·dup-w-calc 1·restore 2) | 재현 |
| 공격 33 | base 13 FAIL / 시제품 28 PASS | `run_attack33.sh` 표가 키트 `a33f_0f23786.table.md`와 diff 0. 합계 base FAIL 13·PASS 15, fixed PASS 28 | 재현 |
| 잘못된 구현(spec 문장) | draft 5·loose 7·nosuper 1 FAIL | 28단계에서 draft 5(external-attr·name-strings·local-shadow·reexport-other·super-leak), loose 7(앞 5 + attr·str-collision), nosuper 1(super-chain) | 재현 |
| `build_graph` 시간 | 보고 수치(임계값 없음) | HEAD 도구 3.9초, fixed 5.0초(다른 측정과 동시) | 참고 |

질문 속 "27건"은 질문 시점 값이고, 승인 초안 주석이 28(`2d58fd8`)과 29(`0f23786`)를 따로 적었다. 맞다.

## (3) 독립 검토 구멍 3건 -- 구멍마다 잘못된 시제품(그 구멍 하나만 연 것)

| 구멍 | 잘못된 시제품(fixed + 그 구멍 하나) | 28단계 중 FAIL | 판정 |
|---|---|---|---|
| B1 `super().__init__` 누수 | `h1_dunder`: dunder 속성 전역 폴백 되살림 | `ctor-super-leak`(exit 0) | 막힘 |
| B1 변형 | `h1_superbyname`: `super().__d__`를 같은 이름 전체 def로 | `ctor-super-leak`(exit 0) | 막힘 |
| B2 그래프 밖 재수출 | `h2_byname`: 재수출 = 같은 이름 바인딩 전체 | `registry-external-attr`·`registry-reexport-other` | 막힘 |
| B2 핵심 | `h2_extfb`: M이 그래프 밖이면 이름으로 폴백 | `registry-external-attr` | 막힘 |
| B2 변형 | `h2_chase_xout`: M은 그래프 안이고 M의 `from X import NAME`에서 X가 그래프 밖이면 이름으로 폴백 | **28단계 전부 PASS**(검토용 탐침 단계에서만 FAIL) | **구멍 → S1** |
| B3 속성만으로 도달 | `h3_attr`: 비모듈 속성 → 같은 이름 바인딩 | `registry-attr-collision` | 막힘 |
| B3 문자열만으로 도달 | `h3_str`: 문자열 상수 → 같은 이름 바인딩 | `registry-str-collision` | 막힘 |
| (참고) S1·S2 | `s1_strbind` / `s2_noshadow` | `registry-name-strings` / `registry-local-shadow` | 막힘 |
| (참고) import 없는 맨 이름 | `h3_name`: import 없는 맨 이름 → 다른 파일 같은 이름 바인딩 | **28단계 전부 PASS** | minor m1 |

`fixed`는 검토용 탐침까지 29/29 PASS다(규칙 문장 자체는 맞다).

## should-fix

**S1. 재수출 사슬의 X가 그래프 밖인 경우를 고정하는 단계가 없다.** 계약 1과 R1 (iv)는 "M·X는 그래프 안 모듈"이라 하는데, 단계 `registry-external-attr`는 M이 그래프 밖인 경우(`math.pi`)만 본다. 엔진이 `from math import pi`를 하고, 하네스가 `from rt_engine import pi`로 읽고, 다른 소스 `rt_other.py`에 고아 `pi = {"q": _f_q}`가 있는 경우를 보자. 사슬 끝(X = math)에서 이름 폴백하는 구현은 28단계를 전부 통과하면서 `_f_q`를 거짓 도달시킨다(실측, 탐침 `probe-reexport-x-outside` exit 0). 승인 질문의 "그래프 밖 재수출" 구멍과 같은 계열이다. 고칠 곳: 거부 단계 1개를 더한다(위 구성, 기대 exit 1, `uwa` = [`A/rt_other.py::_f_q`]). base 도구는 바인딩 간선이 없으므로 이 단계에서도 exit 1일 것이다(다른 거부 단계와 같은 성격, 키트로 재확인 필요. 실측한 것은 `draft`·`loose`·`h2_byname`·`h2_chase_xout` exit 0, `fixed` exit 1). 단계 수가 29가 되므로 승인 초안 범위 설명의 단계 수와 '거부 11 → 12', '판정 유형 근거'를 함께 고친다. 대신 범위 밖이라고 보면, 알려진 한계에 "X 그래프 밖 사슬은 시험하지 않음"이라고 적어 정직하게 남긴다. 어느 쪽이든 승인 문장(R1 (iv))은 바뀌지 않는다.

## minor

* m1. `h3_name`(import 없는 맨 이름 → 다른 파일 같은 이름 바인딩)이 28단계를 전부 통과한다. 계약 1 본문("import 없이 다른 파일에 있는 같은 이름 … 바인딩으로 가지 않는다")을 고정하는 단계가 없다. 실행 가능한 코드에서는 이런 참조가 드물다(내장 이름과 같은 바인딩, 예: 모듈 최상위 `len = {...}`). 그래서 구멍 3건 밖이다. 단계를 하나 더하거나(하네스에 import 없는 `_REG_Z` 참조 + 다른 파일 고아 `_REG_Z`), 그대로 둔다는 판단을 card에 적는다.
* m2. 승인 초안 '사용자 원문'은 질문과 라벨만 인용하고 선택지 **설명**은 빠졌다. 새 단계 `ctor-factory-limit`·`ctor-factory-exempt`와 "G1보다 먼저"의 근거가 바로 그 설명이다((a): "defaultdict(Cls) 같은 팩토리 모양은 거짓 FAIL이 나며, 면제 승인으로 처리합니다", 승인: "순서는 Phase 3 G1보다 먼저입니다"). 두 설명 원문을 괄호 안에 더하고 `check_user_quote.py`가 description도 대조하게 하면 근거가 완결된다.
* m3. spec '거부해야 할 입력' 절에 `ctor-factory-limit`(known_limit, exit 1)이 없다. 역할은 거부가 아니라 고정이지만 exit 1 기대 단계이므로 한 줄로 적어 두면 test-author가 헷갈리지 않는다.
* m4. 키트 `run_attack33.sh`/`run_redteam_variants.py`는 MSYS 경로(`/c/...`)를 받으면 Windows Python `subprocess(cwd=...)`에서 `NotADirectoryError`로 죽는다(첫 실행 재현). `C:/...` 경로를 써야 한다고 키트 머리말에 적는다. `run_headline.sh`는 두 형식 모두 된다. 그리고 이 측정은 기본 background 30분을 넘긴다(m4 29쌍 약 40분, 변형 1개 약 8~10분). 실행 시간 안내를 적는다.

## 결론

편집은 사용자 승인 안에 있다(Q1 (a)와 그 선택지 설명을 그대로 단계로 고정했고, (b)나 중간안을 거부함을 실측했다). 승인 초안의 질문 원문은 그대로이고 머리 수치는 `0f23786`에서 전부 재현된다. 구멍 B1·B3와 B2의 기본형은 단계가 실제로 거부한다. B2 계열 중 'X가 그래프 밖인 재수출 사슬'만 단계가 없다(S1). S1을 반영하거나 한계로 명시하면 착수할 수 있다.
