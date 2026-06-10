"""Configuração central do projeto — fonte da verdade read-only."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PASTA_DADOS = BASE_DIR / "dados"

# Fallback quando não há planilha em dados/
PLANILHA_PADRAO = "DANONE_NOVO_ESTUDO01.xlsx"

PERIODO_LABEL_PADRAO = "MAT Abr/25 vs MAT Abr/26"

# Nomes de abas — resolvidos com busca flexível (maiúsculas, prefixo, legado)
ABA_DADOS_CANDIDATOS = ("DADOS", "Dados")
ABA_RANKING_CANDIDATOS = ("Ranking", "RANKING")
ABA_ANALISE_CANDIDATOS = ("Analise Básica", "Analise Basica", "Análise Básica")
ABA_REGIAO_CANDIDATOS = ("Ranking Regiao", "Ranking Regiao|UF", "Ranking Região")
ABA_ABRAFAD_PREFIXOS = ("Ranking ABRAFAD", "RANKING ABRAFAD")
ABA_CONCORRENTE_CANDIDATOS = ("CONCORRENTE", "Concorrente")

# Aliases legados (mantidos para scripts antigos)
SHEET_DADOS = "Dados"
SHEET_RANKING = "Ranking"
SHEET_REGIAO = "Ranking Regiao|UF"
SHEET_ABRAFAD = "Ranking ABRAFAD"
SHEET_CONCORRENTE = "CONCORRENTE"
PERIODO_LABEL = PERIODO_LABEL_PADRAO
PLANILHA_CANDIDATOS = (PLANILHA_PADRAO,)


def listar_planilhas() -> list[Path]:
    """Lista planilhas .xlsx em dados/ (mais recente primeiro)."""
    if not PASTA_DADOS.exists():
        return []
    arquivos = [p for p in PASTA_DADOS.glob("*.xlsx") if not p.name.startswith("~$")]
    return sorted(arquivos, key=lambda p: p.stat().st_mtime, reverse=True)


def resolver_planilha(nome: str | None = None) -> Path:
    """
    Retorna a planilha em dados/.
    - Se `nome` for informado, usa esse arquivo.
    - Caso contrário, usa a planilha .xlsx mais recente da pasta.
    """
    if nome:
        candidato = Path(nome)
        if not candidato.is_absolute():
            candidato = PASTA_DADOS / nome
        if candidato.exists():
            return candidato.resolve()

    planilhas = listar_planilhas()
    if planilhas:
        return planilhas[0].resolve()

    return (PASTA_DADOS / PLANILHA_PADRAO).resolve()


PLANILHA_FONTE = resolver_planilha()
PASTA_SAIDAS = BASE_DIR / "saidas"
PASTA_APRESENTACOES = PASTA_SAIDAS / "apresentacoes"
PASTA_RELATORIOS = PASTA_SAIDAS / "relatorios"
