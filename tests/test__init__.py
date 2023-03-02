from importlib.metadata import metadata

import cs_events


def test_metadata() -> None:
    data = metadata(cs_events.__name__)
    assert data["Author"] == cs_events.__author__
    # assert data["Summary"] == cs_events.__doc__
    assert data["Version"] == cs_events.__version__
