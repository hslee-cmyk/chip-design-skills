# -*- coding: utf-8 -*-
"""계획 이력 문서에 2026-09-30 ~ 10-01 행을 넣는다(history_patch.md 묶음 A + P9·P10 완료 + 결정 A1-a·A1-b(+정정)·A3·B33).

A2(8356c1e)가 이미 넣은 것은 다시 넣지 않는다: H1 둘째 표 'A2 레일 넷 전환기 종료·B26 앞당김(U2)' 행, DEC-60 경위,
H2 'DEC-60 레일 넷 전환기' 행, H4 넷 판정 AST 전수·supply_nets 9/9·analog-grammar 12함수 행.

넣는 자리(문서 형식 = 시간 순, 표 끝에 더함):
  * H1 둘째 표(`| ID | 확정·닫힘 | 사용자 원문·경위 |`): 2026-09-30 행 6개는 A2 행 **앞**(Phase 1 완료 행 뒤),
    2026-10-01 행 7개는 A2 행 **뒤**.
  * H2 첫 표: 'DEC-60 레일 넷 전환기' 행 **뒤**(표 끝)에 DF-36 V3 면제 누수 1행.

사용: python -B patch_history_groupAB.py [--root <저장소 루트>]
- 바이너리 읽기/쓰기, 줄 끝 감지. 기준 줄 머리가 정확히 1번(줄 머리 일치) 있어야 넣는다.
- 넣을 행이 전부 이미 있으면 '이미 적용'(멱등), 일부만 있으면 중단.
"""
import argparse
import os
import sys

REL = "docs/01-plan/features/gain-budget-gmid-sizing.history.md"

A2_ROW_HEAD = "| A2 레일 넷 전환기 종료·B26 앞당김(U2) | 2026-10-01 확정 |"
H2_LAST_ROW_HEAD = "| DEC-60 레일 넷 전환기와 그 인용 문구(v5.19) |"

H1_BEFORE_A2 = [
    "| DF-36 완료 | 2026-09-30 | `20260930-df36-instance-relpath`(red-green): `save_instance_json`의 `topology_ref`를 저장소 루트 기준 `/` 상대 경로로(비공개 헬퍼 `_topology_ref_relpath`, 루트는 `__file__` 유도), 저장소 밖·다른 드라이브 topology는 파일 쓰기 전 `ValueError`. 1차 시도는 V3 FAIL -- 다른 드라이브 분기 변이가 생존(test 공백, 1차 test `2c61257`). 2차는 test에 다른 드라이브 2건 추가(`6444a03`)하고 코드는 1차와 같게(`ed98d35`), 병합 `b29be01`, 판정 `148bd6d`(red 21, 798 passed·15 xfailed, V3 대체 측정 26 중 killed 22·면제 4·생존 0, E-INST·E-LIB·E-LIB-INST 판정값 base와 같음). **재시도 절차 교훈**: 오케스트레이터가 code-author에게 1차 커밋 `git cherry-pick`을 지시했고 EL1이 hook 없는 커밋 생성으로 거부했다(agent의 `git apply` 시도도 거부). 이후 1차 구현 재사용은 `git show`로 읽고 Edit로 옮겨 일반 commit, `git diff <1차> HEAD -- <파일>` 빈 출력 확인으로 지시한다. 면제 4는 뒤에 누수로 판명(H2 'DF-36 V3 면제 4') |",
    "| B28 완료 | 2026-09-30 | 게이트 변경 `20260930-v3-history-clone`(red-green, 승인 `ab90ec5`): V3 사본 = `--head` 격리 복제본(이력 포함, origin 없음), 기준 실행 실패·복제 실패 = `ERROR` exit 2, 임시 복제본 강제 삭제. 원인은 P8 1차 시도에서 드러난 결함 -- `.git` 없는 사본에서 `test_ts6_probe_relocate`의 `git show`가 기준 실행을 실패시켜 변이 2,060개가 전부 '생존'으로 셌다. spec card `d99919c`(design 05 §10 V3 행 ④ 개정), test `b93c1e4`(redteam 공격 31, `rt.py` 선택 키 `tool_tmpdir`·`root_state`), code `dee338d`, 병합 `2b41e79`, 판정 `8790b24`(공격 31 FAIL→PASS, redteam 병합본 PASS 52·SKIPPED 7·FAIL 0, pytest 795 passed·15 xfailed·3 xpassed, DF-36 범위 재실행 killed 22·면제 4·생존 0). 사전 실측: clone 6.5 s·54 MB(copytree 8.9 s·231 MB). 이 card 뒤 V3가 실제로 돌면서 본문 전체 변이 비용이 드러났다(A1-a·A1-b 행) |",
    "| P9 설계 E1 정정 | 2026-09-30 | 사용자 \"E1 문구 정정 승인하고 topology.json주석은 보류해.\" design 20 E1·§6.2·§8 P9 행·196행 정정(`6398a28`): P9는 `kcl_series_union` 본문의 중복 엣지 정의만 정본 `_kcl_and_matching_edges` 호출로, `_metric_kcl_residual`은 P9 대상 아님, 차등 test 경로 `tests/contracts`, 다선형 보간은 DUP 대상 아님. 승인 기록 `20260930-p9-e1-correction`(`ab90ec5`) |",
    "| topology.json 주석 정리 보류 | 2026-09-30 | 같은 답의 뒷부분. `current_reuse_telescopic_ota.topology.json` 1250·1281(`suggest_headroom_stack_groups`)·1872(`_metrics_comment`), `nmcnr_amplifier.topology.json` 74(`slew_rate()`)의 삭제된 이름 안내는 P10 범위 밖 백로그 B29. 고칠 때 승인 기록(쓰기 경로표·U-16), 주석 필드만·connectivity 불변, auditor가 주석 외 필드·E-LIB 동일 확인 |",
    "| Phase 2 DoD D1 -- E4 기준값 정정 | 2026-09-30 | 사용자 \"둘다 기본안으로 진행해\". E4 원문 \"Phase 1 DoD와 같은 값(회로 9/9 로드, instance.json 해시 동일)\"은 Phase 1 기록에 값이 없고 DF-36이 `topology_ref`를 의도 변경해 그대로 잴 수 없었다. 기본안: `da03c0e`(Phase 1 마지막 병합본)와 Phase 2 마지막 병합본을 같은 경로에서 비교 -- E-LIB 9/9 로드·`run_topology_pipeline` 출력 동일, E-INST(파일럿·folded_cascode)는 `topology_ref`를 뺀 해시 동일 + `topology_ref` = DF-36 계약 1 값, `da03c0e` 쪽 하네스는 DF-35 base 모드(경로 리터럴 치환). design 20 §10 E4 정정 `2140da8`, 승인 기록 `20260930-phase2-e4-baseline`(`b7d2570`, target_kind diff) |",
    "| Phase 2 DoD D2 -- 남은 probe | 2026-09-30 | 같은 답. P3c 보류분 `tests/probe_physical_consistency.py`는 추가 card 없이 E2 문구(`tests/probes/**`)대로 판정하고 DoD 기록 '남긴 관찰'에 \"P3c 보류(B21, Phase 4), 스캐너 범위 밖 rail-set 재구현 1건\"을 적는다. 기준 변경 아님(승인 기록 없음) |",
]

H1_AFTER_A2 = [
    "| P9 완료 | 2026-10-01 | `20260930-p9-kcl-edges`(equivalence, 승인 `20260923-20-dead-code-dup-design` + `20260930-p9-e1-correction`): `kcl_series_union` 본문의 엣지 정의를 정본 `_kcl_and_matching_edges` 호출로 통합(경로 압축 제거), 함수·시그니처 유지. spec card·interface card `7535799`. spec card 단계 독립 검토(`review_p9.md`) blocking 1: 경로 압축 줄 삭제가 어떤 test로도 죽지 않는 등가 변이라 V3 FAIL 확정 -- 경로 압축 자체를 지워 대상에서 없앴다. should-fix 4(`Transistor`를 interface card에, 줄 수 판정을 AST `Name` 참조 수 19→18로, V3 실행 조건·timeout 명시, DIFF-DUP 입력 고정) 반영. **2회 시도**: 1차(test `c8d55db`, code `16a71fa`, 병합 `b7765b0`)는 V2 FAIL -- 레지스트리 428행(`trace_vdd_to_gnd_branches`)에 낡은 줄 번호 'SD:1216-1224'가 남아 계약 8(c) 불충족, 판정 기록 미커밋. 2차는 test `6bf510b`(1차와 같은 blob), code `a410f31`(엔진 blob 1차와 같음, 레지스트리 43·308·428·474행만 보완), 병합 `93b18db`, 판정 `766b5c2` -- 엔진·test 트리가 1차 병합본과 같아 V1·V3·DIFF-DUP·E-LIB·E-INST는 1차 측정 재사용(822 passed·15 xfailed, V3 28/28 killed, DIFF-DUP 36/36, E-LIB·E-INST base와 바이트 동일), 레지스트리 계약 8·reg_check·V4~V7은 새로 실행 |",
    "| P10 완료 | 2026-10-01 | `20260930-p10-df23-inventory`(test-only, 승인 `20260923-20-dead-code-dup-design`, 재시도 없음): DF-23 전수 목록 재측정과 참조 문서의 Phase 2 삭제·이동 이름 표시. 문서 커밋 `0fa6ca2`(`df23_inventory.json` measured_at = `766b5c2`, 515항목 = 동작을 정함 213·메시지뿐 302, 생성기 `mk_df23_inventory.py`, 참조 문서 19줄 표시 -- 문서 백로그 B22 (b), design 20 §8 P10 행 정정·P10b 행 추가·§11-1 정정), spec card·interface card `b8d4c4d`, test `56b86c6`(계약 1~4 `test_df23_inventory`, 계약 5 `test_phase2_stale_refs`, 새 test id 49), 판정 `62ae24f`(V1~V7·V10 PASS, V8·V9 N/A; 871 passed·15 xfailed, 계약 7 (a)~(f) 불일치 0, 계약 8 = measured_at 상태에서 새 test 7 failed AssertionError). 레일 넷 이름 리터럴 62항목은 새 DF 없이 DF-19·DF-26에 묶었다(design 20 §11-1). auditor 주: 계약 6의 diff(`766b5c2`..T)에 다른 card 커밋(`fe638ab` E4 정정, `2d58fd8` 승인 기록)이 끼어 이 card `Change-Id` 커밋들의 diff로 읽어 판정했다 -- 교훈: 범위·diff 계약은 이 card `Change-Id` 커밋으로 한정해 적는다 |",
    "| A1-a V3 면제 묶기 | 2026-10-01 | AskUserQuestion 답 \"승인 (Recommended)\". 게이트 변경 `20260930-v3-exempt-binding`(강화): 면제 원소 = `변이 id@함수 원본 해시`(docstring·데코레이터 포함 원본 def의 `ast.dump` sha256), 해시가 같을 때만 적용, 원소 형식 오류 = `malformed`, exempt도 `--out`에 기록, 데코레이터 변이 NOOP 수정(`_replace_def`를 첫 데코레이터 줄부터). 근거 = DF-36 면제 누수(H2 'DF-36 V3 면제 4'). 순서 P9·P10·P10b 뒤, B26-1 전. 승인 기록은 target_kind diff(계획·design 05·design 10·spec card·interface card 문구 커밋)로 받는다 -- 이 행 작성 시점 gate `master`에 기록·card 문서가 아직 없다 |",
    "| A1-b V3 범위 정책 | 2026-10-01 | AskUserQuestion 답 \"② N2 (Recommended)\". `20260930-v3-changed-stmt-scope`: V3 대상 = 바뀐 문장 + 감싸는 제어문 + 삭제 지점 주변 + 새 함수 전체 + 항상 `early_return`, def 머리 변경은 좁은 판 (b)(def 자기 필드 + 바뀐 매개변수를 읽는 문장). 계획 문구 기준 **판정 약화** -- 승인 기록 범위 설명에 \"약화 승인\"을 적는다. 승인 당시 근거 수치 B26-1: 변이 2,472 → 228, 현실 하한 19 h → 0.6 h, 미실행 줄 변이 306 → 6. 놓치는 것: 바뀌지 않은 문장의 기존 test 강도. 승인 기록 `20260930-v3-changed-stmt-scope`(target_kind diff)은 이 행 작성 시점 gate에 없다 |",
    "| A1-b 정정 -- T6 넓힘 | 2026-10-01 | 2차 검토(`review2_v3_cards.md`) 적대 사례 21건 중 N2가 현행보다 더 놓치는 4건, 그중 2건(사례 11·14: 같은 블록·바로 다음이 아닌 문장)이 승인 안내에 없었다. AskUserQuestion 답 \"규칙을 안내에 맞게 넓힘 (Recommended)\" -- T6 = 삭제 지점 바로 뒤 문장 + 바뀐 영역이 바꾸는 이름을 같은 블록 뒤쪽에서 읽는 문장, 반복문 본문이면 위치 무관. 놓치는 것을 승인 때 안내한 대로 ① 다른 블록 ② 두 단계 이상 흐름 ③ 바뀌지 않은 문장의 기존 test 강도로 한정. 재측정: B26-1 228 → 294(현실 하한 0.88 h, 미실행 줄 변이 9) |",
    "| A3 E4 PT 실행 | 2026-10-01 | AskUserQuestion 답 \"phase=2 + dod 실행 (Recommended)\". 드라이런에서 E4가 design 10 §10 PT 정의(`--gmid-phase=1`)를 \"그대로\" 쓰는 것이 Phase 2 DoD와 어긋남을 발견 -- PT를 `--gmid-phase=2`와 `--gmid-dod` 두 실행으로 고정, 같은 커밋에서 스크립트 출처(Phase 2 마지막 병합본 판을 복제본 밖으로 복사해 두 판에 같은 사본)·`python -B -P` 절차 보강. design 20 §10 E4 정정 `fe638ab`, 승인 기록 `20260930-phase2-e4-phase`(target_kind diff, `2d58fd8`). 드라이런 값(증거 아님): E-LIB 해시 동일, E-INST `topology_ref` 제외 두 회로 동일, 두 실행 모두 798 passed·15 xfailed |",
    "| B33 V7 호출 그래프 간선 | 2026-10-01 | AskUserQuestion 답 \"승인 (Recommended)\" -- 게이트 변경 `20260930-v7-registry-edges`: V7 `reachability.py` 정적 호출 그래프가 ① 레지스트리 dict·클래스 생성자 경유 호출을 못 봐 실사용 함수를 미도달로 세고 ② test 파일의 같은 이름 함수로 간선이 새던(`size_transistor` 거짓 도달) 것을 고친다. 질문에 적은 효과: 미도달 115 → 39, V3 인벤토리 1.31배(레지스트리 경유 metric의 거짓 FAIL 제거), 독립 검토(`review_b33.md`) 구멍 3건(`super().__init__` 누수, 그래프 밖 재수출, 문자열·속성만으로 레지스트리 도달)을 막은 판, 과거 판정 기록 27건의 V7 판정 불변. 순서는 Phase 3 G1보다 먼저. 같은 날 Q1 \"(a) 호출 위치만 (Recommended)\": 생성자 간선은 `Cls(...)`·`raise Cls`에서만(isinstance·except 이름 참조 제외), 팩토리 모양(`defaultdict(Cls)`)의 거짓 FAIL은 면제 승인으로 처리. 승인 기록 `20260930-v7-registry-edges`(target_kind diff: spec card·interface card·design 05 V7 행)는 이 행 작성 시점 gate에 없다 |",
]

H2_AFTER_LAST = [
    "| **DF-36 V3 면제 4**(판정 `148bd6d`, B28 재실행 `8790b24`도 같음) | 면제 4개는 C8 승인 `20260922-ic3-v3-exempt`의 변이 id였다. 그 승인은 옛 `save_instance_json`(def 해시 `9cb09766…`)에 대해 받은 것인데 DF-36이 함수를 바꾼 뒤(`11a55c19…`) 같은 id가 그대로 적용됐다 -- 면제 원소가 id뿐이라 함수가 바뀌어도 승인이 따라왔다(승인 범위 밖 누수). auditor는 4개가 같은 문장을 가리키는지 손으로 확인했지만 승인 범위로 보면 V3 PASS는 누수에 기댄 판정이다. 자동 번복 경로는 없다(`integrity.py` 행 3(나) 재판정은 `merge_gate.py`만 돌리고 V3를 부르지 않는다) | 2026-10-01 사용자 결정 A1-a(H1) -- 게이트 변경 `20260930-v3-exempt-binding`(면제 = id@원본 def 해시). 필요하면 4개를 실제로 돌려 DF-36 V3를 다시 잰다(백로그) | 계획 N4.2 V3 행, design 05 §10 V3 |",
]


def _find_line(data, head, eol):
    """줄 머리가 head인 줄의 (시작, 끝(줄 끝 포함)) -- 정확히 1개여야 한다."""
    hb = head.encode("utf-8")
    hits = []
    pos = 0
    for line in data.split(eol):
        if line.startswith(hb):
            hits.append((pos, pos + len(line) + len(eol)))
        pos += len(line) + len(eol)
    if len(hits) != 1:
        raise SystemExit("중단: 기준 줄 '%s' %d회(기대 1)" % (head, len(hits)))
    return hits[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills")
    ns = ap.parse_args()
    path = os.path.join(ns.root, *REL.split("/"))
    with open(path, "rb") as f:
        data = f.read()
    eol = b"\r\n" if b"\r\n" in data else b"\n"
    rows = H1_BEFORE_A2 + H1_AFTER_A2 + H2_AFTER_LAST
    for r in rows:
        assert r.startswith("| ") and r.endswith(" |"), r[:40]
        # 셀 안에 '|'가 없다: H1 표 3열(파이프 4개), H2 표 4열(파이프 5개)
        assert r.count("|") == (5 if r in H2_AFTER_LAST else 4), ("열 수 불일치", r[:40])
    present = [r.encode("utf-8") in data for r in rows]
    if all(present):
        print("이미 적용: " + REL)
        return 0
    if any(present):
        print("중단: 넣을 행 %d/%d개만 이미 있다 -- 수동 확인 필요" % (sum(present), len(rows)))
        return 1
    enc = lambda lines: b"".join(x.encode("utf-8") + eol for x in lines)
    a2_s, a2_e = _find_line(data, A2_ROW_HEAD, eol)
    h2_s, h2_e = _find_line(data, H2_LAST_ROW_HEAD, eol)
    assert a2_e <= h2_s, "A2 행이 H2 행보다 뒤에 있다"
    out = (data[:a2_s] + enc(H1_BEFORE_A2) + data[a2_s:a2_e] + enc(H1_AFTER_A2)
           + data[a2_e:h2_e] + enc(H2_AFTER_LAST) + data[h2_e:])
    # 기존 바이트는 그대로(넣은 블록만 차이), 줄 끝 수 일치
    assert out.replace(enc(H1_BEFORE_A2), b"", 1).replace(enc(H1_AFTER_A2), b"", 1).replace(enc(H2_AFTER_LAST), b"", 1) == data
    assert out.count(b"\n") == data.count(b"\n") + len(rows)
    assert out.count(b"\r\n") == data.count(b"\r\n") + (len(rows) if eol == b"\r\n" else 0)
    with open(path, "wb") as f:
        f.write(out)
    print("적용: %s (+%d줄: H1 %d+%d, H2 %d)" % (REL, len(rows), len(H1_BEFORE_A2), len(H1_AFTER_A2), len(H2_AFTER_LAST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
