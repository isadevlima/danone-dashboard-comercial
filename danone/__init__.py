"""Pacote Danone — leitura read-only e formatação do estudo MAT MAIO."""

from danone.config import BASE_DIR, PASTA_SAIDAS, PERIODO_LABEL, PLANILHA_FONTE
from danone.formatters import fmt_moeda, fmt_ms, fmt_numero, fmt_pct, fmt_produto_curto
from danone.models import DadosApresentacao, EstudoDanone, LinhaFaturamento
from danone.reader import carregar_dados, carregar_estudo

__all__ = [
    "BASE_DIR",
    "PASTA_SAIDAS",
    "PERIODO_LABEL",
    "PLANILHA_FONTE",
    "DadosApresentacao",
    "EstudoDanone",
    "LinhaFaturamento",
    "carregar_dados",
    "carregar_estudo",
    "fmt_moeda",
    "fmt_ms",
    "fmt_numero",
    "fmt_pct",
    "fmt_produto_curto",
]
