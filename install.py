"""
Install chip-design skills + agents + agent-kit to ~/.claude/

    python install.py            # install everything
    python install.py --dry-run  # preview
    python install.py --only agents   # one component: skills | agents | kit
"""
import shutil, pathlib, argparse, sys

HOME = pathlib.Path.home() / ".claude"
REPO = pathlib.Path(__file__).parent

SKILLS = ["verilog-rtl", "verilog-a", "lattice-fpga",
          "uvm-verification", "chip-verification", "formal-verification"]
EXCLUDE = {"skill-validation-prompt.md", "consistency-map.md", "all-skills-consistency.md"}


def _ignore(_d, contents):
    return {n for n in contents if n in EXCLUDE}


def install_skills(dry):
    root = HOME / "skills"
    for name in SKILLS:
        src, dest = REPO / "skills" / name, root / name
        if not src.exists():
            print(f"SKIP skill (not found): {name}"); continue
        if dry:
            print(f"[dry-run] skill {'UPDATE' if dest.exists() else 'INSTALL'}: {name} -> {dest}")
        else:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest, ignore=_ignore)
            print(f"skill installed: {name}")


def install_agents(dry):
    src, dest = REPO / "agents", HOME / "agents"
    if not src.exists():
        print("SKIP agents (no agents/ dir)"); return
    mds = sorted(src.glob("*.md"))
    if dry:
        print(f"[dry-run] agents -> {dest}/ : {[m.name for m in mds]}")
    else:
        dest.mkdir(parents=True, exist_ok=True)
        for m in mds:
            shutil.copy2(m, dest / m.name)
        print(f"agents installed ({len(mds)}) -> {dest}")


def install_kit(dry):
    src, dest = REPO / "agent-kit", HOME / "agent-kit"
    if not src.exists():
        print("SKIP agent-kit (no agent-kit/ dir)"); return
    if dry:
        print(f"[dry-run] agent-kit -> {dest}/ : {[p.name for p in sorted(src.iterdir())]}")
    else:
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        print(f"agent-kit installed -> {dest}")


def main():
    ap = argparse.ArgumentParser(description="Install chip-design skills + agents + kit")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", choices=["skills", "agents", "kit"], help="install only one component")
    a = ap.parse_args()
    if not HOME.exists():
        print(f"ERROR: {HOME} not found"); sys.exit(1)
    if a.only in (None, "skills"): install_skills(a.dry_run)
    if a.only in (None, "agents"): install_agents(a.dry_run)
    if a.only in (None, "kit"):    install_kit(a.dry_run)
    print("\n(dry-run) nothing changed." if a.dry_run else f"\nDone -> {HOME}")


if __name__ == "__main__":
    main()
