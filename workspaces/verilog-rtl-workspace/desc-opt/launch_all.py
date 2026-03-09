import subprocess, sys, os

BASE = "C:/Users/HSLEE/.claude/skills"
SKILL_CREATOR = f"{BASE}/skill-creator"
MODEL = "claude-sonnet-4-6"

skills = [
    ("verilog-rtl",       f"{BASE}/verilog-rtl-workspace/desc-opt"),
    ("verilog-a",         f"{BASE}/verilog-a-workspace/desc-opt"),
    ("lattice-fpga",      f"{BASE}/lattice-fpga-workspace/desc-opt"),
    ("uvm-verification",  f"{BASE}/uvm-verification-workspace/desc-opt"),
    ("chip-verification", f"{BASE}/chip-verification-workspace/desc-opt"),
]

procs = []
for skill_name, ws in skills:
    eval_set = f"{ws}/trigger-eval.json"
    skill_path = f"{BASE}/{skill_name}"
    log_file = open(f"{ws}/run_loop.log", "w", encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    p = subprocess.Popen(
        [sys.executable, "-m", "scripts.run_loop",
         "--eval-set", eval_set,
         "--skill-path", skill_path,
         "--model", MODEL,
         "--max-iterations", "5",
         "--verbose"],
        cwd=SKILL_CREATOR,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env
    )
    print(f"Started {skill_name}: PID={p.pid}")
    procs.append((skill_name, p, log_file))

print("\nWaiting for all to complete...")
for skill_name, p, log_file in procs:
    p.wait()
    log_file.close()
    print(f"{skill_name}: exit code {p.returncode}")

print("\nAll done!")
