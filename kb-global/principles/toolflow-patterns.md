---
kind: pattern
domain: toolflow
scope: global
tags: [subprocess, windows, msys2, shell, eda, simvision, graphify, tooling-maintenance]
promoted_from:
  - graphify-version-drift-skill-resync-20260622
  - pgrcmd-dll-init-failed-wmi-workaround-20260624
  - shell-run-stderr-contamination-pattern-20260624
  - simvision-duplicate-db-explorefull-20260408
---

# Toolflow 일반 패턴 (전 프로젝트 적용) — 장기 지식

> 특정 프로젝트의 버그 instance가 아니라, **여러 프로젝트에 일반화되는 원칙**.
> 프로젝트별 구체 사례는 각 프로젝트의 `docs/solutions/toolflow/` 참조.

---

## P-SUBPROCESS-STDERR · Python shell wrapper stderr→stdout append 오염

**증상**: 경로 파싱이 garbage 문자열을 반환하거나, `splitlines()` 결과에 에러 메시지가 섞임.
`bool(result.strip())` 조건 분기가 의도치 않게 True. 문제가 간헐적으로 보여 재현 어려움.

**근본 원인**: shell wrapper가 `result.stderr`를 `result.stdout`에 무조건 append하는 패턴.
`find`/`grep`/`git` 등이 부분 실패하면 stderr 에러 메시지가 반환값에 포함돼 파싱 오염.

```python
# BAD — stderr 무조건 append
result = subprocess.run(["bash", "-c", cmd], capture_output=True)
out = result.stdout.decode()
out += "\n" + result.stderr.decode()   # 오염 원천
return out

# GOOD — 파싱용 명령은 stderr를 억제
r = await shell_run(f"grep -rl 'pattern' {path} 2>/dev/null || true")

# GOOD — splitlines() 후 형식 검증
for line in r.strip().splitlines():
    if not line.startswith("expected_prefix"):
        continue
    # 처리
```

**원칙**:
- 반환값을 path / list / 조건 분기에 쓰는 shell 명령은 `2>/dev/null` 필수.
- `|| true`로 exit code를 억제할 때 stderr도 함께 억제했는지 확인.
- `splitlines()` 후 라인 형식 검증(prefix/regex)으로 에러 메시지 방어.

---

## P-WINDOWS-CONSOLE · MSYS2 서브프로세스에서 Windows CONSOLE exe 실행 실패

**증상**: Windows CONSOLE 서브시스템 실행 파일을 MSYS2 bash/Python subprocess로 실행 시
`STATUS_DLL_INIT_FAILED`(`0xC0000142`) 또는 exit 127. log 파일 미생성.
`Start-Process`, `CREATE_NEW_CONSOLE`, `AllocConsole()` 등도 실패.

**근본 원인**: MSYS2 bash 서브프로세스로 실행하면 stdin/stdout/stderr가 POSIX pseudo-handle(파이프)로
설정돼 자식 프로세스에 상속. Windows CONSOLE exe의 CRT DllMain이 유효한 콘솔 핸들을 찾지 못해 FALSE 반환.

**해결 패턴 — WMI `Win32_Process.Create` 우회**:

```bash
run_via_wmi() {
    local win_exe_path="$1"   # cygpath -w 변환 필요
    local args="$2"

    powershell.exe -NoProfile -NonInteractive -Command "
\$wmi = [wmiclass]'Win32_Process'
\$result = \$wmi.Create('\"$win_exe_path\" $args')
if (\$result.ReturnValue -eq 0 -and \$result.ProcessId) {
    \$p = Get-Process -Id \$result.ProcessId -ErrorAction SilentlyContinue
    if (\$p) { \$p.WaitForExit(30000) }
}
Start-Sleep -Milliseconds 500
" || true
}
```

WMI 서비스(winmgmt)는 MSYS2 프로세스 계층 **외부**에서 프로세스를 생성하므로 깨끗한 Windows 컨텍스트를 얻음.

**원칙**:
- MSYS2에서 Windows CONSOLE 서브시스템 exe(Lattice pgrcmd, 일부 EDA 툴)는 직접 서브프로세스 실행 금지.
- exit code는 MSYS2 context에서 127로 오보 → 성공 판단은 tool이 생성하는 **log 파일**로.
- Claude Code bash tool에서도 동일 실패 — 실제 MSYS2 터미널 직접 실행 또는 WMI 패턴 사용.

---

## P-SIMVISION-EXPLOREFULL · SimVision `explorefull`/`explore` → duplicate DB handle

**증상**: `database find` 결과에 동일 이름 DB가 2개 반환(`"ci_top_TOP015 ci_top_TOP015"`).
`waveform add`에서 실제 파형 대신 "placeholder for future object creation" 표시.

**근본 원인**: `database open` 후 `database explorefull` 또는 `database explore` 호출 시
SimVision 내부적으로 동일 이름의 DB 핸들을 추가 생성. `db_prefix` 파싱이 두 번째 핸들로 오염.

```tcl
# BAD — explorefull이 duplicate DB handle 생성
database open $shm_path
database explorefull -using $db_name

# GOOD — open만, explore 계열 제거
# SHM은 명령줄로 전달: simvision -waves $shm_path
```

**원칙**:
- SimVision TCL 스크립트에서 `explorefull`/`explore` 호출 금지. `database open`으로 충분.
- SHM은 `database open` 후 TCL explore가 아니라 **명령줄 인수**(`-waves $shm_path`)로 전달.
- `database find` 결과는 `lindex $db_list 0`으로 방어적으로 첫 번째만 사용.
- waveform placeholder → signal이 SHM probe scope 내에 있는지 먼저 확인.

---

## P-GRAPHIFY-UPGRADE · graphify 업그레이드 시 skill↔package 동기 필수

**증상**: `graphify` 호출 시 경고 `"skill is from X.Y.Z, package is A.B.C. Run 'graphify install' to update"`.
`graphify.exe` 직접 실행 시 `ModuleNotFoundError`. 업그레이드 후 동작 불일치.

**근본 원인**: graphify는 `SKILL.md`(skill)를 패키지가 install. 패키지만 업그레이드하면
skill이 구 버전으로 남아 skill↔package 불일치 발생. `.exe` 콘솔 런처는 user-site 경로를
못 찾는 transient 케이스 존재.

**업그레이드 4-step 체크리스트**:
1. 버전 핀 갱신 (`graphifyy==<버전>`, ≥7일 릴리스 적격 확인)
2. `pip install -U graphifyy==<버전>` (공유 venv 기준)
3. **skill 재동기**: `python -m graphify install --platform claude` (경고 해소)
4. 그래프 재빌드: `python -m graphify update .`

**원칙**:
- `requirements.txt`로 버전 **핀** 고정. graphify는 거의 매일 릴리스 → HEAD 추종 금지.
- 항상 `python -m graphify` 사용 (`graphify.exe` 런처 flaky 회피).
- 4-step을 **함께** 수행 — skill과 package 버전이 다르면 워크플로우 전체가 깨짐.
