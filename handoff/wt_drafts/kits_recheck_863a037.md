# Phase 3 착수 키트 재점검 -- gate master 863a037 (2026-10-07)

대상: `t0_launch.sh`·`fu_launch.sh`·`g1_launch.sh`·`d0a_launch.sh`·`d0b_launch.sh` (+ 키트가 쓰는 `launch_common.sh`, T0 운반 핀 `t0_carry.sh`).
방법: 읽기 전용. 모래상자 `/c/g391`(clone `-c core.autocrlf=false`, 가짜 gate `C:/g391/gate.git`, TMP/TEMP `/c/g391/tmp`)에서
`conds`(T0·FU·D0a·D0b), G1 `pre`(실제 복제본) + G1 `mk-sandbox --sim-pred all` 뒤 `pre`·`local`(모래상자 커밋만, push 없음).
실제 저장소에서는 T0·FU `conds`만(fetch 없음, 캐시 안 씀 -- 생긴 빈 `*_launch_state.txt.tmpd` 두 개는 지움). 키트·초안은 고치지 않았다.
기준 차이: `2183f2e..863a037` = b26pre(새 test `tests/contracts/test_b26pre_existing_paths.py` + 판정 기록·spec) + backfill spec/interface 문서뿐 -- 엔진·tools·계획·레지스트리 변경 0.
엔진 변경은 `dafe5cf..863a037`에서 B34 `2eb7e55`(10-06) 하나: `sizing_recipe.py` 5줄, `stick_diagram.py` 70줄(-14줄 밀림).

## 키트별 결과

| 키트 | 지금 실패하는 착수 조건 | 판정 |
|---|---|---|
| T0 `conds` | 6 backfill·7 B26-1·8 B33 판정 기록 없음, 9 `test_b26_rail_accessor.py` 없음, 11 V4 면제 승인 기록 없음(초안에 `<MATCH 결과 줄` 자리표시 1개 남음), measured 앵커 없음 | 전부 예상(선행 미병합, (아) MATCH는 B26-1 뒤 착수 0단계). 1~5·10 충족(b26pre 조건 5가 오늘 충족) |
| FU `conds` | 7 backfill·8 B26-1·9 B33, measured 앵커 없음 | 예상. 11(DR·ACF = dd60db6)·12(future SR·SD·TL만) 여전히 충족 |
| G1 `pre`(복제본) | backfill 판정 기록 없음에서 멈춤 | 예상 |
| G1 `pre`/`local`(선행 7건 흉내) | **measured rev `dafe5cf`(초안 '작성 전 실측' 가장 새 문단) 뒤 G1 입력 차이**: `sizing_recipe.py`·`stick_diagram.py`(B34) | **드리프트(B34 원인, 오늘 병합 아님)**. 그 문단만 더하면 pre·doc·card·appr·final(로컬 EL4 receive exit 0) 전부 통과 -- 패치 5곳 줄(V3 317·V6 320·V7 321·거부 338·계획 533), interface 신규 7행, 단계 수 31, UD-5 원문 대조 OK |
| D0a `conds` | 2 선행(backfill·B26-1·B33·G1), 4 G1 이름(SourceIndex·moved_defs) 없음, 6 measured 앵커 없음 | 예상. 1·3·5·7 충족, 8((e1)·(e4) AST 스캔) 0·0 충족 |
| D0b `conds` | 2 선행(…·G1·FU·D0a) + FU 두 줄 없음, 4·5·7 D0a 도구 없음, 8 measured 앵커 없음 | 예상. 1(D-11 승인·MOD1 토큰)·3·6 충족 |

공통(실제 저장소): 지금 `role/{test,code,audit}/20261001-b26-backfill-interdig-final-audit`가 있어 T0·FU·G1 `pre`의 역할 브랜치 0, D0a 조건 7, D0b 조건 6은 실제 저장소에서 실패한다 -- backfill 진행 중이라 예상(모래상자 복제본에는 로컬 role 브랜치가 없어 충족으로 나왔다).

## 핀(sha) 대조

* T0 `t0_carry.sh` `T0_DRAFT_SHA256`(canon(`approval_20260930-p3-tests-location-free.md`)) = `ca5385a6…a094` 실측 일치, `T0_QCHK_SHA256`(`t0_quote_check.py`) = `03d07619…4421` 일치. 고칠 것 없음.
* D0a 초안 현재 sha256 `7012f2ffc41f6b9f…`. 5개 키트·launch_common·briefs 어디에도 D0a 초안 sha 핀이 없다(옛 `b5b1e96a…`는 `review_d0a_det4.md` 기록에만). 고칠 것 없음.
* D0b 초안 `7b72cd5c77184460…` -- `d0b_launch.sh`는 요약 캐시 키로 실행 때 계산(핀 아님). 아직 캐시 없음(D0a 미병합). 고칠 것 없음.
* M card 초안(m1~m6·m8~m10)은 2026-10-07 12:47에 다른 작업이 고쳤다 -- 5개 키트 어디도 M card sha를 핀하지 않는다.
* interface card(게이트 캐시 판 `interface_card.py`, 863a037 트리): T0 기존 6행 = `IFC_REQ`(rail_declaration 없음 -- B26-1 전 정상), FU 0·0, D0a 기존 0·신규 `move_plan.*`·`move_plan.main` = `IFC_NEW`, D0b 0·0, G1 0·7(SourceIndex.tree 포함). 전부 키트 기대와 같다.

## 줄 인용 드리프트(전부 B34 `2eb7e55` 또는 10-06 계획 커밋 원인 -- 오늘 병합 원인 0)

| 위치 | 지금 | 863a037 실측 | 원인 |
|---|---|---|---|
| `draft_p3_g1.spec.md` 349행(작성 전 실측 8) 및 267·280행 v9 문단 | `stick_diagram.py:1050`·`:8962` | `:1049`·`:8948` | B34 |
| `draft_p3_d0b.spec.md` 272행 | `stick_diagram.py:8478` `class NameCollisionVerdict`·`:8486` `def check_topology_name_uniqueness` | `:8464`·`:8472` | B34(초안 10-06 22:28 개정 때 반영 안 됨) |
| `d0a_launch.sh` 157행 `COND_TITLE_3`, `draft_p3_d0a.spec.md` 26행 | '계획 991행' | 계획 993행(`모든 Phase의 공통 착수 조건 … 이전 Phase DoD PASS`) | `fd4ef8c`·`29d2fc2`(10-06 계획 2줄 추가) |
| FU kit-cmds `sed -n 26,29p`/`36,39p`, 레지스트리 217행 | -- | 그대로(DR·ACF = dd60db6, 217행 `design_report.py:32`) | 변화 없음 |
| T0 `sizing_recipe.py:24`, D0a `sizing_recipe.py:5302`·`:1411` | -- | 그대로 | 변화 없음 |

## 고칠 것(편집하지 않음 -- 제안)

1. **G1**(착수 전 필수, 키트 설계대로): G1 착수 때 `g1_launch.sh kit-cmds` 재측정 후 `draft_p3_g1.spec.md` '작성 전 실측'에 `(착수 재측정 <날짜>, gate \`master\` \`<rev>\`, …` 문단 추가. 그 문단에서 엔진 사실 8의 `__file__` 줄을 `1049·8948`로(B34 뒤 값), 349행 인용도 함께. 이 문단이 없으면 `pre`가 424행에서 멈춘다(지금 실측).
2. **D0b 초안** 272행: `:8478`→`:8464`, `:8486`→`:8472`(또는 D0b 착수 0단계 재측정 때 함께).
3. **D0a**: `d0a_launch.sh` 157행 `COND_TITLE_3`과 `draft_p3_d0a.spec.md` 26행 '계획 991행' → '계획 993행'(표시 문자열, 판정 영향 없음).
4. (외관, 기존 결함) `t0_launch.sh` `stage_conds` 291행·`fu_launch.sh` `stage_conds` 235행: exit 3(미충족)에서도 ERR trap이 `[중단] …: return $rc`를 찍는다 -- d0a·d0b처럼 `return $rc` 앞에 `trap - ERR`.
5. T0 착수 0단계 (라): b26pre가 더한 `tests/contracts/test_b26pre_existing_paths.py`(모듈 import + 속성 호출만, `__file__`은 경로 계산 1곳, monkeypatch·getsource 없음)를 contracts_files A/B군으로 분류 -- `t0_briefs.md` 92행이 이미 예고, 키트 수정 불필요.

나머지 미충족은 전부 선행(backfill·B26-1·B33·G1·FU·D0a) 미병합, T0 V4 면제 MATCH 미기입, measured 앵커 미기입(착수 0단계 재측정 대상) 때문이며 예상된 상태다. 오늘 병합(b26pre `2db7622`, backfill card `863a037`)이 일으킨 드리프트는 없다.
