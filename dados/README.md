# Dados (fonte da verdade)

Coloque aqui as planilhas de estudo (`.xlsx`). O dashboard lê **automaticamente** todos os arquivos desta pasta.

## Como usar

1. Copie o estudo para `dados/` (ex.: `DANONE_NOVO_ESTUDO01.xlsx`, `ACHE_ESTUDO_01.xlsx`, `TEUTO_NOVO_ESTUDO_01.xlsx`)
2. Inicie o dashboard — o arquivo mais recente é carregado por padrão
3. Na sidebar, selecione outro estudo se houver mais de um arquivo

## Formato esperado (novo)

Abas lidas pelo sistema:

| Aba | Conteúdo |
|-----|----------|
| `DADOS` | Detalhe produto × região × laboratório |
| `Analise Básica` | Setores de mercado e portfólio |
| `Ranking` | Ranking, totais e impactos |
| `Ranking Regiao` | Performance regional |

Abas opcionais (formato legado): `Ranking ABRAFAD`, `CONCORRENTE`, `Ranking Regiao\|UF`.

Os scripts **apenas leem** — nunca alteram o Excel.
