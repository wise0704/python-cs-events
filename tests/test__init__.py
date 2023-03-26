from importlib.metadata import metadata

import events


def test_metadata() -> None:
    data = metadata("cs-events")
    assert data["Author"] == events.__author__
    # assert data["Summary"] == cs_events.__doc__
    assert data["Version"] == events.__version__
