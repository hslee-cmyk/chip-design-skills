"""순서 7 산출물을 audit worktree 판정 기록 폴더로 복사한다(instance.json 사본은 해시만 남기고 복사하지 않는다)."""
import hashlib, os, shutil
D = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b34-grammar-explicit-audit/.ai/verification/20260930-b34-grammar-explicit"
O = "C:/g299/out"
os.makedirs(D + "/order7/einst", exist_ok=True)
for f in sorted(os.listdir(O)):
    p = os.path.join(O, f)
    if os.path.isfile(p):
        shutil.copyfile(p, D + "/order7/" + f)
for f in sorted(os.listdir(O + "/einst")):
    p = O + "/einst/" + f
    if f.endswith(".instance.json"):
        print("instance", f, hashlib.sha256(open(p, "rb").read()).hexdigest())
        continue
    shutil.copyfile(p, D + "/order7/einst/" + f)
for f in ("run_m.sh", "red_green_m.py", "c7_run.sh", "einst.sh", "e_lib.py", "e_inst_df36.py", "install_probe.py", "copy_out.py"):
    shutil.copyfile("C:/g299/scripts/" + f, D + "/scripts/" + f)
print(sorted(os.listdir(D + "/order7")))
