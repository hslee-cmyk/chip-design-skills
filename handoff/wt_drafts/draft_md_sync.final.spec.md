---
id: 20261001-topology-md-sync
phase: 2
evidence_type: test-only
gate_change: no
approval: 20261001-b47-md-sync
---
## 의도

백로그 B47(`_drafts/backlog_additions.md` 21행, 준비 측정 `_drafts/prep_b47_stale_md.md`): library의 추적 파일 `A/library/<n>.topology.md`(사람이 connectivity를 재확인하는 net 기준 표, 계획 WP-09·SKILL.md 435~436행·
`references/topology-extraction-checklist.md` §5)가 json connectivity 정정 커밋에서 다시 만들어지지 않아 낡았다 -- `folded_cascode`(M1/M2 게이트 넷이 맞바뀜, 원인 커밋 `7ec8eff`)와
`current_reuse_telescopic_ota`(`passive_elements` 6개 CL1/CL2·Cf1/Cf2·Cs1/Cs2 누락, 원인 커밋 `8ae82e7`). SKILL.md·checklist는 "connectivity를 고칠 때마다 다시 생성"하라고 하지만 강제 장치가 없다
(md 내용을 읽는 test·게이트 0건 -- 작성 전 실측 7). 이 card는 **재발 방지용 영구 계약 test** 하나를 더한다: 추적 md마다 표를 직접 파싱해 같은 이름의 json과 집합으로 대조한다.
A = `skills/analog-gmid-design/assets`.

* **순서(N3.12.3 순서 1, P10 `20260930-p10-df23-inventory` 선례)**: (1) 오케스트레이터 문서 커밋 D -- 낡은 md 2개 재생성(`Role: doc`, `Change-Id: 20261001-topology-md-sync`, 명령은
  `_drafts/b47_regen_commands.md`) (2) 이 spec card + interface card 커밋 (3) test 커밋(gmid-test-author) (4) audit 커밋. card base는 D를 포함하므로 새 test는 base에서 PASS하고,
  D의 부모(`measured_at`)에서는 AssertionError로 FAIL한다(계약 8 -- auditor 측정). test를 먼저 넣으면 gate `master`가 일시적으로 red가 되므로 이 순서가 기본안이다.
  D와 (2)의 push는 진행 중인 변경이 없을 때만 된다(`git for-each-ref refs/heads/role/`이 비어야 한다 -- EL1 `role_hooks._judge_push`. 2026-10-01 현재 P10b `20260930-df23-registry-record`
  역할 브랜치 3개가 있다 -- P10b 정리 뒤). (1)·(2) 커밋은 모두 `Change-Id: 20261001-topology-md-sync`를 단다(계약 9가 이 Change-Id 커밋만 본다).
  사용자 답 원문 기록(`.ai/context.md`)은 **이 Change-Id를 달지 않는 별도 문서 커밋**으로 한다(계약 9 범위 밖으로 두기 위해).
* **작성자≠검증자(oracle 독립)**: 기대값은 json 데이터에서만 만든다. md를 만든 렌더러(A의 md 생성 스크립트와 그것이 부르는 topology 로더)를 test가 import·호출·실행하지 않는다 --
  렌더러 출력과 문자열을 맞대면 렌더러 결함이 기준으로 굳는다(계약 6).
* **범위**: connectivity 표(Net 표·소자 표·수동 소자 표·ideal source 표)와 합계 줄, 파일·회로 이름 대응. 대조하지 않는 것: `소스:` 머리 줄(실행 cwd·인자 형태에 따라 달라지는 경로 문자열 --
  DF-36과 같은 유형, 별도 백로그), 자동 플래그 절·해소된 플래그 절의 문장, Net 셀 끝의 플래그 표시(⚠️/ℹ️) 종류, ideal source 표의 Value·Implementable 열, 문단 문장. (결정 필요 항목 1~3)

## 관찰 가능한 계약

새 test 파일은 `A/tests/contracts/test_topology_md_sync.py` 하나다. test 함수 이름은 모두 `test_mdsync_`로, 모듈 수준 도우미는 모두 `_mdsync_`로 시작한다. 판정 대상 = `A/library/` 바로 아래의
`*.topology.md` 전부(작업 트리 파일, `_`로 시작하는 이름 포함 -- HEAD에는 없음). 파일은 UTF-8로 읽고 줄 끝 `\r\n`·`\n`을 같게 다룬다(추적 md는 작업 트리에서 CRLF다 -- 작성 전 실측 1).
아래에서 **J** = 같은 이름의 json(`A/library/<n>.topology.json`)을 `json.load`한 dict, **T(J)** = J의 `netlist` 원소에 J의 `linked_topology_files`(없거나 빈 목록이면 없음)가 가리키는 같은 폴더
파일들의 `netlist` 원소를 이어 붙인 목록, **P(J)** = J의 `passive_elements`(없으면 빈 목록), **S(J)** = J의 `ideal_sources`(없으면 빈 목록). P·S는 진입 json 것만 쓴다(연결 파일의 것을 합치지 않는다).
T(J)의 원소가 dict가 아니거나 `name`·`kind`·`source`·`drain`·`gate` 중 하나가 없으면 그 md는 계약 2 FAIL이다(예외로 test가 끝나지 않는다). P(J)·S(J) 원소에 `terminals`가 없으면 빈 목록으로 본다.
**절과 표**: "`<접두>`로 시작하는 절" = 그 접두로 시작하는 줄(머리 줄)이 md에 정확히 하나이고(0개·2개 이상이면 그 계약 FAIL), 그 절의 **표** = 머리 줄 뒤 처음 나오는 `|`로 시작하는 줄부터
`|`로 시작하지 않는 첫 줄 전까지의 연속 줄이다(그 사이에 `## `로 시작하는 줄이 먼저 나오면 표 없음 = FAIL). 표의 첫 줄(머리 행)은 각 계약에 적은 머리와 **문자열로 같아야** 하고(다르면 FAIL),
둘째 줄(구분 행)은 데이터가 아니다. **셀** = 앞뒤 공백을 뗀 행에서 맨 앞·맨 뒤 `|`를 하나씩 떼고 나머지를 `|`로 나눈 뒤 각 조각의 앞뒤 공백을 뗀 것이다. 열 수가 머리와 다르면 FAIL.
**백틱 셀** = 정확히 `` `x` ``(x에 백틱 없음) 형태이고 값은 x다. 백틱 셀이어야 할 자리가 그 형태가 아니면 그 계약 FAIL.
**다중집합 비교**는 `collections.Counter`(원소 = 문자열·튜플)나 정렬한 튜플 목록으로 한다(정렬 기준·튜플화가 정해진 값만 `==`로 비교한다 -- `__eq__` 없는 객체·순서가 정해지지 않은 표현 비교 금지).
**플래그 문자**: ` ⚠️` = 공백 + U+26A0 + U+FE0F, ` ℹ️` = 공백 + U+2139 + U+FE0F(렌더러가 쓰는 바이트 그대로, 작성 전 실측 1).
**판정 결과의 모양(계약 8의 측정 입력)**: 실제 library 판정은 md 파일마다 계약 1 (b)~(d)·2·3·4·5를 **모두** 판정해 실패 쌍 (계약 번호, `<n>`, 사유)을 전부 모은 뒤, 마지막에 "실패 목록이 비었다"를
assert 하나로 판정한다(첫 실패에서 멈추지 않는다). assert 메시지는 실패 쌍마다 `계약 <k> <n>: <사유>` 한 줄을 담는다. 계약 1 (a)는 별도 test 함수로 판정한다(매개변수화로 md 수만큼
test를 만들 때도 0개면 test가 수집되지 않는 빈 판정이 되므로). 파싱 실패는 그 계약의 실패 쌍으로 기록하고(그 계약의 판정기 안에서 `ValueError`·`KeyError`·`IndexError`만 잡는다),
`Exception` 전체를 잡아 넘기지 않는다.

1. **짝과 이름**: (a) 판정 대상 md가 1개 이상이다(0개면 FAIL -- 빈 판정 금지). (b) md `<n>.topology.md`마다 `A/library/<n>.topology.json`이 있다. (c) J의 `topology_name` == n.
   (d) md에 `# `로 시작하는 줄이 정확히 하나이고 그 줄이 `# <n> -- topology connectivity table`이다.
2. **소자 표**: md에 `## 소자별 연결 표`로 시작하는 절이 정확히 하나 있고, 그 표(머리 `| Name | Kind | Source | Drain | Gate |`)의 데이터 행을 (Name, Kind, Source 백틱 값, Drain 백틱 값, Gate 백틱 값)
   5짝으로 읽은 **다중집합**이 T(J)의 원소마다 (`name`, `kind`, `source`, `drain`, `gate`) 5짝의 다중집합과 같다(행 중복·누락·여분·필드 차이 모두 FAIL. 행 순서는 보지 않는다).
3. **수동 소자 표·ideal source 표**: (a) P(J)가 비지 않았으면 md에 `## 수동 소자 표`로 시작하는 절이 정확히 하나 있고, 데이터 행을 (Name, Kind, Terminals)로 읽은 다중집합이 P(J) 원소마다
   (`name`, `kind`(없으면 `?`), `terminals` 순서 그대로의 튜플)의 다중집합과 같다. Terminals 셀은 `, `로 나눈 백틱 값들의 **순서 있는** 튜플이다(빈 셀 = 빈 튜플). P(J)가 비었으면 그 절이 없다.
   머리 = `| Name | Kind | Terminals |`.
   (b) S(J)에 대해 `## ⚡ Ideal source 표`(`⚡` = U+26A1)로 시작하는 절(머리 `| Name | Kind | Terminals | Value | Implementable |`)이 같은 규칙을 따른다(앞 세 열만 대조, Value·Implementable 열은 대조하지 않는다).
   S(J)가 비었으면 그 절이 없다.
4. **Net 표**: md에 `## Net별 연결 표`로 시작하는 절이 정확히 하나 있고(머리 `| Net | 연결된 단자 (device.terminal) | 단자 수 |`), 데이터 행의 첫 셀은 `` `<net>` `` 뒤에 아무것도 없거나 ` ⚠️` 또는 ` ℹ️` 하나가 붙은 형태다(net 값만 쓴다).
   json 쪽 기대값 N(J): T(J)의 원소 d마다 (d.`name`, `source`)를 d.`source` 넷에, (d.`name`, `drain`)을 d.`drain` 넷에, (d.`name`, `gate`)를 d.`gate` 넷에 넣고, P(J)와 S(J)의 원소 e마다
   e.`terminals`의 i번째 넷에 (e.`name`, `t<i>`)를 넣는다(i는 0부터). 판정: (a) md net 값의 집합 == N(J)의 키 집합이고 net 행이 중복되지 않는다 (b) net마다 둘째 셀을 `, `로 나누고 각 조각을
   **마지막** `.`에서 (소자, 단자)로 나눈 다중집합 == N(J)[net] (c) 셋째 셀(단자 수)의 정수 == 그 행 둘째 셀의 조각 수.
5. **합계 줄**: md에 `총 `으로 시작하는 줄이 정확히 하나이고 형식이 `총 <a>개 소자 + <b>개 수동소자 + <c>개 ideal source, <k>개 net.`이며
   (a, b, c, k) == (len(T(J)), len(P(J)), len(S(J)), len(N(J))).
6. **oracle 독립(auditor 측정 -- 영구 test가 아니다)**: 새 test 파일의 AST에 A 바로 아래 모듈(`A/*.py`)이나 `workspaces/run_harness.py`의 import가 없고(`import`·`from … import`·`importlib`·
   `__import__`·`runpy`·`subprocess`로 A의 스크립트 실행 모두), json 기대값은 `json` 표준 모듈로 읽은 데이터에서만 만든다. md 파일을 쓰지 않는다(읽기만).
7. **판정기 자기 점검(합성 입력 -- 영구 test)**: 계약 1~5 판정기를 실제 library와 별개로, test 안에 문자열로 적은 합성 md·json 짝(아래 '거부해야 할 입력')에 돌려 거부해야 할 짝은 실제로
   거부하고 통과해야 할 짝은 통과함을 assert한다. 각 거부 케이스는 판정기가 낸 **실패 계약 번호 집합이 괄호에 적은 집합과 정확히 같음**을 assert한다(다른 계약의 우연한 실패로 통과하지 않게,
   그리고 판정기가 실패를 과하게 퍼뜨리지 않게). 통과 케이스는 실패 집합이 비었음을 assert한다. 파싱 실패(필수 절·합계 줄 없음, 셀 형식 위반)는 예외로 test를 끝내지 않고 해당 계약의 실패로
   이어진다(위 '판정 결과의 모양'). 판정은 assert로 하고(print·logging 판정 금지 -- `test_ts3_no_print_verdicts`), 각 test 함수에 if·try 밖의 assert가 하나 이상 있다(V4 (3)(4)).
   test 함수 이름과 `pytest.mark.parametrize` id(케이스 이름 포함)에 `dup_`·`new_topology`를 넣지 않는다(design 20 §10 E1 `-k "dup_w_calc or dup_kcl_edges"`, E5 `-k new_topology`와
   계획 문장의 옛 필터 `-k "dup_"` -- 중복 행 케이스 이름은 `repeated_row`처럼).
8. **base PASS와 거부 확인(auditor 측정)**: (a) card base(문서 커밋 D 포함)에서 새 test 전부 PASS -- 판정 대상 md 6개 전부 계약 1~5 통과. (b) 격리 복제본을 `measured_at` = `D^`로 체크아웃하고
   T의 새 test 파일만 그 위에 복사해 실행하면 실패한다 -- 실패는 assertion 실패이고(수집 오류·ImportError가 아니다. 합성 자기 점검 test는 `D^`에서도 PASS), 실패 assert 메시지의
   `계약 <k> <n>` 줄이 가리키는 (계약, 파일) 쌍이 정확히
   {(2, `folded_cascode`), (4, `folded_cascode`), (3, `current_reuse_telescopic_ota`), (4, `current_reuse_telescopic_ota`), (5, `current_reuse_telescopic_ota`)}이다(나머지 4개 md는 `D^`에서도 통과 --
   무동작 증거). test-only 판정 기록은 `red` 필드가 금지이므로(00-common §8.1 표) 결과는 `checks.V2.basis`와 `reproduced_numbers`에 적는다. `git rev-parse D^`가 `measured_at`과 같다는 것도 적는다.
9. **범위(이 card `Change-Id` 커밋으로 한정)**: `git log --format=%H <measured_at>..<new>` 중 트레일러 `Change-Id: 20261001-topology-md-sync`인 커밋(D, spec·interface card 커밋, test 커밋,
   audit 커밋 -- 사이에 끼는 다른 문서 커밋은 세지 않는다)마다 `git diff-tree --no-commit-id --name-only -r <커밋>`의 합집합에서 `.ai/verification/20261001-topology-md-sync*`·이 spec card·interface card를
   빼면 `A/library/folded_cascode.topology.md`, `A/library/current_reuse_telescopic_ota.topology.md`, `A/tests/contracts/test_topology_md_sync.py` 셋뿐이다. 그 커밋들은 `A/*.py`·`workspaces/run_harness.py`·
   `A/library/*.topology.json`·`*.structure.json`·다른 md 4개·기존 test·레지스트리를 바꾸지 않는다. 더해 `git diff --name-only <measured_at> <old> -- A/library A/topology_to_markdown.py A/stick_diagram.py`가
   D의 두 md뿐이다(D 앞뒤로 다른 card가 library json·렌더러를 바꾸지 않았다 -- 아래 blob 대조의 전제). test 커밋(`old..new^`)만 보면 새 test 파일 하나뿐이다. 문서 커밋 D가 바꾼 두 md의 내용(LF 정규화 blob)은 D에서 실행한 렌더러 출력과 같다 --
   D의 blob id `folded_cascode` = `711a59108bd53891ea410963e235617a6955b416`, `current_reuse_telescopic_ota` = `2a3e67a5ccef1aae8829688bedaa3098b57d74e2`(HEAD `a796468` 기준 사본 실측 -- D 전에
   gate `master`에 library json·렌더러 변경이 들어오면 다시 잰다).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only: code 커밋이 없다(엔진·도구·레지스트리·library json 불변). 이 card가 더하는 것은 test 파일 하나이고, 데이터 쪽 변경(md 2개 재생성)은 오케스트레이터 경로(N3.12.2 636행, 조건 `없음`)의
문서 커밋으로 card base에 먼저 들어간다.
* 모양: design 05 §9.2-4 표 test-only = "`old..new^`는 첫 부모 사슬이고 전부 `Role: test`(1개 이상), `new`는 `Role: audit` 1개, 병합 없음, T = `new^`, K 없음". code 커밋이 없는 변경은 이 모양만 EL4를 통과한다.
* 선례: P10 `20260930-p10-df23-inventory`(문서 커밋 `0fa6ca2` → spec card `b8d4c4d` → test `56b86c6` → audit `62ae24f`, 계약 8 `measured_at 766b5c2 = 0fa6ca2^`)와 같은 형태.
* V2: "변경 전 test 집합이 base에서 통과시킨 것을 변경 후에도 모두 PASS + 새 test가 base에서 PASS"에 계약 8 (b) 거부 확인을 더한다. 기준을 약하게 하는 변경이 아니라 검사를 더하는 것이라 DEC-40 승인 대상이 아니다.

## oracle 종류와 출처

(d) 실측 원자료: 기대값은 판정 시점의 `A/library/<n>.topology.json`(사용자 승인을 거친 connectivity 원본 -- `7ec8eff` "사용자 승인 후 M1/M2 게이트 넷 맞바꿈", `8ae82e7` "사용자 확정")을 test가
`json`으로 읽어 계약 2~5의 정의대로 만든다. md 생성 스크립트·topology 로더를 쓰지 않는다(계약 6). 계약 2~5의 정의(표 머리·셀 형식·Net 표의 단자 이름 `t<i>`·합계 줄 문형)는 이 card 문장이고,
현재 추적 md 6개의 형식을 사본에서 잰 것이다(작성 전 실측 1).
(a) 구성 입력: 계약 7의 합성 md·json 짝 -- 무엇을 바꿨는지가 곧 거부 여부다.
**누가 무엇을 쓰는가**: md 재생성 = 오케스트레이터(문서 커밋 D, 판정 대상 데이터), 영구 계약 test = gmid-test-author가 interface card(피검 심볼 0행)와 이 spec card의 '관찰 가능한 계약' 계약 1~7·'거부해야 할 입력' 문장만으로 쓴다
(agent 정의 `agents/gmid-test-author.md` 입력 2 -- interface card 생성기는 계약 문장을 옮기지 않는다. 렌더러 소스·`_drafts` 사전 점검기를 보지 않는다), 계약 6·8·9 = auditor 자신의 스크립트. 준비 단계의 `C:/g95/precheck_mdsync.py`는 오케스트레이터 쪽 사전 점검 전용이다 -- 커밋하지 않고, test-author·auditor에게 건네지 않고,
그 출력을 판정 기록·보고 수치의 증거로 쓰지 않는다(이 초안 작성 후 `C:/g95`와 함께 지웠다).

## 거부해야 할 입력

합성 기준 짝(통과): json `topology_name` `syn`, `netlist` M1(nmos, `gnd`/`out`/`in`)·M2(pmos, `vdd`/`out`/`in`), `passive_elements` C1(capacitor, [`out`, `gnd`]), `ideal_sources` 빈 목록 +
그 json을 계약 2~5 정의대로 손으로 적은 md(H1 `# syn -- topology connectivity table`, Net 표 4행 `gnd`/`in`/`out`/`vdd`, 소자 표 2행, 수동 소자 표 1행, 합계 `총 2개 소자 + 1개 수동소자 + 0개 ideal source, 4개 net.`).
합성 기준 짝 2(ideal source 있음, 통과): 기준 짝 json에 `ideal_sources` I1(current_source, [`vdd`, `in`], `value_amp` 1e-6, `implementable` false)을 더한 json + 그에 맞춘 md
(Net 표 `in`·`vdd` 행에 `I1.t1`·`I1.t0` 추가, ideal source 표 1행 `| I1 | current_source | `vdd`, `in` | 1e-06 | ⚠️ False |`, 합계 `총 2개 소자 + 1개 수동소자 + 1개 ideal source, 4개 net.`).
**통과해야 할 변형**: 줄 끝을 CRLF로 바꾼 md, `소스:` 줄의 경로를 바꾼 md, Net 셀의 ` ⚠️`를 지우거나 ` ℹ️`로 바꾼 md, 자동 플래그 절 문장을 바꾼 md, 표 행 순서를 섞은 md, 기준 짝 2에서
Value·Implementable 열 값만 바꾼 md.
**거부해야 할 변형(괄호 = 판정기가 내야 하는 실패 계약 집합, 정확히 같아야 한다 -- 계약 7)**: 소자 행의 Gate 값 바꿈(2), 소자 행 하나 중복(2), 소자 행 하나 삭제(2), `## 소자별 연결 표` 절 없음(2),
json에만 수동 소자 C2(capacitor, [`in`, `gnd`]) 추가(3·4·5), md 수동 소자 표 절 삭제(3), 수동 소자 Terminals 순서 뒤집기(3),
json에만 ideal source I1(기준 짝 2와 같은 값) 추가 -- md는 기준 짝 그대로(3·4·5: 표 없음·`in`/`vdd` 단자 누락·합계 ideal source 수),
기준 짝 2의 md를 기준 짝 json(`ideal_sources` 빈 목록)과 대조(3·4·5: 표 있음·여분 단자·합계 수),
기준 짝 md에 ideal source 표 절만 더함(Net 표·합계는 그대로)(3),
Net 행에서 단자 하나 삭제(4), Net 행 단자 수 열만 틀림(4), json에 없는 net 행 추가(4), net 행 중복(4), Net 셀에 백틱 없음(4), Net 셀 플래그가 ` ⚠️`·` ℹ️` 밖의 문자(4),
합계 줄 수동소자 수 틀림(5), 합계 줄 없음(5), 합계 줄 문형이 다름(5), 소자 표 머리 행 문자열이 다름(2),
H1의 회로 이름이 json `topology_name`과 다름(1), 파일 이름 `<n>`과 json `topology_name`이 다름(1), 짝 json 없음(1 -- 짝이 없으면 2~5는 판정하지 않는다), 판정 대상 md 0개(1).
(사전 점검기로 위 케이스 대부분을 실측했다 -- 작성 전 실측 1b. 리뷰 정정: 옛 초안의 "json에 ideal source를 더했는데 md에 표 없음(3)"은 N(J)·합계도 바뀌므로 정확한 집합이 3·4·5다.)

## library 회로 적용 여부

적용: 추적 md가 있는 6회로(`current_reuse_telescopic_ota`, `folded_cascode`, `ngcc_3stage_ff`, `pushpull_follower_buffer`, `sf_pushpull_output_opamp`, `two_stage_ota_sf`)가 판정 대상이다.
md가 없는 json 4개(`_TEMPLATE`, `common_gate_amplifier`, `nmcnr_amplifier`, `two_stage_ota`)는 판정 대상이 아니다(계약 1은 md→json 방향만 -- 결정 필요 항목 4). 일반성 측정: 재생성 전에도
나머지 4개 md는 통과한다(계약 8 (b) -- 낡지 않은 md에서 무동작). library json은 바뀌지 않으므로 E-LIB·E-INST는 base와 같다.

## 무동작 판정 입력(무발동 값)

엔진·library json·기존 test 전부 -- 판정이 base와 같다. 새 산출물 필드 없음. md 2개는 렌더러가 만드는 사람용 표이고 엔진·test·게이트·기준선이 읽지 않는다(작성 전 실측 7).

## 재현할 수치

auditor가 독립으로 센다: 판정 대상 md 수(base 6), md마다 (소자 행 수, 수동 소자 행 수, ideal source 행 수, net 행 수) -- base 기대 사실은 json에서 auditor가 다시 센다(이 card의 수를 옮겨 적지 않는다),
계약 8 (b) `D^`에서 실패한 (계약, 파일) 쌍과 실패한 새 test id 수·`D^`에서 통과한 합성 자기 점검 test 수, 계약 9 Change-Id 커밋 수와 변경 경로 수(3)와 D blob id 일치 여부, 계약 6 금지 import 0.
참고(사본 실측, `a796468`): `D^`에서 `folded_cascode`는 소자 표 2행(M1 Gate `vin_p`↔json `vin_n`, M2 반대)·net 2개(`vin_n`, `vin_p`) 불일치, `current_reuse_telescopic_ota`는 수동 소자 6개 누락,
net 5개(`Vim`, `Vip`, `Vom`, `Vop`, `gnd`) 단자 누락, 합계 (51, 6, 1, 37) vs json (51, 12, 1, 37).

## 결정 필요 항목

착수 조건(충족, 2026-10-01): 오케스트레이터 B47 점검 보고(15:30 KST)의 "처리 방침 (원칙상 기본안이라 따로 여쭙지 않고 진행합니다)" 1(md 2개 재생성)·2(일치 test card 추가)에 대한 사용자 답
"응, 그렇게 진행해"(15:32), md 일치 card 검토 요약(16:34) 뒤 같은 답(16:40) -- 두 메시지 원문과 답은 승인 기록 `20261001-b47-md-sync` '사용자 원문'. 같은 날 같은 문구가 card 순서 보고의 답으로도 쓰였으므로(`_drafts/user_decisions.md` 2026-10-01 card 순서) `.ai/context.md` 기록에는 **질문 문안 전체와 답을 함께** 옮긴다
(Change-Id 없는 별도 문서 커밋 -- 의도 절). **묶음 여부**: prep §3은 "다른 작은 test-only card와 묶기"를 기본안으로 적었으나 지금 묶을 test-only card가 없고(P10b 진행 중, 다음 순서 card는
모두 red-green·게이트 변경), 묶으면 판정 유형·Change-Id가 섞여 계약 8·9가 흐려지므로 단독 card로 한다 -- 실제 보낸 방침 2번에는 묶기 언급이 없다(승인 기록 원문).
**순서**: 사용자 지시 순서(P10b → Phase 2 DoD → …, `_drafts/user_decisions.md`)에 이 card의 자리는 없다. 기본안 = P10b 정리 직후·Phase 2 DoD 전(DoD E4 `PT2` 전체 실행에 새 test가 들어가
PASS로 셈된다 -- 판정 기준을 바꾸지 않는다). 처음(16:40 직후) 사용자에게는 이 card를 DoD 뒤로 알렸다가 runbook 준비에서 DoD 전으로 바꿨고,
그 변경과 'DoD 전에 이 card 한 주기(test → audit → push)가 끝나야 한다'는 점을 2026-10-01 진행 보고에서 사용자에게 알렸다(이의 없음 -- 승인 아님, 알림). `phase`는 card 커밋 시점의 진행 Phase로 다시 확인한다(V1 `--gmid-phase` 값이 이것을 따른다).
**승인 줄**: `approval: 20261001-b47-md-sync`(`target_kind: decision`, 위 사용자 답 원문 -- 새 질문 없이 받은 답을 옮긴다. 초안 `_drafts/approval_20261001-b47-md-sync.md`). 게이트가 요구하지는 않는다
(`merge_gate.py` 721~738행은 `gate_change: yes`일 때만 card approval을 요구, 경로표 조건 md `없음`·test `없음`, DEC-40 무관, 양식 교훈 9 비해당 -- 동작 변경 없음, N6.1 어느 Phase에도 배정되지 않은
백로그라 당겨오는 일도 아님). 그래도 두는 이유: 지금까지 판정 기록 32건 전부 `approvals[]`가 비지 않았다 -- `approval` 줄이 없던 card 3개(`20260922-sections-major-merge`·`20260922-ts1-extract-tool`·
`20260922-ts1-legacy-move`)도 판정 기록은 design 10 승인을 적었다. 이 card는 덮는 design 승인이 없어, 기록이 없으면 auditor가 `approvals[]`에 적을 근거가 없고 '사용자 확인 뒤'(B47 본문)라는
착수 조건이 커밋 이력에서 추적되지 않는다. 기록은 card 커밋 전에 Change-Id 없는 문서 커밋(`.ai/context.md` 기록과 같은 커밋)으로 넣는다. decision `target` 값 `B47-MD-SYNC`는 V3·V4·V7·
`engine_dup_scan` 면제 집합에 들어가지만 어떤 변이 id·test id·`<path>::<rule>`과도 같지 않아 판정에 영향이 없다. 아래는 원칙으로 정한 기본안이다(사용자 몫 아님):
1. **`소스:` 머리 줄은 대조하지 않는다.** 이 줄은 렌더러가 받은 경로 인자를 그대로 적어 실행 위치에 따라 달라진다(사실 문장이 아니라 생성 환경 기록). 정규화해 대조하면 test가 실행 방식을
   규정하게 된다 -- 경로 정규화는 렌더러 쪽 수정이고 엔진 card 몫(별도 백로그, DF-36과 같은 유형). 이번 재생성은 6개 md 형식을 `library/<n>.topology.json`으로 맞춘다(재생성 명령).
2. **플래그 절과 Net 셀 플래그 종류는 대조하지 않는다.** 플래그(고아 net·gate-only net·`_known_dangling_nets`)는 connectivity에서 렌더러가 **추론**한 진단이라, 같은 추론을 test에 다시 쓰면
   렌더러 규칙을 기준으로 굳히게 된다. connectivity 사실(계약 2~5)이 맞으면 같은 렌더러가 만든 플래그도 따라 맞다. 셀 형식(백틱 + 선택 플래그 하나)만 본다.
3. **ideal source 표의 Value·Implementable 열은 대조하지 않는다.** B47의 결함은 connectivity이고, 두 열은 소자 값·구현 가능성 표기(렌더러의 float 문자열 형식·기본값 규칙)라 같은 이유(2)로 뺀다.
4. **md가 없는 json은 요구하지 않는다.** md 생성은 "connectivity를 고칠 때마다"의 운영 규칙이고 md가 없는 4회로는 낡은 표가 없다(prep §1). 4회로 md를 새로 만들지는 별도 문서 결정(백로그).
5. **`linked_topology_files`**: HEAD library에 비지 않은 값이 없다(작성 전 실측 1). 계약은 로더 docstring이 아니라 json 데이터 규약으로 정한다 -- 소자는 연결 파일까지 합치고(회로 전체를 표로
   보이려는 md 용도), 수동 소자·ideal source는 진입 파일만 본다(현재 md 형식). 연결 파일 회로가 생기면 그때 이 정의를 재검토한다(지금 무발동).

### 분리한 것(이 card 밖)

| 항목 | 처리 |
|---|---|
| md 재생성(낡은 2개) | 오케스트레이터 문서 커밋 D(이 card 순서 1). 명령 `_drafts/b47_regen_commands.md` |
| `소스:` 줄 경로 정규화 | 렌더러 수정 -- 엔진 code card(백로그) |
| 렌더러가 출력 경로 없이 추적 md를 덮어쓰는 기본 동작 | 운영 규칙(표만 볼 때는 둘째 인자로 사본 경로) + 백로그. B47 본문 2026-10-01 실사례 |
| connectivity 정정 커밋에서 md 재생성 강제 | 이 test가 대신한다(json만 바꾸고 md를 안 바꾸면 V1·V2에서 이 test가 FAIL) |

## 작성 전 실측

(측정 HEAD = gate `master` `a796468`, 2026-10-01. 저장소 읽기 전용 -- `git archive HEAD skills/analog-gmid-design`과 `git show HEAD:workspaces/run_harness.py`를 `C:/g95`에 풀어 사본에서만
실행했다. python `C:/Python314/python.exe -B`. 결과는 scratch 파일에 쓰고 수치를 여기 옮긴 뒤 `C:/g95`는 지웠다.)
1. 사실 문장 재측정: 사본 `library/`에 md 6개(`current_reuse_telescopic_ota` 130줄, `folded_cascode` 55, `ngcc_3stage_ff` 57, `pushpull_follower_buffer` 43, `sf_pushpull_output_opamp` 83,
   `two_stage_ota_sf` 46), 모두 UTF-8·CRLF(`file`). md 형식(H1·`소스:` 줄·절 제목 `## Net별 연결 표`·`## 소자별 연결 표`·`## 수동 소자 표`·`## ⚡ Ideal source 표`·표 머리·백틱 셀·`t<i>` 단자·
   합계 줄 문형)은 사본 md와 렌더러 출력에서 읽었다. json 10개 조사(`survey.py`): 소자 `kind` ∈ {nmos, pmos}, 소자 키 ⊆ {name, kind, source, drain, gate, `_comment`}(body·bulk 없음),
   `linked_topology_files`는 전부 없음·빈 목록, `passive_elements` 수 CRTO 12·ngcc 3·sf_pushpull 5·two_stage_ota_sf 2·pushpull 1, `ideal_sources` CRTO·folded·sf_pushpull 각 1, `_TEMPLATE`의
   `netlist`는 dict 아닌 원소 1개(md 없음 -- 판정 대상 밖). 6개 md의 json `topology_name` = 파일 이름.
1b. 사전 점검(오케스트레이터 전용 `precheck_mdsync.py`, 계약 1~5 문장의 구현, 렌더러 import 없음): HEAD md → FAIL 2파일 -- `folded_cascode` 계약 2(M1·M2 행)·4(`vin_n`·`vin_p`),
   `current_reuse_telescopic_ota` 계약 3(CL1·CL2·Cf1·Cf2·Cs1·Cs2)·4(`Vim`·`Vip`·`Vom`·`Vop`·`gnd`)·5((51,6,1,37) vs (51,12,1,37)), 나머지 4개 OK. 사본에서 재생성(재생성 명령과 같은 형태) 뒤 → 6개 전부 OK.
   합성 자기 점검 17케이스(통과 4: 기준·CRLF·`소스:` 변경·플래그 제거, 거부 13: Gate 바꿈·행 중복·수동 표 삭제·Terminals 순서·Net 단자 삭제·단자 수 열·여분 net·합계 수·합계 줄 없음·이름·
   json 수동 소자 추가·json ideal source 추가·소자 표 절 없음) → 예상과 다른 결과 0. prep §1의 diff 분류(folded 내용 4줄 + `소스:` 1줄, CRTO 18줄)와 일치.
1c. 독립 리뷰 재측정(`_drafts/review_md_sync.md`, 사본 `C:/g97`, HEAD `a796468`): 사본에서 6개 모두 `cwd = assets`, 인자 `library/<n>.topology.json`, 둘째 인자 = 사본 밖 출력으로 렌더링 →
   LF 정규화 blob `folded_cascode` `711a5910…`, `current_reuse_telescopic_ota` `2a3e67a5…`(계약 9 값과 같음), 나머지 4개는 HEAD blob과 같음(차이 0). numstat folded 5/5, CRTO 12/6.
   리뷰어 독립 판정기(card 문장만으로 구현, 렌더러 import 없음): HEAD md → 실패 쌍 정확히 {(2,folded),(4,folded),(3,CRTO),(4,CRTO),(5,CRTO)}, 재생성 md → 6개 전부 OK.
   렌더러의 플래그 바이트 = U+26A0 U+FE0F / U+2139 U+FE0F(이 card 문자와 같음), CRTO에 ` ℹ️` 행이 실제로 있다(두 플래그 모두 실제 library에서 쓰인다).
2. 이름 충돌: `ls A/tests/contracts/` 27개에 `test_topology_md_sync.py` 없음. `grep -rn "glob(" A/tests/` → 패턴은 `*.py`·`probe_*.py`·`*.topology.json`(`test_df23_inventory.py:109`, `test_df36_instance_relpath.py:58`,
   `test_ic3.py:49`, `unit/test_selftest_sizing_recipe.py:3056`)·references `*.md`(`test_phase2_stale_refs.py:85`)·`.ai/approvals/*.md`(`tests/tools/engine_dup_scan.py:107`) -- 새 test의
   `library/*.topology.md`와 겹치지 않고, 새 파일은 `*.topology.json`을 추가·변경하지 않는다. `mdsync`는 `A/tests/` 전체에 0건. 계획·design의 `-k` 필터는 `"dup_"`·`"dup_w_calc or dup_kcl_edges"`·
   `new_topology`뿐 -- test·도우미 이름에 `dup_`·`new_topology`를 넣지 않는다(예: 중복 행 케이스는 `duplicate_row`가 아니라 `repeated_row`처럼). `*.py` 전수 스캐너(`test_ts3_no_print_verdicts`,
   `test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests` 이름 스캔, `test_ic_markers_match_plan` IC 표식)에 대해: 새 test는 print·logging 판정 없음, 엔진 이름 import·호출 없음, `gmid_ic` 표식 없음.
3. 원칙의 계약화: 작성자≠검증자 → 계약 6(렌더러 import 금지, json 데이터만)·계약 7(판정기 자기 점검)·계약 8(red는 auditor가 `D^`에서). 일반화 → 계약은 회로 이름 없이 `library/*.topology.md` 전수,
   회로 이름은 계약 8·9의 측정 기대값에만. 빈 판정 금지 → 계약 1 (a).
4. 쓰기 경로(계획 N3.12.2 표, HEAD 행 번호): `A/library/*.topology.md` = 오케스트레이터 조건 `없음`(636행), `A/library/*.topology.json` = 오케스트레이터 조건 `승인 기록`(634행 -- 이 card는 json을 바꾸지 않는다),
   test = gmid-test-author `A/tests/**`(제외 `tests/tools/**`, 618행), spec·interface card = 오케스트레이터 `docs/02-design/**`. 게이트 함수로 확인(`role_paths.read_write_paths` + `allowed`, 변경 id
   `20261001-topology-md-sync`): 오케스트레이터 + 두 md → 허용(행 636, 분류 `data`), gmid-test-author + 새 test → 허용(행 618), 오케스트레이터 + 새 test → 거부(`판정 트리` 기본 거부),
   auditor + `.ai/verification/20261001-topology-md-sync.json` → 허용. 트레일러 `Role: doc` → 주체 오케스트레이터(`ACTOR_OF_TRAILER`). card `approval`: `merge_gate.py` 721~738행은 `gate_change: yes`일 때만
   approval 기록을 요구한다(test-only 선례 P10은 design 승인을 적었지만 이 card는 design 문서가 없다).
5. 계획서 소비자: 지우거나 옮기는 이름 없음. `topology.md`를 언급하는 계획·design 문장(U-34 `ngcc_3stage_ff.topology.md` 산출물 -- 이미 일치)은 바뀌지 않는다.
6. 미배선: 새 def는 test 파일 안 도우미뿐(운영 코드 없음). 사전 점검기는 커밋하지 않는다.
7. 기존 계약 test·md 소비자: `git grep -l "topology\.md" -- tools skills/analog-gmid-design/assets` (md·jsonl 제외) → 렌더러 `topology_to_markdown.py` 하나(파일 이름 리터럴, DF-23 항목).
   A/tests에서 md 파일을 읽는 test 0건 -- 조정 불필요, V5 없음. `tests/contracts/test_df23_inventory.py` 57행은 모듈 이름을 scope에 적을 뿐 md를 읽지 않는다(prep §2).
8. V3 규모: 이 card의 Change-Id 커밋은 `A/*.py`·`workspaces/run_harness.py`·`tests/tools/**`를 바꾸지 않는다(계약 9) -- `mutate_changed.py` 대상 def 0, 변이 0(P10 판정 기록 V3 `targets [], mutants 0`과
   같은 모양). 새 test 파일 안의 도우미 def는 test 분류라 V3 대상이 아니다.
9. 승인 줄: `20261001-b47-md-sync`(decision, 사용자 답 원문) -- 근거는 '결정 필요 항목' 승인 줄 문단. 게이트 요구는 없고(gate_change no) 판정 기록 `approvals[]`의 근거·착수 조건 추적용.
   `.ai/approvals/`에 기록이 있어야 하는 시점: audit 커밋 전(로더 규칙 6이 `new` 트리에서 읽는다) -- 기본안은 card 커밋 전.
10. 범위 계약: 계약 9를 이 card `Change-Id` 커밋의 diff 합집합으로 한정했다(P10은 card 커밋과 test 사이에 다른 문서 커밋 `fe638ab`·`2d58fd8`이 끼었다 -- `git log --oneline 766b5c2..62ae24f`).
    사용자 답 기록(`.ai/context.md`)은 Change-Id 없는 별도 커밋.
11. test 이름·모양: 접두 `test_mdsync_`·`_mdsync_`(A/tests 전체 0건), parametrize id에도 `dup_`·`new_topology` 금지(계약 7). 피검 함수가 없는 test-only라 '직접 호출' 규칙은 해당 없음.
12. 같음 판정: 비교는 문자열·튜플의 `Counter`/정렬 목록만(관찰 가능한 계약 머리 '다중집합 비교'). dict 원소 비교·`set` 출력 순서 비교 없음.
13. red 모양: test-only라 `red` 필드 금지(00-common §8.1). 계약 8 (b)는 `D^`에서 AssertionError만 허용, 파싱 실패는 계약 실패 쌍으로 모은 뒤 assert(좁은 예외 3종만 잡음, `Exception` 전체 금지).
14. interface card 생성 점검: 이 초안의 '관찰 가능한 계약' 절을 `tools/gates/interface_card.py` `build`(사본 루트 `C:/g95`)에 넣어 피검 심볼 행 수를 쟀다(아래 실측값 -- 0이 기대값. 계약 절의
   백틱 토큰이 엔진 def 이름과 우연히 같으면 피검 심볼로 잡히므로). 결과: 피검 심볼 행 0. 머리 블록 `role_paths.parse_spec_card(text, "20261001-topology-md-sync")` → 통과
   (id·phase `2`·`test-only`·`no`·approval 없음, 본문 절 11개). phase `2` ∈ `merge_gate.read_plan_tables(<계획서>).phase_order`(아래 15).
15. Phase: `read_plan_tables` HEAD `phase_order` = (0.5, 1, 2, 3, 4, 5, 6a, 6b, 6c, 7a, 7b, 7c). 진행 중인 Phase가 2이고(직전 card P10·DF-36·B34·B26-1 초안 모두 `phase: 2`), 이 card는
   N6.1 Phase 2 범위 항목이 아니라 백로그 test-only라 V8·V9(도입 Phase가 뒤)는 N/A 형식(`도입 <Phase>: <사유>`)으로 적힌다(P10 판정 기록과 같은 처리).
