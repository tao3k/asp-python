from __future__ import annotations

import ast


def _args(args: ast.arguments) -> str:
    return _expr(args)


def _targets(targets: list[ast.expr]) -> str:
    return ", ".join(_expr(target) for target in targets)


def _with_items(items: list[ast.withitem]) -> str:
    rendered: list[str] = []
    for item in items:
        optional = (
            f" as {_expr(item.optional_vars)}" if item.optional_vars is not None else ""
        )
        rendered.append(f"{_expr(item.context_expr)}{optional}")
    return ", ".join(rendered)


def _aug_assign_stmt(node: ast.AugAssign) -> str:
    return f"{_expr(node.target)} {_aug_operator(node.op)}= {_expr(node.value)}"


def _import_stmt(node: ast.Import | ast.ImportFrom) -> str:
    if isinstance(node, ast.Import):
        return "import " + ", ".join(alias.name for alias in node.names)
    module = "." * node.level + (node.module or "")
    return f"from {module} import " + ", ".join(alias.name for alias in node.names)


def _expr(node: ast.AST | None) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Dict):
        return _dict_expr(node)
    if isinstance(node, ast.List):
        return _list_expr(node)
    if isinstance(node, ast.Tuple):
        return _tuple_expr(node)
    if isinstance(node, ast.JoinedStr):
        return "template"
    if isinstance(node, ast.Call):
        return _call_expr(node)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return "string"
        if isinstance(node.value, bytes):
            return "bytes"
    try:
        text = ast.unparse(node)
    except Exception:
        text = node.__class__.__name__
    return _limit_expr(" ".join(text.split()))


def _list_expr(node: ast.List) -> str:
    return _sequence_expr("list", node.elts)


def _tuple_expr(node: ast.Tuple) -> str:
    return _sequence_expr("tuple", node.elts)


def _sequence_expr(kind: str, items: list[ast.expr]) -> str:
    rendered = ",".join(_list_item_expr(item) for item in items[:3])
    if rendered == "":
        return f"{kind}[{len(items)}]"
    return f"{kind}[{len(items)}] items={rendered}"


def _list_item_expr(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        return _call_expr(node)
    if isinstance(node, ast.Dict | ast.List | ast.Tuple):
        return _limit_expr(_expr(node), max_chars=72)
    try:
        text = ast.unparse(node)
    except Exception:
        text = node.__class__.__name__
    return _limit_expr(" ".join(text.split()), max_chars=40)


def _dict_expr(node: ast.Dict) -> str:
    pairs = [
        _dict_item_expr(key, value)
        for key, value in zip(node.keys, node.values, strict=False)
    ][:4]
    if not pairs:
        return f"dict[{len(node.keys)}]"
    remaining_keys = [
        _dict_key_expr(key) if key is not None else "**"
        for key in node.keys[len(pairs) :]
    ]
    if remaining_keys:
        key_suffix = ",..." if len(remaining_keys) > 6 else ""
        pairs.append(f"keys={','.join(remaining_keys[:6])}{key_suffix}")
    return f"dict[{len(node.keys)}] {' '.join(pairs)}"


def _dict_item_expr(key: ast.AST | None, value: ast.AST) -> str:
    if key is None:
        return f"**{_dict_value_expr(value)}"
    return f"{_dict_key_expr(key)}={_dict_value_expr(value)}"


def _dict_key_expr(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return _limit_expr(node.value, max_chars=32)
    return _limit_expr(_expr(node), max_chars=32)


def _dict_value_expr(node: ast.AST) -> str:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return _limit_expr(node.value, max_chars=64)
        return _limit_expr(str(node.value), max_chars=32)
    if isinstance(node, ast.Dict):
        return f"dict[{len(node.keys)}]"
    return _limit_expr(_expr(node), max_chars=64)


def _call_expr(node: ast.Call) -> str:
    name = _call_name(node.func)
    first_arg = node.args[0] if node.args else None
    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
        return f"{name}:{first_arg.value}"
    return name


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.__class__.__name__


def _limit_expr(text: str, *, max_chars: int = 120) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "..."


def _aug_operator(op: ast.operator) -> str:
    operators = {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.MatMult: "@",
        ast.Div: "/",
        ast.Mod: "%",
        ast.Pow: "**",
        ast.LShift: "<<",
        ast.RShift: ">>",
        ast.BitOr: "|",
        ast.BitXor: "^",
        ast.BitAnd: "&",
        ast.FloorDiv: "//",
    }
    return operators.get(type(op), op.__class__.__name__)
