# G1 dafe5cf 갱신분 독립 검증 (2026-10-06)

검증자: 작성자가 아닌 독립 agent. 실제 저장소는 읽기만(`git -C`), 측정은 `/c/g300`(TMP·TEMP도 그 아래, 끝나고 삭제).
gate `master` = 메인 `master` = `7243f28`.

## 판정: B 0 · S 1 · minor 5 — G1 card 커밋을 막는 결함은 없다. 사용자에게 물을 것도 없다.

| # | 항목 | 결과 |
|---|---|---|
| 1 | card sha256·절 대조·check_apr_draft·사용자 원문 | 통과 |
| 2 | noop 기준선 원인(자식 bash에서 env 소실 → pytest 없음 → BaselineFailed) | 재현함. 키트 수정은 맞다. 다만 autocrlf 처리에 S 1건 |
| 3a | 계약 12 `overwrite-similar` `not_targeted`=12 | 승인 범위 안이 맞다. 질문 필요 없음 |
| 3b | qualname 중복 문구 | 사실 맞음. 문구안도 맞음 |
| 4 | `7243f28`에서 mk-sandbox → kit-cmds → pre → local 리허설 | 전부 rc=0. push는 출력만 됨 |

## 1. card·승인 초안

* sha256을 다시 계산했다.
  * `draft_p3_g1.spec.md` = `72d8ff60eecc88015ab4d461cd7e1416819dc688d9bd87f0d6983a7845f515fd`
  * `.pre-35.bak` = `89719c85…`
  * `.pre-dafe.bak` = `a6615951…`(a17b8bd 판)
* `## ` 머리 기준으로 12블록(머리 블록 포함)을 바이트 단위로 대조했다. 세 판 모두 11블록이 같고 `## 작성 전 실측`만 다르다.
  * 같은 블록에는 `관찰 가능한 계약`(27,452바이트)이 들어 있다. 계약 0~13과 계약 12 redteam 표가 모두 이 블록 안이다.
  * 89719c85 → a6615951: +20줄(a17b8bd 문단), 지운 줄 0.
  * a6615951 → 72d8ff60: 273행 끝에 구절 하나, dafe5cf 문단 7줄, 문단 순서 줄 교체.
  * 승인 초안 pin 문단의 서술과 정확히 일치한다.
* 사용자 원문: 세션 jsonl의 tool_use `toolu_01VKN8qT3BbTikfZQyV9sdQi`(UD-5)와 바이트로 대조했다.
  * 질문, 선택지 3개(라벨과 설명), 답 `(가) 전역 이동 인식 (Recommended)`가 모두 초안에 있다.
  * 답 시각은 2026-10-02T02:05:20Z = KST 11:05이고, `date: 2026-10-02`와 맞는다.
  * 초안의 사용자 원문 블록(1~30행)은 pre-dafe.bak과 같다. 이번 변경은 pin 문단(49→53행)뿐이다.
  * g1_kit 양식과의 차이는 자리표시 3곳뿐이다(pin 문단은 두 파일이 같다).
* `check_apr_draft`가 리허설 pre와 appr에서 통과했다. 출력은 "양식에서 자리표시 줄만 다름, red 8 + 거부 23 = 31단계"였다.
* 리허설에서 커밋된 spec blob의 sha256 = `72d8ff60…`이고, 승인 기록에 `72d8ff60`이 2회 나온다.

## 2. noop 기준선 원인과 키트 수정

* 재현 1: 이 셸에서 `bash -c` 안의 APPDATA·USERPROFILE이 빈 값이고 HOME=/home/HSLEE가 된다.
  * 사용자 site-packages가 `~\Python\Python314\site-packages`로 풀린다.
  * 결과: `ModuleNotFoundError: No module named 'pytest'`.
  * 넷을 export하면 `import pytest`가 된다(9.0.2). APPDATA 하나만 export해도 된다.
  * 참고: `/usr/bin/bash`는 env를 유지하고 PATH로 찾은 `/c/msys64/usr/bin/bash`는 잃었다(같은 exe다). 하네스나 런타임 쪽 현상으로 보인다. 그래서 명시적으로 export하고 단정하는 방식이 맞다.
* 재현 2: `/c/g300/b`(7243f28, autocrlf=false 복제본)에서 `run_all.py --only 28-v3`를 돌렸다.
  * env를 빼면 4단계 모두 exit 2(`BaselineFailed`)다. 옛 `noop_base_{4a286f0,a17b8bd}`의 `opts-kill` exit 2와 같은 모양이다.
  * export하면 4단계 모두 PASS다.
* 기존 기준선 산출물 대조:
  * `out/noop_{base,proto}_dafe5cf`는 13케이스·264단계 모두 PASS다.
  * base와 proto가 단계마다 (exit, verdict, observed) 같다.
  * card의 exit 분포 문장(28 {0:4}, 31 {0:1,1:1,2:1}, 34 {0:1,1:5}, 35 {0:3,1:8})이 실측과 같다.
  * 옛 기준선의 FAIL 케이스는 28·31·34·35·v3_survivor이고, 모두 V3 exit 2였다.
* 결론: 원인 확인됨. 네 스크립트의 export와 `import pytest` 단정은 맞는 수정이다.
* **S1 — `setup_clones.sh`의 `git -c core.autocrlf=false clone`은 이 설정을 복제본에 남기지 않는다.**
  * 이 머신은 `C:/Program Files/Git/etc/gitconfig`에 `core.autocrlf=true`가 있다.
  * 그래서 셋째 인자 REV로 하는 `checkout --detach`는 바뀐 파일을 CRLF로 꺼낸다.
  * 실측: 7243f28 복제본에서 dafe5cf로 checkout하니 계획서가 CRLF 1,191줄이었다(blob은 0줄).
  * 지금 영향은 없다. REV(gate master)와 원본 HEAD 사이의 차이는 문서뿐이고 G1 입력은 같다.
  * 하지만 briefs §4 표가 말하는 "`-c core.autocrlf=false`, 셋째 인자 = 체크아웃 rev"가 REV 경로에서는 성립하지 않는다.
  * 수정안(한 줄): `git clone -c core.autocrlf=false …`(설정이 복제본 config에 남는다), 또는 REV checkout에도 `git -C … -c core.autocrlf=false checkout`.

## 3. 계약 12 메모

### (a) `overwrite-similar`의 `not_targeted` = 12

판단: 작성자와 같이 **승인 범위 안이 분명하다. 사용자 질문 없음.** 근거는 아래와 같다.

* design 30 §5.5.2(UD-0 승인본, 7243f28)가 이 경우를 문장으로 정한다: "나머지 def에는 범위 정책 계약 1이 그대로 적용된다: base **같은 경로**에 같은 qualname이 있고 해시가 다르면 문장 단위 대상 … 없으면 새 def 본문 전체".
  * §5.2 본문(268행)과 card 계약 4(사용자 질문 때 판 b8a47418부터 바이트로 같다)도 같은 조건을 가진다.
* 범위 정책 승인(`.ai/approvals/20260930-v3-changed-stmt-scope.md`, 7243f28)은 "해시가 바뀐 기존 def에서는 … 좁힌다"고 한다. `overwrite`의 목적 def `b.py::f`는 경로와 qualname으로 보면 기존 def다.
  * 그 승인이 받아들인 약화 ①(바뀌지 않은 문장의 test 강도)이 정확히 이 12개다.
* G1이 더하는 것은 0이다. 7243f28 `changed_defs`·`_Scope(base_defs[q], fn)`(687행)는 이동을 모르고 같은 선택을 한다.
* D-20 근거 (1)과 (3)은 "경로 밖 이동 **원본**과 맞추기"를 금지한다. 여기서는 같은 경로의 옛 def와 맞추므로 해당하지 않는다.
* UD-5 질문의 "약화는 없습니다 / 거부해야 할 단계는 전부 거부"도 그대로다.
  * `a32_proto_a17b8bd`에서 overwrite·overwrite-import·swap V3는 exit 1, `move_rejected` M-0, `not_targeted` 0이다.
  * `early_return`이 늘 대상이므로 거부도 유지된다.
* 결함은 계약 12의 근거 구절 "(같은 이유)"가 틀렸다는 것 하나뿐이다. 기대값은 맞다.

### (b) qualname 중복

* 7243f28 코드로 사실을 확인했다.
  * `changed_defs`의 bmap과 `base_defs = dict(iter_defs(...))`(671행)는 마지막 같은 qualname 기준이다.
  * `targets_by_def["%s::%s"]`(690행)는 덮어쓴다.
* 공격 32 `property-getter-changed` V3 관찰 `defs` = `["b.py::P.x","b.py::P.x"]`이다. 계약 4 "두 번 나온다"와 맞는다.
* 문구안은 정확하고, G1이 바꾸는 것이 없으므로 질문 대상이 아니다.

## 4. 리허설 (7243f28)

* G1 입력 8묶음의 `dafe5cf..7243f28` diff가 비어 있다. 그 사이 커밋 8개는 모두 docs다(D-11, B34 card 등).
* `mk-sandbox --sbx /c/g300/sbx` → rc 0. sim-pred all로 선행 7건 자리표시, 합성 gate `06be5bf`.
* `kit-cmds` → rc 0. 출력만 했다.
* `pre` → rc 0.
  * 선행 7건 OK, design 승인 OK, UD-5 바이트 대조 OK.
  * measured rev dafe5cf이고 G1 입력·reachability_roots가 같다.
  * attacks에 32가 없다.
  * 게이트 밖 호출 10줄·9스크립트로 card와 같다(docstring 2줄 제외).
  * 패치 check ok 5. plan_tables_hash `16b899d1…`.
* `local`(doc → card → appr → final) → rc 0.
  * A 22a7635, B 94a5453, C 0f05d33.
  * gate_change_ok C True / B False / A False.
  * 로컬 EL4 receive exit 0.
  * push 명령은 출력만 됐다.
* 실제 저장소: HEAD·gate master `7243f28` 그대로, reflog 변화 없음, worktree 목록 그대로.
* 실제 `pre`는 지금 멈춘다(B34 role 브랜치·worktree가 있고 선행 판정 기록이 없음). 착수 조건대로이고 결함이 아니다.

## minor

1. `run_attack32.sh`·`run_variants.sh`의 scratch 가드가 `C:/g*`다. `setup_clones.sh`·`run_noop.sh`는 `C:/g[0-9]*`로 고쳤는데 두 파일은 그대로다.
2. `setup_clones.sh`는 `$S/$n`이 이미 있으면 `continue`한다. 재사용한 복제본이 REV에 있는지 확인하지 않는다.
3. 메모 (a) 문구안의 "있으면(`overwrite`·`swap`)"는 "있으면(예: `overwrite`·`swap`)"으로 쓰는 것이 안전하다. 표의 다른 거부 단계를 모두 열거해 확인한 문장이 아니기 때문이다.
4. 메모 (a)를 적용하면 card의 계약 블록이 바뀐다. 그러면 pin 문단을 승인 초안과 **g1_kit 양식 둘 다**에서 같게 고쳐야 한다. 양식 밖 차이가 생기면 `check_apr_draft`가 멈춘다. 메모에는 초안만 적혀 있다.
5. `g1_launch.sh mk-sandbox` 복제는 autocrlf=true 그대로라 모래상자 작업 트리가 CRLF다. 리허설은 통과했고 리허설에만 영향이 있다. g1_kit 양식의 자리표시 문단이 선택지 라벨을 실제와 다르게 풀어 썼는데("전역 이동 인식 규칙", "승인 기록에 선언한 이동만 인정"), 채운 판에서 대체되는 줄이라 영향이 없다.

## 권고

* S1은 G1 card 커밋 전에 한 줄로 고친다(측정 키트일 뿐이고 판정 근거는 아니다).
* 메모 (a)와 (b)의 문구는 기본안대로 적용해도 좋다. 다만 minor 3·4를 함께 처리한다. 적용하면 sha가 바뀌므로 pin 문단에 "계약 안 차이, 기대값 무변경"이라고 적는다.
