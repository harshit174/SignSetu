"""Guard rails for the parchment design system (assets/theme.css): paper, not screen."""
import re

from conftest import ROOT

CSS = (ROOT / "assets" / "theme.css").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_no_shadows_or_gradients():
    assert not re.search(r"box-shadow\s*:\s*(?!none)", CSS)
    assert "gradient" not in CSS


def test_only_one_clay_button_style():
    # clay is reserved for the primary action
    assert len(re.findall(r"background:\s*var\(--clay\)", CSS)) == 1


def test_app_has_no_emoji_in_ui_strings():
    emoji = re.compile("[\U0001F300-\U0001FAFF☀-⛿✀-➿️]")
    offenders = [l.strip() for l in APP.splitlines() if emoji.search(l) and "✓" not in l and "✕" not in l]
    assert not offenders, offenders[:3]
