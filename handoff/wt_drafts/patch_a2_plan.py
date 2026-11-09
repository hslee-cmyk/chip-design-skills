#!/usr/bin/env python3
"""A2 계획 정정 패치 -- DEC-60 레일 넷 전환기 종료 + DF-19·DF-26 넷 몫을 MG1에서 분리(B26-1~B26-4).

승인: `.ai/approvals/20260930-b26-before-phase3.md`(target_kind: decision, target U2-B26-BEFORE-PHASE3).
대상: docs/01-plan/features/gain-budget-gmid-sizing.plan.md (필수 인자)
      docs/01-plan/features/gain-budget-gmid-sizing.history.md (--history, 선택)

사용:
  python -B patch_a2_plan.py <plan.md> [--history <history.md>] [--gate-dir <repo>/tools/gates] [--dry-run]

성질:
* 결정적: 정확 부분 문자열 치환만 한다. 치환마다 옛 글 정확히 1회(적용 전) 또는 새 글 정확히 1회(적용 뒤)여야 한다.
  파일 안 치환들이 '전부 적용 전' 또는 '전부 적용 뒤' 둘 중 하나가 아니면(부분 적용 상태) 아무것도 쓰지 않고 실패한다.
* 멱등: 이미 적용된 파일에 다시 돌리면 바이트가 그대로이고 "already applied"를 출력한다.
* 바이너리 안전: 바이트로 읽고 UTF-8로 풀어 치환한 뒤 같은 인코딩으로 쓴다. 줄 끝(계획 CRLF, 이력 LF)은 파일에서 감지해 그대로 둔다.
  치환 글에는 줄바꿈이 없고, 삽입 줄에는 감지한 줄 끝을 붙인다.
* 표 보호: 각 치환은 옛 글과 새 글의 `|` 수·백틱 수 홀짝·괄호 균형이 같아야 한다(표 칸이 깨지지 않는다).
* --gate-dir를 주면 merge_gate.plan_tables_hash를 정정 전후로 재서 같음을 단언하고,
  N5.2 DF-19·DF-26 `수정 Phase` 칸의 괄호 밖 Phase 토큰(P10 계약 3이 읽는 값)이 그대로임을 단언한다.
"""
import argparse
import importlib
import os
import sys

# --------------------------------------------------------------------------------------------- 계획서 치환
PLAN_EDITS = [
    ("frontmatter version",
     "version: 5.19",
     "version: 5.20"),

    ("DEC-60 발췌 1(넷 전환기 종료, 전압 전환기 유지)",
     "`supply_nets`가 없는 기존 4개 회로는 **전환기 이름집합 해석**으로 현 코드 이름 집합(정본 표 N3.16, DF-19·DF-26)을 쓴다. "
     "MG1(Phase 4) 전까지만 전환기 이름집합 해석을 쓴다: `supplies_v`가 없으면 레일 둘, 가장 높은 레일 = spec `vdd`, 가장 낮은 레일 = 0 V.",
     "레일 **넷**의 전환기 이름집합 해석은 B26-1(spec card `20260930-b26-rail-accessor-set`)에서 끝낸다: B26-1부터 `supply_nets`가 없는 topology는 "
     "`load_topology`가 `ValueError`로 거부하고, 넷 이름 집합으로 대신 판정하지 않는다(현 코드의 이름 집합 -- 정본 표 N3.16, DF-19·DF-26 -- 은 B26-1~B26-4가 없앤다). "
     "레일 **전압**은 MG1(Phase 4) 전까지만 전환기 해석을 쓴다: `supplies_v`가 없으면 레일 둘, 가장 높은 레일 = spec `vdd`, 가장 낮은 레일 = 0 V."),

    ("DEC-60 (i)(ii) 적용 범위 -> (i)만 스펙 선언 회로, (ii)는 로드 거부",
     "**(i)(ii)는 사이징 스펙이 선언된 회로에만 적용한다** -- 스펙이 없는 회로는 레일 전압이 선언될 자리가 없어 (i)(ii)의 판정 입력 자체가 없고, "
     "그대로 두면 거부도 통과도 규정되지 않는다(실측 9회로 중 5회로). 스펙 미선언 회로는 구조 검사인 (iii)만 받고 6a 구조 유도 대상이 되며, 스펙이 선언되는 시점에 (i)(ii)가 걸린다.",
     "**(i)은 사이징 스펙이 선언된 회로에만 적용한다** -- 스펙이 없는 회로는 레일 전압이 선언될 자리가 없어 (i)의 판정 입력 자체가 없고, "
     "그대로 두면 거부도 통과도 규정되지 않는다(실측 9회로 중 5회로). 스펙 미선언 회로는 (ii)(로드 거부)와 구조 검사인 (iii)만 받고 6a 구조 유도 대상이 되며, 스펙이 선언되는 시점에 (i)이 걸린다."),

    ("DEC-60 발췌 2((ii) 판정 입력)",
     "(ii) 선언이 없으면 전환기 이름집합 해석이 찾은 레일 수와 실행 spec 레일 전압의 부호다. 이름집합 해석으로 찾은 레일이 정확히 둘이 아니거나"
     "(`agnd` 같은 중간 전위 넷은 이 해석에서 레일로 읽히지 않는다) 레일 전압에 음수가 있으면 `supply_nets` 없이는 거부한다.",
     "(ii) `supply_nets` 미선언 -- B26-1부터 스펙 유무와 무관하게 `load_topology`가 거부한다(로드의 첫 거부. 이름 집합 판정으로 넘어가지 않으므로 "
     "레일 수·전압 부호를 셀 판정 입력이 생기지 않는다)."),

    ("DEC-60 (iii) 근거 문장의 (i)(ii) 지칭",
     "이 조건은 (i)(ii)와 달리 사이징 스펙이 없는 library 회로에서도 발동한다 -- (i)(ii)만 두면",
     "이 조건은 (i)과 달리 사이징 스펙이 없는 library 회로에서도 발동한다 -- (i)과 옛 이름 집합 판정만 두면"),

    ("DEC-60 발췌 3(한시 허용 = 전압만)",
     "전환기 이름집합 해석은 **레일이 정확히 둘이고 그 이름 집합을 쓰는 회로에만 MG1(Phase 4)까지 한시 허용**한다.",
     "레일 **전압**의 전환기 해석은 **레일이 정확히 둘인 회로에만 MG1(Phase 4)까지 한시 허용**한다(레일 넷의 전환기 이름집합 해석은 B26-1에서 끝난다)."),

    ("DEC-69 MG1 범위",
     "MG1 Phase 4(레일 코드)",
     "MG1 Phase 4(레일 전압 코드. 레일 넷 코드는 B26 -- DF-19·DF-26)"),

    ("GB0 로드 게이트 레일 문구",
     "`supply_nets`·`supplies_v` 선언 또는 전환기 이름집합·기본 해석(DEC-60: `supply_nets`는 library 회로 전부 필수이고 "
     "**레일 셋 이상·음전위 레일 회로는 미선언이면 여기서 거부**한다, 전환기 이름집합 해석은 레일이 정확히 둘인 회로에만 MG1까지 허용, "
     "레일 셋 이상·음전위 레일이면 `supplies_v` 필수, `supplies_v` 넷 키 = `supply_nets`)",
     "`supply_nets` 선언(없으면 `load_topology`가 거부 -- B26-1)과 `supplies_v` 선언 또는 전환기 전압 해석(DEC-60: 전환기 전압 해석은 "
     "레일이 정확히 둘인 회로에만 MG1까지 허용, 레일 셋 이상·음전위 레일이면 `supplies_v` 필수, `supplies_v` 넷 키 = `supply_nets`)"),

    ("W0 레일 노드 전압 문구",
     "(미선언이면 DEC-60 전환기 이름집합·기본 해석 -- 레일이 정확히 둘인 회로에만 허용)",
     "(`supplies_v` 미선언이면 DEC-60 전환기 전압 해석 -- 레일이 정확히 둘인 회로에만 MG1까지 허용. 레일 넷은 `supply_nets`만 -- B26-1)"),

    ("N3.16 레일 넷 행 단계 칸",
     "| 레일 넷 | `supply_nets`(list) | topology | sizing_recipe `_DEFAULT_RAIL_HI/LO`, `rail_nets`, stick_diagram `_RAIL_NETS` | MG1 |",
     "| 레일 넷 | `supply_nets`(list) | topology | sizing_recipe `_DEFAULT_RAIL_HI/LO`, `rail_nets`, stick_diagram `_RAIL_NETS` | "
     "B26(DF-19·DF-26 넷 몫, Phase 3 착수 전 가능: B26-1 집합 판정, B26-2 극성, B26-3 MNA 고정 노드, B26-4 이름 상수 삭제와 lint). "
     "kcl_residual 선언의 metric 키 `rail_nets`는 B26-1에서 거부(`ValueError`)한다. "
     "그 밖의 옛 키(계획 `supplies`, spec 스칼라 `vdd`, metric 인자 `supply_nets`) 거부 게이트는 MG1 |"),

    ("MG1 행",
     "| MG1 | 레일: topology `supply_nets`, spec `supplies_v`, `vdd` 유도 함수, 이름 집합 제거, metric 인자 `supply_nets`/`rail_nets` 정리. "
     "옛 키 거부 게이트 + IC11 | code-author / test-author | Phase 4(DF-19·24·26과 같은 변경 단위) |",
     "| MG1 | 레일 전압: spec `supplies_v`, `vdd` 유도 함수, metric 인자 `supply_nets` 정리. "
     "옛 키(계획 `supplies`, spec 스칼라 `vdd`, metric 인자 `supply_nets`) 거부 게이트 + IC11. "
     "레일 넷(`supply_nets` 배선, 이름 집합 제거, kcl_residual `rail_nets` 거부)은 B26(DF-19·DF-26 넷 몫)이 먼저 한다 | code-author / test-author | "
     "Phase 4(DF-24, DF-19의 전압 몫과 같은 변경 단위. B26-1 병합이 선행) |"),

    ("DF-19 수정 Phase 칸(괄호 밖 토큰 4 유지)",
     "| 4(DEC-60 `supply_nets`·`supplies_v` 선언으로 교체, MG1, DF-26과 같은 변경 단위, U-26) |",
     "| 4(DEC-60 선언으로 교체. 넷 몫(`supply_nets`)은 B26-1~B26-4로 나누고 Phase 3 착수 전에 해도 된다 -- DF-26과 같은 변경 단위. "
     "전압 몫(`supplies_v`, 스칼라 `vdd` 리터럴)은 MG1과 같은 변경 단위, U-26) |"),

    ("DF-19 비고(전수 정본 = history H4 AST 전수, assets 밖 사이트 B35)",
     "**위치 열은 전수여야 한다**: 레일 넷 이름을 동작 조건으로 쓰는 운영부 함수가 실측 29개(`sizing_recipe` 15 · `stick_diagram` 10 · `run_harness` 4)인데 "
     "현 목록은 일부만 적는다 -- MNA 고정 노드(`fixed = {\"gnd\": 0.0}`)와 기둥 추적의 진입 넷 비교가 특히 빠져 있고, 이 둘은 DEC-71 기둥 유도·IC11 3레일이 겨누는 고장이다. "
     "Phase 4에 **'운영부 레일 이름 리터럴 0' lint**를 두고 목록을 그 lint 산출로 대체한다(원자료는 history H4) |",
     "**위치 열은 전수여야 한다**: 넷 판정 운영 함수 전수의 정본은 history H4의 AST 전수 행이고, B26-4의 **'운영부 레일 이름 리터럴 0' lint** 산출이 그 목록을 대체한다. "
     "MNA 고정 노드(`fixed = {\"gnd\": 0.0}`, B26-3)와 기둥 추적의 진입 넷 비교(B26-2)는 DEC-71 기둥 유도·IC11 3레일이 겨누는 고장이다. "
     "**assets 밖 사이트**: `skills/analog-grammar/assets/netclass.py`의 `RAILS`·`RAILS_POS`·`RAILS_NEG`(대소문자 무관 이름 집합)를 stick_diagram이 "
     "`_import_analog_grammar`로 불러 쓴다(사용 함수 목록은 history H4). 이 사이트는 B26-1 범위 밖이고 백로그 B35가 처리한다: analog-grammar 진입 함수에 "
     "기본값 없는 레일 인자를 두고 stick_diagram은 B26-1의 `meta[\"rails\"]`를 넘긴다(착수 조건 = B36 게이트 변경 card와 `plan_tables` 승인, B26-2). "
     "B26-1에서 빼는 이유는 analog-grammar 파일이 N3.12.2 쓰기 경로표의 어느 주체 행에도 없다는 것(게이트 공백, 백로그 B36)과 대체 방식이 극성 선언을 먼저 요구한다는 것이다. "
     "호출부에서 넷 이름을 바꿔 넘기는 번역은 쓰지 않는다(이름 집합을 인코딩 통로로 쓰게 되고 출력 전부의 역변환이 필요하다) |"),

    ("DF-26 위치·수정 Phase 칸(괄호 밖 토큰 4 유지)",
     "| sizing_recipe.py 3882~3883, stick_diagram.py 3147 참고 | 4(DEC-60 구현, DF-19와 같은 변경 단위) |",
     "| sizing_recipe `_DEFAULT_RAIL_HI`/`_DEFAULT_RAIL_LO`, stick_diagram `_RAIL_NETS`(모듈 상수. 사용처 전수는 DF-19 비고) | "
     "4(DEC-60 넷 몫 구현 = B26-1~B26-4, Phase 3 착수 전에 해도 된다. DF-19와 같은 변경 단위. 전압 몫은 MG1) |"),

    ("N6.1 Phase 4 행 범위 칸(Phase 열 무변경)",
     "MG1 레일 이름 변경(DEC-69)",
     "MG1 레일 전압 이름 변경(DEC-69). DF-19·DF-26의 넷 몫(B26-1~B26-4)은 Phase 3 착수 전에 해도 된다"
     "(이 행의 범위에서 빠지지 않는다 -- 먼저 병합하는 card의 spec card `phase` 값은 병합 시점의 진행 Phase다)"),

    ("N4.3 공격 13 기대",
     "GB0 로드 게이트 거부(DEC-60). 전환기 이름집합 해석으로 조용히 넘어가지 않음을 **거부 로그로** 증명하고,",
     "GB0 로드 게이트 거부(DEC-60). B26-1부터는 `load_topology`의 `supply_nets` 없음 거부가 그 거부이고 6a GB0 로드 게이트가 그대로 쓴다. "
     "이름 집합 판정으로 조용히 넘어가지 않음을 **거부 로그로** 증명하고,"),

    ("N6.2 6a supply_nets 미선언 문장",
     "`supply_nets` 미선언 회로는 레일·교류접지 집합이 전환기 이름집합 해석으로 정해져 `agnd`를 레일로 읽지 못하므로 그 회로의 "
     "교류접지·셀 분류·구동 종류·stage 경계·극점 노드·기둥 유도·DEC-65 방향 분류 판정을 무효로 보고한다(PASS로 세지 않는다)",
     "`supply_nets` 미선언 topology는 B26-1부터 로드에서 거부되므로 레일·교류접지 집합을 이름 집합으로 정하는 회로가 없다"
     "(미선언 회로의 판정을 무효로 보고하던 옛 조건은 history H2)"),

    ("U-26 (a) 기본안 칸",
     "확정 전에는 DEC-60 전환기 이름집합·기본 해석(레일이 정확히 둘인 회로만)",
     "확정 전에는 DEC-60 전환기 전압 해석(레일이 정확히 둘인 회로만). 레일 넷은 9/9 선언이라 전환기가 없다(B26-1)"),

    ("U-26 (b) 필요 시점 칸",
     "미선언이면 레일이 전환기 이름집합 해석으로만 정해져 `agnd`가 레일로 읽히지 않고, 그 회로의 교류접지 집합·셀 분류·구동 종류·stage 경계·극점 노드·루프 탐지·"
     "기둥 유도(DEC-71 (1))·DEC-65 방향 분류가 전부 무효다 -- 무효 판정은 PASS로 세지 않고 보고한다)",
     "B26-1부터 미선언 topology는 로드에서 거부된다 -- 미선언 시 무효가 되던 판정 목록은 history H2)"),
]

# --------------------------------------------------------------------------------------------- 이력 문서
# 기존 줄 안 치환
HIST_EDITS = [
    ("H1 DEC-60 결정일·경위",
     "| DEC-60 | 2026-09-15 | 2026-09-15 U-26으로 nmcnr `supplies_v{vdd: 0.9, vss: −0.9}` 확정(사용자 \"1.8로 고쳐\", \"+-0.9로 고치고\"). "
     "v5.15에서 `supply_nets`를 library 회로 전부 필수로 올리고 GB0 로드 게이트 거부를 붙였다 |",
     "| DEC-60 | 2026-09-15, 10-01 | 2026-09-15 U-26으로 nmcnr `supplies_v{vdd: 0.9, vss: −0.9}` 확정(사용자 \"1.8로 고쳐\", \"+-0.9로 고치고\"). "
     "v5.15에서 `supply_nets`를 library 회로 전부 필수로 올리고 GB0 로드 게이트 거부를 붙였다. "
     "2026-10-01 결정 A2(사용자 결정 U2, 승인 기록 `20260930-b26-before-phase3`)로 레일 **넷**의 전환기 이름집합 해석을 B26-1(`20260930-b26-rail-accessor-set`)에서 끝내고 "
     "DF-19·DF-26의 넷 몫을 MG1에서 뗐다(v5.20. 원문은 아래 U 표 'A2' 행, 정정 내용은 H2) |"),

    ("H4 '29개' 행의 계획서 사용처",
     "| `review11_code_literals_opsplit.txt` | 계획서 DF-19 |",
     "| `review11_code_literals_opsplit.txt` | 계획서 DF-19(v5.19까지. v5.20부터 아래 '넷 판정 운영 함수 AST 전수' 행이 대체) |"),
]

# 줄 삽입: (이름, 앵커 줄 접두(정확히 한 줄이 이것으로 시작), 삽입할 줄(줄 끝 제외))
HIST_INSERTS = [
    ("H1 U 표 -- A2 결정 원문",
     "| Phase 1 완료 | 2026-09-23 |",
     "| A2 레일 넷 전환기 종료·B26 앞당김(U2) | 2026-10-01 확정 | \"승인 (Recommended)\" -- 질문(2026-09-30): ① DEC-60의 '넷 이름으로 전원을 판정하는 전환기' 조항을 끝내고 "
     "전원은 topology `supply_nets` 선언으로만 정하며 선언이 없으면 오류 ② DF-19·DF-26 가운데 전원 넷 판정 몫을 MG1(전압값 작업)과 분리 ③ B26-1(spec card "
     "`20260930-b26-rail-accessor-set`)과 B34(`20260930-b34-grammar-explicit`, analog-grammar 부재 시 조용한 폴백 -> `ImportError`)를 Phase 3 모듈 분할보다 먼저(Phase 2 진행 중, "
     "card `phase: 2`). 다른 선택지는 '①②만 승인, ③은 Phase 3 뒤'와 '보류'. 원칙 기본안(사용자 원칙 '엔진 식은 topology 무관', U-26 (b) 9/9 선언으로 전제 소멸)이어도 "
     "DEC-60 한시 조항의 기한과 Phase 4 DF의 순서 변경은 결정 내용이라 U-39·DF-35/36 선례대로 사용자 원문 승인 한 건으로 받았다(review_b26_1 S3). "
     "승인 기록 `20260930-b26-before-phase3`(target_kind decision). 판정 표(`plan_tables_hash` 입력)는 바꾸지 않아 `plan_tables` 승인은 없다. "
     "재검토: B26-1 또는 B34가 병합되지 않은 채 Phase 3 M card가 `stick_diagram`·`sizing_recipe`를 나누기 시작하면 병합되지 않은 card의 앞당김은 효력을 잃는다 |"),

    ("H2 정정·폐기 행 -- DEC-60 넷 전환기",
     "| 옛 형태 \"input+cascode 동시 결정\" |",
     "| DEC-60 레일 넷 전환기와 그 인용 문구(v5.19) | 레일 **넷**도 전압과 함께 MG1(Phase 4)까지 이름집합 해석을 허용했다(`supply_nets`가 없던 기존 4회로용 한시 조항). "
     "옛 원문: \"`supply_nets`가 없는 기존 4개 회로는 **전환기 이름집합 해석**으로 현 코드 이름 집합(정본 표 N3.16, DF-19·DF-26)을 쓴다\", "
     "(ii) \"선언이 없으면 전환기 이름집합 해석이 찾은 레일 수와 실행 spec 레일 전압의 부호\"(이름집합 해석으로 찾은 레일이 정확히 둘이 아니거나 음전위면 거부), "
     "N6.2 6a \"`supply_nets` 미선언 회로는 레일·교류접지 집합이 전환기 이름집합 해석으로 정해져 `agnd`를 레일로 읽지 못하므로 그 회로의 교류접지·셀 분류·구동 종류·stage 경계·"
     "극점 노드·기둥 유도·DEC-65 방향 분류 판정을 무효로 보고한다\", U-26 (b) 같은 취지의 무효 목록(루프 탐지 포함). "
     "넷과 전압을 한 변경 단위(MG1)로 묶어 넷 판정이 U-26 (a)(기존 3회로 `supplies_v` 미확정)에 묶여 있었다. "
     "같이 고친 것: DF-19 비고의 '29개(`sizing_recipe` 15 · `stick_diagram` 10 · `run_harness` 4)'는 옛 review11 줄 스캔이었고 `run_harness` 4는 넷 판정이 아니라 "
     "전압 선언(스칼라 `vdd: 1.8`, MG1 몫)이었다 -- 2026-09-30 AST 전수(H4)가 대체. DF-26 위치 칸의 줄 번호(sizing_recipe 3882~3883, stick_diagram 3147)는 이미 낡아 "
     "이름 상수로 바꿨다. MG1 행의 'DF-19·24·26과 같은 변경 단위' | "
     "2026-10-01 v5.20 -- U-26 (b) 9/9 선언(2026-09-17)으로 전제가 없어졌고 사용자 원칙 '엔진 식은 topology 무관, 이름 기반 `_DEFAULT_RAIL_*`는 정본 아님'(2026-09-30)과 "
     "맞지 않는다. 레일 넷 전환기를 B26-1에서 끝내고(없으면 `load_topology` 거부) DF-19·DF-26 넷 몫을 B26-1~B26-4로 MG1에서 분리, 레일 전압 전환기는 MG1까지 유지. "
     "Phase 3 전이 싼 근거: 편집 파일 2개 대 Phase 3 뒤 6개 모듈, `_RAIL_NETS` 참조 함수가 `cd64170` 10개(P9 병합 뒤 9개)에서 B26-1 뒤 3개(`trace_vdd_to_gnd_branches`·"
     "`trace_gnd_to_vdd_branches`·`propose_theta_kcl_gap_fill`)로 준다. kcl_residual `rail_nets` 키는 조용히 무시하지 않고 B26-1에서 거부(review_b26_1 S5). "
     "card `phase` 값 선례 = DF-35·DF-36 `phase: 2`. 사용자 결정 U2 승인 `20260930-b26-before-phase3` | "
     "계획서 DEC-60·DEC-69·GB0·W0·N3.16·MG1·DF-19·DF-26·N6.1 Phase 4 범위·공격 13·N6.2 6a·U-26 |"),

    ("H4 측정 근거 -- 넷 판정 운영 함수 AST 전수",
     "| `two_stage_ota` 크로스오버: 선언식 36.6 MHz 대 전체 응답 실측 30.50 MHz |",
     "| 넷 판정 운영 함수 AST 전수: `sizing_recipe` 14(+이름 상수 `_DEFAULT_RAIL_HI`·`_DEFAULT_RAIL_LO`) · `stick_diagram` 14(+이름 상수 `_RAIL_NETS`, 예제 데이터 2 제외), "
     "그중 운영 경로 밖 3(`node_pole_estimate`·`find_differential_and_mirror_forks`·`propose_theta_kcl_gap_fill`) / 극성이 필요한 곳 = `trace_vdd_to_gnd_branches`·"
     "`trace_gnd_to_vdd_branches`, 차동·미러 방향 라벨 3함수, `propagate_node_voltages`, `_metric_supply_current`·`_metric_rail_referenced_voltage`·"
     "`_metric_battery_centering_deviation`, MNA 고정 노드(`build_ac_network`·`_full_circuit_response`의 `fixed = {\"gnd\": 0.0}`) | "
     "2026-09-30, 기준 `cd64170`. assets 운영 파일 7개와 `workspaces/run_harness.py`를 AST로 훑음(docstring 제외): 이름 상수 참조, `.rail_nets` 속성, 레일 이름 문자열 리터럴"
     "(`vdd`·`vss`·`gnd`·`avdd`·`avss`·`agnd`·`dvdd`·`dvss`·`vcc`·`vee`, 대소문자). 도달 = 모듈 간 최상위 이름 참조 그래프(`run_harness.run`·`optimize_full_circuit_budget`·"
     "`run_full_circuit_audit_from_topology`에서). N(넷이 레일인가 판정, B26)과 V(스칼라 `spec[\"vdd\"]`, MG1)를 가름 -- `run_harness` 4곳은 V | "
     "오케스트레이터 사전 조사 `prep_b26_supply_nets.md` §1(저장소 밖 초안, 실측 스크립트는 삭제 -- 방법은 이 칸) | 계획서 DF-19·DF-26 |"),

    ("H4 측정 근거 -- 선언 대 이름 집합",
     "| 넷 판정 운영 함수 AST 전수:",
     "| `supply_nets` 9/9 선언, 선언 집합 = 이름 집합 7/9(다른 2 = `pushpull_follower_buffer`·`sf_pushpull_output_opamp`의 `agnd`, 커패시터 단자에만 나옴), "
     "대문자 변형 0, `linked_topology_files` 사용 0 / 엔진이 최상위 `supply_nets`를 읽는 곳 0(metric 선언 안의 같은 이름 키뿐) | "
     "2026-09-30, 기준 `cd64170`. 회로마다 netlist 단자(source/drain/gate/bulk)와 `passive_elements`·`ideal_sources` 단자에 실제로 나오는 넷으로 "
     "`supply_nets`와 stick `_RAIL_NETS`·sizing `_DEFAULT_RAIL_*` 교집합을 대조(`_TEMPLATE`은 선언 없음 -- 작성 틀). 트랜지스터 단자만 보는 집합 판정 사이트는 9회로 모두 결과가 같고 "
     "달라지는 곳은 수동소자 단자까지 보는 MNA 고정 노드(B26-3)뿐 | `prep_b26_supply_nets.md` §2 | 계획서 DEC-60·DF-26 |"),

    ("H4 측정 근거 -- analog-grammar 레일 이름 집합 사용처",
     "| `supply_nets` 9/9 선언, 선언 집합 = 이름 집합 7/9",
     "| stick_diagram이 analog-grammar(`netclass`·`idioms`)를 쓰는 함수 12, 그중 운영 경로 8(`suggest_vertical_stack_composites`·`refine_differential_and_mirror_relations`·"
     "`find_verified_differential_and_mirror_relations`·`propose_device_roles_gap_fill`·`_propose_headroom_roles`·`_propose_vertical_stack_ids`·`find_stack_edges`·"
     "`find_stack_edges` 경유 `geometry_colocation_union`) / 그 12함수가 부르는 analog-grammar 함수 12개가 전부 `RAILS`·`RAILS_POS`·`RAILS_NEG`를 쓴다 / "
     "9회로 `RAILS ∩ 트랜지스터 넷` = `supply_nets ∩ 트랜지스터 넷` 9/9 | 2026-09-30, 기준 `cd64170`. `tools/gates/reachability.build_graph`로 그래프를 만들고 "
     "V7 `before_phase3` 루트에서 도달. 옛 '11(운영 7)'은 직접 import만 센 값 | 오케스트레이터 사전 조사 `prep_b34_b35_grammar.md` §2(저장소 밖 초안) | 계획서 DF-19 비고 |"),

    ("Version History 5.20",
     "| **5.19** | 2026-09-18 |",
     "| **5.20** | 2026-10-01 | **DEC-60 레일 넷 전환기 종료 + DF-19·DF-26 넷 몫을 MG1에서 분리**(사용자 결정 U2 \"승인 (Recommended)\", 승인 기록 `20260930-b26-before-phase3`. "
     "원칙 기본안 -- 사용자 원칙 '엔진 식은 topology 무관', U-26 (b) 9/9 선언 완료). 레일 넷은 `supply_nets`만(없으면 `load_topology` 거부, B26-1 `20260930-b26-rail-accessor-set`), "
     "레일 전압 전환기는 MG1까지 유지. DF-19·DF-26 넷 몫 = B26-1~B26-4(Phase 3 착수 전 가능), 전압 몫 = MG1. DEC-60 (i)은 스펙 선언 회로만, (ii)는 스펙과 무관한 로드 거부. "
     "DF-19 비고를 AST 전수(H4) 정본으로 바꾸고 assets 밖 사이트(`analog-grammar` `netclass.RAILS*`, 백로그 B35)를 추가. N3.16·MG1: kcl_residual `rail_nets`는 B26-1에서 거부, "
     "그 밖의 옛 키 거부 게이트는 MG1. N6.1 Phase 4 범위·공격 13·N6.2 6a·U-26 문구 정정. 판정 표 무변경(`plan_tables_hash` 전후 동일, DF-19·DF-26 `수정 Phase` 괄호 밖 토큰 `4` 그대로). "
     "DEC-60 상태 칸은 B26-1 병합 뒤 고친다 |"),
]


# --------------------------------------------------------------------------------------------- 공통
class PatchError(Exception):
    pass


def _balanced_delta(s):
    return s.count("(") - s.count(")")


def _validate_pair(label, old, new):
    for name, s in (("old", old), ("new", new)):
        if "\n" in s or "\r" in s:
            raise PatchError("%s: %s 글에 줄바꿈" % (label, name))
    if old in new or new in old:
        raise PatchError("%s: 옛 글과 새 글이 서로 부분 문자열이다(멱등 판정 불가)" % label)
    if old.count("|") != new.count("|"):
        raise PatchError("%s: `|` 수가 다르다(%d -> %d)" % (label, old.count("|"), new.count("|")))
    if old.count("`") % 2 != new.count("`") % 2:
        raise PatchError("%s: 백틱 홀짝이 다르다" % label)
    if _balanced_delta(old) != _balanced_delta(new):
        raise PatchError("%s: 괄호 균형이 다르다" % label)


def _detect_eol(text):
    crlf = text.count("\r\n")
    lf = text.count("\n")
    if crlf == lf and crlf > 0:
        return "\r\n"
    if crlf == 0 and lf > 0:
        return "\n"
    raise PatchError("줄 끝이 섞여 있다(CRLF %d, LF %d)" % (crlf, lf))


def _apply_edits(text, edits, what):
    states = []
    for label, old, new in edits:
        _validate_pair(label, old, new)
        n_old, n_new = text.count(old), text.count(new)
        if n_old == 1 and n_new == 0:
            states.append("todo")
        elif n_old == 0 and n_new == 1:
            states.append("done")
        else:
            raise PatchError("%s [%s]: 옛 글 %d회, 새 글 %d회 -- 정확히 하나여야 한다" % (what, label, n_old, n_new))
    if len(set(states)) > 1:
        raise PatchError("%s: 부분 적용 상태(%s) -- 쓰지 않는다" % (what, ", ".join("%s=%s" % (e[0], s) for e, s in zip(edits, states))))
    if states and states[0] == "done":
        return text, False
    for label, old, new in edits:
        text = text.replace(old, new, 1)
    return text, True


def _apply_inserts(text, inserts, eol, what):
    if not inserts:
        return text, False
    states = []
    for label, anchor, line in inserts:
        if "\n" in line or "\r" in line:
            raise PatchError("%s: 삽입 줄에 줄바꿈" % label)
        lines = text.split(eol)
        earlier = [x[2] for x in inserts[:len(states)]]
        n_line = sum(1 for l in lines if l == line)
        n_anchor = sum(1 for l in lines + earlier if l.startswith(anchor))
        anchor_lines = [l for l in lines + earlier if l.startswith(anchor)]
        if anchor_lines and anchor_lines[0].count("|") != line.count("|"):
            raise PatchError("%s [%s]: 삽입 줄 `|` 수 %d가 앵커 줄 %d와 다르다(표 열 수)" % (what, label, line.count("|"), anchor_lines[0].count("|")))
        if n_line == 0 and n_anchor == 1:
            states.append("todo")
        elif n_line == 1:
            states.append("done")
        else:
            raise PatchError("%s [%s]: 삽입 줄 %d회, 앵커 %d회" % (what, label, n_line, n_anchor))
    if len(set(states)) > 1:
        raise PatchError("%s: 부분 적용 상태 -- 쓰지 않는다" % what)
    if states and states[0] == "done":
        return text, False
    for label, anchor, line in inserts:  # 순서대로: 뒤 삽입이 앞 삽입 줄을 앵커로 쓸 수 있다
        lines = text.split(eol)
        idx = [i for i, l in enumerate(lines) if l.startswith(anchor)]
        if len(idx) != 1:
            raise PatchError("%s [%s]: 앵커 %d회" % (what, label, len(idx)))
        lines.insert(idx[0] + 1, line)
        text = eol.join(lines)
    return text, True


def _gate_checks(gate_dir, before, after):
    sys.path.insert(0, os.path.abspath(gate_dir))
    mg = importlib.import_module("merge_gate")
    rp = importlib.import_module("role_paths")
    h0, h1 = mg.plan_tables_hash(before), mg.plan_tables_hash(after)
    print("plan_tables_hash before %s" % h0)
    print("plan_tables_hash after  %s" % h1)
    if h0 != h1:
        raise PatchError("plan_tables_hash가 바뀌었다 -- 이 정정은 판정 표를 바꾸면 안 된다")

    def df_tokens(text):
        header, rows = rp.read_section_table(text, "### N5.2 ")
        ci = [i for i, h in enumerate(header) if h.strip() == "ID"][0]
        cp = [i for i, h in enumerate(header) if h.strip() == "수정 Phase"][0]
        out = {}
        for r in rows:
            if r[ci].strip() in ("DF-19", "DF-26"):
                o, _ = mg.plan_phase_tokens(r[cp])
                out[r[ci].strip()] = sorted(o)
        return out
    t0, t1 = df_tokens(before), df_tokens(after)
    print("N5.2 수정 Phase 괄호 밖 토큰 before %s after %s" % (t0, t1))
    if t0 != t1 or set(t1) != {"DF-19", "DF-26"}:
        raise PatchError("DF-19·DF-26 수정 Phase 토큰이 바뀌었다")
    # 표 모양: 읽기 정본이 정정본을 그대로 읽는다(N4.1·N4.2·N6.1·N3.12.2)
    mg.read_plan_tables_text(after)
    rp.read_write_paths(after)


def _rw(path, edits, inserts, dry, what, gate_dir=None):
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    eol = _detect_eol(text)
    new, ch1 = _apply_edits(text, edits, what)
    new, ch2 = _apply_inserts(new, inserts, eol, what)
    if gate_dir:
        _gate_checks(gate_dir, text, new)
    out = new.encode("utf-8")
    if not (ch1 or ch2):
        if out != raw:
            raise PatchError("%s: already applied인데 바이트가 다르다" % what)
        print("%s: already applied (변경 없음)" % what)
        return
    if _detect_eol(new) != eol:
        raise PatchError("%s: 줄 끝이 바뀌었다" % what)
    if raw.count(b"\n") + len(inserts) * int(ch2) != out.count(b"\n"):
        raise PatchError("%s: 줄 수가 예상과 다르다" % what)
    if dry:
        print("%s: would apply %d edits, %d inserts (dry-run)" % (what, len(edits), len(inserts) if ch2 else 0))
        return
    with open(path, "wb") as fh:
        fh.write(out)
    print("%s: applied %d edits, %d inserts" % (what, len(edits), len(inserts) if ch2 else 0))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--history")
    ap.add_argument("--gate-dir", help="<repo>/tools/gates -- plan_tables_hash 전후 동일 단언")
    ap.add_argument("--dry-run", action="store_true")
    ns = ap.parse_args(argv)
    try:
        _rw(ns.plan, PLAN_EDITS, [], ns.dry_run, "plan", ns.gate_dir)
        if ns.history:
            _rw(ns.history, HIST_EDITS, HIST_INSERTS, ns.dry_run, "history")
    except PatchError as e:
        print("PATCH FAILED: %s" % e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
