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
    padding: 2rem 2.2rem;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(26, 43, 74, 0.18);
}
.hero h1 { color: white !important; font-size: 1.85rem; margin: 0 0 0.4rem 0; font-weight: 700; line-height: 1.25; }
.hero p  { color: rgba(255,255,255,0.9); margin: 0; font-size: 1rem; line-height: 1.45; }

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
.kpi-delta-pos { color: #1B5E20; font-weight: 600; font-size: 0.9rem; display: flex; align-items: center; gap: 0.35rem; }
.kpi-delta-neg { color: #BF5700; font-weight: 600; font-size: 0.9rem; display: flex; align-items: center; gap: 0.35rem; }
.kpi-arrow { font-size: 1.05rem; font-weight: 700; line-height: 1; }
.kpi-value-up { color: #1B5E20 !important; }
.kpi-value-down { color: #BF5700 !important; }

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

/* Gráficos Plotly — caixa branca (sem wrapper HTML extra no Streamlit) */
.main [data-testid="stPlotlyChart"] {
    background: #FFFFFF;
    border-radius: 14px;
    border: 1px solid #E9ECEF;
    padding: 2.25rem 0.75rem 0.5rem 0.75rem;
    box-shadow: 0 2px 14px rgba(26, 43, 74, 0.05);
    margin-bottom: 0.5rem;
}

.portfolio-card {
    background: #FFFFFF;
    border-radius: 14px;
    border: 1px solid #E9ECEF;
    padding: 1.15rem 1.25rem;
    margin-bottom: 0.85rem;
    box-shadow: 0 4px 16px rgba(26, 43, 74, 0.07);
}
.portfolio-card.destaque {
    border-color: #2E86AB;
    background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFD 100%);
}
.portfolio-name {
    font-size: 0.92rem;
    font-weight: 700;
    color: #1A2B4A;
    margin-bottom: 0.45rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.portfolio-val {
    font-size: 1.35rem;
    font-weight: 700;
    color: #2E86AB;
    margin-bottom: 0.55rem;
}
.portfolio-metrics {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 0.15rem;
}
.portfolio-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.28rem 0.7rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
}
.portfolio-badge.pos { background: #E8F5E9; color: #1B5E20; }
.portfolio-badge.neg { background: #FFF3E0; color: #BF5700; }
.portfolio-ms {
    display: inline-flex;
    align-items: center;
    padding: 0.28rem 0.7rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    background: #E8F0F8;
    color: #1A2B4A;
    border: 1px solid #C5D9E8;
}
.portfolio-concorrente {
    display: inline-flex;
    align-items: center;
    padding: 0.28rem 0.7rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    background: #F1F3F5;
    color: #495057;
    border: 1px solid #DEE2E6;
}

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
.sidebar-brand-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.sidebar-brand-row img {
    height: 40px;
    width: auto;
    max-width: 92px;
    object-fit: contain;
    flex-shrink: 0;
    display: block;
}
.sidebar-brand-text {
    min-width: 0;
}
.sidebar-brand-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.3;
}
.sidebar-brand-sub {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.82);
    margin-top: 0.25rem;
}
.sidebar-nav-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(255,255,255,0.72);
    font-weight: 600;
    margin-bottom: 0.6rem;
}
.sidebar-footer {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.65);
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,0.1);
    line-height: 1.4;
}


/* ── Área principal: textos sempre legíveis (evita branco em fundo claro) ── */
.main label,
.main .stMarkdown,
.main .stMarkdown p,
.main [data-testid="stWidgetLabel"],
.main .stCaption,
.main h3,
.main h4 {
    color: #1A2B4A !important;
}
.main .stSlider label,
.main .stMultiSelect label,
.main .stTextInput label {
    color: #334155 !important;
    font-weight: 600 !important;
}
.main div[data-baseweb="select"] > div,
.main input {
    color: #1A2B4A !important;
    background-color: #FFFFFF !important;
}
.main .stAlert p,
.main [data-testid="stNotification"] {
    color: inherit !important;
}
.url-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 8px;
    padding: 0.35rem 0.75rem;
    font-size: 0.85rem;
    color: #FFFFFF !important;
    margin-top: 0.5rem;
    font-family: Consolas, 'Segoe UI', monospace;
}
.url-badge a {
    color: #B8E6F5 !important;
    text-decoration: none;
    font-weight: 600;
}
</style>
"""

FUNDO_PAGINA = "#F0F4F8"

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
    "modeBarButtonsToRemove": [
        "lasso2d",
        "select2d",
        "autoScale2d",
        "zoomIn2d",
        "zoomOut2d",
        "resetScale2d",
    ],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}

# Estilos inline (funcionam com st.html — não dependem de classes CSS externas)
BOX_CARD = (
    "background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;"
    "box-shadow:0 4px 18px rgba(26,43,74,0.08);"
)
BOX_PANEL = (
    "background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;"
    "box-shadow:0 6px 24px rgba(26,43,74,0.07);padding:1.1rem 1.25rem;"
)


def aplicar_layout(
    fig: go.Figure,
    *,
    altura: int = 400,
    titulo: str | None = None,
    legenda: bool = True,
    margem_esq: int = 20,
    margem_dir: int = 24,
        margem_topo: int = 56,
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
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#CBD5E1",
            borderwidth=1,
            font=dict(size=12, color="#1A2B4A"),
        )
        layout["margin"]["b"] = max(margem_base, 88)
    else:
        layout["showlegend"] = False

    fig.update_layout(**layout)
    return fig
