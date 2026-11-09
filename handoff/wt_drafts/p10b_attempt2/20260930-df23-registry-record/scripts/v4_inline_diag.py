"""V4 (2) 진단(auditor 실험, 판정 기록 근거 보조): 새 test가 피검 check_df23을 helper `_p10b_check`로 감싸 부르므로
test_lint (2)가 판정 문장에서 피검을 보지 못한다(NO-SUBJECT). helper 호출을 그 정의대로 직접 호출
`check_df23(text, inv 또는 _p10b_inventory(), rel 또는 _P10B_INV_REL)`로 AST 치환한 사본을 만들어
같은 base 판 test_lint로 돌려, 감싸지 않았다면 (2)가 무엇을 냈을지 잰다. 사본은 C:/g88/v4diag(병합본 복제본 사본) 안에만 쓴다.

사용: python v4_inline_diag.py <병합본 복제본 사본 루트>
"""
import ast
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
tf = root / "skills/analog-gmid-design/assets/tests/contracts/test_reg_check_df23.py"
src = tf.read_text(encoding="utf-8")
tree = ast.parse(src)


class R(ast.NodeTransformer):
    n = 0

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "_p10b_check":
            args = list(node.args)
            kw = {k.arg: k.value for k in node.keywords}
            text = args[0]
            inv = args[1] if len(args) > 1 else kw.get("inv")
            rel = args[2] if len(args) > 2 else kw.get("rel")
            if inv is None or (isinstance(inv, ast.Constant) and inv.value is None):
                inv = ast.Call(func=ast.Name("_p10b_inventory", ast.Load()), args=[], keywords=[])
            if rel is None:
                rel = ast.Name("_P10B_INV_REL", ast.Load())
            R.n += 1
            return ast.Call(func=ast.Name("check_df23", ast.Load()), args=[text, inv, rel], keywords=[])
        return node


new = ast.fix_missing_locations(R().visit(tree))
tf.write_text(ast.unparse(new) + "\n", encoding="utf-8")
print("replaced", R.n)
