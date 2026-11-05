"""memory-guarded foreground runner: g2.py <label> <cwd> <python args...>; waits >=3.7GB (max 8 min), stops the run if <2GB. Writes out2/<label>.log/.meta"""
import ctypes, os, subprocess, sys, time
class M(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong), ("c", ctypes.c_ulonglong), ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
def free():
    m = M(); m.l = ctypes.sizeof(M); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)); return m.ap / 2 ** 30
label, cwd = sys.argv[1:3]; args = sys.argv[3:]
out = "C:/Users/HSLEE/AppData/Local/Temp/la1s_tb1_audit/out2/"
os.makedirs(out, exist_ok=True)
log = open(out + label + ".log", "w", encoding="utf8")
meta = open(out + label + ".meta", "w", encoding="utf8")
t0 = time.time()
while free() < 3.7 and time.time() - t0 < 480:
    meta.write(f"wait free={free():.2f}\n"); meta.flush(); time.sleep(15)
if free() < 3.7:
    meta.write("gave_up_waiting\n"); meta.close(); print("gave_up_waiting", free()); sys.exit(3)
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf8")
start = free(); lo = start; t = time.time()
p = subprocess.Popen([sys.executable] + args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, env=env)
meta.write(f"start free={start:.2f} pid={p.pid}\n"); meta.flush(); stopped = False
while p.poll() is None:
    f = free(); lo = min(lo, f)
    if f < 2.0:
        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True); stopped = True; meta.write(f"STOPPED free={f:.2f}\n"); break
    time.sleep(2)
rc = p.wait()
line = f"rc={rc} start_free={start:.2f} min_free={lo:.2f} secs={time.time() - t:.0f} stopped={stopped}"
meta.write(line + "\n"); meta.close(); print(label, line)
