# CURSOR-APRESENTACAO — Estudo Danone + Dashboard Comercial

Projeto para **ler** a planilha `ESTUDO_DANONE_MAT_MAIO.xlsx` (read-only) e gerar:

- **Dashboard interativo** (Streamlit) — visão comercial
- **Apresentação executiva** (PowerPoint)
- **Relatórios Excel** (diretoria e cliente)

---

## Regra principal

> **`ESTUDO_DANONE_MAT_MAIO.xlsx` é sempre a fonte da verdade.**
> Os scripts **apenas leem** — nunca alteram o Excel.

---

## Estrutura do projeto

```
CURSOR-APRESENTACAO/
├── ESTUDO_DANONE_MAT_MAIO.xlsx     ← BASE (não alterar pelos scripts)
├── danone/                          ← pacote central (leitura + formatação)
│   ├── config.py
│   ├── models.py
│   ├── formatters.py
│   └── reader.py
├── dashboard/
│   ├── app.py                       ← Dashboard comercial (Streamlit)
│   └── theme.py
├── gerar_apresentacao_diretoria.py
├── gerar_relatorios_laboratorios.py
├── ler_planilha_maio2026.py         ← compatibilidade legada
└── saidas_automacao/
```

---

## Instalação

```powershell
cd "C:\Users\Monaliza.Lima\OneDrive\Documentos\CURSOR-APRESENTACAO"
pip install -r requirements.txt
```

---

## Dashboard comercial (principal)

```powershell
streamlit run streamlit_app.py
```

### Publicar na internet (link permanente)

Guia completo: **[DEPLOY_STREAMLIT.md](DEPLOY_STREAMLIT.md)**

Resumo:
1. Subir o projeto no **GitHub** (repositório **privado** recomendado)
2. Deploy em **https://share.streamlit.io** → Main file: `streamlit_app.py`
3. Configurar **senha** em Settings → Secrets

---

| Aba | Conteúdo comercial |
|-----|-------------------|
| **Visão Geral** | KPIs Danone NTR, portfólio (Baby/Medical/Brasil), Top 3 mercado |
| **Regional** | Faturamento e crescimento por região — onde focar vendas |
| **Produtos** | Top SKUs, maiores crescimentos e quedas |
| **Bandeiras** | Ranking ABRAFAD — redes prioritárias |
| **Concorrência** | Top 15 laboratórios + ambiente concorrente |
| **Impactos** | Produtos que puxam ou derrubam o resultado |
| **Explorador** | Filtros por região, UF, bandeira e produto (aba Dados) |

---

## Abas lidas da planilha

| Aba | Uso |
|-----|-----|
| `Dados` | Detalhe produto × região × UF × bandeira (8.667 linhas) |
| `Analise Básica` | Total NTR, portfólio Danone |
| `Ranking` | Laboratórios, Top 3, impactos positivos/negativos |
| `Ranking Regiao\|UF` | Performance regional |
| `Ranking ABRAFAD` | Bandeiras farmacêuticas |
| `CONCORRENTE` | Panorama concorrente |
| `FILTERS` | Metadados do recorte (somente leitura) |

**Período:** MAT Abr/25 vs MAT Abr/26

---

## Outros comandos

### Apresentação PowerPoint

```powershell
python gerar_apresentacao_diretoria.py
```

### Relatórios Excel

```powershell
python gerar_relatorios_laboratorios.py
```

---

## Dados de referência

| KPI | Valor |
|-----|-------|
| Danone NTR Abr/26 | R$ 2,06 bi (+20,09%) |
| Baby Nutrit | +23,43% |
| Medical Nut | −1,47% |
| Top bandeira ABRAFAD | Rede Soma |

---

## Histórico

| Etapa | Entrega |
|-------|---------|
| v1 | Scripts com CSV e slides estáticos |
| v2 | Planilha Excel multi-abas + PowerPoint dinâmico |
| v3 | Market share, ranking Brasil |
| **v4** | Novo estudo `ESTUDO_DANONE_MAT_MAIO` + pacote `danone/` + **dashboard comercial** |
