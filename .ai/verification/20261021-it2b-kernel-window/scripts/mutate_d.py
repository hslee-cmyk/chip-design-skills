"""IT-2b 감사: D (b)(c)(d) 정적 AST test 가 실제로 거부하는지 변형으로 확인(복제본 m 에서만, 끝나면 원문 복원).
usage: python -I mutate_d.py <clone m root> <out jsonl>
파일은 CRLF 일 수 있어 LF 로 바꿔 변형한 뒤 원래 줄끝으로 되돌려 쓴다. 변형마다 넣은 문자열(markers)이 결과에 모두 있어야 applied = true.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
SKILL = ROOT / "skills" / "analog-gmid-design"
BC = SKILL / "gmid_engine" / "sizing" / "block_columns.py"
S2 = SKILL / "gmid_engine" / "sizing" / "s2_values.py"
TESTS = ["gmid_engine/tests/sizing/test_block_columns.py::test_it2b_d_region_rows_kinds_are_sat_and_triode_only",
         "gmid_engine/tests/sizing/test_block_columns.py::test_it2b_d_region_rows_has_no_zero_vgs_op_point_conduction_columns_or_eo1_import",
         "gmid_engine/tests/sizing/test_block_columns.py::test_it2b_d_no_operating_point_mismatch_vocabulary_in_engine_sources"]
SHORT = ["D_b", "D_c", "D_d"]
ANCHOR = "        return tuple(rows)\n\n    def input_windows"
ROWS_ANCHOR = '_ROW_TRIODE = "triode"'
S2_ANCHOR = 'TIE_ROOT = "w4_root"'
MOS_POINT = "    def mos_point(self, m, values):\n"
IMP = "from .s2_values import (\n"


def inject(body):
    return lambda t: t.replace(ANCHOR, "        if False:\n" + body + "        return tuple(rows)\n\n    def input_windows", 1)


def chain(*fns):
    def run(t):
        for fn in fns:
            t = fn(t)
        return t
    return run


def rep(a, b):
    return lambda t: t.replace(a, b, 1)


OFF_ROW = '            rows.append((d, s, sign, 0.0, "off"))\n'
VARIANTS = [
    ("none", {}, [], "변형 없음(기준)"),
    ("off_literal", {BC: inject(OFF_ROW)}, [OFF_ROW], "region_rows 에 off 행(문자열 상수)"),
    ("off_module_const", {BC: chain(rep(ROWS_ANCHOR, ROWS_ANCHOR + '\n_ROW_OFF = "off"'),
                                    inject("            rows.append((d, s, sign, 0.0, _ROW_OFF))\n"))},
     ['_ROW_OFF = "off"', "0.0, _ROW_OFF))"], "모듈 수준 상수 _ROW_OFF = \"off\" 로 off 행"),
    ("off_imported_const", {S2: rep(S2_ANCHOR, S2_ANCHOR + '\nROW_OFF = "off"'),
                            BC: chain(rep(IMP, IMP + "    ROW_OFF,\n"), inject("            rows.append((d, s, sign, 0.0, ROW_OFF))\n"))},
     ['ROW_OFF = "off"', "    ROW_OFF,\n", "0.0, ROW_OFF))"], "s2_values 의 ROW_OFF = \"off\" 를 import 해 off 행"),
    ("off_imported_alias", {S2: rep(S2_ANCHOR, S2_ANCHOR + '\nROW_OFF = "off"'),
                            BC: chain(rep(IMP, IMP + "    ROW_OFF as _OFF_ALIAS,\n"), inject("            rows.append((d, s, sign, 0.0, _OFF_ALIAS))\n"))},
     ['ROW_OFF = "off"', "ROW_OFF as _OFF_ALIAS", "0.0, _OFF_ALIAS))"], "import 별칭(as)으로 off 행 -- 측정 한계 확인"),
    ("off_in_callee", {BC: rep(MOS_POINT, MOS_POINT + '        if False:\n            return "off"\n')}, ['return "off"'],
     "region_rows 가 부르는 mos_point 안에 \"off\""),
    ("op_point_vgs0_pos", {BC: inject("            op_point(self.lut.memo, kind, w_key, self.L[m], 0, vds, vsb)\n")}, ["self.L[m], 0, vds"],
     "VGS=0 op_point(5번째 위치 인자 0)"),
    ("op_point_vgs0_kw", {BC: inject("            op_point(self.lut.memo, kind, w_key, self.L[m], vgs=0, vds=vds, vsb=vsb)\n")}, ["vgs=0, vds"],
     "VGS=0 op_point(vgs=0 키워드)"),
    ("op_point_vgs0_float", {BC: inject("            op_point(self.lut.memo, kind, w_key, self.L[m], 0.0, vds, vsb)\n")}, ["self.L[m], 0.0, vds"],
     "VGS=0.0 op_point(실수 0)"),
    ("off_current_read", {BC: inject("            _x = self.lut.memo.dc_off_current\n")}, ["memo.dc_off_current"], "dc_off_current 속성 읽기"),
    ("floor_read_str", {BC: inject('            _x = values.get("dc_conduction_floor")\n')}, ['get("dc_conduction_floor")'], "dc_conduction_floor 문자열 읽기"),
    ("eo1_import", {BC: inject("            from .conduction import is_conducting  # noqa\n")}, ["from .conduction import"], "EO-1 모듈 import(이름에 conduct)"),
    ("eo1_import_other_name", {BC: inject("            from .region_on import v_on  # noqa\n")}, ["from .region_on import"],
     "EO-1 꼴 import 이름에 conduct 없음 -- 대리 측정 한계"),
    ("vocab_const", {S2: rep(S2_ANCHOR, S2_ANCHOR + '\nINPUT_STATUS_OP_MISMATCH = "op_mismatch"')}, ['INPUT_STATUS_OP_MISMATCH = "op_mismatch"'],
     "s2_values 에 op_mismatch 상수"),
    ("vocab_field", {S2: rep("    tol_v: object = None\n", "    tol_v: object = None\n    status_detail: tuple = ()\n")}, ["status_detail: tuple"],
     "Window.status_detail 칸"),
    ("vocab_metric_code", {S2: rep(S2_ANCHOR, S2_ANCHOR + '\nCODE_X = "input_window_operating_point_mismatch"')},
     ['"input_window_operating_point_mismatch"'], "metric code 문자열"),
    ("vocab_comment_only", {S2: rep(S2_ANCHOR, S2_ANCHOR + "  # op_mismatch status_detail")}, ["# op_mismatch status_detail"],
     "주석에만 어휘 -- green 유지 기대"),
]


def main():
    originals = {BC: BC.read_bytes(), S2: S2.read_bytes()}
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        for name, edits, markers, desc in VARIANTS:
            for p, b in originals.items():
                p.write_bytes(b)
            texts = {}
            for p, fn in edits.items():
                raw = originals[p].decode("utf-8")
                crlf = "\r\n" in raw
                n = fn(raw.replace("\r\n", "\n"))
                texts[p] = n
                p.write_bytes((n.replace("\n", "\r\n") if crlf else n).encode("utf-8"))
            joined = "".join(texts.values())
            applied = all(mk in joined for mk in markers)
            res = {}
            for tid, short in zip(TESTS, SHORT):
                r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=line", tid], cwd=SKILL,
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
                res[short] = "pass" if r.returncode == 0 else "FAIL"
            rec = {"variant": name, "desc": desc, "applied": applied, **res}
            print(json.dumps(rec, ensure_ascii=False), flush=True)
            with OUT.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    finally:
        for p, b in originals.items():
            p.write_bytes(b)


if __name__ == "__main__":
    main()
