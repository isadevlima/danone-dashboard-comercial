# Danone NTR — Dashboard Comercial + Automações

Projeto para **ler** a planilha `dados/ESTUDO_DANONE_MAT_MAIO.xlsx` (read-only) e gerar:

- **Dashboard interativo** (Streamlit) — visão comercial
- **Apresentação executiva** (PowerPoint)
- **Relatórios Excel** (diretoria e cliente)

---

## Regra principal

> **`dados/ESTUDO_DANONE_MAT_MAIO.xlsx` é sempre a fonte da verdade.**
> Os scripts **apenas leem** — nunca alteram o Excel.

---

## Estrutura do projeto

```
CURSOR-APRESENTACAO/
├── streamlit_app.py              ← entrada do Streamlit Cloud
├── iniciar_dashboard.bat         ← abrir dashboard (duplo clique)
├── gerar_apresentacao.bat        ← gerar PowerPoint
├── gerar_relatorios.bat          ← gerar Excel diretoria/cliente
├── requirements.txt
│
├── dados/                        ← planilha oficial (não alterar pelos scripts)
│   └── ESTUDO_DANONE_MAT_MAIO.xlsx
│
├── danone/                       ← pacote central (leitura + formatação)
│   ├── config.py
│   ├── reader.py
│   ├── models.py
│   └── formatters.py
│
├── dashboard/                    ← interface Streamlit
│   ├── app.py
│   └── theme.py
│
├── scripts/                      ← automações executáveis
│   ├── gerar_apresentacao_diretoria.py
│   ├── gerar_relatorios_laboratorios.py
│   ├── ler_planilha_maio2026.py
│   └── restaurar_estudo_danone_original.py
│
├── saidas/                       ← artefatos gerados (git ignora conteúdo)
│   ├── apresentacoes/            ← .pptx
│   └── relatorios/               ← .xlsx
│
├── docs/                         ← guias de deploy e uso
│   ├── COMO_RODAR_EM_QUALQUER_LUGAR.md
│   └── DEPLOY_STREAMLIT.md
│
└── .streamlit/                   ← tema e secrets (exemplo)
```

---

## Rodar em qualquer lugar

Guia passo a passo: **[docs/COMO_RODAR_EM_QUALQUER_LUGAR.md](docs/COMO_RODAR_EM_QUALQUER_LUGAR.md)**

| Objetivo | O que fazer |
|----------|-------------|
| **Link para o time** | GitHub + Streamlit Cloud → [docs/DEPLOY_STREAMLIT.md](docs/DEPLOY_STREAMLIT.md) |
| **Outro PC seu** | Copiar pasta + `iniciar_dashboard.bat` |

---

## Instalação

```powershell
cd "C:\Users\Monaliza.Lima\OneDrive\Documentos\CURSOR-APRESENTACAO"
pip install -r requirements.txt
```

Confirme que existe: `dados\ESTUDO_DANONE_MAT_MAIO.xlsx`

---

## Dashboard comercial

**Duplo clique:** `iniciar_dashboard.bat`

**Ou no terminal:**

```powershell
streamlit run streamlit_app.py
```

URL: **http://localhost:8501**

### Publicar na internet

Guia: **[docs/DEPLOY_STREAMLIT.md](docs/DEPLOY_STREAMLIT.md)**

1. Crie o repo **privado** `danone-dashboard-comercial` em https://github.com/new (conta [isadevlima](https://github.com/isadevlima))
2. Envie o código (copie e cole no PowerShell):

```powershell
cd "C:\Users\Monaliza.Lima\OneDrive\Documentos\CURSOR-APRESENTACAO"
git add .
git commit -m "Dashboard Danone — estrutura organizada para deploy"
git branch -M main
git remote add origin https://github.com/isadevlima/danone-dashboard-comercial.git
git push -u origin main
```

3. Deploy em https://share.streamlit.io → repositório `isadevlima/danone-dashboard-comercial` → Main file: `streamlit_app.py`
4. Senha em Settings → Secrets

---

## Gerar apresentação e relatórios

**Duplo clique:** `gerar_apresentacao.bat` · `gerar_relatorios.bat`

**Ou no terminal (na raiz do projeto):**

```powershell
python -m scripts.gerar_apresentacao_diretoria
python -m scripts.gerar_relatorios_laboratorios
```

Saídas:

| Artefato | Pasta |
|----------|--------|
| PowerPoint | `saidas/apresentacoes/` |
| Excel diretoria/cliente | `saidas/relatorios/` |

---

## Abas lidas da planilha

| Aba | Uso |
|-----|-----|
| `Dados` | Detalhe produto × região × UF × bandeira |
| `Analise Básica` | Total NTR, portfólio Danone |
| `Ranking` | Laboratórios, Top 3, impactos |
| `Ranking Regiao\|UF` | Performance regional |
| `Ranking ABRAFAD` | Bandeiras farmacêuticas |
| `CONCORRENTE` | Panorama concorrente |

**Período:** MAT Abr/25 vs MAT Abr/26

---

## Histórico

| Etapa | Entrega |
|-------|---------|
| v4 | Estudo MAIO + pacote `danone/` + dashboard |
| **v5** | Pastas `dados/`, `scripts/`, `docs/`, `saidas/` — pronto para GitHub |
