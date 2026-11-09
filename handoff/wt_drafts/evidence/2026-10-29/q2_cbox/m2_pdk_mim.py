"""q2_cbox m2: PDK 선언에서 최소 MIM 용량과 면적 예산이 주는 C 상한 계산 (읽기 전용, 값 하드코딩 없음 -- 파일에서 파싱).
입력:
  - C:/pdk/sky130_fd_pr/models/r+c/res_*__cap_*__lin.spice 7·8행 camimc·cpmimc (로컬)
  - capm.1 최소 폭: 로컬 periphery.csv 745행 = N/A -> 로컬 원본 없음. 원격 사실(open_pdks sky130.tech
    'width *mimcap 1000 "MiM cap width < %d (capm.1)"', magic 단위 nm)을 인자로 받아 계산만 한다(로컬 PDK 선언 아님).
  - 13 spec area_search_m2 (저장소)
식: C(W,L) = camimc*W*L + cpmimc*2*(W+L)  (cap_mim_m3_1 셀 모델 .param carea/cperim; 셀 원본은 로컬 없음, 원격 확인)
    C_min = C(w_min, w_min)
    C_max(area) = area_search_m2 * camimc(F/m^2)  (MOS 면적 0 가정 = 느슨한 위쪽 경계; 둘레 항 무시)
출력: m2_pdk_mim.txt
"""
import glob, json, pathlib, re

OUT = pathlib.Path(__file__).with_suffix(".txt")
OUT.write_text("", encoding="utf-8")
PDK = pathlib.Path(r"C:/pdk/sky130_fd_pr/models/r+c")
A = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets")
W_MIN_UM_REMOTE = 1000 / 1000.0   # open_pdks sky130.tech capm.1 '1000' (nm) -> um; 원격 사실, 로컬 선언 아님


def emit(s):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(s + "\n")


def param(path, key):
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = re.match(r"^\+\s*%s\s*=\s*([0-9.eE+-]+)" % key, line)
        if m:
            return float(m.group(1)), i
    raise KeyError(key)


emit("== 최소 MIM 용량 (capm.1 w_min = %.3f um, 정사각 1개, MF=1) ==" % W_MIN_UM_REMOTE)
corners = {}
for f in sorted(PDK.glob("res_*__cap_*__lin.spice")):
    ca, la = param(f, "camimc")
    cp, lp = param(f, "cpmimc")
    w = W_MIN_UM_REMOTE
    c = ca * w * w + cp * 2 * (w + w)
    corners[f.name] = (ca, cp, c)
    emit(f"{f.name}: camimc={ca:.4g} F/um^2 (행 {la}), cpmimc={cp:.4g} F/um (행 {lp}) -> C_min = {c*1e15:.3f} fF "
         f"(면적항 {ca*w*w*1e15:.3f} + 둘레항 {cp*4*w*1e15:.3f}, 둘레 몫 {cp*4*w/c:.0%})")
ca_tt = corners["res_typical__cap_typical__lin.spice"][0]
cp_tt = corners["res_typical__cap_typical__lin.spice"][1]
c_tt = corners["res_typical__cap_typical__lin.spice"][2]
emit(f"box 하한 0.1 pF / C_min(tt) = {1e-13/c_tt:.1f} 배")
# 0.1 pF 정사각 변
import math
a, b, cc = ca_tt, 4 * cp_tt, -1e-13
w01 = (-b + math.sqrt(b * b - 4 * a * cc)) / (2 * a)
emit(f"0.1 pF 정사각 변 = {w01:.2f} um (면적 {w01*w01:.1f} um^2); 면적만 식(C/camimc) = {1e-13/ca_tt:.1f} um^2 -> 둘레 무시 오차 {(1e-13/ca_tt)/(w01*w01)-1:+.1%}")
emit(f"C_min(tt)를 면적만 식으로 환산한 면적 = {c_tt/ca_tt:.2f} um^2 vs 실제 {W_MIN_UM_REMOTE**2:.2f} um^2 ({(c_tt/ca_tt)/W_MIN_UM_REMOTE**2-1:+.0%})")
emit("")
emit("== 면적 예산이 주는 C 상한 (area_search_m2 x camimc_tt; MOS 면적 0 가정 느슨한 경계) ==")
for spec in sorted(glob.glob(str(A / "library/*.sizing_spec.json")) + glob.glob(str(A / "heldout/*.sizing_spec.json"))):
    s = json.loads(pathlib.Path(spec).read_text(encoding="utf-8"))
    ar = [c["value"] for c in s["human"].get("constraints", []) if c.get("metric") == "area_search_m2"]
    tb = (s["human"].get("search") or {}).get("theta_bounds") or {}
    caps = [k for k, v in tb.items() if isinstance(v, dict) and v.get("max", 1) < 1e-6]
    name = pathlib.Path(spec).name.replace(".sizing_spec.json", "")
    if ar:
        cmax = ar[0] * ca_tt * 1e12
        emit(f"{name:32s} area={ar[0]:.3g} m^2 -> C_max(전 면적 C) = {cmax*1e12:.1f} pF ; θ C 상자 {caps or '-'} 상한 10 pF 대비 {cmax/1e-11:.2f} 배")
    else:
        emit(f"{name:32s} area 제약 없음 -> 면적 상한 유도 불가 ; θ C 상자 {caps or '-'}")
