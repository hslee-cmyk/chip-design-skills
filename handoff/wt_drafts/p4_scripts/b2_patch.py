"""Phase 4 design v0.4 B2 측정 -- #50 red 형태 결정용 원점 이동 시뮬레이션 패처.

HEAD(7535799) 사본의 sizing_recipe.py를 C:/g61/sim 사본에서 고친다(저장소 쓰기 0).
환경변수 P4_SIM 이 비어 있으면 원 코드와 같은 값(S_A). 모드:
  S1  : #21을 '뜻대로' 분류한 원점 이동 -- 노드전압 프레임(propagate/derive_vsb의 vdd 인자, 8652)은 폭(span)=1.8,
        절대 전위 읽기(4626·4653·10157~10160)는 hi=0.9 / lo=-0.9. rail_lo 고정 0.0 그대로(#17·#22 전).
  S2  : #21이 노드전압 프레임 인자를 hi(0.9)로 잘못 분류한 경우(rail_lo 고정 0.0 그대로).
  S3  : 레일을 선언 전위로 고정(rail_hi=0.9, rail_lo=-0.9)했지만 DF-24 vsb 식(nmos = V(source))은 그대로인 경우
        (= #22가 고정만 바꾸고 vsb 식을 안 고친 부분 수정 / '레일 0 V 가정'이 남은 엔진).
P4_AXIS=raise 이면 LUT 보간에서 VS 축 밖 점을 ValueError('lut_axis_out_of_range')로(DF-27 #25 상당).
P4_AXIS=count 이면 VS 축 밖 조회 수만 센다(_P4_AXIS_LOG).
폭(span) 읽기(1729·3254·7068·7222·7228·8233·8277)는 spec['vdd']=1.8 그대로 -- 두 선언 모두 폭 1.8.
"""
import re
import shutil
import sys
from pathlib import Path

SRC = Path("C:/g61/repo")
DST = Path("C:/g61/sim")

if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)
p = DST / "skills/analog-gmid-design/assets/sizing_recipe.py"
lines = p.read_text(encoding="utf-8").split("\n")

def sub(lineno, old, new):
    i = lineno - 1
    assert old in lines[i], (lineno, lines[i])
    lines[i] = lines[i].replace(old, new)

# 노드전압 프레임 인자
sub(7295, 'spec["vdd"]', '_p4_v(spec, "node")')
sub(7296, 'spec["vdd"]', '_p4_v(spec, "node")')
sub(7449, 'spec["vdd"]', '_p4_v(spec, "node")')
sub(7450, 'spec["vdd"]', '_p4_v(spec, "node")')
sub(8652, 'spec.get("vdd")', '_p4_v(spec, "node")')
# 절대 전위 읽기
sub(4626, 'ctx.spec["vdd"] if spec["rail"] == "vdd" else 0.0',
    '_p4_v(ctx.spec, "hi") if spec["rail"] == "vdd" else _p4_v(ctx.spec, "lo")')
sub(4653, 'ctx.spec["vdd"]', '_p4_v(ctx.spec, "center")')
sub(10157, 'spec["vdd"] - vgs_h', '_p4_v(spec, "hi") - vgs_h')
sub(10157, '(0.0 + vgs_h)', '(_p4_v(spec, "lo") + vgs_h)')
sub(10159, 'spec["vdd"] - vgs_l', '_p4_v(spec, "hi") - vgs_l')
sub(10159, '(0.0 + vgs_l)', '(_p4_v(spec, "lo") + vgs_l)')
sub(10160, 'spec["vdd"]', '_p4_v(spec, "center")')
# rail_lo 고정
sub(3756, 'nodes[n] = 0.0', 'nodes[n] = _p4_lo_pin()')

helper = '''
import os as _p4_os
_P4_AXIS_LOG = []
def _p4_mode():
    return _p4_os.environ.get("P4_SIM", "")
def _p4_v(spec, kind):
    m = _p4_mode()
    if not m:
        if kind == "lo":
            return 0.0
        return spec.get("vdd") if kind == "node" else spec["vdd"]
    hi, lo = 0.9, -0.9
    if kind == "node":
        return spec.get("vdd") if m == "S1" else hi
    if kind == "hi":
        return hi
    if kind == "lo":
        return lo
    if kind == "center":
        return hi + lo
    raise KeyError(kind)
def _p4_lo_pin():
    return -0.9 if _p4_mode() == "S3" else 0.0
def _p4_axis_check(grids, pt):
    mode = _p4_os.environ.get("P4_AXIS", "")
    if not mode:
        return
    vs = pt[3]
    g = grids[3]
    lo, hi = (g[0], g[-1])
    if vs < lo - 1e-12 or vs > hi + 1e-12:
        _P4_AXIS_LOG.append(float(vs))
        if mode == "raise":
            raise ValueError(f"lut_axis_out_of_range(sim): vsb={vs!r} outside [{lo}, {hi}]")
'''
# helper를 import 블록 뒤(numpy import 줄 뒤)에 넣는다
idx = next(i for i, l in enumerate(lines) if l.startswith("import numpy as np"))
lines.insert(idx + 1, helper)
text = "\n".join(lines)

# 보간 두 함수 입구에 축 검사
def inject(fn_sig, pts_expr):
    global text
    m = re.search(r"^def " + re.escape(fn_sig) + r"\(.*?\n    \"\"\".*?\"\"\"\n", text, re.S | re.M)
    assert m, fn_sig
    ins = f"    for _p4_pt in ({pts_expr}):\n        _p4_axis_check([list(g) for g in grids], list(_p4_pt))\n"
    text = text[:m.end()] + ins + text[m.end():]

inject("_multilinear_interp", "points.tolist() if hasattr(points, 'tolist') else (points if points and hasattr(points[0], '__len__') else [points])")
inject("_multilinear_interp_point_multi", "[point]")
p.write_text(text, encoding="utf-8")
print("patched", p)
