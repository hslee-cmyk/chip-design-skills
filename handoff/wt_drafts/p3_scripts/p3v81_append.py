"""v8.1 binary append helper: append UTF-8 text blocks to the end of target files (no rewrite of existing bytes)."""
import sys, pathlib

D = pathlib.Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts")

DESIGN_APPX = """
## 부록 I. 초안 v8 대비 정정(6차 검토 `review6_phase3_v8.md` 반영 -- 대응표는 `phase3_revision_log.md` '초안 v8 → v8.1' 절)

| # | v8 | v8.1 |
|---|---|---|
| 1 | E5 비교 판 B0를 D-28(원칙 기본값)에 두고 "원리상 성립하지 않았다"(N1) | UD-0 '기준에 닿는 기본값' (c)로 옮김(§9.2 UD-0 행, 승인 질문). 기본안 B0 + card 판정 기록 사슬, 대안 = 선례 `20260930-phase2-e4-baseline` 기본안 모양(Phase 2 DoD 대상 커밋과 비교, 의도적으로 바뀐 필드만 계약값으로 따로 판정). 선례와 일치하는 쪽은 대안. D-28 (e)·§10 E5 문장을 'raw 해시 그대로는 성립하지 않는다'로 좁힘 |
| 2 | §10 E2 통과 기준에 `E2 INVALID` 없음 -- D-27 사후 강제가 판정에서 빠짐(N2) | E2 행 맨 앞에 "`E2 INVALID` 줄 없음(B0..HEAD `tools/gates`·`tools/migrate` 무변경 -- D-27)" |
| 3 | A2-③·§8.1 확정 순서에 backfill 결함 card 없음(N3) | 네 card(B34·b26pre·backfill `20261001-b26-backfill-interdig-final-audit`·B26-1), 순서 B34 → b26pre → backfill → B26-1(§8.1 코드 블록·표, §9.1 엔진 선행·재측정 (1), §9.2 A2-③ 행, §11-11, 승인 질문) |
| 4 | §11-11·승인 질문 (4)가 1008~1010행만 인용(N4) | card `phase`가 V1 `--gmid-phase`·`--gmid-strict`를 정한다(`merge_gate.py` 1042행 `strict_set`, 1210~1213행 `v1_command_check(..., phase=card["phase"])` -- gate `master` `0f23786` 재확인), 거부 위험 없음 |
| 5 | minor | m-a D-26 한계에 E3b가 놓치는 세 모양(`sys.modules` 별칭·lambda가 돌려주는 모듈·이름 바꾼 `import_module`, `0f23786` 노출 0건 재확인), m-b D-28에 `e_inst_p3.py` 출처 확인 범위 차이(경로 꼬리 조건·run 전 시점, 스크립트는 바꾸지 않음), m-c revision log의 B26-1 초안 줄 번호 |
"""

LOG = """
---

# 초안 v8 → v8.1 (6차 검토 `review6_phase3_v8.md` 반영, 2026-10-01)

입력: `_drafts/review6_phase3_v8.md`(막는 것 1·고칠 것 3·minor 3, 루프 종료 규칙: v8이 만든 결함과 5차 미해결만). 개정 전 사본: `draft_phase3_design_v8.0.md`, `phase3_approval_question.v8.md`.
모두 문장 수정이다 -- 판정 명령(§10 bash)·spec card(G1·T0·D0a)·문서 개정 문안·`e_inst_p3.py`는 바꾸지 않았다.

| # | 발견 | 대응 |
|---|---|---|
| N1 | E5 비교 판 B0가 선례 `20260930-phase2-e4-baseline`의 고르지 않은 대안과 같은 모양인데 '원칙 기본값'으로 분류 | 승인 질문 UD-0 '기준에 닿는 기본값'에 (c) 추가: 기본안 = B0(M1 base) + Phase 2 DoD와는 card 판정 기록(B34·b26pre·backfill·B26-1)이 잇는다, 대안 = Phase 2 DoD 대상 커밋과 마지막 병합본 비교 + 의도적으로 바뀐 필드(B34·B26-1·backfill)만 그 card 계약값으로 따로 판정. 선례 기록의 사용자 원문 "둘다 기본안으로 진행해"와 선택지 문장("기본안 = da03c0e와 Phase 2 마지막 병합본을 같은 경로에서 비교하고 `topology_ref`만 DF-36 계약값으로 판정, 대안 = card별 판정 기록 사슬로 갈음")을 원문 그대로 인용, 선례와 일치하는 쪽 = 대안이라고 명시. 수정 요청 선택지 예시에 (c), '질문에 넣지 않은 것'의 D-28에서 비교 판 부분 삭제. design: D-28 첫 칸·(e), §10 E5 행 'raw 해시 그대로는 성립하지 않는다'로 좁힘, §9.2 UD-0 행. 어느 쪽을 기본안(Recommended)으로 둘지는 오케스트레이터 몫 -- 문안은 v8 기본안(B0)을 그대로 기본안으로 두고 선례와의 관계를 사실로 적었다 |
| N2 | E2 통과 기준 행에 `E2 INVALID` 없음(fail-open) | §10 E2 행 맨 앞에 "`E2 INVALID` 줄 없음(B0..HEAD `tools/gates`·`tools/migrate` 무변경 -- D-27)" |
| N3 | A2-③·확정 순서에 backfill 결함 card `20261001-b26-backfill-interdig-final-audit`(초안 `phase: 2`) 누락 | 승인 질문 A2-③ 사실 (3)·(가)를 네 card로(backfill은 승인 ③ 대상이 아니라 계획 1001행으로 같은 값이라는 줄), 순서 B34 → b26pre → backfill → B26-1(`b26pre_revision_log.md` m5). design §8.1 머리 문장·코드 블록·표(b26pre·backfill 행 추가), §9.1 엔진 선행·재측정 (1), §9.2 A2-③ 행, §11-11, D-28 (e)·E5의 구간 card 목록 |
| N4 | A2-③ 사실 (4)가 '판정에 영향 없음'으로 읽힘 | (4)와 §11-11에 문장 추가: card `phase`가 이 card들의 V1 `--gmid-phase`·`--gmid-strict`를 정한다. gate `master` `0f23786` `tools/gates/merge_gate.py` 재확인 -- 1042행 `if c["phase"] == card["phase"]: keys |= set(c["activated_ic_case"])`, 1210~1211행 `conftest_has_gmid_phase` → `strict = strict_set(old_view, card)`, 1212~1213행 `v1_command_check(..., strict_needed=strict, phase=card["phase"])`, 1009~1012행 `phase_tok`·`strict_tok` 대조 |
| m-a | E3b가 놓치는 세 모양 | D-26 한계에 `sys.modules` 대입 별칭·lambda가 돌려주는 모듈·이름 바꾼 `import_module` 추가. `0f23786` 추적 `.py`에서 `git grep -E 'sys\\.modules\\[[^]]*stick_diagram|import_module as|from importlib import import_module'` 0건 재확인 |
| m-b | `e_inst_p3.py` 출처 확인 범위(경로 꼬리 조건, run 전 시점) | D-28 첫 칸에 범위 차이 문장(스크립트는 바꾸지 않음 -- 바꾸면 sha256과 F3v8 동등 실측을 다시 재야 한다) |
| m-c | revision log '새로 드러난 것'의 "`draft_b26_1.spec.md` 91행" | 그 줄을 '계약 2(20:04 판 92행, 첫 언급 58행)'로 고침(제자리 수정 -- 이 절 외 유일한 기존 줄 변경) |

## 대상 판 해시(v8.1, sha256 앞 16자리 -- 승인 질문 끝 목록과 같음)

HASHES_PLACEHOLDER
"""


def append(path: pathlib.Path, text: str) -> None:
    before = path.read_bytes()
    data = text.encode("utf-8")
    if not before.endswith(b"\n"):
        data = b"\n" + data
    with open(path, "ab") as f:
        f.write(data)
    after = path.read_bytes()
    assert after[: len(before)] == before, "prefix changed"
    print("appended", path.name, len(before), "->", len(after))


if __name__ == "__main__":
    which = sys.argv[1]
    if which == "design":
        append(D / "draft_phase3_design_v8.md", DESIGN_APPX)
    elif which == "log":
        hashes = sys.argv[2].replace("\\n", "\n")
        append(D / "phase3_revision_log.md", LOG.replace("HASHES_PLACEHOLDER", hashes))
