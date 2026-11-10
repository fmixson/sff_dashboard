"""Look of SFF at a Glance, matched to the Cohort KPI Dashboard (PycharmProjects/KPI Cohort Dashboard/app.py):
navy title bands with white text and an ice-blue subtitle, light-gray section bands, white bordered cards,
green for better / red for worse. Used only by simple_app.py; the full dashboard keeps its own look."""
import streamlit as st

NAVY = "#1E2761"
ICE = "#CADCFC"
GREEN = "#1E7A46"
RED = "#B3261E"
GRAY = "#6B6B6B"
LIGHTBG = "#F2F2F2"
BORDER = "#E3E3E3"
INK = "#2A2A2A"
GOAL_LINE = "#1E2761"


def inject_css():
    """Navy for primary buttons, the selected group button and the active menu item."""
    st.markdown(f"""<style>
      [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {{
        background:{NAVY}; border-color:{NAVY}; color:white; }}
      [data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover {{
        background:#2B3A86; border-color:#2B3A86; color:white; }}
      button[data-variant="segmented_control"][aria-checked="true"] {{
        background:{NAVY} !important; border-color:{NAVY} !important; color:white !important; }}
      button[data-variant="segmented_control"][aria-checked="true"] * {{ color:white !important; }}
      [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child {{
        background-color:{NAVY} !important; border-color:{NAVY} !important; }}
      [data-testid="stSidebarNav"] a[aria-current="page"] {{ background:{ICE}; }}
      [data-testid="stExpander"] summary {{ background:{LIGHTBG}; }}
      [role="tablist"] {{ gap:6px; flex-wrap:wrap; }}
      [data-testid="stTab"] {{ background:{LIGHTBG}; border-radius:8px 8px 0 0; padding:8px 16px !important; }}
      [data-testid="stTab"] p {{ font-size:1.02rem !important; font-weight:700; color:{GRAY}; }}
      [data-testid="stTab"][aria-selected="true"] {{ background:{NAVY}; }}
      [data-testid="stTab"][aria-selected="true"] p {{ color:white !important; }}
      [data-baseweb="tab-highlight"], [data-testid="stTabsHighlight"] {{ background-color:{NAVY} !important; }}
      [data-testid="stExpander"] summary:hover {{ color:{NAVY}; }}
    </style>""", unsafe_allow_html=True)


def banner(title: str, subtitle: str = ""):
    st.markdown(
        f"<div style='background:{NAVY};padding:1rem 1.5rem;border-radius:8px;margin-bottom:1rem;'>"
        f"<div style='color:white;font-size:1.6rem;font-weight:700;line-height:1.3'>{title}</div>"
        + (f"<div style='color:{ICE};font-size:0.9rem;'>{subtitle}</div>" if subtitle else "")
        + "</div>", unsafe_allow_html=True)


def band(title: str, subtitle: str = ""):
    st.markdown(
        f"<div style='background:{LIGHTBG};border-radius:8px;padding:0.6rem 0.9rem;margin:0.6rem 0 0.6rem 0;'>"
        f"<div style='font-weight:700;color:{NAVY};font-size:1.15rem'>{title}</div>"
        + (f"<div style='color:{GRAY};font-size:0.85rem'>{subtitle}</div>" if subtitle else "")
        + "</div>", unsafe_allow_html=True)


def tile(label: str, value: str, note: str = "", color: str = NAVY, tip: str = "") -> str:
    """White card like the KPI dashboard's metric_card. tip shows on hover."""
    t = f" title=\"{tip}\"" if tip else ""
    return (f"<div{t} style='border:1px solid {BORDER};border-radius:10px;padding:0.9rem 1rem;background:white;"
            f"height:100%'><div style='font-size:0.85rem;color:{INK};font-weight:600'>{label}</div>"
            f"<div style='font-size:1.9rem;font-weight:700;color:{color};line-height:1.3'>{value}</div>"
            f"<div style='font-size:0.78rem;color:{GRAY}'>{note}</div></div>")


def html_table(header: list[str], rows: list[list[str]], first_col_label: str = "") -> str:
    """Navy header row, light-gray first column, like the KPI dashboard's tables."""
    th = (f"<th style='padding:0.55rem 0.9rem;text-align:left;background:{NAVY};color:white;font-size:0.8rem'>"
          f"{first_col_label}</th>") + "".join(
        f"<th style='padding:0.55rem 0.9rem;text-align:center;background:{NAVY};color:white;font-size:0.8rem;"
        f"white-space:nowrap'>{h}</th>" for h in header)
    body = ""
    for r in rows:
        body += ("<tr><td style='padding:0.5rem 0.9rem;font-weight:600;color:" + INK + ";background:" + LIGHTBG
                 + ";font-size:0.85rem;border-top:1px solid " + BORDER + "'>" + r[0] + "</td>"
                 + "".join(f"<td style='padding:0.5rem 0.9rem;text-align:center;font-size:0.95rem;"
                           f"border-top:1px solid {BORDER}'>{c}</td>" for c in r[1:]) + "</tr>")
    return (f"<div style='overflow-x:auto;border:1px solid {BORDER};border-radius:8px'>"
            f"<table style='border-collapse:collapse;width:100%'><tr>{th}</tr>{body}</table></div>")


TINT = {"up": ("#E3F1E8", GREEN), "down": ("#F7E1DF", RED), "same": ("#EEF1FA", NAVY)}


def trend_pill(pts: float | None, vs: str) -> str:
    """Colored pill: green when up, red when down, light navy when about the same."""
    if pts is None:
        return ""
    kind = "same" if abs(pts) < 0.5 else ("up" if pts > 0 else "down")
    bg, fg = TINT[kind]
    txt = (f"About the same as {vs}" if kind == "same" else
           f"{'▲ Up' if kind == 'up' else '▼ Down'} {abs(pts):.1f} points vs. {vs}")
    return (f"<span style='display:inline-block;background:{bg};color:{fg};font-weight:700;font-size:0.82rem;"
            f"border-radius:999px;padding:4px 10px'>{txt}</span>")


def trend_color(pts: float | None) -> str:
    if pts is None or abs(pts) < 0.5:
        return NAVY
    return GREEN if pts > 0 else RED


def kpi_card(label: str, body: str, accent: str = NAVY, muted: bool = False, min_h: int = 250) -> str:
    """Large card: navy header strip with the KPI name in white, a colored accent bar down the left side."""
    head = GRAY if muted else NAVY
    tint = {GREEN: "#F1F8F3", RED: "#FCF0EF", NAVY: "#F4F6FC"}.get(accent, "#F6F6F6")
    return (f"<div style='border:1px solid {BORDER};border-left:7px solid {accent};border-radius:12px;"
            f"background:{tint};min-height:{min_h}px;overflow:hidden;box-shadow:0 1px 3px rgba(30,39,97,.10)'>"
            f"<div style='background:{head};color:white;font-weight:700;font-size:1rem;line-height:1.3;"
            f"padding:10px 14px;min-height:62px;display:flex;align-items:center'>{label}</div>"
            f"<div style='padding:12px 14px'>{body}</div></div>")
