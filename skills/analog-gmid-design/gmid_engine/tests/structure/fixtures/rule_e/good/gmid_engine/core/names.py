def entry(device, nets):
    """드레인·게이트·소스 넷을 선언에서 읽는다(이름은 값으로만)."""
    if device["kind"] not in ("nmos", "pmos"):
        raise ValueError("unknown kind: %s" % device["kind"])
    return nets[device["drain"]], nets["supply_nets"], f"{device['name']}_row"
