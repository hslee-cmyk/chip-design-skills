"""b26pre 준비: b26_scripts 사본(C:/g83 -> C:/g87 치환)과 C:/g87/base(= git archive HEAD), C:/g87/b1(base 사본).
mk_b1.py는 따로 실행한다."""
import io, os, shutil, subprocess, tarfile

D = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/"
REPO = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
SRC, DST = D + "b26_scripts/", D + "b26pre_scripts/"
for fn in os.listdir(SRC):
    if fn.endswith(".py"):
        t = open(SRC + fn, encoding="utf-8").read().replace("C:/g83", "C:/g87").replace("_drafts/b26_scripts", "_drafts/b26pre_scripts")
        with open(DST + fn, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(t)
os.makedirs("C:/g87/out", exist_ok=True)
if not os.path.exists("C:/g87/base"):
    data = subprocess.run(["git", "-C", REPO, "archive", "HEAD"], capture_output=True, check=True).stdout
    tarfile.open(fileobj=io.BytesIO(data)).extractall("C:/g87/base", filter="data")
if not os.path.exists("C:/g87/b1"):
    shutil.copytree("C:/g87/base", "C:/g87/b1")
print("ok", sorted(os.listdir(DST)))
