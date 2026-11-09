# -*- coding: utf-8 -*-
"""design 20-dead-code-dup §10 E4 PT phase 정정 패치 (승인 후보 20260930-phase2-e4-phase).

사용: C:/Python314/python.exe -B patch_e4_phase.py <design 20 파일 경로>

- 바이너리로 읽고 쓴다(줄 끝 바이트 보존: 바꾸는 것은 줄 내용뿐, 줄 끝 문자는 건드리지 않는다).
- 바꿀 문장 2개(§10 머리 문장, E4 행)는 각각 파일 안에서 정확히 1번 나와야 한다(아니면 중단, 쓰기 없음).
- 멱등: 새 문장이 이미 각각 1번 있고 옛 문장이 0번이면 아무것도 쓰지 않고 exit 0.
- 일부만 적용된 상태(옛 1 + 새 1 등)는 중단(exit 2).
"""
import hashlib
import sys

# ---------------------------------------------------------------- §10 머리 문장
OLD_HEAD = (
    "auditor가 Phase 2 마지막 card 병합본의 격리 복제본 `<iso>`에서 실행한다. "
    "`PT`는 `10-test-separation` §10 정의를 그대로 쓴다."
)
NEW_HEAD = (
    "auditor가 Phase 2 마지막 card 병합본의 격리 복제본 `<iso>`에서 실행한다. "
    "`PT`는 `10-test-separation` §10 정의를 그대로 쓴다. "
    "단 E4는 그 정의에서 `--gmid-phase=1`만 `--gmid-phase=2`로 바꾼 `PT2`로 실행한다"
    "(E4 행, 2026-10-01 정정, 승인 `20260930-phase2-e4-phase`)."
)

# ---------------------------------------------------------------- E4 행 (2140da8 정정본)
OLD_E4 = (
    "| E4 | 동작 보존 | `PT` 전체. 그리고 **같은 격리 복제본 `<iso>`(같은 체크아웃 경로)** 에서 "
    "`git -C <iso> checkout --detach da03c0e`(Phase 1 DoD 대상 커밋, `phase1-dod.md` 3행) 판과 "
    "Phase 2 마지막 card 병합본 판을 차례로 떠 E-LIB·E-INST를 잰다(판을 바꿀 때마다 "
    "`git -C <iso> checkout -- workspaces`·`git -C <iso> clean -fdx` 로 산출을 지운다). "
    "E-LIB = `.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py <iso> <out>`(두 판 같은 스크립트). "
    "E-INST(회로 `current_reuse_telescopic_ota`·`folded_cascode`) = da03c0e 판은 "
    "`.ai/verification/20260930-df35-harness-paths/scripts/e_inst_df35.py <iso> <회로> base <out>`"
    "(하네스의 메인 체크아웃 경로 리터럴 ASSETS 2·WORKSPACES 1개를 같은 표기의 `<iso>` 경로로 치환), "
    "병합본 판은 `.ai/verification/20260930-df36-instance-relpath/scripts/e_inst_df36.py <iso> <회로> <out>`"
    "(치환 없음, 리터럴 0개 요구) | "
    "`PT` 실패 0(수집 수는 Phase 1과 다르므로 비교하지 않는다). "
    "E-LIB: 두 판 모두 library 9/9 로드(`_TEMPLATE` 제외), `e_lib.py` 결과 해시(`hash`)가 두 판에서 같다. "
    "E-INST: 두 회로 모두 (a) `without_topology_ref_sha256`(`topology_ref`를 뺀 instance.json의 키 정렬 compact JSON sha256)이 "
    "두 판에서 같다 (b) 병합본 판 `topology_ref` = DF-36 계약 1 기대값 "
    "`skills/analog-gmid-design/assets/library/<topology 파일>`(`topology_ref_equals_expected_contract1` true), "
    "경로 문자열 잎 0 (c) da03c0e 판 `topology_ref`는 `<iso>`의 ASSETS 경로와 `library/<topology 파일>`을 이은 절대 경로"
    "(`topology_ref_is_join_of_ASSETS_DIR` true -- 같은 파일). "
    "(2026-09-30 정정, 승인 `20260930-phase2-e4-baseline`: 옛 기준 'Phase 1 DoD와 같은 값(회로 9/9 로드, instance.json 해시 동일)'은 "
    "(1) Phase 1 DoD 기록에 E-LIB·E-INST 값이 없고 (2) DF-36(`20260930-df36-instance-relpath`, red-green)이 "
    "`topology_ref`를 절대 경로에서 저장소 상대 경로로 의도적으로 바꿔 raw 해시 동일이 원리상 성립하지 않아 잴 수 없었다. "
    "비교 기준을 Phase 1 DoD 대상 커밋 da03c0e의 같은 경로 실측으로 바꾸고, 의도적으로 바뀐 `topology_ref` 하나만 "
    "DF-36 계약값으로 따로 판정한다) |"
)
NEW_E4 = (
    "| E4 | 동작 보존 | `PT2` 전체와 `PT2 --gmid-dod` 전체, 두 실행"
    "(`PT2` = `10-test-separation` §10 `PT` 정의에서 `--gmid-phase=1`만 `--gmid-phase=2`로 바꾼 것). "
    "그리고 **같은 격리 복제본 `<iso>`(같은 체크아웃 경로)** 에서 "
    "`git -C <iso> checkout --detach da03c0e`(Phase 1 DoD 대상 커밋, `phase1-dod.md` 3행) 판과 "
    "Phase 2 마지막 card 병합본 판을 차례로 떠 E-LIB·E-INST를 잰다(판을 바꿀 때마다 "
    "`git -C <iso> checkout -- workspaces`·`git -C <iso> clean -fdx` 로 산출을 지운다). "
    "스크립트 출처: 아래 세 스크립트는 da03c0e 판에 없으므로, 판을 바꾸기 전에 Phase 2 마지막 card 병합본 판의 "
    "`<iso>/.ai/verification/…`에서 `<iso>` 밖 임시 경로로 복사해(sha256 기록) 두 판에 같은 사본을 쓴다. "
    "`<out>`도 `<iso>` 밖이다(`git clean -fdx`가 복제본 안 산출을 지운다). "
    "실행은 `$PY -B -P <사본> …`이다. "
    "E-LIB = `.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py <iso> <out>`(두 판 같은 사본). "
    "E-INST(회로 `current_reuse_telescopic_ota`·`folded_cascode`) = da03c0e 판은 "
    "`.ai/verification/20260930-df35-harness-paths/scripts/e_inst_df35.py <iso> <회로> base <out>`"
    "(하네스의 메인 체크아웃 경로 리터럴 ASSETS 2·WORKSPACES 1개를 같은 표기의 `<iso>` 경로로 치환), "
    "병합본 판은 `.ai/verification/20260930-df36-instance-relpath/scripts/e_inst_df36.py <iso> <회로> <out>`"
    "(치환 없음, 리터럴 0개 요구) | "
    "`PT2`와 `PT2 --gmid-dod` 두 실행 모두 실패 0(수집 수는 Phase 1과 다르므로 비교하지 않는다). "
    "E-LIB: 두 판 모두 library 9/9 로드(`_TEMPLATE` 제외), `e_lib.py` 결과 해시(`hash`)가 두 판에서 같다. "
    "E-INST: 두 회로 모두 (a) `without_topology_ref_sha256`(`topology_ref`를 뺀 instance.json의 키 정렬 compact JSON sha256)이 "
    "두 판에서 같다 (b) 병합본 판 `topology_ref` = DF-36 계약 1 기대값 "
    "`skills/analog-gmid-design/assets/library/<topology 파일>`(`topology_ref_equals_expected_contract1` true), "
    "경로 문자열 잎 0 (c) da03c0e 판 `topology_ref`는 `<iso>`의 ASSETS 경로와 `library/<topology 파일>`을 이은 절대 경로"
    "(`topology_ref_is_join_of_ASSETS_DIR` true -- 같은 파일). "
    "(2026-09-30 정정, 승인 `20260930-phase2-e4-baseline`: 옛 기준 'Phase 1 DoD와 같은 값(회로 9/9 로드, instance.json 해시 동일)'은 "
    "(1) Phase 1 DoD 기록에 E-LIB·E-INST 값이 없고 (2) DF-36(`20260930-df36-instance-relpath`, red-green)이 "
    "`topology_ref`를 절대 경로에서 저장소 상대 경로로 의도적으로 바꿔 raw 해시 동일이 원리상 성립하지 않아 잴 수 없었다. "
    "비교 기준을 Phase 1 DoD 대상 커밋 da03c0e의 같은 경로 실측으로 바꾸고, 의도적으로 바뀐 `topology_ref` 하나만 "
    "DF-36 계약값으로 따로 판정한다) "
    "(2026-10-01 정정, 승인 `20260930-phase2-e4-phase`: 옛 명령 '`PT` 전체'는 §10 머리에 따라 10 §10의 Phase 1 DoD용 "
    "`--gmid-phase=1`로 돌아 Phase 2 DoD 검사가 아니었고(phase 값에 따라 xfail 조건·엄격 집합이 다르다), "
    "Phase 2 DoD 브리핑의 `--gmid-dod` 실행이 설계서에 없었다. `PT2`(`--gmid-phase=2`) 실행과 `PT2 --gmid-dod` 실행 "
    "두 개로 고정한다. 같은 정정에서 절차를 명확히 했다(기준 변경 아님): 세 스크립트는 da03c0e 판에 없어 병합본 판에서 "
    "`<iso>` 밖으로 복사한 같은 사본을 두 판에 쓰고, `<out>`은 `<iso>` 밖, 인터프리터 옵션은 `-B -P`) |"
)

PAIRS = (("§10 머리", OLD_HEAD, NEW_HEAD), ("E4 행", OLD_E4, NEW_E4))


def _count_lines(data: bytes, needle: bytes) -> int:
    """needle이 '줄 내용 전체'로 나오는 횟수(줄 끝 \\r\\n·\\n 어느 쪽이든)."""
    n = 0
    for raw in data.split(b"\n"):
        if raw.endswith(b"\r"):
            raw = raw[:-1]
        if raw == needle:
            n += 1
    return n


def main(argv):
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if len(argv) != 2:
        print("사용: patch_e4_phase.py <design 20 파일>", file=sys.stderr)
        return 64
    path = argv[1]
    with open(path, "rb") as fh:
        data = fh.read()
    before = hashlib.sha256(data).hexdigest()

    state = []
    for name, old, new in PAIRS:
        ob, nb = old.encode("utf-8"), new.encode("utf-8")
        # 줄 전체 일치 횟수와 부분 문자열 횟수를 둘 다 본다(부분 일치가 다른 곳에 숨어 있으면 중단).
        oc, nc = _count_lines(data, ob), _count_lines(data, nb)
        osub, nsub = data.count(ob), data.count(nb)
        if nb.startswith(ob):  # 새 문장이 옛 문장을 접두로 포함하는 경우(§10 머리) 부분 횟수 보정
            osub -= nsub
        state.append((name, ob, nb, oc, nc, osub, nsub))
        print("%s: 옛 줄 %d(부분 %d) / 새 줄 %d(부분 %d)" % (name, oc, osub, nc, nsub))

    if all(oc == 0 and nc == 1 and osub == 0 and nsub == 1 for _, _, _, oc, nc, osub, nsub in state):
        print("이미 적용됨 -- 쓰기 없음. sha256 %s" % before)
        return 0
    for name, _, _, oc, nc, osub, nsub in state:
        if not (oc == 1 and osub == 1 and nc == 0 and nsub == 0):
            print("중단: %s 상태가 '옛 1·새 0'이 아니다 -- 쓰기 없음" % name, file=sys.stderr)
            return 2

    out_lines = []
    for raw in data.split(b"\n"):
        cr = raw.endswith(b"\r")
        body = raw[:-1] if cr else raw
        for _, ob, nb, *_ in state:
            if body == ob:
                body = nb
                break
        out_lines.append(body + (b"\r" if cr else b""))
    out = b"\n".join(out_lines)

    # 사후 확인: 줄 수·줄 끝 종류 불변, 바뀐 줄은 정확히 2개
    assert out.count(b"\n") == data.count(b"\n")
    assert out.count(b"\r\n") == data.count(b"\r\n")
    a, b = data.split(b"\n"), out.split(b"\n")
    assert sum(1 for x, y in zip(a, b) if x != y) == len(PAIRS)
    for _, ob, nb, *_ in state:
        assert _count_lines(out, nb) == 1 and _count_lines(out, ob) == 0

    with open(path, "wb") as fh:
        fh.write(out)
    print("적용함. sha256 %s -> %s" % (before, hashlib.sha256(out).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
