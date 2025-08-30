import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from client.t1 import model, serialize


def test_roundtrip(tmp_path) -> None:
    state = model.default_map()
    data = serialize.export_map(state)
    loaded = serialize.import_map(data)
    assert loaded == state

    path = tmp_path / "map.json"
    serialize.save_map(state, path)
    assert serialize.load_map(path) == state
