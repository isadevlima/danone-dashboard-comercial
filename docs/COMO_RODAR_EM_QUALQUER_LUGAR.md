# Como rodar o dashboard em qualquer lugar

Guia simples — sem termos complicados.

---

## O que significa “rodar em qualquer lugar”?

Você tem **duas formas** de usar o dashboard. Escolha a que combina com o seu caso:

| Forma | Onde funciona | Precisa do seu PC ligado? |
|-------|----------------|---------------------------|
| **A — Link na internet** | Celular, casa, escritório, qualquer navegador | **Não** (fica na nuvem) |
| **B — Pasta no computador** | Só no PC onde você instalou | **Sim** |

**Recomendação para o time comercial:** use a **Forma A** (link fixo).  
**Recomendação para você testar ou sem internet:** use a **Forma B**.

---

## Forma A — Link na internet (qualquer pessoa, qualquer lugar)

### Em poucas palavras

1. Você sobe o projeto para o **GitHub** (como uma pasta na nuvem).
2. O **Streamlit Cloud** lê essa pasta e publica um site.
3. Você manda o **link** para o time — eles abrem no Chrome, Edge, celular, etc.

### O que você precisa ter

- Conta no **GitHub** (grátis): https://github.com/signup  
- Conta no **Streamlit** (grátis, login com GitHub): https://share.streamlit.io  
- A pasta do projeto com a planilha em `dados/ESTUDO_DANONE_MAT_MAIO.xlsx`  
- **Repositório privado** no GitHub (recomendado — dados da Danone)

### Passo a passo (resumido)

**Passo 1 — Criar repositório no GitHub**

1. Entre em https://github.com/new  
2. Nome: `danone-dashboard-comercial`  
3. Marque **Private**  
4. Crie o repositório (sem README)

**Passo 2 — Enviar os arquivos do seu PC para o GitHub**

Seu GitHub: **https://github.com/isadevlima**

Abra o PowerShell na pasta do projeto e **copie e cole** (já com seu usuário):

```powershell
cd "C:\Users\Monaliza.Lima\OneDrive\Documentos\CURSOR-APRESENTACAO"
git add .
git commit -m "Dashboard Danone — estrutura organizada para deploy"
git branch -M main
git remote add origin https://github.com/isadevlima/danone-dashboard-comercial.git
git push -u origin main
```

> Se aparecer `remote origin already exists`, use só: `git push -u origin main`

Na primeira vez o GitHub pode pedir login (navegador ou token).

**Passo 3 — Publicar no Streamlit Cloud**

1. Acesse https://share.streamlit.io  
2. **Create app**  
3. Escolha seu repositório  
4. **Main file path:** `streamlit_app.py`  
5. **Deploy**

Em alguns minutos aparece um link tipo:

`https://danone-dashboard-comercial.streamlit.app`

**Passo 4 — Senha (opcional, mas recomendado)**

No app publicado → **Settings** → **Secrets** → cole:

```toml
[dashboard]
senha = "EscolhaUmaSenhaForte"
```

Salve. Quem abrir o link precisará dessa senha.

**Passo 5 — Compartilhar**

Envie por e-mail ou Teams:

- Link do app  
- Senha (se configurou)

Pronto: **qualquer pessoa, em qualquer lugar com internet**, abre o dashboard.

Guia detalhado: [DEPLOY_STREAMLIT.md](DEPLOY_STREAMLIT.md)

---

## Forma B — Rodar em outro computador (pasta + Python)

### Em poucas palavras

Você copia a **pasta inteira** do projeto para outro PC (pendrive, OneDrive, zip).  
Naquele PC instala **Python** uma vez, instala as bibliotecas e abre o dashboard.

### O que precisa estar na pasta

Copie **tudo** isso junto (mesma estrutura):

```
CURSOR-APRESENTACAO/
├── dados/
│   └── ESTUDO_DANONE_MAT_MAIO.xlsx   ← obrigatório
├── streamlit_app.py
├── requirements.txt
├── iniciar_dashboard.bat
├── danone/          (pasta inteira)
├── dashboard/       (pasta inteira)
├── scripts/         (pasta inteira)
└── .streamlit/      (pasta inteira)
```

Não precisa copiar: `__pycache__`, `.git` (opcional), pasta `saidas/` (só saídas geradas).

### No computador novo (uma vez só)

1. Instale **Python 3.10 ou superior**: https://www.python.org/downloads/  
   - Na instalação, marque **“Add Python to PATH”**

2. Abra o PowerShell na pasta do projeto:

```powershell
cd "CAMINHO\PARA\CURSOR-APRESENTACAO"
pip install -r requirements.txt
```

3. Para abrir o dashboard:

```powershell
streamlit run streamlit_app.py
```

4. No navegador, abra: **http://localhost:8501**

### Atalho no Windows (duplo clique)

Use o arquivo **`iniciar_dashboard.bat`** na pasta do projeto — ele instala o que falta e abre o dashboard.

---

## Comparando as duas formas

```
Forma A (Internet)
  Você → GitHub → Streamlit Cloud → Link
  Time abre o link em qualquer lugar ✓

Forma B (Computador local)
  Você → Copia pasta → Outro PC → Python + streamlit run
  Só funciona naquele PC com a pasta ✓
```

---

## Quando atualizar os dados (nova planilha)

1. Substitua o arquivo em `dados/ESTUDO_DANONE_MAT_MAIO.xlsx` (mesmo nome).  
2. **Forma A:** `git add` + `git commit` + `git push` → o site atualiza sozinho.  
3. **Forma B:** só trocar o Excel na pasta e atualizar a página do dashboard (F5).

O Excel **nunca é alterado** pelos scripts — só leitura.

---

## Problemas comuns

| Problema | O que fazer |
|----------|-------------|
| “Planilha não encontrada” | Confirme que existe `dados/ESTUDO_DANONE_MAT_MAIO.xlsx` |
| `python` não reconhecido | Reinstale Python marcando “Add to PATH” |
| `streamlit` não reconhecido | Rode `pip install -r requirements.txt` |
| Link da nuvem não abre | Veja os logs em share.streamlit.io → seu app → Manage app |
| Push no GitHub falha | Planilha é grande (~22 MB); use internet estável ou GitHub Desktop |

---

## Checklist rápido

**Para link em qualquer lugar (Forma A):**

- [ ] Conta GitHub  
- [ ] Repositório privado criado  
- [ ] Projeto enviado (`git push`)  
- [ ] Deploy no Streamlit com `streamlit_app.py`  
- [ ] Senha em Secrets (opcional)  
- [ ] Link testado no celular  

**Para outro PC (Forma B):**

- [ ] Python instalado  
- [ ] Pasta completa copiada com o Excel  
- [ ] `pip install -r requirements.txt`  
- [ ] `streamlit run streamlit_app.py` ou duplo clique no `.bat`  

---

## Precisa de ajuda?

- Publicar na internet: [DEPLOY_STREAMLIT.md](DEPLOY_STREAMLIT.md)  
- Uso diário do projeto: [README.md](README.md)
