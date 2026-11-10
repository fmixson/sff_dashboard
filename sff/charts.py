"""Plotly figure builders (no Streamlit imports, reusable in notebooks/reports)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from . import config as C

FONT = dict(family="Arial, sans-serif", size=12, color="#0b0b0b")
GRID = "#e6e5e0"


def _base(fig: go.Figure, height: int, top: int = 30) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=top, b=10), font=FONT,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(font=dict(family="Arial", size=12)),
    )
    return fig


def status_by_lever(strat: pd.DataFrame) -> go.Figure:
    """Stacked horizontal bar: count of strategies in each status, per lever."""
    fig = go.Figure()
    levers = list(C.LEVERS)
    labels = [f"{k}. {v}" for k, v in C.LEVERS.items()]
    for st in C.STATUSES:
        counts = [int(((strat["lever"] == L) & (strat["status"] == st)).sum()) for L in levers]
        fig.add_bar(
            y=labels, x=counts, name=f"{C.STATUS_ICONS[st]} {st}", orientation="h",
            marker=dict(color=C.STATUS_COLORS[st], line=dict(color="#fcfcfb", width=2)),
            hovertemplate="%{y}<br>" + st + ": %{x} strategies<extra></extra>",
        )
    fig.update_layout(barmode="stack",
                      legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, traceorder="normal"),
                      xaxis=dict(title=None, dtick=1, gridcolor=GRID, ticksuffix=""),
                      yaxis=dict(autorange="reversed"))
    return _base(fig, 280, top=60)


def dollars_by_strategy(df: pd.DataFrame, metric: str = "requested") -> go.Figure:
    """Horizontal bar of $ per strategy, colored by lever; fixed order A.1 -> D.6."""
    d = df[df["strategy"] != "None"].copy()
    d["lever"] = d["strategy"].str[0]
    d["label"] = d["strategy"] + "  " + d["lever"].map(C.LEVERS)
    fig = go.Figure()
    for L, name in C.LEVERS.items():
        s = d[d["lever"] == L]
        fig.add_bar(
            y=s["strategy"], x=s[metric], orientation="h", name=f"{L}. {name}",
            marker=dict(color=C.LEVER_COLORS[L], cornerradius=4, line=dict(color="#fcfcfb", width=2)),
            customdata=s[["requests", "text_cost"]].values,
            hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<br>%{customdata[0]} requests"
                          " (%{customdata[1]} with non-numeric cost)<extra></extra>",
        )
    fig.update_layout(
        xaxis=dict(title="Dollars (numeric costs only)", tickprefix="$", tickformat="~s", gridcolor=GRID),
        yaxis=dict(categoryorder="array", categoryarray=list(d["strategy"])[::-1], title=None),
        legend=dict(orientation="h", y=-0.12), bargap=0.25,
    )
    return _base(fig, 620)


def dollars_grouped(df: pd.DataFrame, by: str, groups: list[str], colors: dict[str, str]) -> go.Figure:
    """Grouped horizontal bars: requested $ per strategy, one bar per group (year or area).
    `colors` maps each group to a fixed slot so color follows the entity, not its position."""
    d = df[df["strategy"] != "None"]
    order = sorted(d["strategy"].unique())
    fig = go.Figure()
    # horizontal grouped bars stack the first trace at the bottom, so add groups in
    # reverse (first group on top) and reverse the legend
    for g in reversed(groups):
        s = d[d[by] == g].set_index("strategy").reindex(order).reset_index()
        fig.add_bar(
            y=s["strategy"], x=s["requested"], orientation="h", name=g,
            marker=dict(color=colors[g], cornerradius=4, line=dict(color="#fcfcfb", width=2)),
            customdata=s[["requests"]].values,
            hovertemplate="<b>%{y}</b> " + g + "<br>$%{x:,.0f} · %{customdata[0]} requests<extra></extra>",
        )
    fig.update_layout(
        barmode="group", bargap=0.2, bargroupgap=0.05,
        xaxis=dict(title="Requested $ (numeric costs only)", tickprefix="$", tickformat="~s", gridcolor=GRID),
        yaxis=dict(categoryorder="array", categoryarray=order[::-1], title=None),
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, traceorder="reversed"),
    )
    return _base(fig, 760, top=50)


def dollars_by_year(df: pd.DataFrame, years: list[str]) -> go.Figure:
    all_years = sorted(df["fiscal_year"].unique())
    colors = {y: C.YEAR_COLORS[i % len(C.YEAR_COLORS)] for i, y in enumerate(all_years)}
    return dollars_grouped(df, "fiscal_year", years, colors)


def dollars_by_area(df: pd.DataFrame, areas: list[str]) -> go.Figure:
    return dollars_grouped(df, "area", areas, C.AREA_COLORS)


def kpi_trend(results: pd.DataFrame, groups: list[str], target: float | None,
              order: list[str] | None = None) -> go.Figure:
    """Line chart of one KPI over time for selected groups (categorical slots in fixed order)."""
    palette = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
    fig = go.Figure()
    for i, g in enumerate(groups):
        s = results[results["group"] == g].sort_values("year")
        ref = order or C.EQUITY_GROUPS                              # color follows the group, not rank
        color = palette[(ref.index(g) if g in ref else len(ref)) % len(palette)]
        fig.add_scatter(
            x=s["year"], y=s["value"], mode="lines+markers", name=g,
            line=dict(color=color, width=2), marker=dict(size=8, line=dict(color="#fcfcfb", width=2)),
            hovertemplate=g + "<br>%{x}: %{y:.1%}<extra></extra>",
        )
        if len(groups) <= 4 and not s.empty:  # selective direct labels
            fig.add_annotation(x=s["year"].iloc[-1], y=s["value"].iloc[-1], text=g, showarrow=False,
                               xanchor="left", xshift=8, font=dict(size=11, color="#52514e"))
    if target is not None and pd.notna(target):
        fig.add_hline(y=float(target), line=dict(color="#52514e", dash="dash", width=1),
                      annotation_text=f"Target {float(target):.0%}", annotation_position="top left")
    fig.update_layout(yaxis=dict(tickformat=".0%", gridcolor=GRID, title=None),
                      xaxis=dict(title=None), hovermode="x unified",
                      legend=dict(orientation="h", y=-0.15))
    return _base(fig, 380)


def goal_progress(baseline: float, target: float, current: float | None, current_label: str = "Latest") -> go.Figure:
    """Single bullet bar: baseline -> current -> target. current_label names the bar (e.g., a cohort's
    completion so far, which is still rising)."""
    fig = go.Figure()
    fig.add_bar(x=[target], y=[""], orientation="h", marker_color="#e6e5e0", hoverinfo="skip", showlegend=False)
    if current is not None:
        fig.add_bar(x=[current], y=[""], orientation="h", marker=dict(color="#2a78d6", cornerradius=4),
                    width=0.4, hovertemplate=current_label + ": %{x:.1%}<extra></extra>", showlegend=False)
        fig.add_annotation(x=current, y=0, text=f"{current_label}: {current:.1%}", showarrow=False,
                           xanchor="left", xshift=6, yshift=-26, font=dict(size=11, color="#2a78d6"))
    fig.add_vline(x=baseline, line=dict(color="#52514e", width=2),
                  annotation_text=f"Baseline {baseline:.0%}", annotation_position="top")
    fig.add_vline(x=target, line=dict(color="#0b0b0b", width=2, dash="dash"),
                  annotation_text=f"Goal {target:.0%}", annotation_position="top")
    fig.update_layout(barmode="overlay", xaxis=dict(range=[0, 0.6], tickformat=".0%", gridcolor=GRID))
    return _base(fig, 140)


GROUP_PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]


def _group_color(g: str) -> str:
    return GROUP_PALETTE[C.EQUITY_GROUPS.index(g) % len(GROUP_PALETTE)] if g in C.EQUITY_GROUPS else "#52514e"


def goal_by_group(results: pd.DataFrame, groups: list[str]) -> go.Figure:
    """5-year completion by student group, with the 50% goal and the straight-line path
    the college must follow from the 29% baseline to reach it by 2028-29."""
    g = results[results["kpi_code"] == "GOAL"]
    years = sorted(set(g["year"]) | {C.GOAL_BASELINE_YEAR, C.GOAL_TARGET_YEAR})
    # fill in reporting years between latest data and target year so the path is continuous
    y0, y1 = int(years[0][:4]), int(C.GOAL_TARGET_YEAR[:4])
    years = [f"{y}-{str(y + 1)[2:]}" for y in range(y0, y1 + 1)]
    fig = go.Figure()
    b0, b1 = int(C.GOAL_BASELINE_YEAR[:4]), int(C.GOAL_TARGET_YEAR[:4])
    path_x = [f"{y}-{str(y + 1)[2:]}" for y in range(b0, b1 + 1)]
    path_y = [C.GOAL_BASELINE + (C.GOAL_TARGET - C.GOAL_BASELINE) * i / (b1 - b0) for i in range(b1 - b0 + 1)]
    fig.add_scatter(x=path_x, y=path_y, mode="lines", name="Path to goal (from 29% baseline)",
                    line=dict(color="#52514e", width=1.5, dash="dot"),
                    hovertemplate="Path to goal<br>%{x}: %{y:.1%}<extra></extra>")
    for grp in groups:
        s = g[g["group"] == grp].sort_values("year")
        fig.add_scatter(x=s["year"], y=s["value"], mode="lines+markers", name=grp,
                        line=dict(color=_group_color(grp), width=3 if grp == "All students" else 2),
                        marker=dict(size=8, line=dict(color="#fcfcfb", width=2)),
                        hovertemplate=grp + "<br>%{x}: %{y:.1%}<extra></extra>")
        if len(groups) <= 4 and not s.empty:
            fig.add_annotation(x=s["year"].iloc[-1], y=s["value"].iloc[-1], text=grp, showarrow=False,
                               xanchor="left", xshift=8, font=dict(size=11, color="#52514e"))
    fig.add_hline(y=C.GOAL_TARGET, line=dict(color="#0b0b0b", dash="dash", width=1),
                  annotation_text=f"Goal {C.GOAL_TARGET:.0%} by {C.GOAL_TARGET_YEAR}", annotation_position="top left")
    fig.update_layout(xaxis=dict(type="category", categoryorder="array", categoryarray=years, title=None),
                      yaxis=dict(tickformat=".0%", gridcolor=GRID, range=[0.15, 0.55], title=None),
                      legend=dict(orientation="h", y=-0.15), hovermode="x unified")
    return _base(fig, 420)


def kpi_small(results: pd.DataFrame, code: str, title: str, target: float | None) -> go.Figure:
    """Compact single-series trend (All students) for small multiples on strategy pages."""
    s = results[(results["kpi_code"] == code) & (results["group"] == "All students")].sort_values("year")
    fig = go.Figure()
    fig.add_scatter(x=s["year"], y=s["value"], mode="lines+markers", name="All students",
                    line=dict(color="#2a78d6", width=2), marker=dict(size=6),
                    hovertemplate="%{x}: %{y:.1%}<extra></extra>", showlegend=False)
    if target is not None and pd.notna(target):
        fig.add_hline(y=float(target), line=dict(color="#52514e", dash="dash", width=1),
                      annotation_text=f"Target {float(target):.0%}", annotation_position="top left")
    fig.update_layout(title=dict(text=f"<b>{code}</b> {title[:48]}{'…' if len(title) > 48 else ''}",
                                 font=dict(size=12), x=0, y=0.97),
                      yaxis=dict(tickformat=".0%", gridcolor=GRID, nticks=4),
                      xaxis=dict(tickfont=dict(size=10), nticks=4))
    return _base(fig, 200, top=40)
