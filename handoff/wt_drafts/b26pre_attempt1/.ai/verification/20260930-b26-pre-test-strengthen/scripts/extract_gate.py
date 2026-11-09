"""base 판 tools/gates/(redteam/ 밖) blob을 git cat-file로 뽑아 캐시 디렉터리에 쓴다. file_set_sha256 출력."""
import hashlib, os, subprocess, sys
root, rev, dst = sys.argv[1:4]
ls = subprocess.run(["git", "-C", root, "ls-tree", "-r", "--name-only", rev, "tools/gates/"], capture_output=True, check=True).stdout.decode().split("\n")
lines = []
for p in ls:
    if not p or p.startswith("tools/gates/redteam/"):
        continue
    data = subprocess.run(["git", "-C", root, "cat-file", "blob", f"{rev}:{p}"], capture_output=True, check=True).stdout
    rel = p[len("tools/gates/"):]
    out = os.path.join(dst, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    lines.append(f"{rel} {hashlib.sha256(data).hexdigest()}\n")
lines.sort()
print(len(lines), hashlib.sha256("".join(lines).encode()).hexdigest())
