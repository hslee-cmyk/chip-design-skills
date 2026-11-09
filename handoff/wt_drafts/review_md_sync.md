# 독립 리뷰 -- spec card 초안 `20261001-topology-md-sync`(test-only) + `b47_regen_commands.md`

리뷰어: 독립 검토 agent(작성자 아님). 기준: gate `master` = HEAD `a796468`(2026-10-01). 저장소 읽기 전용. 실행은 `git archive HEAD`를 `C:/g97`에 푼 사본에서만 했고(측정 뒤 삭제),
python `C:/Python314/python.exe -B`. 대상: `_drafts/draft_md_sync.spec.md`, `_drafts/b47_regen_commands.md`. 정정본: `_drafts/draft_md_sync.reviewed.spec.md`(머리 `parse_spec_card` 통과 -- 아래 V).

## 요약

| 등급 | 수 | 항목 |
|---|---|---|
| 막음(blocking) | 3 | B1 재생성 명령이 EL1에 통째로 거부됨 + push 형태 오류 + 지금 P10b 역할 브랜치 존재 / B2 계약 8 (b)의 (계약, 파일) 쌍을 test가 보여 줄 의무가 계약에 없음 / B3 계약 9 범위가 Change-Id로 한정되지 않음(교훈 10) |
| 고칠 것(should-fix) | 5 | S1 계약 7 거부 귀속 의미·주석 오류 / S2 표 파싱 정의 불충분 / S3 승인 줄·착수 조건 문단 / S4 test-author 입력 서술 오류 / S5 새 양식 교훈 8~13 항목 누락 |
| 사소(minor) | 4 | M1~M4 |

측정으로 확인된 것(초안 주장과 일치): D blob id 두 개, 나머지 4개 md 차이 0, numstat, base PASS·`D^` 실패 쌍, CRLF·플래그 바이트, 이름 충돌 없음, 머리 블록·interface card 0행.

## 막음(blocking)

### B1. 재생성 명령 블록은 EL1(PreToolUse)에 통째로 거부된다 -- 그리고 push 형태가 틀렸다

1. `T=$(mktemp -d)` … `rm -rf "$T"`: `T`가 명령 치환이라 hook이 값을 모른다. `rm`은 쓰기 명령이고 대상이 해석되지 않으면 거부한다(`tools/gates/role_hooks.py` 491~494 `_write_target`: "쓰기 대상을 해석하지 못함", 542~544 `rm`·`touch`·`mkdir`).
   PreToolUse는 명령 문자열 전체를 실행 전에 판정하므로 **한 번의 bash 호출로 적힌 0~5단계 전체가 하나도 실행되지 않는다**(실해는 없지만 절차가 작동하지 않는다). 이 리뷰 중 같은 규칙으로 실제 거부를 두 번 겪었다
   (`2>/c/g97/out/$n.err` 리다이렉트 -- "쓰기 대상을 해석하지 못함(리다이렉트 >)"; `cd` 뒤 상대 경로 쓰기 -- "§5.1").
2. 6단계 `git -C … push gate master`: EL1은 메인 저장소 push를 정확히 `gate master:master` 인자로만 허용한다(`role_hooks.py` 802~816 `_judge_push` -- 그 밖은 "허용된 push 형태가 아니다"). design 05 §12-0도 `git push gate master:master`.
3. 같은 함수가 `refs/heads/role/`에 브랜치가 있으면 문서 커밋 push를 거부한다. **지금** P10b `20260930-df23-registry-record`의 role/test·code·audit 브랜치 3개와 worktree가 있다(`git branch --list 'role/*'`).
   D는 P10b 정리 뒤에만 push된다. P10b가 바꾸는 경로는 레지스트리·`tests/tools/reg_check.py`·새 test 하나라(`git diff --name-only a796468 role/audit/20260930-df23-registry-record`) D의 기대 blob에는 영향이 없다.

고친 명령(`b47_regen_commands.md` 0~6단계 교체안 -- `T`를 리터럴로, 확인을 단정식으로, push 형태 정정):

```bash
set -euo pipefail
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
PY=/c/Python314/python.exe
L=skills/analog-gmid-design/assets/library
T=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b47_render      # 리터럴(EL1이 mkdir·rm 대상을 해석할 수 있어야 한다)

# 0. 시작 상태
git -C "$R" fetch gate
test -z "$(git -C "$R" for-each-ref refs/heads/role/)"           # 진행 중 변경 없음(있으면 6단계 push가 EL1 거부)
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"   # 이 값 = measured_at(= D^)
git -C "$R" diff --cached --quiet                                 # 미리 스테이징된 것 없음
test -z "$(git -C "$R" status --porcelain -- "$L")"
test -z "$(git -C "$R" diff --name-only a796468 HEAD -- "$L" skills/analog-gmid-design/assets/topology_to_markdown.py skills/analog-gmid-design/assets/stick_diagram.py)"
#   ↑ 비지 않으면 멈춘다: 기대 numstat·blob id를 다시 재고 card 계약 9 값도 고친다

# 1. 낡은 2개만 제자리 재생성(cwd = assets, 인자 = library/<n>.topology.json)
cd "$R/skills/analog-gmid-design/assets"
for n in folded_cascode current_reuse_telescopic_ota; do
  "$PY" -B topology_to_markdown.py "library/$n.topology.json" > /dev/null
done

# 2. 나머지 4개: 추적 파일을 건드리지 않고 리터럴 임시 경로로 렌더링해 차이 0
mkdir -p "$T"
for n in ngcc_3stage_ff pushpull_follower_buffer sf_pushpull_output_opamp two_stage_ota_sf; do
  "$PY" -B topology_to_markdown.py "library/$n.topology.json" "$T/$n.topology.md" > /dev/null
  diff --strip-trailing-cr "library/$n.topology.md" "$T/$n.topology.md"
done
rm -rf "$T"

# 3·4. 바뀐 경로와 blob을 단정식으로
git -C "$R" add -- "$L/folded_cascode.topology.md" "$L/current_reuse_telescopic_ota.topology.md"
test "$(git -C "$R" diff --cached --name-only | sort | tr '\n' ' ')" = "$L/current_reuse_telescopic_ota.topology.md $L/folded_cascode.topology.md "
test "$(git -C "$R" rev-parse ":$L/folded_cascode.topology.md")" = 711a59108bd53891ea410963e235617a6955b416
test "$(git -C "$R" rev-parse ":$L/current_reuse_telescopic_ota.topology.md")" = 2a3e67a5ccef1aae8829688bedaa3098b57d74e2
test -z "$(git -C "$R" status --porcelain -- "$L" | grep -v '^M  ')"      # library 아래 다른 변경·__pycache__ 0
git -C "$R" diff --cached --numstat -- "$L"                                # 눈 확인: 5 5 folded, 12 6 CRTO

# 5. 커밋(메시지는 기존 초안 그대로 -- Role: doc, Change-Id: 20261001-topology-md-sync)
git -C "$R" commit -F - <<'MSG'
(기존 5단계 메시지 그대로)
MSG
git -C "$R" log -1 --format='%H %P'
```

```bash
# 6. push -- 단독 호출, 전체 출력 확인
git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills push gate master:master
```

(hook 판정 근거: 루프 변수 `$n`이 든 **인자**는 해석 못 해도 건너뛰고(`_check_pointing`은 `None` 인자를 넘긴다), 리다이렉트는 `/dev/null`만이라 통과, `mkdir`·`rm`은 리터럴 `$T`라 해석된다.
`wt/_drafts`는 경로표 어느 행과도 겹치지 않아 즉시 통과. 이 블록 자체는 실행하지 않았다 -- 첫 실행 때 hook이 거부하면 그 메시지로 고친다.)

### B2. 계약 8 (b)의 "(계약, 파일) 쌍이 정확히 {…}"를 test가 보여 줄 의무가 계약 1~7에 없다

test-author는 계약 1~7 문장만으로 test를 쓴다. 계약 8 (b)는 `D^`에서 **실패 메시지가 가리키는 (계약, 파일) 쌍 5개**를 auditor가 읽어야 성립하는데,
(1) 메시지 형식이 정해져 있지 않고 (2) 한 test 함수가 파일·계약을 돌며 첫 assert에서 멈추면 첫 실패 하나만 보인다(5쌍을 관찰할 수 없다). 그러면 auditor는 V2 근거를 못 세우고 재시도가 된다.
정정(정정본 '관찰 가능한 계약' 머리 '판정 결과의 모양'): 파일마다 계약 1 (b)~(d)·2~5를 **모두** 판정해 실패 쌍을 모은 뒤 assert 하나, 메시지는 쌍마다 `계약 <k> <n>: <사유>` 한 줄,
계약 1 (a)는 별도 test 함수(매개변수화로 md 0개면 수집 0 = 빈 판정이 되므로). 계약 8 (b) 문장도 "assert 메시지의 `계약 <k> <n>` 줄"로 맞췄다.

### B3. 계약 9 범위가 `measured_at..new` 전체 diff다 -- 교훈 10 위반, 이 card 자신의 지시로도 깨진다

`git diff --name-only <measured_at> <new>`는 그 사이에 낀 **다른 문서 커밋**까지 잡는다. 실제 선례: P10은 card 커밋 `b8d4c4d`와 test `56b86c6` 사이에 `fe638ab`(design 20)·`2d58fd8`(`.ai/approvals` 2개 +
`.ai/context.md`)이 끼었다(`git log --oneline 766b5c2..62ae24f`). 더구나 이 초안의 '결정 필요 항목'은 "답을 받으면 원문을 `.ai/context.md`에 남긴다"고 하므로 그 기록이 D나 card 커밋에 들어가도,
따로 끼어도 계약 9는 FAIL이다(제외 목록에 `.ai/context.md`가 없다).
정정: 계약 9를 "`measured_at..new` 중 트레일러 `Change-Id: 20261001-topology-md-sync`인 커밋들의 `diff-tree` 합집합"으로 한정하고, 의도 절에 (1)·(2) 커밋 모두 이 Change-Id를 달고
사용자 답 기록·승인 기록은 Change-Id 없는 별도 커밋으로 한다고 적었다. blob 대조의 전제(D 앞뒤로 library json·렌더러 불변)는 `git diff --name-only <measured_at> <old> -- A/library A/topology_to_markdown.py A/stick_diagram.py` = D의 두 md로 따로 적었다.

## 고칠 것(should-fix)

### S1. 계약 7: 거부 귀속의 의미가 모호하고 주석 하나가 틀렸다

"각 거부 케이스는 **어느 계약이** 거부했는지까지 확인"이 '괄호 계약이 실패 집합에 들어 있다'(⊇)인지 '정확히 같다'(=)인지 정해지지 않았다. =로 읽으면 초안 주석
"json에 ideal source를 더했는데 md에 표 없음(3)"은 틀렸다 -- json에 ideal source를 더하면 N(J)(단자 추가)와 합계의 `c`도 바뀌어 정확한 실패 집합은 {3, 4, 5}다(단자가 빈 목록이어도 {3, 5}).
또 "json에만 수동 소자 C2 추가"는 C2의 단자가 없어 실패 집합이 결정되지 않고, "ideal source가 있는 짝에서 Value·Implementable만 바꾼 md"는 그 짝이 정의돼 있지 않다(기준 짝은 `ideal_sources` 빈 목록).
정정본: 의미 = 정확히 같음(과잉 실패도 잡는다), C2 = capacitor [`in`, `gnd`], 기준 짝 2(I1 current_source [`vdd`, `in`], 1e-6, false)와 그 md를 정의, ideal source 관련 거부 케이스 셋을
(3·4·5)/(3·4·5)/(3)으로 나눔, 플래그 문자 위반(4)·소자 표 머리 행 다름(2) 추가, "짝 json 없음"은 2~5를 판정하지 않는다고 명시.
(작성 전 실측 1b의 "예상과 다른 결과 0"은 사전 점검기가 ⊇로 봤기 때문으로 보인다 -- 사전 점검기는 지워져 확인 불가.)

### S2. 표 파싱 정의가 test-author가 card만으로 결정하기에 부족하다

빠진 것: (a) 절의 표 범위(머리 줄 뒤 첫 `|` 줄부터 연속 `|` 줄) (b) 셀 나누기에서 맨 앞·맨 뒤 `|` 처리(그냥 `|`로 나누면 빈 셀 2개가 생긴다) (c) 표 머리 행을 **판정하는지**(초안은 괄호 설명뿐, Net 표·수동 소자 표는 머리 미기재)
(d) T(J) 원소가 dict가 아니거나 키가 없을 때(지금은 `_TEMPLATE`뿐이라 무발동이지만 test가 예외로 끝나면 계약 8 (b)의 "assertion 실패" 조건을 깬다) (e) `terminals` 없음 = 빈 목록(렌더러와 같은 규약)
(f) 플래그 문자의 코드포인트(카드 문자는 렌더러와 같은 U+26A0 U+FE0F / U+2139 U+FE0F임을 실측 -- 문자로만 적으면 변이 선택자 유무가 갈린다) (g) 다중집합 비교 방법(교훈 12: `Counter`/정렬 튜플).
(h) 파싱 실패를 계약 실패로 바꾸는 예외 범위(교훈 13 취지: `Exception` 전체를 잡지 않는다 -- `ValueError`·`KeyError`·`IndexError`만). 정정본 '관찰 가능한 계약' 머리에 모두 넣었다.

### S3. 승인 줄·착수 조건 문단

* **게이트·규칙상 필수는 아니다** -- 확인: `merge_gate.py` 721~738행은 `gate_change: yes`일 때만 card approval을 요구, 판정 기록 스키마 `approvals`는 `minItems` 없음, 로더 규칙 6은 목록을 돌 뿐,
  경로표 조건 md `없음`(계획 N3.12.2)·test `없음`, DEC-40 무관, 새 양식 교훈 9(동작 변경·다른 Phase 일 당겨오기)에도 해당하지 않는다(B47은 N6.1 어느 Phase에도 없다).
* **그래도 기록을 권한다(정정본 채택)**: 지금까지 판정 기록 32건이 모두 `approvals[]`가 비지 않았다. `approval` 줄이 없는 card 3개(`20260922-sections-major-merge`·`ts1-extract-tool`·`ts1-legacy-move`)도
  판정 기록에는 design 10 승인(`20260922-10-test-separation-design`)을 적었다. 이 card는 덮는 design 승인이 없는 **첫 변경**이 되어 auditor가 `approvals[]`에 적을 근거가 없고,
  B47 본문의 "재생성 커밋은 사용자 확인 뒤"가 커밋 이력에서 추적되지 않는다. 사용자 답은 이미 있으므로 새 질문 없이 옮기면 된다(초안 부록 A). decision `target` 값은 V3·V4·V7·`engine_dup_scan` 면제 집합에
  들어가지만 어떤 id와도 같지 않아 판정에 영향이 없다(`reachability._approved_ids`, `engine_dup_scan._read_exemptions` 코드 확인).
* **착수 조건 문장이 낡았다**: 초안은 "답을 받으면"이라 적었지만 답은 이미 받았다 -- 원문·날짜를 card에 인용한다.
* **같은 문구 두 번**: "응, 그렇게 진행해"는 `_drafts/user_decisions.md`에 2026-10-01 card 순서 보고의 답으로도 기록돼 있다. 기록에는 질문 문안 전체를 함께 옮겨야 어느 질문의 답인지 구분된다.
* **묶음 여부**: 질문 (2)는 "지금 바로 할지, 다른 작은 card와 묶을지"를 물었고 prep §3은 "다른 작은 test-only card와 묶기"를 **기본안**으로 적었다. 사용자에게 보인 질문이 그 권고를 담았다면
  "그렇게 진행해"는 묶기 승인으로 읽힐 수 있다. 정정본은 단독 진행 근거(지금 묶을 test-only card 없음, 섞으면 계약 8·9가 흐려짐)를 적고, 권고와 다르면 보고에 한 줄 알리게 했다. **실제 보낸 질문 문안 확인 필요.**
* **자리**: 사용자 지시 순서(P10b → Phase 2 DoD → …)에 이 card가 없다. 정정본 기본안 = P10b 정리 직후·DoD 전(DoD E4 `PT2` 전체에 새 test가 PASS로 들어갈 뿐 기준 불변), `phase`는 card 커밋 시점에 재확인.

### S4. "test-author가 interface card의 계약 1~7 문장만으로 쓴다"는 사실과 다르다

`interface_card.build`(사본 실행)의 출력은 피검 심볼 표 두 개뿐이고 계약 문장을 옮기지 않는다(P10 interface card도 같다). test-author의 입력은 agent 정의(`agents/gmid-test-author.md` 21~22행)상
interface card + spec card의 '관찰 가능한 계약'·'oracle'·'거부해야 할 입력'·'재현할 수치'다. 정정본 'oracle 종류와 출처'를 그렇게 고쳤다(작성자≠검증자 분리는 그대로 성립).

### S5. 새 양식 교훈 6개(작성 전 실측 8~13)가 card에 없다

초안의 작성 전 실측 8·9는 interface card·Phase 점검이라 새 양식 번호(8 V3 규모, 9 승인 줄, 10 범위 계약, 11 test 이름·모양, 12 같음 판정, 13 red 모양)와 겹친다. 정정본은 8~13을 새로 쓰고
옛 8·9를 14·15로 옮겼다. 내용: V3 대상 def 0·변이 0(code 경로 불변), 승인 줄 근거, 계약 9의 Change-Id 한정(P10 끼임 실례), 접두·parametrize id 규칙(피검 함수 없음 -- 직접 호출 규칙 해당 없음),
`Counter`/정렬 비교, test-only의 red 필드 금지 + `D^` AssertionError만·좁은 예외.

## 사소(minor)

* **M1 `-k` 필터**: 이름만이 아니라 `parametrize` id도 `-k`에 걸린다. design 20 §10 E1은 `tests/contracts`에 `-k "dup_w_calc or dup_kcl_edges"`, E5는 `tests/unit`에 `-k new_topology`(새 파일은 contracts라 E5 무관).
  계약 7에 "함수 이름·parametrize id에 `dup_`·`new_topology` 금지"를 넣었다(초안은 '작성 전 실측'에만 있어 test-author 입력 밖이었다).
* **M2 phase**: `phase: 2`는 게이트상 `phase_order` 원소이기만 하면 되지만 V1의 `--gmid-phase` 값이 이것을 따른다 -- Phase 3 착수 뒤 커밋하면 다시 정한다(정정본 결정 문단).
* **M3 재생성 3·4단계**의 "기대: …"가 눈 확인이라 `set -e`가 막지 못한다 -- B1 교체안에서 단정식(`test … = …`, `git rev-parse :<path>`)으로 바꿨다.
* **M4 계약 1 (d)·5의 "줄이 정확히 하나"**: `_known_dangling_nets` 근거 문자열에 줄바꿈이 들어가면 `# `·`총 `으로 시작하는 줄이 생길 수 있다(현재 library 0건). 받아들일 수 있는 위험 -- 생기면 그 md가 FAIL로 드러난다.

## 확인된 것(측정)

| 점검 | 결과 |
|---|---|
| (6) D blob(LF 정규화) | 사본 `cwd = assets`, `library/<n>.topology.json`, 출력은 사본 밖 → `folded_cascode` `711a59108bd53891ea410963e235617a6955b416`, `current_reuse_telescopic_ota` `2a3e67a5ccef1aae8829688bedaa3098b57d74e2` -- 초안과 같다 |
| (6) 나머지 4개 | `ngcc_3stage_ff` `cff41e2f…`, `pushpull_follower_buffer` `3baa1a28…`, `sf_pushpull_output_opamp` `ea11f075…`, `two_stage_ota_sf` `e3093137…` = HEAD tree blob(차이 0) |
| (6) numstat | folded 5/5(`소스:` 1줄 + Net 2행 + 소자 2행), CRTO 12/6 -- 초안 기대와 같다. 렌더러 출력은 CRLF(Windows 텍스트 모드) |
| (3) base PASS / `D^` FAIL | 리뷰어가 card 문장만으로 짠 독립 판정기(렌더러 import 없음): HEAD md → 실패 쌍 **정확히** {(2,folded),(4,folded),(3,CRTO),(4,CRTO),(5,CRTO)}(folded 2: M1·M2 Gate, 4: `vin_n`·`vin_p`; CRTO 3: CL1·CL2·Cf1·Cf2·Cs1·Cs2, 4: `Vim`·`Vip`·`Vom`·`Vop`·`gnd`, 5: (51,6,1,37) vs (51,12,1,37)), 나머지 4개 OK. 재생성 md → 6개 OK |
| (2) CRLF/LF | 계약 문장대로 `\r\n` 정규화하면 두 줄 끝 모두 같은 결과. `open(..., newline="")` 읽기로 검증 |
| (2) 플래그 | 렌더러 ` ⚠️`=U+26A0 U+FE0F, ` ℹ️`=U+2139 U+FE0F, card 문자도 같은 바이트. CRTO에 ` ℹ️` 행이 실제로 있다(두 형태 모두 실제 library에서 판정됨) |
| (2) `소스:` 줄 | 계약 1~5 어디에도 들어가지 않는다(계약 1 (d)는 `# ` 줄만). folded의 `소스:` 줄 차이는 판정 밖 -- 옳다 |
| 렌더러 규약과의 일치 | P·S는 진입 json만(`render_markdown` 84~85행 `raw.get`) -- `load_topology`는 연결 파일의 ideal_sources까지 합치지만 md는 진입 파일 것만 쓰므로 card 정의가 md와 맞다. 소자는 연결 파일까지(`load_topology` 8592~8606행) |
| (5) 이름 충돌 | `mdsync` A/tests 0건. `glob`/`rglob` 스캐너 전수(사본 grep 25곳) 중 `*.topology.md`를 쓰는 곳 없음. `test_d_delete_dead` 등의 이름 스캔은 삭제 이름 6개·메서드 2개만 -- 새 test가 쓸 이유 없음 |
| (1) 쓰기 경로 | 계획 N3.12.2: `library/*.topology.md` 오케스트레이터 `없음`, `assets/tests/**`(tests/tools 제외) gmid-test-author `없음` |
| 머리 블록 | `role_paths.parse_spec_card(text, "20261001-topology-md-sync")` -- 초안·정정본 모두 통과(정정본 approval `['20261001-b47-md-sync']`), 본문 절 11개 |
| 부록 A 승인 기록 머리 | `merge_gate.parse_approval_header` 통과(decision, target_list `[B47-MD-SYNC]`) |
| interface card | `interface_card.build`(사본 루트 `C:/g97`) -- 초안·정정본 모두 피검 심볼 0행 |

## 정정본

`_drafts/draft_md_sync.reviewed.spec.md` -- 위 B2·B3·S1~S5·M1·M2 반영. 바꾼 곳: 머리(`approval` 줄), 의도(push 전제·Change-Id·기록 커밋 분리), 관찰 가능한 계약 머리(파싱·비교·플래그·판정 결과의 모양),
계약 3·4(머리 행), 계약 7·8·9, oracle 절(test-author 입력), 거부해야 할 입력(기준 짝 2, 귀속 의미, 주석 정정, 케이스 추가), 재현할 수치, 결정 필요 항목(착수 조건·묶음·자리·승인 줄),
작성 전 실측(1c 리뷰 재측정, 8~13 신설, 옛 8·9 → 14·15). B1은 `b47_regen_commands.md` 교체안(위)으로 반영한다(이 리뷰는 그 파일을 고치지 않았다).

## 부록 A. 승인 기록 초안 `.ai/approvals/20261001-b47-md-sync.md` (decision)

```
---
id: 20261001-b47-md-sync
date: 2026-10-01
target_kind: decision
target: B47-MD-SYNC
scope: 백로그 B47 -- library 추적 md 2개(folded_cascode·current_reuse_telescopic_ota) 재생성 문서 커밋 + md·json 일치 영구 test card 20261001-topology-md-sync(test-only) 진행
---

## 사용자 원문

> 응, 그렇게 진행해

(질문 -- 2026-10-01, `_drafts/prep_b47_stale_md.md` §5 문안. **실제로 보낸 문안으로 교체 확인**:
"B47 측정 결과, 추적 md 6개 중 2개가 json과 다릅니다. … (1) 두 md를 현재 json으로 다시 만드는 doc 커밋 1개를 진행해도 될까요? …
(2) 같은 일이 다시 생기지 않도록 md 표를 json과 직접 대조하는 일치 test(test-only card)를 추가할까요? 지금 바로 할지, 다른 작은 card와 묶을지도 알려 주세요."
같은 날 같은 문구가 card 순서 보고의 답으로도 쓰였다 -- 이 기록은 위 B47 질문의 답이다.)

## 범위 설명

덮는 것: (1) `skills/analog-gmid-design/assets/library/folded_cascode.topology.md`·`current_reuse_telescopic_ota.topology.md`를 HEAD json으로 다시 만드는 `Role: doc` 커밋
(`Change-Id: 20261001-topology-md-sync`, 명령 `_drafts/b47_regen_commands.md`) (2) spec card `20261001-topology-md-sync`(test-only) -- 새 test `A/tests/contracts/test_topology_md_sync.py` 하나,
단독 card로 진행(묶을 test-only card 없음).
덮지 않는 것: library `*.topology.json`·엔진·렌더러 변경, `소스:` 줄 경로 정규화와 렌더러 덮어쓰기 기본 동작(별도 백로그), md가 없는 4회로의 md 신설, 기준 약화(없음).
판정 영향: decision `target` `B47-MD-SYNC`는 V3·V4·V7·`engine_dup_scan` 면제 집합의 어떤 id와도 같지 않다.
```
