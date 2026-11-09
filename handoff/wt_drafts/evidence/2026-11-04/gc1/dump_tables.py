"""권한표·블록 READS/WRITES 덤프(import만, 평가·LUT 0). 사본 경로의 엔진을 읽는다. 바이트코드를 쓰지 않는다.
사용: python -B dump_tables.py <gmid_engine의 부모 경로> <tables.json>"""
import dataclasses
import importlib
import json
import pathlib
import pkgutil
import sys

sys.dont_write_bytecode = True
root, out = sys.argv[1], pathlib.Path(sys.argv[2])
sys.path.insert(0, root)
import gmid_engine  # noqa: E402
from gmid_engine.core.compute_block import ComputeBlock  # noqa: E402
from gmid_engine.layout._ly_fields import LY_WRITERS  # noqa: E402
from gmid_engine.search.s0_fields import S0_WRITERS  # noqa: E402

failed, blocks = [], {}
for info in pkgutil.walk_packages(gmid_engine.__path__, "gmid_engine."):
    if ".tests" in info.name:
        continue
    try:
        mod = importlib.import_module(info.name)
    except Exception as exc:  # 기록만, 측정은 계속
        failed.append((info.name, repr(exc)[:200]))
        continue
    for name, value in vars(mod).items():
        if isinstance(value, ComputeBlock):
            fields = {f.name: getattr(value, f.name) for f in dataclasses.fields(value)} if dataclasses.is_dataclass(value) else vars(value)
            blocks[value.name] = (value.name, sorted(list(r) for r in value.reads), sorted(list(w) for w in value.writes))
writers = sorted(list(e[0]) + [e[1]] for e in list(S0_WRITERS.entries) + list(LY_WRITERS.entries))
out.write_text(json.dumps({"writers": writers, "blocks": sorted(blocks.values()), "import_failed": failed}, ensure_ascii=False, indent=0), encoding="utf-8")
print(len(writers), len(blocks), failed)
