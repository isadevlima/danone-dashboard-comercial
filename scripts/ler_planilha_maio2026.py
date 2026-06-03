"""
Compatibilidade legada — reexporta o pacote danone/.
Use: from danone import carregar_estudo
"""

from danone import *  # noqa: F403
from danone import (
    EstudoDanone as DadosApresentacao,
    carregar_estudo as carregar_dados,
)
from danone.config import PLANILHA_FONTE
from danone.reader import copiar_planilha_entrega

__all__ = [
    "PLANILHA_FONTE",
    "DadosApresentacao",
    "carregar_dados",
    "copiar_planilha_entrega",
]
