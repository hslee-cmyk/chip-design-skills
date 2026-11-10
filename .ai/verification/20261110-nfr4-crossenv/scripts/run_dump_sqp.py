"""nfr4_run_dump 를 순수 Python SQP 로 돌린다: 엔진 코드는 그대로 두고 세 모듈의 모듈 전역 `scipy_minimize` 만 교체한다(실험)."""
import importlib
import sys

SKILL = "/usrdata/hoseung.lee/claude.run/chip-design-skills/skills/analog-gmid-design"
sys.path.insert(0, SKILL)
sys.path.insert(0, "/usrdata/hoseung.lee/claude.run/scratch/nfr4_work/exp_sqp")
sys.path.insert(0, SKILL + "/gmid_engine/tests")
sys.path.insert(0, SKILL + "/gmid_engine/tests/integration")
import pure_sqp  # noqa: E402
import gmid_engine.search  # noqa: E402,F401

patched = []
for name in ("layer0_center", "slsqp_outer", "macro_poles"):
    mod = importlib.import_module("gmid_engine.search." + name)
    assert hasattr(mod, "scipy_minimize"), name
    mod.scipy_minimize = pure_sqp.minimize
    patched.append(name)
sys.stderr.write("patched scipy_minimize -> pure_sqp in: %s\n" % ", ".join(patched))
import nfr4_run_dump  # noqa: E402
sys.exit(nfr4_run_dump.main(sys.argv[1:]))
