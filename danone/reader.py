"""
Leitura read-only de ESTUDO_DANONE_MAT_MAIO.xlsx.
Nunca altera o arquivo de origem.
"""

from __future__ import annotations

import shutil
import unicodedata
from pathlib import Path

import pandas as pd

from danone.config import (
    BASE_DIR,
    PERIODO_LABEL,
    PLANILHA_FONTE,
    SHEET_ABRAFAD,
    SHEET_CONCORRENTE,
    SHEET_DADOS,
    SHEET_RANKING,
    SHEET_REGIAO,
)

PASTA_CACHE_PLANILHA = BASE_DIR / ".cache" / "planilha"
from danone.models import CardPanoramaVisao, EstudoDanone, LinhaFaturamento

# Layout aba Ranking (ESTUDO_DANONE_MAT_MAIO)
COL_LAB_ESQ = 0
COL_LAB_DIR = 5
COL_RANK_ESQ = 4
FATURAMENTO_MINIMO_LAB = 1_000_000
FATURAMENTO_MINIMO_BANDEIRA = 100_000


def _num(valor) -> float | None:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace("R$", "").replace("\xa0", " ").strip()
    if not texto or texto in ("-", "nan", "None"):
        return None
    negativo = texto.startswith("(") and texto.endswith(")")
    texto = texto.strip("()").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        n = float(texto)
        return -n if negativo else n
    except ValueError:
        return None


def _pct(valor) -> float | None:
    if isinstance(valor, (int, float)) and not (isinstance(valor, float) and pd.isna(valor)):
        return float(valor)
    texto = str(valor).strip()
    if not texto or texto.lower() in ("nan", "none", "-"):
        return None
    if "%" in texto:
        n = _num(texto.replace("%", ""))
        return n / 100 if n is not None else None
    return _num(valor)


def _market_share(valor) -> float | None:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    if isinstance(valor, (int, float)):
        v = float(valor)
        if 0 <= v <= 1.0:
            return v
        if 0 < v <= 100:
            return v / 100
        return None
    texto = str(valor).strip()
    if not texto or texto.lower() in ("nan", "none", "-"):
        return None
    if "%" in texto:
        return _pct(valor)
    n = _num(texto)
    if n is None:
        return None
    if 0 <= n <= 1.0:
        return n
    if 0 < n <= 100:
        return n / 100
    return None


def _indice_coluna_market_share(row) -> int | None:
    for j in range(len(row)):
        cel = row.iloc[j]
        if cel is None or (isinstance(cel, float) and pd.isna(cel)):
            continue
        t = str(cel).strip().lower()
        if ("market" in t and "share" in t) or ("particip" in t and "%" in t):
            return j
    return None


def _market_share_na_linha(row, col_preferida: int = 4) -> float | None:
    if col_preferida < len(row):
        ms = _market_share(row.iloc[col_preferida])
        if ms is not None:
            return ms
    for j in range(4, min(len(row), 12)):
        if j == 3:
            continue
        ms = _market_share(row.iloc[j])
        if ms is not None:
            return ms
    return None


def _texto_chave(valor: str) -> str:
    norm = unicodedata.normalize("NFD", valor)
    sem_acento = "".join(c for c in norm if unicodedata.category(c) != "Mn")
    return sem_acento.lower().strip()


def _resolver_leitura_planilha(caminho: Path) -> Path:
    """Sincroniza cópia em .cache/planilha/ (funciona com Excel aberto no Windows)."""
    caminho = Path(caminho).resolve()
    if not caminho.exists():
        return caminho
    destino = PASTA_CACHE_PLANILHA / caminho.name
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(caminho, destino)
        return destino
    except (PermissionError, OSError):
        if destino.exists():
            return destino
        return caminho


def _linha(row, col_lab: int, ler_ms: bool = True) -> LinhaFaturamento | None:
    nome = row.iloc[col_lab] if col_lab < len(row) else None
    if nome is None or (isinstance(nome, float) and pd.isna(nome)):
        return None
    nome = str(nome).strip()
    ignorar = (
        "laboratorio", "laboratório", "nan", "(vários itens)",
        "setor_nec_aberto", "setor nec aberto", "ranking", "concorrentes",
        "bandeira", "regiao|uf", "região|uf", "total",
    )
    if not nome or nome.lower() in ignorar:
        return None
    if nome.lower().startswith("impactos"):
        return None

    fat25 = _num(row.iloc[col_lab + 1]) if col_lab + 1 < len(row) else None
    fat26 = _num(row.iloc[col_lab + 2]) if col_lab + 2 < len(row) else None
    cresc_col = _pct(row.iloc[col_lab + 3]) if col_lab + 3 < len(row) else None
    ms_col = None
    if ler_ms and col_lab + 4 < len(row):
        ms_col = _market_share(row.iloc[col_lab + 4])

    if fat26 is None and fat25 is None:
        return None

    if fat25 and fat26 and fat25 != 0:
        cresc = (fat26 - fat25) / fat25
    else:
        cresc = cresc_col

    delta = (fat26 - fat25) if fat25 is not None and fat26 is not None else None

    return LinhaFaturamento(
        nome=nome,
        fat_2025=fat25 or 0.0,
        fat_2026=fat26 or 0.0,
        crescimento=cresc,
        market_share=ms_col,
        delta_abs=delta,
    )


def _sheet_por_prefixo(caminho: Path, prefixo: str) -> str | None:
    xl = pd.ExcelFile(caminho)
    prefixo_lower = prefixo.lower()
    for nome in xl.sheet_names:
        if nome.lower().startswith(prefixo_lower):
            return nome
    return None


def _extrair_bloco_ranking(df: pd.DataFrame, col_lab: int) -> list[LinhaFaturamento]:
    saida: list[LinhaFaturamento] = []
    for _, row in df.iterrows():
        linha = _linha(row, col_lab)
        if linha is None:
            continue
        if linha.nome.lower().startswith("total geral"):
            continue
        if linha.fat_2026 < FATURAMENTO_MINIMO_LAB:
            continue
        saida.append(linha)
    return saida


def _extrair_top3_curado(df: pd.DataFrame) -> list[LinhaFaturamento]:
    """Top 3 do bloco direito (NESTLE, DANONE, ABBOTT) antes de TOTAL/Impactos."""
    saida: list[LinhaFaturamento] = []
    for _, row in df.iterrows():
        linha = _linha(row, COL_LAB_DIR)
        if linha is None:
            continue
        upper = linha.nome.upper()
        if upper in ("TOTAL", "TOTAL GERAL"):
            break
        if upper.startswith("IMPACTOS"):
            break
        saida.append(linha)
        if len(saida) >= 3:
            break
    return saida


def _extrair_top_por_rank(df: pd.DataFrame, max_rank: int = 3) -> list[LinhaFaturamento]:
    por_rank: dict[int, LinhaFaturamento] = {}
    for _, row in df.iterrows():
        rank = row.iloc[COL_RANK_ESQ] if COL_RANK_ESQ < len(row) else None
        if rank is None or (isinstance(rank, float) and pd.isna(rank)):
            continue
        try:
            r = int(float(rank))
        except (TypeError, ValueError):
            continue
        if r < 1 or r > max_rank:
            continue
        linha = _linha(row, COL_LAB_DIR) or _linha(row, COL_LAB_ESQ)
        if linha:
            por_rank[r] = linha
    if por_rank:
        return [por_rank[r] for r in sorted(por_rank) if r in por_rank]
    return _extrair_top3_curado(df)


def _extrair_impactos(df: pd.DataFrame) -> tuple[list[LinhaFaturamento], list[LinhaFaturamento]]:
    positivos: list[LinhaFaturamento] = []
    negativos: list[LinhaFaturamento] = []
    secao: str | None = None

    for _, row in df.iterrows():
        rotulo = row.iloc[COL_LAB_DIR] if COL_LAB_DIR < len(row) else None
        if rotulo is not None and not (isinstance(rotulo, float) and pd.isna(rotulo)):
            texto = str(rotulo).strip().lower()
            if texto == "impactos positivos":
                secao = "pos"
                continue
            if texto == "impactos negativos":
                secao = "neg"
                continue
            if texto in ("laboratorio", "laboratório"):
                secao = None
                continue

        if secao is None:
            continue

        linha = _linha(row, COL_LAB_DIR, ler_ms=False)
        if linha is None:
            continue
        # Coluna extra = incremento absoluto de receita
        if COL_LAB_DIR + 4 < len(row):
            inc = _num(row.iloc[COL_LAB_DIR + 4])
            if inc is not None:
                linha = LinhaFaturamento(
                    nome=linha.nome,
                    fat_2025=linha.fat_2025,
                    fat_2026=linha.fat_2026,
                    crescimento=linha.crescimento,
                    delta_abs=inc,
                )
        if secao == "pos":
            positivos.append(linha)
        else:
            negativos.append(linha)

    return positivos, negativos


def _extrair_portfolio_analise(caminho: Path) -> tuple[list[LinhaFaturamento], LinhaFaturamento | None]:
    sheet = _sheet_por_prefixo(caminho, "analise")
    if not sheet:
        return [], None

    df = pd.read_excel(caminho, sheet_name=sheet, header=None)
    portfolio: list[LinhaFaturamento] = []
    total: LinhaFaturamento | None = None
    na_secao = False
    col_ms = 4

    for _, row in df.iterrows():
        lab = row.iloc[0] if len(row) else None
        if lab is None or (isinstance(lab, float) and pd.isna(lab)):
            continue
        texto = str(lab).strip()
        if _texto_chave(texto) == "laboratorio":
            na_secao = True
            idx_ms = _indice_coluna_market_share(row)
            if idx_ms is not None:
                col_ms = idx_ms
            continue
        if not na_secao:
            continue
        if texto.lower().startswith("total geral"):
            linha = _linha(row, 0, ler_ms=False)
            if linha:
                total = linha
            break
        if "danone" in texto.lower():
            fat25 = _num(row.iloc[1]) if len(row) > 1 else None
            fat26 = _num(row.iloc[2]) if len(row) > 2 else None
            cresc = _pct(row.iloc[3]) if len(row) > 3 else None
            ms = _market_share_na_linha(row, col_ms)
            if fat25 is None and fat26 is None:
                continue
            if fat25 and fat26 and fat25 != 0 and cresc is None:
                cresc = (fat26 - fat25) / fat25
            portfolio.append(
                LinhaFaturamento(
                    nome=texto,
                    fat_2025=fat25 or 0.0,
                    fat_2026=fat26 or 0.0,
                    crescimento=cresc,
                    market_share=ms,
                )
            )

    return portfolio, total


def _extrair_total_ntr_analise(caminho: Path) -> LinhaFaturamento | None:
    sheet = _sheet_por_prefixo(caminho, "analise")
    if not sheet:
        return None
    df = pd.read_excel(caminho, sheet_name=sheet, header=None)
    for _, row in df.iterrows():
        lab = row.iloc[0]
        if lab is not None and str(lab).strip().upper() == "NAO_MEDICAMENTO_NTR":
            fat25 = _num(row.iloc[1])
            fat26 = _num(row.iloc[3])
            uni25 = _num(row.iloc[2])
            uni26 = _num(row.iloc[4])
            cresc = _pct(row.iloc[5]) if len(row) > 5 else None
            if fat25 and fat26 and fat25 != 0 and cresc is None:
                cresc = (fat26 - fat25) / fat25
            ms = _market_share(row.iloc[7]) if len(row) > 7 else None
            if fat25 or fat26:
                return LinhaFaturamento(
                    nome="Danone NTR",
                    fat_2025=fat25 or 0,
                    fat_2026=fat26 or 0,
                    crescimento=cresc,
                    market_share=ms,
                    unidades_2025=uni25,
                    unidades_2026=uni26,
                )
    return None


def _extrair_regioes(caminho: Path) -> tuple[list[LinhaFaturamento], LinhaFaturamento | None]:
    try:
        df = pd.read_excel(caminho, sheet_name=SHEET_REGIAO, header=None)
    except (ValueError, FileNotFoundError):
        return [], None

    regioes: list[LinhaFaturamento] = []
    total: LinhaFaturamento | None = None
    for _, row in df.iterrows():
        linha = _linha(row, 0, ler_ms=True)
        if linha is None:
            continue
        if linha.nome.lower().startswith("total geral"):
            total = linha
        elif linha.nome.lower() not in ("regiao|uf", "região|uf"):
            regioes.append(linha)
    return regioes, total


def _extrair_ranking_market_share(caminho: Path) -> list[LinhaFaturamento]:
    """Ranking com Market Share% da aba Ranking. (layout coluna 1 = laboratório)."""
    xl = pd.ExcelFile(caminho)
    sheet = next((s for s in xl.sheet_names if s.strip().lower() == "ranking."), None)
    if not sheet:
        return []

    df = pd.read_excel(caminho, sheet_name=sheet, header=None)
    saida: list[LinhaFaturamento] = []
    for _, row in df.iterrows():
        linha = _linha(row, 1, ler_ms=True)
        if linha is None:
            continue
        nome = linha.nome.lower()
        if nome in ("total", "laboratorio", "laboratório", "ranking"):
            continue
        if linha.fat_2026 < FATURAMENTO_MINIMO_LAB:
            continue
        saida.append(linha)
    saida.sort(key=lambda x: x.market_share or 0, reverse=True)
    return saida


def _extrair_total_abrafad(caminho: Path) -> LinhaFaturamento | None:
    """Total Geral da aba Ranking ABRAFAD."""
    try:
        df = pd.read_excel(caminho, sheet_name=SHEET_ABRAFAD, header=None)
    except (ValueError, FileNotFoundError):
        return None

    for _, row in df.iterrows():
        linha = _linha(row, 0, ler_ms=True)
        if linha and linha.nome.lower().startswith("total geral"):
            return LinhaFaturamento(
                nome="ABRAFAD",
                fat_2025=linha.fat_2025,
                fat_2026=linha.fat_2026,
                crescimento=linha.crescimento,
                market_share=linha.market_share,
            )
    return None


def _linha_concorrentes_agregado(concorrentes: list[LinhaFaturamento]) -> LinhaFaturamento | None:
    for c in concorrentes:
        if _texto_chave(c.nome) == "concorrentes":
            return c
    return concorrentes[0] if concorrentes else None


def _extrair_danone_canal_abrafad(
    dados: pd.DataFrame,
    bandeiras: list[LinhaFaturamento],
    total_abrafad: LinhaFaturamento | None,
) -> LinhaFaturamento | None:
    """Faturamento e crescimento da Danone nas bandeiras do canal ABRAFAD (aba Dados)."""
    if dados is None or dados.empty or "Laboratorio" not in dados.columns:
        return None

    nomes_bandeiras = {b.nome.upper() for b in bandeiras}
    mask_lab = dados["Laboratorio"].astype(str).str.upper().str.contains("DANONE", na=False)
    if nomes_bandeiras:
        mask_band = dados["Bandeira"].astype(str).str.upper().isin(nomes_bandeiras)
    else:
        mask_band = ~dados["Bandeira"].astype(str).str.upper().eq("CONCORRENTES")
    sub = dados[mask_lab & mask_band]
    fat25 = float(sub["fat_2025"].sum())
    fat26 = float(sub["fat_2026"].sum())
    if not fat25 and not fat26:
        return None

    cresc = (fat26 - fat25) / fat25 if fat25 else None
    ms = fat26 / total_abrafad.fat_2026 if total_abrafad and total_abrafad.fat_2026 else None
    return LinhaFaturamento(
        nome="DANONE ABRAFAD",
        fat_2025=fat25,
        fat_2026=fat26,
        crescimento=cresc,
        market_share=ms,
    )


def cards_panorama_visao_geral(
    estudo: EstudoDanone,
    caminho: Path | None = None,
) -> list[CardPanoramaVisao]:
    """
    Três ângulos da Danone para a Visão Geral:
    1) Faturamento Brasil (NTR)  2) Danone no canal ABRAFAD  3) Danone vs concorrentes.
    """
    caminho_leitura = _resolver_leitura_planilha(Path(caminho or PLANILHA_FONTE))
    danone = estudo.total_ntr
    total_abrafad = _extrair_total_abrafad(caminho_leitura)
    danone_abrafad = _extrair_danone_canal_abrafad(
        estudo.dados_detalhe,
        estudo.bandeiras,
        total_abrafad,
    )
    conc = _linha_concorrentes_agregado(estudo.concorrentes)

    saida: list[CardPanoramaVisao] = []

    if danone:
        ms_br = danone.market_share
        saida.append(
            CardPanoramaVisao(
                titulo="DANONE BRASIL",
                subtitulo="Faturamento NTR total no Brasil",
                ms_rotulo="Participação no mercado NTR",
                fat_2025=danone.fat_2025,
                fat_2026=danone.fat_2026,
                crescimento=danone.crescimento,
                market_share=ms_br,
                destaque=True,
            )
        )

    if danone_abrafad:
        ms_canal = danone_abrafad.market_share
        saida.append(
            CardPanoramaVisao(
                titulo="DANONE · ABRAFAD",
                subtitulo="Faturamento da Danone no canal farmácias ABRAFAD",
                ms_rotulo="Participação no canal ABRAFAD",
                fat_2025=danone_abrafad.fat_2025,
                fat_2026=danone_abrafad.fat_2026,
                crescimento=danone_abrafad.crescimento,
                market_share=ms_canal,
            )
        )

    if danone and conc:
        total_mercado = danone.fat_2026 + conc.fat_2026
        ms_danone = danone.fat_2026 / total_mercado if total_mercado else None
        saida.append(
            CardPanoramaVisao(
                titulo="DANONE · CONCORRENTES",
                subtitulo="Posição da Danone frente ao bloco concorrentes",
                ms_rotulo="Participação vs concorrentes",
                fat_2025=danone.fat_2025,
                fat_2026=danone.fat_2026,
                crescimento=danone.crescimento,
                market_share=ms_danone,
            )
        )

    return saida


def linhas_panorama_visao_geral(
    estudo: EstudoDanone,
    caminho: Path | None = None,
) -> list[LinhaFaturamento]:
    """Compatibilidade — converte cards em linhas para gráficos."""
    return [
        LinhaFaturamento(
            nome=c.titulo,
            fat_2025=c.fat_2025,
            fat_2026=c.fat_2026,
            crescimento=c.crescimento,
            market_share=c.market_share,
        )
        for c in cards_panorama_visao_geral(estudo, caminho)
    ]


def _extrair_bandeiras(caminho: Path) -> list[LinhaFaturamento]:
    try:
        df = pd.read_excel(caminho, sheet_name=SHEET_ABRAFAD, header=None)
    except (ValueError, FileNotFoundError):
        return []

    bandeiras: list[LinhaFaturamento] = []
    for _, row in df.iterrows():
        linha = _linha(row, 0, ler_ms=True)
        if linha is None:
            continue
        if linha.nome.lower().startswith("total geral"):
            continue
        if linha.fat_2026 < FATURAMENTO_MINIMO_BANDEIRA:
            continue
        bandeiras.append(linha)
    bandeiras.sort(key=lambda x: x.fat_2026, reverse=True)
    return bandeiras


def _extrair_concorrentes(caminho: Path) -> list[LinhaFaturamento]:
    try:
        df = pd.read_excel(caminho, sheet_name=SHEET_CONCORRENTE, header=None)
    except (ValueError, FileNotFoundError):
        return []

    saida: list[LinhaFaturamento] = []
    for _, row in df.iterrows():
        nome_cel = row.iloc[0] if len(row) else None
        if nome_cel is None or (isinstance(nome_cel, float) and pd.isna(nome_cel)):
            continue
        nome = str(nome_cel).strip()
        if nome.lower() in ("concorrentes", "laboratorio", "laboratório", "setor_nec_aberto"):
            fat25 = _num(row.iloc[1]) if len(row) > 1 else None
            fat26 = _num(row.iloc[2]) if len(row) > 2 else None
            cresc = _pct(row.iloc[3]) if len(row) > 3 else None
            ms = _market_share(row.iloc[4]) if len(row) > 4 else None
            if fat25 or fat26:
                saida.append(
                    LinhaFaturamento(
                        nome="CONCORRENTES",
                        fat_2025=fat25 or 0.0,
                        fat_2026=fat26 or 0.0,
                        crescimento=cresc,
                        market_share=ms,
                    )
                )
            continue
        linha = _linha(row, 0, ler_ms=True)
        if linha is None:
            continue
        if linha.nome.lower().startswith("total geral"):
            continue
        saida.append(linha)
    return saida


def _calcular_market_share(linhas: list[LinhaFaturamento]) -> list[LinhaFaturamento]:
    total = sum(l.fat_2026 for l in linhas if l.fat_2026)
    if not total:
        return linhas
    return [
        LinhaFaturamento(
            nome=l.nome,
            fat_2025=l.fat_2025,
            fat_2026=l.fat_2026,
            crescimento=l.crescimento,
            market_share=l.market_share if l.market_share is not None else l.fat_2026 / total,
            unidades_2025=l.unidades_2025,
            unidades_2026=l.unidades_2026,
            delta_abs=l.delta_abs,
        )
        for l in linhas
    ]


def _carregar_dados_detalhe(caminho: Path) -> pd.DataFrame:
    df = pd.read_excel(caminho, sheet_name=SHEET_DADOS)
    df.columns = [str(c).strip() for c in df.columns]
    rename = {
        "Mat MAT 04/25 Real CPP": "fat_2025",
        "Mat MAT 04/26 Real CPP": "fat_2026",
        "Mat MAT 04/25 Unidades": "unid_2025",
        "Mat MAT 04/26 Unidades": "unid_2026",
    }
    df = df.rename(columns=rename)
    df["delta_fat"] = df["fat_2026"] - df["fat_2025"]
    df["crescimento"] = df.apply(
        lambda r: r["delta_fat"] / r["fat_2025"] if r["fat_2025"] else None,
        axis=1,
    )
    return df


def _agregar_produtos(dados: pd.DataFrame) -> pd.DataFrame:
    agg = (
        dados.groupby("Produto", as_index=False)
        .agg(
            fat_2025=("fat_2025", "sum"),
            fat_2026=("fat_2026", "sum"),
            unid_2025=("unid_2025", "sum"),
            unid_2026=("unid_2026", "sum"),
        )
    )
    agg["delta_fat"] = agg["fat_2026"] - agg["fat_2025"]
    agg["crescimento"] = agg.apply(
        lambda r: r["delta_fat"] / r["fat_2025"] if r["fat_2025"] else None,
        axis=1,
    )
    return agg.sort_values("fat_2026", ascending=False)


def ler_market_share_portfolio(caminho: Path | None = None) -> dict[str, float]:
    """Mapa nome da unidade (upper) → market share (0–1). Leitura direta, sem cache Streamlit."""
    caminho = _resolver_leitura_planilha(Path(caminho or PLANILHA_FONTE))
    portfolio, _ = _extrair_portfolio_analise(caminho)
    return {
        p.nome.upper(): p.market_share
        for p in portfolio
        if p.market_share is not None
    }


def carregar_estudo(caminho: Path | None = None) -> EstudoDanone:
    caminho = Path(caminho or PLANILHA_FONTE)
    if not caminho.exists():
        raise FileNotFoundError(f"Planilha não encontrada: {caminho}")

    caminho = _resolver_leitura_planilha(caminho)

    df_ranking = pd.read_excel(caminho, sheet_name=SHEET_RANKING, header=None)

    top3 = _extrair_top_por_rank(df_ranking)
    ranking_ms = _extrair_ranking_market_share(caminho)
    ranking = ranking_ms if ranking_ms else _extrair_bloco_ranking(df_ranking, COL_LAB_ESQ)
    ranking = _calcular_market_share(ranking)
    top3 = _calcular_market_share(top3)
    portfolio, total_portfolio = _extrair_portfolio_analise(caminho)
    total_ntr = _extrair_total_ntr_analise(caminho) or total_portfolio
    positivos, negativos = _extrair_impactos(df_ranking)
    positivos.sort(key=lambda x: x.crescimento or 0, reverse=True)
    negativos.sort(key=lambda x: x.crescimento or 0)
    regioes, total_regioes = _extrair_regioes(caminho)
    regioes = _calcular_market_share(regioes)
    bandeiras = _calcular_market_share(_extrair_bandeiras(caminho))
    concorrentes = _extrair_concorrentes(caminho)

    dados_detalhe = _carregar_dados_detalhe(caminho)
    produtos = _agregar_produtos(dados_detalhe)

    return EstudoDanone(
        periodo_label=PERIODO_LABEL,
        total_ntr=total_ntr,
        portfolio=portfolio,
        laboratorios_top3=top3,
        laboratorios_ranking=ranking,
        impactos_positivos=positivos,
        impactos_negativos=negativos,
        regioes=regioes,
        total_regioes=total_regioes,
        bandeiras=bandeiras,
        concorrentes=concorrentes,
        produtos=produtos,
        dados_detalhe=dados_detalhe,
    )


# Alias legado
carregar_dados = carregar_estudo


def copiar_planilha_entrega(
    destino: Path,
    origem: Path | None = None,
) -> Path:
    """Copia a planilha original para pasta de entrega (sem modificá-la)."""
    import shutil

    origem = Path(origem or PLANILHA_FONTE)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)
    return destino.resolve()
