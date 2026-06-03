"""Configuração central do projeto — fonte da verdade read-only."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PLANILHA_FONTE = BASE_DIR / "ESTUDO_DANONE_MAT_MAIO.xlsx"
PASTA_SAIDAS = BASE_DIR / "saidas_automacao"
PERIODO_LABEL = "MAT Abr/25 vs MAT Abr/26"

# Abas esperadas (nomes flexíveis para variações de encoding)
SHEET_DADOS = "Dados"
SHEET_RANKING = "Ranking"
SHEET_REGIAO = "Ranking Regiao|UF"
SHEET_ABRAFAD = "Ranking ABRAFAD"
SHEET_CONCORRENTE = "CONCORRENTE"
