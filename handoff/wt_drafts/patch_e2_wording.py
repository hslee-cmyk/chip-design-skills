"""design 20 §10 E2 기준 문구 정정(사용자 2026-10-01 Q-P2DOD-E2 "문구 정정 (Recommended)").
사용: python -B patch_e2_wording.py <repo root> [--check]
바이트 단위로 한 줄만 바꾼다(줄 끝 보존). 이미 적용됐으면 already-applied.
"""
import sys, pathlib

REL = "docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md"
OLD = ("| E2 | probe 엔진 식 재구현 0 | `$PY <iso>/skills/analog-gmid-design/assets/tests/tools/engine_dup_scan.py --root <iso>` "
       "| exit 0, 발견 0 |")
NEW = ("| E2 | probe 엔진 식 재구현 0 | `$PY <iso>/skills/analog-gmid-design/assets/tests/tools/engine_dup_scan.py --root <iso>` "
       "| exit 0, 면제되지 않은 발견 0(면제 = `target_kind: decision` 승인 기록이 적은 `<path>::<rule>`로 스캐너가 `\"exempt\": true`를 붙인 발견 -- "
       "현재 승인 `20260929-p4-scan-exempt` 1건; 면제 발견은 DoD 기록에 path·line·rule·승인 id로 적는다) |")


def main(argv):
    root = pathlib.Path(argv[1])
    check = "--check" in argv
    p = root / REL
    b = p.read_bytes()
    old, new = OLD.encode("utf-8"), NEW.encode("utf-8")
    if b.count(new) == 1 and b.count(old) == 0:
        print("already-applied")
        return 0
    if b.count(old) != 1:
        print("OLD 줄이 정확히 하나가 아니다: %d" % b.count(old))
        return 1
    if check:
        print("pending")
        return 0
    p.write_bytes(b.replace(old, new, 1))
    print("applied")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
