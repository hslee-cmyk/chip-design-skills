from .front_entries import read_front_entries


def previous(run_dir):
    return read_front_entries(run_dir)
