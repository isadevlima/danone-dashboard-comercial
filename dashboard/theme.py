"""Tema visual e helpers de gráficos do dashboard comercial Danone."""

from __future__ import annotations

import plotly.graph_objects as go

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

.main .block-container {
    padding-top: 1.2rem;
    max-width: 1400px;
}

.hero {
    background: linear-gradient(135deg, #1A2B4A 0%, #2E86AB 100%);
    border-radius: 16px;
    padding: 1.8rem 2rem;
    color: white;
    margin-bottom: 1.2rem;
    box-shadow: 0 8px 32px rgba(26, 43, 74, 0.18);
}
.hero h1 { color: white !important; font-size: 1.75rem; margin: 0 0 0.35rem 0; font-weight: 700; line-height: 1.25; }
.hero p  { color: rgba(255,255,255,0.88); margin: 0; font-size: 0.95rem; line-height: 1.45; }

.kpi-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 1.15rem 1.3rem;
    border: 1px solid #E9ECEF;
    box-shadow: 0 2px 14px rgba(26, 43, 74, 0.06);
    height: 100%;
    min-height: 108px;
}
.kpi-label { font-size: 0.72rem; color: #6C757D; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
.kpi-value { font-size: 1.45rem; font-weight: 700; color: #1A2B4A; margin: 0.35rem 0; line-height: 1.2; }
.kpi-delta-pos { color: #1B5E20; font-weight: 600; font-size: 0.9rem; }
.kpi-delta-neg { color: #BF5700; font-weight: 600; font-size: 0.9rem; }

.section-title {
    font-size: 1.12rem;
    font-weight: 700;
    color: #1A2B4A;
    margin: 1.6rem 0 1rem 0;
    padding-bottom: 0.35rem;
    border-bottom: 2px solid #2E86AB;
    display: block;
    width: 100%;
}

.chart-wrap {
    background: #FFFFFF;
    border-radius: 14px;
    border: 1px solid #E9ECEF;
    padding: 0.5rem 0.75rem 0.25rem 0.75rem;
    box-shadow: 0 2px 14px rgba(26, 43, 74, 0.05);
    margin-bottom: 0.5rem;
}

.portfolio-card {
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E9ECEF;
    padding: 1rem 1.15rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 10px rgba(26, 43, 74, 0.05);
}
.portfolio-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #1A2B4A;
    margin-bottom: 0.35rem;
}
.portfolio-val {
    font-size: 1.25rem;
    font-weight: 700;
    color: #2E86AB;
    margin-bottom: 0.4rem;
}
.portfolio-badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
}
.portfolio-badge.pos { background: #E8F5E9; color: #1B5E20; }
.portfolio-badge.neg { background: #FFF3E0; color: #BF5700; }

.insight-box {
    background: #F8F9FA;
    border-left: 4px solid #2E86AB;
    border-radius: 0 10px 10px 0;
    padding: 0.85rem 1rem;
    margin: 0.65rem 0;
    font-size: 0.9rem;
    color: #2C3E50;
    line-height: 1.5;
}
.insight-box.pos { border-left-color: #1B5E20; background: #E8F5E9; }
.insight-box.neg { border-left-color: #BF5700; background: #FFF3E0; }

footer { visibility: hidden; }
#MainMenu { visibility: hidden; }

/* ── Fundo geral da aplicação ── */
.stApp {
    background-color: #F0F4F8 !important;
}
.main .block-container {
    background: transparent;
}

/* ── Sidebar escura (identidade Danone) ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A2B4A 0%, #1e3352 55%, #243B55 100%) !important;
    border-right: none !important;
    box-shadow: 4px 0 24px rgba(26, 43, 74, 0.15);
}
section[data-testid="stSidebar"] > div:first-child {
    background: transparent !important;
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] h3 {
    color: rgba(255, 255, 255, 0.92) !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.15) !important;
    margin: 1rem 0 !important;
}

/* Radio / navegação */
section[data-testid="stSidebar"] .stRadio > label {
    display: none;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] {
    gap: 0.35rem;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    padding: 0.55rem 0.85rem !important;
    margin-bottom: 0.2rem !important;
    color: rgba(255, 255, 255, 0.85) !important;
    font-weight: 500 !important;
    transition: all 0.15s ease;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.12) !important;
    border-color: rgba(46, 134, 171, 0.6) !important;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio div[aria-checked="true"] label {
    background: rgba(46, 134, 171, 0.35) !important;
    border-color: #2E86AB !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Expander e inputs na sidebar */
section[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.06) !important;
    border-radius: 8px !important;
    color: rgba(255, 255, 255, 0.8) !important;
    font-size: 0.82rem !important;
}
section[data-testid="stSidebar"] input {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: white !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
}

/* Botão recolher sidebar */
button[kind="header"] {
    color: #1A2B4A !important;
}

.sidebar-brand {
    padding: 0.5rem 0 1.2rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.12);
    margin-bottom: 1rem;
}
.sidebar-brand-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.3;
}
.sidebar-brand-sub {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.55);
    margin-top: 0.25rem;
}
.sidebar-nav-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(255,255,255,0.45);
    font-weight: 600;
    margin-bottom: 0.6rem;
}
.sidebar-footer {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.4);
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,0.1);
    line-height: 1.4;
}

/* Gráficos Plotly — fundo sempre claro */
[data-testid="stPlotlyChart"] {
    background: transparent;
}
</style>
"""

CORES = {
    "navy": "#1A2B4A",
    "teal": "#2E86AB",
    "green": "#1B5E20",
    "orange": "#BF5700",
    "gray": "#94A3B8",
    "gray_dark": "#64748B",
    "light": "#F8F9FA",
    "bar_2025": "#94A3B8",
    "bar_2026": "#1A2B4A",
}

PALETA_REGIAO = ["#1A2B4A", "#2E86AB", "#4ECDC4", "#45B7D1", "#96CEB4"]

PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}


def aplicar_layout(
    fig: go.Figure,
    *,
    altura: int = 400,
    titulo: str | None = None,
    legenda: bool = True,
    margem_esq: int = 20,
    margem_dir: int = 24,
    margem_topo: int = 48,
    margem_base: int = 72,
) -> go.Figure:
    """Layout padronizado — evita título/legenda sobrepostos."""
    layout = dict(
        height=altura,
        barmode="group",
        bargap=0.28,
        bargroupgap=0.08,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, Segoe UI, sans-serif", size=12, color="#2C3E50"),
        margin=dict(l=margem_esq, r=margem_dir, t=margem_topo, b=margem_base),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=11, color="#475569"),
            title=None,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#EEF2F6",
            gridwidth=1,
            tickfont=dict(size=11, color="#475569"),
            title=None,
            zeroline=False,
        ),
        hoverlabel=dict(bgcolor="#1A2B4A", font_size=12, font_color="white"),
    )

    if titulo:
        layout["title"] = dict(
            text=titulo,
            x=0,
            xanchor="left",
            y=0.98,
            yanchor="top",
            font=dict(size=14, color="#1A2B4A", family="Inter, Segoe UI"),
        )
        layout["margin"]["t"] = margem_topo + 18

    if legenda:
        layout["legend"] = dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#E9ECEF",
            borderwidth=1,
            font=dict(size=11),
        )
        layout["margin"]["b"] = max(margem_base, 88)
    else:
        layout["showlegend"] = False

    fig.update_layout(**layout)
    return fig
