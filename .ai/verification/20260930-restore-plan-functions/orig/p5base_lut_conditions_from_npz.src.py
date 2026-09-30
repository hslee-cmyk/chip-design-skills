def lut_conditions_from_npz(npz_data) -> dict:
    """LUT npz가 들고 있는 **측정 조건**(코너/온도)을 읽어 돌려준다(2026-09-08, A5).

    사이징 결과는 LUT이 뽑힌 조건에서만 유효한데, 그 조건이 파일에 기록돼 있지 않으면
    산출물이 "이 설계가 어디서 유효한가"를 말할 수 없다. 기록이 없으면 **조용히 기본값을
    가정하지 않고** `recorded=False`로 그 사실 자체를 돌려준다(§3.2 P1).

    `sky130_lut_sweep.py`는 2026-09-08부터 `corner`/`temp_c`를 함께 저장한다. 그 이전에
    만들어진 npz(예: 저장소의 `sky130_nfet_pfet_lut_sample.npz`)에는 기록이 없다 -- 생성기
    코드상 tt/27C인 것은 알지만, **파일이 스스로 말하지 않는 값을 엔진이 대신 지어내지는
    않는다**. 재생성하면 기록된다."""
    files = set(getattr(npz_data, "files", []) or [])
    if "corner" in files or "temp_c" in files:
        out = {"recorded": True}
        if "corner" in files:
            out["corner"] = str(npz_data["corner"])
        if "temp_c" in files:
            out["temp_c"] = float(npz_data["temp_c"])
        return out
    return {"recorded": False,
            "note": "이 LUT 파일에 코너/온도가 기록돼 있지 않다 -- 사이징 결과가 어느 조건에서 "
                    "유효한지 추적할 수 없다. sky130_lut_sweep.py로 재생성하면 기록된다(A5)."}
