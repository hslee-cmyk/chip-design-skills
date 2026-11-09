"""변형 확인: review2의 own 314·deep 336과 범위 card 규칙(v3_scope_widen, 바꾸는 이름 ⓐ~ⓓ) 차이의 원인 찾기.
변형 A = '바꾸는 이름'을 Name(Store/Del)·except 이름만(ⓑ 속성·첨자 대입 대상, ⓒ 메서드 호출 수신자 제외)."""
import ast, sys
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_scripts")
import b26v4_classify as C
W = C.W
_orig = W.mod_names


def mod_names_A(node, own_only=False):
    out = set()
    for r in W._roots(node, own_only):
        for x in ast.walk(r):
            if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del)):
                out.add(x.id)
    if isinstance(node, ast.ExceptHandler) and node.name:
        out.add(node.name)
    return out


def mod_names_B(node, own_only=False):
    """ⓐ+ⓑ만(메서드 수신자 제외)."""
    out = set()
    for r in W._roots(node, own_only):
        for x in ast.walk(r):
            if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del)):
                out.add(x.id)
            elif isinstance(x, (ast.Attribute, ast.Subscript)) and isinstance(x.ctx, (ast.Store, ast.Del)):
                r0 = W._root(x)
                if r0:
                    out.add(r0)
    if isinstance(node, ast.ExceptHandler) and node.name:
        out.add(node.name)
    return out


if __name__ == "__main__":
    import builtins
    for tag, f in (("A_name_only", mod_names_A), ("B_no_method_receiver", mod_names_B)):
        W.mod_names = f
        C.TAG = "var_%s_" % tag
        C.main("review2")
    W.mod_names = _orig
