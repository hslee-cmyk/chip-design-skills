"""B34(20260930-b34-grammar-explicit) 오케스트레이터 문서 커밋 초안 -- references/analog-grammar-integration.md의
'analog-grammar 부재 -> 조용히 None 폴백' 서술을 'ImportError'로 고친다(spec card '작성 전 실측' 7, 승인 20260930-b26-before-phase3 '덮는 것' ③ B34).

  C:/Python314/python.exe -B patch_b34_refs.py --root <저장소 루트> [--check]

* gate 소자 없음 경로(`if not devs: return None`, 문서 110~111·201~202행)는 고치지 않는다(card 범위 4 -- 그 경로는 남는다).
* 앵커는 문자열 전체 일치(각 정확히 1회, `except ImportError` 쌍만 2회). 이미 적용된 상태면 'already-applied', 앵커가 하나라도 없으면 exit 2(무쓰기).
* blob은 LF·UTF-8(BOM 없음, 측정 0f23786). 작업 사본이 autocrlf로 CRLF면 LF로 맞춰 대조하고 같은 줄 끝으로 되써서 blob은 LF로 남는다.
출력: pending N / applied / already-applied. --check는 쓰지 않는다.
"""
import argparse
import os
import sys

REL = "skills/analog-gmid-design/references/analog-grammar-integration.md"

PAIRS = [
    # 95~98 (설계안 classify_device_roles docstring)
    ("""    device role을 배정한다. analog-grammar가 sys.path에 없으면(다른 skill이라 설치
    여부가 이 스크립트 실행 환경에 좌우됨) None을 반환한다 — 호출자는 None이면 이
    보강 기능 없이 기존 동작(role=None)으로 폴백해야 한다. 절대 예외를 삼키고 조용히
    "판정 없음"으로 넘어가지 않는다 — ImportError만 잡고 다른 예외는 그대로 던진다.\"\"\"""",
     """    device role을 배정한다. analog-grammar를 import하지 못하면(설치 안 됨·경로 다름) skill
    이름 `analog-grammar`와 탐색 경로를 적은 `ImportError`를 원래 예외에 이어(`from`) 던진다
    (B34 -- 예전의 'None 반환 후 기존 동작으로 폴백'은 사이징 입력을 조용히 바꿔서 없앴다).
    gate가 있는 소자가 없는 입력만 None이다.\"\"\"""", 1),
    # 106~107, 197~198 (설계안 코드 블록 두 곳)
    ("""    except ImportError:
        return None
""",
     """    except ImportError as e:
        raise ImportError(f"analog-grammar skill을 import할 수 없다(탐색 경로 {_ag_path})") from e
""", 2),
    # 118~119
    ("""의존한다 — 저장소 밖에서 `analog-gmid-design/assets`만 따로 복사해 쓰는 경우엔
자동으로 `None`이 되어 조용히 하위호환 경로로 빠진다(의도된 동작).""",
     """의존한다 — 저장소 밖에서 `analog-gmid-design/assets`만 따로 복사해 쓰는 경우엔
skill 이름과 탐색 경로를 적은 `ImportError`로 멈춘다(B34 -- 예전에는 조용히 `None`이 되어
하위호환 경로로 빠졌다). 설치본에서는 `install.py`가 `analog-grammar`도 함께 설치해야 한다.""", 1),
    # 186~188 (설계안 find_idiom_matches docstring 끝)
    ("""    두 쌍(M1a/M1b, M4a/M4b)이지 4소자 뭉치가 아니다. analog-grammar가 sys.path에
    없으면 None(호출자는 find_matching_candidates(transistors, idiom_matches=None)으로
    폴백).\"\"\"""",
     """    두 쌍(M1a/M1b, M4a/M4b)이지 4소자 뭉치가 아니다. analog-grammar를 import하지
    못하면 `ImportError`(B34). gate가 있는 소자가 없는 입력이면 None(호출자는
    find_matching_candidates(transistors, idiom_matches=None)으로 폴백).\"\"\"""", 1),
    # 440~443 (test 계획 4)
    ("""4. **analog-grammar 부재 시 폴백**: `sys.path`에서 `analog-grammar/assets`를 일부러
   빼고 `find_idiom_matches()`가 `None`을 반환하는지, 그 `None`을 그대로
   `find_matching_candidates(transistors, idiom_matches=None)`에 넘겼을 때 기존
   동작과 동일한지 확인.""",
     """4. **analog-grammar 부재 시 `ImportError`**(B34가 옛 '부재 시 None 폴백' 계획을 대체): `sys.modules`에
   `netclass`·`idioms`를 `None`으로 두어 부재를 흉내 내고, 공개 진입점이 skill 이름 `analog-grammar`·
   탐색 경로·원래 예외(`__cause__`)를 담은 `ImportError`를 내는지 확인(spec card
   `20260930-b34-grammar-explicit` 계약 1~3).""", 1),
]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--check", action="store_true")
    ns = ap.parse_args(argv)
    p = os.path.join(ns.root, *REL.split("/"))
    raw = open(p, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):
        print("BOM이 있다 -- 앵커 기준이 아니다", file=sys.stderr)
        return 2
    crlf = b"\r\n" in raw
    if crlf and raw.count(b"\r\n") != raw.count(b"\n"):
        print("줄 끝이 섞여 있다(CRLF·LF) -- 무쓰기", file=sys.stderr)
        return 2
    t = raw.decode("utf-8").replace("\r\n", "\n")   # 작업 사본이 autocrlf(CRLF)면 LF로 맞춰 대조하고 쓸 때 되돌린다
    pending, done, bad = 0, 0, []
    for old, new, n in PAIRS:
        co, cn = t.count(old), t.count(new)
        if co == n and cn == 0:
            pending += 1
        elif co == 0 and cn == n:
            done += 1
        else:
            bad.append((old.splitlines()[0][:60], co, cn))
    if bad:
        print("앵커 불일치(무쓰기): %r" % bad, file=sys.stderr)
        return 2
    if pending == 0:
        print("already-applied")
        return 0
    if done:
        print("부분 적용 상태(pending %d, done %d) -- 무쓰기" % (pending, done), file=sys.stderr)
        return 2
    if ns.check:
        print("pending %d" % pending)
        return 0
    for old, new, n in PAIRS:
        t = t.replace(old, new)
    with open(p, "wb") as fh:
        fh.write((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
    print("applied")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
