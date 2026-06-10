# Publicar o Dashboard no Streamlit Cloud

Link permanente tipo: `https://seu-app.streamlit.app`

---

## Dados e confidencialidade (leia antes)

As planilhas em `dados/*.xlsx` (ex.: `DANONE_NOVO_ESTUDO01.xlsx`) contêm **dados comerciais** (faturamento, produto, região) — não há CPF ou nomes de pessoas, então o risco **direto de LGPD** é baixo.

O risco principal é **confidencialidade comercial** (Danone, ABRAFAD, concorrentes). Por isso:

| O que protege | O que NÃO protege |
|---------------|-------------------|
| Repositório **privado** no GitHub | Senha do app **não** impede download do Excel no GitHub público |
| **Senha** no Streamlit Secrets | Link do GitHub público expõe a planilha a qualquer clone |
| Compartilhar só o link `.streamlit.app` | Histórico público antigo no GitHub pode ter cópias da planilha |

**Recomendação:** repositório **privado** + senha forte no app.

---

## Passo a passo — tornar o repo privado e manter o Streamlit funcionando

Siga nesta ordem se o repositório está **público** hoje.

### A) GitHub — tornar o repositório privado

1. Abra: https://github.com/isadevlima/danone-dashboard-comercial
2. Clique em **Settings** (aba do repositório)
3. Role até **Danger Zone**
4. Clique em **Change repository visibility**
5. Escolha **Make private**
6. Confirme digitando o nome do repositório

> A planilha deixa de ser visível para quem não tem acesso ao repo. Quem já clonou quando era público pode ter cópia — avise o gestor se necessário.

### B) Streamlit Cloud — permitir repositórios privados

1. Abra: https://share.streamlit.io
2. Faça login com a **mesma conta GitHub** (`isadevlima`)
3. No canto superior direito, clique no **ícone de perfil**
4. Vá em **Settings**
5. Em **Linked accounts** / **GitHub**, clique em **Reconnect** ou **Grant access**
6. Na tela do GitHub, autorize o Streamlit a acessar repositórios **privados** (marque `danone-dashboard-comercial` ou “All repositories” conforme sua política)
7. Confirme e volte ao Streamlit Cloud

### C) Streamlit Cloud — verificar se o app ainda está ligado ao repo

1. Em https://share.streamlit.io, abra seu app (ex.: `danone-dashboard-comercial`)
2. Menu **⋮** (três pontos) → **Settings**
3. Confira:
   - **Repository:** `isadevlima/danone-dashboard-comercial`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
4. Se o app sumiu ou deu erro após tornar privado:
   - **Create app** de novo com os mesmos campos acima
   - Ou **Manage app → Settings → Reboot app**

### D) Streamlit Cloud — configurar senha (obrigatório em produção)

1. No app publicado, abra **Settings** (⚙️)
2. No menu lateral, clique em **Secrets**
3. Cole (troque pela **sua** senha forte — mínimo 12 caracteres, letras e números):

```toml
[dashboard]
senha = "SuaSenhaForteAqui2026"
```

4. Clique em **Save**
5. O app **reinicia sozinho** (aguarde 1–2 minutos)
6. Abra o link do app em aba anônima e teste a tela de senha

> Sem a seção `[dashboard]` nos Secrets, o app fica **aberto** para quem tiver o link.

### E) Testar

1. Abra o link `https://….streamlit.app` (não o GitHub)
2. Digite a senha
3. Confira se a **Visão Geral** carrega (planilha em `dados/`)
4. Opcional: teste em outro celular/PC

### F) Compartilhar com o time

Envie **apenas**:

- Link do app Streamlit (`https://….streamlit.app`)
- Senha (por canal seguro: Teams privado, não e-mail aberto se possível)

**Não** divulgue o link do repositório GitHub.

---

## Deploy inicial (primeira vez)

### Antes de começar

- Conta **GitHub**: https://github.com/signup
- Conta **Streamlit Cloud**: https://share.streamlit.io (login com GitHub)
- Planilha em `dados/` (ex.: `DANONE_NOVO_ESTUDO01.xlsx`, ~21 MB)

### Passo 1 — GitHub

1. https://github.com/new
2. Nome: `danone-dashboard-comercial`
3. Marque **Private**
4. **Create repository**

```powershell
cd "C:\Users\Monaliza.Lima\OneDrive\Documentos\CURSOR-APRESENTACAO"
git add .
git commit -m "Dashboard comercial Danone NTR"
git branch -M main
git remote add origin https://github.com/isadevlima/danone-dashboard-comercial.git
git push -u origin main
```

### Passo 2 — Streamlit Cloud

1. https://share.streamlit.io → **Create app**
2. **Repository:** `isadevlima/danone-dashboard-comercial`
3. **Branch:** `main`
4. **Main file path:** `streamlit_app.py`
5. **Deploy**
6. Siga a seção **D** acima para configurar **Secrets**

---

## Atualizar planilha (nova base MAT)

1. Coloque ou substitua arquivos `.xlsx` na pasta `dados/` — o dashboard usa automaticamente o mais recente
2. No PowerShell:

```powershell
git add dados/
git commit -m "Atualiza base MAT"
git push
```

O Streamlit Cloud redeploya em ~1–2 min. O **mesmo link** `.streamlit.app` continua válido após o push.

---

## Solução de problemas

| Problema | Solução |
|----------|---------|
| Repo privado não aparece no Streamlit | share.streamlit.io → Settings → reconectar GitHub e autorizar repos privados |
| App pede senha mas não aceita | Confira Secrets: `[dashboard]` e `senha = "..."` (aspas) |
| App abre sem pedir senha | Secrets vazio ou seção `[dashboard]` ausente |
| Erro de planilha no deploy | Confirme pelo menos um `.xlsx` em `dados/` no GitHub (repo privado, você precisa estar logado para ver) |
| Deploy falhou | **Manage app → Logs** |
| App lento na 1ª carga | Normal (~21 MB por planilha); depois usa cache |

---

## Checklist de segurança

- [ ] Repositório GitHub **privado**
- [ ] Streamlit autorizado a acessar repo privado
- [ ] Senha forte em **Secrets** (não usar exemplos da documentação)
- [ ] Link testado com senha em aba anônima
- [ ] Time recebe só link `.streamlit.app` + senha
- [ ] Gestor/jurídico Danone ciente do uso em nuvem (Streamlit)
