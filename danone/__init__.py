"""Pacote Danone — leitura read-only e formatação do estudo MAT MAIO."""

from danone.config import (
    BASE_DIR,
    PASTA_APRESENTACOES,
    PASTA_DADOS,
    PASTA_RELATORIOS,
    PASTA_SAIDAS,
    PERIODO_LABEL,
    PLANILHA_FONTE,
    listar_planilhas,
    resolver_planilha,
)
from danone.formatters import fmt_moeda, fmt_ms, fmt_numero, fmt_pct, fmt_produto_curto
from danone.models import (
    CardPanoramaVisao,
    DadosApresentacao,
    EstudoDanone,
    LinhaFaturamento,
    MetadadosEstudo,
)
from danone.reader import (
    carregar_dados,
    carregar_estudo,
    ler_market_share_portfolio,
    cards_panorama_visao_geral,
    linhas_panorama_visao_geral,
)

__all__ = [
    "BASE_DIR",
    "PASTA_APRESENTACOES",
    "PASTA_DADOS",
    "PASTA_RELATORIOS",
    "PASTA_SAIDAS",
    "PERIODO_LABEL",
    "PLANILHA_FONTE",
    "listar_planilhas",
    "resolver_planilha",
    "MetadadosEstudo",
    "DadosApresentacao",
    "EstudoDanone",
    "CardPanoramaVisao",
    "LinhaFaturamento",
    "cards_panorama_visao_geral",
    "carregar_dados",
    "carregar_estudo",
    "ler_market_share_portfolio",
    "linhas_panorama_visao_geral",
    "fmt_moeda",
    "fmt_ms",
    "fmt_numero",
    "fmt_pct",
    "fmt_produto_curto",
]
