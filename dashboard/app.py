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
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from danone import PLANILHA_FONTE, carregar_estudo, fmt_moeda, fmt_pct, fmt_produto_curto
from dashboard.theme import CORES, CSS, PALETA_REGIAO

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


def _bar_comparativo(
    df: pd.DataFrame,
    nome_col: str,
    titulo: str,
    horizontal: bool = False,
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Abr/25",
        x=df[nome_col] if not horizontal else df["fat_2025"],
        y=df["fat_2025"] if not horizontal else df[nome_col],
        orientation="h" if horizontal else "v",
        marker_color=CORES["gray"],
    ))
    fig.add_trace(go.Bar(
        name="Abr/26",
        x=df[nome_col] if not horizontal else df["fat_2026"],
        y=df["fat_2026"] if not horizontal else df[nome_col],
        orientation="h" if horizontal else "v",
        marker_color=CORES["navy"],
    ))
    fig.update_layout(
        title=titulo,
        barmode="group",
        template="plotly_white",
        height=380 if not horizontal else max(320, len(df) * 38),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        font=dict(family="Inter, Segoe UI"),
    )
    if horizontal:
        fig.update_xaxes(tickformat=".2s", ticksuffix="")
    else:
        fig.update_yaxes(tickformat=".2s")
    return fig


def _grafico_crescimento(df: pd.DataFrame, nome_col: str, titulo: str) -> go.Figure:
    df = df.copy()
    df["cresc_pct"] = df["crescimento"] * 100
    df["cor"] = df["cresc_pct"].apply(lambda v: CORES["green"] if v >= 0 else CORES["orange"])
    fig = px.bar(
        df,
        x="cresc_pct" if not nome_col == "nome" else nome_col,
        y=nome_col if nome_col != "nome" else "cresc_pct",
        orientation="h" if nome_col != "nome" else "v",
        title=titulo,
        color="cor",
        color_discrete_map="identity",
    )
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        height=max(300, len(df) * 36),
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(family="Inter, Segoe UI"),
    )
    fig.update_xaxes(title="Crescimento YoY (%)")
    return fig


def main() -> None:
    if not _verificar_acesso():
        return

    st.sidebar.markdown("### 🎯 Navegação")
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

    planilha = st.sidebar.text_input("Planilha (read-only)", str(PLANILHA_FONTE))
    path = Path(planilha)
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
            col_g, col_t = st.columns([3, 2])
            with col_g:
                st.plotly_chart(_bar_comparativo(df_p, "Unidade", "Faturamento por unidade de negócio"), use_container_width=True)
            with col_t:
                for p in estudo.portfolio:
                    emoji = "🟢" if (p.crescimento or 0) >= 0 else "🟠"
                    st.markdown(f"**{emoji} {p.nome.replace('DANONE ', '')}**  \n"
                                f"{fmt_moeda(p.fat_2026, True)} · {fmt_pct(p.crescimento)}")

        st.markdown('<div class="section-title">Top 3 Laboratórios (mercado)</div>', unsafe_allow_html=True)
        if estudo.laboratorios_top3:
            df_t3 = pd.DataFrame([{
                "Laboratório": l.nome,
                "fat_2025": l.fat_2025,
                "fat_2026": l.fat_2026,
                "crescimento": l.crescimento,
                "market_share": l.market_share,
            } for l in estudo.laboratorios_top3])
            st.plotly_chart(_bar_comparativo(df_t3, "Laboratório", "Comparativo Top 3 — faturamento"), use_container_width=True)
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
                st.plotly_chart(_bar_comparativo(df_r, "Região", "Faturamento por região"), use_container_width=True)
            with c2:
                df_r2 = df_r.sort_values("crescimento", ascending=True)
                fig = px.bar(
                    df_r2, x="crescimento", y="Região", orientation="h",
                    title="Crescimento YoY por região",
                    color="crescimento",
                    color_continuous_scale=["#BF5700", "#F8F9FA", "#1B5E20"],
                    color_continuous_midpoint=0,
                )
                fig.update_layout(template="plotly_white", height=380, showlegend=False)
                fig.update_xaxes(tickformat=".1%", title="YoY")
                st.plotly_chart(fig, use_container_width=True)

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

        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(
                top_fat.sort_values("fat_2026"),
                x="fat_2026", y="nome_curto", orientation="h",
                title=f"Top {top_n} produtos — faturamento Abr/26",
                color_discrete_sequence=[CORES["navy"]],
            )
            fig.update_layout(template="plotly_white", height=420, xaxis_tickformat=".2s")
            st.plotly_chart(fig, use_container_width=True)
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
            st.plotly_chart(
                _bar_comparativo(df_b.sort_values("fat_2026"), "Bandeira", "Top bandeiras — faturamento Danone", horizontal=True),
                use_container_width=True,
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
            fig = px.bar(
                df_c.sort_values("fat_2026"),
                x="fat_2026", y="Laboratório", orientation="h",
                title="Top 15 laboratórios — faturamento Abr/26",
                color="crescimento",
                color_continuous_scale=["#BF5700", "#F8F9FA", "#1B5E20"],
                color_continuous_midpoint=0,
            )
            fig.update_layout(template="plotly_white", height=520, xaxis_tickformat=".2s")
            st.plotly_chart(fig, use_container_width=True)

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
