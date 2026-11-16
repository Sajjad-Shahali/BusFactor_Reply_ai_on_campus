"""Every palette keeps the interface readable: contrast of text and buttons, and no leftover original blues."""

from pathlib import Path

import pytest

from ui import palettes
from ui.theme import _CSS

NAMES = [n for n, p in palettes.PALETTES.items() if p]
MUTED = ["#E8EBF7", "#A9B2D6", "#8D97BC", "#AEB7DA", "#9FAAD6", "#B9C1E0", "#B5BDDC", "#8F9AC4", "#C9D0EA", "#7E89B1"]


def luminance(hex_color: str) -> float:
    r, g, b = [int(hex_color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.mark.parametrize("name", NAMES)
def test_button_text_is_readable_on_every_accent_fill(name):
    p = palettes.get(name)
    for role in ("fill_dark", "fill", "fill_hi"):
        assert contrast(p["on_fill"], p[role]) >= 4.5, (name, role, contrast(p["on_fill"], p[role]))


@pytest.mark.parametrize("name", NAMES)
def test_accent_text_is_readable_on_every_background(name):
    p = palettes.get(name)
    for fg in ("hi", "hi2", "soft", "softer", "acc2", "text"):
        for bg in ("bg", "surface", "side_bottom", "side_top"):
            assert contrast(p[fg], p[bg]) >= 4.5, (name, fg, bg, round(contrast(p[fg], p[bg]), 2))


@pytest.mark.parametrize("name", NAMES)
def test_muted_text_stays_readable_after_it_is_tinted(name):
    p = palettes.get(name)
    for original in MUTED:
        tinted = palettes.color(original, name)
        for bg in ("bg", "surface", "side_bottom"):
            assert contrast(tinted, p[bg]) >= 4.5, (name, original, tinted, bg, round(contrast(tinted, p[bg]), 2))


@pytest.mark.parametrize("name", NAMES)
def test_no_original_blue_survives_in_the_stylesheet(name):
    css = palettes.recolor(_CSS, name)
    for blue in ("#2F4FD8", "#3A54E0", "#4F6BFF", "#6F88FF", "#A9B9FF", "#8FA5FF", "#C5D0FF", "#0A0F1F"):
        assert blue.lower() not in css.lower(), (name, blue)
    assert "rgba(111,136,255" not in css and "rgba(47,79,216" not in css and "rgba(43,68,176" not in css


def test_the_classic_palette_is_the_original_sheet_and_status_colours_never_change():
    assert palettes.recolor(_CSS, "classic") == _CSS
    for name in NAMES:
        css = palettes.recolor(_CSS, name)
        for status in ("#4BE3AE", "#FF8A80", "#F5C46B", "rgba(43,217,159", "rgba(255,107,97", "rgba(245,196,107"):
            assert status.lower() in css.lower(), (name, status)


def test_colours_in_svg_and_the_3d_map_follow_the_palette():
    assert palettes.color("#4F6BFF", "classic") == "#4F6BFF"
    assert palettes.color("#4F6BFF", "teal") == palettes.get("teal")["fill_hi"]
    page = "scene.fog = new THREE.FogExp2(0x0A0F1F, 0.03); const c = 0x2BD99F; new THREE.Color(0x2F4FD8);"
    out = palettes.recolor(page, "forest")
    assert "0x2BD99F" in out and "0x0A1410" in out.replace("0x0a1410", "0x0A1410").upper().replace("0X", "0x")
    assert "2F4FD8" not in out.upper()


def test_every_palette_has_a_matching_streamlit_theme():
    flags = palettes.streamlit_theme_flags("forest")
    assert any(f.startswith("--theme.primaryColor=#") for f in flags) and any("backgroundColor=#0A1410" in f for f in flags)


FLAT = [n for n in NAMES if palettes.get(n)["flat"]]


def test_there_are_flat_and_gradient_palettes():
    assert len(FLAT) >= 4 and len(NAMES) > len(FLAT)


@pytest.mark.parametrize("name", FLAT)
def test_flat_palettes_switch_gradients_glows_and_texture_off(name):
    css = palettes.overrides(name)
    for selector in (".stApp", ".bf-hero", "stSidebar", "-webkit-text-fill-color", 'kind="primary"', ".bf-ring .val"):
        assert selector in css, (name, selector)
    assert "gradient" not in css and "background-image: none" in css


@pytest.mark.parametrize("name", [n for n in NAMES if n not in FLAT])
def test_gradient_palettes_add_no_overrides(name):
    assert palettes.overrides(name) == ""
    assert palettes.overrides("classic") == ""


@pytest.mark.parametrize("name", FLAT)
def test_flat_overrides_sit_inside_the_style_block_not_on_the_page(monkeypatch, name):
    import importlib

    from ui import theme
    monkeypatch.setattr(palettes, "DEFAULT", name)
    theme = importlib.reload(theme)
    try:
        assert theme.CSS.count("<style>") == 1 and theme.CSS.count("</style>") == 1
        assert theme.CSS.rstrip().endswith("</style>")                      # nothing after the closing tag (it would be shown as text)
        assert "flat palette: solid colours only" in theme.CSS.split("</style>")[0]
    finally:
        monkeypatch.setattr(palettes, "DEFAULT", "classic")
        importlib.reload(theme)


def test_the_default_palette_matches_streamlits_theme_and_its_accent_text_is_readable():
    default = palettes.get(palettes.DEFAULT)
    assert palettes.DEFAULT == "brass" and default["label"] == "Espresso & Brass"
    # Streamlit paints the active tab text and toggles with primaryColor: it must read on the page background
    assert contrast(default["primary"], default["bg"]) >= 4.5
    config = (Path(__file__).resolve().parents[1] / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    for flag in palettes.streamlit_theme_flags(palettes.DEFAULT):
        key, value = flag.removeprefix("--theme.").split("=")
        assert f'{key} = "{value}"' in config, key
