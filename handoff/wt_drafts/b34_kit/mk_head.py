"""B34 모의 head: gate master 0f23786 SD에 spec card '코드를 바꾸는 것' 표(사이트 1·2·3·11·11b)만 적용(독립 작성)."""
import subprocess
CL = "C:/g123/repo"
SD = "skills/analog-gmid-design/assets/stick_diagram.py"
src = subprocess.run(["git", "-C", CL, "show", "0f23786:" + SD], capture_output=True, check=True).stdout.decode("utf-8")
assert "\r\n" not in src
def rep(old, new, count=1):
    global src
    n = src.count(old)
    assert n == count, (old, n)
    src = src.replace(old, new)
# 사이트 1
rep("""    except ImportError:
        return tuple(None for _ in module_names)
""", """    except ImportError as e:
        raise ImportError(f"analog-grammar skill을 import할 수 없다(탐색 경로 {_ag_path})") from e
""")
# 사이트 2
rep("""    netclass, idioms_mod = _import_analog_grammar("netclass", "idioms")
    if netclass is None:
        return None
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return None
    cls, imp, _assume = netclass.classify_nets(devs, inputs, outputs, biases, feedbacks, clocks)
    role = netclass.assign_roles(devs, cls, imp)
    return idioms_mod.match_all(devs, cls, imp, role)
""", """    netclass, idioms_mod = _import_analog_grammar("netclass", "idioms")
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return None
    cls, imp, _assume = netclass.classify_nets(devs, inputs, outputs, biases, feedbacks, clocks)
    role = netclass.assign_roles(devs, cls, imp)
    return idioms_mod.match_all(devs, cls, imp, role)
""")
# 사이트 3
rep("""    (netclass,) = _import_analog_grammar("netclass")
    if netclass is None:
        return None
    devs = _to_analog_grammar_devs(transistors)
""", """    (netclass,) = _import_analog_grammar("netclass")
    devs = _to_analog_grammar_devs(transistors)
""")
# 사이트 11, 11b
rep("""    netclass_mod, idioms_mod = _import_analog_grammar("netclass", "idioms")
    if netclass_mod is None or idioms_mod is None:
        return []
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return []
    matches = find_idiom_matches(transistors, inputs, outputs, feedbacks, biases, clocks)
    if matches is None:
        return []
""", """    netclass_mod, idioms_mod = _import_analog_grammar("netclass", "idioms")
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return []
    matches = find_idiom_matches(transistors, inputs, outputs, feedbacks, biases, clocks)
""")
open(CL + "/" + SD, "w", encoding="utf-8", newline="\n").write(src)
print("ok")
