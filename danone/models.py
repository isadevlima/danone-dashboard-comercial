"""Modelos de dados do estudo comercial."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class MetadadosEstudo:
    """Metadados detectados automaticamente a partir da planilha."""

    arquivo: str
    cliente: str
    abas: tuple[str, ...]
    formato: str  # "novo" | "legado"
    tem_bandeiras: bool = False
    tem_uf: bool = False
    tem_abrafad: bool = False
    tem_concorrente_aba: bool = False


@dataclass(frozen=True)
class CardPanoramaVisao:
    """Card da Visão Geral — recorte principal do estudo."""

    titulo: str
    subtitulo: str
    ms_rotulo: str
    fat_2025: float
    fat_2026: float
    crescimento: float | None = None
    market_share: float | None = None
    destaque: bool = False


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
    """Todos os dados extraídos da planilha de estudo (read-only)."""

    periodo_label: str
    metadados: MetadadosEstudo
    total_ntr: LinhaFaturamento | None
    total_mercado_ntr: LinhaFaturamento | None
    portfolio: list[LinhaFaturamento]
    laboratorios_top3: list[LinhaFaturamento]
    laboratorios_ranking: list[LinhaFaturamento]
    produtos_ranking: list[LinhaFaturamento]
    impactos_positivos: list[LinhaFaturamento]
    impactos_negativos: list[LinhaFaturamento]
    regioes: list[LinhaFaturamento]
    total_regioes: LinhaFaturamento | None
    bandeiras: list[LinhaFaturamento]
    concorrentes: list[LinhaFaturamento]
    produtos: pd.DataFrame = field(repr=False)
    dados_detalhe: pd.DataFrame = field(repr=False)

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
