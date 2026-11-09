# B47 준비 -- library `*.topology.md` 낡음 전수 측정

측정 시점: HEAD = gate master `a796468` (2026-10-01). 저장소에는 쓰지 않았다. `git archive HEAD skills/analog-gmid-design`을 `C:/g94`에 풀고, 그 사본에서 `topology_to_markdown.py`(HEAD 판)를 돌렸다. 측정이 끝난 뒤 `C:/g94`는 지웠다.
스크립트: `C:/g94/regen.py`(CLI 실행 + diff), `regen2.py`(cwd=assets, 경로 인자 `library/<n>.topology.json`으로 `render_markdown` 실행), `bisect.py`(md 마지막 커밋 이후 json 커밋마다 HEAD 렌더러로 렌더링해 추적 md 본문과 대조, `소스:` 머리 줄은 빼고 비교). 출력은 사본과 함께 지웠다. 수치는 모두 아래 표에 옮겨 두었다.

## 1. 회로별 결과 (추적 md가 있는 6회로 전부)

| 회로 | 낡음? | 차이 종류 | json 마지막 커밋 | md 마지막 커밋 | 어긋남을 만든 커밋 |
|---|---|---|---|---|---|
| `folded_cascode` | **낡음** | **connectivity**: 소자 표 M1.gate `vin_p`→`vin_n`, M2.gate `vin_n`→`vin_p`, Net 표 `vin_n`/`vin_p` 행의 단자 목록이 맞바뀜(각 1단자, ⚠️ 플래그는 그대로). 그 밖에 `소스:` 머리 줄 경로 차이 1줄(`skills/analog-gmid-design/assets/library/...` → `library/...`, 생성 위치에 따른 것) | `7ec8eff` 2026-09-17 (plan v5.18, U-08) | `da1ec7b` 2026-08-05 | **`7ec8eff`**. 커밋 본문에 "folded_cascode 입력 극성 정정(vin_p가 역상이었다 -- 사용자 승인 후 M1/M2 게이트 넷 맞바꿈, stick_diagram 동기화)"라고 적혀 있는데 md는 다시 만들지 않았다. md 마지막 커밋 뒤의 json 커밋 6개 중 앞의 5개(`00e7ebb`·`fa2fcfb`·`41f95e5`·`28e696d`·`0d586a2`)는 렌더링 결과가 같다(SAME) |
| `current_reuse_telescopic_ota` | **낡음** | **connectivity(수동 소자)**: `passive_elements` 6개(CL1 Vop–gnd, CL2 Vom–gnd, Cf1 Vom–Vip, Cf2 Vop–Vim, Cs1 Vip–gnd, Cs2 Vim–gnd)가 md에 없다. 그래서 Net 표 5행(Vim 2→4, Vip 2→4, Vom 4→6, Vop 4→6, gnd 15→19 단자), 수동 소자 표 +6행, 합계 줄 "6개 수동소자"→"12개"가 다르다. 트랜지스터 표·플래그·net 수(37)는 같다. 줄 수 130→136 | `7ec8eff` 2026-09-17 | `35023ea` 2026-08-04 | **`8ae82e7`** 2026-09-10 (plan v4.36 "보상망을 실제로 세고 Cc를 유도한다", ④ "빠져 있던 connectivity (사용자 확정)"로 CL/Cf/Cs 추가). 앞선 json 커밋 37개는 렌더링 결과가 같고, `8ae82e7`부터 HEAD까지 5개 커밋이 모두 DIFF |
| `ngcc_3stage_ff` | 아님 | 없음(바이트 단위로 같음. cwd=assets, 상대 경로로 생성) | `1bcddbb` 2026-09-21 | `5459a44` 2026-09-16 | -- (`1bcddbb`는 스펙 키만 바꿈, SAME) |
| `pushpull_follower_buffer` | 아님 | 없음 | `1bcddbb` | `12b7e69` 2026-09-15 | -- (`4ea001f`·`7ec8eff`·`1bcddbb` 모두 SAME) |
| `sf_pushpull_output_opamp` | 아님 | 없음 | `1bcddbb` | `4ea001f` 2026-09-15 | -- (SAME) |
| `two_stage_ota_sf` | 아님 | 없음 | `1bcddbb` | `ad85c2c` 2026-09-15 | -- (`2c2ddc1`·`7ec8eff`·`1bcddbb` SAME) |

md가 없는 library json은 `_TEMPLATE`·`common_gate_amplifier`·`nmcnr_amplifier`·`two_stage_ota` 4개다. 이번 B47 범위 밖이다. 참고로 `two_stage_ota`도 `eabc80a`에서 입력 극성을 정정했지만 md가 없어서 낡은 표가 생기지 않았다.

차이 분류 요약: 낡은 2회로의 차이는 **둘 다 connectivity 표**다. 주석·플래그·서식 차이는 없다. 유일한 비내용 차이는 `소스:` 머리 줄 경로다. 이 줄에는 `render_markdown(topology_json_path)`가 받은 인자가 그대로 들어간다(`topology_to_markdown.py` 95행). 그래서 어디서 실행했느냐에 따라 달라진다. 추적 md 6개 중 5개는 `library/...`(assets에서 실행), folded만 `skills/analog-gmid-design/assets/library/...`(저장소 루트에서 실행)다.

어긋난 원인은 같은 유형이다. json connectivity를 고친 커밋(`8ae82e7`, `7ec8eff`)이 `topology_to_markdown.py`를 다시 돌리지 않았다. SKILL.md 435행과 `references/topology-extraction-checklist.md` §5는 "connectivity를 고칠 때마다 실행"하라고 하지만 이를 강제하는 장치가 없다. 렌더러 쪽 변경(`topology_to_markdown.py`·`stick_diagram.load_topology`)은 원인이 아니다. HEAD 렌더러로 md 마지막 커밋 시점의 json을 렌더링하면 추적 md와 같게 나온다.

줄바꿈: 추적 md 6개는 모두 `i/lf w/crlf`이고 `core.autocrlf=true`, `.gitattributes` 속성은 없다. 스크립트는 Windows 텍스트 모드로 써서 작업 트리에 CRLF를 남긴다. 커밋할 때 LF로 정규화되므로 재생성 diff는 위 내용 줄만 남는다.

## 2. 이 md를 읽는 곳 -- 재생성하면 판정·기준선이 바뀌는가

grep 범위: `tools/**`, `skills/analog-gmid-design/**/*.py`, `SKILL.md`, `references/**`, `docs/01-plan`·`02-design`·`03-analysis`, `.ai/**`.

- **md 내용을 읽는 코드·test·게이트는 0건이다.** `tests/**`에서 `topology.md`, `render_markdown`, `topology_to_markdown`를 찾으면 `tests/contracts/test_df23_inventory.py` 57행 하나만 나온다. 이 줄은 DF-23 전수 목록의 scope에 모듈 이름 `topology_to_markdown`을 올린 것이고 md 파일은 읽지 않는다.
- `tools/gates/gate_config.json` 10·16행: `topology_to_markdown.py::__main__`을 도달성 루트로 쓴다. 코드 쪽이라 md를 다시 만들어도 영향이 없다.
- `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/probe-df23-summary.md` 186·216행, `df23_inventory.json`: `topology_to_markdown.py` 200행의 파일 이름 리터럴 `f"{topo_name}.topology.md"`를 DF-23 항목으로 센다. 역시 코드 쪽이라 영향이 없다.
- 계획 U-34(1109행)는 `ngcc_3stage_ff.topology.md`를 산출물로 부른다. 이 md는 이미 일치한다.
- 사람이 읽는 곳: SKILL.md 435~436행, checklist §5, 계획 WP-09(291행, "회로도 이미지 판독은 net 표로 재검증"). **낡은 표의 실제 위험은 사람의 판독이다.** UD-17 공동분석 같은 회로 해석 자리에서 사용자가 이 표를 보면, folded의 입력 극성이 반대로 보이고 CRTO의 보상·부하 C가 빠져 보인다.
- **DEC-40(기준 약화 승인)과는 관계없다.** md는 판정 기준선이 아니다. `sky130_regression_reference.json`·`canonical_theta_star.json` 같은 기준선이나 test 기대값도 md를 참조하지 않는다. 재생성은 어떤 판정도 바꾸지 않는다.
- `.ai/verification/**`에 나오는 이름들은 과거 판정 기록 안의 경로 목록·AST 스냅샷이다. md를 다시 읽지 않는다.

## 3. 일치 test 유무와 제안

**현재 md와 json의 일치를 검사하는 test는 없다**(위 grep 결과 0건). 재발을 막는 장치가 없다는 뜻이다.

### 쓰기 경로(계획 N3.12.2, 591행~) 확인

- 636행 `| 오케스트레이터 | skills/analog-gmid-design/assets/library/*.topology.md | -- | 없음 |`. **md 재생성은 오케스트레이터 몫이고 조건은 `없음`이라 승인 기록이 필요 없다.** 경로표상으로는 `Role: doc` 커밋 하나면 된다. 비교하면 같은 표의 `*.topology.json` 행(635행)은 조건이 `승인 기록`이다.
- connectivity 원본(json)은 두 커밋 모두 이미 사용자 승인·확정을 거쳤다(`7ec8eff` "사용자 승인 후 M1/M2 게이트 넷 맞바꿈", `8ae82e7` "사용자 확정"). 그래서 md 재생성은 회로 해석이 아니라 이미 확정된 사실을 파생 표에 옮기는 일이다.
- 다만 backlog `backlog_additions.md` B47 항목은 "재생성 커밋은 사용자 확인 뒤"라고 적어 두었다. 그래서 아래 질문으로 확인만 받는다. 승인 기록 파일은 만들지 않는다.
- 일치 test는 `skills/analog-gmid-design/assets/tests/**` 경로라 **gmid-test-author**가 쓴다(경로표 `gmid-test-author | skills/analog-gmid-design/assets/tests/** | tests/tools/** 제외 | 없음`). 검사를 새로 더하는 것이지 기준을 약하게 하는 것이 아니므로 DEC-40 승인 대상이 아니다. 피검 대상이 데이터(md·json)뿐이고 엔진 코드를 고치지 않으므로 test-only card다(P10 `20260930-p10-df23-inventory`와 같은 형태).

### 제안 test (spec card 초안 재료)

- 위치: `skills/analog-gmid-design/assets/tests/contracts/test_topology_md_sync.py`(가칭). test glob 충돌은 card를 쓸 때 grep으로 확인한다.
- oracle 독립성(작성자≠검증자, test-author가 피검 함수로 기대값을 만들지 않는다는 규칙): **`render_markdown`를 불러 문자열 동등을 보지 않는다.** 그렇게 하면 렌더러 결함까지 기준으로 굳어진다. 대신 md 표를 직접 파싱해 json과 집합으로 대조한다.
  1. 계약 1: `library/` 안의 모든 `<n>.topology.md`에 대해 같은 이름의 `<n>.topology.json`이 있다.
  2. 계약 2 (소자 표): md "소자별 연결 표"의 (name, kind, source, drain, gate) 집합 = json `netlist`의 같은 5필드 집합.
  3. 계약 3 (수동 소자·ideal source 표): md의 (name, kind, terminals) 집합 = json `passive_elements`·`ideal_sources`. 표가 없으면 json 쪽도 비어 있어야 한다.
  4. 계약 4 (Net 표): net마다 md 단자 목록 집합 = json에서 직접 세운 (device.terminal) 집합. 트랜지스터 source/drain/gate와 elements의 `t<i>`를 쓴다.
  5. 계약 5 (합계 줄): 소자·수동소자·ideal source·net 개수가 json과 같다.
  6. `소스:` 머리 줄과 플래그 절(⚠️/ℹ️ 문구)은 대조하지 않는다. 경로 의존 줄이고 서식이라 범위 밖이다.
- red-green 증거: `a796468`(재생성 전)에서는 folded(계약 2·4)와 CRTO(계약 3·4·5)가 FAIL한다. 재생성 doc 커밋 뒤에는 6/6 PASS다. 다른 4회로가 이미 PASS라는 사실은 무동작 증거가 된다(일반화 측정).
- 순서: (1) 재생성 doc 커밋을 먼저 하고, (2) test card를 이어서 한다. auditor의 red는 (1)의 부모에서 재현한다(P10 계약 8 `measured_at` 방식). 반대로 test를 먼저 넣으면 master가 일시적으로 red가 된다.
- 판단할 점: 메모리 "인프라 작업은 gmid 엔진을 막을 때만"과 어긋나지 않는지. 재생성 자체는 UD-17 공동분석(회로 해석)의 입력 표를 바로잡는 일이라 gmid 목표에 직접 필요하다. test card는 작고 독립적이라 다른 작은 test-only card와 묶는 것(card 처리 속도 규칙의 "작은 card 묶기")을 기본안으로 둔다.

### 부수 관찰 (범위 밖, backlog 후보)

- `소스:` 머리 줄이 실행 cwd와 인자 형태에 따라 달라진다. DF-36(instance.json `topology_ref`를 저장소 루트 기준 상대 경로로 저장)과 같은 유형이다. 이번 재생성은 **assets를 cwd로 하고 `library/<n>.topology.json`으로 실행**해 5개 md와 형식을 맞추는 것이 기본안이다(folded 머리 줄도 함께 `library/...`로 바뀐다). 렌더러가 경로를 정규화하는 수정은 엔진 쪽 card이므로 따로 둔다.
- `topology_to_markdown.py`는 출력 경로를 주지 않으면 추적 md를 덮어쓴다. backlog B47 본문에 2026-10-01 실사례가 적혀 있다. 표만 출력하려는 목적이라면 출력 경로 인자를 사본으로 주는 운영 규칙이 필요하다.

## 4. 권고

1. **재생성 doc 커밋 1개**(`Role: doc`, 오케스트레이터): `folded_cascode.topology.md`, `current_reuse_telescopic_ota.topology.md` 두 파일만 바꾼다. 실행 방법은 `cd skills/analog-gmid-design/assets && python -B topology_to_markdown.py library/<n>.topology.json`이다. 커밋 전에 `git diff --stat`으로 **나머지 4개 md에 diff가 0인지** 확인한다(앞의 측정으로는 0이다). 커밋 본문에 어긋남을 만든 커밋(`7ec8eff`, `8ae82e7`)을 적는다. 경로표 조건이 `없음`이라 승인 기록은 필요 없다.
2. **일치 test card 1개**(test-only, gmid-test-author): 위 계약 1~5를 넣는다. red는 재생성 커밋의 부모(`a796468` 또는 그 시점 HEAD)에서 재현한다.
3. backlog B47은 1이 끝나면 닫고, 2를 B47-b로 둔다. 머리 줄 경로 정규화와 덮어쓰기 기본 동작은 별도 backlog로 둔다.

## 5. 사용자에게 할 질문 (그대로)

> B47 측정 결과, 추적 md 6개 중 2개가 json과 다릅니다. 둘 다 connectivity 표 차이입니다.
> - `folded_cascode.topology.md`: M1/M2 게이트(`vin_p`↔`vin_n`)가 json과 반대입니다. `7ec8eff`(9/17, 승인된 극성 정정)에서 md를 다시 만들지 않았습니다.
> - `current_reuse_telescopic_ota.topology.md`: CL1/CL2·Cf1/Cf2·Cs1/Cs2 6개 C가 빠져 있습니다. `8ae82e7`(9/10, 사용자 확정 connectivity)에서 md를 다시 만들지 않았습니다.
> 나머지 4개는 일치합니다. 이 md를 읽는 test·게이트·기준선은 없어서, 재생성해도 판정은 바뀌지 않습니다(DEC-40과 무관).
>
> (1) 두 md를 현재 json으로 다시 만드는 doc 커밋 1개를 진행해도 될까요? (경로표상 승인 기록은 필요 없습니다. json은 건드리지 않습니다.)
> (2) 같은 일이 다시 생기지 않도록 md 표를 json과 직접 대조하는 일치 test(test-only card)를 추가할까요? 지금 바로 할지, 다른 작은 card와 묶을지도 알려 주세요.
