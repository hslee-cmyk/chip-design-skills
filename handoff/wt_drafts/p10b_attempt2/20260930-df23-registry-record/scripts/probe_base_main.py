"""순서 3 사전 점검(판정 아님): 새 test의 합성 레지스트리가 base 도구의 기존 규칙(인자 추가 없음)에서
발견 0 / §7 이름 바꾸면 `stale`인지 -- test 결함(병합 뒤에야 드러날 구성 오류)을 미리 본다.
새 test 소스를 읽어 import 줄만 `from reg_check import main`으로 바꾸고 exec한다. 결과는 C:/g88/out2/probe_base_main.txt."""
import io
import contextlib
import pathlib
import sys

R = pathlib.Path("C:/g88/iso2")
TF = R / "skills/analog-gmid-design/assets/tests/contracts/test_reg_check_df23.py"
OUT = pathlib.Path("C:/g88/out2/probe_base_main.txt")
WORK = pathlib.Path("C:/g88/probe2")

src = TF.read_text(encoding="utf-8")
old = "from reg_check import check_df23, main"
assert src.count(old) == 1
src = src.replace(old, "from reg_check import main\ncheck_df23 = None")
ns = {"__file__": str(TF), "__name__": "p10b_probe"}
exec(compile(src, str(TF), "exec"), ns)

import reg_check  # noqa: E402  (iso2 tools, test 머리가 sys.path에 넣음)
assert not hasattr(reg_check, "check_df23"), "base 도구에 check_df23이 있다"
lines = ["reg_check file: " + reg_check.__file__]


def run(tag, text):
    d = WORK / tag
    root, reg, _ = ns["_p10b_make_root"](d, text)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = reg_check.main(["--registry", str(reg), "--root", str(root)])
    lines.append(f"{tag}: rc={rc} out={buf.getvalue()!r}")


run("no_s8", ns["_p10b_registry"](None))
run("with_s8", ns["_p10b_registry"](ns["_p10b_section8"]()))
run("stale", ns["_p10b_registry"](ns["_p10b_section8"](), s7_name="p10b_gone_fn"))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = reg_check.main(["--registry", "x", "--root", "y", "--df23-inventory", "z"])
lines.append(f"base_unknown_arg: rc={rc}")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
