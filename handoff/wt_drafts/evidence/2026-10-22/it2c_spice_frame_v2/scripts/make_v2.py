"""v1 스크립트에서 v2 사본을 만든다(v1 파일은 그대로 둔다)."""
from pathlib import Path

D = Path(__file__).parent
s = (D / "spice_follow.py").read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert a in s, a
    s = s.replace(a, b)


rep('"""IT-2c SPICE 틀 판정 -- SPICE 쪽.', '''"""IT-2c SPICE 틀 판정 v2 -- SPICE 쪽 (v1 결함 수정: v1 은 w_key 를 nm 로 읽어 1 um finger 로 만들었다).

v2 기하: finger 폭 = 엔진 LUT 정본 필드 slice_map[(kind, w_key)].w_m (out_v2/slice_wm.json, slice_wm.py 가 엔진에서 읽음),
m = W / w_m (실수 배수, 진단 전용 -- 엔진 모형 'w_m 슬라이스 전류밀도 x W' 를 넷리스트로 그대로 옮김).
오라클 스키마는 n_fingers 정수라 convert·write_netlists 에는 n = max(1, round(W/w_m)) 를 넘기고, 쓴 넷리스트의 MOS 행 m= 만
실수 W/w_m 으로 바꾼다(그 밖의 본문·확산 기하(ad/as/pd/ps = finger 폭 규칙)는 오라클 경로 출력 그대로).
---- 이하 v1 설명''')
rep('OUT = ROOT / "out"\nSP = ROOT / "spice"',
    'ENG_DIR = ROOT / "out"\nOUT = ROOT / "out_v2"\nSP = ROOT / "spice_v2"\nWM = json.loads((OUT / "slice_wm.json").read_text(encoding="utf-8"))')
rep('''        W, wk = op["W"], op["w_key"] * 1e-9
        n = max(1, math.floor(W / wk))
        inst.append({"name": m, "w": W, "n_fingers": n, "finger_w": W / n, "l": op["L"]})''',
    '''        W, wm = op["W"], WM[name][m]["w_m"]
        n = max(1, round(W / wm))
        inst.append({"name": m, "w": W, "n_fingers": n, "finger_w": wm, "l": op["L"]})''')
rep('''    eng = json.loads((OUT / (name + ".engine.json")).read_text(encoding="utf-8"))''',
    '''    eng = json.loads((ENG_DIR / (name + ".engine.json")).read_text(encoding="utf-8"))''')
rep('''    text = cir.read_text(encoding="utf-8")''', r'''    text = cir.read_text(encoding="utf-8")
    # v2: MOS 행 m= 를 실수 W / w_m 으로 (진단 전용)
    import re
    ops = eng["device_cols"]["dc_op"]
    patched, new = [], []
    for ln in text.splitlines():
        mm = re.match(r"^X(\S+) (.*) m=(\d+)( .*)?$", ln)
        if mm and mm.group(1) in ops:
            mreal = ops[mm.group(1)]["W"] / WM[name][mm.group(1)]["w_m"]
            ln = f"X{mm.group(1)} {mm.group(2)} m={mreal:.12g}{mm.group(4) or ''}"
            patched.append((mm.group(1), int(mm.group(3)), mreal))
        new.append(ln)
    text = "\n".join(new) + "\n"
    (SP / (name + ".free.mreal.cir")).write_text(text, encoding="utf-8")
    info["m_patch"] = patched
    if len(patched) != len(ops):
        info["stop"] = f"m 패치 수 {len(patched)} != MOS 수 {len(ops)}"
        (OUT / (name + ".spice_info.json")).write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
        return''')
(D / "spice_follow_v2.py").write_text(s, encoding="utf-8")

OLD = 'OUT = Path(r"C:\\Users\\HSLEE\\Documents\\Todoc\\fpga\\wt\\_scratch_it2c_spice\\out")'
NEW = ('OUT = Path(r"C:\\Users\\HSLEE\\Documents\\Todoc\\fpga\\wt\\_scratch_it2c_spice\\out_v2")\n'
       'ENG_DIR = Path(r"C:\\Users\\HSLEE\\Documents\\Todoc\\fpga\\wt\\_scratch_it2c_spice\\out")')
for f in ("analyze", "summarize"):
    t = (D / f"{f}.py").read_text(encoding="utf-8")
    assert OLD in t
    t = t.replace(OLD, NEW)
    t = t.replace('(OUT / f"{name}.engine.json")', '(ENG_DIR / f"{name}.engine.json")')
    t = t.replace('(OUT / f"{n}.engine.json")', '(ENG_DIR / f"{n}.engine.json")')
    t = t.replace('(OUT / "tol_tables.json")', '(ENG_DIR / "tol_tables.json")')
    (D / f"{f}_v2.py").write_text(t, encoding="utf-8")
print("ok")
