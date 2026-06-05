"""
Dashboard Comercial Danone NTR — ESTUDO_DANONE_MAT_MAIO (read-only).

Uso:
  streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from danone import (
    carregar_estudo,
    fmt_moeda,
    fmt_ms,
    fmt_pct,
    fmt_produto_curto,
    cards_panorama_visao_geral,
    resolver_planilha,
)
from danone.models import LinhaFaturamento

CACHE_ESTUDO_VERSAO = 5
from dashboard.theme import (
    BOX_CARD,
    BOX_PANEL,
    CORES,
    CSS,
    FUNDO_PAGINA,
    PALETA_REGIAO,
    PLOTLY_CONFIG,
    aplicar_layout,
)

st.set_page_config(
    page_title="Danone NTR — Dashboard Comercial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

def _inject_theme() -> None:
    if st.session_state.get('_theme_css'):
        return
    st.markdown(CSS, unsafe_allow_html=True)
    st.session_state['_theme_css'] = True


def _verificar_acesso() -> bool:
    """Senha opcional via .streamlit/secrets.toml ou Streamlit Cloud Secrets."""
    if st.session_state.get("autenticado"):
        return True

    try:
        senha_cfg = st.secrets.get("dashboard", {}).get("senha")
    except (FileNotFoundError, KeyError):
        senha_cfg = None

    if not senha_cfg:
        return True

    st.markdown("""
    <div class="hero">
        <h1>Dashboard Comercial — Danone NTR</h1>
        <p>Acesso restrito · Digite a senha fornecida pelo responsável</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        senha = st.text_input("Senha", type="password", placeholder="Senha de acesso")
        if st.button("Entrar", type="primary", use_container_width=True):
            if senha == senha_cfg:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    return False


@st.cache_data(show_spinner="Carregando estudo Danone…")
def _load(path: str, arquivo_mtime: float, versao: int = CACHE_ESTUDO_VERSAO):
    return carregar_estudo(Path(path))


@st.cache_data(show_spinner=False)
def _bytes_planilha_excel(path: str, arquivo_mtime: float, versao: int = CACHE_ESTUDO_VERSAO) -> bytes:
    from danone.reader import _resolver_leitura_planilha

    return _resolver_leitura_planilha(Path(path)).read_bytes()


def _seta(positivo: bool) -> str:
    return "↑" if positivo else "↓"


def _nome_laboratorio_top3(nome: str) -> str:
    """Unifica BABY/BRASIL/MEDICAL em um único rótulo DANONE no Top 3."""
    if "DANONE" in nome.upper():
        return "DANONE"
    return nome.strip()


def _unificar_top3_laboratorios(linhas: list[LinhaFaturamento]) -> list[LinhaFaturamento]:
    ordem: list[str] = []
    grupos: dict[str, list[LinhaFaturamento]] = {}
    for linha in linhas:
        nome = _nome_laboratorio_top3(linha.nome)
        if nome not in grupos:
            ordem.append(nome)
            grupos[nome] = []
        grupos[nome].append(linha)

    saida: list[LinhaFaturamento] = []
    for nome in ordem:
        itens = grupos[nome]
        fat25 = sum(i.fat_2025 or 0 for i in itens)
        fat26 = sum(i.fat_2026 or 0 for i in itens)
        cresc = (fat26 - fat25) / fat25 if fat25 else None
        if cresc is None and len(itens) == 1:
            cresc = itens[0].crescimento
        ms_vals = [i.market_share for i in itens if i.market_share is not None]
        ms = sum(ms_vals) if ms_vals else None
        saida.append(
            LinhaFaturamento(
                nome=nome,
                fat_2025=fat25,
                fat_2026=fat26,
                crescimento=cresc,
                market_share=ms,
            )
        )
    return saida


def _kpi_card(
    label: str,
    value: str,
    delta: str,
    positivo: bool = True,
    *,
    valor_com_seta: bool = False,
    delta_com_seta: bool = False,
) -> str:
    val_color = "#1A2B4A"
    if valor_com_seta:
        val_color = "#1B5E20" if positivo else "#BF5700"
        value = f"{_seta(positivo)} {value}"

    if delta_com_seta:
        delta_color = "#1B5E20" if positivo else "#BF5700"
        delta_html = f'<div style="color:{delta_color};font-size:0.88rem;font-weight:600;margin-top:0.45rem;">{_seta(positivo)} {delta}</div>'
    else:
        delta_html = f'<div style="color:#6C757D;font-size:0.82rem;margin-top:0.45rem;">{delta}</div>'

    return (
        f'<div style="{BOX_CARD}padding:1.2rem 1.35rem;min-height:118px;">'
        f'<div style="font-size:0.7rem;color:#6C757D;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">{label}</div>'
        f'<div style="font-size:1.5rem;font-weight:700;color:{val_color};margin:0.4rem 0 0 0;line-height:1.2;">{value}</div>'
        f"{delta_html}"
        f"</div>"
    )


def _kpi_row_html(total) -> str:
    pos = (total.crescimento or 0) >= 0
    cards = [
        _kpi_card("Faturamento Abr/25", fmt_moeda(total.fat_2025, True), "Base comparativa"),
        _kpi_card("Faturamento Abr/26", fmt_moeda(total.fat_2026, True), "Período atual"),
        _kpi_card(
            "Crescimento YoY",
            fmt_pct(total.crescimento),
            "vs. ano anterior",
            pos,
            valor_com_seta=True,
            delta_com_seta=True,
        ),
    ]
    if total.unidades_2025 and total.unidades_2026:
        cresc_u = (total.unidades_2026 - total.unidades_2025) / total.unidades_2025
        cards.append(
            _kpi_card(
                "Unidades Abr/26",
                f"{total.unidades_2026:,.0f}".replace(",", "."),
                fmt_pct(cresc_u),
                cresc_u >= 0,
                valor_com_seta=True,
                delta_com_seta=True,
            )
        )
    n = len(cards)
    return (
        f'<div style="display:grid;grid-template-columns:repeat({n},minmax(0,1fr));'
        f'gap:1rem;margin:0 0 1.5rem 0;">{"".join(cards)}</div>'
    )


def _portfolio_card(
    nome: str,
    valor: str,
    cresc: str,
    positivo: bool,
    *,
    market_share: float | None = None,
    destaque: bool = False,
    subtitulo: str = "",
    ms_rotulo: str = "Participação de mercado %",
) -> str:
    badge_bg = "#E8F5E9" if positivo else "#FFF3E0"
    badge_fg = "#1B5E20" if positivo else "#BF5700"
    border = "1px solid #2E86AB" if destaque else "1px solid #E2E8F0"
    bg = "linear-gradient(180deg,#FFFFFF 0%,#F5FAFC 100%)" if destaque else "#FFFFFF"

    ms_pct = (market_share or 0) * 100
    ms_largura = min(max(ms_pct, 0), 100)
    ms_texto = fmt_ms(market_share) if market_share is not None else "—"
    ms_bloco = (
        f'<div style="margin-top:0.75rem;padding:0.7rem 0.85rem;background:#F0F7FC;'
        f'border-radius:10px;border:1px solid #D4E8F4;">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:0.5rem;">'
        f'<span style="font-size:0.68rem;font-weight:600;color:#64748B;text-transform:uppercase;'
        f'letter-spacing:0.06em;">{ms_rotulo}</span>'
        f'<span style="font-size:1.08rem;font-weight:700;color:#1A2B4A;white-space:nowrap;">'
        f"{ms_texto}</span></div>"
        f'<div style="margin-top:0.45rem;height:6px;background:#E2E8F0;border-radius:999px;overflow:hidden;">'
        f'<div style="width:{ms_largura:.1f}%;height:100%;background:linear-gradient(90deg,#2E86AB,#5BA4C9);'
        f'border-radius:999px;"></div></div></div>'
    )

    return (
        f'<div style="background:{bg};border:{border};border-radius:14px;'
        f'padding:1.15rem 1.25rem;margin-bottom:0.85rem;'
        f'box-shadow:0 4px 16px rgba(26,43,74,0.06);">'
        f'<div style="font-size:0.9rem;font-weight:700;color:#1A2B4A;text-transform:uppercase;letter-spacing:0.04em;">{nome}</div>'
        + (
            f'<div style="font-size:0.78rem;color:#64748B;margin:0.2rem 0 0.35rem 0;line-height:1.35;">{subtitulo}</div>'
            if subtitulo
            else ""
        )
        + f'<div style="font-size:1.35rem;font-weight:700;color:#2E86AB;margin:0.45rem 0;">{valor}</div>'
        f'<span style="display:inline-flex;align-items:center;gap:0.25rem;padding:0.3rem 0.75rem;'
        f'border-radius:999px;background:{badge_bg};color:{badge_fg};font-size:0.82rem;font-weight:600;">'
        f"{_seta(positivo)} {cresc}</span>"
        f"{ms_bloco}"
        f"</div>"
    )


def _section_title(texto: str) -> str:
    return (
        f'<div style="font-size:1.15rem;font-weight:700;color:#1A2B4A;margin:1.25rem 0 1rem 0;'
        f'padding-bottom:0.4rem;border-bottom:2px solid #2E86AB;">{texto}</div>'
    )


def _bar_comparativo(
    df: pd.DataFrame,
    nome_col: str,
    titulo: str,
    horizontal: bool = False,
) -> go.Figure:
    n = len(df)
    if horizontal:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Abr/25",
            y=df[nome_col],
            x=df["fat_2025"],
            orientation="h",
            marker=dict(color=CORES["bar_2025"], cornerradius=4),
            text=[f"R$ {v/1e6:.1f}M" if v >= 1e6 else f"R$ {v/1e3:.0f}K" for v in df["fat_2025"]],
            textposition="outside",
            textfont=dict(size=10, color="#64748B"),
            cliponaxis=False,
        ))
        fig.add_trace(go.Bar(
            name="Abr/26",
            y=df[nome_col],
            x=df["fat_2026"],
            orientation="h",
            marker=dict(color=CORES["bar_2026"], cornerradius=4),
            text=[f"R$ {v/1e6:.1f}M" if v >= 1e6 else f"R$ {v/1e3:.0f}K" for v in df["fat_2026"]],
            textposition="outside",
            textfont=dict(size=10, color="#1A2B4A"),
            cliponaxis=False,
        ))
        altura = max(340, n * 52 + 100)
        aplicar_layout(fig, altura=altura, titulo=titulo, margem_esq=120, margem_dir=80, margem_base=90)
        fig.update_xaxes(tickformat=".2s", showgrid=True, gridcolor="#EEF2F6")
        fig.update_yaxes(tickfont=dict(size=11))
    else:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Abr/25",
            x=df[nome_col],
            y=df["fat_2025"],
            marker=dict(color=CORES["bar_2025"], cornerradius=6),
            width=0.35,
        ))
        fig.add_trace(go.Bar(
            name="Abr/26",
            x=df[nome_col],
            y=df["fat_2026"],
            marker=dict(color=CORES["bar_2026"], cornerradius=6),
            width=0.35,
        ))
        altura = max(400, 320)
        aplicar_layout(fig, altura=altura, titulo=titulo, margem_topo=62, margem_base=95)
        fig.update_yaxes(tickformat=".2s")
        fig.update_xaxes(tickangle=0, tickfont=dict(size=11))

    return fig


def _grafico_crescimento_horizontal(
    df: pd.DataFrame,
    nome_col: str,
    titulo: str,
) -> go.Figure:
    df = df.copy()
    df["cresc_pct"] = df["crescimento"] * 100
    df["cor"] = df["cresc_pct"].apply(lambda v: CORES["green"] if v >= 0 else CORES["orange"])

    fig = go.Figure(go.Bar(
        x=df["cresc_pct"],
        y=df[nome_col],
        orientation="h",
        marker=dict(color=df["cor"], cornerradius=4),
        text=[f"{v:+.1f}%".replace(".", ",") for v in df["cresc_pct"]],
        textposition="outside",
        textfont=dict(size=10, color="#475569"),
        cliponaxis=False,
    ))
    aplicar_layout(
        fig,
        altura=max(360, len(df) * 48 + 100),
        titulo=titulo,
        legenda=False,
        margem_esq=100,
        margem_dir=60,
        margem_base=50,
    )
    fig.update_xaxes(title="Crescimento YoY (%)", zeroline=True, zerolinecolor="#CBD5E1")
    fig.add_vline(x=0, line_width=1, line_color="#CBD5E1")
    return fig


def _html(html: str) -> None:
    st.markdown(html.strip(), unsafe_allow_html=True)


def _pasta_logo_danone() -> Path | None:
    """Pasta logo danone na raiz do projeto."""
    for nome in ("logo danone", "logo Danone", "Logo Danone"):
        direto = ROOT / nome
        if direto.is_dir():
            return direto
    for item in ROOT.iterdir():
        if item.is_dir() and item.name.lower().replace(" ", "") == "logodanone":
            return item
    return None


def _resolver_logo_danone() -> Path | None:
    """Logo Danone para sidebar (prefere versão clara/branca)."""
    pasta = _pasta_logo_danone()
    if pasta:
        preferidos = (
            "Logo Danone - Branco.png",
            "Logo Danone Branco.png",
            "logo_danone_branco.png",
            "Danone_logo_white.png",
            "Logo Danone.png",
            "logo_danone.png",
            "Danone.png",
        )
        for nome in preferidos:
            caminho = pasta / nome
            if caminho.is_file():
                return caminho.resolve()
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.svg"):
            arquivos = sorted(pasta.glob(ext))
            if arquivos:
                return arquivos[0].resolve()

    for nome in ("logo_danone.png", "logo_danone.jpg", "logo_danone.webp"):
        caminho = ROOT / "assets" / nome
        if caminho.is_file():
            return caminho.resolve()
    return None


@st.cache_data(show_spinner=False)
def _logo_danone_sidebar_bytes(caminho: str) -> tuple[bytes, str]:
    """Ajusta logo com fundo escuro para a sidebar (#1A2B4A)."""
    import io
    from pathlib import Path as P

    path = P(caminho)
    suffix = path.suffix.lower()
    if suffix == ".svg":
        return path.read_bytes(), "image/svg+xml"

    try:
        from PIL import Image
    except ImportError:
        raw = path.read_bytes()
        mime = "image/png" if suffix == ".png" else "image/jpeg"
        return raw, mime

    fundo = (26, 43, 74)  # #1A2B4A — sidebar
    img = Image.open(path).convert("RGBA")
    pixels = img.load()
    largura, altura = img.size
    for y in range(altura):
        for x in range(largura):
            r, g, b, a = pixels[x, y]
            if a < 10:
                pixels[x, y] = (*fundo, 255)
            elif r < 50 and g < 50 and b < 50:
                pixels[x, y] = (*fundo, 255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), "image/png"


def _render_sidebar_brand() -> None:
    logo = _resolver_logo_danone()
    if logo:
        dados, _ = _logo_danone_sidebar_bytes(str(logo))
        st.sidebar.image(dados, width=72)
    st.sidebar.markdown("### Danone NTR")
    st.sidebar.caption("Dashboard Comercial · MAT MAIO")
    st.sidebar.divider()
    st.sidebar.markdown("**Navegação**")

def _pasta_logo_abrafad() -> Path | None:
    """Pasta logo Abrafad na raiz do projeto."""
    direto = ROOT / "logo Abrafad"
    if direto.is_dir():
        return direto
    for item in ROOT.iterdir():
        if item.is_dir() and item.name.lower().replace(" ", "") == "logoabrafad":
            return item
    return None


def _resolver_logo_abrafad() -> Path | None:
    """Logo oficial — pasta logo Abrafad/ (arquivo original, sem alterar)."""
    pasta = _pasta_logo_abrafad()
    if pasta:
        preferidos = (
            "Logo ABRAFAD - Branco.png",
            "Logo ABRAFAD - Branco (3).png",
            "Logo ABRAFAD - Branco (2).png",
        )
        for nome in preferidos:
            caminho = pasta / nome
            if caminho.is_file():
                return caminho.resolve()
        pngs = sorted(pasta.glob("*.png"))
        if pngs:
            return pngs[0].resolve()

    for nome in ("logo_abrafad.png", "logo_abrafad.jpg", "logo_abrafad.webp"):
        caminho = ROOT / "assets" / nome
        if caminho.is_file():
            return caminho.resolve()
    return None


def _nome_abrafad_html() -> str:
    """Fallback: só o nome, igual à marca (ABRA negrito + FAD claro)."""
    return (
        '<div style="display:flex;align-items:center;gap:0;line-height:1;">'
        '<span style="font-family:Segoe UI,Arial,sans-serif;font-size:2rem;'
        'font-weight:700;color:#3D4450;letter-spacing:-0.02em;">ABRA</span>'
        '<span style="font-family:Segoe UI,Arial,sans-serif;font-size:2rem;'
        'font-weight:300;color:#8B939C;letter-spacing:-0.02em;">FAD</span>'
        "</div>"
    )


@st.cache_data(show_spinner=False)
def _logo_abrafad_fundo_pagina(caminho: str) -> bytes:
    """Ajusta PNG (fundo preto + texto branco) para o fundo claro da página."""
    import io

    from PIL import Image

    fundo = (240, 244, 248)  # #F0F4F8 — igual ao fundo do dashboard
    texto = (61, 68, 80)  # cinza escuro do logotipo em fundo claro

    img = Image.open(caminho).convert("RGBA")
    pixels = img.load()
    largura, altura = img.size
    for y in range(altura):
        for x in range(largura):
            r, g, b, a = pixels[x, y]
            if a < 10:
                pixels[x, y] = (*fundo, 255)
            elif r < 55 and g < 55 and b < 55:
                pixels[x, y] = (*fundo, 255)
            elif r > 185 and g > 185 and b > 185:
                pixels[x, y] = (*texto, a)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _cabecalho_abrafad() -> None:
    """Logo ABRAFAD no topo — fundo igual ao da página."""
    logo = _resolver_logo_abrafad()
    if logo:
        with st.container(border=True):
            st.image(_logo_abrafad_fundo_pagina(str(logo)), width=200)
    else:
        with st.container(border=True):
            _html(_nome_abrafad_html())
            st.caption("Coloque os PNG em `logo Abrafad/` na pasta do projeto.")


def _plot(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)


def _grafico_market_share(
    df: pd.DataFrame,
    nome_col: str,
    titulo: str,
    *,
    horizontal: bool = True,
) -> go.Figure:
    df = df.copy()
    df = df[df["market_share"].notna() & (df["market_share"] > 0)]
    if df.empty:
        fig = go.Figure()
        aplicar_layout(fig, altura=200, titulo=titulo, legenda=False)
        return fig

    df["ms_pct"] = df["market_share"] * 100
    df = df.sort_values("ms_pct", ascending=True)

    fig = go.Figure(go.Bar(
        x=df["ms_pct"],
        y=df[nome_col],
        orientation="h" if horizontal else "v",
        marker=dict(color=CORES["teal"], cornerradius=4),
        text=[f"{v:.1f}%".replace(".", ",") for v in df["ms_pct"]],
        textposition="outside",
        textfont=dict(size=11, color="#1A2B4A"),
        cliponaxis=False,
    ))
    aplicar_layout(
        fig,
        altura=max(360, len(df) * 42 + 100),
        titulo=titulo,
        legenda=False,
        margem_esq=120 if horizontal else 20,
        margem_dir=70,
        margem_base=50,
    )
    fig.update_xaxes(title="Market Share %", ticksuffix="%")
    return fig


def main() -> None:
    _inject_theme()

    if not _verificar_acesso():
        return

    _render_sidebar_brand()

    pagina = st.sidebar.radio(
        "Seção",
        [
            "Visão Geral",
            "Market Share",
            "Regional",
            "Produtos",
            "Bandeiras",
            "Concorrência",
            "Impactos",
            "Explorador",
        ],
        label_visibility="collapsed",
    )

    path = resolver_planilha()
    with st.sidebar.expander("Fonte de dados", expanded=False):
        st.caption(f"Pasta: `dados/`")
        st.code(str(path), language=None)
        planilha_input = st.text_input(
            "Outro caminho (opcional)",
            value="",
            placeholder=str(path),
            key="planilha_caminho_opcional",
            label_visibility="collapsed",
        )
        if planilha_input.strip():
            candidato = Path(planilha_input.strip())
            if candidato.exists():
                path = candidato.resolve()
            else:
                st.sidebar.warning("Caminho inválido — usando planilha em dados/.")

    st.sidebar.caption(f"Base: {path.name}")
    st.sidebar.caption("Leitura automática · Excel intacto")

    if not path.exists():
        st.error(
            f"Planilha não encontrada em **dados/**.\n\n"
            f"Esperado: `dados/ESTUDO_DANONE_MAT_MAIO1.xlsx`\n\n"
            f"Caminho testado: `{path}`"
        )
        st.stop()

    mtime = path.stat().st_mtime if path.exists() else 0.0
    estudo = _load(str(path), mtime)

    _cabecalho_abrafad()

    _html(
        f'<div style="background:linear-gradient(135deg,#1A2B4A 0%,#2E86AB 100%);border-radius:16px;'
        f'padding:2rem 2.2rem;color:white;margin-bottom:1.5rem;'
        f'box-shadow:0 8px 32px rgba(26,43,74,0.18);">'
        f'<h1 style="color:white;font-size:1.85rem;margin:0 0 0.4rem 0;font-weight:700;">'
        f"Dashboard Comercial — Danone NTR</h1>"
        f'<p style="color:rgba(255,255,255,0.92);margin:0;font-size:1rem;">'
        f"{estudo.periodo_label} · Fonte: {path.name} · Leitura automática (Python, sem alterar o Excel)</p>"
        f"</div>"
    )

    # ── VISÃO GERAL ──
    if pagina == "Visão Geral":
        total = estudo.total_ntr
        if total:
            _html(_kpi_row_html(total))

        _html(_section_title("Danone — Brasil, ABRAFAD e Concorrentes"))
        cards_panorama = cards_panorama_visao_geral(estudo, path)
        if cards_panorama:
            df_p = pd.DataFrame([{
                "Recorte": c.titulo,
                "fat_2025": c.fat_2025,
                "fat_2026": c.fat_2026,
                "crescimento": c.crescimento,
            } for c in cards_panorama])

            cards_html = ""
            for c in cards_panorama:
                pos = (c.crescimento or 0) >= 0
                cards_html += _portfolio_card(
                    c.titulo,
                    fmt_moeda(c.fat_2026, True),
                    fmt_pct(c.crescimento),
                    pos,
                    market_share=c.market_share,
                    destaque=c.destaque,
                    subtitulo=c.subtitulo,
                    ms_rotulo=c.ms_rotulo,
                )

            col_g, col_t = st.columns([1.65, 1], gap="large")
            with col_g:
                with st.container(border=True):
                    _plot(_bar_comparativo(
                        df_p,
                        "Recorte",
                        "Faturamento Danone — Brasil, canal ABRAFAD e vs concorrentes",
                    ))
            with col_t:
                _html(f'<div style="{BOX_PANEL}">{cards_html}</div>')

        _html(_section_title("Top 3 Laboratórios (mercado)"))
        if estudo.laboratorios_top3:
            top3 = _unificar_top3_laboratorios(estudo.laboratorios_top3)
            df_t3 = pd.DataFrame([{
                "Laboratório": l.nome,
                "fat_2025": l.fat_2025,
                "fat_2026": l.fat_2026,
                "crescimento": l.crescimento,
                "market_share": l.market_share,
            } for l in top3])
            _plot(_bar_comparativo(df_t3, "Laboratório", "Comparativo Top 3 — faturamento"))
            for l in top3:
                seta = _seta((l.crescimento or 0) >= 0)
                ms = f" · MS {fmt_ms(l.market_share)}" if l.market_share else ""
                st.markdown(
                    f'<div class="insight-box">{l.nome}: {fmt_moeda(l.fat_2026, True)} · '
                    f'<b>{seta} {fmt_pct(l.crescimento)}</b>{ms}</div>',
                    unsafe_allow_html=True,
                )

    # ── MARKET SHARE ──
    elif pagina == "Market Share":
        st.markdown('<div class="section-title">Market Share % — Panorama</div>', unsafe_allow_html=True)

        if estudo.total_ntr and estudo.total_ntr.market_share:
            st.markdown(
                f'<div class="insight-box">📊 <b>Danone NTR</b> representa '
                f'<b>{fmt_ms(estudo.total_ntr.market_share)}</b> do mercado mapeado no estudo.</div>',
                unsafe_allow_html=True,
            )

        if estudo.laboratorios_ranking:
            df_ms = pd.DataFrame([{
                "Laboratório": l.nome,
                "market_share": l.market_share,
                "fat_2026": l.fat_2026,
                "crescimento": l.crescimento,
            } for l in estudo.laboratorios_ranking if l.market_share])
            top_ms = df_ms.nlargest(15, "market_share")
            _plot(_grafico_market_share(top_ms, "Laboratório", "Top 15 — Market Share por laboratório"))

            st.dataframe(
                top_ms.sort_values("market_share", ascending=False).assign(
                    **{
                        "Market Share %": lambda d: d["market_share"].map(lambda v: fmt_ms(v)),
                        "Faturamento Abr/26": lambda d: d["fat_2026"].map(lambda v: fmt_moeda(v, True)),
                        "Crescimento YoY": lambda d: d["crescimento"].map(fmt_pct),
                    }
                )[["Laboratório", "Market Share %", "Faturamento Abr/26", "Crescimento YoY"]],
                use_container_width=True,
                hide_index=True,
            )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-title">Market Share por Região</div>', unsafe_allow_html=True)
            if estudo.regioes:
                df_r = pd.DataFrame([{
                    "Região": r.nome.title(),
                    "market_share": r.market_share,
                } for r in estudo.regioes if r.market_share])
                _plot(_grafico_market_share(df_r, "Região", "Participação regional"))
        with c2:
            st.markdown('<div class="section-title">Market Share — Top Bandeiras</div>', unsafe_allow_html=True)
            if estudo.bandeiras:
                df_b = pd.DataFrame([{
                    "Bandeira": b.nome.title(),
                    "market_share": b.market_share,
                } for b in estudo.bandeiras[:10] if b.market_share])
                _plot(_grafico_market_share(df_b, "Bandeira", "ABRAFAD — share no canal"))

    # ── REGIONAL ──
    elif pagina == "Regional":
        st.markdown('<div class="section-title">Performance por Região</div>', unsafe_allow_html=True)
        if estudo.regioes:
            df_r = pd.DataFrame([{
                "Região": r.nome.title(),
                "fat_2025": r.fat_2025,
                "fat_2026": r.fat_2026,
                "crescimento": r.crescimento,
                "market_share": r.market_share,
            } for r in estudo.regioes])
            c1, c2 = st.columns(2)
            with c1:
                _plot(_bar_comparativo(df_r, "Região", "Faturamento por região"))
            with c2:
                df_r2 = df_r.sort_values("crescimento", ascending=True)
                _plot(_grafico_crescimento_horizontal(df_r2, "Região", "Crescimento YoY por região"))

            if df_r["market_share"].notna().any():
                st.markdown('<div class="section-title">Market Share por Região</div>', unsafe_allow_html=True)
                _plot(_grafico_market_share(df_r, "Região", "Participação de mercado regional"))

            lider = max(estudo.regioes, key=lambda x: x.crescimento or -999)
            maior = max(estudo.regioes, key=lambda x: x.fat_2026)
            st.markdown(
                f'<div class="insight-box pos">📍 <b>Prioridade comercial:</b> {lider.nome.title()} '
                f'lidera crescimento ({fmt_pct(lider.crescimento)}). '
                f'{maior.nome.title()} concentra maior faturamento ({fmt_moeda(maior.fat_2026, True)}).</div>',
                unsafe_allow_html=True,
            )

    # ── PRODUTOS ──
    elif pagina == "Produtos":
        st.markdown('<div class="section-title">Ranking de Produtos</div>', unsafe_allow_html=True)
        prod = estudo.produtos.copy()
        prod = prod[prod["fat_2025"] > 0]
        prod["nome_curto"] = prod["Produto"].apply(fmt_produto_curto)

        filtro_reg = st.multiselect(
            "Filtrar por região",
            sorted(estudo.dados_detalhe["Regiao"].dropna().unique()),
        )
        if filtro_reg:
            base = estudo.dados_detalhe[estudo.dados_detalhe["Regiao"].isin(filtro_reg)]
            prod = (
                base.groupby("Produto", as_index=False)
                .agg(fat_2025=("fat_2025", "sum"), fat_2026=("fat_2026", "sum"))
            )
            prod["delta_fat"] = prod["fat_2026"] - prod["fat_2025"]
            prod["crescimento"] = prod["delta_fat"] / prod["fat_2025"]
            prod["nome_curto"] = prod["Produto"].apply(fmt_produto_curto)

        top_n = st.slider("Top N produtos", 5, 20, 10)
        top_fat = prod.nlargest(top_n, "fat_2026")
        top_cresc = prod[prod["fat_2026"] > 1_000_000].nlargest(5, "crescimento")
        pior_cresc = prod[prod["fat_2025"] > 1_000_000].nsmallest(5, "crescimento")

        c1, c2 = st.columns([1.6, 1])
        with c1:
            top_fat_ord = top_fat.sort_values("fat_2026")
            fig = go.Figure(go.Bar(
                x=top_fat_ord["fat_2026"],
                y=top_fat_ord["nome_curto"],
                orientation="h",
                marker=dict(color=CORES["bar_2026"], cornerradius=4),
            ))
            aplicar_layout(
                fig,
                altura=max(420, top_n * 38 + 120),
                titulo=f"Top {top_n} produtos — faturamento Abr/26",
                legenda=False,
                margem_esq=160,
                margem_dir=40,
            )
            fig.update_xaxes(tickformat=".2s")
            _plot(fig)
        with c2:
            st.markdown("**🚀 Maiores crescimentos** (fat > R$ 1 mi)")
            for _, r in top_cresc.iterrows():
                st.markdown(f"• {fmt_produto_curto(r['Produto'])} — **{fmt_pct(r['crescimento'])}**")
            st.markdown("**⚠️ Maiores quedas** (fat > R$ 1 mi)")
            for _, r in pior_cresc.iterrows():
                st.markdown(f"• {fmt_produto_curto(r['Produto'])} — **{fmt_pct(r['crescimento'])}**")

    # ── BANDEIRAS ──
    elif pagina == "Bandeiras":
        st.markdown('<div class="section-title">Ranking ABRAFAD — Bandeiras</div>', unsafe_allow_html=True)
        if estudo.bandeiras:
            top_b = estudo.bandeiras[:12]
            df_b = pd.DataFrame([{
                "Bandeira": b.nome.title(),
                "fat_2025": b.fat_2025,
                "fat_2026": b.fat_2026,
                "crescimento": b.crescimento,
                "market_share": b.market_share,
            } for b in top_b])
            _plot(
                _bar_comparativo(
                    df_b.sort_values("fat_2026"),
                    "Bandeira",
                    "Top bandeiras — faturamento Danone",
                    horizontal=True,
                )
            )
            lider = top_b[0]
            ms_txt = f" · MS {fmt_ms(lider.market_share)}" if lider.market_share else ""
            st.markdown(
                f'<div class="insight-box">🏪 <b>{lider.nome.title()}</b> lidera o canal mapeado '
                f'({fmt_moeda(lider.fat_2026, True)} · {fmt_pct(lider.crescimento)}{ms_txt}). '
                f'Foco comercial: redes com maior tração e share incremental.</div>',
                unsafe_allow_html=True,
            )
            if df_b["market_share"].notna().any():
                st.markdown('<div class="section-title">Market Share — Bandeiras</div>', unsafe_allow_html=True)
                _plot(_grafico_market_share(df_b.head(10), "Bandeira", "Share no ranking ABRAFAD"))

    # ── CONCORRÊNCIA ──
    elif pagina == "Concorrência":
        st.markdown('<div class="section-title">Panorama Competitivo</div>', unsafe_allow_html=True)
        if estudo.laboratorios_ranking:
            df_c = pd.DataFrame([{
                "Laboratório": l.nome,
                "fat_2026": l.fat_2026,
                "crescimento": l.crescimento,
                "market_share": l.market_share,
            } for l in estudo.laboratorios_ranking[:15]])
            df_c = df_c.sort_values("fat_2026")
            fig = go.Figure(go.Bar(
                x=df_c["fat_2026"],
                y=df_c["Laboratório"],
                orientation="h",
                marker=dict(
                    color=df_c["crescimento"],
                    colorscale=[[0, CORES["orange"]], [0.5, "#E2E8F0"], [1, CORES["green"]]],
                    cmin=df_c["crescimento"].min(),
                    cmax=df_c["crescimento"].max(),
                    cornerradius=4,
                ),
                text=[fmt_pct(c) for c in df_c["crescimento"]],
                textposition="outside",
                textfont=dict(size=10, color="#475569"),
            ))
            aplicar_layout(
                fig,
                altura=max(520, len(df_c) * 34 + 100),
                titulo="Top 15 laboratórios — faturamento Abr/26",
                legenda=False,
                margem_esq=140,
                margem_dir=70,
            )
            fig.update_xaxes(tickformat=".2s")
            _plot(fig)

            df_ms_c = df_c[df_c["market_share"].notna() & (df_c["market_share"] > 0)]
            if not df_ms_c.empty:
                st.markdown('<div class="section-title">Market Share — Laboratórios</div>', unsafe_allow_html=True)
                _plot(_grafico_market_share(
                    df_ms_c.rename(columns={"Laboratório": "Laboratório"}),
                    "Laboratório",
                    "Share de mercado (Top 15)",
                ))

        if estudo.concorrentes:
            st.markdown("**Ambiente concorrente (aba CONCORRENTE)**")
            for c in estudo.concorrentes[:5]:
                st.markdown(f"• {c.nome}: {fmt_moeda(c.fat_2026, True)} · {fmt_pct(c.crescimento)}")

    # ── IMPACTOS ──
    elif pagina == "Impactos":
        st.markdown('<div class="section-title">Impactos Positivos e Negativos</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🟢 Destaques positivos")
            for p in estudo.impactos_positivos[:5]:
                delta = fmt_moeda(p.delta_abs, True) if p.delta_abs else ""
                st.markdown(
                    f'<div class="insight-box pos"><b>{fmt_produto_curto(p.nome)}</b><br>'
                    f'{fmt_pct(p.crescimento)} · {fmt_moeda(p.fat_2025, True)} → {fmt_moeda(p.fat_2026, True)}'
                    f'{" · Δ " + delta if delta else ""}</div>',
                    unsafe_allow_html=True,
                )
        with c2:
            st.markdown("#### 🟠 Pontos de alerta")
            for p in estudo.impactos_negativos[:5]:
                delta = fmt_moeda(abs(p.delta_abs), True) if p.delta_abs else ""
                st.markdown(
                    f'<div class="insight-box neg"><b>{fmt_produto_curto(p.nome)}</b><br>'
                    f'{fmt_pct(p.crescimento)} · {fmt_moeda(p.fat_2025, True)} → {fmt_moeda(p.fat_2026, True)}'
                    f'{" · Perda " + delta if delta else ""}</div>',
                    unsafe_allow_html=True,
                )

    # ── EXPLORADOR ──
    elif pagina == "Explorador":
        st.markdown('<div class="section-title">Explorador de Dados</div>', unsafe_allow_html=True)
        _html(
            '<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;'
            'padding:1.25rem 1.4rem;margin-bottom:1.25rem;box-shadow:0 4px 16px rgba(26,43,74,0.06);">'
            '<div style="font-size:1rem;font-weight:700;color:#1A2B4A;margin-bottom:0.35rem;">'
            "Planilha fonte do estudo</div>"
            '<p style="color:#64748B;font-size:0.9rem;margin:0 0 1rem 0;line-height:1.5;">'
            f"Arquivo <b>{path.name}</b> — todas as abas (Ranking, Análise Básica, Dados, etc.). "
            "Baixe para abrir no Excel e explorar os dados completos.</p></div>"
        )
        try:
            excel_bytes = _bytes_planilha_excel(str(path), mtime)
            st.download_button(
                label="Baixar planilha Excel (.xlsx)",
                data=excel_bytes,
                file_name=path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
        except OSError as err:
            st.error(f"Não foi possível ler a planilha para download: {err}")

        st.markdown(
            '<div class="section-title" style="margin-top:1.5rem;">Filtros — aba Dados</div>',
            unsafe_allow_html=True,
        )
        df = estudo.dados_detalhe
        cols_filtro = st.columns(4)
        regioes = sorted(df["Regiao"].dropna().unique())
        ufs = sorted(df["UF"].dropna().unique())
        bandeiras = sorted(df["Bandeira"].dropna().unique())

        with cols_filtro[0]:
            f_reg = st.multiselect("Região", regioes)
        with cols_filtro[1]:
            f_uf = st.multiselect("UF", ufs)
        with cols_filtro[2]:
            f_band = st.multiselect("Bandeira", bandeiras)
        with cols_filtro[3]:
            f_prod = st.text_input("Buscar produto")

        filtrado = df.copy()
        if f_reg:
            filtrado = filtrado[filtrado["Regiao"].isin(f_reg)]
        if f_uf:
            filtrado = filtrado[filtrado["UF"].isin(f_uf)]
        if f_band:
            filtrado = filtrado[filtrado["Bandeira"].isin(f_band)]
        if f_prod:
            filtrado = filtrado[filtrado["Produto"].str.contains(f_prod, case=False, na=False)]

        agg = (
            filtrado.groupby(["Produto", "Regiao", "UF"], as_index=False)
            .agg(fat_2025=("fat_2025", "sum"), fat_2026=("fat_2026", "sum"))
        )
        agg["crescimento"] = (agg["fat_2026"] - agg["fat_2025"]) / agg["fat_2025"]

        st.dataframe(
            agg.sort_values("fat_2026", ascending=False).head(200),
            use_container_width=True,
            column_config={
                "fat_2025": st.column_config.NumberColumn("Abr/25", format="R$ %.2f"),
                "fat_2026": st.column_config.NumberColumn("Abr/26", format="R$ %.2f"),
                "crescimento": st.column_config.NumberColumn("YoY", format="%.2%%"),
            },
        )
        st.caption(f"{len(filtrado):,} linhas filtradas · Planilha não alterada".replace(",", "."))


if __name__ == "__main__":
    main()
