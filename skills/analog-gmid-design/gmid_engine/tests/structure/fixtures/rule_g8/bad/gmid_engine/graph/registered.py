from dataclasses import field


def build():
    return field(default_factory=dict)
