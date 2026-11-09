"""b26_reconcile 준비: b26_scripts 사본(C:/g83 -> C:/g103), 시제품 test 2종 복사,
C:/g103/base(= git archive HEAD), C:/g103/b1(base 사본; mk_b1.py로 B34 적용은 따로), out에 junit/실행 줄 기록 복사."""
import io, os, shutil, subprocess, tarfile

D = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/"
REPO = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
SRC, DST = D + "b26_scripts/", D + "b26_reconcile/"
for fn in os.listdir(SRC):
    if fn.endswith(".py"):
        t = open(SRC + fn, encoding="utf-8").read().replace("C:/g83", "C:/g103").replace("_drafts/b26_scripts", "_drafts/b26_reconcile")
        with open(DST + fn, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(t)
shutil.copyfile(D + "b26pre_scripts/proto_test_b26pre_card.py", DST + "proto_test_b26pre_card.py")
os.makedirs("C:/g103/out", exist_ok=True)
for f in ("junit_base.xml", "executed_lines.json"):
    shutil.copyfile(D + "v3_scripts/out/" + f, "C:/g103/out/" + f)
if not os.path.exists("C:/g103/base"):
    data = subprocess.run(["git", "-C", REPO, "archive", "HEAD"], capture_output=True, check=True).stdout
    tarfile.open(fileobj=io.BytesIO(data)).extractall("C:/g103/base", filter="data")
if not os.path.exists("C:/g103/b1"):
    shutil.copytree("C:/g103/base", "C:/g103/b1")
print("ok", sorted(os.listdir(DST)))
