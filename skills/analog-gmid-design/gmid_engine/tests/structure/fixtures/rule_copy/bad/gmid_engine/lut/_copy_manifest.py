"""fake registry (fixture): new code with a self-consistent hash, and a path outside the package."""

COPY_SOURCE = "legacy/old.py"

COPIED_DEFINITIONS = (
    ("fake.py", "invented", "4~5", "7fc7debfaccc312ebf9f0139411552e0439dc524d466642fbe5d6a0b94cef5d1", ("99",)),
    ("../graph/copied.py", "scan", "11~14", "ef7c32f1df1688582cd5d737a82a2717ecd64c118951dd2c3a2deafb6eb49c59", ("40",)),
)
