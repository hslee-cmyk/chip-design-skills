# 백로그 이관 문서 커밋 계획 (backlog_additions.md -> .ai/context.md)

작성 2026-10-01. 기준 gate/master = master = `0f23786`(측정 시점). 도구 `_drafts/patch_backlog.py`.

## 1. 정본 위치와 형식

* 정본: `.ai/context.md`(날짜순 진행 기록). gmid 문서 백로그는 진행 줄 사이의 `백로그 Bnn(...)` 문장(B20~B28)과
  `- 백로그 추가(<출처>, <날짜>):` 머리 줄 + `  - Bnn <내용>` 하위 항목(B29~B37·B32, gate 0f23786 15001~15010행) 두 모양이다.
  최신 모양은 후자라 이번에도 같은 모양을 쓴다.
* 다른 번호 체계(겹침, B31): history `docs/01-plan/features/gain-budget-gmid-sizing.history.md` §10.3의 B1~B25(엔진 결함 표, 3895행~)는
  같은 B 번호를 다른 뜻으로 쓴다. 이번 커밋은 context 쪽 번호만 잇는다(B31의 `BL-` 접두사 제안은 미결정 -- 이번에 바꾸지 않음).
* 파일: UTF-8(BOM 없음), 메인 작업 트리 LF(15,014줄, 끝 줄 바꿈 있음). `core.autocrlf=true`라 새 복제본은 CRLF로 풀릴 수 있다 --
  도구는 파일의 줄 끝을 따르고, 기존 바이트를 건드리지 않는다(메모리 규칙: heredoc append 금지, Python 바이너리 append만).

## 2. 들어가는 것(14줄 = 머리 1 + 항목 13, 6,194바이트)

| id | 처리 | gate 0f23786 재측정 |
|---|---|---|
| (머리) | `- 백로그 추가(2026-10-01, ... 이관 -- 줄 번호는 gate 0f23786 기준 재측정, B29~B37·B32는 위 블록에 이미 있음, B45는 G1 초안 v7 계약 4에 반영돼 뺌):` | -- |
| B35 보충 | 초안의 들여쓴 `(2026-10-01 추가)` 줄. 기존 B35 줄은 고치지 않고(삭제 0) 하위 항목 `B35 보충`으로 더함. 줄 번호 추가 | stick_diagram.py 2495 `if _netclass_al is not None:`, 4076 `if _idioms_lcmf is not None:`, 4100 `cascoded_active_load_legs = set()` 일치. B26-1 초안 v5 45행·B34 final 70·74행도 B35로 넘김 -- 여전히 유효 |
| B38 | **회수**: backlog_additions.md에 없던 번호. `draft_e4_clarify.md`의 "백로그 B38"(instance.json 2개 낡음) | 두 instance.json 3행 `topology_ref`가 `C:\\Users\\HSLEE\\...` 메인 절대 경로 -- 사실. sizing 값 차이는 `dryrun_phase2_e4.md` ④ 인용(재측정 안 함). 빼려면 `--skip B38` |
| B39 | 줄 번호만 추가 | 1333 `len(members) >= 2`, 3431 `def propose_theta_kcl_gap_fill` 일치. 변이 수 242·~48은 인용(재측정 안 함) |
| B40 | 줄 번호만 추가 | 3957 `"analog-grammar를 import할 수 없어 ..."` 일치(B26-1 v4가 이 분기를 지우면 해소 -- 아직 미병합) |
| B41 | 그대로 | 148bd6d 판정 기록 67·101행에 `20260922-ic3-v3-exempt`, 승인 파일 존재. v3-exempt-binding card 미병합이라 유효 |
| B42 | 근거 줄 추가 | mutate_changed.py 203 `nf.decorator_list = []`, topology_library.py 248 `@functools.lru_cache(maxsize=256)` 일치 |
| B43 | 근거 줄 추가 | mutate_changed.py 160 `not isinstance(node.value, bool)` 일치 |
| B44 | **문장 정정**: 초안 "2712~2718"은 def 2710·문구 2714~2716. "B34 병합 뒤 낡은"은 B34(`20260930-b34-grammar-explicit`) 미병합이라 "병합 뒤 낡는", 계약 test 파일은 "gate 0f23786에는 아직 없음" | 2710 `def test_s120_section(`, 2714 `analog-grammar 미설치 상황` 일치, `tests/contracts/test_b34_grammar_explicit.py` 없음 |
| B46 | 그대로 | (도구 연산자 집합 설명 -- B43과 같은 근거) |
| B47 | **문장 보강**: "다른 library md 일치 여부도 확인" -> 점검 결과(6개 중 2개 불일치, current_reuse md에 CL·Cf·Cs 없음)와 처리 방침 승인 기록 `20261001-b47-md-sync` | folded md 33행 M1 `vin_p`·36행 M2 `vin_n`, json M1 `vin_n`·M2 `vin_p`. current_reuse md에 `Cf` 0회. "나머지 4개 바이트 동일"은 오케스트레이터 점검 인용 |
| B48 | 근거 위치 추가 | spec card 20260930-df23-registry-record 119행 `assert len(findings) == 0` 우회 문장 일치 |
| B49 | 그대로 | design 20 190(P6)·192(P8) equivalence, 197행 "P7·P8은 red-green", "P5·P6·P9는 equivalence"; 두 판정 기록 `evidence_type` = red-green 일치 |
| B50 | 그대로 | stick_diagram.py 1584 주석 시작, 1595 "못 찾던 것만 보충", 1601·1605 `layer1_fallback` 일치 |

## 3. 빠지는 것과 이유

| id | 이유 |
|---|---|
| B29~B37, B32 | gate master `.ai/context.md` 15002~15010행에 초안과 **바이트 동일**하게 이미 있음(2140da8). 다시 쓰지 않음 |
| B45 | 해소: `_drafts/draft_p3_g1.spec.md`(=v7 이후) 97행 계약 4에 "def 안의 변이 선택은 `20260930-v3-changed-stmt-scope` 계약 1 그대로"가 이미 들어감. G1 card가 커밋되면 함께 들어간다 |
| (B28) | 초안 범위 밖이지만 참고: gate 8790b24로 병합 완료, 15000행 완료 기록 있음 |

## 4. 번호 겹침 -- 결정 필요(기본안 있음)

* Phase 4 설계 초안(`draft_phase4_design.md` 133·687·845행)과 `decision_package.md` 114행(U-27)이 **B48·B49·B50**을
  다른 뜻(VS 0.2 V 보간 오차 / sf_pushpull 경로 3 그룹 / 측정 사본 analog-grammar 동봉)으로 쓴다. 초안 자신이 "번호는 오케스트레이터가
  append 때 확정"이라 적었으므로 **기본안: backlog_additions.md의 B48~B50을 유지, Phase 4 제안은 B51~B53**.
  `--with-p4`로 세 줄을 함께 넣을 수 있다(+3줄, 합 17줄 7,151바이트). 넣으면 Phase 4 초안·decision_package의 'B48/B49/B50' 표기를
  B51/B52/B53으로 고쳐야 한다(초안 문서 몫). 기본 실행에는 넣지 않았다(B52는 b37a_revision_log §5 관찰 인용, 재측정 안 함).
* Phase 4 v0.3의 'B38'(바이어스 힌트)은 v0.4에서 철회됐으므로 B38 회수(instance.json)와 충돌하지 않는다.

## 5. 실행 순서와 주의

1. 메인 작업 트리에서 `C:/Python314/python.exe -B _drafts/patch_backlog.py --root <저장소> --check` -> "적용 가능" 확인.
   사실 검사(FACTS 25개)는 --root 작업 트리를 다시 잰다. 아래 병합이 먼저 들어오면 거부되며 그것이 정상이다:
   * B34 병합(`test_b34_grammar_explicit.py` 생김, stick_diagram 줄 이동) -> B35·B39·B40·B44·B50 문장 줄 번호 재측정 후 ITEMS·FACTS 갱신.
   * B47 재생성 문서 커밋(Change-Id 20261001-topology-md-sync) -> B47 문장을 "해소" 모양으로 바꾸거나 `--skip B47`.
   * B26-1 병합(사이트 정리) -> B40 확인.
2. 적용: 같은 명령에서 `--check` 뺌(기본 `--at eof`, 진행 기록 시간순; `--at after-backlog`는 B32 줄 바로 뒤 삽입 -- 둘 다 삭제 0).
   다시 실행하면 "이미 적용"(exit 0, 쓰기 없음). post_p10b_context_append.py(c1·b47)와 순서 무관(둘 다 끝 append, 표지 독립).
3. `git diff --numstat` = `14	0	.ai/context.md`(삭제 0 확인 -- 메모리 규칙) 뒤 커밋.

커밋 메시지(트레일러는 `--trailer`로):

```
git commit -F <msg> --trailer "Role: doc" --trailer "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

```
docs: 백로그 B35 보충·B38~B50 이관(.ai/context.md, gate 0f23786 기준 줄 번호 재측정) -- B38 회수(instance.json topology_ref 낡음), B45는 G1 초안 v7 반영으로 뺌
```

## 6. 드라이런 기록(격리 복제본 C:/g141/clone, origin 제거, 0f23786 checkout, autocrlf=false로 메인과 같은 LF)

* `--check` -> 적용 가능 +14줄(6,194바이트), 줄 끝 `\n`, 항목 B35 B38 B39 B40 B41 B42 B43 B44 B46 B47 B48 B49 B50.
* 적용 -> `git diff --numstat` = `14	0	.ai/context.md`; 시험 커밋(Role: doc, Co-Authored-By 트레일러) `git show --numstat` = `14	0	.ai/context.md`.
* 재실행 -> "이미 적용", exit 0, numstat 그대로.
* `--at after-backlog --with-p4` -> `17	0`, B32 줄(15010) 바로 뒤 삽입.
* 거부 경로 확인: 앵커 중복(`  - B32` 2번) exit 1, 부분 중복(`  - B41` 줄 존재) exit 1, 사실 불일치(current_reuse md에 `Cf` 추가) exit 1·쓰기 없음,
  모르는 `--skip` id exit 1.
* CRLF 복제본(autocrlf=true)에서도 `--check` 통과, 줄 끝 `\r\n` 감지.
* 복제본은 작업 뒤 삭제. 메인 저장소 쓰기·상태 변경 없음.
