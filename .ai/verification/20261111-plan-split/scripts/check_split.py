"""분할 검사 -- 분할한 계획서가 원본과 같은 내용인지, 정의(절·결정 행·card 제목)가 plan에 그대로 남았는지.

사용: check_split.py <원본 plan.md(분할 전 사본)> <분할된 plan.md>
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import split_plan as S  # noqa: E402

orig_path, new_path = Path(sys.argv[1]), Path(sys.argv[2])
orig, new = S.read(orig_path), S.read(new_path)
stem = new_path.name[:-len(".plan.md")]
base = new_path.parent / ("%s.parts" % stem)
ok = True


def check(name, cond, detail=""):
    global ok
    ok = ok and cond
    print("%-4s %s %s" % ("PASS" if cond else "FAIL", name, detail))


# 1. 복원 == 원본 (바이트)
back = S.rebuild(new, lambda p: S.read(new_path.parent / p))
check("복원이 원본과 바이트 단위로 같다", back == orig, "(원본 %d B)" % len(orig.encode("utf-8")))

# 2. 표지와 조각 파일이 짝이 맞는다
marks = re.findall(r"<!-- split:(?:section|row)=(\S+) -->", new)
files = sorted(str(p.relative_to(new_path.parent)).replace("\\", "/") for p in base.rglob("*.md") if p.name != "README.md")   # README.md는 조각이 아니라 안내 파일
check("표지 수 == 조각 파일 수", len(marks) == len(files), "(표지 %d, 파일 %d)" % (len(marks), len(files)))
check("표지가 가리키는 파일이 모두 있고 중복이 없다", sorted(marks) == files and len(set(marks)) == len(marks))

# 3. 링크 대상이 있다
links = re.findall(r"\]\((%s\.parts/[^)]+)\)" % re.escape(stem), new)
missing = [l for l in links if not (new_path.parent / l).is_file()]
check("링크 대상이 모두 있다", not missing, "(링크 %d, 없음 %s)" % (len(links), missing[:3]))


# 4. 정의가 plan에 남았다: ## ### 제목, 표 행 첫 칸 ID
def defs(text):
    heads = {h[3] for h in S.sections(text.split("\n"))}
    rows = set(re.findall(r"^\| ([A-Z]+-\d+[a-z]?) \|", text, re.M))
    return heads, rows


oh, orow = defs(orig)
nh, nrow = defs(new)
check("## ### 제목이 모두 plan에 남았다", oh == nh, "(원본 %d, 분할 %d, 빠진 것 %s)" % (len(oh), len(nh), sorted(oh - nh)[:3]))
moved = set()                       # card·archive 조각 안의 표 행은 그 절과 함께 옮겨졌으므로 plan에 없어도 된다
for sub in ("cards", "archive"):
    for f in (base / sub).glob("*.md"):
        moved |= set(re.findall(r"^\| ([A-Z]+-\d+[a-z]?) \|", S.read(f), re.M))
check("표 행 ID(DEC·O 등)가 card·archive 조각 밖에서는 모두 plan에 남았다", (orow - moved) <= nrow and nrow <= orow, "(원본 %d, card·archive 안 %d, 분할 %d, 빠진 것 %s)" % (len(orow), len(moved), len(nrow), sorted((orow - moved) - nrow)[:3]))

# 5. 분할 표 행의 칸 수가 4다
bad = [l[:40] for l in new.split("\n") if "split:row=" in l and "decisions/" in l and l.count(" | ") != 3]
check("요약 행의 표 칸 수 정상", not bad, str(bad[:2]))

# 6. 크기
ob, nb = len(orig.encode("utf-8")), len(new.encode("utf-8"))
pb = sum(p.stat().st_size for p in base.rglob("*.md") if p.name != "README.md")
check("plan 본문 + 조각 합계가 원본 이상(스텁 증분만큼)", nb + pb >= ob, "(plan %d + 조각 %d = %d, 원본 %d)" % (nb, pb, nb + pb, ob))
print("\nplan %d B (%.0f%%), 조각 %d개 %d B, 최대 줄 %d B" % (nb, 100.0 * nb / ob, len(files), pb, max(len(l.encode('utf-8')) for l in new.split("\n"))))
sys.exit(0 if ok else 1)
