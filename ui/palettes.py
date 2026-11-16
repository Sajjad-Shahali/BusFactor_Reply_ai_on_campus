"""Colour palettes for the interface.

The stylesheet (ui/theme.py) was written with one blue-and-green palette. Every colour in it is mapped to a *role*
(page background, surface, line, accent fill, accent text, second accent ...) and a palette only has to say what each
role looks like. Status colours (green = fine, red = risk, amber = attention) are not part of a palette: they keep
their meaning in every theme.

Pick a palette with the BUSFACTOR_PALETTE environment variable (default below). Streamlit's own widgets take their
colours from .streamlit/config.toml, which should use the same primary colour.

Contrast rules checked in tests/test_palettes.py: white text on every accent fill >= 4.5:1, accent text and muted text
on every background >= 4.5:1.
"""
from __future__ import annotations

import colorsys
import os
import re

DEFAULT = os.getenv("BUSFACTOR_PALETTE", "brass").strip().lower()   # Espresso & Brass

# literal in the original stylesheet -> role
HEX_ROLES = {
    "#0A0F1F": "bg", "#0D1430": "side_top", "#121B42": "side_bottom", "#121A33": "surface", "#161F3D": "surface2",
    "#243058": "line", "#33427A": "line_hover", "#3A4670": "line_dim", "#56628F": "line_strong",
    "#2F4FD8": "fill_dark", "#3A54E0": "fill", "#4A66FF": "fill_hi", "#4F6BFF": "fill_hi", "#5B76FF": "fill_hi",
    "#2B44B0": "glow1", "#6F88FF": "hi", "#8FA5FF": "hi", "#7189FF": "hi", "#93A8FF": "hi2", "#9DB0FF": "soft",
    "#A9B9FF": "soft", "#C5D0FF": "softer", "#46E0A8": "acc2", "#E8EBF7": "text",
}
RGB_ROLES = {
    (18, 26, 51): "surface_rgb", (16, 24, 64): "surface2_rgb", (111, 136, 255): "hi_rgb", (79, 107, 255): "fill_hi_rgb",
    (47, 79, 216): "fill_rgb", (43, 68, 176): "glow1_rgb", (70, 224, 168): "acc2_rgb", (30, 154, 98): "glow2_rgb",
}


def _rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def _palette(name, label, note, *, bg, side_top, side_bottom, surface, surface2, line, line_hover, line_dim, line_strong,
             fill_dark, fill, fill_hi, glow1, hi, hi2, soft, softer, acc2, glow2, text, neutral_hue, neutral_sat,
             flat=False, on_fill="#FFFFFF"):
    p = dict(name=name, label=label, note=note, bg=bg, side_top=side_top, side_bottom=side_bottom, surface=surface,
             surface2=surface2, line=line, line_hover=line_hover, line_dim=line_dim, line_strong=line_strong,
             fill_dark=fill_dark, fill=fill, fill_hi=fill_hi, glow1=glow1, hi=hi, hi2=hi2, soft=soft, softer=softer,
             acc2=acc2, text=text, neutral_hue=neutral_hue, neutral_sat=neutral_sat, flat=flat, on_fill=on_fill)
    p.update(surface_rgb=_rgb(surface), surface2_rgb=_rgb(surface2), hi_rgb=_rgb(hi), fill_hi_rgb=_rgb(fill_hi),
             fill_rgb=_rgb(fill), glow1_rgb=_rgb(glow1), acc2_rgb=_rgb(acc2), glow2_rgb=glow2)
    return p


PALETTES: dict[str, dict | None] = {
    "classic": None,   # the original navy, blue and green
    "forest": _palette(
        "forest", "Forest & Gold", "deep green-black, emerald buttons, gold highlights",
        bg="#0A1410", side_top="#0C1A14", side_bottom="#11261D", surface="#11201A", surface2="#0E281E",
        line="#1F3A2E", line_hover="#2F5A46", line_dim="#2C4A3C", line_strong="#4A7A63",
        fill_dark="#166A45", fill="#1B7F54", fill_hi="#1B8254", glow1="#1B5C3E",
        hi="#E3B94F", hi2="#F0CF7A", soft="#F2D88F", softer="#F8E7B5", acc2="#8FE3B0", glow2="40,160,110",
        text="#EEF3EE", neutral_hue=150, neutral_sat=0.30),
    "teal": _palette(
        "teal", "Teal & Lime", "ink teal, deep-teal buttons, lime accents",
        bg="#061416", side_top="#08191C", side_bottom="#0D2A30", surface="#0C2024", surface2="#08262C",
        line="#17414A", line_hover="#22616D", line_dim="#1C4D57", line_strong="#3C8793",
        fill_dark="#095F68", fill="#0A6F78", fill_hi="#0C7882", glow1="#0F5E66",
        hi="#2DD4BF", hi2="#6EE7D3", soft="#99F0E0", softer="#C8F7EE", acc2="#C6F26B", glow2="60,180,150",
        text="#E9F5F4", neutral_hue=185, neutral_sat=0.35),
    "rose": _palette(
        "rose", "Graphite & Rose", "neutral graphite, rose buttons, gold secondary",
        bg="#101012", side_top="#131316", side_bottom="#1B1B21", surface="#1A1A1F", surface2="#241E24",
        line="#2D2D35", line_hover="#45454F", line_dim="#3A3A44", line_strong="#6A6A78",
        fill_dark="#8F1245", fill="#B4195A", fill_hi="#BE1E62", glow1="#7A1D45",
        hi="#FF7AA8", hi2="#FF9DBF", soft="#FFB8D0", softer="#FFD6E4", acc2="#F5C16C", glow2="200,140,60",
        text="#F1F0F2", neutral_hue=270, neutral_sat=0.08),
    "brass": _palette(
        "brass", "Espresso & Brass", "warm brown-black, brass buttons, sage secondary",
        bg="#120E0B", side_top="#15100C", side_bottom="#211912", surface="#1C1510", surface2="#2C2014",
        line="#3A2D22", line_hover="#5A4634", line_dim="#4A3A2B", line_strong="#7D6548",
        fill_dark="#7A5A12", fill="#8A6516", fill_hi="#916C1A", glow1="#5C4510",
        hi="#E8C468", hi2="#F0D58C", soft="#F4DFA6", softer="#FAEFC9", acc2="#A8D8B0", glow2="160,120,50",
        text="#F3EEE6", neutral_hue=30, neutral_sat=0.25),
    # ---- flat palettes: solid colours only (no gradients, glows or grid texture), see overrides()
    "mono": _palette(
        "mono", "Mono & Signal", "flat: neutral black and grey, signal-yellow highlights and buttons",
        bg="#0D0D0D", side_top="#121212", side_bottom="#141414", surface="#171717", surface2="#1F1F1F",
        line="#2B2B2B", line_hover="#444444", line_dim="#383838", line_strong="#6B6B6B",
        fill_dark="#E6BE00", fill="#FFD60A", fill_hi="#FFE14D", glow1="#333333",
        hi="#FFD60A", hi2="#FFE14D", soft="#FFE98A", softer="#FFF3BF", acc2="#E5E5E5", glow2="120,120,120",
        text="#F2F2F2", neutral_hue=0, neutral_sat=0.0, flat=True, on_fill="#0D0D0D"),
    "bordeaux": _palette(
        "bordeaux", "Bordeaux & Cream", "flat: wine-black, wine buttons, cream highlights",
        bg="#150C0F", side_top="#1B1013", side_bottom="#1D1114", surface="#1D1114", surface2="#26161B",
        line="#3B2229", line_hover="#5A3540", line_dim="#4A2C35", line_strong="#86515F",
        fill_dark="#6B1830", fill="#7E1D38", fill_hi="#8C2442", glow1="#5A1A2B",
        hi="#F0E2C8", hi2="#F6EBD6", soft="#F8EFDD", softer="#FBF6EA", acc2="#D9A5B0", glow2="150,80,100",
        text="#F6F0EA", neutral_hue=345, neutral_sat=0.20, flat=True),
    "olive": _palette(
        "olive", "Olive & Sand", "flat: olive-black, olive buttons, sand highlights",
        bg="#11120D", side_top="#14160F", side_bottom="#181A12", surface="#181A12", surface2="#20231A",
        line="#2E3322", line_hover="#474E35", line_dim="#3B422B", line_strong="#6F7A52",
        fill_dark="#4A5A22", fill="#55662A", fill_hi="#5E7030", glow1="#3C4A1E",
        hi="#D9C896", hi2="#E6D8AE", soft="#EDE2C2", softer="#F5EEDA", acc2="#A9C27A", glow2="100,130,50",
        text="#F1EFE4", neutral_hue=70, neutral_sat=0.25, flat=True),
    "slate": _palette(
        "slate", "Slate & Amber", "flat: cool slate, slate-teal buttons, amber highlights",
        bg="#0F1316", side_top="#12181C", side_bottom="#151B20", surface="#151B20", surface2="#1C242B",
        line="#28333B", line_hover="#3E505C", line_dim="#33424C", line_strong="#5F7685",
        fill_dark="#2B4A57", fill="#335766", fill_hi="#3A6173", glow1="#264451",
        hi="#F2A93B", hi2="#F7BE62", soft="#FAD08E", softer="#FDE5BD", acc2="#8FC1D4", glow2="60,110,130",
        text="#EDF1F3", neutral_hue=205, neutral_sat=0.30, flat=True),
}


def get(name: str | None = None) -> dict | None:
    """The palette dictionary (None for the original colours)."""
    return PALETTES.get((name or DEFAULT).lower())


def _is_blue(h: float, s: float) -> bool:
    return 200 <= h * 360 <= 262 and s > 0.04


def _retint(r: int, g: int, b: int, palette: dict) -> tuple[int, int, int]:
    """Any other blue-family colour: keep the lightness, move to the palette's neutral tint (or accent for vivid ones)."""
    h, light, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if not _is_blue(h, s):
        return r, g, b
    hue = palette["neutral_hue"] / 360
    sat = s * palette["neutral_sat"] if s < 0.55 else min(1.0, s * 0.8)
    if s >= 0.55:
        hue = colorsys.rgb_to_hls(*(int(x) / 255 for x in _rgb(palette["hi"]).split(",")))[0]
    nr, ng, nb = colorsys.hls_to_rgb(hue, light, sat)
    return round(nr * 255), round(ng * 255), round(nb * 255)


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def color(hex_color: str, name: str | None = None) -> str:
    """One colour from the original sheet in the active palette (for SVG and inline styles)."""
    palette = get(name)
    key = hex_color.upper()
    if palette is None:
        return hex_color
    role = HEX_ROLES.get(key)
    if role:
        return palette[role]
    r, g, b = _retint(*_hex_to_rgb(key), palette)
    return f"#{r:02X}{g:02X}{b:02X}"


def recolor(text: str, name: str | None = None) -> str:
    """Rewrite every colour literal in a stylesheet or HTML/JS string (#RRGGBB, 0xRRGGBB, rgb()/rgba())."""
    palette = get(name)
    if palette is None:
        return text

    def hex_sub(match):
        prefix, digits = match.group(1), match.group(2)
        new = color("#" + digits, name).lstrip("#")
        return f"{prefix}{new}"

    def rgb_sub(match):
        r, g, b = int(match.group(2)), int(match.group(3)), int(match.group(4))
        role = RGB_ROLES.get((r, g, b))
        if role:
            nr, ng, nb = (palette[role].split(",") if "," in palette[role] else _hex_to_rgb(palette[role]))
        else:
            nr, ng, nb = _retint(r, g, b, palette)
        return f"{match.group(1)}{nr},{ng},{nb}"

    text = re.sub(r"(#|0x)([0-9A-Fa-f]{6})\b", hex_sub, text)
    return re.sub(r"(rgba?\(\s*)(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", rgb_sub, text)


def overrides(name: str | None = None) -> str:
    """Extra CSS for a flat palette: solid backgrounds instead of gradients, glows and grid texture."""
    p = get(name)
    if not p or not p.get("flat"):
        return ""
    return f"""
/* ---------- flat palette: solid colours only ---------- */
.stApp {{ background: {p['bg']} !important; }}
[data-testid="stSidebar"] {{ background: {p['side_bottom']} !important; border-right: 1px solid {p['line']} !important; }}
.bf-hero, .bf-panel, .bf-dark {{ background: {p['surface']} !important; background-image: none !important;
  border: 1px solid {p['line']} !important; box-shadow: none !important; }}
.bf-hero h1 em, .bf-grad, .bf-dark h1 em {{ background: none !important; -webkit-background-clip: border-box !important;
  background-clip: border-box !important; -webkit-text-fill-color: {p['hi']} !important; color: {p['hi']} !important; }}
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primaryFormSubmit"], [data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"] {{ background: {p['fill']} !important; box-shadow: none !important;
  color: {p['on_fill']} !important; border: none !important; }}
.stButton button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover {{ background: {p['fill_hi']} !important; filter: none !important; }}
.stButton button[kind="primary"] p, [data-testid="stBaseButton-primary"] p {{ color: {p['on_fill']} !important; }}
.bf-win {{ background: {p['surface2']} !important; }}
.bf-ring .val {{ stroke: {p['hi']} !important; }}
.bf-next .nx, .bf-hero .bf-st.now span {{ background: {p['fill']} !important; color: {p['on_fill']} !important;
  border-color: {p['hi']} !important; box-shadow: none !important; }}
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][height] {{ backdrop-filter: none !important; box-shadow: none !important; }}
"""


def streamlit_theme_flags(name: str | None = None) -> list[str]:
    """The matching Streamlit theme options (for a preview run or for .streamlit/config.toml)."""
    p = get(name)
    if p is None:
        return ["--theme.primaryColor=#5B76FF", "--theme.backgroundColor=#0A0F1F",
                "--theme.secondaryBackgroundColor=#161F3D", "--theme.textColor=#E8EBF7"]
    return [f"--theme.primaryColor={p['fill_hi']}", f"--theme.backgroundColor={p['bg']}",
            f"--theme.secondaryBackgroundColor={p['surface2']}", f"--theme.textColor={p['text']}"]
