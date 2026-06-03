# Publicar o Dashboard no Streamlit Cloud (Opção 3)

Link permanente tipo: `https://seu-app.streamlit.app`

---

## Antes de começar

- Conta no **GitHub**: https://github.com/signup
- Conta no **Streamlit Cloud**: https://share.streamlit.io (entrar com GitHub)
- A planilha `dados/ESTUDO_DANONE_MAT_MAIO.xlsx` (~22 MB) vai para o repositório — **use repositório PRIVADO** se os dados forem confidenciais

---

## Passo 1 — Subir o projeto no GitHub

### Opção A — Pelo site do GitHub (mais fácil)

1. Acesse https://github.com/new
2. Nome sugerido: `danone-dashboard-comercial`
3. Marque **Private** (recomendado)
4. **Não** marque “Add README” (já temos arquivos locais)
5. Clique em **Create repository**

Seu GitHub: **https://github.com/isadevlima**

No PowerShell, na pasta do projeto — **copie e cole**:

```powershell
cd "C:\Users\Monaliza.Lima\OneDrive\Documentos\CURSOR-APRESENTACAO"

git add .
git commit -m "Dashboard comercial Danone NTR — Streamlit Cloud"

git branch -M main
git remote add origin https://github.com/isadevlima/danone-dashboard-comercial.git
git push -u origin main
```

> Se aparecer `remote origin already exists`, use só: `git push -u origin main`

> O upload da planilha (~22 MB) pode levar alguns minutos.

### Opção B — GitHub Desktop

1. Baixe: https://desktop.github.com
2. **File → Add local repository** → selecione a pasta `CURSOR-APRESENTACAO`
3. **Publish repository** → marque **Keep this code private**
4. Publish

---

## Passo 2 — Deploy no Streamlit Cloud

1. Acesse https://share.streamlit.io
2. Clique em **Create app**
3. Preencha:
   - **Repository:** `isadevlima/danone-dashboard-comercial`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
4. Clique em **Deploy**

Aguarde 2–5 minutos. O link aparecerá no formato:

`https://danone-dashboard-comercial.streamlit.app`

(ou nome parecido, conforme o repositório)

---

## Passo 3 — Senha de acesso (recomendado)

No Streamlit Cloud:

1. Abra seu app → **Settings** (⚙️)
2. **Secrets** → cole:

```toml
[dashboard]
senha = "Danone2026"
```

3. **Save** → o app reinicia sozinho

Quem abrir o link precisará dessa senha. Troque por uma senha forte.

Para testar localmente, copie o exemplo:

```powershell
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
# Edite secrets.toml com sua senha
```

---

## Passo 4 — Compartilhar com o time

Envie:

- **Link:** `https://seu-app.streamlit.app`
- **Senha:** (se configurou secrets)

O dashboard atualiza sozinho quando você der `git push` no GitHub.

---

## Atualizar dados (nova planilha)

1. Substitua `dados/ESTUDO_DANONE_MAT_MAIO.xlsx` (mesmo nome)
2. No PowerShell:

```powershell
git add dados/ESTUDO_DANONE_MAT_MAIO.xlsx
git commit -m "Atualiza base MAT"
git push
```

O Streamlit Cloud redeploya em ~1–2 min.

---

## Solução de problemas

| Problema | Solução |
|----------|---------|
| App não abre / erro de planilha | Confirme que `dados/ESTUDO_DANONE_MAT_MAIO.xlsx` está no GitHub |
| Deploy falhou | Veja **Manage app → Logs** no Streamlit Cloud |
| Repo privado não aparece | Reconecte GitHub em share.streamlit.io → Settings |
| App lento ao abrir | Normal na 1ª carga (~22 MB); depois fica em cache |

---

## Checklist final

- [ ] Repositório GitHub criado (preferencialmente **privado**)
- [ ] `dados/ESTUDO_DANONE_MAT_MAIO.xlsx` incluído no push
- [ ] App deployado com main file `streamlit_app.py`
- [ ] Senha configurada em Secrets
- [ ] Link testado no celular/outro PC
