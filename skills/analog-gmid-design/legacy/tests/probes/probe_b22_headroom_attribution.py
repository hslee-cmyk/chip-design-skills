# -*- coding: utf-8 -*-
"""B22(미러 인식 diode 창) 적용 후 파일럿이 infeasible한 **원인을 귀속**하는 조사 도구
(2026-09-09).

## 배경

미러 15소자에 `gm_id_match_vgs_of`를 선언하고(B19' 배선) `diode_vds_window()`를 미러
인식하게 고친(B22) 뒤 SLSQP 3 start가 전부 실패했다. 그런데 **실패 사유가 미러가 아니다**:

    'biasgen_vom_floatsrc_sink' 그룹(예산 -0.0239609V, 미해결 ['M9b'])

M9b는 미러 소자가 아니고, 이 오류는 배선 전에도 중점 theta에서 나왔다. 그러나 B20
재탐색(미배선)은 성공했으므로, **B22가 diode의 `lo`를 올려 헤드룸을 더 먹은 것이
이 스택을 음수로 밀었는지**를 가려야 한다.

## 방법 -- 같은 theta에서 세 가지를 나란히 돌린다

    (a) 미배선            : device_roles에 gm_id_match_vgs_of 없음
    (b) 배선 + B22 끔      : 선언은 있으나 창은 diode 자신만 본다(mirror_members=())
    (c) 배선 + B22 켬      : 현재 구현

(a)와 (b)가 같고 (c)만 다르면 원인은 B22의 창 상향이다. (b)부터 이미 실패하면 원인은
미러 gm_id 강제 자체다. 셋 다 실패하면 theta 자체가 나쁜 것이다.

**아무것도 고치지 않는다** -- 재기만 한다. 결과는 파일에도 남긴다.

실행: assets 디렉터리에서 `python tests/probe_b22_headroom_attribution.py`
"""
import sys
import os
import json
import copy

ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "workspaces"))
import numpy as np
import sizing_recipe as sr
import run_harness as H

_RESULT_PATH = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first_emit = [True]


def emit(*parts):
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    mode = "w" if _first_emit[0] else "a"
    _first_emit[0] = False
    with open(_RESULT_PATH, mode, encoding="utf-8") as _f:
        _f.write(line + "\n")


TOPO = os.path.join(ASSETS, "..", "assets", "library", "current_reuse_telescopic_ota.topology.json")
d = np.load(os.path.join(ASSETS, "..", "assets", "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])


def make_spec():
    """정본 spec을 준다(2026-09-10 -- 손으로 복붙한 블록을 폐기).

    복제본은 정본과 갈려 있었다(gm_id_grid 21점 vs 57점, L_candidates 12점 vs 41점,
    VDS_candidates 9점 vs 13점, stage_power_tolerance 누락). 이 스크립트는 헤드룸
    귀속을 재는 것이라 해상도가 결과를 바꾼다 -- 정본을 써야 한다.
    """
    return H.canonical_spec("current_reuse_telescopic_ota")


topo_wired = json.load(open(TOPO, encoding="utf-8"))
n_wired = sum(1 for v in topo_wired["device_roles"].values()
              if isinstance(v, dict) and v.get("gm_id_match_vgs_of"))
emit(f"현재 토폴로지의 gm_id_match_vgs_of 선언: {n_wired}개")

# "미배선" 원본은 **git HEAD 버전**을 쓴다. 선언만 벗기면 안 된다 --
# 배선하면서 gm_id_role을 제거했으므로, 그냥 벗기면 두 필드가 다 없는 상태가 되어
# require_device_roles_reviewed() 게이트에 "검토 안 된 제안"으로 걸린다(실측).
import subprocess
import tempfile
_tmp = tempfile.mkdtemp()
P_UNWIRED = os.path.join(_tmp, "unwired.topology.json")
_rel = "skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json"
_repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(ASSETS))))
_blob = subprocess.run(["git", "-C", os.path.join(ASSETS, "..", "..", ".."),
                        "show", "HEAD:" + _rel], capture_output=True)
assert _blob.returncode == 0, _blob.stderr.decode("utf-8", "replace")[:200]
with open(P_UNWIRED, "wb") as f:
    f.write(_blob.stdout)
_chk = json.loads(open(P_UNWIRED, encoding="utf-8").read())
_n_un = sum(1 for v in _chk["device_roles"].values()
            if isinstance(v, dict) and v.get("gm_id_match_vgs_of"))
emit(f"git HEAD 원본(미배선)의 선언: {_n_un}개")

_ORIG_WINDOW = sr.diode_vds_window


def _window_no_mirror(lut, kind, L, ID, vsb, W_bounds, mirror_members=()):
    """B22를 끈 버전 -- 멤버를 무시하고 diode 자신만 본다(수정 전 동작)."""
    return _ORIG_WINDOW(lut, kind, L, ID, vsb, W_bounds, ())


def run_case(tag, topo_path, b22_on):
    sr.diode_vds_window = _ORIG_WINDOW if b22_on else _window_no_mirror
    try:
        spec = make_spec()
        env = sr._build_theta_evaluator(topo_path, spec)
        ctx, metrics = env["evaluate"](dict(THETA))
        emit(f"  [{tag}] 성공 -- gain_db={metrics.get('gain_db', float('nan')):.4f}, "
             f"area_um2={metrics.get('area_um2', float('nan')):.2f}")
        return ctx, None
    except Exception as e:
        emit(f"  [{tag}] 실패 -- {type(e).__name__}: {str(e)[:170]}")
        return None, e
    finally:
        sr.diode_vds_window = _ORIG_WINDOW


# ── theta 선택 ────────────────────────────────────────────────────────────────
# bounds 중점은 **배선과 무관하게** infeasible임이 실측으로 확인됐다(세 경우가 바이트
# 단위로 같은 오류). 그 점에서는 실험이 아무것도 가르지 못한다. 그래서 **미배선에서
# 실제로 성립하는 최적점**을 구해 그 점에서 셋을 비교한다 -- 그래야 "배선/B22가
# 멀쩡하던 점을 깨뜨리는가"라는 질문에 답할 수 있다.
THETA_CACHE = os.path.splitext(os.path.abspath(__file__))[0] + ".unwired_theta.json"
if os.path.exists(THETA_CACHE):
    THETA = json.load(open(THETA_CACHE, encoding="utf-8"))
    emit(f"[캐시] 미배선 최적 theta 재사용 ({len(THETA)}개)")
else:
    emit("[신규] 미배선 최적 theta를 SLSQP로 구한다(수 분)...")
    _r = sr.optimize_full_circuit_budget(P_UNWIRED, make_spec(), search_method="slsqp",
                                         slsqp_kwargs={"n_starts": 1, "maxiter": 40})
    THETA = {k: float(v) for k, v in (_r["theta_star"] or {}).items()}
    json.dump(THETA, open(THETA_CACHE, "w", encoding="utf-8"), indent=1)
    emit(f"[신규] 확보 ({len(THETA)}개). 이 점의 gain_db="
         f"{_r['metrics'].get('gain_db', float('nan')):.4f}")

emit("")
emit("=" * 96)
emit("**미배선 최적점**에서 세 경우를 나란히 평가")
emit("=" * 96)
emit("")
ctx_a, err_a = run_case("a) 미배선          ", P_UNWIRED, True)
ctx_b, err_b = run_case("b) 배선 + B22 끔   ", TOPO, False)
ctx_c, err_c = run_case("c) 배선 + B22 켬   ", TOPO, True)

emit("")
emit("=" * 96)
emit("귀속")
emit("=" * 96)
emit("")
same_ab = (err_a is None) == (err_b is None) and (
    err_a is None or str(err_a)[:80] == str(err_b)[:80])
if err_a is None and err_b is None and err_c is not None:
    emit("  -> 원인은 **B22의 창 상향**이다. 미러 gm_id 강제만으로는 통과한다.")
elif err_a is None and err_b is not None:
    emit("  -> 원인은 **미러 gm_id 강제 자체**다(B22 이전 단계).")
elif err_a is not None:
    emit("  -> 이 theta는 **배선과 무관하게** 이미 infeasible이다 -- 세 경우를 가르는")
    emit("     실험이 성립하지 않는다. 다른 theta(최적점)로 다시 재야 한다.")
else:
    emit("  -> 세 경우 전부 통과. 이 theta에서는 아무것도 막지 않는다.")
emit(f"     (a)와 (b)가 같은 결과인가: {same_ab}")

emit("")
emit("완료. 결과 파일:", _RESULT_PATH)
