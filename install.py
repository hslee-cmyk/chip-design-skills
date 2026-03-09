"""
Install custom chip design skills to ~/.claude/skills/

Usage:
    python install.py          # install all skills
    python install.py --dry-run  # preview without copying
"""
import shutil, pathlib, argparse, sys

SKILLS_DIR = pathlib.Path.home() / ".claude" / "skills"
REPO_SKILLS = pathlib.Path(__file__).parent / "skills"

CUSTOM_SKILLS = [
    "verilog-rtl",
    "verilog-a",
    "lattice-fpga",
    "uvm-verification",
    "chip-verification",
]


def install(dry_run: bool = False):
    if not SKILLS_DIR.exists():
        print(f"ERROR: Skills directory not found: {SKILLS_DIR}")
        sys.exit(1)

    for skill_name in CUSTOM_SKILLS:
        src = REPO_SKILLS / skill_name
        dest = SKILLS_DIR / skill_name

        if not src.exists():
            print(f"SKIP (not found): {skill_name}")
            continue

        if dry_run:
            action = "UPDATE" if dest.exists() else "INSTALL"
            print(f"[dry-run] {action}: {skill_name}  →  {dest}")
        else:
            if dest.exists():
                shutil.rmtree(dest)
                action = "Updated"
            else:
                action = "Installed"
            shutil.copytree(src, dest)
            print(f"{action}: {skill_name}")

    if dry_run:
        print("\n(dry-run) No files were changed.")
    else:
        print(f"\nAll skills installed to: {SKILLS_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Install chip design skills")
    parser.add_argument("--dry-run", action="store_true", help="Preview without copying")
    args = parser.parse_args()
    install(dry_run=args.dry_run)
