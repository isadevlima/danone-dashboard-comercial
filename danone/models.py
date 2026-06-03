"""Modelos de dados do estudo Danone."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class LinhaFaturamento:
    nome: str
    fat_2025: float
    fat_2026: float
    crescimento: float | None = None
    market_share: float | None = None
    unidades_2025: float | None = None
    unidades_2026: float | None = None
    delta_abs: float | None = None


@dataclass
class EstudoDanone:
    """Todos os dados extraídos do ESTUDO_DANONE_MAT_MAIO (read-only)."""

    periodo_label: str
    total_ntr: LinhaFaturamento | None
    portfolio: list[LinhaFaturamento]
    laboratorios_top3: list[LinhaFaturamento]
    laboratorios_ranking: list[LinhaFaturamento]
    impactos_positivos: list[LinhaFaturamento]
    impactos_negativos: list[LinhaFaturamento]
    regioes: list[LinhaFaturamento]
    total_regioes: LinhaFaturamento | None
    bandeiras: list[LinhaFaturamento]
    concorrentes: list[LinhaFaturamento]
    produtos: pd.DataFrame = field(repr=False)
    dados_detalhe: pd.DataFrame = field(repr=False)

    # Alias para compatibilidade com apresentação legada
    @property
    def laboratorios_destaque(self) -> list[LinhaFaturamento]:
        return self.laboratorios_top3

    @property
    def portfolio_danone(self) -> list[LinhaFaturamento]:
        return self.portfolio

    @property
    def total_danone(self) -> LinhaFaturamento | None:
        return self.total_ntr

    @property
    def bandeiras_brasil(self) -> list[LinhaFaturamento]:
        return self.bandeiras

    @property
    def total_bandeiras_brasil(self) -> LinhaFaturamento | None:
        return None


# Alias legado
DadosApresentacao = EstudoDanone
