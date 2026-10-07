"""base 엔진 사본에서 지정한 줄(1-based)만 지운 변형을 만든다. 줄 글이 기대와 다르면 멈춘다."""
import sys
path = sys.argv[1]
lines_to_del = [int(x) for x in sys.argv[2].split(",")]
with open(path, "rb") as fh:
    data = fh.read()
lines = data.split(b"\n")
for n in lines_to_del:
    s = lines[n - 1].strip()
    if s not in (b"_backfill_interdig_ok(result)", b"_backfill_interdig_ok(fixed_audit)"):
        raise SystemExit("unexpected line %d: %r" % (n, s))
    print("delete %d: %r" % (n, lines[n - 1]))
for n in sorted(lines_to_del, reverse=True):
    del lines[n - 1]
with open(path, "wb") as fh:
    fh.write(b"\n".join(lines))
