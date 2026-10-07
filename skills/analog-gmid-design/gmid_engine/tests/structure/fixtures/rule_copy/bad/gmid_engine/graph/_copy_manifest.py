"""copy registry (fixture): valid, edited copy, wrong literal list, missing definition."""

COPY_SOURCE = "legacy/old.py"

COPIED_DEFINITIONS = (
    ("copied.py", "LIMITS", "8~8", "aa2632ac9ebe6db820becbddad4466b1f6e480f3bbfce13cb067e0340daebed6", ("3", "4")),
    ("copied.py", "scan", "11~14", "ef7c32f1df1688582cd5d737a82a2717ecd64c118951dd2c3a2deafb6eb49c59", ("40",)),
    ("changed.py", "renamed", "17~21", "b2eb23a3032972cf87f67fbc97e4f15b1c92886b6ee229ae6d6d5d0fd470e29b", ("5",)),
    ("miscount.py", "miscounted", "24~25", "1edb9d18498aff26288263c23f6e0000eb98efde480ef4e0142c6fcf671a8c58", ()),
    ("copied.py", "gone", "4~5", "0000000000000000000000000000000000000000000000000000000000000000", ()),
)
