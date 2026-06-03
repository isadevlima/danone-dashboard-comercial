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

from danone import PLANILHA_FONTE, carregar_estudo, fmt_moeda, fmt_pct, fmt_produto_curto
from dashboard.theme import CORES, CSS, PALETA_REGIAO, PLOTLY_CONFIG, aplicar_layout

st.set_page_config(
    page_title="Danone NTR — Dashboard Comercial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CSS, unsafe_allow_html=True)


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
def _load(path: str):
    return carregar_estudo(Path(path))


def _kpi_card(label: str, value: str, delta: str, positivo: bool = True) -> str:
    cls = "kpi-delta-pos" if positivo else "kpi-delta-neg"
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="{cls}">{delta}</div>
    </div>
    """


def _portfolio_card(nome: str, valor: str, cresc: str, positivo: bool) -> str:
    badge_cls = "pos" if positivo else "neg"
    return f"""
    <div class="portfolio-card">
        <div class="portfolio-name">{nome}</div>
        <div class="portfolio-val">{valor}</div>
        <span class="portfolio-badge {badge_cls}">{cresc}</span>
    </div>
    """


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
        aplicar_layout(fig, altura=altura, titulo=titulo, margem_base=95)
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


def _plot(fig: go.Figure) -> None:
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
    st.markdown("</div>", unsafe_allow_html=True)



def main() -> None:
    if not _verificar_acesso():
        return

    st.sidebar.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-title">Danone NTR</div>
        <div class="sidebar-brand-sub">Dashboard Comercial · MAT MAIO</div>
    </div>
    <div class="sidebar-nav-label">Navegação</div>
    """, unsafe_allow_html=True)

    pagina = st.sidebar.radio(
        "Seção",
        [
            "Visão Geral",
            "Regional",
            "Produtos",
            "Bandeiras",
            "Concorrência",
            "Impactos",
            "Explorador",
        ],
        label_visibility="collapsed",
    )

    path = PLANILHA_FONTE
    with st.sidebar.expander("Fonte de dados", expanded=False):
        planilha_input = st.text_input("Planilha (read-only)", str(PLANILHA_FONTE), label_visibility="collapsed")
        if planilha_input.strip():
            path = Path(planilha_input.strip())

    st.sidebar.markdown(
        f'<div class="sidebar-footer">Base: {path.name}<br>Leitura automática · Excel intacto</div>',
        unsafe_allow_html=True,
    )

    if not path.exists():
        st.error(f"Planilha não encontrada: {path}")
        st.stop()

    estudo = _load(str(path))

    st.markdown(f"""
    <div class="hero">
        <h1>Dashboard Comercial — Danone NTR</h1>
        <p>{estudo.periodo_label} · Fonte: {path.name} · Leitura automática (Python, sem alterar o Excel)</p>
    </div>
    """, unsafe_allow_html=True)

    # ── VISÃO GERAL ──
    if pagina == "Visão Geral":
        total = estudo.total_ntr
        c1, c2, c3, c4 = st.columns(4)
        if total:
            with c1:
                st.markdown(_kpi_card("Faturamento Abr/25", fmt_moeda(total.fat_2025, True), "Base comparativa"), unsafe_allow_html=True)
            with c2:
                st.markdown(_kpi_card("Faturamento Abr/26", fmt_moeda(total.fat_2026, True), "Período atual"), unsafe_allow_html=True)
            with c3:
                pos = (total.crescimento or 0) >= 0
                st.markdown(_kpi_card("Crescimento YoY", fmt_pct(total.crescimento), "vs. ano anterior", pos), unsafe_allow_html=True)
            with c4:
                if total.unidades_2025 and total.unidades_2026:
                    cresc_u = (total.unidades_2026 - total.unidades_2025) / total.unidades_2025
                    st.markdown(_kpi_card("Unidades Abr/26", f"{total.unidades_2026:,.0f}".replace(",", "."), fmt_pct(cresc_u), cresc_u >= 0), unsafe_allow_html=True)

        st.markdown('<div class="section-title">Portfólio Danone</div>', unsafe_allow_html=True)
        if estudo.portfolio:
            df_p = pd.DataFrame([{
                "Unidade": p.nome.replace("DANONE ", ""),
                "fat_2025": p.fat_2025,
                "fat_2026": p.fat_2026,
                "crescimento": p.crescimento,
            } for p in estudo.portfolio])
            col_g, col_t = st.columns([1.65, 1])
            with col_g:
                _plot(_bar_comparativo(df_p, "Unidade", "Faturamento por unidade de negócio"))
            with col_t:
                st.markdown("<br>", unsafe_allow_html=True)
                for p in estudo.portfolio:
                    nome = p.nome.replace("DANONE ", "")
                    pos = (p.crescimento or 0) >= 0
                    st.markdown(
                        _portfolio_card(nome, fmt_moeda(p.fat_2026, True), fmt_pct(p.crescimento), pos),
                        unsafe_allow_html=True,
                    )

        st.markdown('<div class="section-title">Top 3 Laboratórios (mercado)</div>', unsafe_allow_html=True)
        if estudo.laboratorios_top3:
            df_t3 = pd.DataFrame([{
                "Laboratório": l.nome,
                "fat_2025": l.fat_2025,
                "fat_2026": l.fat_2026,
                "crescimento": l.crescimento,
                "market_share": l.market_share,
            } for l in estudo.laboratorios_top3])
            _plot(_bar_comparativo(df_t3, "Laboratório", "Comparativo Top 3 — faturamento"))
            for l in estudo.laboratorios_top3:
                ms = f" · MS {fmt_pct(l.market_share, False)}" if l.market_share else ""
                st.markdown(f'<div class="insight-box">{l.nome}: {fmt_moeda(l.fat_2026, True)} · {fmt_pct(l.crescimento)}{ms}</div>', unsafe_allow_html=True)

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
            st.markdown(
                f'<div class="insight-box">🏪 <b>{lider.nome.title()}</b> lidera o canal mapeado '
                f'({fmt_moeda(lider.fat_2026, True)} · {fmt_pct(lider.crescimento)}). '
                f'Foco comercial: redes com maior tração e share incremental.</div>',
                unsafe_allow_html=True,
            )

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
        st.markdown('<div class="section-title">Explorador de Dados (aba Dados)</div>', unsafe_allow_html=True)
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
