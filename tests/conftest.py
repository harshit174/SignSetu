import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def label_map():
    return json.loads((ROOT / "models" / "label_map.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def hindi_of(label_map):
    table = {v["class_key"]: v["hindi"] for v in label_map.values()}
    return lambda key: table.get(key, key)
