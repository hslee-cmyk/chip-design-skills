"""M-TH1c 정적 표: 엔진 gm/ID 역산·gm/ID 축 곡선 소비자 전수.

소스를 파일로 읽어 `ast`로 파싱한다. gmid_engine을 import하거나 실행하지 않는다. LUT를 읽지 않는다.
엔진 인용 용도 = 재작성 범위(원칙 8). 소유 card는 이 표가 정하지 않는다(README 표).

사용: python m_th1c_ast.py <gmid_engine 폴더> <결과 폴더>
결과: consumers.jsonl(자리마다 append), summary.txt
"""
import ast
import collections
import json
import pathlib
import re
import sys

# 대상 정의(P:1259): gm/ID -> VGS 역산, gm/ID 축 곡선 읽기(LR5 measure_L_knee 포함), tol_V gm/ID 역산 지표 칸,
# LI-1 범위 (2) finger_candidates gm_id READS.
# 호출·import로 잡는 이름 = 역산 함수와 gm/ID 축 곡선 함수.
FUNCS = ("vgs_for_gm_id", "axis_curve", "gm_id_curve", "ft_curve", "intrinsic_gain_curve", "vdsat_curve", "idu_curve",
         "measure_L_knee", "solve_vgs",
         # A-67 W3: gm/ID 축 읽기 본체, gm/ID 목표 역산, 정점(강반전 분지) 경로
         "curve_value", "curve_bundle", "curve_bundle_of", "_at_gm_id", "hull", "gm_id_for_target", "peak_index",
         "monotone_end", "strong_inversion_root", "branch_targets", "ln_idu_floors", "_peak_floor",
         "_conduction_ok", "curve_report")
# 문자열·이름으로 잡는 이름 = 지표 칸·표지.
NAMES = ("gm_id_inverse", "gm_id_inverse_v", "METHOD_INVERSE", "QUANTITY_GM_ID", "TOL_V_METRICS", "rightmost_root",
         "largest_vgs")
# 텍스트로 잡는 칸 읽기(정의 자리 대조용).
GM_ID_READ = re.compile(r"\.gm_id\b|\"gm_id\"|'gm_id'")
# A-67 W3: 정점 계산(argmax)과 gm/ID 좌표 변수. 판정은 손 분류, 새 소비자 키에 든다.
PEAK_TEXT = re.compile(r"argmax\(.*gm_id|\b(r_peak|at_peak|peak)\b")
GM_COORD_TEXT = re.compile(r"\bgm_id_(lo|hi|cap)\b|\bgm_id\[")


def rel(root, p):
    return p.relative_to(root).as_posix()


def scan(root, path):
    src = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src)
    parents = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            parents[c] = n

    def enclosing(n):
        while n in parents:
            n = parents[n]
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                return n.name
        return "<module>"

    lines = src.splitlines()
    for n in ast.walk(tree):
        kind, name = None, None
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                if a.name in FUNCS or a.name in NAMES:
                    yield dict(file=rel(root, path), line=n.lineno, how="import", name=a.name, scope=enclosing(n))
            continue
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in FUNCS:
            kind, name = "def", n.name
        elif isinstance(n, ast.Call):
            f = n.func
            callee = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if callee in FUNCS:
                kind, name = "call", callee
        elif isinstance(n, ast.Name) and n.id in FUNCS + NAMES and not isinstance(parents.get(n), ast.Call):
            kind, name = "name", n.id
        elif isinstance(n, ast.Attribute) and n.attr in NAMES:
            kind, name = "attr", n.attr
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in NAMES:
            kind, name = "str", n.value
        if kind:
            yield dict(file=rel(root, path), line=n.lineno, how=kind, name=name, scope=enclosing(n),
                       text=lines[n.lineno - 1].strip()[:150])
    for i, text in enumerate(lines, 1):
        if GM_ID_READ.search(text):
            yield dict(file=rel(root, path), line=i, how="gm_id_field_text", name="gm_id", scope="", text=text.strip()[:150])
        if PEAK_TEXT.search(text):
            yield dict(file=rel(root, path), line=i, how="peak_text", name="peak", scope="", text=text.strip()[:150])
        if GM_COORD_TEXT.search(text):
            yield dict(file=rel(root, path), line=i, how="gm_coord_text", name="gm_id_coord", scope="", text=text.strip()[:150])


def main():
    root, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    jl = out / "consumers.jsonl"
    jl.write_text("", encoding="utf-8")
    rows = []
    failed = []
    for path in sorted(root.rglob("*.py")):
        if "tests" in path.relative_to(root).parts:
            continue
        try:
            found = list(scan(root, path))
        except SyntaxError as exc:
            failed.append((rel(root, path), str(exc)))
            continue
        with jl.open("a", encoding="utf-8") as fh:
            for r in found:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        rows.extend(found)
    by = collections.defaultdict(collections.Counter)
    for r in rows:
        by[r["file"]][r["how"] + ":" + r["name"]] += 1
    with (out / "summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("files=%d rows=%d parse_failed=%s\n" % (len(by), len(rows), failed))
        for f in sorted(by):
            fh.write(f + "\t" + ", ".join("%s=%d" % kv for kv in sorted(by[f].items())) + "\n")
    print((out / "summary.txt").read_text(encoding="utf-8"))


main()
