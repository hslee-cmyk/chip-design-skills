"""b26pre v2 -- C:/g106/b34 = C:/g106/base(git archive a796468) 사본 + B34 코드 변경(사이트 1·2·3·11·11b).
치환 규칙은 _drafts/b26pre_scripts/v3_scope_classify.build_b34와 같다(def 범위 안 정확 1회 치환).
전제: C:/g106/base가 이미 있다(`git -C <repo> archive a796468 | tar -x -C C:/g106/base`)."""
import ast, os, shutil

BASE, B34 = "C:/g106/base", "C:/g106/b34"
SD = "skills/analog-gmid-design/assets/stick_diagram.py"


def defs(tree, prefix=""):
    for n in ast.iter_child_nodes(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            q = prefix + n.name
            yield q, n
            yield from defs(n, q + ".")


def def_replace(src, qual, old, new):
    fn = dict(defs(ast.parse(src)))[qual]
    lines = src.split("\n")
    seg = "\n".join(lines[fn.lineno - 1:fn.end_lineno])
    assert seg.count(old) == 1, (qual, seg.count(old))
    return "\n".join(lines[:fn.lineno - 1] + seg.replace(old, new).split("\n") + lines[fn.end_lineno:])


if not os.path.exists(B34):
    shutil.copytree(BASE, B34)
src = open(os.path.join(BASE, SD), encoding="utf-8").read()
src = def_replace(src, "_import_analog_grammar", "    except ImportError:\n        return tuple(None for _ in module_names)",
                  "    except ImportError as e:\n        raise ImportError(\"analog-grammar skill을 import할 수 없다(탐색 경로 %s)\" % _ag_path) from e")
src = def_replace(src, "find_idiom_matches", "    if netclass is None:\n        return None\n", "")
src = def_replace(src, "find_stack_edges", "    if netclass is None:\n        return None\n", "")
src = def_replace(src, "audit_theta_root_direction", "    if netclass_mod is None or idioms_mod is None:\n        return []\n", "")
src = def_replace(src, "audit_theta_root_direction", "    if matches is None:\n        return []\n", "")
ast.parse(src)
with open(os.path.join(B34, SD), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(src)
print("b34 written")
