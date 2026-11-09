---
id: 20260930-v7-registry-edges
date: 2026-10-01
target_kind: diff
target: 200d6534ebf725401a8248c068cb7bc3d172da69d2d68e85722c2090226eeae3
diff_base: 0f237862c007f6a53122f2bdfb3c87e6366ec133
diff_head: fd9334adb0e252da92fa034922880259bfde3f2a
diff_path: docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
diff_path: docs/02-design/specs/20260930-v7-registry-edges.interface.md
diff_path: docs/02-design/specs/20260930-v7-registry-edges.spec.md
scope: 게이트 변경 spec card 20260930-v7-registry-edges(V7 reachability.py 정적 호출 그래프: R1 모듈 최상위 레지스트리 바인딩 간선, R2 생성자 간선 = 호출 위치만(Q1 (a)), R2' dunder 속성 전역 폴백 제거 + super().__d__ → 기반 클래스, R3 도달 계산은 소스 분류 노드 안에서만, 바인딩 값 문자열 상수는 간선 아님)와 design 05 §10 V7 행·거부 증명 줄 문구 개정 승인, V3 인벤토리 증가(1.31배) 수용 -- 강화(거짓 PASS 차단) + 거짓 FAIL 제거
---

## 사용자 원문

> 승인 (Recommended)

> (a) 호출 위치만 (Recommended)

(AskUserQuestion 2026-10-01 질문 원문 두 개:
첫째 -- "[B33] V7 호출 그래프를 고치는 게이트 변경(20260930-v7-registry-edges)을 승인하시겠습니까? 고치는 결함은 두 가지입니다. ① 레지스트리 dict와 클래스 생성자를 거치는 호출을 못 봐서, 실제로 쓰는 함수(_METRICS_REGISTRY의 metric 등)를 '도달 안 함'으로 셈니다. ② 반대로 test 파일의 같은 이름 함수로 간선이 새어 나가, 쓰지 않는 함수(size_transistor)를 '도달'로 잘못 셈니다(거짓 PASS). 고치면 미도달 함수가 115개에서 39개로 줄어듭니다. V3 인벤토리도 같은 그래프를 쓰므로 1.31배로 늘어납니다. 이는 레지스트리로만 불리던 metric 함수의 인벤토리가 0이라 반드시 FAIL하던 거짓 FAIL을 없애는 방향입니다. 독립 검토에서 나온 구멍 3건(super().__init__ 누수, 그래프 밖 재수출, 문자열과 속성만으로 레지스트리 도달)은 막았고, 과거 판정 기록 27건의 V7 결과는 그대로입니다." 선택지: "승인 (Recommended)" / "보류". 답: "승인 (Recommended)".
둘째 -- "[B33 Q1] 생성자 간선(R2)을 어디서 생기게 할까요? 지금 HEAD 기준으로는 두 선택지 모두 미도달 39개로 결과가 같고, 앞으로의 판정 엄격도만 다릅니다." 선택지: "(a) 호출 위치만 (Recommended)" / "(b) 클래스 이름 참조 전부". 답: "(a) 호출 위치만 (Recommended)".)

## 범위 설명

덮는 것:
* spec card `20260930-v7-registry-edges` 전체(계약 1~14)와 interface card. `tools/gates/reachability.py`의 `build_graph`·`main` 변경(code-author):
  * **R1 레지스트리 바인딩**: 모듈 최상위 단순 이름 바인딩(`NAME = <식>`, `NAME: T = <식>`)마다 바인딩 노드(`<파일>::=NAME`, 노드 집합 밖 -- 간선 사전에만). 바인딩 노드 → 값 식의
    이름·속성·생성자 참조. 바인딩으로 가는 간선은 네 형식뿐: 같은 파일 맨 이름(함수 지역 이름 제외), `from M import NAME`, `M.NAME`(모듈 별칭), M에 없으면 M의 `from X import NAME`을
    따른 재수출(M·X는 그래프 안 모듈, 순환은 방문 집합 -- 깊이 상수 없음). import 문장 자체는 간선이 아니다(R0 거절).
  * **바인딩 값 문자열 제외**: 바인딩 값 식 안의 문자열 상수는 간선을 만들지 않는다(함수 몸체·`<module>`·`__main__`의 기존 문자열 규칙은 그대로).
  * **R2 생성자 -- 호출 위치만(사용자 결정 Q1 (a))**: 도달 코드(바인딩 값 식 포함)의 `Cls(...)`·`raise Cls` → 그 클래스(없으면 기반 클래스, 재귀)의 `__init__`·`__new__`·`__post_init__`.
    `isinstance`·`except`·주석 등 호출이 아닌 클래스 이름 참조는 간선이 아니다. 받아들인 대가: 클래스를 값으로 넘겨 다른 곳에서 인스턴스화하는 모양(`defaultdict(Cls)`, `{"k": Cls}`,
    `field(default_factory=Cls)`)의 생성자는 미도달(거짓 FAIL) -- V7 면제 승인(`target_kind: decision`)으로 처리한다(HEAD에는 이 모양만으로 생성되는 클래스 0개).
  * **R2' dunder 규칙**: 속성 참조 `x.__y__`·`M.__y__`는 같은 이름 def 전역 폴백을 쓰지 않는다(모듈 별칭의 그 모듈 def는 그대로). `super().__d__`는 둘러싼 클래스의 기반 클래스의
    `__d__`로 간다. 옛 그래프에서 빠지는 간선은 이 dunder 폴백 간선뿐(HEAD 3개, 도달 감소 0 -- 계약 9로 auditor가 잰다).
  * **R3 운영 범위**: V7 `main`의 도달 계산은 소스 분류 파일(`_is_source`) 노드만 따라간다(test·probe·workspace 스크립트 def를 거친 도달은 세지 않는다). `build_graph`·V3는 R3를 모른다.
* V3(`mutate_changed.py`, 코드 변경 없음)가 같은 `build_graph`를 쓰는 데서 오는 인벤토리 변화 수용: (소스 def, 도달 test) 쌍 33,991 → 44,493(1.31배, 작성자 사전 실측 7535799 --
  판정 기록 수치는 auditor가 계약 12로 다시 잰다). 인벤토리는 실행할 test 집합일 뿐이라 기준 약화가 아니고(옛 인벤토리 ⊆ 새 인벤토리, dunder 폴백 간선 제외), 레지스트리 경유
  def의 '인벤토리 없음 → 생존' 거짓 FAIL을 없앤다. 새 위험(새 인벤토리 test의 기준 실행 실패 → `ERROR`, `--timeout` 초과 변이가 '죽인 변이'로 세짐)은 auditor가 기록한다(계약 12).
* 문서: design 05 §10 V7 행(그래프 규칙 명시)과 같은 절 거부 증명 줄(V7 → `redteam/v7_unwired`·공격 33). `reachability.py` 모듈 docstring 그래프 설명(code-author, 계약 13).
* redteam: 새 케이스 `tools/gates/redteam/attacks/33-v7-registry-edges/`(test-author, Phase 3 design D-18 배정 번호 33) -- 28단계(red 12 = V7 11 + V3 1, 거부 11, known_limit 1(팩토리 모양 `ctor-factory-limit` -- Q1 (a)로 받아들인 거짓 FAIL을 고정), 대조군·면제 4(그중 `ctor-factory-exempt` = 그 거짓 FAIL의 면제 승인 처리)).
  `lib/rt.py`는 바꾸지 않는다(단계별 `base`·head 승인 파일·`subjects`는 기존 `vcase`가 지원).
* 순서: B33을 G1(`20260930-p3-gate-move-aware`)보다 먼저 병합한다.

덮지 않는 것:
* 계획 121행 '운영 경로'·N4.2 V7 행(843행) -- 바꾸지 않는다(이 card는 게이트를 그 문구에 맞춘다). 판정 표(`plan_tables_hash` 입력)도 바뀌지 않는다.
* V3 대상 선택·연산자·면제·timeout 처리 -- 바꾸지 않는다(timeout을 별도 결과로 분리하는 변경은 백로그 후보). V3 면제 묶기(`20260930-v3-exempt-binding`)·범위 정책
  (`20260930-v3-changed-stmt-scope`)은 별도 승인.
* 알려진 한계(거짓 FAIL 쪽, HEAD 0건): 팩토리 모양 생성, 최상위 `REG["k"] = f`·`REG.update(...)`, `globals()` 컴프리헨션 레지스트리, 데코레이터 등록, `cls(...)`·`type(self)(...)`,
  클래스 본문 안 속성 대입 -- 간선을 만들지 않는다. 필요하면 V7 면제 승인(`target_kind: decision`).
* 이미 내려진 판정 기록 -- 바꾸지 않는다(착수 시점 gate master의 과거 V7 쌍 전부 -- `0f23786`에서 29개 -- 에서 verdict·unreached·unreached_without_approval 불변을 auditor가 계약 14로 확인).
* 면제 승인 `20260930-restore-unwired-until-6a`의 두 id -- 그대로(병합본 도구에서도 미도달인지 auditor 보고 수치).
