"""malformed registry (fixture): short entry, then a duplicated entry."""

COPY_SOURCE = "legacy/old.py"

COPIED_DEFINITIONS = (
    ("broken.py", "thing"),
    ("broken.py", "thing", "4~5", "1d2f4593e3abfc29b55ca5858f94cafeb6b1d00ed46651fe55d729dfb525923f", ("77",)),
    ("broken.py", "thing", "4~5", "1d2f4593e3abfc29b55ca5858f94cafeb6b1d00ed46651fe55d729dfb525923f", ("77",)),
)
