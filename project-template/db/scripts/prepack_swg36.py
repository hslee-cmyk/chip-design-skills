# prepack_swg36.py — SWG36 패키지 IO 배치 (nextpnr --pre-pack)
#
# iCE5LP4K-SWG36 패키지는 오픈소스 chipdb(sg48)에 없으므로,
# SG48에 존재하는 IO tile만 배치하고 나머지는 자동 배치.
#
# 출처: venezia_io_pcf.log (iCEcube2 packer output)

# SWG36 ball → (tile_x, tile_y, io_block) 매핑 (iCEcube2 보고서)
# SG48 chipdb에 존재 여부 표시
SWG36_TO_SG48 = {
    # ball: (tile_x, tile_y, block, sg48_pin_or_None)
    "A2": (21, 21, 0, None),   # topBank LED — SG48에 없음
    "B1": (20,  0, 0, None),   # SG48에 없음
    "B2": (22,  0, 1, 18),     # SG48 pin 18
    "B4": (12,  0, 0, None),   # SG48에 없음 (12,0,0)
    "D2": (20,  0, 1, None),   # SG48에 없음
    "D5": ( 7,  0, 1, 45),     # SG48 pin 45
    "D6": ( 7,  0, 0, 48),     # SG48 pin 48
    "E2": (21,  0, 1, 19),     # SG48 pin 19
    "E3": (17,  0, 0, 11),     # SG48 pin 11
    "E5": ( 8,  0, 1, None),   # SG48에 없음 (8,0,1)
    "E6": ( 6,  0, 1, 44),     # SG48 pin 44
    "F3": (15,  0, 0, 9),      # SG48 pin 9
    "F4": (12,  0, 1, None),   # SG48에 없음 (12,0,1)
    "F5": ( 8,  0, 0, 2),      # SG48 pin 2
    "F6": ( 6,  0, 0, 47),     # SG48 pin 47
}

# PCF signal → ball 매핑
PCF_MAP = {
    "i_earpiece_det_n": "E2",
    "i_pcmSync":        "E3",
    "i_sdaIn":          "F6",
    "o_backTel_pwr_en": "E5",
    "o_serial_tp_out":  "D6",
    "i_pcmIn":          "F5",
    "i_scl":            "D2",
    "o_askData":        "B4",
    "i_backTel_p":      "E6",
    "i_deep_slp_en":    "F3",
    "i_dyn_slp_en":     "D5",
    "i_rst_n":          "B1",
    "o_refClk":         "B2",
    "o_sdaOut":         "A2",
    "o_refClkInv":      "F4",
}

constrained = 0
skipped = 0

for sig_name, ball in PCF_MAP.items():
    if ball not in SWG36_TO_SG48:
        continue
    tx, ty, tb, sg48_pin = SWG36_TO_SG48[ball]
    if sg48_pin is None:
        # SG48에 없는 IO tile → 자동 배치
        skipped += 1
        continue
    bel = f"X{tx}/Y{ty}/io{tb}"
    for cell_name, cell in ctx.cells:
        if sig_name in cell_name:
            cell.setAttr("BEL", bel)
            constrained += 1
            break

print(f"SWG36 pre-pack: {constrained} constrained, {skipped} auto-placed (SG48 incompatible)")
