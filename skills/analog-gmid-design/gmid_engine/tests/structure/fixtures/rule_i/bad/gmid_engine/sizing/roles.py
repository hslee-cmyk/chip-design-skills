def pick(doc, dev, roles, spec):
    tagged = doc["device_roles"]
    fg = roles.get("fold_group")
    if "headroom_role" in roles:
        spec = getattr(dev, "L_role")
    match roles:
        case {"gm_id_role": value}:
            spec = value
    return tagged, fg, dev.vertical_stack_id, spec
