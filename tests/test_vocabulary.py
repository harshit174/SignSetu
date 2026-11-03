"""Data integrity: the label map, situations and demo scripts must reference real signs."""
import isl_lang


def test_label_map_shape(label_map):
    assert len(label_map) == 301
    keys = [label_map[str(i)]["class_key"] for i in range(301)]
    assert len(set(keys)) == 301
    assert keys[-1] == "__reject__"
    assert all(label_map[str(i)]["hindi"] for i in range(301))


def test_scenarios_reference_real_signs(label_map):
    vocab = {v["class_key"] for v in label_map.values()}
    for name, sc in isl_lang.SCENARIOS.items():
        missing = [k for k in sc["keys"] + sc["demo"] if k not in vocab]
        assert not missing, f"{name}: unknown signs {missing}"
        assert set(sc["demo"]) <= set(sc["keys"]), f"{name}: demo uses signs outside its focus set"
        assert sc["phrases"], f"{name}: no quick phrases"


def test_every_demo_composes_a_sentence(hindi_of):
    for name, sc in isl_lang.SCENARIOS.items():
        assert isl_lang.compose(sc["demo"], hindi_of)["en"], name
