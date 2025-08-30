from pathlib import Path


def get_root() -> Path:
    path = Path(__file__).resolve().absolute().parent
    while not path.joinpath("pyproject.toml").exists():
        path = path.parent
    return path
