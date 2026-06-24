"""
Install chip-design skills + agents + agent-kit + hooks to ~/.claude/
(and bkit-workflow customizations under bkit/).

    python install.py            # install everything to global ~/.claude/
    python install.py --dry-run  # preview
    python install.py --only agents   # one component:
                                      #   skills | agents | kit | hooks | bkit-agents

    # project-level (bkit precedence: project .claude/ overrides ~/.claude/):
    python install.py --only agents --project /path/to/proj   # -> proj/.claude/agents/
    python install.py --only hooks  --project /path/to/proj   # -> proj/.claude/hooks/ + settings.json

    # bkit PDCA/sprint template override (plugin templates are hardcoded; see bkit/README.md):
    python install.py --patch-bkit-templates           # copy bkit/templates/*.template.md
                                                        # into the installed bkit plugin (re-run after upgrade)

kit/skills always go global (agents reference ~/.claude/agent-kit by absolute path).
Hooks register at USER scope by default (common to every project) and merge — as a
union — with bkit's own plugin hooks (Claude Code fires all hook scopes; none shadow).
"""
import shutil, pathlib, argparse, sys, json, os, re

HOME = pathlib.Path.home() / ".claude"
REPO = pathlib.Path(__file__).parent

SKILLS = ["verilog-rtl", "verilog-a", "lattice-fpga",
          "uvm-verification", "chip-verification", "formal-verification",
          "solution-capture"]
EXCLUDE = {"skill-validation-prompt.md", "consistency-map.md", "all-skills-consistency.md"}

# default hook trigger; override per-hook with a sidecar "<name>.json" {"event","matcher"}
HOOK_DEFAULT = {"event": "PreToolUse", "matcher": "Write|Edit"}


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


def _is_agent_md(m):
    # an agent definition starts with YAML frontmatter ('---'); skip README and
    # meta docs so they are never deployed to ~/.claude/agents as broken agents.
    if m.name.lower() == "readme.md":
        return False
    try:
        return m.read_text(encoding="utf-8").lstrip().startswith("---")
    except Exception:
        return False


def _agents_dest(project):
    # --project redirects agents to <proj>/.claude/agents (project-level, overrides global)
    return (pathlib.Path(project).expanduser().resolve() / ".claude" / "agents") if project \
        else (HOME / "agents")


def _install_agents_from(src, dest, label, dry):
    if not src.exists():
        print(f"SKIP {label} (no {src.name}/ dir)"); return
    mds = sorted(m for m in src.glob("*.md") if _is_agent_md(m))
    if not mds:
        print(f"SKIP {label} (no agent .md yet)"); return
    if dry:
        print(f"[dry-run] {label} -> {dest}/ : {[m.name for m in mds]}")
    else:
        dest.mkdir(parents=True, exist_ok=True)
        for m in mds:
            shutil.copy2(m, dest / m.name)
        print(f"{label} installed ({len(mds)}) -> {dest}")


def install_agents(dry, project=None):
    _install_agents_from(REPO / "agents", _agents_dest(project), "agents", dry)


def install_bkit_agents(dry, project=None):
    # bkit/agents = bkit-workflow customizations (copy-rename of plugin agents).
    _install_agents_from(REPO / "bkit" / "agents", _agents_dest(project), "bkit-agents", dry)


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


def install_kb_global(dry, workspace=None):
    """Deploy the long-term knowledge *tooling* to <workspace>/.tools/kb-global/.

    Option 2 (단일 정본): kb_index.py는 정본 코퍼스(kb-global/principles/ + agent-kit/
    failure-taxonomy.md)를 git repo에서 **직접 색인**한다 → 런타임에 principles 복사본을
    두지 않는다(분기·유실 불가). 따라서 이 함수는 툴링만 배포한다:
      kb_index.py, kb_search.py, README.md (편의용 런타임 사본) + requirements.txt.
    인덱스(kb.sqlite)·캐시·venv는 보존(파일 단위 복사). 정본 principles는 repo에만 존재.
    workspace 기본값 = 이 repo의 부모(= fpga 워크스페이스).
    """
    src = REPO / "kb-global"
    if not src.exists():
        print("SKIP kb-global (no kb-global/ dir)"); return
    ws = pathlib.Path(workspace).expanduser().resolve() if workspace else REPO.parent
    dest = ws / ".tools" / "kb-global"
    stale_principles = dest / "principles"   # Option 1 잔재 — 있으면 제거(혼동 방지)
    if dry:
        print(f"[dry-run] kb-global tooling -> {dest}/ (kb_index/kb_search/README; preserve kb.sqlite)")
        print(f"[dry-run]   정본 principles는 repo에만(런타임 복사 안 함). 정본 직접 색인.")
        if stale_principles.exists():
            print(f"[dry-run]   remove stale runtime principles: {stale_principles}")
        print(f"[dry-run]   requirements.txt -> {ws / '.tools' / 'requirements.txt'}")
        return
    dest.mkdir(parents=True, exist_ok=True)
    for f in ("kb_index.py", "kb_search.py", "kb_eval.py", "README.md"):
        if (src / f).exists():
            shutil.copy2(src / f, dest / f)
    if (src / "eval").is_dir():                       # eval 골드셋 + 하니스
        (dest / "eval").mkdir(parents=True, exist_ok=True)
        for p in sorted((src / "eval").glob("*.json")):
            shutil.copy2(p, dest / "eval" / p.name)
    if (src / "requirements.txt").exists():
        shutil.copy2(src / "requirements.txt", ws / ".tools" / "requirements.txt")
    if stale_principles.exists():
        shutil.rmtree(stale_principles)
        print(f"  removed stale runtime principles -> {stale_principles}")
    print(f"kb-global tooling installed -> {dest}  (정본 principles는 repo 직접 색인; kb.sqlite 보존)")
    print(f"  재색인: <ws>/.tools/kb-venv/Scripts/python.exe {dest / 'kb_index.py'}")


# --------------------------------------------------------------------- hooks

def _iter_hook_scripts():
    """All hook scripts: top-level hooks/ (bkit-agnostic) + bkit/hooks/ (bkit-workflow)."""
    for base in (REPO / "hooks", REPO / "bkit" / "hooks"):
        if not base.exists():
            continue
        for p in sorted(base.glob("*.py")):
            meta = dict(HOOK_DEFAULT)
            side = p.with_suffix(".json")
            if side.exists():
                try:
                    meta.update(json.loads(side.read_text(encoding="utf-8")))
                except Exception:
                    pass
            yield p, meta


def _register_hook(settings_path, command, matcher, event, tag, dry):
    """Idempotently add a command hook into a settings.json (dedupe by `tag` substring)."""
    data = {}
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except Exception:
            print(f"  ! cannot parse {settings_path}; skip registration"); return
    arr = data.setdefault("hooks", {}).setdefault(event, [])
    for block in arr:
        for h in block.get("hooks", []):
            if tag in (h.get("command") or ""):
                print(f"  hook already registered ({tag}) in {settings_path}")
                return
    arr.append({"matcher": matcher, "hooks": [{"type": "command", "command": command}]})
    if dry:
        print(f"  [dry-run] register {event}/{matcher} ({tag}) -> {settings_path}"); return
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    print(f"  hook registered ({tag}) -> {settings_path}")


def install_hooks(dry, project=None, py_exe=None):
    py_exe = py_exe or sys.executable
    if project:
        proj = pathlib.Path(project).expanduser().resolve()
        hooks_dir = proj / ".claude" / "hooks"
        settings = proj / ".claude" / "settings.json"
        def cmd_for(name):  # portable across clones via CLAUDE_PROJECT_DIR
            return '"%s" "${CLAUDE_PROJECT_DIR}\\.claude\\hooks\\%s"' % (py_exe, name)
    else:
        hooks_dir = HOME / "hooks"
        settings = HOME / "settings.json"
        def cmd_for(name):  # absolute path computed at install time -> machine-portable
            return '"%s" "%s"' % (py_exe, hooks_dir / name)
    found = False
    for p, meta in _iter_hook_scripts():
        found = True
        dest = hooks_dir / p.name
        if dry:
            print(f"[dry-run] hook {p.name} -> {dest}")
        else:
            hooks_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            print(f"hook installed: {p.name} -> {dest}")
        _register_hook(settings, cmd_for(p.name), meta["matcher"], meta["event"],
                       tag=p.stem, dry=dry)
    if not found:
        print("SKIP hooks (none found)")


def install_git_hooks(dry, project):
    """프로젝트 git hooks 배포 → <proj>/.git/hooks/ (지식 자산화 배관 A·B).
    pre-commit: docs/solutions 검증(차단)+regression-rules 동기. post-commit: graphify L3 갱신.
    venezia 등은 core.hooksPath 미설정 → .git/hooks 기본 위치 사용(클론마다 재실행 필요)."""
    if not project:
        print("ERROR: --install-git-hooks requires --project PATH"); return 1
    proj = pathlib.Path(project).expanduser().resolve()
    if not (proj / ".git").exists():
        print(f"ERROR: not a git repo: {proj}"); return 1
    src = REPO / "project-hooks"
    if not src.is_dir():
        print("SKIP git-hooks (no project-hooks/ dir)"); return 0
    gitdir = proj / ".git" / "hooks"
    for name in ("pre-commit", "post-commit"):
        s = src / name
        if not s.exists():
            continue
        dest = gitdir / name
        if dest.exists():
            print(f"  ! {name} already exists at {dest} — 덮어씀(백업: {name}.bak)")
            if not dry:
                shutil.copy2(dest, dest.with_suffix(".bak"))
        if dry:
            print(f"[dry-run] git hook {name} -> {dest}"); continue
        gitdir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, dest)
        try:
            os.chmod(dest, 0o755)
        except Exception:
            pass
        print(f"git hook installed: {name} -> {dest}")
    print("  (core.hooksPath 미사용 → .git/hooks 기본; 클론마다 재실행)")
    return 0


def _escape_for_claude(path: pathlib.Path) -> str:
    """경로 → Claude Code projects 디렉토리 key. C:\\foo\\bar -> C--foo-bar"""
    return re.sub(r'[:\\/]', '-', str(path.resolve()))


def install_memory_junction(dry, project, workspace=None):
    """프로젝트 Claude memory 디렉토리를 workspace 공유 memory로 junction.

    ~/.claude/projects/<proj-key>/memory/  →junction→  ~/.claude/projects/<ws-key>/memory/

    --workspace 미지정 시 project의 부모 디렉토리를 workspace로 사용.
    기존 memory 디렉토리가 있고 junction이 아니면 경고 후 건너뜀(--force로 강제).
    """
    if not project:
        print("ERROR: --install-memory-junction requires --project PATH"); return 1
    proj = pathlib.Path(project).expanduser().resolve()
    ws   = pathlib.Path(workspace).expanduser().resolve() if workspace else proj.parent

    claude_projects = pathlib.Path.home() / ".claude" / "projects"
    shared_memory   = claude_projects / _escape_for_claude(ws)   / "memory"
    proj_memory     = claude_projects / _escape_for_claude(proj) / "memory"

    if dry:
        print(f"[dry-run] memory junction:")
        print(f"  junction : {proj_memory}")
        print(f"  -> target: {shared_memory}")
        return 0

    # 공유 memory 디렉토리가 없으면 생성
    shared_memory.mkdir(parents=True, exist_ok=True)

    # 이미 junction이면 skip
    try:
        is_junc = proj_memory.is_junction()
    except AttributeError:                         # Python < 3.12 폴백
        is_junc = False
    if is_junc:
        print(f"  memory junction already exists: {proj_memory} -> {proj_memory.resolve()}")
        return 0

    # 실제 디렉토리가 있으면 경고 (--force 없이는 건너뜀)
    if proj_memory.exists():
        count = len(list(proj_memory.iterdir()))
        print(f"  ! {proj_memory} 이미 존재 (파일 {count}개) — junction 아님. 건너뜀.")
        print(f"    강제로 만들려면: 디렉토리 삭제 후 재실행.")
        return 1

    # junction 생성 (Windows: mklink /J, admin 불필요)
    import subprocess
    r = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(proj_memory), str(shared_memory)],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        print(f"  memory junction created: {proj_memory}")
        print(f"    -> {shared_memory}")
        return 0
    print(f"  ERROR: junction 생성 실패: {r.stderr.strip() or r.stdout.strip()}")
    return 1


def install_mcp(dry, project):
    """프로젝트 .mcp.json 에 graphify MCP 서버 등록 → 에이전트가 프로젝트 wiki 심층 탐색
    (graphify_query / shortest_path / explain / neighbors). graphify-out/graph.json 있을 때만."""
    if not project:
        print("ERROR: --install-mcp requires --project PATH"); return 1
    proj = pathlib.Path(project).expanduser().resolve()
    graph = proj / "graphify-out" / "graph.json"
    if not graph.exists():
        print(f"  graph 없음 → graphify MCP skip (먼저 `/graphify .` 로 그래프 생성): {proj.name}")
        return 0
    venv = proj.parent / ".tools" / "kb-venv" / "Scripts" / "python.exe"
    pyexe = str(venv) if venv.exists() else sys.executable
    mcp_path = proj / ".mcp.json"
    data = {}
    if mcp_path.exists():
        try:
            data = json.loads(mcp_path.read_text(encoding="utf-8"))
        except Exception:
            print(f"  ! {mcp_path} 파싱 실패 — skip"); return 0
    data.setdefault("mcpServers", {})["graphify"] = {
        "command": pyexe,
        "args": ["-m", "graphify.serve", str(graph), "--transport", "stdio"],
    }
    if dry:
        print(f"[dry-run] .mcp.json graphify 서버 등록 -> {mcp_path}"); return 0
    mcp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"graphify MCP registered -> {mcp_path}  (CC 재시작 후 graphify_* 툴 사용)")
    return 0


# ----------------------------------------------------------- bkit templates

def _vkey(name):
    return [int(x) if x.isdigit() else 0 for x in name.split(".")]


def patch_bkit_templates(dry):
    """Copy bkit/templates/*.template.md INTO the installed bkit plugin templates dir.

    bkit reads PDCA/sprint templates only from ${CLAUDE_PLUGIN_ROOT}/templates/ (hardcoded);
    there is no config/precedence override. This patches the plugin in place — it is
    versioned, so re-run after every bkit upgrade. Prefer the CLAUDE.md redirect snippet
    (bkit/templates/CLAUDE-redirect-snippet.md) for an upgrade-safe alternative.
    """
    src = REPO / "bkit" / "templates"
    tpls = sorted(src.glob("*.template.md")) if src.exists() else []
    if not tpls:
        print("SKIP template patch (no *.template.md in bkit/templates/)"); return
    base = HOME / "plugins" / "cache" / "bkit-marketplace" / "bkit"
    if not base.exists():
        print(f"SKIP template patch (bkit plugin not found: {base})"); return
    vers = sorted([d for d in base.iterdir() if d.is_dir()], key=lambda d: _vkey(d.name))
    if not vers:
        print("SKIP template patch (no plugin version dirs)"); return
    pdir = vers[-1] / "templates"
    print(f"  target plugin templates ({vers[-1].name}): {pdir}")
    for t in tpls:
        dest = pdir / t.name
        if dry:
            print(f"[dry-run] patch template {t.name} -> {dest}")
        else:
            shutil.copy2(t, dest)
            print(f"template patched: {t.name} -> {dest}")
    print("  NOTE: re-run after every bkit plugin upgrade (plugin dir is versioned).")


# ------------------------------------------------- RD-PDCA sub-step overlay

def _gen_phase_template(profile_meta, phase, spec):
    """Render one bkit-style phase template (markdown) from a profile phase spec."""
    pat = spec.get("pattern", "")
    out = [
        "<!-- GENERATED by install.py --gen-rd-pdca from bkit/workflow/substeps."
        + f"{profile_meta['profile']}.json — DO NOT edit by hand; edit the profile JSON and regenerate. -->",
        "",
        f"# {phase.capitalize()} — RD-PDCA sub-steps  (profile: {profile_meta['profile']} v{profile_meta['version']}, {pat})",
        "",
        f"> bkit는 이 문서를 {phase} 단계 1개로 인식한다. 실제로는 아래 sub-step이 council/swarm 게이트로 동작한다.",
        f"> 오케스트레이션은 `chip-cto-lead` agent가 `.ai/rd-pdca-substeps.json`을 읽어 수행.",
        "",
    ]
    for i, s in enumerate(spec.get("substeps", []), 1):
        gate = "  ⛔gate" if s.get("gate") else ""
        owner = s.get("owner", "?")
        skill = f" · skill:`{s['skill']}`" if s.get("skill") else ""
        out.append(f"## {i}. {s['title']}{gate}")
        out.append(f"*owner:* `{owner}`{skill}  ·  *id:* `{s['id']}`")
        out.append("")
        for c in s.get("checklist", []):
            out.append(f"- [ ] {c}")
        out.append("")
    return "\n".join(out)


def gen_rd_pdca(dry, project, profile):
    """Generate the project's active RD-PDCA profile + derived phase templates.

    Source of truth: bkit/workflow/substeps.<profile>.json. Outputs:
      <proj>/.ai/rd-pdca-substeps.json            (active profile chip-cto-lead reads)
      <proj>/.ai/bkit-templates/<phase doc>.md    (derived templates, regenerable)
      <proj>/.ai/bkit-templates/CLAUDE-redirect-snippet.md  (copy, for project CLAUDE.md)
    Swappable: edit/replace the profile JSON and re-run; agent + this generator are unchanged.
    """
    if not project:
        print("ERROR: --gen-rd-pdca requires --project PATH"); return 1
    src = REPO / "bkit" / "workflow" / f"substeps.{profile}.json"
    if not src.exists():
        print(f"ERROR: profile not found: {src}"); return 1
    try:
        prof = json.loads(src.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: cannot parse {src}: {e}"); return 1
    meta = {"profile": prof.get("profile", profile), "version": prof.get("version", "0")}
    proj = pathlib.Path(project).expanduser().resolve()
    ai = proj / ".ai"
    tdir = ai / "bkit-templates"
    print(f"== RD-PDCA overlay (profile '{meta['profile']}' v{meta['version']}) -> {ai}")

    # 1) active profile the agent reads at runtime
    active = ai / "rd-pdca-substeps.json"
    if dry:
        print(f"[dry-run] write {active}")
    else:
        ai.mkdir(parents=True, exist_ok=True)
        active.write_text(json.dumps(prof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  wrote {active}")

    # 2) derived phase templates
    for phase, spec in prof.get("phases", {}).items():
        doc = spec.get("doc", f"{phase}.template.md")
        dest = tdir / doc
        text = _gen_phase_template(meta, phase, spec)
        if dry:
            print(f"[dry-run] generate {dest}  ({len(spec.get('substeps', []))} substeps)")
        else:
            tdir.mkdir(parents=True, exist_ok=True)
            dest.write_text(text + "\n", encoding="utf-8")
            print(f"  generated {dest}  ({len(spec.get('substeps', []))} substeps)")

    # 3) CLAUDE.md redirect snippet (copy for convenience)
    snip = REPO / "bkit" / "templates" / "CLAUDE-redirect-snippet.md"
    if snip.exists():
        dest = tdir / "CLAUDE-redirect-snippet.md"
        if dry:
            print(f"[dry-run] copy {dest}")
        else:
            tdir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(snip, dest)
            print(f"  copied {dest}")
    print("  NEXT: paste .ai/bkit-templates/CLAUDE-redirect-snippet.md into the project's CLAUDE.md,")
    print("        then invoke `chip-cto-lead` during a Design/Do/Check phase. (Agent Teams: set")
    print("        CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 for real council/swarm parallelism.)")
    return 0


# ------------------------------------------------- project AI infra scaffold

def init_ai_infra(dry, project, force):
    """Scaffold the generalized AI infra (.ai/ + CLAUDE/AGENTS/GEMINI) from project-template/.

    Safe on existing projects: NEVER overwrites an existing file (skip) unless --force.
    Placeholders ({{PROJECT_NAME}} etc.) are filled; remaining `<!-- 채울 것 -->` are left for humans.
    """
    if not project:
        print("ERROR: --init-ai-infra requires --project PATH"); return 1
    proj = pathlib.Path(project).expanduser().resolve()
    if not proj.is_dir():
        print(f"ERROR: not a directory: {proj}"); return 1
    src_root = REPO / "project-template"
    if not src_root.is_dir():
        print(f"ERROR: template not found: {src_root}"); return 1
    name = proj.name
    repl = {
        "{{PROJECT_NAME}}": name,
        "{{PROJECT_TAGLINE}}": "( 한 줄 설명 — 무엇을 하는 칩/FPGA인가 )",
        "{{SUBMODULE_DIR}}": "db/design",
    }
    created, skipped = [], []
    TEXT_EXTS = {".md", ".sh", ".tcl", ".py", ".json", ".v", ".sv", ".pcf", ".sdc"}

    def emit(src, dst):
        rel = dst.relative_to(proj)
        if dst.exists() and not force:
            skipped.append(str(rel)); print(f"  skip (exists): {rel}"); return
        if dry:
            print(f"  [dry-run] {'overwrite' if dst.exists() else 'create'}: {rel}")
            created.append(str(rel)); return
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() in TEXT_EXTS:
            text = src.read_text(encoding="utf-8")
            for k, v in repl.items():
                text = text.replace(k, v)
            dst.write_text(text, encoding="utf-8", newline="\n")
        else:
            shutil.copy2(src, dst)
        created.append(str(rel)); print(f"  {'overwrote' if force and dst.exists() else 'created'}: {rel}")

    def emit_text(dst, text):
        rel = dst.relative_to(proj)
        if dst.exists() and not force:
            skipped.append(str(rel)); print(f"  skip (exists): {rel}"); return
        if dry:
            print(f"  [dry-run] {'overwrite' if dst.exists() else 'create'}: {rel}"); created.append(str(rel)); return
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8", newline="\n")
        created.append(str(rel)); print(f"  generated: {rel}")

    # never write into an already-mounted submodule (e.g. db/design = shared chip RTL)
    def _is_mounted_submodule(p):
        return p.is_dir() and any(p.iterdir())

    skip_dirs, skip_files = [], set()
    design = proj / "db" / "design"
    if _is_mounted_submodule(design):
        skip_dirs.append(design)
        print(f"  note: skip db/design subtree (mounted submodule: {design})")

    # toolchain decides whether config.sh + iCE40 build scripts are needed at all
    tool = _detect_toolchain(proj)
    if tool == "icecube2":
        print("  toolchain: iCE40 (iCEcube2/yosys) — db/scripts + config.sh 포함")
    elif tool in ("diamond", "radiant"):
        skip_dirs.append(proj / "db" / "scripts")   # one-line build → no scripts/config.sh
        print(f"  toolchain: {tool} — db/scripts/config.sh 생략(한 줄 빌드, build.md에 기록)")
    else:
        skip_dirs.append(proj / "db" / "scripts")   # unknown → don't dump iCE40 scripts
        print("  toolchain: 미감지 — db/scripts 생략(.ldf/.rdf/.prj 추가 후 --detect-config)")
    skip_files.add(src_root / "ai" / "build.md")     # build.md is generated per-toolchain

    def scaffold_tree(sub_src, dst_root):
        if not sub_src.is_dir():
            return
        for root, _dirs, files in os.walk(sub_src):
            for fn in sorted(files):
                s = pathlib.Path(root) / fn
                if s in skip_files:
                    continue
                dst = dst_root / s.relative_to(sub_src)
                if any(sd == dst.parent or sd in dst.parents for sd in skip_dirs):
                    continue  # mounted submodule or toolchain-irrelevant subtree
                if fn == ".gitkeep":
                    if not dry:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        if not dst.exists():
                            dst.touch()
                    continue
                emit(s, dst)

    print(f"== AI infra scaffold -> {proj}  (name='{name}', toolchain={tool or 'unknown'})")
    scaffold_tree(src_root / "ai", proj / ".ai")    # 에이전트 지식 베이스 (+ .ai/rag preflight)
    scaffold_tree(src_root / "db", proj / "db")     # 공통 db 구조 (+ iCE40면 scripts)
    scaffold_tree(src_root / "refs", proj / "refs") # 프로젝트 연관 문서
    scaffold_tree(src_root / "docs", proj / "docs") # 단기 지식 자산화 (docs/solutions T1..T9)
    emit_text(proj / ".ai" / "build.md", _gen_build_md(tool, proj, name))   # toolchain별 build.md
    for ptr in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"):
        emit(src_root / ptr, proj / ptr)

    print(f"\n  created/updated: {len(created)} · skipped(existing): {len(skipped)}")
    nextmsg = "  NEXT: fill `<!-- 채울 것 -->` in .ai/*.md, CLAUDE.md"
    nextmsg += "; db/scripts/config.sh" if tool == "icecube2" else " (build.md에 빌드 명령 기록됨 — 스크립트 불필요)"
    print(nextmsg + ";  git submodule add <url> db/design")
    return 0


def _find_one(proj, *globs):
    for g in globs:
        hits = sorted(proj.glob(g))
        if hits:
            return hits[0]
    return None


def _parse_part(part):
    """LCMXO2-4000ZE-1TG144I -> (device, package, speed, temp)."""
    toks = part.split("-")
    device = "-".join(toks[:2]) if len(toks) >= 2 else part
    pkg = speed = temp = ""
    if len(toks) >= 3:
        tail = toks[-1]                       # e.g. 1TG144I
        m = re.match(r"^(\d+)?([A-Za-z]+\d+)([A-Za-z])?$", tail)
        if m:
            speed, pkg, temp = m.group(1) or "", m.group(2) or "", m.group(3) or ""
        else:
            pkg = tail
    return device, pkg, speed, temp


def _detect_diamond_radiant(pf, tool):
    """Parse a Diamond .ldf / Radiant .rdf (XML). Returns a field dict or None."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.parse(str(pf)).getroot()
    except Exception as e:
        print(f"  ! cannot parse {pf.name}: {e}"); return None
    part = root.get("device", "")
    title = root.get("title", pf.stem)
    impl = root.find(".//Implementation")
    top = synth = defines = impl_name = ""
    if impl is not None:
        impl_name = impl.get("title", "impl1")
        synth = impl.get("synthesis", "")
        opt = impl.find("Options")
        if opt is not None:
            top = opt.get("top", "")
            defines = (opt.get("VERILOG_DIRECTIVES", "") or "").replace(";", " ").strip()
    device, pkg, speed, temp = _parse_part(part)
    return {
        "TOOL": tool, "PART": part, "DEVICE": device, "PACKAGE": pkg,
        "SPEED": speed, "TEMP": temp, "TOP_MODULE": top, "SYNTHESIS": synth or "synplify",
        "DEFINES": defines, "BASE_NAME": pf.stem, "IMPL": impl_name or "impl1",
        "PROJECT_FILE": pf,
    }


def _detect_icecube2(pf):
    """Best-effort parse of a Synplify/iCEcube2 .prj (TCL). Returns field dict."""
    txt = pf.read_text(encoding="utf-8", errors="replace")
    def opt(name):
        m = re.search(r'set_option\s+-%s\s+"?([^"\n]+)"?' % re.escape(name), txt)
        return (m.group(1).strip() if m else "")
    part = opt("part") or opt("technology")
    device, pkg, speed, temp = _parse_part(part)
    top = opt("top_module")
    defines = " ".join(re.findall(r'set_option\s+-vlog_std[^\n]*|add_file[^\n]*-define\s+(\S+)', txt))
    return {
        "TOOL": "icecube2", "PART": part, "DEVICE": device, "PACKAGE": pkg,
        "SPEED": speed, "TEMP": temp, "TOP_MODULE": top, "SYNTHESIS": "synplify",
        "DEFINES": "", "BASE_NAME": pf.stem, "IMPL": "", "PROJECT_FILE": pf,
    }


def _render_config(proj, name, f):
    """Render a pre-filled config.sh from detected fields f."""
    rel = f["PROJECT_FILE"].relative_to(proj).as_posix()
    lpf = _find_one(proj, "db/work/*.lpf", "**/*.lpf")
    rdc = _find_one(proj, "db/work/*.pdc", "**/*.pdc")
    sdc = _find_one(proj, "db/sdc/*.sdc", "**/*.sdc")
    lpf_s = lpf.relative_to(proj).as_posix() if lpf else "db/sdc/<constraint>.lpf"
    sdc_s = sdc.relative_to(proj).as_posix() if sdc else "db/sdc/<timing>.sdc"
    tool = f["TOOL"]
    L = [
        "#!/usr/bin/env bash",
        f"# config.sh — {name} 빌드 공유 설정  (AUTO-DETECTED from {rel} by install.py --detect-config)",
        "# 이 파일이 유일한 프로젝트별 설정점. 검출값이 틀리면 여기만 수정.",
        "",
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
        'PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"',
        "",
        f'PROJECT="{name}"',
        f'BASE_NAME="{f["BASE_NAME"]}"',
        f'TOOL="{tool}"',
        f'PART="{f["PART"]}"',
        f'DEVICE="{f["DEVICE"]}"',
        f'PACKAGE="{f["PACKAGE"]}"',
        f'SPEED="{f["SPEED"]}"',
        f'TOP_MODULE="{f["TOP_MODULE"]}"',
        f'SYNTHESIS="{f["SYNTHESIS"]}"',
        f'DEFINES="{f["DEFINES"]}"',
        "",
    ]
    # _render_config is only used for iCE40 (Diamond/Radiant use build.md one-liner instead).
    L += [
        '# 툴 경로는 버전 고정하지 않음 — PATH/env 우선, 없으면 설치된 최신 버전 자동 탐색.',
        'ICECUBE2_PATH="${ICECUBE2_PATH:-$(ls -d /c/lscc/iCEcube2.* 2>/dev/null | sort -V | tail -1)}"',
        'OSS_CAD_SUITE="${OSS_CAD_SUITE:-/c/oss-cad-suite/oss-cad-suite}"',
        'OUTPUT_DIR="img"',
        'BUILD_DIR="db/work/${BASE_NAME}/${BASE_NAME}_Implmnt"',
        f'SDC="{sdc_s}"',
        '# 빌드: bash db/scripts/build.sh',
    ]
    L += [
        "",
        "# ── 소스: 칩 공유 RTL = db/design 서브모듈 (정본 filelist 있으면 그것을 사용) ─",
        'DESIGN_FILELIST="db/design/d_filelist.f"',
        'DESIGN_SRC_GLOBS=( "db/design/d_*/mdl/*.v" "db/design/d_*/mdl/*.sv" )',
        'TOP_SRCS=( db/top/*.v )',
        "",
        'log_info()  { echo "[INFO]  $*"; }',
        'log_warn()  { echo "[WARN]  $*" >&2; }',
        'log_error() { echo "[ERROR] $*" >&2; }',
        "",
    ]
    return "\n".join(L) + "\n"


def detect_config(dry, project):
    """Auto-generate db/scripts/config.sh from an existing tool project file.

    Detects Diamond(.ldf) / Radiant(.rdf) / iCEcube2-Synplify(.prj) and writes a
    pre-filled, tool-correct config.sh — so you don't hand-write it per project.
    Existing config.sh is backed up to config.sh.bak.
    """
    if not project:
        print("ERROR: --detect-config requires --project PATH"); return 1
    proj = pathlib.Path(project).expanduser().resolve()
    if not proj.is_dir():
        print(f"ERROR: not a directory: {proj}"); return 1
    name = proj.name
    ldf = _find_one(proj, "db/work/*.ldf", "**/*.ldf")
    rdf = _find_one(proj, "db/work/*.rdf", "**/*.rdf")
    prj = _find_one(proj, "db/work/**/*.prj", "**/*.prj")
    if ldf:
        f = _detect_diamond_radiant(ldf, "diamond")
    elif rdf:
        f = _detect_diamond_radiant(rdf, "radiant")
    elif prj:
        f = _detect_icecube2(prj)
    else:
        print("ERROR: no tool project found (.ldf/.rdf/.prj under the project)"); return 1
    if not f:
        return 1
    tool = f["TOOL"]
    print(f"== detect-config: {tool} <- {f['PROJECT_FILE'].relative_to(proj).as_posix()}")
    print(f"   PART={f['PART']} TOP={f['TOP_MODULE']} DEFINES='{f['DEFINES']}'")
    scripts = proj / "db" / "scripts"

    # Diamond/Radiant: one-line build → NO config.sh. Write build.md, purge iCE40 scripts.
    if tool in ("diamond", "radiant"):
        bmd = proj / ".ai" / "build.md"
        text = _gen_build_md(tool, proj, name)
        if dry:
            print(f"  [dry-run] write {bmd}  (toolchain 한 줄 빌드)")
            print(f"  [dry-run] remove iCE40 scripts in {scripts}: {[s for s in ICE40_SCRIPTS if (scripts/s).exists()]}")
            return 0
        bmd.parent.mkdir(parents=True, exist_ok=True)
        bmd.write_text(text, encoding="utf-8", newline="\n")
        print(f"  wrote {bmd} (한 줄 빌드 명령 — config.sh/스크립트 불필요)")
        removed = []
        for s in ICE40_SCRIPTS + ("config.sh.bak", "README.md"):
            p = scripts / s
            if p.exists():
                p.unlink(); removed.append(s)
        if scripts.is_dir() and not any(scripts.iterdir()):
            scripts.rmdir(); print(f"  removed empty db/scripts/")
        elif removed:
            print(f"  removed iCE40-only files: {', '.join(removed)}")
        print("  검토: build.md의 device/top/defines/툴경로 확인.")
        return 0

    # iCE40 (icecube2/yosys): config.sh is needed.
    text = _render_config(proj, name, f)
    dst = scripts / "config.sh"
    if dry:
        print(f"  [dry-run] write {dst}"); print("  --- generated ---"); print(text); return 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        bak = dst.with_suffix(".sh.bak")
        shutil.copy2(dst, bak); print(f"  backed up existing -> {bak.name}")
    dst.write_text(text, encoding="utf-8", newline="\n")
    print(f"  wrote {dst}")
    print("  검토: DEVICE/PACKAGE/SPEED 파싱, 제약파일 경로, 툴 경로 확인.")
    return 0


# iCE40-only build machinery (needs config.sh + multi-step scripts). Diamond/Radiant build
# from their single project file (.ldf/.rdf) in one line — no config.sh, no scripts.
ICE40_SCRIPTS = ("config.sh", "build.sh", "build_yosys.sh", "build_icecube2.sh",
                 "synth_icecube2.tcl", "program.sh", "prepack_swg36.py")


def _detect_toolchain(proj):
    """Return 'diamond' | 'radiant' | 'icecube2' | None based on tool project files."""
    if _find_one(proj, "db/work/*.ldf", "**/*.ldf"):
        return "diamond"
    if _find_one(proj, "db/work/*.rdf", "**/*.rdf"):
        return "radiant"
    if _find_one(proj, "db/work/**/*.prj", "**/*.prj", "**/*_syn.prj"):
        return "icecube2"
    return None


def _gen_build_md(tool, proj, name):
    """build.md content tailored to the detected toolchain.

    iCE40 → script-based (db/scripts/). Diamond/Radiant → one-line build, NO script/config.
    Unknown → generic skeleton + hint to run --detect-config after adding a tool project.
    """
    if tool in ("diamond", "radiant"):
        pf = _find_one(proj, f"db/work/*.{'ldf' if tool=='diamond' else 'rdf'}", f"**/*.{'ldf' if tool=='diamond' else 'rdf'}")
        f = _detect_diamond_radiant(pf, tool) if pf else {}
        rel = pf.relative_to(proj).as_posix() if pf else f"db/work/<proj>.{'ldf' if tool=='diamond' else 'rdf'}"
        is_dia = tool == "diamond"
        toolc = "diamondc" if is_dia else "radiantc"
        var = "DIAMONDC" if is_dia else "RADIANTC"
        envp = "DIAMOND_PATH" if is_dia else "RADIANT_PATH"   # optional override of install root
        root = "/c/lscc/diamond" if is_dia else "/c/lscc/radiant"  # default install root (version-agnostic)
        outdir = f"db/work/{f.get('IMPL','impl1')}" if is_dia else "impl_1"
        arts = ".jed/.bit/.sed (MachXO2)" if is_dia else ".bit (Nexus)"
        return "\n".join([
            f"# Build — {name} (Lattice {'Diamond' if is_dia else 'Radiant'})",
            "",
            f"> 이 프로젝트는 **{tool} 단일 프로젝트 빌드**다. `{rel}` 가 device·top·defines·소스·제약을 모두 담는다.",
            "> **별도 빌드 스크립트·config.sh 불필요** — AI는 아래 한 줄로 빌드한다.",
            "",
            f"- Device: `{f.get('PART','?')}`  ·  Top: `{f.get('TOP_MODULE','?')}`",
            f"- Defines: `{f.get('DEFINES','')}`  (수정은 {'Diamond/.ldf' if is_dia else 'Radiant/.rdf'}에서)",
            "",
            "## 빌드 (한 줄, 스크립트 없음)",
            f"`{toolc}` 위치는 **고정하지 않는다** — PATH에 있으면 그대로, 없으면 설치된 **최신 버전**을 자동 탐색.",
            "```bash",
            f"# {toolc}: PATH 우선 → 설치된 최신 버전(버전 비고정). 다른 위치면 {envp} 또는 PATH 지정.",
            f'{var}=$(command -v {toolc} || ls -d "${{{envp}:-{root}}}"/*/bin/nt64/{toolc}* 2>/dev/null | sort -V | tail -1)',
            f'"${var}" "{rel}"',
            "```",
            f"- 산출물: `{outdir}/` ({arts})",
            f"- GUI 대안: {'Diamond' if is_dia else 'Radiant'}에서 `{rel}` 열고 Process → Export/Generate.",
            "",
            "## 프로그래밍",
            f"- {'Diamond' if is_dia else 'Radiant'} Programmer로 산출물 다운로드(JTAG/SVF). 비가역 단계가 있으면 주의.",
            "",
            "## 시뮬레이션·검증",
            "→ `servers.md` (원격 sim 서버·ssh-mcp·xcelium-mcp).",
        ]) + "\n"
    # iCE40 (icecube2/yosys) — script-based
    if tool == "icecube2":
        return "\n".join([
            f"# Build — {name} (iCE40, iCEcube2/yosys)",
            "",
            "> iCE40은 다단계 빌드 → `db/scripts/`의 공통 스크립트 사용. **`config.sh`만 프로젝트별 수정**.",
            "",
            "```bash",
            "bash db/scripts/build.sh            # 자동 감지(iCEcube2 우선, yosys fallback)",
            "bash db/scripts/build.sh --tool yosys|icecube2",
            "bash db/scripts/build.sh --clean",
            "bash db/scripts/program.sh         # SPI Flash (개발)",
            "bash db/scripts/program.sh --nvcm  # NVCM (비가역 OTP)",
            "```",
            "- 출력: `img/*.bin`(SPI) · `img/*.nvcm`(OTP). ⚠️ `program.sh`는 실제 터미널에서 실행.",
            "- 상세 스크립트 역할: `db/scripts/README.md`.",
            "",
            "## 시뮬레이션·검증",
            "→ `servers.md`.",
        ]) + "\n"
    # unknown — no tool project yet
    return "\n".join([
        f"# Build — {name}",
        "",
        "> ⚠️ FPGA toolchain 미감지 (db/work에 .ldf/.rdf/.prj 없음).",
        "> 툴 프로젝트를 추가한 뒤 `python install.py --detect-config --project <repo>` 를 실행하면",
        "> 이 문서와 (iCE40인 경우) `db/scripts/config.sh` 가 toolchain에 맞게 자동 구성된다.",
        "",
        "- Lattice **Diamond**(MachXO2/ECP5 등, `.ldf`) · **Radiant**(Nexus, `.rdf`): `<tool>c <project>` 한 줄 빌드, 스크립트 불필요.",
        "- **iCE40**(iCEcube2/yosys, `.prj`): `db/scripts/` 스크립트 + `config.sh` 사용.",
    ]) + "\n"


def main():
    try:  # Windows consoles default to cp949/cp1252 — avoid UnicodeEncodeError on Korean/em-dash
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Install chip-design skills + agents + kit + hooks")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only",
                    choices=["skills", "agents", "kit", "hooks", "bkit-agents", "kb-global"],
                    help="install only one component")
    ap.add_argument("--project", metavar="PATH",
                    help="install AGENTS/HOOKS into PATH/.claude/ (project-level, overrides "
                         "~/.claude). kit/skills still go global.")
    ap.add_argument("--python", default=sys.executable,
                    help="python executable used inside the hook command (default: this interpreter)")
    ap.add_argument("--patch-bkit-templates", action="store_true",
                    help="copy bkit/templates/*.template.md into the installed bkit plugin "
                         "(no config override exists; re-run after each bkit upgrade)")
    ap.add_argument("--gen-rd-pdca", action="store_true",
                    help="generate RD-PDCA sub-step overlay (profile + derived phase templates) "
                         "into --project/.ai/ from bkit/workflow/substeps.<profile>.json")
    ap.add_argument("--profile", default="common",
                    help="RD-PDCA profile name for --gen-rd-pdca (default: common)")
    ap.add_argument("--init-ai-infra", action="store_true",
                    help="scaffold generalized AI infra (.ai/ + CLAUDE/AGENTS/GEMINI) into --project "
                         "from project-template/ (skips existing files unless --force)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite existing files (for --init-ai-infra)")
    ap.add_argument("--onboard", action="store_true",
                    help="신규 프로젝트 온보딩 한 방: init-ai-infra + git-hooks(A·B) + CC hooks(D)를 순서대로 (--project 필수)")
    ap.add_argument("--install-git-hooks", action="store_true",
                    help="프로젝트 git hooks(pre-commit 검증·동기, post-commit graphify) 배포 → --project/.git/hooks/")
    ap.add_argument("--install-mcp", action="store_true",
                    help="프로젝트 .mcp.json 에 graphify MCP 서버 등록(그래프 심층 탐색; graph.json 있을 때)")
    ap.add_argument("--install-memory-junction", action="store_true",
                    help="~/.claude/projects/<proj>/memory/ → 공유 memory junction 생성 (--workspace 미지정 시 프로젝트 부모 디렉토리)")
    ap.add_argument("--workspace", metavar="PATH",
                    help="공유 memory의 기준 워크스페이스 경로 (--install-memory-junction / --onboard 용; 기본: --project의 부모)")
    ap.add_argument("--detect-config", action="store_true",
                    help="auto-generate db/scripts/config.sh from an existing tool project "
                         "(.ldf Diamond / .rdf Radiant / .prj iCEcube2) in --project")
    a = ap.parse_args()
    if not HOME.exists():
        print(f"ERROR: {HOME} not found"); sys.exit(1)

    if a.onboard:
        if not a.project:
            print("ERROR: --onboard requires --project PATH"); sys.exit(1)
        print(f"== Onboard {a.project}: init-ai-infra → git-hooks(A·B) → CC hooks(D) → memory junction\n")
        rc = init_ai_infra(a.dry_run, a.project, a.force) or 0
        if rc == 0:
            print(); rc = install_git_hooks(a.dry_run, a.project) or 0
        if rc == 0:
            print(); install_hooks(a.dry_run, a.project, a.python)
        print(); install_mcp(a.dry_run, a.project)   # graph 있으면 등록, 없으면 skip
        print(); install_memory_junction(a.dry_run, a.project, a.workspace)
        print("\n(dry-run) nothing changed." if a.dry_run else
              "\nDone (onboard). NEXT: 공유 venv 미구성이면 .tools/kb-venv 먼저, "
              "RTL 에이전트는 `--only agents --project`. graphify 그래프 1회 `/graphify .` "
              "후 `--install-mcp --project` 로 MCP 등록.")
        sys.exit(rc)

    if a.install_mcp:
        rc = install_mcp(a.dry_run, a.project)
        print("\n(dry-run) nothing changed." if a.dry_run else "\nDone (mcp).")
        sys.exit(rc or 0)

    if a.install_memory_junction:
        rc = install_memory_junction(a.dry_run, a.project, a.workspace)
        print("\n(dry-run) nothing changed." if a.dry_run else "\nDone (memory junction).")
        sys.exit(rc or 0)

    if a.install_git_hooks:
        rc = install_git_hooks(a.dry_run, a.project)
        print("\n(dry-run) nothing changed." if a.dry_run else "\nDone (git hooks).")
        sys.exit(rc or 0)

    if a.detect_config:
        rc = detect_config(a.dry_run, a.project)
        print("\n(dry-run) nothing changed." if a.dry_run else "\nDone (detect-config).")
        sys.exit(rc or 0)

    if a.init_ai_infra:
        rc = init_ai_infra(a.dry_run, a.project, a.force)
        print("\n(dry-run) nothing changed." if a.dry_run else "\nDone (AI infra).")
        sys.exit(rc or 0)

    if a.gen_rd_pdca:
        rc = gen_rd_pdca(a.dry_run, a.project, a.profile)
        print("\n(dry-run) nothing changed." if a.dry_run else "\nDone (RD-PDCA overlay).")
        sys.exit(rc or 0)

    if a.patch_bkit_templates:
        patch_bkit_templates(a.dry_run)
        if a.only is None:
            print("\n(--patch-bkit-templates done; pass no --only to also run normal install)")
            return

    if a.only in (None, "skills"):      install_skills(a.dry_run)
    if a.only in (None, "agents"):      install_agents(a.dry_run, a.project)
    if a.only in (None, "kit"):         install_kit(a.dry_run)
    if a.only in (None, "kb-global"):   install_kb_global(a.dry_run)  # workspace = repo parent
    if a.only in (None, "hooks"):       install_hooks(a.dry_run, a.project, a.python)
    if a.only in (None, "bkit-agents"): install_bkit_agents(a.dry_run, a.project)
    print("\n(dry-run) nothing changed." if a.dry_run else f"\nDone -> {HOME}")


if __name__ == "__main__":
    main()
