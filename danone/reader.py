"""
Leitura read-only de planilhas de estudo (.xlsx em dados/).
Nunca altera o arquivo de origem.
Suporta formato novo (DANONE_NOVO_ESTUDO01) e legado (ESTUDO_DANONE_MAT_MAIO).
"""

from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path

import pandas as pd

from danone.config import (
    ABA_ANALISE_CANDIDATOS,
    ABA_CONCORRENTE_CANDIDATOS,
    ABA_DADOS_CANDIDATOS,
    ABA_RANKING_CANDIDATOS,
    ABA_REGIAO_CANDIDATOS,
    ABA_ABRAFAD_PREFIXOS,
    BASE_DIR,
    PERIODO_LABEL_PADRAO,
    PLANILHA_FONTE,
    resolver_planilha,
)
from danone.models import CardPanoramaVisao, EstudoDanone, LinhaFaturamento, MetadadosEstudo

PASTA_CACHE_PLANILHA = BASE_DIR / ".cache" / "planilha"

# Layout legado aba Ranking
COL_LAB_ESQ = 0
COL_LAB_DIR = 5
COL_RANK_ESQ = 4

FATURAMENTO_MINIMO_LAB = 1_000_000
FATURAMENTO_MINIMO_BANDEIRA = 100_000

MARCADORES_PRODUTO = (
    " PO ",
    " G X ",
    " LAT",
    " KIT ",
    " JR ",
    " POLAP",
    " SUSTAIN",
    " TRIDENT ",
    " LACTA ",
    " APTAMIL",
    " APTANUTRI",
    " MILNUTRI",
    " PREGOMIN",
)
MARCADORES_LAB_DANONE = ("APTAMIL", "APTANUTRI", "MILNUTRI", "PREGOMIN", "NUTRICIA")


def eh_laboratorio(nome: str) -> bool:
    """True quando o rótulo é laboratório (não SKU/produto)."""
    if not nome or not isinstance(nome, str):
        return False
    n = nome.strip()
    if not n or n.upper() in ("LABORATORIO", "LABORATÓRIO", "NAN"):
        return False
    if n.lower().startswith("total") or n.lower() in ("total", "ranking"):
        return False
    upper = n.upper()
    if any(m in upper for m in MARCADORES_PRODUTO):
        return False
    if re.search(r"\d+\.?\d*\s*G\b", upper):
        return False
    if re.search(r"\sX\s*\d", upper):
        return False
    if re.search(r"\d+\.?\d*\s*KG", upper):
        return False
    if len(n.split()) > 6:
        return False
    return True


def inferir_laboratorio(nome: str) -> str:
    """Infere laboratório a partir do nome de produto ou rótulo agregado."""
    upper = nome.upper()
    if "DANONE" in upper or any(m in upper for m in MARCADORES_LAB_DANONE):
        return "DANONE"
    if "CONCORRENTE" in upper:
        return "Concorrente"
    return nome.strip()


def _texto_chave(valor: str) -> str:
    norm = unicodedata.normalize("NFD", str(valor))
    sem_acento = "".join(c for c in norm if unicodedata.category(c) != "Mn")
    return sem_acento.lower().strip()


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
        v = float(valor)
        if abs(v) > 1.5:
            return v / 100
        return v
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
        return caminho


def _mapa_abas(caminho: Path) -> dict[str, str]:
    """Mapa chave normalizada → nome real da aba."""
    xl = pd.ExcelFile(caminho)
    return {_texto_chave(n): n for n in xl.sheet_names}


def _resolver_aba(
    caminho: Path,
    *candidatos: str,
    prefixos: tuple[str, ...] = (),
) -> str | None:
    mapa = _mapa_abas(caminho)
    for nome in candidatos:
        chave = _texto_chave(nome)
        if chave in mapa:
            return mapa[chave]
    for prefixo in prefixos:
        pref = _texto_chave(prefixo)
        for chave, real in mapa.items():
            if chave.startswith(pref):
                return real
    return None


def _inferir_cliente(caminho: Path) -> str:
    nome = caminho.stem.upper()
    for token in re.split(r"[_\-\s]+", nome):
        if token in ("ESTUDO", "NOVO", "MAT", "MAIO", "JUNHO", "01", "1", "V1"):
            continue
        if len(token) >= 3:
            return token.title()
    return "Estudo"


def _mes_abrev(numero: str) -> str:
    meses = {
        "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
        "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
        "09": "Set", "10": "Out", "11": "Nov", "12": "Dez",
    }
    return meses.get(numero.zfill(2), numero)


def _inferir_periodo_label(caminho: Path) -> str:
    aba = _resolver_aba(caminho, *ABA_DADOS_CANDIDATOS)
    if not aba:
        aba = _resolver_aba(caminho, *ABA_ANALISE_CANDIDATOS)
    if not aba:
        return PERIODO_LABEL_PADRAO

    try:
        df = pd.read_excel(caminho, sheet_name=aba, header=None, nrows=3)
    except (ValueError, FileNotFoundError):
        return PERIODO_LABEL_PADRAO

    textos = " ".join(str(v) for v in df.values.flatten() if pd.notna(v))
    vistos: list[tuple[str, str]] = []
    for m, a in re.findall(r"(\d{2})/(\d{2})", textos):
        par = (m, a)
        if par not in vistos:
            vistos.append(par)
    if len(vistos) >= 2:
        m1, a1 = vistos[0]
        m2, a2 = vistos[1]
        return f"MAT {_mes_abrev(m1)}/{a1} vs MAT {_mes_abrev(m2)}/{a2}"
    if len(vistos) == 1:
        m, a = vistos[0]
        return f"MAT {_mes_abrev(m)}/{a}"
    return PERIODO_LABEL_PADRAO


def _detectar_metadados(caminho: Path) -> MetadadosEstudo:
    mapa = _mapa_abas(caminho)
    abas = tuple(pd.ExcelFile(caminho).sheet_names)
    tem_abrafad = any(k.startswith("ranking abrafad") for k in mapa)
    tem_concorrente = any(_texto_chave(c) in mapa for c in ABA_CONCORRENTE_CANDIDATOS)

    aba_dados = _resolver_aba(caminho, *ABA_DADOS_CANDIDATOS)
    tem_uf = False
    tem_bandeiras = tem_abrafad
    if aba_dados:
        try:
            cols = [str(c).strip().lower() for c in pd.read_excel(caminho, sheet_name=aba_dados, nrows=0).columns]
            tem_uf = any("uf" == c or c.endswith("|uf") for c in cols)
            tem_bandeiras = tem_bandeiras or any("bandeira" in c for c in cols)
        except (ValueError, FileNotFoundError):
            pass

    formato = "legado" if tem_abrafad or "ranking regiao|uf" in mapa else "novo"
    if _texto_chave(ABA_DADOS_CANDIDATOS[0]) in mapa:
        formato = "novo"

    return MetadadosEstudo(
        arquivo=caminho.name,
        cliente=_inferir_cliente(caminho),
        abas=abas,
        formato=formato,
        tem_bandeiras=tem_bandeiras,
        tem_uf=tem_uf,
        tem_abrafad=tem_abrafad,
        tem_concorrente_aba=tem_concorrente,
    )


def _linha(row, col_lab: int, ler_ms: bool = True) -> LinhaFaturamento | None:
    nome = row.iloc[col_lab] if col_lab < len(row) else None
    if nome is None or (isinstance(nome, float) and pd.isna(nome)):
        return None
    nome = str(nome).strip()
    ignorar = (
        "laboratorio", "laboratório", "nan", "(vários itens)", "(varios itens)",
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


def _detectar_col_lab_ranking(df: pd.DataFrame) -> int:
    """Detecta coluna de nomes no layout novo (rank em col 0) ou legado."""
    for _, row in df.head(12).iterrows():
        c0 = row.iloc[0] if len(row) else None
        c1 = row.iloc[1] if len(row) > 1 else None
        try:
            if c0 is not None and not pd.isna(c0) and int(float(c0)) >= 1:
                if c1 is not None and not pd.isna(c1):
                    t1 = str(c1).strip().lower()
                    if t1 not in ("laboratorio", "laboratório", "ranking", "nan"):
                        return 1
        except (TypeError, ValueError):
            pass
    return COL_LAB_ESQ


def _extrair_bloco_ranking(
    df: pd.DataFrame,
    col_lab: int,
    *,
    apenas_labs: bool = True,
) -> list[LinhaFaturamento]:
    saida: list[LinhaFaturamento] = []
    for _, row in df.iterrows():
        linha = _linha(row, col_lab)
        if linha is None:
            continue
        nome = linha.nome.lower()
        if nome.startswith("total") or nome.startswith("impactos"):
            break
        if apenas_labs and not eh_laboratorio(linha.nome):
            continue
        if linha.fat_2026 < FATURAMENTO_MINIMO_LAB and linha.fat_2025 < FATURAMENTO_MINIMO_LAB:
            continue
        saida.append(linha)
    return saida


def _extrair_ranking_todas_linhas(df: pd.DataFrame, col_lab: int) -> list[LinhaFaturamento]:
    """Ranking incluindo CONCORRENTE e unidades — sem filtro de laboratório."""
    saida: list[LinhaFaturamento] = []
    for _, row in df.iterrows():
        linha = _linha(row, col_lab)
        if linha is None:
            continue
        nome = linha.nome.lower()
        if nome.startswith("total") or nome.startswith("impactos"):
            break
        if linha.fat_2026 < FATURAMENTO_MINIMO_LAB and linha.fat_2025 < FATURAMENTO_MINIMO_LAB:
            continue
        saida.append(linha)
    return saida


def _extrair_top3_curado(df: pd.DataFrame, col_lab: int = COL_LAB_DIR) -> list[LinhaFaturamento]:
    """Top 3 do bloco direito (legado) ou primeiras linhas ranqueadas (novo)."""
    saida: list[LinhaFaturamento] = []
    for _, row in df.iterrows():
        linha = _linha(row, col_lab)
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
        linha = _linha(row, COL_LAB_DIR) or _linha(row, COL_LAB_ESQ) or _linha(row, 1)
        if linha:
            por_rank[r] = linha
    if por_rank:
        return [por_rank[r] for r in sorted(por_rank) if r in por_rank]

    col_lab = _detectar_col_lab_ranking(df)
    linhas = _extrair_ranking_todas_linhas(df, col_lab)
    linhas.sort(key=lambda x: x.fat_2026, reverse=True)
    return linhas[:max_rank]


def _coluna_impactos(df: pd.DataFrame) -> int:
    for col in (COL_LAB_DIR, 1, COL_LAB_ESQ, 0):
        for _, row in df.iterrows():
            cel = row.iloc[col] if col < len(row) else None
            if cel is None or (isinstance(cel, float) and pd.isna(cel)):
                continue
            if str(cel).strip().lower() == "impactos positivos":
                return col
    return COL_LAB_DIR


def _extrair_impactos(df: pd.DataFrame) -> tuple[list[LinhaFaturamento], list[LinhaFaturamento]]:
    positivos: list[LinhaFaturamento] = []
    negativos: list[LinhaFaturamento] = []
    secao: str | None = None
    col_imp = _coluna_impactos(df)

    for _, row in df.iterrows():
        rotulo = row.iloc[col_imp] if col_imp < len(row) else None
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

        linha = _linha(row, col_imp, ler_ms=False)
        if linha is None:
            continue
        if col_imp + 4 < len(row):
            inc = _num(row.iloc[col_imp + 4])
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
    sheet = _resolver_aba(caminho, *ABA_ANALISE_CANDIDATOS)
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


def _extrair_mercado_ntr_analise(caminho: Path) -> LinhaFaturamento | None:
    """Setor NAO_MEDICAMENTO_NTR — mercado total NTR (contexto de share)."""
    sheet = _resolver_aba(caminho, *ABA_ANALISE_CANDIDATOS)
    if not sheet:
        return None
    df = pd.read_excel(caminho, sheet_name=sheet, header=None)
    for _, row in df.iterrows():
        lab = row.iloc[0]
        if lab is not None and str(lab).strip().upper() == "NAO_MEDICAMENTO_NTR":
            fat25 = _num(row.iloc[1])
            fat26 = _num(row.iloc[3]) if len(row) > 3 else _num(row.iloc[2])
            uni25 = _num(row.iloc[2]) if len(row) > 2 else None
            uni26 = _num(row.iloc[4]) if len(row) > 4 else None
            cresc = _pct(row.iloc[5]) if len(row) > 5 else None
            if fat25 and fat26 and fat25 != 0 and cresc is None:
                cresc = (fat26 - fat25) / fat25
            ms = _market_share(row.iloc[7]) if len(row) > 7 else None
            if fat25 or fat26:
                return LinhaFaturamento(
                    nome="Mercado NTR",
                    fat_2025=fat25 or 0,
                    fat_2026=fat26 or 0,
                    crescimento=cresc,
                    market_share=ms,
                    unidades_2025=uni25,
                    unidades_2026=uni26,
                )
    return None


def _extrair_regioes(caminho: Path) -> tuple[list[LinhaFaturamento], LinhaFaturamento | None]:
    sheet = _resolver_aba(caminho, *ABA_REGIAO_CANDIDATOS)
    if not sheet:
        return [], None
    try:
        df = pd.read_excel(caminho, sheet_name=sheet, header=None)
    except (ValueError, FileNotFoundError):
        return [], None

    regioes: list[LinhaFaturamento] = []
    total: LinhaFaturamento | None = None
    for _, row in df.iterrows():
        linha = _linha(row, 0, ler_ms=True)
        if linha is None:
            continue
        chave = _texto_chave(linha.nome)
        if chave.startswith("total geral"):
            total = linha
        elif chave not in ("regiao|uf", "regiao", "laboratorio"):
            regioes.append(linha)
    return regioes, total


def _extrair_ranking_market_share(caminho: Path) -> list[LinhaFaturamento]:
    """Ranking com MS% — aba 'Ranking.' (legado)."""
    mapa = _mapa_abas(caminho)
    sheet = mapa.get("ranking.")
    if not sheet:
        return []

    df = pd.read_excel(caminho, sheet_name=sheet, header=None)
    saida: list[LinhaFaturamento] = []
    for _, row in df.iterrows():
        linha = _linha(row, 1, ler_ms=True)
        if linha is None:
            continue
        nome = linha.nome.lower()
        if nome in ("laboratorio", "laboratório", "ranking"):
            continue
        if nome.startswith("total") or nome.startswith("impactos"):
            break
        if not eh_laboratorio(linha.nome):
            continue
        if linha.fat_2026 < FATURAMENTO_MINIMO_LAB:
            continue
        saida.append(linha)
    saida.sort(key=lambda x: x.market_share or 0, reverse=True)
    return saida


def _extrair_produtos_ranking(
    positivos: list[LinhaFaturamento],
    negativos: list[LinhaFaturamento],
    total_fat_2026: float | None,
) -> list[LinhaFaturamento]:
    if not total_fat_2026:
        return []
    vistos: set[str] = set()
    saida: list[LinhaFaturamento] = []
    for linha in positivos + negativos:
        if eh_laboratorio(linha.nome):
            continue
        chave = linha.nome.strip().upper()
        if chave in vistos or linha.fat_2026 < FATURAMENTO_MINIMO_LAB:
            continue
        vistos.add(chave)
        saida.append(
            LinhaFaturamento(
                nome=linha.nome.strip(),
                fat_2025=linha.fat_2025,
                fat_2026=linha.fat_2026,
                crescimento=linha.crescimento,
                market_share=linha.fat_2026 / total_fat_2026,
                delta_abs=linha.delta_abs,
            )
        )
    saida.sort(key=lambda x: x.fat_2026, reverse=True)
    return saida


def _resolver_sheet_abrafad(caminho: Path) -> str | None:
    mapa = _mapa_abas(caminho)
    if "ranking abrafad." in mapa:
        return mapa["ranking abrafad."]
    if "ranking abrafad" in mapa:
        return mapa["ranking abrafad"]
    return _resolver_aba(caminho, prefixos=ABA_ABRAFAD_PREFIXOS)


def _extrair_linhas_abrafad(
    caminho: Path,
    *,
    minimo_fat: float = 0,
) -> list[LinhaFaturamento]:
    sheet = _resolver_sheet_abrafad(caminho)
    if not sheet:
        return []
    try:
        df = pd.read_excel(caminho, sheet_name=sheet, header=None)
    except (ValueError, FileNotFoundError):
        return []

    saida: list[LinhaFaturamento] = []
    for _, row in df.iterrows():
        linha = _linha(row, 0, ler_ms=True)
        if linha is None:
            continue
        if linha.nome.lower().startswith("total"):
            continue
        if linha.fat_2026 < minimo_fat:
            continue
        saida.append(linha)
    return saida


def _extrair_total_abrafad(caminho: Path) -> LinhaFaturamento | None:
    linhas = _extrair_linhas_abrafad(caminho)
    if not linhas:
        return None

    fat25 = sum(l.fat_2025 for l in linhas)
    fat26 = sum(l.fat_2026 for l in linhas)
    if not fat25 and not fat26:
        return None

    cresc = (fat26 - fat25) / fat25 if fat25 else None
    return LinhaFaturamento(
        nome="ABRAFAD",
        fat_2025=fat25,
        fat_2026=fat26,
        crescimento=cresc,
        market_share=1.0,
    )


def _linha_concorrentes_agregado(concorrentes: list[LinhaFaturamento]) -> LinhaFaturamento | None:
    fat25 = sum(c.fat_2025 for c in concorrentes)
    fat26 = sum(c.fat_2026 for c in concorrentes)
    if not fat25 and not fat26:
        for c in concorrentes:
            if _texto_chave(c.nome) == "concorrentes":
                return c
        return concorrentes[0] if concorrentes else None
    cresc = (fat26 - fat25) / fat25 if fat25 else None
    return LinhaFaturamento(
        nome="CONCORRENTES",
        fat_2025=fat25,
        fat_2026=fat26,
        crescimento=cresc,
    )


def _extrair_danone_canal_abrafad(
    dados: pd.DataFrame,
    bandeiras: list[LinhaFaturamento],
    total_abrafad: LinhaFaturamento | None,
) -> LinhaFaturamento | None:
    if dados is None or dados.empty or "Laboratorio" not in dados.columns:
        return None

    nomes_bandeiras = {b.nome.upper() for b in bandeiras}
    mask_lab = dados["Laboratorio"].astype(str).str.upper().str.contains("DANONE", na=False)
    if nomes_bandeiras and "Bandeira" in dados.columns:
        mask_band = dados["Bandeira"].astype(str).str.upper().isin(nomes_bandeiras)
    elif "Bandeira" in dados.columns:
        mask_band = ~dados["Bandeira"].astype(str).str.upper().eq("CONCORRENTES")
    else:
        return None
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


def _extrair_concorrentes_ranking(df: pd.DataFrame, col_lab: int) -> list[LinhaFaturamento]:
    saida: list[LinhaFaturamento] = []
    for _, row in df.iterrows():
        linha = _linha(row, col_lab, ler_ms=True)
        if linha is None:
            continue
        if _texto_chave(linha.nome) == "concorrente":
            saida.append(linha)
        if linha.nome.lower().startswith("total"):
            break
    return saida


def _extrair_concorrentes(caminho: Path, df_ranking: pd.DataFrame | None, col_lab: int) -> list[LinhaFaturamento]:
    sheet = _resolver_aba(caminho, *ABA_CONCORRENTE_CANDIDATOS)
    if sheet:
        try:
            df = pd.read_excel(caminho, sheet_name=sheet, header=None)
        except (ValueError, FileNotFoundError):
            df = None
        if df is not None:
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
            if saida:
                return saida

    if df_ranking is not None:
        return _extrair_concorrentes_ranking(df_ranking, col_lab)
    return []


def _agregar_laboratorios_dados(dados: pd.DataFrame) -> list[LinhaFaturamento]:
    if dados.empty or "Laboratorio" not in dados.columns:
        return []
    agg = (
        dados.groupby("Laboratorio", as_index=False)
        .agg(fat_2025=("fat_2025", "sum"), fat_2026=("fat_2026", "sum"))
    )
    saida: list[LinhaFaturamento] = []
    for _, row in agg.iterrows():
        fat25, fat26 = float(row["fat_2025"]), float(row["fat_2026"])
        cresc = (fat26 - fat25) / fat25 if fat25 else None
        saida.append(
            LinhaFaturamento(
                nome=str(row["Laboratorio"]).strip(),
                fat_2025=fat25,
                fat_2026=fat26,
                crescimento=cresc,
            )
        )
    saida.sort(key=lambda x: x.fat_2026, reverse=True)
    return saida


def cards_panorama_visao_geral(
    estudo: EstudoDanone,
    caminho: Path | None = None,
) -> list[CardPanoramaVisao]:
    """Cards da Visão Geral — adapta ao formato disponível na planilha."""
    caminho_leitura = _resolver_leitura_planilha(Path(caminho or PLANILHA_FONTE))
    danone = estudo.total_ntr
    mercado = estudo.total_mercado_ntr
    saida: list[CardPanoramaVisao] = []

    if danone:
        ms_br = danone.market_share
        if ms_br is None and mercado and mercado.fat_2026:
            ms_br = danone.fat_2026 / mercado.fat_2026
        saida.append(
            CardPanoramaVisao(
                titulo=f"{estudo.metadados.cliente.upper()} — TOTAL",
                subtitulo="Faturamento total do estudo",
                ms_rotulo="Participação no mercado NTR" if mercado else "Participação de mercado",
                fat_2025=danone.fat_2025,
                fat_2026=danone.fat_2026,
                crescimento=danone.crescimento,
                market_share=ms_br,
                destaque=True,
            )
        )

    if estudo.metadados.tem_abrafad:
        total_abrafad = _extrair_total_abrafad(caminho_leitura)
        danone_abrafad = _extrair_danone_canal_abrafad(
            estudo.dados_detalhe,
            estudo.bandeiras,
            total_abrafad,
        )
        if danone_abrafad:
            saida.append(
                CardPanoramaVisao(
                    titulo=f"{estudo.metadados.cliente.upper()} · ABRAFAD",
                    subtitulo="Faturamento no canal farmácias ABRAFAD",
                    ms_rotulo="Participação no canal ABRAFAD",
                    fat_2025=danone_abrafad.fat_2025,
                    fat_2026=danone_abrafad.fat_2026,
                    crescimento=danone_abrafad.crescimento,
                    market_share=danone_abrafad.market_share,
                )
            )
    elif estudo.portfolio:
        maior = max(estudo.portfolio, key=lambda p: p.fat_2026)
        saida.append(
            CardPanoramaVisao(
                titulo=maior.nome.upper(),
                subtitulo="Maior unidade de negócio no portfólio",
                ms_rotulo="Participação no portfólio",
                fat_2025=maior.fat_2025,
                fat_2026=maior.fat_2026,
                crescimento=maior.crescimento,
                market_share=maior.market_share,
            )
        )

    conc = _linha_concorrentes_agregado(estudo.concorrentes)
    if danone and conc:
        total_mercado = danone.fat_2026 + conc.fat_2026
        ms_danone = danone.fat_2026 / total_mercado if total_mercado else None
        saida.append(
            CardPanoramaVisao(
                titulo=f"{estudo.metadados.cliente.upper()} · CONCORRENTES",
                subtitulo="Posição frente ao bloco concorrentes",
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
    bandeiras = _extrair_linhas_abrafad(caminho, minimo_fat=FATURAMENTO_MINIMO_BANDEIRA)
    bandeiras.sort(key=lambda x: x.fat_2026, reverse=True)
    return bandeiras


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


def _normalizar_colunas_dados(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    rename: dict[str, str] = {}
    for col in df.columns:
        chave = col.lower()
        if "04/25" in chave and "real" in chave and "cpp" in chave:
            rename[col] = "fat_2025"
        elif "04/26" in chave and "real" in chave and "cpp" in chave:
            rename[col] = "fat_2026"
        elif "04/25" in chave and "unid" in chave:
            rename[col] = "unid_2025"
        elif "04/26" in chave and "unid" in chave:
            rename[col] = "unid_2026"
    df = df.rename(columns=rename)
    return df


def _carregar_dados_detalhe(caminho: Path) -> pd.DataFrame:
    sheet = _resolver_aba(caminho, *ABA_DADOS_CANDIDATOS)
    if not sheet:
        return pd.DataFrame()
    df = pd.read_excel(caminho, sheet_name=sheet)
    df = _normalizar_colunas_dados(df)
    for col in ("fat_2025", "fat_2026"):
        if col not in df.columns:
            df[col] = 0.0
    df["delta_fat"] = df["fat_2026"] - df["fat_2025"]
    df["crescimento"] = df.apply(
        lambda r: r["delta_fat"] / r["fat_2025"] if r["fat_2025"] else None,
        axis=1,
    )
    return df


def _agregar_produtos(dados: pd.DataFrame) -> pd.DataFrame:
    if dados.empty or "Produto" not in dados.columns:
        return pd.DataFrame(columns=["Produto", "fat_2025", "fat_2026", "crescimento"])
    agg = (
        dados.groupby("Produto", as_index=False)
        .agg(
            fat_2025=("fat_2025", "sum"),
            fat_2026=("fat_2026", "sum"),
            unid_2025=("unid_2025", "sum") if "unid_2025" in dados.columns else ("fat_2025", "first"),
            unid_2026=("unid_2026", "sum") if "unid_2026" in dados.columns else ("fat_2026", "first"),
        )
    )
    if "unid_2025" not in dados.columns:
        agg = agg.drop(columns=[c for c in ("unid_2025", "unid_2026") if c in agg.columns], errors="ignore")
    agg["delta_fat"] = agg["fat_2026"] - agg["fat_2025"]
    agg["crescimento"] = agg.apply(
        lambda r: r["delta_fat"] / r["fat_2025"] if r["fat_2025"] else None,
        axis=1,
    )
    return agg.sort_values("fat_2026", ascending=False)


def ler_market_share_portfolio(caminho: Path | None = None) -> dict[str, float]:
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
    metadados = _detectar_metadados(caminho)
    periodo_label = _inferir_periodo_label(caminho)

    sheet_ranking = _resolver_aba(caminho, *ABA_RANKING_CANDIDATOS)
    df_ranking = (
        pd.read_excel(caminho, sheet_name=sheet_ranking, header=None)
        if sheet_ranking
        else pd.DataFrame()
    )

    col_lab = _detectar_col_lab_ranking(df_ranking) if not df_ranking.empty else COL_LAB_ESQ

    top3 = _extrair_top_por_rank(df_ranking) if not df_ranking.empty else []
    ranking_ms = _extrair_ranking_market_share(caminho)

    ranking = ranking_ms if ranking_ms else _extrair_bloco_ranking(df_ranking, col_lab, apenas_labs=True)
    if len(ranking) < 3:
        ranking_ranking = _extrair_ranking_todas_linhas(df_ranking, col_lab) if not df_ranking.empty else []
        if len(ranking_ranking) > len(ranking):
            ranking = ranking_ranking

    dados_detalhe = _carregar_dados_detalhe(caminho)
    labs_dados = _agregar_laboratorios_dados(dados_detalhe)
    if len(ranking) < len(labs_dados):
        ranking = labs_dados

    ranking = _calcular_market_share(ranking)

    concorrentes = _extrair_concorrentes(caminho, df_ranking if not df_ranking.empty else None, col_lab)
    conc_agg = _linha_concorrentes_agregado(concorrentes)

    concorrentes_no_top = sum(1 for l in top3 if "CONCORRENTE" in l.nome.upper())
    if metadados.formato == "novo" or concorrentes_no_top > 1:
        top3 = labs_dados[:3]
        if conc_agg and conc_agg.fat_2026 >= (top3[0].fat_2026 if top3 else 0):
            top3 = [conc_agg] + labs_dados[:2]
        elif conc_agg:
            top3 = (top3 + [conc_agg])[:3]
    top3 = _calcular_market_share(top3) if top3 else ranking[:3]

    portfolio, total_portfolio = _extrair_portfolio_analise(caminho)
    total_mercado_ntr = _extrair_mercado_ntr_analise(caminho)

    total_ntr = total_portfolio
    if total_ntr and total_mercado_ntr and total_mercado_ntr.fat_2026:
        total_ntr = LinhaFaturamento(
            nome=total_ntr.nome,
            fat_2025=total_ntr.fat_2025,
            fat_2026=total_ntr.fat_2026,
            crescimento=total_ntr.crescimento,
            market_share=total_ntr.fat_2026 / total_mercado_ntr.fat_2026,
            unidades_2025=total_ntr.unidades_2025,
            unidades_2026=total_ntr.unidades_2026,
        )

    positivos, negativos = _extrair_impactos(df_ranking) if not df_ranking.empty else ([], [])
    produtos_ranking = _extrair_produtos_ranking(
        positivos,
        negativos,
        total_ntr.fat_2026 if total_ntr else None,
    )
    positivos.sort(key=lambda x: x.crescimento or 0, reverse=True)
    negativos.sort(key=lambda x: x.crescimento or 0)

    regioes, total_regioes = _extrair_regioes(caminho)
    regioes = _calcular_market_share(regioes)
    bandeiras = _calcular_market_share(_extrair_bandeiras(caminho))

    produtos = _agregar_produtos(dados_detalhe)

    return EstudoDanone(
        periodo_label=periodo_label,
        metadados=metadados,
        total_ntr=total_ntr,
        total_mercado_ntr=total_mercado_ntr,
        portfolio=portfolio,
        laboratorios_top3=top3,
        laboratorios_ranking=ranking,
        produtos_ranking=produtos_ranking,
        impactos_positivos=positivos,
        impactos_negativos=negativos,
        regioes=regioes,
        total_regioes=total_regioes,
        bandeiras=bandeiras,
        concorrentes=concorrentes,
        produtos=produtos,
        dados_detalhe=dados_detalhe,
    )


carregar_dados = carregar_estudo


def copiar_planilha_entrega(
    destino: Path,
    origem: Path | None = None,
) -> Path:
    origem = Path(origem or PLANILHA_FONTE)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)
    return destino.resolve()
