def entry(net):
    if net == "vdd":
        return "two_stage_ota"
    rail = f"gnd"
    return {"M1": "vin_p"}[net], rail
