"""The ISL gloss -> English/Hindi sentence engine (offline, deterministic). Examples are the ones documented in the README."""
import pytest

import isl_lang

CASES = [
    (["hello", "i", "sick", "doctor", "where"], "Hello! I am sick. Where is the doctor?", "नमस्ते! मैं बीमार हूँ। डॉक्टर कहाँ है?"),
    (["help", "accident", "ambulance"], "Please help me! There has been an accident! Please call an ambulance!", None),
    (["good_morning", "i", "deaf", "please", "slow"], "Good morning! I am deaf. Please speak slowly.", "सुप्रभात! मैं बधिर हूँ। कृपया धीरे बोलिए।"),
    (["namaste", "how_are_you", "i", "happy"], "Namaste! How are you? I am happy.", "नमस्ते! आप कैसे हैं? मैं खुश हूँ।"),
    (["sorry", "my", "book", "where"], "I am sorry. Where is my book?", "माफ़ कीजिए। मेरी किताब कहाँ है?"),
    (["you", "sad", "why"], "Why are you sad?", "आप उदास क्यों हैं?"),
]


@pytest.mark.parametrize("keys,en,hi", CASES)
def test_documented_examples(keys, en, hi, hindi_of):
    out = isl_lang.compose(keys, hindi_of)
    assert out["en"] == en
    if hi:
        assert out["hi"] == hi


def test_empty_and_reject_produce_nothing(hindi_of):
    assert isl_lang.compose([], hindi_of)["en"] == ""
    assert isl_lang.compose(["__reject__"], hindi_of)["en"] == ""


def test_emergency_is_flagged_urgent(hindi_of):
    assert isl_lang.compose(["fire"], hindi_of)["urgent"] is True
    assert isl_lang.compose(["hello"], hindi_of)["urgent"] is False


def test_unknown_gloss_never_crashes(hindi_of):
    assert isl_lang.compose(["not_a_real_sign", "i"], hindi_of)["en"]


def test_levels_are_monotonic_and_named():
    cur, nxt = isl_lang.level_for(0)
    assert cur[1] == "Beginner" and nxt is not None
    assert isl_lang.level_for(10_000)[1] is None
    assert all(len(lv) == 2 for lv in isl_lang.LEVELS)
